"""Document rendering: tailored resume -> HTML (template-faithful), HTML -> PDF
(Playwright's bundled Chromium, or an optional external html-to-pdf node script),
and cover-letter HTML in a matching style.

The resume HTML reuses the baseline template's exact <style> block; only the
body is rebuilt from the structured TailoredResume.
"""
import copy
import os
import re
import subprocess
import time

from backend import line_menu
from backend.app import load_config, materials_path
from backend.profile_store import display_name


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _template_css():
    css = line_menu.load_baseline().get("css", "")
    # ATS text-layer fix: the baseline's positioned bullets (li position:relative
    # + absolutely-positioned "\2022" pseudo-element) paint in a later pass, so
    # naive content-stream extraction reads every bullet AFTER the static text
    # (scrambling role->bullet association for some ATS parsers). Replace with a
    # hanging-indent technique that keeps the identical visual layout but stays
    # in normal flow.
    css = css.replace("position: relative;\n    padding-left: 10pt;",
                      "padding-left: 10pt;\n    text-indent: -10pt;")
    css = re.sub(r"ul\.bullets li::before \{[^}]*\}",
                 lambda m: 'ul.bullets li::before { content: "\u2022\u00a0"; font-weight: 700; }',
                 css)
    # keep each role entry on one page (never split title/scope from its bullets)
    css += ("\n.company-line, .title-row, .title-progression, .scope-line { break-after: avoid; page-break-after: avoid; }"
            "\nul.bullets li { break-inside: avoid; page-break-inside: avoid; }\n")
    return css


# ------------------------------------------------------------- resume -> HTML

def render_resume_html(tailored, profile):
    """Rebuild the resume body from the structured TailoredResume, using the
    baseline template's CSS verbatim."""
    css = _template_css()
    name = display_name(profile)
    linkedin = re.sub(r"^https?://(www\.)?", "", profile.get("linkedin") or "")
    contact_bits = [profile.get("location"), profile.get("email"), profile.get("phone"), linkedin]
    contact = " · ".join(_esc(b) for b in contact_bits if b)

    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        f"<title>{_esc(name)} Resume</title>",
        f"<style>{css}</style>",
        "</head>",
        "<body>",
        f'<div class="name">{_esc(name)}</div>',
        f'<div class="subtitle">{_esc(line_menu_strip(tailored.get("subtitle")))}</div>',
        f'<div class="contact">{contact}</div>',
        "<h2>Professional Summary</h2>",
        f'<p class="summary">{tailored.get("summary_html", "")}</p>',
        "<h2>Professional Experience</h2>",
    ]

    for i, role in enumerate(tailored.get("roles", [])):
        parts.append('<div class="role-block">')
        # continuation entries (a later title under the same employer) skip the
        # company line so the employer prints once with stacked title entries.
        if not role.get("continuation"):
            parts.append(f'<div class="company-line"><span>{_esc(role.get("company"))}</span>'
                         f'<span>{_esc(role.get("location"))}</span></div>')
        titles = role.get("titles") or []
        if len(titles) > 1:
            parts.append('<div class="title-progression">')
        for t in titles:
            parts.append(f'<div class="title-row"><span class="title">{_esc(t.get("title"))}</span>'
                         f'<span class="dates">{_esc(t.get("dates"))}</span></div>')
        if len(titles) > 1:
            parts.append("</div>")
        if role.get("scope_line"):
            parts.append(f'<div class="scope-line">{_esc(role["scope_line"])}</div>')
        parts.append('<ul class="bullets"' + (' style="margin-top: 3pt;"' if len(titles) == 1 else "") + ">")
        for b in role.get("bullets", []):
            parts.append(f"<li>{b.get('html', '')}</li>")
        parts.append("</ul>")
        if i == 0 and tailored.get("earlier_impact"):
            parts.append(f'<div class="subhead">{_esc(tailored.get("earlier_impact_heading") or "Earlier impact:")}</div>')
            parts.append('<ul class="bullets">')
            for b in tailored["earlier_impact"]:
                parts.append(f"<li>{b.get('html', '')}</li>")
            parts.append("</ul>")
        parts.append("</div>")

    projects = tailored.get("projects")
    if projects and projects.get("bullets"):
        parts.append('<div class="role-block">')
        parts.append(f'<div class="company-line"><span>{_esc(projects.get("heading"))}</span>'
                     f'<span>{_esc(projects.get("dates"))}</span></div>')
        if projects.get("scope_line"):
            parts.append(f'<div class="scope-line">{_esc(projects["scope_line"])}</div>')
        parts.append('<ul class="bullets">')
        for b in projects["bullets"]:
            parts.append(f"<li>{b.get('html', '')}</li>")
        parts.append("</ul>")
        parts.append("</div>")

    parts.append("<h2>Skills &amp; Tools</h2>")
    parts.append(f'<p class="skills">{tailored.get("skills_html", "")}</p>')
    parts.append("<h2>Education &amp; Training</h2>")
    for edu in tailored.get("education", []):
        parts.append(f'<div class="education-line">{edu}</div>')
    parts.append("</body>")
    parts.append("</html>")
    html = "\n".join(parts)
    head, sep, body = html.partition("</head>")
    head = head.replace("</style>", ".nbh { white-space: nowrap; }\n</style>")
    return head + sep + _protect_hyphens(body)


_HYPH_TOKEN = re.compile(r"\b([\w$%.]+(?:-[\w$%.]+)+)\b")


def _protect_hyphens(html):
    """Wrap hyphenated compounds in no-wrap spans so lines never break at the
    hyphen. PDF text extractors treat an end-of-line hyphen as a soft hyphen
    and DELETE it ("Partner-Distributed" -> "PartnerDistributed"), which breaks
    keyword matching in ATS/AI resume graders. Operates on text nodes only,
    never inside tags."""
    parts = re.split(r"(<[^>]+>)", html)
    for i, seg in enumerate(parts):
        if seg.startswith("<"):
            continue
        parts[i] = _HYPH_TOKEN.sub(lambda m: '<span class="nbh">' + m.group(1) + "</span>", seg)
    return "".join(parts)


def line_menu_strip(text):
    """Subtitle may arrive with markdown bold from menu variants; strip it."""
    return re.sub(r"\*\*(.+?)\*\*", r"\1", str(text or ""))


# --------------------------------------------------------------- HTML -> PDF

def _pdf_pages_from_binary(pdf_path):
    """Count pages by reading the PDF itself (pages-tree /Count, falling back
    to /Type /Page objects). Reliable for puppeteer output."""
    try:
        with open(pdf_path, "rb") as f:
            data = f.read()
        counts = [int(c) for c in re.findall(rb"/Count\s+(\d+)", data)]
        if counts:
            return max(counts)
        n = len(re.findall(rb"/Type\s*/Page[^s]", data))
        return n or None
    except Exception:
        return None


def _pdf_pages(pdf_path):
    """Page count: pypdf first, then macOS Spotlight metadata (mdls; may return
    "(null)" right after the file is written, so retry once), then the PDF's
    own pages tree."""
    try:
        from pypdf import PdfReader
        return len(PdfReader(pdf_path).pages)
    except Exception:
        pass
    for attempt in range(2):
        try:
            out = subprocess.run(
                ["mdls", "-name", "kMDItemNumberOfPages", "-raw", pdf_path],
                capture_output=True, text=True, timeout=15,
            ).stdout.strip()
            if out.isdigit():
                return int(out)
        except Exception:
            pass
        if attempt == 0:
            n = _pdf_pages_from_binary(pdf_path)
            if n:
                return n
            time.sleep(1)
    return _pdf_pages_from_binary(pdf_path)


def _render_pdf_playwright(html_path, pdf_path):
    """Default renderer: Playwright's Chromium (installed by scripts/setup.sh
    via `playwright install chromium`). Honors the template's @page CSS."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("playwright is not installed (pip install playwright && playwright install chromium)")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                page = browser.new_page()
                page.goto("file://" + os.path.abspath(html_path), wait_until="load")
                page.wait_for_timeout(500)  # let fonts settle
                page.pdf(path=pdf_path, format="Letter", print_background=True,
                         prefer_css_page_size=True,
                         margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
            finally:
                browser.close()
    except Exception as e:
        msg = str(e)
        if "Executable doesn't exist" in msg or "playwright install" in msg:
            raise RuntimeError("Chromium for Playwright is missing: run `.venv/bin/playwright install chromium`")
        raise RuntimeError(f"PDF render failed: {msg[-400:]}")


def render_pdf(html_path, pdf_path, expect_pages=1):
    """Render HTML to PDF. Uses the node script at config.json ->
    materials.html_to_pdf_script when one is configured and present, else
    Playwright's Chromium. Returns the page count (int) or None if it could not
    be determined. Raises RuntimeError on render failure."""
    script = materials_path("html_to_pdf_script")
    if not script or not os.path.exists(script):
        _render_pdf_playwright(html_path, pdf_path)
        if not os.path.exists(pdf_path):
            raise RuntimeError("PDF render produced no file")
        return _pdf_pages(pdf_path)
    cmd = [
        "node", script, html_path, pdf_path,
        "--format=Letter", "--margin=0", "--scale=1.0", "--wait=2000",
    ]
    if expect_pages:
        cmd.append(f"--expect-pages={expect_pages}")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        raise RuntimeError("PDF render timed out")
    if not os.path.exists(pdf_path):
        tail = (proc.stderr or proc.stdout or "")[-400:]
        raise RuntimeError(f"PDF render failed: {tail}")
    return _pdf_pages(pdf_path)


def _trim_lowest(tailored):
    """Drop the lowest-scoring trimmable bullet. Main role bullets are kept to a
    floor of 3, the optional projects section to a floor of 2, earlier-impact to
    a floor of 1. Returns the trimmed ref or None."""
    candidates = []
    roles = tailored.get("roles", [])
    if roles and len(roles[0].get("bullets", [])) > 3:
        for b in roles[0]["bullets"]:
            candidates.append((b.get("score", 0), "main", b))
    if len(tailored.get("earlier_impact", [])) > 1:
        for b in tailored["earlier_impact"]:
            candidates.append((b.get("score", 0), "earlier", b))
    projects = tailored.get("projects")
    if projects and len(projects.get("bullets", [])) > 2:
        for b in projects["bullets"]:
            candidates.append((b.get("score", 0), "projects", b))
    if candidates:
        # Length-aware: among the near-lowest scores, drop the LONGEST bullet —
        # frees the most vertical space per unit of relevance lost.
        floor_score = min(c[0] for c in candidates)
        near_lowest = [c for c in candidates if c[0] <= floor_score + 0.75]
        _, slot, victim = max(near_lowest, key=lambda c: len(c[2].get("html", "")))
        if slot == "main":
            roles[0]["bullets"].remove(victim)
        elif slot == "projects":
            projects["bullets"].remove(victim)
        else:
            tailored["earlier_impact"].remove(victim)
        return victim.get("source_ref")
    # Floors reached. Last-resort space levers, only relevant when the optional
    # projects section is competing for the page:
    if projects and projects.get("scope_line"):
        projects["scope_line"] = ""
        return "projects-scope-line"
    if projects and tailored.get("earlier_impact"):
        victim = tailored["earlier_impact"][-1]
        tailored["earlier_impact"] = []
        return victim.get("source_ref")
    # Final lever: cut a long education entry to its first sentence (drops the
    # course-topic detail, keeps the credential + date).
    edu = tailored.get("education") or []
    for i, entry in enumerate(edu):
        plain = re.sub(r"<[^>]+>", "", entry)
        if len(plain) > 150 and ". " in entry:
            edu[i] = entry.split(". ", 1)[0] + "."
            return "education-detail"
    return None


def render_resume_pdf_one_page(tailored, profile, html_path, pdf_path, max_trims=8):
    """Render the tailored resume to a 1-page PDF, trimming the lowest-scoring
    bullet and re-rendering (up to `max_trims` times) on overflow.

    Returns (pages, tailored_used, trimmed_refs)."""
    work = copy.deepcopy(tailored)
    trimmed = []
    for _ in range(max_trims + 1):
        html = render_resume_html(work, profile)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        pages = render_pdf(html_path, pdf_path, expect_pages=1)
        if pages is None or pages <= 1:
            return pages, work, trimmed
        ref = _trim_lowest(work)
        if ref is None:
            return pages, work, trimmed
        trimmed.append(ref)
    return pages, work, trimmed


# ------------------------------------------------------- ATS parseability

def ats_check(pdf_path, job, profile):
    """Machine-readability check on a rendered resume PDF (via pypdf).

    Returns {ok, chars, contact: {name, email, phone}, keywords_found,
    keywords_total, missing: [...]} — plus "reason" when ok is False.
    Never raises: extraction failure returns ok False with a reason.
    """
    profile = profile or {}
    empty_contact = {"name": False, "email": False, "phone": False}
    try:
        from pypdf import PdfReader
        from backend.review_checks import _GENERIC_JD_TOKENS
        from backend.tailoring import _tokens

        try:
            reader = PdfReader(pdf_path)
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception as e:
            return {"ok": False, "reason": f"PDF text extraction failed: {e}", "chars": 0,
                    "contact": dict(empty_contact),
                    "keywords_found": 0, "keywords_total": 0, "missing": []}

        chars = len(text.strip())
        low = text.lower()
        text_digits = re.sub(r"\D", "", text)
        name = str(profile.get("name") or "")
        email = str(profile.get("email") or "").lower()
        phone_digits = re.sub(r"\D", "", str(profile.get("phone") or ""))
        contact = {
            "name": bool(name) and all(p.lower() in low for p in name.split()),
            "email": bool(email) and email in low,
            "phone": bool(phone_digits) and phone_digits in text_digits,
        }

        # Top ~12 JD keywords, matching-style tokenization (stopword-filtered).
        freq = {}
        for t in _tokens(f"{job.get('title') or ''}\n{job.get('description') or ''}"):
            if len(t) >= 3 and not t.isdigit() and t not in _GENERIC_JD_TOKENS:
                freq[t] = freq.get(t, 0) + 1
        top = [t for t, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:12]]
        pdf_tokens = set(_tokens(text))
        missing = [t for t in top if t not in pdf_tokens]

        ok = chars >= 200 and contact["email"]
        out = {"ok": ok, "chars": chars, "contact": contact,
               "keywords_found": len(top) - len(missing), "keywords_total": len(top),
               "missing": missing}
        if not ok:
            out["reason"] = ("extracted text is suspiciously short — resume may not be "
                             "machine-readable" if chars < 200
                             else "email address not found in extracted text")
        return out
    except Exception as e:  # belt-and-braces: this helper must never raise
        return {"ok": False, "reason": f"ATS check failed: {e}", "chars": 0,
                "contact": dict(empty_contact),
                "keywords_found": 0, "keywords_total": 0, "missing": []}


# ------------------------------------------------------------- cover letters

def _md_to_paragraphs(markdown_text):
    html_parts = []
    for block in re.split(r"\n\s*\n", str(markdown_text or "").strip()):
        block = block.strip()
        if not block:
            continue
        esc = _esc(block)
        esc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc)
        esc = esc.replace("\n", "<br>")
        html_parts.append(f"<p>{esc}</p>")
    return "\n".join(html_parts)


def render_cover_letter_html(markdown_text, profile, job):
    """Clean letter layout reusing the resume's fonts/colors, with a
    name/contact letterhead matching the resume header."""
    name = display_name(profile)
    linkedin = re.sub(r"^https?://(www\.)?", "", profile.get("linkedin") or "")
    contact_bits = [profile.get("location"), profile.get("email"), profile.get("phone"), linkedin]
    contact = " · ".join(_esc(b) for b in contact_bits if b)
    role_line = " · ".join(x for x in [job.get("title"), job.get("company")] if x)
    body = _protect_hyphens(_md_to_paragraphs(markdown_text))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{_esc(name)} Cover Letter</title>
<style>
  @page {{ size: Letter; margin: 0.75in 0.85in; }}
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0; padding: 0;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    color: #0e1217;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
  }}
  body {{ font-size: 10.5pt; line-height: 1.45; }}
  .nbh {{ white-space: nowrap; }}
  .name {{
    font-size: 20pt; font-weight: 700; letter-spacing: 0.02em;
    margin: 0 0 2pt 0; text-transform: uppercase;
  }}
  .contact {{
    font-size: 9.5pt; color: #2a3340; margin: 0 0 6pt 0;
    padding-bottom: 6pt; border-bottom: 1pt solid #0e1217;
  }}
  .re-line {{ font-size: 9.75pt; font-style: italic; color: #2a3340; margin: 8pt 0 14pt 0; }}
  p {{ margin: 0 0 10pt 0; }}
  p strong {{ font-weight: 700; }}
</style>
</head>
<body>
<div class="name">{_esc(name)}</div>
<div class="contact">{contact}</div>
<div class="re-line">Re: {_esc(role_line) or "Application"}</div>
{body}
</body>
</html>"""


# ------------------------------------------------------------ resume -> DOCX

def _docx_add_html_runs(paragraph, html):
    """Render our simple bullet HTML (<strong> only) into docx runs."""
    for i, seg in enumerate(re.split(r"(<strong>.*?</strong>)", html)):
        if not seg:
            continue
        if seg.startswith("<strong>"):
            run = paragraph.add_run(re.sub(r"</?strong>", "", seg))
            run.bold = True
        else:
            paragraph.add_run(re.sub(r"<[^>]+>", "", seg))


def render_resume_docx(tailored, profile, path):
    """True structured DOCX companion: real heading styles and List Bullet
    paragraphs, so ATS/AI parsers get organized structure instead of a PDF
    text-layer line stream. Content identical to the PDF."""
    import docx
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    d = docx.Document()
    style = d.styles["Normal"]
    style.font.name = "Helvetica"
    style.font.size = Pt(10)

    name = display_name(profile)
    linkedin = re.sub(r"^https?://(www\.)?", "", profile.get("linkedin") or "")
    p = d.add_paragraph()
    r = p.add_run(name.upper()); r.bold = True; r.font.size = Pt(20)
    d.add_paragraph(line_menu_strip(tailored.get("subtitle") or ""))
    d.add_paragraph(" · ".join(x for x in [profile.get("location"), profile.get("email"),
                                           profile.get("phone"), linkedin] if x))

    def heading(text):
        p = d.add_paragraph()
        r = p.add_run(text); r.bold = True; r.font.size = Pt(11)

    heading("PROFESSIONAL SUMMARY")
    p = d.add_paragraph(); _docx_add_html_runs(p, tailored.get("summary_html", ""))

    heading("PROFESSIONAL EXPERIENCE")
    for i, role in enumerate(tailored.get("roles", [])):
        if not role.get("continuation"):
            p = d.add_paragraph()
            r = p.add_run(f"{role.get('company')} | {role.get('location')}"); r.bold = True
        for t in role.get("titles") or []:
            d.add_paragraph(f"{t.get('title')} ({t.get('dates')})")
        if role.get("scope_line"):
            d.add_paragraph(role["scope_line"])
        for b in role.get("bullets", []):
            p = d.add_paragraph(style="List Bullet")
            _docx_add_html_runs(p, b.get("html", ""))
        if i == 0 and tailored.get("earlier_impact"):
            d.add_paragraph(tailored.get("earlier_impact_heading") or "Earlier impact:")
            for b in tailored["earlier_impact"]:
                p = d.add_paragraph(style="List Bullet")
                _docx_add_html_runs(p, b.get("html", ""))

    projects = tailored.get("projects")
    if projects and projects.get("bullets"):
        p = d.add_paragraph()
        r = p.add_run(f"{projects.get('heading')} ({projects.get('dates')})"); r.bold = True
        for b in projects["bullets"]:
            p = d.add_paragraph(style="List Bullet")
            _docx_add_html_runs(p, b.get("html", ""))

    heading("SKILLS & TOOLS")
    p = d.add_paragraph(); _docx_add_html_runs(p, tailored.get("skills_html", ""))

    heading("EDUCATION & TRAINING")
    for edu in tailored.get("education", []):
        p = d.add_paragraph(); _docx_add_html_runs(p, edu)

    d.save(path)
    return path
