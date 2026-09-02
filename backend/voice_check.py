"""Voice linter + scrubber. Source of truth: the writing voice guide at
config.json -> materials.voice_guide (materials/guides/writing_voice_guide.md),
built from AI-tells research and grading-panel rounds.

check(text, kind)  -> findings list, run on EVERY tailoring/edit/generation pass
scrub(text)        -> deterministic cleanup applied to INITIAL drafts (both modes)
VOICE_RULES_PROMPT -> concise rules injected into LLM generation prompts
"""
import re
import statistics

VOICE_RULES_PROMPT = """
VOICE RULES (violations make the output unusable; see writing_voice_guide.md):
- NEVER use em-dashes. Use commas, colons, semicolons, or periods.
- Banned AI-tell words: delve, showcase, pivotal, tapestry, testament, realm,
  intricate, meticulous, boasts, crucial, foster, leverage, seamless, robust,
  "evolving landscape", "underscores", "in today's", "results-driven".
- No meta/throat-clearing ("let me be direct", "I am writing to express").
- No false-contrast shapes ("it's not X, it's Y", "not just X").
- No aphorism zingers or crafted punchlines; plain statements only.
- No empty connective clauses; every clause carries a fact or claim.
- Cover letters use contractions (I'm, I'd, I've); vary sentence length;
  problem -> plan -> proof architecture.
- Resume bullets start with an action verb (present tense for ongoing, past
  for completed). Numbers must trace to sources and stay consistent across
  the resume and cover letter (years, headcounts, led-vs-helped verbs).
- Never echo the target JD's own phrasing back verbatim.
"""

_BANNED = [
    (r"\bdelv\w+", "delve"), (r"\bshowcas\w+", "showcase"), (r"\bpivotal\b", "pivotal"),
    (r"\btapestr\w+", "tapestry"), (r"\btestament\b", "testament"), (r"\brealm\b", "realm"),
    (r"\bintricate\w*", "intricate"), (r"\bmeticulous\w*", "meticulous"), (r"\bboasts?\b", "boasts"),
    (r"\bcrucial\b", "crucial"), (r"\bfoster(?:s|ing|ed)?\b", "foster"),
    (r"\bleverag\w+", "leverage"), (r"\bseamless\w*", "seamless"), (r"\brobust\w*", "robust"),
    (r"evolving landscape", "evolving landscape"), (r"\bunderscores?\b", "underscores"),
    (r"in today's", "in today's"), (r"results-driven", "results-driven"),
    (r"detail-oriented", "detail-oriented"), (r"passionate professional", "passionate professional"),
    (r"honest gap", "honest gap (cliché)"),
]
_META = [
    r"let me be (?:direct|clear|honest)", r"i am writing to", r"i'm writing to",
    r"it'?s important to note", r"take this opportunity", r"please find (?:my|attached)",
]
_FALSE_CONTRAST = [
    r"(?:it'?s|is|are)\s+not\s+(?:just\s+|about\s+)?[^.;]{2,50}[,;]\s*(?:it'?s|but|instead)",
    r"\bnot just\b",
]
# Possessives must NOT count as contractions: "Acme's" is not "I'm", and a
# single possessive was enough to defeat the zero-contractions check entirely.
# 't/'ve/'m/'re/'ll/'d are contractions on any stem; bare 's only counts after
# the handful of words where it means "is"/"has".
_CONTRACTION = re.compile(
    r"\b(?:\w+'(?:t|ve|m|re|ll|d)"
    r"|(?:it|that|there|here|he|she|who|what|let|one|nothing|something|everything)'s)\b",
    re.I)


def _plain(text):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or ""))


def check(text, kind="resume"):
    """-> [{rule, severity ('flag'|'warn'), detail}]. `kind`: resume|cover_letter."""
    t = _plain(text)
    low = t.lower()
    findings = []

    n = (text or "").count("—")
    if n:
        findings.append({"rule": "em-dash", "severity": "flag", "detail": f"{n} em-dash(es) present"})
    for pat, name in _BANNED:
        if re.search(pat, low):
            findings.append({"rule": "ai-tell-word", "severity": "flag", "detail": name})
    for pat in _META:
        m = re.search(pat, low)
        if m:
            findings.append({"rule": "meta-statement", "severity": "flag", "detail": m.group(0)})
    for pat in _FALSE_CONTRAST:
        m = re.search(pat, low)
        if m:
            findings.append({"rule": "false-contrast", "severity": "flag", "detail": m.group(0)[:60]})

    sentences = [s for s in re.split(r"[.!?]+\s", t) if len(s.split()) >= 3]
    if kind == "cover_letter":
        if not _CONTRACTION.search(t):
            findings.append({"rule": "no-contractions", "severity": "flag",
                            "detail": "zero contractions reads as AI; add I'm/I'd/I've"})
        if len(sentences) >= 6:
            lens = [len(s.split()) for s in sentences]
            if statistics.pstdev(lens) / max(statistics.mean(lens), 1) < 0.30:
                findings.append({"rule": "uniform-rhythm", "severity": "warn",
                                "detail": "sentence lengths too uniform (low burstiness)"})

    tricolons = re.findall(r",\s+[^,;.]{2,40},\s+and\s+", t)
    if len(tricolons) > 3:
        findings.append({"rule": "tricolon-density", "severity": "warn",
                        "detail": f"{len(tricolons)} three-item lists; break some chains"})
    return findings


def scrub(text):
    """Deterministic cleanup for INITIAL drafts: em-dashes out (menu source text
    is em-dash-heavy). Comma is the safe default join; the article/noun-aware
    replacements in tailoring.apply_translations run before this."""
    if not text:
        return text
    text = re.sub(r"\s*—\s*", ", ", text)
    return re.sub(r"\s*–\s*", ", ", text)  # en-dash too
