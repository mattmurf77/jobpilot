"""Ashby boards over the config watchlist (watchlist.ashby: [slug, ...]).

Added in integration: Ramp and Plaid moved off Greenhouse to Ashby, so the broad
watchlist needs an Ashby source. Reuses the dream module's Ashby parser.
"""
from backend.sources import dream


def fetch(config):
    jobs = []
    for slug in (config.get("watchlist") or {}).get("ashby") or []:
        postings = dream._fetch_ashby(slug)  # raises on a dead board; refresh isolates per-source
        for p in postings:
            p["company"] = p.get("company") or slug.replace("-", " ").title()
        jobs.extend(postings)
    return jobs
