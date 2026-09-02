"""Interview-prep pack builder — deterministic, sourced only from stored data.

build_prep(job, profile, config, inventory, resume_structure, posting_text) -> markdown

Everything in the pack traces to (a) the tailored resume actually submitted,
(b) the line-menu inventory, (c) the stored posting text, or (d) a curated
static PM question bank. Company facts are ONLY extracted from the posting
text — never invented; external research is an explicit manual TODO.
"""
import re

from backend import line_menu
from backend.tailoring import _tokens

_TAG_RE = re.compile(r"<[^>]+>")


def _plain(html):
    s = _TAG_RE.sub("", str(html or ""))
    return s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()


def _fragment(text, n=90):
    text = text.strip()
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + "..."


def _selected_bullets(structure):
    """[(plain_text, source_ref, slot_label)] for every bullet on the tailored resume."""
    out = []
    for i, role in enumerate((structure or {}).get("roles") or []):
        label = role.get("company") or f"role {i + 1}"
        for b in role.get("bullets") or []:
            out.append((_plain(b.get("html")), b.get("source_ref") or "baseline", label))
    for b in (structure or {}).get("earlier_impact") or []:
        out.append((_plain(b.get("html")), b.get("source_ref") or "baseline", "earlier impact"))
    projects = (structure or {}).get("projects") or {}
    for b in projects.get("bullets") or []:
        out.append((_plain(b.get("html")), b.get("source_ref") or "baseline",
                    projects.get("heading") or "projects"))
    return out


def _backup_stories(inventory, used_refs, jd_token_set, n=4):
    """Strongest unused line-menu bullets (role + project sections) as backup STAR stories."""
    used = {r.lstrip("§") for r in used_refs}
    pool = []
    for sec in (inventory or {}).get("sections", []):
        if sec["id"] not in ("3", "4", "5", "6", "7", "17"):
            continue
        for b in sec["bullets"]:
            if b["id"] in used:
                continue
            overlap = len(set(_tokens(b["text"])) & jd_token_set)
            strength = overlap + min(len(b.get("metrics", [])), 3)
            pool.append((strength, b))
    pool.sort(key=lambda x: -x[0])
    return [b for _, b in pool[:n]]


# Curated static PM question bank, organized by interview stage.
_STATIC_QUESTIONS = [
    ("Recruiter screen", [
        "Tell me about yourself / walk me through your background in 2 minutes.",
        "Why are you looking to leave your current company?",
        "Why this company, specifically?",
        "What are your compensation expectations?",
        "What's your timeline — are you interviewing elsewhere?",
    ]),
    ("Hiring manager", [
        "Walk me through the product you're most proud of shipping, end to end.",
        "Tell me about a time you disagreed with engineering (or a stakeholder) and how it resolved.",
        "How do you prioritize when everything is a P0? Walk through a real example.",
        "Tell me about a launch that went wrong. What did you change afterward?",
        "How do you work with compliance, legal, or risk partners on a regulated product?",
    ]),
    ("Product case", [
        "How would you improve one of our core product flows? Pick one and go deep.",
        "Design a feature for a customer segment we don't serve well today.",
        "What metrics would you set for this product area, and what would you watch weekly?",
        "Conversion in a key funnel dropped 10% week-over-week. How do you diagnose it?",
    ]),
    ("Final round", [
        "Where do you want to grow in the next 2-3 years?",
        "What would you do in your first 90 days here?",
        "Why should we hire you over someone with direct domain experience?",
    ]),
]

# Questions-to-ask pool: (trigger keyword in JD, question). Matched first, then defaults.
_ASK_POOL = [
    ("payment", "Where is the biggest friction in the money-in / money-out experience today, and what's been tried?"),
    ("compliance", "How do product and compliance/legal work together day to day — embedded partners or review gates?"),
    ("regulat", "Which regulatory constraint most shapes the roadmap right now?"),
    ("roadmap", "What are the top 2-3 roadmap priorities for this team over the next 12 months?"),
    ("metric", "Which single metric matters most to this team right now, and where is it today?"),
    ("ai", "How is the team using AI/LLMs today — in the product itself, or in how you build?"),
    ("growth", "Which growth levers have actually worked, and which are still unproven bets?"),
    ("experiment", "What does the experimentation stack look like — who designs and reads A/B tests?"),
    ("platform", "How do platform priorities get balanced against surface-level feature asks?"),
    ("stakeholder", "Which partner teams will this role spend the most time with in a normal week?"),
    ("fraud", "How is the fraud/risk tradeoff owned — is it this PM's number or a partner team's?"),
    ("scale", "What breaks first as volume scales — systems, process, or decision-making?"),
]
_ASK_DEFAULTS = [
    "What does success look like for this role at 6 and 12 months?",
    "What's the hardest problem this team is carrying into next quarter?",
    "How do decisions get made when PM and engineering disagree on scope?",
    "What do the strongest PMs here do differently from the merely good ones?",
    "How is the team structured, and who would I work with daily?",
    "What made the last person in this seat successful (or not)?",
]


def _company_paragraphs(posting_text, company):
    """Paragraphs of stored posting text that state facts about the company.
    ONLY source of company notes — nothing is invented."""
    if not posting_text:
        return []
    company_low = str(company or "").lower()
    out = []
    for para in re.split(r"\n\s*\n", posting_text):
        p = " ".join(para.split())
        if not p or len(p) < 60:
            continue
        low = p.lower()
        about = company_low and low.startswith(f"about {company_low}")
        facty = company_low and company_low in low and re.search(
            r"\bfounded\b|\bmission\b|\bheadquarter|\bcustomers\b|\bmillion\b|\bbillion\b"
            r"|\bleader\b|\blargest\b|\bwe are\b|\bour team\b", low)
        if about or facty:
            out.append(p if len(p) <= 600 else p[:597] + "...")
        if len(out) >= 3:
            break
    return out


def build_prep(job, profile, config, inventory, resume_structure, posting_text):
    company = job.get("company") or "Unknown company"
    title = job.get("title") or "Unknown role"
    jd_set = set(_tokens(f"{title}\n{job.get('description') or ''}"))
    bullets = _selected_bullets(resume_structure)
    menu_bullets = [(t, r, l) for t, r, l in bullets if r != "baseline"]

    md = []
    md.append(f"# Interview Prep — {title} @ {company}")
    md.append("")
    md.append(f"- **Company:** {company}")
    md.append(f"- **Role:** {title}")
    md.append(f"- **Status:** {job.get('status') or 'unknown'}")
    md.append(f"- **Posting:** {job.get('url') or 'n/a'}")
    md.append("")

    # ---- 1. What they read ----
    md.append("## What they read")
    md.append("")
    md.append("The interviewer's only picture of you is the tailored resume below. Own every line.")
    md.append("")
    if bullets:
        for text, ref, label in bullets:
            md.append(f"- {text} *({ref}, {label})*")
    else:
        md.append("- (No tailored resume structure available — run Tailor before prepping.)")
    metrics = []
    for text, _, _ in bullets:
        for m in line_menu.extract_metrics(text):
            if m not in metrics:
                metrics.append(m)
    md.append("")
    md.append("**Know these numbers cold** (every metric on the page — expect to be asked about each):")
    md.append("")
    md.append("- " + " · ".join(metrics) if metrics else "- (no metrics found on the tailored resume)")
    md.append("")

    # ---- 2. STAR bank ----
    md.append("## STAR bank")
    md.append("")
    md.append("One practice prompt per bullet you submitted — write out Situation / Task / Action / Result for each:")
    md.append("")
    star_source = menu_bullets or bullets
    for text, ref, _ in star_source:
        md.append(f'- **Story behind:** "{_fragment(text)}" ({ref}) — prep Situation / Task / Action / Result.')
    backups = _backup_stories(inventory, [r for _, r, _ in menu_bullets], jd_set)
    if backups:
        md.append("")
        md.append("**Backup stories** (strong line-menu bullets you did NOT submit — safe extra material, "
                  "already vetted as true):")
        md.append("")
        for b in backups:
            md.append(f"- §{b['id']}: {b['text']}")
    md.append("")

    # ---- 3. Likely questions ----
    md.append("## Likely questions")
    md.append("")
    for stage, questions in _STATIC_QUESTIONS:
        md.append(f"### {stage}")
        md.append("")
        for q in questions:
            md.append(f"- {q}")
        md.append("")
    derived = []
    for text, ref, _ in star_source:
        if line_menu.extract_metrics(text):
            derived.append(f'- Walk me through: "{_fragment(text, 110)}" ({ref})')
        if len(derived) >= 6:
            break
    if derived:
        md.append("### From your own resume claims")
        md.append("")
        md.extend(derived)
        md.append("")

    # ---- 4. Questions to ask ----
    md.append("## Questions to ask")
    md.append("")
    jd_low = f"{title}\n{job.get('description') or ''}".lower()
    picked = [q for kw, q in _ASK_POOL if kw in jd_low]
    for q in _ASK_DEFAULTS:
        if len(picked) >= 9:
            break
        picked.append(q)
    for q in picked[:10]:
        md.append(f"- {q}")
    md.append("")

    # ---- 5. Company notes ----
    md.append("## Company notes")
    md.append("")
    paras = _company_paragraphs(posting_text, job.get("company"))
    if paras:
        md.append("From the stored job posting (the only verified source in this pack):")
        md.append("")
        for p in paras:
            md.append(f"> {p}")
            md.append("")
    else:
        md.append("_No company facts could be extracted from the stored posting text. "
                  "Do not improvise company facts in the interview — research below._")
        md.append("")
    md.append("**Research TODO (manual — do not skip):**")
    md.append("")
    md.append("- [ ] Recent company news / press releases (last 90 days)")
    md.append("- [ ] Funding, earnings, or growth signals")
    md.append("- [ ] LinkedIn profiles of the interviewers (background, tenure, what they post about)")
    md.append("- [ ] Use the product: sign up, run the core flow, note 2 things you'd improve")
    md.append("- [ ] Top 2-3 competitors and how this company positions against them")
    md.append("- [ ] Glassdoor / Blind interview reports for this team")
    md.append("")

    # ---- 6. Consistency warning ----
    md.append("> **Consistency check:** everything you say must match the materials you submitted. "
              "Numbers, titles, dates, and claims in the interview must be exactly the ones on the "
              "resume above — if a story needs a fact that is not in your submitted materials or the "
              "line menu, do not use it.")
    md.append("")

    return "\n".join(md)
