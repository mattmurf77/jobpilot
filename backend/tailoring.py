"""Resume tailoring engine.

`tailor(job, profile, config)` -> {"mode": "llm"|"basic", "resume": TailoredResume, "notes": str}

TailoredResume (structured JSON):
    {
      "subtitle": str,
      "summary_html": str,
      "roles": [{"company", "location", "titles": [{"title","dates"}],
                 "scope_line", "bullets": [{"html", "source_ref", "score"}]}],
      "earlier_impact": [{"html", "source_ref", "score"}],
      "earlier_impact_heading": str,
      "skills_html": str,
      "education": [str],
    }

The stable skeleton (companies, titles, dates, scope lines, education) always
comes from the baseline resume and NEVER changes. Only bullet selection/order,
summary, subtitle, and skills emphasis vary per job.

Guardrails: LLM output is validated — every selected bullet id must exist in
the inventory; any number in a rephrased bullet must already appear in its
source line (else the verbatim source line is used); skills must trace to the
source materials. Any API/parse failure falls back to deterministic basic mode.
"""
import json
import os
import re

from backend import line_menu, voice_check

# Menu section ids -> resume slots. Overridable in config.json under
# tailoring.menu_slots; the defaults match materials/templates/resume_line_menu.md
# (see line_menu.ROLE_SECTION_IDS for what the parser harvests).
DEFAULT_SLOTS = {
    "main": ("3", "4", "5"),      # current employer: main bullet list
    "earlier": ("6",),            # "Earlier impact" subhead inside the first role block
    "second_role": ("7",),        # previous employer (second role block)
    "projects": ("17",),          # optional Projects section
}


def _slots(config):
    cfg = ((config or {}).get("tailoring") or {}).get("menu_slots") or {}
    slots = {}
    for key, default in DEFAULT_SLOTS.items():
        val = cfg.get(key)
        slots[key] = tuple(str(x) for x in val) if isinstance(val, (list, tuple)) and val else default
    return slots


def _projects_settings(config, inventory):
    """Heading/dates/scope/triggers for the optional Projects section.
    config.json tailoring.projects wins; heading falls back to the menu's own
    section title (minus any trailing editorial note)."""
    cfg = ((config or {}).get("tailoring") or {}).get("projects") or {}
    heading = str(cfg.get("heading") or "").strip()
    if not heading:
        ids = _slots(config)["projects"]
        sec = next((s for s in inventory.get("sections", []) if s["id"] in ids), None)
        if sec:
            heading = re.split(r"\s+[—–-]{1,2}\s+|\s*\(added", sec["heading"], 1)[0].strip()
    return {
        "heading": heading or "Projects",
        "dates": str(cfg.get("dates") or ""),
        "scope_line": str(cfg.get("scope_line") or ""),
        "triggers": [str(t).lower() for t in (cfg.get("triggers") or []) if str(t).strip()],
    }


def _trigger_hits(jd_lower, triggers):
    return [t for t in triggers if re.search(r"\b" + re.escape(t) + r"\b", jd_lower)]


def _projects_block(inventory, jd, jd_set, compiled_tx, config):
    """Optional Projects section. Included when a configured trigger term
    appears in the JD (tailoring.projects.triggers), or, with no triggers
    configured, when at least two project bullets overlap the JD's vocabulary.
    Returns None to omit."""
    slots = _slots(config)
    settings = _projects_settings(config, inventory)
    picked = _select(inventory, slots["projects"], jd_set, 3, compiled_tx)
    if not picked:
        return None
    hits = _trigger_hits(jd.lower(), settings["triggers"])
    bullets = [_bullet_entry(b, jd_set, compiled_tx) for b in picked[:3]]
    if settings["triggers"]:
        if not hits:
            return None
    else:
        if sum(1 for b in bullets if b["score"] > 0) < 2:
            return None
        hits = ["keyword-overlap"]
    if len(bullets) < 2:
        return None
    # The section is here because the JD signaled relevance, but these bullets
    # score low on raw keyword overlap and were being trimmed first on tight
    # pages. Credit the trigger strength so they compete fairly.
    boost = min(len(hits), 5) * 0.6
    for b in bullets:
        b["score"] = round(b["score"] + boost, 2)
    return {
        "heading": settings["heading"],
        "dates": settings["dates"],
        "scope_line": settings["scope_line"],
        "bullets": bullets,
        "triggers": hits,
    }


# ----------------------------------------------------------- user feedback
# Review-tab feedback. Directives ("include §3.2", "remove §17.4", "subtitle 7")
# are honored deterministically in BOTH modes; the full free text additionally
# steers the LLM prompt. Section -> resume slot per tailoring.menu_slots
# (defaults: 3/4/5 main, 6 earlier, 7 second role, 17 projects).

_FB_REF_RE = re.compile(
    r"\b(include|add|use|pin|keep|remove|drop|exclude|cut)\b[^§\d]{0,12}§?\s*(\d+(?:\.\d+)+)", re.I)
_FB_SUBTITLE_RE = re.compile(r"\bsubtitle\b\s*[:#]?\s*(\d+)", re.I)
_FB_INCLUDE_VERBS = ("include", "add", "use", "pin", "keep")


def parse_feedback(feedback):
    """-> {"includes": set[ref], "excludes": set[ref], "subtitle_n": int|None}"""
    includes, excludes, subtitle_n = set(), set(), None
    for verb, ref in _FB_REF_RE.findall(feedback or ""):
        (includes if verb.lower() in _FB_INCLUDE_VERBS else excludes).add(ref)
    m = _FB_SUBTITLE_RE.search(feedback or "")
    if m:
        subtitle_n = int(m.group(1))
    return {"includes": includes - excludes, "excludes": excludes, "subtitle_n": subtitle_n}


def _slot_for_section(section_id, slots):
    top = str(section_id).split(".")[0]
    if top in slots["main"]:
        return "main"
    if top in slots["earlier"]:
        return "earlier"
    if top in slots["second_role"]:
        return "sales"
    if top in slots["projects"]:
        return "projects"
    return None


def _apply_feedback(resume, fb, inventory, jd_set, compiled_tx, config):
    """Mutates the assembled resume per parsed feedback. Returns notes []."""
    notes = []
    by_id = _all_bullets(inventory, compiled_tx)
    slots = _slots(config)
    proj = _projects_settings(config, inventory)

    def slot_list(slot):
        if slot == "main":
            return resume["roles"][0]["bullets"] if resume.get("roles") else None
        if slot == "earlier":
            return resume.get("earlier_impact")
        if slot == "sales":
            return resume["roles"][1]["bullets"] if len(resume.get("roles", [])) > 1 else None
        if slot == "projects":
            return (resume.get("projects") or {}).get("bullets")
        return None

    for ref in sorted(fb["excludes"]):
        removed = False
        for slot in ("main", "earlier", "sales", "projects"):
            lst = slot_list(slot)
            if lst is None:
                continue
            before = len(lst)
            lst[:] = [b for b in lst if b.get("source_ref") != f"§{ref}"]
            removed = removed or len(lst) < before
        notes.append(f"removed §{ref}" if removed else f"§{ref} was not in the draft (remove ignored)")
        # An emptied projects section disappears entirely.
        if resume.get("projects") and not resume["projects"]["bullets"]:
            resume["projects"] = None

    for ref in sorted(fb["includes"]):
        if ref not in by_id:
            notes.append(f"§{ref} not found in the line menu (include ignored)")
            continue
        slot = _slot_for_section(ref, slots)
        if slot is None:
            notes.append(f"§{ref} is not a resume-slot section (include ignored)")
            continue
        if slot == "projects" and not resume.get("projects"):
            resume["projects"] = {"heading": proj["heading"], "dates": proj["dates"],
                                  "scope_line": proj["scope_line"], "bullets": [],
                                  "triggers": ["user-feedback"]}
        lst = slot_list(slot)
        if lst is None:
            notes.append(f"no slot available for §{ref} (include ignored)")
            continue
        if any(b.get("source_ref") == f"§{ref}" for b in lst):
            notes.append(f"§{ref} already present")
            continue
        entry = _bullet_entry(by_id[ref], jd_set, compiled_tx)
        entry["score"] = 99  # user-pinned: never the trim victim
        lst.insert(0, entry)
        notes.append(f"pinned §{ref} into {slot}")

    n = fb["subtitle_n"]
    if n is not None:
        subs = inventory.get("subtitles", [])
        if 1 <= n <= len(subs):
            resume["subtitle"] = apply_translations(subs[n - 1], compiled_tx)
            notes.append(f"subtitle forced to §0.2 variant {n}")
        else:
            notes.append(f"subtitle {n} out of range 1-{len(subs)} (ignored)")
    return notes


def _domain_subtitle(inventory, baseline_subtitle, jd_set):
    """Basic mode: pick the §0.2 subtitle variant whose vocabulary overlaps the
    JD most; keep the baseline unless a variant clearly beats it (>= 2 more
    shared terms)."""
    subs = inventory.get("subtitles", [])
    if not subs:
        return baseline_subtitle, None

    def overlap(text):
        return len({t for t in _tokens(text) if len(t) > 2} & jd_set)

    base_score = overlap(baseline_subtitle)
    best = max(subs, key=overlap)
    if best.strip() != baseline_subtitle.strip() and overlap(best) >= base_score + 2:
        return best, f"{overlap(best)} JD terms in variant vs {base_score} in baseline"
    return baseline_subtitle, None

STOPWORDS = frozenset(
    "a an the and or of to in for with on at by from as is are was were be been being "
    "this that these those it its their our your you we they he she will would can could "
    "should may might must have has had do does did not no but if then than so such per "
    "across into over under more most other some any all each both about within while "
    "who whom whose what which when where how why also etc eg ie via vs s t".split()
)

_NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")


# ----------------------------------------------------------------- utilities

def _tokens(text):
    return [w for w in re.findall(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", str(text or "").lower())
            if w not in STOPWORDS and len(w) > 1]


def _numbers(text):
    return {m.group(0).replace(",", "") for m in _NUM_RE.finditer(str(text or ""))}


def _validate_numbers(source, output, extra_allowed=""):
    """True if every numeric token in `output` appears in `source` (or in the
    allowed extras, e.g. translation replacement strings)."""
    return _numbers(output) <= (_numbers(source) | _numbers(extra_allowed))


def _compile_translations(pairs):
    out = []
    for internal, external in sorted(pairs, key=lambda p: -len(p[0])):
        try:
            # Capture an optional preceding article so substitutions can fix
            # clashes like "a GML product" -> "a the merchant-lending ... product".
            out.append((re.compile(r"(?:\b(a|an|the|A|An|The)\s+)?\b" + re.escape(internal) + r"\b"),
                        external))
        except re.error:
            continue
    return out


_NEXT_WORD_RE = re.compile(r"^\s+([A-Za-z][\w-]*)")


def apply_translations(text, compiled):
    for rx, external in compiled:
        def _sub(m, external=external):
            repl = external
            # Noun-stacking guard: if the word right after the match already
            # appears inside the replacement ("GML product" with repl
            # "the merchant-lending product team"), cut the replacement just
            # before that word so it reads "merchant-lending product".
            nxt = _NEXT_WORD_RE.match(m.string[m.end():])
            if nxt:
                tokens = repl.split()
                lowered = [t.lower().strip(".,;:") for t in tokens]
                if nxt.group(1).lower() in lowered[1:]:
                    cut = lowered[1:].index(nxt.group(1).lower()) + 1
                    repl = " ".join(tokens[:cut])
            article = m.group(1)
            if article:
                capitalized = article[0].isupper()
                # Drop the original article when the replacement brings its own
                # ("the ...") or starts with a possessive ("PayPal's ...").
                if re.match(r"^(the|a|an)\b", repl, re.I) or re.match(r"^[A-Z][\w]*'s\b", repl):
                    return repl[0].upper() + repl[1:] if capitalized else repl
                # Replacement reduced to a bare modifier ("merchant-lending"):
                # keep the article, fixing a/an agreement with the new first word.
                if article.lower() in ("a", "an"):
                    article = "an" if repl[:1].lower() in "aeiou" else "a"
                    if capitalized:
                        article = article.capitalize()
                return f"{article} {repl}"
            return repl
        text = rx.sub(_sub, text)
    # Collapse word doublings the substitutions can create.
    text = re.sub(r"\b([a-z]+) \1\b", r"\1", text)
    return text


def _translation_extra_text(inventory):
    return " ".join(ext for _, ext in inventory.get("translation_pairs", []))


def _all_bullets(inventory, compiled_tx):
    by_id = {}
    for sec in inventory["sections"]:
        for b in sec["bullets"]:
            by_id[b["id"]] = dict(b, section=sec["id"],
                                  tx_text=apply_translations(b["text"], compiled_tx))
    return by_id


def _jd_text(job):
    return f"{job.get('title') or ''}\n{job.get('description') or ''}"


def _score_bullet(bullet, jd_token_set):
    # Score against the jargon-translated text so e.g. "PPBL" matches a JD
    # that says "business loan".
    text = bullet.get("tx_text") or bullet["text"]
    overlap = len(set(_tokens(text)) & jd_token_set)
    metrics = bullet.get("metrics", [])
    metric_boost = min(len(metrics), 3) * 0.5
    # Scale-signal boost (menu §11: lead with the biggest numeric anchors).
    if any("B" in m and "$" in m for m in metrics):
        metric_boost += 1.0
    return overlap + metric_boost


def _dedupe(selected, candidate):
    """Skip a candidate that repeats >=2 metric tokens of an already-picked bullet
    (e.g. the $1.37B portfolio bullet exists in both §3.2 and §4.1)."""
    cand = set(candidate.get("metrics", []))
    for b in selected:
        if len(cand & set(b.get("metrics", []))) >= 2:
            return True
    return False


def _select(inventory, section_ids, jd_token_set, max_n, compiled_tx):
    pool = []
    for sec in inventory["sections"]:
        if sec["id"] in section_ids:
            pool.extend(dict(b, section=sec["id"],
                             tx_text=apply_translations(b["text"], compiled_tx))
                        for b in sec["bullets"])
    pool.sort(key=lambda b: -_score_bullet(b, jd_token_set))
    out = []
    for b in pool:
        if len(out) >= max_n:
            break
        if not _dedupe(out, b):
            out.append(b)
    return out


def _bullet_entry(bullet, jd_token_set, compiled_tx, text_override=None):
    text = text_override if text_override is not None else bullet["text"]
    text = voice_check.scrub(apply_translations(text, compiled_tx))
    return {
        "html": line_menu.md_to_html(text),
        "source_ref": f"§{bullet['id']}",
        "score": round(_score_bullet(bullet, jd_token_set), 2),
    }


def _skills(inventory, baseline, jd_text, llm_skills=None):
    """Order skills tokens by JD relevance; bold the JD-mirrored ones.
    Every token must trace to the baseline skills line or the menu §8 library."""
    base_tokens = [t.strip() for t in re.sub(r"<[^>]+>", "", baseline["skills_html"]).split("·") if t.strip()]
    library = list(dict.fromkeys(base_tokens + inventory.get("skills_library", [])))
    allowed = {t.lower(): t for t in library}
    jd_lower = jd_text.lower()

    def jd_freq(token):
        core = re.sub(r"\s*\([^)]*\)", "", token).strip().lower()
        n = jd_lower.count(core) if len(core) > 2 else 0
        # Parenthesized abbreviations count too: "Model Context Protocol (MCP)"
        # should match a JD that just says "MCP" (same for RICE, SDLC, CRO...).
        for paren in re.findall(r"\(([^)]+)\)", token):
            for abbr in re.split(r"[,/]", paren):
                a = abbr.strip().lower()
                if len(a) >= 3:
                    n += len(re.findall(r"\b" + re.escape(a) + r"\b", jd_lower))
        return n

    if llm_skills:
        chosen = [allowed[s.strip().lower()] for s in llm_skills
                  if isinstance(s, str) and s.strip().lower() in allowed]
        chosen = list(dict.fromkeys(chosen))
        if len(chosen) < 8:  # too few survived validation; fall back
            chosen = None
    else:
        chosen = None
    if not chosen:
        matched = [t for t in library if jd_freq(t) > 0]
        matched.sort(key=lambda t: -jd_freq(t))
        rest = [t for t in base_tokens if jd_freq(t) == 0]
        chosen = (matched + rest)[:20]
        if len(chosen) < 12:
            chosen = list(dict.fromkeys(chosen + base_tokens))[:18]

    parts = []
    for t in chosen:
        esc = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        parts.append(f"<strong>{esc}</strong>" if jd_freq(t) > 0 else esc)
    mirrored = [t for t in chosen if jd_freq(t) > 0][:6]
    return " · ".join(parts), mirrored


def _assemble(baseline, subtitle, summary_html, main_bullets, earlier, sales, skills_html,
              projects=None):
    roles = []
    for i, role in enumerate(baseline["roles"]):
        r = {
            "company": role["company"],
            "location": role["location"],
            "titles": role["titles"],
            "scope_line": role["scope_line"],
            "bullets": [],
        }
        if i == 0:
            r["bullets"] = main_bullets
        elif i == 1:
            r["bullets"] = sales or [
                {"html": b, "source_ref": "baseline", "score": 0} for b in role["bullets"]]
        else:
            r["bullets"] = [{"html": b, "source_ref": "baseline", "score": 0} for b in role["bullets"]]
        roles.append(r)
    return {
        "subtitle": voice_check.scrub(subtitle),
        "summary_html": voice_check.scrub(summary_html),
        "roles": roles,
        "earlier_impact": earlier,
        "earlier_impact_heading": baseline["earlier_impact_heading"] or "Earlier impact:",
        "projects": projects,  # optional Projects block (tailoring.projects)
        "skills_html": skills_html,
        "education": baseline["education"],
    }


# ---------------------------------------------------------------- basic mode

def _tailor_basic(job, profile, config, inventory, baseline, prefix_notes=""):
    jd = _jd_text(job)
    jd_set = set(_tokens(jd))
    compiled_tx = _compile_translations(inventory.get("translation_pairs", []))
    max_n = int(config.get("tailoring", {}).get("max_bullets_per_role", 6))

    slots = _slots(config)
    main = [_bullet_entry(b, jd_set, compiled_tx)
            for b in _select(inventory, slots["main"], jd_set, max_n, compiled_tx)]
    earlier = [_bullet_entry(b, jd_set, compiled_tx)
               for b in _select(inventory, slots["earlier"], jd_set, 2, compiled_tx)]
    sales = [_bullet_entry(b, jd_set, compiled_tx)
             for b in _select(inventory, slots["second_role"], jd_set, 1, compiled_tx)]
    if not main:  # inventory came up empty; keep the baseline bullets verbatim
        main = [{"html": b, "source_ref": "baseline", "score": 0}
                for b in baseline["roles"][0]["bullets"]] if baseline["roles"] else []
    if not earlier:
        earlier = [{"html": b, "source_ref": "baseline", "score": 0}
                   for b in baseline["earlier_impact"]]

    skills_html, mirrored = _skills(inventory, baseline, jd)
    subtitle, swap_reason = _domain_subtitle(inventory, baseline["subtitle"], jd_set)
    subtitle = apply_translations(subtitle, compiled_tx)
    projects = _projects_block(inventory, jd, jd_set, compiled_tx, config)
    resume = _assemble(baseline, subtitle, baseline["summary_html"],
                       main, earlier, sales, skills_html, projects=projects)
    refs = ", ".join(b["source_ref"] for b in main + earlier + sales if b["source_ref"] != "baseline")
    notes = (prefix_notes + f"Basic (deterministic) tailoring: bullets ranked by JD keyword overlap "
             f"+ metric boost. Selected {refs or 'baseline bullets'}. "
             f"Skills mirroring JD: {', '.join(mirrored) or 'none detected'}. "
             + (f"Subtitle swapped to the best-matching variant ({swap_reason}). " if swap_reason
                else "Baseline subtitle kept. ")
             + (f"Projects section included (triggers: {', '.join(projects['triggers'][:4])}). "
                if projects else "Projects section omitted (no trigger terms / overlap in JD). ")
             + "Baseline summary kept.")
    return {"mode": "basic", "resume": resume, "notes": notes}


# ------------------------------------------------------------------ LLM mode

_LLM_SYSTEM = """You tailor {name}'s resume to a job description. You select content; you do not invent it.

HARD RULES (violations make the output unusable):
1. Select bullets ONLY from the provided inventory, referenced by their exact bullet id.
2. You may lightly rephrase a selected bullet ONLY to (a) translate company-internal jargon using the provided translation pairs, or (b) mirror the job description's vocabulary. Keep the meaning identical.
3. NEVER introduce a number, percentage, dollar amount, employer, job title, date, technology, or claim that is not present in the bullet's source line. If unsure, return the source line verbatim.
4. Pick the subtitle EXACTLY (character-for-character) from the provided subtitle variants.
5. Base the summary on ONE provided summary variant (give its id); light rephrasing under the same constraints as rule 2-3.
6. Skills: choose 15-20 items ONLY from the provided skills library, ordered most-JD-relevant first; 3-6 of them must be exact phrases that appear in the job description.
7. Output STRICT JSON matching the schema. No commentary, no markdown fences.
""" + voice_check.VOICE_RULES_PROMPT

_LLM_SCHEMA = """{
  "subtitle": "<exact text of one subtitle variant>",
  "summary": {"source_id": "<summary variant id>", "text": "<summary, lightly rephrased at most>"},
  "main_bullets": [{"id": "<bullet id>", "text": "<source line, verbatim or lightly rephrased>"}],
  "earlier_impact_bullets": [{"id": "...", "text": "..."}],
  "second_role_bullets": [{"id": "...", "text": "..."}],
  "skills": ["<skill token>", "..."],
  "notes": "<1-2 sentences on selection rationale>"
}"""


def _llm_call(job, profile, config, inventory, max_n, feedback=None):
    import anthropic  # imported lazily; only needed in LLM mode
    from backend.profile_store import display_name

    slots = _slots(config)

    def section_lines(ids):
        lines = []
        for sec in inventory["sections"]:
            if sec["id"] in ids:
                lines.append(f"## {sec['heading']}")
                lines.extend(f"[{b['id']}] {b['text']}" for b in sec["bullets"])
        return "\n".join(lines)

    tx_lines = "\n".join(f"- {i} -> {e}" for i, e in inventory.get("translation_pairs", []))
    subtitle_lines = "\n".join(f"- {s}" for s in inventory.get("subtitles", []))
    summary_lines = "\n".join(f"[{s['id']}] ({s['label']}) {s['text']}" for s in inventory.get("summaries", []))
    skills_lines = " · ".join(inventory.get("skills_library", []))

    user = f"""JOB DESCRIPTION
Title: {job.get('title')}
Company: {job.get('company')}
{(job.get('description') or '')[:6000]}

BULLET INVENTORY — current-employer sections (select up to {max_n} for "main_bullets"):
{section_lines(slots["main"])}

BULLET INVENTORY — earlier impact at the same employer (select 1-2 for "earlier_impact_bullets"; return [] if the inventory is empty):
{section_lines(slots["earlier"])}

BULLET INVENTORY — previous employer (select exactly 1 for "second_role_bullets"; return [] if the inventory is empty):
{section_lines(slots["second_role"])}

SUBTITLE VARIANTS (pick one verbatim):
{subtitle_lines}

SUMMARY VARIANTS:
{summary_lines}

TRANSLATION PAIRS (internal -> external; apply to every selected line):
{tx_lines}

SKILLS LIBRARY (choose 15-20, JD-relevant first):
{skills_lines}
{_feedback_prompt(feedback)}
OUTPUT SCHEMA:
{_LLM_SCHEMA}"""

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=config.get("tailoring", {}).get("model", "claude-opus-5"),
        max_tokens=16000,
        system=_LLM_SYSTEM.replace("{name}", display_name(profile)),
        messages=[{"role": "user", "content": user}],
    )
    if resp.stop_reason == "refusal":
        raise ValueError("model declined the tailoring request")
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    return _parse_json_object(text)


def _parse_json_object(text):
    """Tolerate markdown fences or prose around the JSON object."""
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in model output")
    return json.loads(text[start:end + 1])


def _feedback_prompt(feedback):
    if not feedback:
        return ""
    return f"""
USER FEEDBACK on the previous tailored draft — honor it as long as it does not
violate the HARD RULES (never invent facts to satisfy feedback):
{feedback.strip()}
"""


def _validated_bullets(items, by_id, jd_set, compiled_tx, tx_extra, max_n):
    out, fixed = [], 0
    for item in items or []:
        if len(out) >= max_n:
            break
        bid = str(item.get("id", "")).strip().lstrip("§")
        if bid not in by_id:
            continue
        src = by_id[bid]
        text = str(item.get("text") or "").strip() or src["text"]
        if not _validate_numbers(src["text"], text, extra_allowed=tx_extra):
            text = src["text"]  # rephrasing invented a number: use verbatim source
            fixed += 1
        out.append(_bullet_entry(src, jd_set, compiled_tx, text_override=text))
    return out, fixed


def _tailor_llm(job, profile, config, inventory, baseline, feedback=None):
    jd = _jd_text(job)
    jd_set = set(_tokens(jd))
    compiled_tx = _compile_translations(inventory.get("translation_pairs", []))
    tx_extra = _translation_extra_text(inventory)
    max_n = int(config.get("tailoring", {}).get("max_bullets_per_role", 6))
    by_id = _all_bullets(inventory, compiled_tx)

    data = _llm_call(job, profile, config, inventory, max_n, feedback=feedback)

    main, fx1 = _validated_bullets(data.get("main_bullets"), by_id, jd_set, compiled_tx, tx_extra, max_n)
    earlier, fx2 = _validated_bullets(data.get("earlier_impact_bullets"), by_id, jd_set, compiled_tx, tx_extra, 2)
    sales, fx3 = _validated_bullets(data.get("second_role_bullets", data.get("sales_bullets")),
                                    by_id, jd_set, compiled_tx, tx_extra, 1)
    if len(main) < 3:
        raise ValueError("LLM selected too few valid bullets")

    # Subtitle: must be one of the §0.2 variants, else keep baseline.
    subtitle = str(data.get("subtitle") or "").strip()
    variants = {v.strip() for v in inventory.get("subtitles", [])}
    if subtitle not in variants:
        subtitle = baseline["subtitle"]
    subtitle = apply_translations(subtitle, compiled_tx)

    # Summary: numbers must trace to the chosen variant, else baseline summary.
    summary_html = baseline["summary_html"]
    s = data.get("summary") or {}
    src_summary = next((v for v in inventory.get("summaries", []) if v["id"] == s.get("source_id")), None)
    if src_summary and s.get("text"):
        if _validate_numbers(src_summary["text"], s["text"], extra_allowed=tx_extra):
            summary_html = line_menu.md_to_html(apply_translations(str(s["text"]), compiled_tx))
        else:
            summary_html = line_menu.md_to_html(apply_translations(src_summary["text"], compiled_tx))

    skills_html, mirrored = _skills(inventory, baseline, jd, llm_skills=data.get("skills"))
    # Projects section is deterministic in both modes (short factual bullets;
    # keeps the LLM schema/validation surface unchanged).
    projects = _projects_block(inventory, jd, jd_set, compiled_tx, config)
    resume = _assemble(baseline, subtitle, summary_html, main, earlier, sales, skills_html,
                       projects=projects)

    fixes = fx1 + fx2 + fx3
    refs = ", ".join(b["source_ref"] for b in main + earlier + sales)
    notes = (f"LLM tailoring (validated). Selected {refs}. "
             f"Skills mirroring JD: {', '.join(mirrored) or 'n/a'}. "
             + (f"{fixes} rephrased line(s) failed number validation and were replaced "
                f"with verbatim source lines. " if fixes else "")
             + str(data.get("notes") or "")).strip()
    return {"mode": "llm", "resume": resume, "notes": notes}


# -------------------------------------------------------------------- public

def tailor(job, profile, config, feedback=None):
    inventory = line_menu.load_inventory()
    baseline = line_menu.load_baseline()
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            result = _tailor_llm(job, profile, config, inventory, baseline, feedback=feedback)
        except Exception as e:  # API/parse/validation error -> deterministic mode
            result = _tailor_basic(job, profile, config, inventory, baseline,
                                   prefix_notes=f"LLM mode failed ({type(e).__name__}: {e}); fell back. ")
    else:
        result = _tailor_basic(job, profile, config, inventory, baseline)
    if feedback:
        fb = parse_feedback(feedback)
        jd_set = set(_tokens(_jd_text(job)))
        compiled_tx = _compile_translations(inventory.get("translation_pairs", []))
        fb_notes = _apply_feedback(result["resume"], fb, inventory, jd_set, compiled_tx, config)
        freeform = not (fb["includes"] or fb["excludes"] or fb["subtitle_n"] is not None)
        if freeform and result["mode"] == "basic":
            fb_notes.append("freeform feedback stored — applied fully only in LLM mode "
                            "(add an API key), or use include/remove §id directives")
        result["notes"] += " Feedback: " + ("; ".join(fb_notes) or "passed to LLM prompt") + "."
    return result
