"""Parser for the Resume Line Menu (resume_line_menu.md) and the baseline resume HTML.

Produces a structured inventory the tailoring engine selects from:

    {
        "sections": [{"id", "heading", "bullets": [{"id", "text", "role", "metrics"}]}],
        "subtitles": [...],                # §0.2 brand-subtitle variants
        "summaries": [{"id","label","text"}],   # §1 summary variants
        "value_props": [...],              # §0.1
        "translation_pairs": [(internal, external), ...],  # §0.5.2 Tier-4 lookup
        "skills_library": [...],           # §8 modular keyword library
        "source": "menu" | "baseline_fallback",
    }

The markdown can be irregular; parsing is defensive throughout. If the menu
yields fewer than 10 bullets total, bullets are extracted from the baseline
resume HTML instead so the engine always has an inventory.

Also exposes `load_baseline()` — the stable resume skeleton (name, subtitle,
contact, summary, role blocks with title progressions, skills, education)
parsed from the baseline resume HTML template.
"""
import functools
import os
import re

from backend.app import load_config, resolve_path

# Sections of the menu that contain selectable resume bullets.
ROLE_SECTION_IDS = {"3", "4", "5", "6", "7"}
PROJECT_SECTION_IDS = {"17"}  # Independent AI portfolio (optional Projects section)
# All sections from which numbered items are harvested as bullets.
BULLET_SECTION_IDS = ROLE_SECTION_IDS | PROJECT_SECTION_IDS | {"2", "9", "10"}

_NUM_TOKEN_RE = re.compile(r"[$€£]?\d[\d,.]*(?:\s?[KMB%])?[%+]?", re.I)
_H2_RE = re.compile(r"^##\s+(?:(\d+(?:\.\d+)*)\.?\s*)?(.*?)\s*$")
_H3_RE = re.compile(r"^###\s+(?:(\d+(?:\.\d+)*)\.?\s*[—\-–.]*\s*)?(.*?)\s*$")
_NUMBERED_RE = re.compile(r"^(\d+)\.\s+(.*\S)\s*$")
_QUOTED_RE = re.compile(r'\*\*"([^"]+)"\*\*|"([^"]+)"')


def _materials():
    """Material paths from config, resolved (relative paths root at the project)."""
    return {k: resolve_path(v) for k, v in (load_config().get("materials") or {}).items()}


def extract_metrics(text):
    """All numeric tokens in a line ($1.37B, 24K, 81%, 2-3, 2025...)."""
    return [m.group(0).strip() for m in _NUM_TOKEN_RE.finditer(text)]


def md_to_html(text):
    """Minimal inline markdown -> HTML for a bullet line. Escapes HTML first."""
    s = str(text or "")
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"\1", s)  # drop italics markers
    # Recruiters flag em-dashes as an AI tell (menu §14.7); use plain dashes.
    s = s.replace(" — ", " - ").replace("—", " - ")
    return s


def _strip_md(text):
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", str(text or ""))
    s = re.sub(r"\*(.+?)\*", r"\1", s)
    return s.strip()


def _clean_item(text):
    """Strip trailing editorial comments like *(used in current resume v2...)*."""
    s = re.sub(r"\s*\*\([^)]*\)\*\s*$", "", text)
    return s.strip()


# ---------------------------------------------------------------- menu parse

def _parse_translation_row(cells):
    """One row of the §0.5.2 table -> list of (internal, external) pairs."""
    if len(cells) < 2:
        return []
    raw_key = _strip_md(cells[0])
    replacement_cell = cells[-1]
    if "+" in raw_key or len(raw_key) > 30:
        return []
    keys = [k.strip() for k in raw_key.split("/") if k.strip()]
    # Candidate replacements: quoted strings in the recommendation cell.
    candidates = []
    for m in _QUOTED_RE.finditer(replacement_cell):
        candidates.append((m.group(1) or m.group(2)).strip())
    pairs = []
    for key in keys:
        word = re.compile(r"\b" + re.escape(key) + r"\b", re.I)
        usable = [c for c in candidates if not word.search(c)]
        if usable:
            pairs.append((key, usable[-1]))
    return pairs


def _parse_menu(menu_path):
    with open(menu_path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    sections = {}          # id -> {"id", "heading", "bullets": []}
    section_order = []
    subtitles, summaries, value_props, translation_pairs, skills_library = [], [], [], [], []

    cur_h2_id, cur_h2_heading = None, ""
    cur_sub_id = None      # current ### id like "3.1" / "0.5.2"
    in_table_for = None

    def top_id(num_id):
        return num_id.split(".")[0] if num_id else None

    for raw in lines:
        line = raw.rstrip()

        m2 = _H2_RE.match(line)
        m3 = _H3_RE.match(line) if not m2 else None
        if m2:
            cur_h2_id, cur_h2_heading = m2.group(1), _strip_md(m2.group(2))
            cur_sub_id = cur_h2_id
            in_table_for = None
            tid = top_id(cur_h2_id)
            if tid and tid in BULLET_SECTION_IDS and tid not in sections:
                sections[tid] = {"id": tid, "heading": cur_h2_heading, "bullets": []}
                section_order.append(tid)
            continue
        if m3:
            cur_sub_id = m3.group(1) or cur_sub_id
            in_table_for = None
            continue

        # markdown table rows (for §0.5.2 translation lookup)
        if line.startswith("|") and cur_sub_id and cur_sub_id.startswith("0.5.2"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 2 and not set(cells[0]) <= {"-", ":", " "} \
                    and cells[0].lower() not in ("internal term",):
                translation_pairs.extend(_parse_translation_row(cells))
            continue

        # skills library (§8): prose lines of "·"-separated tokens
        if cur_sub_id and top_id(cur_sub_id) == "8" and "·" in line and not line.startswith((">", "#", "|")):
            skills_library.extend(t.strip() for t in _strip_md(line).split("·") if t.strip())
            continue

        mn = _NUMBERED_RE.match(line.strip())
        if not mn or not cur_sub_id:
            continue
        num, body = mn.group(1), _clean_item(mn.group(2))
        if not body or "✅" in body or "~~" in body:
            continue
        tid = top_id(cur_sub_id)
        item_id = f"{cur_sub_id}.{num}" if cur_sub_id != tid or tid in ROLE_SECTION_IDS else f"{tid}.{num}"

        if cur_sub_id == "0.1":
            value_props.append(_strip_md(body))
        elif cur_sub_id == "0.2":
            subtitles.append(_strip_md(body))
        elif tid == "1":
            label_m = re.match(r"\*\*\(([^)]+)\)\*\*\s*(.*)", body)
            summaries.append({
                "id": f"1.{num}",
                "label": label_m.group(1) if label_m else "",
                "text": (label_m.group(2) if label_m else body).strip(),
            })
        elif tid in BULLET_SECTION_IDS:
            sec = sections.setdefault(tid, {"id": tid, "heading": cur_h2_heading, "bullets": []})
            if tid not in section_order:
                section_order.append(tid)
            sec["bullets"].append({
                "id": item_id,
                "text": body,
                "role": sec["heading"],
                "metrics": extract_metrics(body),
            })

    return {
        "sections": [sections[i] for i in section_order],
        "subtitles": subtitles,
        "summaries": summaries,
        "value_props": value_props,
        "translation_pairs": translation_pairs,
        "skills_library": skills_library,
        "source": "menu",
    }


# ------------------------------------------------------------ baseline parse

def _inner(html_fragment):
    return re.sub(r"\s+", " ", html_fragment).strip()


def parse_baseline(template_path):
    """Parse the baseline resume HTML into the stable skeleton + its content.

    Returns {name, subtitle, contact, summary_html, roles: [{company, location,
    titles:[{title,dates}], scope_line, bullets:[html]}], earlier_impact_heading,
    earlier_impact: [html], skills_html, education: [html], css}.
    """
    with open(template_path, encoding="utf-8") as f:
        html = f.read()

    def first(pattern, default=""):
        m = re.search(pattern, html, re.S)
        return _inner(m.group(1)) if m else default

    css_m = re.search(r"<style>(.*?)</style>", html, re.S)
    out = {
        "name": first(r'<div class="name">(.*?)</div>'),
        "subtitle": first(r'<div class="subtitle">(.*?)</div>'),
        "contact": first(r'<div class="contact">(.*?)</div>'),
        "summary_html": first(r'<p class="summary">(.*?)</p>'),
        "skills_html": first(r'<p class="skills">(.*?)</p>'),
        "education": re.findall(r'<div class="education-line">(.*?)</div>', html, re.S),
        "earlier_impact_heading": first(r'<div class="subhead">(.*?)</div>'),
        "earlier_impact": [],
        "roles": [],
        "css": css_m.group(1) if css_m else "",
    }
    out["education"] = [_inner(e) for e in out["education"]]

    for block in re.findall(r'<div class="role-block">(.*?)</div>\s*(?=<div class="role-block">|<h2)', html, re.S) \
            or re.split(r'<div class="role-block">', html)[1:]:
        spans = re.search(r'<div class="company-line"><span>(.*?)</span><span>(.*?)</span></div>', block, re.S)
        titles = [{"title": _inner(t), "dates": _inner(d)} for t, d in
                  re.findall(r'<span class="title">(.*?)</span><span class="dates">(.*?)</span>', block, re.S)]
        scope = re.search(r'<div class="scope-line">(.*?)</div>', block, re.S)

        # Split bullets before/after the "Earlier impact" subhead, if present.
        subhead_m = re.search(r'<div class="subhead">', block)
        main_part = block[:subhead_m.start()] if subhead_m else block
        earlier_part = block[subhead_m.start():] if subhead_m else ""
        bullets = [_inner(b) for b in re.findall(r"<li>(.*?)</li>", main_part, re.S)]
        if earlier_part:
            out["earlier_impact"] = [_inner(b) for b in re.findall(r"<li>(.*?)</li>", earlier_part, re.S)]

        out["roles"].append({
            "company": _inner(spans.group(1)) if spans else "",
            "location": _inner(spans.group(2)) if spans else "",
            "titles": titles,
            "scope_line": _inner(scope.group(1)) if scope else "",
            "bullets": bullets,
        })
    return out


def _strip_tags(html):
    return re.sub(r"<[^>]+>", "", html)


def _fallback_from_baseline(template_path):
    """Build a minimal inventory from the baseline resume's own bullets."""
    base = parse_baseline(template_path)
    sections = []
    # Map role blocks onto the menu's default section-id scheme so tailoring's
    # grouping (3/4/5 = current role, 6 = earlier impact, 7 = previous role) holds.
    if base["roles"]:
        r0 = base["roles"][0]
        sections.append({"id": "3", "heading": r0.get("company", "Current role"), "bullets": [
            {"id": f"3.B.{i+1}", "text": _strip_tags(b), "role": r0.get("company", ""),
             "metrics": extract_metrics(_strip_tags(b))}
            for i, b in enumerate(r0["bullets"])
        ]})
    if base["earlier_impact"]:
        sections.append({"id": "6", "heading": "Earlier impact", "bullets": [
            {"id": f"6.B.{i+1}", "text": _strip_tags(b), "role": "Earlier impact",
             "metrics": extract_metrics(_strip_tags(b))}
            for i, b in enumerate(base["earlier_impact"])
        ]})
    for j, role in enumerate(base["roles"][1:], start=1):
        sections.append({"id": "7", "heading": role.get("company", f"Role {j}"), "bullets": [
            {"id": f"7.B.{i+1}", "text": _strip_tags(b), "role": role.get("company", ""),
             "metrics": extract_metrics(_strip_tags(b))}
            for i, b in enumerate(role["bullets"])
        ]})
    return {
        "sections": sections,
        "subtitles": [_strip_tags(base["subtitle"])] if base["subtitle"] else [],
        "summaries": [{"id": "1.B", "label": "baseline", "text": _strip_tags(base["summary_html"])}],
        "value_props": [],
        "translation_pairs": [],
        "skills_library": [t.strip() for t in _strip_tags(base["skills_html"]).split("·") if t.strip()],
        "source": "baseline_fallback",
    }


# ------------------------------------------------------------------- caching

@functools.lru_cache(maxsize=4)
def _load_cached(menu_path, template_path, menu_mtime, template_mtime):
    inventory = None
    if menu_path and os.path.exists(menu_path):
        try:
            inventory = _parse_menu(menu_path)
        except Exception:
            inventory = None
    total = sum(len(s["bullets"]) for s in inventory["sections"]) if inventory else 0
    if total < 10:
        inventory = _fallback_from_baseline(template_path)
    return inventory


def load_inventory():
    """Cached structured inventory (cache key includes file mtimes)."""
    mats = _materials()
    menu_path = mats.get("line_menu", "")
    template_path = mats.get("resume_template_html", "")
    mt = os.path.getmtime(menu_path) if menu_path and os.path.exists(menu_path) else 0
    tt = os.path.getmtime(template_path) if template_path and os.path.exists(template_path) else 0
    return _load_cached(menu_path, template_path, mt, tt)


@functools.lru_cache(maxsize=2)
def _baseline_cached(template_path, mtime):
    return parse_baseline(template_path)


def load_baseline():
    """Cached stable skeleton parsed from the baseline resume template."""
    template_path = _materials().get("resume_template_html", "")
    mtime = os.path.getmtime(template_path) if os.path.exists(template_path) else 0
    return _baseline_cached(template_path, mtime)
