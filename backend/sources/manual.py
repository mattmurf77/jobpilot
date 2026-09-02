"""Manual job ingest: paste a URL and/or raw JD text.

Covers boards we will not scrape (LinkedIn/Indeed). If only a URL is given we
GET the page (browser UA, 15s timeout), use the <title> for a best-effort
title/company parse, and the visible page text as the description.
Never raises on bad input — returns (job_dict, None) or (None, error_string).
"""
import hashlib
import re

from backend.sources import http_get, looks_remote, strip_html

# Page-title segments that are site chrome, not a company name.
_GENERIC_SEGMENTS = {
    "careers", "career", "jobs", "job", "job application", "job opening",
    "job openings", "current openings", "open positions", "apply",
    "job details", "job board", "linkedin", "indeed", "greenhouse", "lever",
}


def ingest(payload):
    """payload: {url?, title?, company?, description?} -> (job_dict, None) | (None, error)."""
    payload = payload or {}
    url = str(payload.get("url") or "").strip()
    title = str(payload.get("title") or "").strip()
    company = str(payload.get("company") or "").strip()
    description = str(payload.get("description") or "").strip()

    if not url and not description and not title:
        return None, "Provide a URL, or at least a title/description."

    if url and not description:
        page_title, page_text, err = _fetch_page(url)
        if err:
            return None, err
        description = page_text
        if not title and page_title:
            parsed_title, parsed_company = _parse_page_title(page_title)
            title = parsed_title
            company = company or parsed_company

    if not title:
        # Fall back to the first line of the pasted description.
        first_line = description.splitlines()[0].strip() if description else ""
        title = first_line[:80] if first_line else "Manual job"

    external_id = hashlib.sha1(
        (url or title + "|" + description[:500]).encode("utf-8", "ignore")
    ).hexdigest()[:16]

    return {
        "source": "manual",
        "external_id": external_id,
        "url": url or None,
        "title": title,
        "company": company or None,
        "location": "",
        "remote": looks_remote(title, description[:2000]),
        "salary": None,
        "description": description,
        "posted_at": None,
        "status": "new",
    }, None


def _fetch_page(url):
    """GET url -> (page_title, visible_text, error). Never raises."""
    if not re.match(r"^https?://", url, re.I):
        return None, None, f"Invalid URL (must start with http:// or https://): {url}"
    try:
        resp = http_get(url)
    except Exception as e:
        return None, None, f"Could not fetch URL: {e}"
    if resp.status_code >= 400:
        return None, None, f"URL returned HTTP {resp.status_code} — paste the job description instead."
    html_text = resp.text or ""
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", html_text)
    page_title = strip_html(m.group(1), cap=300) if m else None
    text = strip_html(html_text)
    if not text:
        return page_title, "", "Page fetched but no readable text found — paste the job description instead."
    return page_title, text, None


def _parse_page_title(page_title):
    """Best-effort (job_title, company) from a page <title>."""
    pt = re.sub(r"\s+", " ", page_title).strip()
    pt = re.sub(r"(?i)^(job application for|apply for|apply to|now hiring:?)\s+", "", pt)
    m = re.match(r"(?i)^(.{3,80}?)\s+at\s+([^|\-–—·@]{2,60})", pt)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    parts = re.split(r"\s*[|–—·]\s*|\s+-\s+", pt)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        return pt[:120], ""
    title = parts[0][:120]
    company = ""
    for p in parts[1:]:
        if p.lower() not in _GENERIC_SEGMENTS:
            company = p[:80]
            break
    return title, company
