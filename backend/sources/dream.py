"""Dream-company fetcher (Agent D — Dream Companies monitoring).

config.json -> dream_companies: [{name, url, ats?, slug?}]. On every refresh each
company's board is fetched REGARDLESS of the broad keyword filters; postings only
pass a light title filter (any config search.keyword OR the word "product").
Rows carry dream=True and source "dream-<ats>".

ATS detection (`resolve`) happens once per company — from the URL pattern, else by
probing the company name as a board slug — and is cached in the settings table
under `dream_resolved:<name>`.

Generic (non-ATS) careers pages are monitored by page-change detection: candidate
job links are snapshotted (`dream_snapshot:<name>`) and links NEW since the last
snapshot become job rows. The first-ever snapshot ingests current postings.
"""
import hashlib
import json
import re
import time
from urllib.parse import urljoin, urlsplit

import requests

from backend import db
from backend.sources import BROWSER_UA, DESCRIPTION_CAP, http_get, looks_remote, strip_html
from backend.sources import greenhouse as greenhouse_source
from backend.sources import lever as lever_source

# Order matters: first URL pattern that matches wins.
# Workday is special-cased in resolve(): its slug is "tenant.wdN/Site"
# (two capture groups), e.g. "draftkings.wd1/DraftKings".
ATS_URL_PATTERNS = [
    ("greenhouse", r"(?:boards|job-boards)\.greenhouse\.io/([A-Za-z0-9_.-]+)"),
    ("lever", r"jobs\.lever\.co/([A-Za-z0-9_.-]+)"),
    ("ashby", r"jobs\.ashbyhq\.com/([A-Za-z0-9_.%-]+)"),
    ("workable", r"apply\.workable\.com/([A-Za-z0-9_-]+)"),
    ("pinpoint", r"([A-Za-z0-9_-]+)\.pinpointhq\.com"),
    ("smartrecruiters", r"careers\.smartrecruiters\.com/([A-Za-z0-9_-]+)"),
    ("workday", r"([A-Za-z0-9-]+\.wd\d+)\.myworkdayjobs\.com(?:/[a-z]{2}-[A-Z]{2})?/([A-Za-z0-9_-]+)"),
    # TeamWork Online org/league portal: slug is the 3-segment path, e.g.
    # "football-jobs/footballjobs/nfl-football-jobs". A 4-segment posting URL
    # also matches its first 3 segments — that's the posting's org portal.
    ("teamworkonline", r"teamworkonline\.com/([A-Za-z0-9_-]+/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+)"),
]

SR_DETAIL_CAP = 40  # max per-posting description fetches per smartrecruiters refresh


# ---------- resolve ----------

def _slug_variants(name):
    """'Acme Corp.' -> ['acmecorp', 'acme-corp'] (lowercase, strip punctuation)."""
    lowered = str(name or "").lower()
    joined = re.sub(r"[^a-z0-9]+", "", lowered)
    hyphenated = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    variants = []
    for v in (joined, hyphenated):
        if v and v not in variants:
            variants.append(v)
    return variants


def _probe(ats, slug):
    """True if the slug is a live board on the given ATS (returns >=1 job)."""
    try:
        if ats == "greenhouse":
            resp = http_get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
            return resp.status_code == 200 and bool(resp.json().get("jobs"))
        if ats == "lever":
            resp = http_get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
            data = resp.json() if resp.status_code == 200 else None
            return isinstance(data, list) and len(data) > 0
        if ats == "ashby":
            resp = http_get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
            return resp.status_code == 200 and bool(resp.json().get("jobs"))
        if ats == "pinpoint":
            resp = http_get(f"https://{slug}.pinpointhq.com/postings.json")
            return resp.status_code == 200 and bool(resp.json().get("data"))
    except Exception:
        return False
    return False


def resolve(entry):
    """Detect {ats, slug} for a dream-company entry: explicit fields, then the URL
    pattern, then probing the company name as a slug. Falls back to {ats: "generic"}."""
    ats = entry.get("ats")
    if ats == "generic":
        return {"ats": "generic"}
    if ats and entry.get("slug"):
        return {"ats": ats, "slug": entry["slug"]}
    url = str(entry.get("url") or "")
    for ats_name, pattern in ATS_URL_PATTERNS:
        m = re.search(pattern, url)
        if m:
            if ats_name == "workday":
                return {"ats": "workday", "slug": f"{m.group(1)}/{m.group(2)}"}
            return {"ats": ats_name, "slug": m.group(1)}
    # Generic corporate careers URL: probe the company name as a board slug.
    for slug in _slug_variants(entry.get("name")):
        for ats_name in ("greenhouse", "lever", "ashby", "pinpoint"):
            if _probe(ats_name, slug):
                return {"ats": ats_name, "slug": slug}
    return {"ats": "generic"}


def _resolved_for(entry):
    """resolve() with a settings-table cache so probing happens once per company."""
    if entry.get("ats") and (entry.get("slug") or entry.get("ats") == "generic"):
        return {"ats": entry["ats"], "slug": entry.get("slug")}
    name = str(entry.get("name") or "").strip()
    key = f"dream_resolved:{name}"
    cached = db.get_setting(key)
    if cached:
        try:
            resolved = json.loads(cached)
            if resolved.get("ats"):
                return resolved
        except ValueError:
            pass
    resolved = resolve(entry)
    db.set_setting(key, json.dumps(resolved))
    return resolved


# ---------- per-ATS posting fetchers (raw, pre-filter) ----------

def _fetch_ashby(slug):
    resp = http_get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true")
    resp.raise_for_status()
    jobs = []
    for j in resp.json().get("jobs", []):
        if not j.get("id") or not j.get("title"):
            continue
        location = j.get("location") or ""
        salary = (j.get("compensation") or {}).get("compensationTierSummary")
        description = j.get("descriptionPlain") or strip_html(j.get("descriptionHtml"))
        jobs.append({
            "source": "ashby",
            "external_id": str(j["id"]),
            "url": j.get("jobUrl") or j.get("applyUrl"),
            "title": j["title"],
            "company": None,
            "location": location,
            "remote": bool(j.get("isRemote")) or looks_remote(location, j.get("workplaceType"), j["title"]),
            "salary": salary,
            "description": (description or "")[:DESCRIPTION_CAP],
            "posted_at": j.get("publishedAt"),
        })
    return jobs


def _fetch_pinpoint(slug):
    """Pinpoint boards serve the whole posting list as JSON at /postings.json.
    `location` is a nested object; the rest is flat. Talent-network evergreens
    are dropped — they are not real openings."""
    resp = http_get(f"https://{slug}.pinpointhq.com/postings.json")
    resp.raise_for_status()
    jobs = []
    for j in resp.json().get("data", []):
        title = (j.get("title") or "").strip()
        if not j.get("id") or not title:
            continue
        if "talent network" in title.lower() or "talent community" in title.lower():
            continue
        loc = j.get("location") or {}
        location = (loc.get("name") or loc.get("city") or "") if isinstance(loc, dict) else str(loc)
        description = strip_html(j.get("description")) or ""
        jobs.append({
            "source": "pinpoint",
            "external_id": str(j["id"]),
            "url": j.get("url") or j.get("path"),
            "title": title,
            "company": None,
            "location": location,
            "remote": looks_remote(location, j.get("workplace_type"), title),
            "salary": j.get("compensation") if j.get("compensation_visible") else None,
            "description": description[:DESCRIPTION_CAP],
            "posted_at": j.get("published_at") or j.get("created_at"),
        })
    return jobs


def _fetch_workable(slug):
    resp = http_get(f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true")
    resp.raise_for_status()
    data = resp.json()
    jobs = []
    for j in data.get("jobs", []):
        code = j.get("shortcode") or j.get("code") or j.get("id")
        if not code or not j.get("title"):
            continue
        location = ", ".join(x for x in (j.get("city"), j.get("state"), j.get("country")) if x)
        jobs.append({
            "source": "workable",
            "external_id": str(code),
            "url": j.get("url") or j.get("shortlink") or f"https://apply.workable.com/{slug}/j/{code}/",
            "title": j["title"],
            "company": data.get("name"),
            "location": location,
            "remote": bool(j.get("telecommuting")) or looks_remote(location, j["title"]),
            "salary": None,
            "description": strip_html(j.get("description") or ""),
            "posted_at": j.get("created_at"),
        })
    return jobs


def _fetch_smartrecruiters(slug):
    """List postings (first 100). Descriptions need one API call per posting, so
    they are filled later — only for postings that pass the light filter."""
    resp = http_get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100")
    resp.raise_for_status()
    jobs = []
    for p in resp.json().get("content", []):
        if not p.get("id") or not p.get("name"):
            continue
        loc = p.get("location") or {}
        location = ", ".join(x for x in (loc.get("city"), loc.get("region"), loc.get("country")) if x)
        jobs.append({
            "source": "smartrecruiters",
            "external_id": str(p["id"]),
            "url": f"https://jobs.smartrecruiters.com/{slug}/{p['id']}",
            "title": p["name"],
            "company": None,
            "location": location,
            "remote": bool(loc.get("remote")) or looks_remote(location, p["name"]),
            "salary": None,
            "description": "",
            "posted_at": p.get("releasedDate"),
        })
    return jobs


def _sr_fill_descriptions(slug, jobs):
    """Best-effort description fetch for filtered smartrecruiters postings."""
    for job in jobs[:SR_DETAIL_CAP]:
        try:
            resp = http_get(
                f"https://api.smartrecruiters.com/v1/companies/{slug}/postings/{job['external_id']}"
            )
            resp.raise_for_status()
            sections = ((resp.json().get("jobAd") or {}).get("sections") or {})
            parts = [s.get("text") for s in sections.values() if isinstance(s, dict) and s.get("text")]
            job["description"] = strip_html("\n\n".join(parts))
        except Exception:
            pass  # description stays "" — never crash the refresh


WD_PAGE_SIZE = 20
WD_MAX_POSTINGS = 400
WD_DETAIL_CAP = 40  # max per-posting description fetches per workday refresh


def _wd_parts(slug):
    """'draftkings.wd1/DraftKings' -> (host, tenant, site)."""
    tenant_wd, _, site = str(slug).partition("/")
    if not tenant_wd or not site:
        raise ValueError(f"workday slug must look like 'tenant.wdN/Site', got {slug!r}")
    return f"{tenant_wd}.myworkdayjobs.com", tenant_wd.split(".")[0], site


def _fetch_workday(slug):
    """Workday CXS list API (paginated POST). Descriptions are filled later for
    title-filtered postings only (see _wd_fill_descriptions)."""
    host, tenant, site = _wd_parts(slug)
    list_url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    jobs, offset, total = [], 0, None
    while offset < (WD_MAX_POSTINGS if total is None else min(total, WD_MAX_POSTINGS)):
        resp = requests.post(list_url, headers={**headers, "User-Agent": BROWSER_UA},
                             json={"limit": WD_PAGE_SIZE, "offset": offset, "searchText": ""},
                             timeout=15)
        resp.raise_for_status()
        data = resp.json()
        total = int(data.get("total") or 0)
        postings = data.get("jobPostings") or []
        if not postings:
            break
        for p in postings:
            path = p.get("externalPath") or ""
            title = p.get("title")
            if not path or not title:
                continue
            ext = (p.get("bulletFields") or [None])[0] or hashlib.sha1(
                path.encode("utf-8", "ignore")).hexdigest()[:16]
            location = p.get("locationsText") or ""
            jobs.append({
                "source": "workday",
                "external_id": str(ext),
                "url": f"https://{host}/{site}{path}",
                "title": title,
                "company": None,
                "location": location,
                "remote": looks_remote(location, title, p.get("remoteType")),
                "salary": None,
                "description": "",
                "posted_at": None,
                "_wd_detail": f"https://{host}/wday/cxs/{tenant}/{site}{path}",
            })
        offset += WD_PAGE_SIZE
    return jobs


def _wd_fill_descriptions(kept):
    """Fetch job descriptions for up to WD_DETAIL_CAP kept postings; never raises."""
    for p in kept[:WD_DETAIL_CAP]:
        detail_url = p.pop("_wd_detail", None)
        if not detail_url:
            continue
        try:
            resp = http_get(detail_url)
            if resp.status_code < 400:
                info = (resp.json() or {}).get("jobPostingInfo") or {}
                p["description"] = strip_html(info.get("jobDescription"))[:DESCRIPTION_CAP]
                p["posted_at"] = info.get("startDate") or None
        except Exception:
            pass  # description stays "" — never crash the refresh
    for p in kept[WD_DETAIL_CAP:]:
        p.pop("_wd_detail", None)


TWO_PAGE_CAP = 12    # max teamworkonline feed pages per refresh (48 cards/page)
TWO_DETAIL_CAP = 40  # max per-posting description fetches per teamworkonline refresh

# Job card on a server-rendered TeamWork Online org/league portal page:
# <h3 class="organization-portal__job-title"><a ... href="...">Title</a></h3>
# <p class="organization-portal__job-category">Org</p>
# <p class="organization-portal__job-location">City · ST</p>
_TWO_CARD = re.compile(
    r'(?is)organization-portal__job-title"[^>]*>\s*<a[^>]*href="([^"#]+)"[^>]*>(.*?)</a>'
    r'.*?organization-portal__job-category"[^>]*>(.*?)</p>'
    r'\s*<p[^>]*organization-portal__job-location"[^>]*>(.*?)</p>'
)


def _two_get_with_retry(url, attempts=3, backoff=8.0):
    """TeamWork Online 429s under load even with the per-host spacing in
    fetch_all — the last portal in the list absorbs the cumulative delay of
    every one before it. Back off and retry rather than dropping the company
    for the whole refresh; a 429 is throttling, not a dead feed."""
    last = None
    for i in range(attempts):
        resp = http_get(url)
        if resp.status_code != 429:
            return resp
        last = resp
        if i < attempts - 1:
            time.sleep(backoff * (i + 1))
    return last


def _fetch_teamworkonline(slug):
    """TeamWork Online portal feed (Rails, server-rendered, ?page=N pagination).
    League feeds (e.g. nfl-football-jobs) aggregate every team's postings, so the
    per-card org is kept as the job's company. Descriptions are filled later for
    title-filtered postings only (see _two_fill_descriptions)."""
    base = f"https://www.teamworkonline.com/{str(slug).strip('/')}"
    jobs, seen = [], set()
    for page in range(1, TWO_PAGE_CAP + 1):
        try:
            resp = _two_get_with_retry(f"{base}?page={page}")
            resp.raise_for_status()
        except Exception:
            if page == 1:
                raise  # a dead feed should surface as a per-company error
            break      # later-page hiccup: keep the partial results
        cards = _TWO_CARD.findall(resp.text or "")
        if not cards:
            break  # past the last page (TWO renders an empty portal, no cards)
        for href, raw_title, raw_org, raw_loc in cards:
            url = urljoin("https://www.teamworkonline.com/", href.strip())
            title = strip_html(raw_title, cap=300).strip()
            if not title or url in seen:
                continue
            seen.add(url)
            org = strip_html(raw_org, cap=200).strip()
            location = strip_html(raw_loc, cap=200).replace(" · ", ", ").strip()
            m = re.search(r"-(\d+)/?$", url)
            ext = m.group(1) if m else hashlib.sha1(url.encode("utf-8", "ignore")).hexdigest()[:16]
            jobs.append({
                "source": "teamworkonline",
                "external_id": ext,
                "url": url,
                "title": title,
                "company": org or None,
                "location": location,
                "remote": looks_remote(location, title),
                "salary": None,
                "description": "",
                "posted_at": None,
            })
    return jobs


def _two_fill_descriptions(kept):
    """Best-effort posting-page text for filtered TWO postings (capped); never raises."""
    for p in kept[:TWO_DETAIL_CAP]:
        p["description"] = _fetch_job_page_text(p["url"])[:DESCRIPTION_CAP]


def fetch_postings(ats, slug):
    """All postings for one board, normalized but not yet filtered/decorated."""
    if ats == "greenhouse":
        # Reuse Agent A's parsers by feeding them a single-slug watchlist.
        return greenhouse_source.fetch({"watchlist": {"greenhouse": [slug]}})
    if ats == "lever":
        return lever_source.fetch({"watchlist": {"lever": [slug]}})
    if ats == "ashby":
        return _fetch_ashby(slug)
    if ats == "workable":
        return _fetch_workable(slug)
    if ats == "pinpoint":
        return _fetch_pinpoint(slug)
    if ats == "smartrecruiters":
        return _fetch_smartrecruiters(slug)
    if ats == "workday":
        return _fetch_workday(slug)
    if ats == "teamworkonline":
        return _fetch_teamworkonline(slug)
    raise ValueError(f"unknown ATS {ats!r}")


# ---------- light relevance filter ----------

# "product" must match as a WORD. A bare substring test also matches
# "Production Coordinator", "Post-Production Intern", "Productivity" — which is
# how a theme-park stagecraft internship ends up in a product-management feed.
_PRODUCT_WORD = re.compile(r"(?i)\bproducts?(?:'s)?\b")


def _title_passes(title, config):
    """Dream companies cast a wider net: keep titles containing any configured
    search keyword OR the word 'product'."""
    t = str(title or "").lower()
    terms = [str(k).lower() for k in ((config.get("search") or {}).get("keywords") or []) if k]
    if any(term in t for term in terms):
        return True
    return bool(_PRODUCT_WORD.search(t))


# ---------- generic careers-page fallback (page-change detection) ----------

_HREF_JOBISH = re.compile(
    r"(?i)(/jobs?/|/careers?/.|/positions?\b|/openings?\b|/opportunit|/vacanc|/roles?/"
    r"|greenhouse\.io|lever\.co|ashbyhq\.com|workable\.com|smartrecruiters\.com"
    r"|myworkdayjobs\.com|/apply\b|gh_jid=)"
)
_TEXT_JOBISH = re.compile(
    r"(?i)\b(engineer|engineering|manager|director|designer|developer|analyst|scientist"
    r"|architect|specialist|lead|counsel|recruiter|marketing|intern|product|associate"
    r"|coordinator|head of|apply)\b"
)


# Anchor text that is a call to action, not a job title. Plenty of careers pages
# (Bally's among them) put the real title in a sibling heading outside the <a>
# and label every link "View Job" — which would otherwise yield a page of
# identically-named placeholder rows.
_CTA_ONLY = re.compile(
    r"(?i)^(view|see|read)?\s*(job|jobs|role|position|opening|posting|details|more|"
    r"more info|apply|apply now|learn more|view details|view job|view role|view opening|"
    r"join|join us|full details)\s*(details|now|here|>|»|→)?$"
)
# Trailing path noise: numeric ids, uuids, and locale/paging segments.
_PATH_NOISE = re.compile(r"(?i)^([0-9]+|[0-9a-f]{8}-[0-9a-f-]{20,}|[0-9a-f]{24,}|en|en-us|us|apply)$")


def _title_from_url(url):
    """Derive a human title from a job URL's slug. Careers pages that label every
    link 'View Job' almost always still carry the title in the path, e.g.
    /job/jersey-city/.../casino-retention-coordinator/<uuid> -> 'Casino Retention
    Coordinator'. Returns '' when no segment looks like a title."""
    path = urlsplit(url).path
    segments = [seg for seg in path.split("/") if seg]
    while segments and _PATH_NOISE.match(segments[-1]):
        segments.pop()
    if not segments:
        return ""
    slug = re.sub(r"\.(html?|aspx|php)$", "", segments[-1], flags=re.I)
    words = [w for w in re.split(r"[-_+%20]+", slug) if w]
    # A single word, or something that is mostly digits, is not a job title.
    if len(words) < 2 or sum(c.isdigit() for c in slug) > len(slug) / 2:
        return ""
    return " ".join(w[:1].upper() + w[1:] for w in words)


def extract_job_links(careers_url):
    """Fetch a careers page and return candidate job links [{title, url}] — <a> tags
    whose href or text looks job-ish. Raises on page-fetch failure."""
    resp = http_get(careers_url)
    resp.raise_for_status()
    links, seen = [], set()
    for m in re.finditer(r'(?is)<a\b[^>]*href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', resp.text or ""):
        href = m.group(1).strip()
        if href.lower().startswith(("mailto:", "javascript:", "tel:")):
            continue
        # Card-style links wrap title + location + type; the first line is the title.
        title = strip_html(m.group(2), cap=300).strip().split("\n", 1)[0].strip()
        url = urljoin(careers_url, href)
        # "View Job" and friends carry no information — recover the title from the
        # URL slug instead, and drop the link only if that fails too.
        if not title or _CTA_ONLY.match(title):
            derived = _title_from_url(url)
            if not derived:
                continue
            title = derived
        if not (_HREF_JOBISH.search(href) or _TEXT_JOBISH.search(title)):
            continue
        if url.rstrip("/") == careers_url.rstrip("/") or url in seen:
            continue
        seen.add(url)
        links.append({"title": title, "url": url})
    return links


def _fetch_job_page_text(url):
    """Best-effort plain text of a job page (capped). Never raises."""
    try:
        resp = http_get(url)
        if resp.status_code >= 400:
            return ""
        return strip_html(resp.text)
    except Exception:
        return ""


def _fetch_generic(entry, config):
    """Diff the careers page's job links against the previous snapshot; NEW links
    become job rows. The first-ever snapshot ingests current postings."""
    name = str(entry.get("name") or "").strip() or entry.get("url") or "dream company"
    links = extract_job_links(entry["url"])
    key = f"dream_snapshot:{name}"
    previous_raw = db.get_setting(key)
    if previous_raw is None:
        new_links = links  # first run: don't make the user wait for the next change
    else:
        try:
            previous_urls = {l.get("url") for l in json.loads(previous_raw)}
        except ValueError:
            previous_urls = set()
        new_links = [l for l in links if l["url"] not in previous_urls]
    db.set_setting(key, json.dumps(links))

    jobs = []
    for link in new_links:
        # Generic pages include hiring announcements ("ETR is hiring: ...") whose
        # titles rarely contain "product" — let those through too.
        if not (_title_passes(link["title"], config) or "hiring" in link["title"].lower()):
            continue
        description = _fetch_job_page_text(link["url"])
        jobs.append({
            "source": "dream-generic",
            "external_id": hashlib.sha1(link["url"].encode("utf-8", "ignore")).hexdigest()[:16],
            "url": link["url"],
            "title": link["title"],
            "company": name,
            "location": "",
            "remote": looks_remote(link["title"], description[:2000]),
            "salary": None,
            "description": description,
            "posted_at": None,
            "dream": True,
        })
    return jobs


# ---------- top-level entry points ----------

def fetch_company(entry, config):
    """All current postings for one dream company, lightly filtered, normalized,
    decorated with dream=True and source 'dream-<ats>'."""
    name = str(entry.get("name") or "").strip()
    resolved = _resolved_for(entry)
    ats = resolved["ats"]
    if ats == "generic":
        return _fetch_generic(entry, config)
    postings = fetch_postings(ats, resolved["slug"])
    kept = [p for p in postings if _title_passes(p.get("title"), config)]
    if ats == "smartrecruiters":
        _sr_fill_descriptions(resolved["slug"], kept)
    if ats == "workday":
        _wd_fill_descriptions(kept)
    if ats == "teamworkonline":
        _two_fill_descriptions(kept)
    for p in kept:
        p["source"] = f"dream-{ats}"
        if ats == "teamworkonline":
            # League feeds aggregate many orgs — keep the per-card team/org.
            p["company"] = p.get("company") or name
        else:
            p["company"] = name or p.get("company")
        p["dream"] = True
    return kept


# TeamWork Online rate-limits hard: several portals fetched back-to-back start
# returning 429 partway through. Space consecutive requests to that host instead
# of losing whichever companies happen to come last in the list.
THROTTLED_HOSTS = {"teamworkonline": 6.0}   # seconds between requests, per ATS


def _throttle_key(entry):
    ats = (entry.get("ats") or "").lower()
    if ats in THROTTLED_HOSTS:
        return ats
    return "teamworkonline" if "teamworkonline.com" in str(entry.get("url") or "") else None


def fetch_all(config):
    """(jobs, errors) across config['dream_companies']; one bad company never
    kills the rest. Requests to rate-limited hosts are spaced out."""
    jobs, errors = [], []
    last_hit = {}
    for entry in (config or {}).get("dream_companies") or []:
        label = entry.get("name") or entry.get("url") or "?"
        key = _throttle_key(entry)
        if key:
            gap = THROTTLED_HOSTS[key]
            elapsed = time.monotonic() - last_hit.get(key, 0.0)
            if last_hit.get(key) and elapsed < gap:
                time.sleep(gap - elapsed)
            last_hit[key] = time.monotonic()
        try:
            jobs.extend(fetch_company(entry, config))
        except Exception as e:
            errors.append(f"dream {label}: {e}")
    return jobs, errors


def fetch(config):
    """Registry-compatible wrapper (FETCHERS contract: config -> list[job dict]).
    The refresh route calls fetch_all directly to surface per-company errors."""
    return fetch_all(config)[0]
