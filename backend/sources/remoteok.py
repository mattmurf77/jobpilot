"""RemoteOK API fetcher.

https://remoteok.com/api — free, but requires a real browser User-Agent
(http_get sends one). The FIRST array element is metadata/legal — skip it.
The feed is unfiltered, so we filter client-side against config keywords.
"""
from backend.sources import http_get, strip_html


def _matches(blob, keywords):
    """A job matches if, for any keyword, every word of it appears in the blob."""
    for kw in keywords:
        words = kw.split()
        if words and all(w in blob for w in words):
            return True
    return False


def _format_salary(smin, smax):
    try:
        smin = int(smin or 0)
        smax = int(smax or 0)
    except (TypeError, ValueError):
        return None
    if smin and smax:
        return f"${smin:,}–${smax:,}"
    if smin or smax:
        return f"${(smin or smax):,}"
    return None


def fetch(config):
    keywords = [k.lower() for k in (config.get("search") or {}).get("keywords", [])]
    resp = http_get("https://remoteok.com/api")
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise RuntimeError("unexpected RemoteOK response shape")

    jobs = []
    for item in data[1:]:  # element 0 is metadata/legal notice
        if not isinstance(item, dict) or not item.get("id") or not item.get("position"):
            continue
        description = strip_html(item.get("description"))
        blob = " ".join([
            str(item.get("position") or ""),
            " ".join(item.get("tags") or []),
            description,
        ]).lower()
        if keywords and not _matches(blob, keywords):
            continue
        jobs.append({
            "source": "remoteok",
            "external_id": str(item["id"]),
            "url": item.get("url"),
            "title": item["position"],
            "company": item.get("company") or "",
            "location": item.get("location") or "Remote",
            "remote": True,  # RemoteOK lists remote jobs only
            "salary": _format_salary(item.get("salary_min"), item.get("salary_max")),
            "description": description,
            "posted_at": item.get("date"),
        })
    return jobs
