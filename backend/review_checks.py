"""Deterministic draft critique — a rule-based stand-in for a reviewer agent.

critique(job, resume_structure, cover_letter_md, inventory, profile) ->
    {"findings": [{"severity": "high"|"medium"|"info", "category", "message"}],
     "counts": {"high": n, "medium": n, "info": n}}

No LLM, no network. A future LLM reviewer can append findings to the same
shape (category "llm-review"); the counts contract stays identical.
"""
import re

from backend import line_menu
from backend.evaluation import _requirement_lines
from backend.tailoring import _tokens

_TAG_RE = re.compile(r"<[^>]+>")

WEAK_OPENERS = ("responsible for", "worked on", "helped", "participated", "assisted", "involved in")

BANNED_CL_OPENERS = ("i am writing to apply", "to whom it may concern")
GENERIC_CL_PHRASES = (
    "i believe my skills", "perfect fit", "team player", "fast-paced environment",
    "passionate about", "proven track record", "hit the ground running",
    "thank you for your consideration", "unique blend of", "wealth of experience",
)

# JD tokens too generic to be worth mirroring on a resume.
_GENERIC_JD_TOKENS = frozenset(
    "experience experienced years team teams work working works ability able strong excellent "
    "required requirements preferred plus bonus including include help skills skill knowledge "
    "role roles company candidates candidate qualifications responsibilities day-to-day every "
    "employees benefits equal opportunity applicants applicant status best great join our-team "
    "million customers world people position duties assigned".split()
)


def _plain(html):
    s = _TAG_RE.sub("", str(html or ""))
    return s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()


def _resume_bullets(structure):
    """[(plain_text, source_ref, slot_label), ...] across all bullet slots."""
    out = []
    for i, role in enumerate(structure.get("roles") or []):
        label = role.get("company") or f"role {i + 1}"
        for b in role.get("bullets") or []:
            out.append((_plain(b.get("html")), b.get("source_ref") or "?", label))
    for b in structure.get("earlier_impact") or []:
        out.append((_plain(b.get("html")), b.get("source_ref") or "?", "earlier impact"))
    projects = structure.get("projects") or {}
    for b in projects.get("bullets") or []:
        out.append((_plain(b.get("html")), b.get("source_ref") or "?", "projects"))
    return out


def _flat_resume_text(structure, bullets):
    parts = [structure.get("subtitle") or "", _plain(structure.get("summary_html")),
             _plain(structure.get("skills_html"))]
    parts += [t for t, _, _ in bullets]
    return "\n".join(parts)


def _jd_top_terms(job, n=10):
    """Top requirement-weighted JD terms (requirement-section tokens count 2x)."""
    desc = job.get("description") or ""
    req_tokens = set()
    for line in _requirement_lines(desc):
        req_tokens.update(_tokens(line))
    freq = {}
    for t in _tokens(f"{job.get('title') or ''}\n{desc}"):
        if len(t) < 3 or t.isdigit() or t in _GENERIC_JD_TOKENS:
            continue
        freq[t] = freq.get(t, 0) + 1
    ranked = sorted(freq.items(),
                    key=lambda kv: (-(kv[1] * (2 if kv[0] in req_tokens else 1)), kv[0]))
    return [t for t, _ in ranked[:n]]


def critique(job, resume_structure, cover_letter_md, inventory, profile):
    findings = []
    add = lambda sev, cat, msg: findings.append(
        {"severity": sev, "category": cat, "message": msg})

    bullets = _resume_bullets(resume_structure or {})
    flat = _flat_resume_text(resume_structure or {}, bullets)
    resume_tokens = set(_tokens(flat))

    # 1. missed-keywords: top requirement-weighted JD terms absent from the resume.
    top_terms = _jd_top_terms(job, n=25)
    missing = [t for t in top_terms if t not in resume_tokens][:10]
    if missing:
        sev = "high" if len(missing) >= 6 else "medium"
        add(sev, "missed-keywords",
            f"Top JD terms missing from the resume: {', '.join(missing)}. "
            "Mirror the ones that are true — swap in line-menu bullets or skills tokens that use them.")

    # 2. weak-verbs: passive/dilute bullet openers.
    for text, ref, label in bullets:
        low = text.lower().lstrip("\"'")
        opener = next((w for w in WEAK_OPENERS if low.startswith(w)), None)
        if opener:
            add("medium", "weak-verbs",
                f'Bullet {ref} ({label}) opens with "{opener}" — lead with the outcome verb instead '
                f'(e.g. "Drove", "Shipped", "Cut"): "{text[:90]}..."')

    # 3. verb-repetition: same leading verb on 3+ bullets.
    leads = {}
    for text, ref, _ in bullets:
        m = re.match(r"[^A-Za-z]*([A-Za-z][A-Za-z-]*)", text)
        if m:
            leads.setdefault(m.group(1).lower(), []).append(ref)
    for verb, refs in sorted(leads.items()):
        if len(refs) >= 3:
            add("medium", "verb-repetition",
                f'{len(refs)} bullets start with "{verb}" ({", ".join(refs)}) — vary the leading verbs '
                "so the scan doesn't read as a template.")

    # 4. metric-free bullets (info).
    metric_free = [(ref, label) for text, ref, label in bullets
                   if not line_menu.extract_metrics(text)]
    if metric_free:
        refs = ", ".join(f"{r} ({l})" for r, l in metric_free[:8])
        add("info", "metric-free",
            f"{len(metric_free)} bullet(s) carry no metric: {refs}. Fine in moderation, but each "
            "metric-free line should earn its place with a concrete noun (system, artifact, decision).")

    # 5. overlong bullets.
    for text, ref, label in bullets:
        if len(text) > 280:
            add("medium", "overlong-bullet",
                f"Bullet {ref} ({label}) is {len(text)} characters — over the 280-char scan limit. "
                "Split it or cut subordinate clauses; long bullets get skipped and cost 1-page space.")

    # 6. skills-mirroring: fewer than 3 bolded (JD-mirrored) skills.
    strong_count = str((resume_structure or {}).get("skills_html") or "").count("<strong>")
    if strong_count < 3:
        add("high", "skills-mirroring",
            f"Only {strong_count} skill token(s) mirror the JD (bolded via <strong>). Re-tailor or "
            "reorder the skills line so at least 3 JD-relevant skills lead it.")

    # 7. Cover letter checks (only when a letter exists).
    cl = str(cover_letter_md or "").strip()
    if cl:
        low = cl.lower()
        words = len(re.findall(r"\S+", cl))
        if words > 320:
            add("medium", "cover-letter",
                f"Cover letter is {words} words — over the 320-word ceiling. Cut to 3 short paragraphs; "
                "recruiters skim.")
        company = str(job.get("company") or "").strip()
        if company and company.lower() not in low:
            add("high", "cover-letter",
                f'Company name "{company}" never appears in the cover letter — it reads as a generic blast.')
        title = str(job.get("title") or "").strip()
        if title:
            variants = {title.lower(), title.lower().replace(",", ""),
                        re.split(r"[,–—-]", title)[0].strip().lower()}
            if not any(v and v in low.replace(",", "") for v in variants):
                add("medium", "cover-letter",
                    f'Role title "{title}" is not referenced — name the exact role in the first paragraph.')
        for opener in BANNED_CL_OPENERS:
            if opener in low:
                add("high", "cover-letter",
                    f'Banned opener "{opener}" found — replace with a specific first line about '
                    "the company's problem and your matching result.")
        generic = [p for p in GENERIC_CL_PHRASES if p in low]
        if generic:
            add("medium", "cover-letter",
                f"Generic template phrases found: {', '.join(generic)}. Replace each with a "
                "specific fact from the resume or the JD.")

    counts = {"high": 0, "medium": 0, "info": 0}
    for f in findings:
        counts[f["severity"]] += 1
    return {"findings": findings, "counts": counts}
