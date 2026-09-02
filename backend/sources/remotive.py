"""Remotive API fetcher.

https://remotive.com/api/remote-jobs?search={kw}&limit=50 per config keyword.
Free, no auth. Description is HTML — strip to text. Dedupe across keywords.
"""
from backend.sources import http_get, strip_html


def fetch(config):
    keywords = (config.get("search") or {}).get("keywords", [])
    jobs = []
    seen = set()
    failed = []
    for kw in keywords:
        try:
            resp = http_get("https://remotive.com/api/remote-jobs", params={"search": kw, "limit": 50})
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:  # one keyword failing must not kill the rest
            failed.append(f"{kw!r}: {e}")
            continue
        for j in data.get("jobs", []):
            if not j.get("id") or not j.get("title"):
                continue
            jid = str(j["id"])
            if jid in seen:
                continue
            seen.add(jid)
            jobs.append({
                "source": "remotive",
                "external_id": jid,
                "url": j.get("url"),
                "title": j["title"],
                "company": j.get("company_name") or "",
                "location": j.get("candidate_required_location") or "Remote",
                "remote": True,  # Remotive lists remote jobs only
                "salary": (j.get("salary") or "").strip() or None,
                "description": strip_html(j.get("description")),
                "posted_at": j.get("publication_date"),
            })
    if failed and not jobs and keywords:
        raise RuntimeError("all remotive searches failed: " + "; ".join(failed))
    return jobs
