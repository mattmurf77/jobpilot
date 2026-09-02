"""Lever postings API fetcher.

https://api.lever.co/v0/postings/{slug}?mode=json — free, no auth.
"""
from datetime import datetime, timezone

from backend.sources import http_get, looks_remote

DESCRIPTION_CAP = 20000


def _ms_to_iso(ms):
    if not ms:
        return None
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError, OSError):
        return None


def fetch(config):
    slugs = (config.get("watchlist") or {}).get("lever", [])
    jobs = []
    failed = []
    for slug in slugs:
        try:
            resp = http_get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
            resp.raise_for_status()
            postings = resp.json()
        except Exception as e:  # one bad slug must not kill the rest
            failed.append(f"{slug}: {e}")
            continue
        if not isinstance(postings, list):
            failed.append(f"{slug}: unexpected response shape")
            continue
        for p in postings:
            if not p.get("id") or not p.get("text"):
                continue
            location = ((p.get("categories") or {}).get("location")) or ""
            workplace = p.get("workplaceType") or ""
            jobs.append({
                "source": "lever",
                "external_id": str(p["id"]),
                "url": p.get("hostedUrl") or p.get("applyUrl"),
                "title": p["text"],
                "company": slug.capitalize(),
                "location": location,
                "remote": looks_remote(location, workplace, p["text"]),
                "salary": None,
                "description": (p.get("descriptionPlain") or "")[:DESCRIPTION_CAP],
                "posted_at": _ms_to_iso(p.get("createdAt")),
            })
    if failed and not jobs and slugs:
        raise RuntimeError("all lever boards failed: " + "; ".join(failed))
    return jobs
