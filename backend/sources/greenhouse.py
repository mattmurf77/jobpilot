"""Greenhouse boards API fetcher.

https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
Free, no auth. `content` arrives HTML-escaped — unescape, then strip to text.
"""
import html

from backend.sources import http_get, looks_remote, strip_html


def fetch(config):
    slugs = (config.get("watchlist") or {}).get("greenhouse", [])
    jobs = []
    failed = []
    for slug in slugs:
        try:
            resp = http_get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:  # one bad slug must not kill the rest
            failed.append(f"{slug}: {e}")
            continue
        for j in data.get("jobs", []):
            if not j.get("id") or not j.get("title"):
                continue
            content = html.unescape(j.get("content") or "")
            location = ((j.get("location") or {}).get("name")) or ""
            jobs.append({
                "source": "greenhouse",
                "external_id": str(j["id"]),
                "url": j.get("absolute_url"),
                "title": j["title"],
                "company": j.get("company_name") or slug.capitalize(),
                "location": location,
                "remote": looks_remote(location, j["title"]),
                "salary": None,
                "description": strip_html(content),
                "posted_at": j.get("updated_at"),
            })
    if failed and not jobs and slugs:
        raise RuntimeError("all greenhouse boards failed: " + "; ".join(failed))
    return jobs
