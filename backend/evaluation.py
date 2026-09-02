"""Deterministic multi-dimensional job-fit evaluation (the P0 "judgment layer").

evaluate(job, profile, config, inventory) -> {
    "mode": "basic",
    "dimensions": {key: {"score": 0-100, "label": str, "notes": str}},   # 4 keys
    "location": {"verdict": "PASS"|"FLAG"|"FAIL", "notes": str},
    "strengths": [str, ...],        # max 5
    "gaps": [str, ...],             # max 6, verbatim JD requirement fragments
    "recommendation": "strong"|"moderate"|"weak",
    "summary": str,                 # 2 sentences
}

Rule-based only — no LLM, no network. `mode` is the seam for a future LLM
evaluator: it must return this exact shape with mode "llm"; clients key off it.
The honest-gaps rule (from the ai-job-search framework): gaps are stated,
never smoothed over — a requirement with zero overlap with profile/menu terms
is quoted verbatim as a gap.
"""
import re

from backend.matching import current_level, ladder_delta
from backend.matching import home_terms as matching_home_terms
from backend.matching import _ELSEWHERE_REMOTE as ELSEWHERE_REMOTE, home_country_terms

from backend.matching import _has_phrase, _norm, _title_core
from backend.tailoring import _tokens

DIMENSION_WEIGHTS = {
    "title_seniority": 0.30,
    "skills": 0.30,
    "domain_experience": 0.25,
    "career_alignment": 0.15,
}

# Title terms that signal a level mismatch when they are NOT in the target titles.
_MISMATCH_TITLE_TERMS = (
    "director", "vp", "vice president", "head of", "chief", "cpo",
    "intern", "internship", "co-op", "junior", "associate", "entry level", "entry-level",
)

# Default JD signals that earn career-alignment credit; override per candidate
# in config.json -> search.bonus_signals ({name: [terms]}).
DEFAULT_BONUS_SIGNALS = {
    "growth": ["growth", "0-1", "0 to 1", "0-to-1", "zero to one", "zero-to-one",
               "greenfield", "incubat", "founding", "new product line", "first product manager"],
    "ai": ["ai", "llm", "llms", "genai", "generative ai", "machine learning",
           "agentic", "ai agents", "copilot", "prompt"],
}

_MULTI_LOC_RE = re.compile(r"[/;•|]|\bor\b|\bmultiple locations\b")


def _phrase_count(text, phrase):
    if not phrase:
        return 0
    return len(re.findall(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text))


def _label(score):
    if score >= 80:
        return "excellent"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    return "poor"


def _jd_blob(job):
    return _norm(f"{job.get('title') or ''}\n{job.get('description') or ''}")


def _skill_core(term):
    """'Prioritization Frameworks (RICE, MoSCoW, ICE)' -> core + paren abbrs."""
    core = _norm(re.sub(r"\s*\([^)]*\)", "", term))
    abbrs = []
    for paren in re.findall(r"\(([^)]+)\)", term):
        for a in re.split(r"[,/]", paren):
            a = _norm(a)
            if len(a) >= 3:
                abbrs.append(a)
    return core, abbrs


# ------------------------------------------------------------- dimensions

def _eval_title_seniority(job, profile, config=None):
    title = _norm(job.get("title"))
    search = (config or {}).get("search") or {}
    seniority = {_norm(t) for t in profile.get("seniority_terms", []) if t}
    targets = [_norm(t) for t in profile.get("target_titles", []) if t]
    target_blob = " ".join(targets)

    notes = []
    matched = next((t for t in targets if _has_phrase(title, t)), None)
    core_matched = None
    if not matched:
        cores = {_title_core(t, seniority) for t in targets}
        core_matched = next((c for c in sorted(cores, key=len, reverse=True)
                             if c and _has_phrase(title, c)), None)
    if matched:
        score = 90
        notes.append(f'Job title matches target title "{matched}".')
        delta = ladder_delta(title, search, profile)
        level = current_level(search, profile)
        if delta is not None and delta < 0:
            score = 78
            notes.append(f"Heads-up: this title sits {abs(delta)} rung(s) below the current "
                         f"'{level}' level on the configured title ladder — check scope/comp "
                         "before treating it as lateral.")
        elif delta:
            notes.append(f"Title is {delta} rung(s) above the current '{level}' level.")
    elif core_matched:
        score = 60
        notes.append(f'Title contains "{core_matched}" but is not an exact target-title match.')
        if any(_has_phrase(title, s) for s in seniority):
            score += 15
            notes.append("Seniority level in the title aligns with the profile.")
        else:
            notes.append("No target seniority term (senior/lead/principal/staff/group) in the title.")
    else:
        score = 15
        notes.append("Job title does not match any target title or core-title variant.")

    mismatch = next((m for m in _MISMATCH_TITLE_TERMS
                     if _has_phrase(title, m) and not _has_phrase(target_blob, m)), None)
    if mismatch:
        score -= 30
        notes.append(f'Level mismatch: title says "{mismatch}", which is outside the target band.')
    return max(0, min(100, score)), " ".join(notes)


def _eval_skills(job, profile, inventory):
    jd = _jd_blob(job)
    terms, seen = [], set()
    for term in list(profile.get("keywords", [])) + list((inventory or {}).get("skills_library", [])):
        if _norm(term) not in seen:
            seen.add(_norm(term))
            terms.append(term)
    hits = []
    for term in terms:
        core, abbrs = _skill_core(term)
        n = _phrase_count(jd, core) if len(core) > 1 else 0
        n += sum(_phrase_count(jd, a) for a in abbrs)
        if n:
            hits.append((term, n))
    weighted = sum(min(n, 3) for _, n in hits)
    score = round(100 * (1 - 0.90 ** weighted))
    hits.sort(key=lambda x: (-x[1], x[0]))
    top = [f"{t} (x{n})" for t, n in hits[:5]]
    if hits:
        notes = (f"{len(hits)} profile/menu skill terms appear in the JD. "
                 f"Highest-frequency matches: {', '.join(top)}.")
    else:
        notes = "None of the profile keywords or skills-library terms appear in the JD."
    return max(0, min(100, score)), notes, hits


def _eval_domain(job, profile, config):
    jd = _jd_blob(job)
    search = (config or {}).get("search") or {}
    domains = list(dict.fromkeys(
        [_norm(d) for d in profile.get("target_domains", []) if d]
        + [_norm(d) for d in search.get("domain_terms", []) if d]))
    dom_hits = [d for d in domains if _has_phrase(jd, d)]
    score = 100 * (1 - 0.65 ** len(dom_hits))
    notes = []
    if dom_hits:
        notes.append(f"Target-domain terms in the JD: {', '.join(dom_hits[:6])}.")
    else:
        notes.append("No target-domain terms found in the JD.")
    title_hits = [d for d in domains if _has_phrase(_norm(job.get("title")), d)]
    if title_hits:
        score += 10
        notes.append(f"Target domain named in the job title ({', '.join(title_hits[:3])}).")
    return max(0, min(100, round(score))), " ".join(notes), dom_hits


def _eval_career(job, profile, config=None):
    jd = _jd_blob(job)
    signals = ((config or {}).get("search") or {}).get("bonus_signals") or DEFAULT_BONUS_SIGNALS
    title = _norm(job.get("title"))
    score = 20
    notes = []
    if job.get("dream"):
        score += 35
        notes.append("Dream-company flag is set — high personal-mission fit.")
    title_domains = [d for d in (_norm(x) for x in profile.get("target_domains", []) if x)
                     if d and _has_phrase(title, d)]
    if title_domains:
        score += 20
        notes.append(f"Target domain in the job title itself ({', '.join(title_domains[:3])}).")
    for name, terms in signals.items():
        hits = [t for t in terms if _has_phrase(jd, _norm(t))]
        if len(hits) >= 2:
            score += 15
            notes.append(f"{name.capitalize()} signals in the JD ({', '.join(hits[:4])}).")
        elif hits:
            score += 7
            notes.append(f"Some {name} signal in the JD ({hits[0]}).")
    if not notes:
        notes.append("No dream flag, target-domain title, or bonus signals — a lateral move at best.")
    return max(0, min(100, score)), " ".join(notes)


# --------------------------------------------------------------- location

def _eval_location(job, profile, search):
    """PASS/FLAG/FAIL against the candidate's home base (remote/hybrid-at-home
    OK; relocation per profile.screener_answers.willing_to_relocate)."""
    loc = _norm(job.get("location"))
    desc = _norm(job.get("description"))
    home_terms = matching_home_terms(profile, search)
    home = profile.get("location") or profile.get("city") or "the home location"
    relocate_ok = _norm((profile.get("screener_answers") or {}).get("willing_to_relocate")).startswith("y")
    remote = bool(job.get("remote")) or "remote" in loc
    at_home = any(_has_phrase(loc, t) for t in home_terms)
    home_in_desc = any(_has_phrase(desc, t) for t in home_terms)
    multi = bool(_MULTI_LOC_RE.search(loc))

    if remote:
        own = set(home_terms) | set(home_country_terms(profile))
        pinned = [c for c in ELSEWHERE_REMOTE if c not in own and _has_phrase(loc, c)]
        if pinned:
            return "FLAG", (f'Role is remote but pinned to "{pinned[0]}" in the location field — '
                            f"verify it is open to {home}-based candidates.")
        return "PASS", f"Role is remote (or lists remote), compatible with the {home} + remote-OK profile."
    if not home_terms:
        return "FLAG", "No home location in the profile (set city/state or search.locations) — verify the location manually."
    if at_home and not multi:
        return "PASS", f'Location "{job.get("location")}" matches the {home} profile.'
    if at_home and multi:
        return "FLAG", (f'Location "{job.get("location")}" lists multiple cities including {home} — '
                        "confirm the role can be based there.")
    if not loc:
        if home_in_desc or "remote" in desc:
            return "FLAG", f"No location field, but the description mentions {home}/remote — verify before applying."
        return "FLAG", f"No location listed and no {home}/remote mention in the description — verify before applying."
    if relocate_ok:
        return "FLAG", f'Location "{job.get("location")}" is not {home}; profile allows relocation — confirm before applying.'
    # Clearly a non-home location from here down.
    if "remote" in desc:
        return "FLAG", (f'Location "{job.get("location")}" is not {home}, but the description mentions '
                        "remote — verify whether remote is actually offered for this role.")
    if "hybrid" in loc or "hybrid" in desc:
        return "FAIL" if "relocat" in desc else "FLAG", (
            f'Hybrid role based in "{job.get("location")}" (not {home}) — hybrid elsewhere '
            f"conflicts with the {home} base unless a local office is an option.")
    reason = f'Single onsite location "{job.get("location")}" away from {home} — profile has relocation set to No.'
    if "on-site" in desc or "onsite" in desc or "on site" in desc or "relocat" in desc:
        reason += " Description reinforces onsite/relocation expectations."
    return "FAIL", reason


# ------------------------------------------------------------ honest gaps

_REQ_HEADING_RE = re.compile(
    r"qualifications|requirements|what you.{0,3}ll need|what you will need|you have"
    r"|looking for|must have|who you are|about you|what we need|what we value", re.I)
_BULLET_LINE_RE = re.compile(r"^\s*[-•*·–]\s*(.+?)\s*$")
# Encouragement/EEO boilerplate that lives under requirements headings but isn't a requirement.
_REQ_BOILERPLATE_RE = re.compile(
    r"encourage you|check all the boxes|equal opportunit|we celebrate|reasonable accommodat"
    r"|apply anyway|still apply", re.I)
# Sentence-level requirement signals for paragraph-style JDs with no bullet lists.
_REQ_SENTENCE_RE = re.compile(
    r"\b\d+\+?\s*years?\b|\bexperience (with|in|building|leading|shipping)\b|\bproficien"
    r"|\bdegree in\b|\bfamiliarity with\b|\bexpertise (with|in)\b|\btrack record\b"
    r"|\bhiring .{0,40}who\b|\bmust (be|have)\b", re.I)


def _requirement_lines(description):
    """Requirement fragments from the JD: lines under a qualifications-style
    heading; fallback to any bulleted line mentioning years/experience/skills."""
    lines = (description or "").splitlines()
    reqs, in_req = [], False
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        bullet = _BULLET_LINE_RE.match(raw)
        is_heading = not bullet and len(s.split()) <= 10 and (
            s.isupper() or s.endswith(":") or _REQ_HEADING_RE.search(s))
        if is_heading:
            in_req = bool(_REQ_HEADING_RE.search(s))
            continue
        if in_req:
            text = bullet.group(1) if bullet else (s if len(s) > 30 else None)
            if text:
                reqs.append(text.strip())
        if len(reqs) >= 30:
            break
    if not reqs:
        for raw in lines:
            bullet = _BULLET_LINE_RE.match(raw)
            if bullet and re.search(r"\byears?\b|\bexperience\b|\bskills?\b", bullet.group(1), re.I):
                reqs.append(bullet.group(1).strip())
    if not reqs:
        # Paragraph-style JD with no bullets at all: requirement-shaped sentences.
        for sent in re.split(r"(?<=[.!?])\s+", " ".join((description or "").split())):
            if 30 <= len(sent) <= 300 and _REQ_SENTENCE_RE.search(sent):
                reqs.append(sent.strip())
            if len(reqs) >= 12:
                break
    return [r for r in reqs if not _REQ_BOILERPLATE_RE.search(r)]


def _known_terms(profile, config, inventory):
    search = (config or {}).get("search") or {}
    raw = (list(profile.get("keywords", [])) + list(profile.get("target_titles", []))
           + list(profile.get("target_domains", [])) + list(profile.get("seniority_terms", []))
           + list(search.get("domain_terms", [])) + list(search.get("keywords", [])))
    for term in (inventory or {}).get("skills_library", []):
        core, abbrs = _skill_core(term)
        raw.append(core)
        raw.extend(abbrs)
    return [t for t in {_norm(x) for x in raw} if t and len(t) > 1]


def _honest_gaps(description, profile, config, inventory, max_n=6):
    known = _known_terms(profile, config, inventory)
    gaps = []
    for req in _requirement_lines(description):
        n = _norm(req)
        if any(_has_phrase(n, term) for term in known):
            continue
        frag = req if len(req) <= 200 else req[:197].rstrip() + "..."
        gaps.append(frag)
        if len(gaps) >= max_n:
            break
    return gaps


# ----------------------------------------------------------------- public

def evaluate(job, profile, config, inventory):
    search = (config or {}).get("search") or {}
    t_score, t_notes = _eval_title_seniority(job, profile, config)
    s_score, s_notes, skill_hits = _eval_skills(job, profile, inventory)
    d_score, d_notes, dom_hits = _eval_domain(job, profile, config)
    c_score, c_notes = _eval_career(job, profile, config)
    verdict, loc_notes = _eval_location(job, profile, search)
    gaps = _honest_gaps(job.get("description"), profile, config, inventory)

    dimensions = {
        "title_seniority": {"score": t_score, "label": _label(t_score), "notes": t_notes},
        "skills": {"score": s_score, "label": _label(s_score), "notes": s_notes},
        "domain_experience": {"score": d_score, "label": _label(d_score), "notes": d_notes},
        "career_alignment": {"score": c_score, "label": _label(c_score), "notes": c_notes},
    }

    strengths = []
    title = _norm(job.get("title"))
    if t_score >= 60:
        strengths.append(f'Title fit: "{job.get("title")}" matches a target title.')
    for term, n in skill_hits[:3]:
        strengths.append(f'JD asks for "{term}" ({n}x) — directly evidenced in the line menu.')
    if dom_hits:
        strengths.append(f"Domain overlap: {', '.join(dom_hits[:4])}.")
    if job.get("dream"):
        strengths.append("Dream company — motivation and domain passion are easy to make credible.")
    strengths = strengths[:5]

    weighted = sum(dimensions[k]["score"] * w for k, w in DIMENSION_WEIGHTS.items())
    if weighted >= 70:
        recommendation = "strong"
    elif weighted >= 45:
        recommendation = "moderate"
    else:
        recommendation = "weak"
    if verdict == "FAIL":
        recommendation = "weak"

    first = (f"{recommendation.capitalize()} fit ({round(weighted)}/100 weighted): "
             f"title {t_score}, skills {s_score}, domain {d_score}, career {c_score}.")
    if verdict == "FAIL":
        first = (f"Weak fit — location is a hard blocker ({round(weighted)}/100 weighted otherwise): "
                 f"title {t_score}, skills {s_score}, domain {d_score}, career {c_score}.")
    if strengths:
        second = f"Strongest angle: {strengths[0]}"
    else:
        second = "No standout strengths surfaced by rule-based matching."
    if gaps:
        second += f" Honest gaps: {len(gaps)} requirement(s) with no profile/menu coverage — review before applying."
    elif verdict != "PASS":
        second += f" Location check: {verdict}."

    return {
        "mode": "basic",
        "dimensions": dimensions,
        "location": {"verdict": verdict, "notes": loc_notes},
        "strengths": strengths,
        "gaps": gaps,
        "recommendation": recommendation,
        "summary": f"{first} {second}",
    }
