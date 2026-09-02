"""Cover letter generation.

`generate(job, profile, tailored_resume, config)` ->
    {"mode": "llm"|"basic", "markdown": str, "needs_editing": bool}

LLM mode is grounded ONLY in resume facts + the JD (no fabricated anecdotes,
no numbers absent from the sources; validated). If the user supplies a letter
of their own at config.json -> materials.cover_letter_reference, it is used as
a voice/structure exemplar (never as a source of facts). Basic mode fills a
respectable deterministic template from profile facts mapped to JD keywords
and is flagged `needs_editing: true`.
"""
import os
import re

from backend import voice_check
from backend.app import materials_path
from backend.profile_store import display_name, signature

_NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")


def _numbers(text):
    return {m.group(0).replace(",", "") for m in _NUM_RE.finditer(str(text or ""))}


def _resume_facts_text(profile, tailored_resume):
    parts = [str(v) for v in (profile.get("facts") or {}).values()]
    parts.append(profile.get("current_title") or "")
    parts.append(profile.get("current_company") or "")
    for edu in profile.get("education") or []:
        parts.append(f"{edu.get('school')} {edu.get('degree')} {edu.get('years')}")
    tr = tailored_resume or {}
    parts.append(re.sub(r"<[^>]+>", "", tr.get("summary_html") or ""))
    for role in tr.get("roles", []):
        parts.append(role.get("company") or "")
        for t in role.get("titles", []):
            parts.append(f"{t.get('title')} {t.get('dates')}")
        for b in role.get("bullets", []):
            parts.append(re.sub(r"<[^>]+>", "", b.get("html") or ""))
    for b in tr.get("earlier_impact", []):
        parts.append(re.sub(r"<[^>]+>", "", b.get("html") or ""))
    return "\n".join(p for p in parts if p)


def _role_phrase(profile):
    title = profile.get("current_title") or ""
    company = profile.get("current_company") or ""
    if title and company:
        return f"{title} at {company}"
    return title or company or "a product professional"


# ------------------------------------------------------------- exemplar

def load_reference_letter(config=None):
    """The user's own letter (materials.cover_letter_reference), or "" when
    absent or still the unfilled template."""
    path = materials_path("cover_letter_reference", config)
    if not path or not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # The shipped template keeps instructions above a '---' rule.
    if "\n---\n" in text:
        text = text.split("\n---\n", 1)[1]
    text = text.strip()
    if not text or "[Your letter here" in text or len(text.split()) < 80:
        return ""
    return text


# ------------------------------------------------------------------ LLM mode

# Rules distilled from cover_letter_best_practices.md: hook-first opening,
# 4-paragraph structure, one story carrying the value paragraph, JD-phrase
# mirroring, confident low-friction close, no clichés, <= 300 words, never
# restate the resume wholesale.
_DEFAULT_STRUCTURE = """STRUCTURE (4 short paragraphs, 300 words MAXIMUM, markdown plain text):
1. Hook (2-3 sentences): name the exact role title and company; open with a flagship metric or a pointed problem-framing hook. NEVER "I am writing to apply..." or "I am a results-driven...".
2. Value (3-5 sentences): ONE specific story from the provided resume facts, told as context -> action -> outcome -> why it transfers to this role. Mirror 2-3 exact phrases from the job description.
3. Fit (2-4 sentences): a belief about where the company/role is going, grounded ONLY in what the job description itself says. Echo the company name.
4. Close (1-2 sentences): confident and low-friction (e.g. a conversation about the first 90 days)."""

_EXEMPLAR_STRUCTURE = """STRUCTURE: match the REFERENCE LETTER below. Reproduce its paragraph count, paragraph order, approximate length ({words} words, plus or minus 15%), sentence rhythm, and tone. It was written by the candidate and is the voice to imitate.
The reference letter is a STYLE exemplar only: do NOT reuse any fact, number, employer, product, or anecdote from it unless that fact also appears in RESUME FACTS. Replace every company-specific passage with content for {company} drawn from the JOB DESCRIPTION."""


def _system_prompt(profile, reference):
    if reference:
        structure = _EXEMPLAR_STRUCTURE.replace("{words}", str(len(reference.split())))
    else:
        structure = _DEFAULT_STRUCTURE
    return f"""You write a cover letter for {display_name(profile)} ({_role_phrase(profile)}). Follow these rules exactly:

{structure}
Sign off "Sincerely,\\n{signature(profile)}".

GROUNDING (hard rules):
- Use ONLY facts present in the provided RESUME FACTS and JOB DESCRIPTION. No fabricated anecdotes, customers, products, conversations, or experiences.
- NEVER introduce a number, metric, employer, title, date, or technology not present in those sources.
- Greeting: "Dear {{company}} Hiring Team," unless the JD names a hiring manager.

VOICE: confident, specific, conversational-professional. Forbidden: "results-driven", "passionate", "rockstar", "team player", "dynamic", "synergy", "I believe I would be a great fit", em-dashes. No headers/addresses (a letterhead is added at render time).

Output ONLY the letter markdown. No commentary.""" + voice_check.VOICE_RULES_PROMPT


def _llm_generate(job, profile, config, facts_text):
    import anthropic  # lazy import; only needed in LLM mode

    reference = load_reference_letter(config)
    company = job.get("company") or "the company"
    system = _system_prompt(profile, reference).replace("{company}", company)
    user = f"""JOB DESCRIPTION
Title: {job.get('title')}
Company: {company}
{(job.get('description') or '')[:6000]}

RESUME FACTS (the ONLY permissible source of claims about the candidate):
{facts_text[:6000]}"""
    if reference:
        user += f"""

REFERENCE LETTER (style exemplar only; its facts are NOT permitted unless also in RESUME FACTS):
{reference[:5000]}"""

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=config.get("tailoring", {}).get("model", "claude-opus-5"),
        max_tokens=8000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    if resp.stop_reason == "refusal":
        raise ValueError("model declined the cover letter request")
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    max_words = int(len(reference.split()) * 1.35 + 50) if reference else 380
    if not text or len(text.split()) > max_words:
        raise ValueError("LLM cover letter empty or far over length")
    # Number validation: every numeric token must trace to resume facts or JD.
    allowed = _numbers(facts_text) | _numbers(job.get("description")) | _numbers(job.get("title"))
    if not _numbers(text) <= allowed:
        raise ValueError("LLM cover letter introduced numbers not present in sources")
    return text


# ---------------------------------------------------------------- basic mode

_STOP = frozenset("a an the and or of to in for with on at by from as is are was were "
                  "be been this that you we our your their will would have has".split())


def _pick_facts(profile, jd_text, n=3):
    """Rank profile.facts by keyword overlap with the JD."""
    jd_tokens = set(w for w in re.findall(r"[a-z0-9]+", (jd_text or "").lower()) if w not in _STOP)
    scored = []
    for key, fact in (profile.get("facts") or {}).items():
        if not str(fact or "").strip():
            continue
        blob = f"{key.replace('_', ' ')} {fact}".lower()
        toks = set(re.findall(r"[a-z0-9]+", blob)) - _STOP
        scored.append((len(toks & jd_tokens), key, str(fact)))
    scored.sort(key=lambda t: -t[0])
    return [(k, f) for _, k, f in scored[:n]]


def _fact_sentence(fact):
    """Facts written as full sentences stand alone; fragments get a lead-in."""
    fact = fact.strip().rstrip(".")
    if re.match(r"^[A-Z]", fact) and len(fact.split()) >= 6 and re.search(r"\b(I|my|we|our)\b", fact):
        return fact + "."
    return f"One proof point: {fact}."


def _basic_generate(job, profile):
    company = job.get("company") or "your company"
    title = job.get("title") or "this role"
    jd = f"{job.get('title') or ''} {job.get('description') or ''}"
    facts = _pick_facts(profile, jd, n=3)

    proof1 = _fact_sentence(facts[0][1]) if facts else ""
    proof2 = " ".join(_fact_sentence(f) for _, f in facts[1:3])

    return f"""Dear {company} Hiring Team,

The {title} role at {company} maps directly to the work I do today as {_role_phrase(profile)}.

{proof1} That work required exactly the mix this role calls for: owning a roadmap end to end, aligning cross-functional partners, and turning plans into measurable outcomes.

{proof2} I'd bring the same operating discipline and customer-first perspective to {company}.

I'd welcome a conversation about the role and how I'd approach the first 90 days. Thanks for your time and consideration.

Sincerely,
{signature(profile)}"""


# -------------------------------------------------------------------- public

def generate(job, profile, tailored_resume, config):
    facts_text = _resume_facts_text(profile, tailored_resume)
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            md = _llm_generate(job, profile, config, facts_text)
            return {"mode": "llm", "markdown": md, "needs_editing": False}
        except Exception:
            pass  # fall through to deterministic template
    return {"mode": "basic", "markdown": _basic_generate(job, profile), "needs_editing": True}
