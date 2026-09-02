"""Job source fetchers (Agent A).

Each submodule exposes `fetch(config) -> list[dict]` returning normalized job
dicts matching backend.db.upsert_job keys:
    source, external_id, url, title, company, location, remote (bool),
    salary (str|None), description (plain text), posted_at (ISO str|None)

`FETCHERS` at the bottom is the registry the refresh endpoint iterates.
Shared HTTP/HTML helpers live here so submodules stay tiny.
"""
import html as _html
import re

import requests

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
TIMEOUT = 15  # seconds, per request
DESCRIPTION_CAP = 20000  # chars


def http_get(url, **kwargs):
    """GET with a real browser UA and a hard timeout."""
    headers = {
        "User-Agent": BROWSER_UA,
        "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
    }
    headers.update(kwargs.pop("headers", {}))
    return requests.get(url, headers=headers, timeout=TIMEOUT, **kwargs)


def strip_html(raw, cap=DESCRIPTION_CAP):
    """HTML -> readable plain text: drop script/style, keep paragraph/list breaks,
    unescape entities, collapse whitespace, cap length."""
    if not raw:
        return ""
    text = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", str(raw))
    text = re.sub(r"(?i)<br\s*/?\s*>", "\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "\n- ", text)
    text = re.sub(r"(?i)</(p|div|li|ul|ol|h[1-6]|tr|section|article|header)>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = _html.unescape(text)
    text = re.sub(r"[ \t\r\xa0]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    if cap and len(text) > cap:
        text = text[:cap]
    return text


def looks_remote(*fields):
    """True if any provided string mentions 'remote'."""
    return any("remote" in str(f or "").lower() for f in fields)


# Imported after helpers so submodules can `from backend.sources import http_get, ...`
from backend.sources import greenhouse, lever, remoteok, remotive, dream, ashby  # noqa: E402

FETCHERS = {
    "greenhouse": greenhouse.fetch,
    "lever": lever.fetch,
    "ashby": ashby.fetch,
    "remoteok": remoteok.fetch,
    "remotive": remotive.fetch,
    # Dream companies (Agent D): fetch isolates per-company errors internally;
    # the refresh route calls dream.fetch_all directly for per-company error detail.
    "dream": dream.fetch,
}
