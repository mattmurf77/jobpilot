#!/usr/bin/env python3
"""Build your JobPilot materials from an existing resume (and optional cover letter).

    .venv/bin/python scripts/onboard.py --resume resume.pdf [--cover-letter letter.docx]
                                        [--force] [--no-llm] [--model claude-opus-5]

What it writes (nothing outside the repo; all of it gitignored):
    materials/personal/resume_line_menu.md      bullet inventory the tailoring engine selects from
    materials/personal/resume_template.html     baseline resume in the visual template
    materials/personal/cover_letter_reference.md your own letter, used as a voice exemplar (optional)
    data/profile.json                            contact, targets, keywords, screener defaults
    config.json                                  created from config.example.json if missing

With an Anthropic API key (in .env or the environment) Claude drafts the three
documents from your resume under a strict no-invention rule, and this script
verifies every number in the drafts appears in your resume text. Without a key
(or with --no-llm) it copies the annotated templates for you to fill by hand.
Review everything either way: the engine trusts these files completely.
"""
import argparse
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(ROOT, ".env"))

PERSONAL = os.path.join(ROOT, "materials", "personal")
TEMPLATES = os.path.join(ROOT, "materials", "templates")
PROFILE_PATH = os.path.join(ROOT, "data", "profile.json")
PROFILE_EXAMPLE = os.path.join(ROOT, "data", "profile.example.json")

OUT_MENU = os.path.join(PERSONAL, "resume_line_menu.md")
OUT_TEMPLATE = os.path.join(PERSONAL, "resume_template.html")
OUT_LETTER = os.path.join(PERSONAL, "cover_letter_reference.md")


# ------------------------------------------------------------ text extraction

def extract_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
    if ext == ".docx":
        import docx
        d = docx.Document(path)
        parts = [p.text for p in d.paragraphs]
        for table in d.tables:
            for row in table.rows:
                parts.append(" | ".join(c.text for c in row.cells))
        return "\n".join(parts)
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    if ext in (".html", ".htm"):
        text = re.sub(r"<style.*?</style>|<script.*?</script>", " ", text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"[ \t]+", " ", text)
    return text


def _clean(text):
    text = text.replace(" ", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ------------------------------------------------------------------ helpers

def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  wrote {os.path.relpath(path, ROOT)}")


def _guard(path, force):
    if os.path.exists(path) and not force:
        print(f"  {os.path.relpath(path, ROOT)} exists; use --force to overwrite")
        return False
    return True


_NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _numbers(text):
    return {m.group(0).replace(",", "") for m in _NUM_RE.finditer(text or "")}


def _parse_json_object(text):
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in model output")
    return json.loads(text[start:end + 1])


def _strip_fences(text, lang_hint):
    text = text.strip()
    m = re.match(r"^```[a-zA-Z]*\n(.*)\n```$", text, re.S)
    if m:
        return m.group(1).strip()
    if lang_hint == "html":
        i = text.find("<!DOCTYPE")
        if i < 0:
            i = text.find("<html")
        j = text.rfind("</html>")
        if i >= 0 and j > i:
            return text[i:j + len("</html>")]
    return text


# ---------------------------------------------------------------- LLM calls

NO_INVENTION = """ABSOLUTE RULES:
- Use ONLY facts present in the RESUME TEXT. Never invent an employer, title, date, metric, tool, degree, or skill.
- Copy every number exactly as it appears in the resume (same digits, units, and precision). Do not compute, round, or extrapolate numbers.
- If something the template asks for is not in the resume, leave that slot empty or write a bracketed placeholder like [add: ...] rather than guessing.
- Do not use em-dashes; use commas, colons, or periods."""

PROFILE_SYSTEM = """You extract a structured candidate profile from a resume for a job-search tool.
Output STRICT JSON matching the schema exactly (same keys, same types), nothing else.

""" + NO_INVENTION + """

Field guidance:
- name/first_name/last_name/preferred_name/email/phone/linkedin/website/location/city/state/country: from the resume header. preferred_name = first_name unless the resume shows a nickname. country defaults to "United States" only if the location is clearly in the US, else the country shown.
- current_title / current_company: the most recent role.
- target_titles: 3-6 titles the candidate would plausibly apply to next: the current title's level and one level up, in the candidate's function (e.g. "Senior Product Manager", "Lead Product Manager", "Principal Product Manager").
- seniority_terms: the level words that appear in those target titles, lowercase (e.g. ["senior", "lead", "principal", "staff"]).
- target_domains: 3-6 industry/domain phrases evidenced by the resume (lowercase or as written).
- keywords: 20-30 lowercase skill/tool/domain phrases that appear in the resume and would appear in job descriptions.
- facts: 4-8 short entries, each a single sentence in the first person quoting a flagship, verifiable result from the resume with its number (these seed cover letters). Keys are short snake_case labels.
- education: one entry per degree/program in the resume.
- screener_answers: keep the schema's defaults; change work-authorization or relocation answers only if the resume states them.
"""

MENU_SYSTEM = """You convert a resume into a "Resume Line Menu": a markdown inventory of every line that could appear on a tailored resume. A parser reads this file, so follow the TEMPLATE's structure exactly: the same `## N.` section numbers, `### N.N —` subsections, and `1.` numbered items. Output ONLY the markdown document (no code fences, no commentary).

""" + NO_INVENTION + """

How to fill each section:
- Title line: `# Resume Line Menu — <Full Name> (v1)`. Keep the template's blockquote instructions and "How to use" block verbatim.
- §0.1 value propositions: 2-3 one-sentence pitches synthesized ONLY from resume facts.
- §0.2 subtitles: 3-5 one-line brand subtitles (title + domains), numbered; the first is the safest default. No em-dashes anywhere; use " - " or "," instead.
- §0.5.2 table: one row per company-internal product code, team name, or program nickname you can see in the resume, with a plain-English replacement in quotes in the last column. If there are none, keep the two example rows but mark them "(example row, replace)".
- §1 summaries: 3-4 variants, each `N. **(Label)** text`, 2-3 sentences, built only from resume facts, bold the key metrics.
- §2 role context lines: one scope line per employer.
- §3: the CURRENT role at the current employer. Group its bullets into `###` themed subsections (strategy, execution, process/org, cross-functional leadership, customer impact). Include EVERY bullet from the resume for this role, each as a numbered item, action-verb first, metrics in bold. Add 1-2 reasonable rephrasings of the strongest bullets ONLY if they introduce no new facts.
- §4 and §5: earlier titles at the SAME employer (most recent first). If the resume has only one title at the current employer, keep the headers with a single line `1. [no earlier title at this employer]`.
- §6: "earlier impact" at the current employer: the 1-3 strongest bullets from §4/§5 restated (or leave one placeholder item if not applicable).
- §7: the PREVIOUS employer (the one before the current one). §7.1 = one compressed bullet capturing the role; §7.2 = every bullet from the resume for that role. If there are older employers beyond that, add sections §7.3, §7.4 ... one per employer, in the same format.
- §8 skills library: `·`-separated lines grouped by category; use ONLY skills/tools named or clearly evidenced in the resume.
- §9 education, §10 achievements, §11 quick-reference table of every quantified result with its period.
- §17 projects: only if the resume lists side projects/portfolio work; otherwise keep the header and one item `1. [no independent projects listed]`.
"""

TEMPLATE_SYSTEM = """You fill an HTML resume template from a resume. Output ONLY the complete HTML document (no code fences, no commentary). Keep the <style> block byte-for-byte identical, keep every class name and the nesting shown, and remove the HTML comment.

""" + NO_INVENTION + """

Filling rules:
- .name, .subtitle (a one-line brand subtitle: title + domains, no em-dashes), .contact (location · email · phone · linkedin, omit missing parts).
- p.summary: 2-3 sentences from the resume's own summary or built from its strongest facts, with key metrics in <strong>.
- One .role-block per employer, most recent first. Inside: .company-line with two <span>s (company, location), a .title-progression containing one .title-row per title held there (most recent first) with .title and .dates spans (format dates like "May 2025 to Present"), an optional .scope-line, then ul.bullets with the 4-6 strongest bullets for the role (action verb first, metrics in <strong>).
- Only the FIRST role block may contain a .subhead ("Earlier impact at <Company> (<years>):") followed by a second ul.bullets, and only when the candidate held earlier titles at that employer; otherwise omit the subhead and that list.
- For employers with a single title, use one .title-row directly inside the .role-block (no .title-progression wrapper) as the template's second block shows.
- p.skills: 15-20 skills from the resume, `·`-separated, the 5-6 most important wrapped in <strong>.
- One .education-line per degree/program.
- Keep the whole thing to roughly one printed page: prefer fewer, stronger bullets.
"""


def _client():
    import anthropic
    return anthropic.Anthropic()


def _ask(client, model, system, user, max_tokens=32000):
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        raise RuntimeError("the model declined this request")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("output hit max_tokens; rerun with a shorter resume or higher limit")
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def llm_build(resume_text, model, force):
    from backend import line_menu

    client = _client()
    schema = _read(PROFILE_EXAMPLE)
    menu_template = _read(os.path.join(TEMPLATES, "resume_line_menu.md"))
    html_template = _read(os.path.join(TEMPLATES, "resume_template.html"))
    resume_block = f"RESUME TEXT:\n<<<\n{resume_text}\n>>>"
    allowed_numbers = _numbers(resume_text)

    print("==> drafting profile.json")
    profile_raw = _ask(client, model, PROFILE_SYSTEM,
                       f"SCHEMA (fill every key):\n{schema}\n\n{resume_block}", max_tokens=8000)
    profile = _parse_json_object(profile_raw)
    example = json.loads(schema)
    for k, v in example.items():
        profile.setdefault(k, v)

    print("==> drafting the resume line menu (this is the long one)")
    menu = _strip_fences(_ask(client, model, MENU_SYSTEM,
                              f"TEMPLATE:\n<<<\n{menu_template}\n>>>\n\n{resume_block}"), "md")

    print("==> drafting the baseline resume HTML")
    html = _strip_fences(_ask(client, model, TEMPLATE_SYSTEM,
                              f"TEMPLATE:\n<<<\n{html_template}\n>>>\n\n{resume_block}"), "html")

    # ---- validation: structure + no new numbers
    problems = []
    if _guard(OUT_MENU, force):
        _write(OUT_MENU, menu)
    if _guard(OUT_TEMPLATE, force):
        _write(OUT_TEMPLATE, html)
    if _guard(PROFILE_PATH, force):
        _write(PROFILE_PATH, json.dumps(profile, indent=2))

    inv = line_menu._parse_menu(OUT_MENU) if os.path.exists(OUT_MENU) else None
    if inv:
        n_bullets = sum(len(s["bullets"]) for s in inv["sections"])
        print(f"  line menu parsed: {n_bullets} bullets across sections "
              f"{[s['id'] for s in inv['sections']]}, {len(inv['subtitles'])} subtitles, "
              f"{len(inv['summaries'])} summaries, {len(inv['skills_library'])} skills")
        if n_bullets < 10:
            problems.append("fewer than 10 bullets parsed from the line menu (engine will fall back to the baseline resume)")
        new_nums = set()
        for sec in inv["sections"]:
            for b in sec["bullets"]:
                new_nums |= _numbers(b["text"]) - allowed_numbers
        new_nums -= {str(y) for y in range(1990, 2040)}  # years in date ranges are fine
        if new_nums:
            problems.append(f"numbers in the line menu that do not appear in the resume text: {sorted(new_nums)[:15]}")
    base = line_menu.parse_baseline(OUT_TEMPLATE) if os.path.exists(OUT_TEMPLATE) else None
    if base:
        print(f"  template parsed: name={base['name']!r}, {len(base['roles'])} role block(s), "
              f"{len(base['education'])} education line(s)")
        if not base["name"] or not base["roles"]:
            problems.append("template HTML is missing the name or role blocks; check the class names")
        html_nums = set()
        for role in base["roles"]:
            for b in role["bullets"]:
                html_nums |= _numbers(re.sub(r"<[^>]+>", "", b))
        extra = html_nums - allowed_numbers - {str(y) for y in range(1990, 2040)}
        if extra:
            problems.append(f"numbers in the template resume not found in the resume text: {sorted(extra)[:15]}")
    return problems


# ------------------------------------------------------------- manual path

def manual_build(force):
    print("==> no API key (or --no-llm): copying annotated templates for you to fill in")
    if _guard(OUT_MENU, force):
        shutil.copyfile(os.path.join(TEMPLATES, "resume_line_menu.md"), OUT_MENU)
        print(f"  wrote {os.path.relpath(OUT_MENU, ROOT)}")
    if _guard(OUT_TEMPLATE, force):
        shutil.copyfile(os.path.join(TEMPLATES, "resume_template.html"), OUT_TEMPLATE)
        print(f"  wrote {os.path.relpath(OUT_TEMPLATE, ROOT)}")
    if _guard(PROFILE_PATH, force):
        shutil.copyfile(PROFILE_EXAMPLE, PROFILE_PATH)
        print(f"  wrote {os.path.relpath(PROFILE_PATH, ROOT)}")
    return ["fill in materials/personal/resume_line_menu.md (every numbered line is a candidate bullet)",
            "fill in materials/personal/resume_template.html (keep the class names)",
            "fill in data/profile.json (or use the Settings tab)"]


# ------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--resume", required=True, help="your current resume (.pdf, .docx, .md, .txt, .html)")
    ap.add_argument("--cover-letter", help="a cover letter you wrote (.pdf, .docx, .md, .txt); used as a voice exemplar")
    ap.add_argument("--force", action="store_true", help="overwrite existing personal files")
    ap.add_argument("--no-llm", action="store_true", help="skip Claude; just copy the templates")
    ap.add_argument("--model", help="model id (default: config.json tailoring.model, else claude-opus-5)")
    args = ap.parse_args()

    from backend.app import load_config  # creates config.json from the example if missing
    config = load_config()
    model = args.model or (config.get("tailoring") or {}).get("model") or "claude-opus-5"

    resume_text = _clean(extract_text(args.resume))
    if len(resume_text.split()) < 80:
        sys.exit(f"could not extract enough text from {args.resume} ({len(resume_text.split())} words); "
                 "try a .docx/.txt export")
    print(f"==> read {len(resume_text.split())} words from {args.resume}")

    problems = []
    if args.no_llm or not os.environ.get("ANTHROPIC_API_KEY"):
        problems += manual_build(args.force)
    else:
        try:
            problems += llm_build(resume_text, model, args.force)
        except Exception as e:  # network/auth/parse: fall back rather than leave nothing
            print(f"  LLM drafting failed ({type(e).__name__}: {e}); falling back to templates")
            problems += manual_build(args.force)

    if args.cover_letter:
        letter = _clean(extract_text(args.cover_letter))
        if _guard(OUT_LETTER, args.force):
            header = _read(os.path.join(TEMPLATES, "cover_letter_reference.md")).split("\n---\n", 1)[0]
            _write(OUT_LETTER, header + "\n---\n\n" + letter + "\n")

    print("\nDone." if not problems else "\nDone, with things to review:")
    for p in problems:
        print(f"  - {p}")
    print("""
Next:
  1. Open materials/personal/resume_line_menu.md and fix anything that is not exactly true.
  2. Open materials/personal/resume_template.html and check the layout (the engine keeps this skeleton fixed).
  3. Check data/profile.json (targets, keywords, screener answers) or edit it in the app's Settings tab.
  4. .venv/bin/python run.py  ->  http://127.0.0.1:5151""")


if __name__ == "__main__":
    main()
