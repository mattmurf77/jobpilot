"""Deterministic JD-vs-profile scoring. No LLM, no network — fast and repeatable.

score_job(job, profile, config) -> int 0-100. Weighted components:
  1. target-title phrase in job title ........ 30 (core-title partial: 18)
  2. seniority term in job title ............. 10
  3. profile keyword overlap in description .. 30 (diminishing returns)
  4. domain-term hits (title + description) .. 20 (diminishing returns)
  5. location / remote preference ............ 10 (remote_only miss: -15)
  6. dream-company boost ...................... +search.dream_score_boost (default 15)

extract_keywords_hit(job, profile) -> list of profile terms found in the job,
used by the UI to explain "why this scored 78".
"""
import re


def _norm(s):
    return re.sub(r"\s+", " ", str(s or "").lower()).strip()


def _has_phrase(text, phrase):
    """Whole-phrase match with word-ish boundaries (handles terms like '0-to-1')."""
    if not phrase:
        return False
    return re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text) is not None


DEFAULT_LADDER = ["intern", "associate", "junior", "", "senior", "lead", "staff",
                  "principal", "group", "director", "head of", "vp", "vice president"]


def current_level(search, profile):
    """search.current_level, else the highest ladder term found in
    profile.current_title (e.g. "Lead Product Manager, Growth" -> "lead")."""
    explicit = _norm(search.get("current_level"))
    ladder = [_norm(t) for t in (search.get("title_ladder") or DEFAULT_LADDER)]
    if explicit and explicit in ladder:
        return explicit
    title = _norm((profile or {}).get("current_title"))
    found = [t for t in ladder if t and _has_phrase(title, t)]
    return max(found, key=ladder.index) if found else None


def ladder_delta(title, search, profile):
    """Rungs between the job title's level and the candidate's current level
    (positive = step up, 0 = lateral, negative = step down). None when either
    side is unknown. An untitled rung ("") in the ladder stands for a bare,
    unqualified title (plain "Product Manager")."""
    ladder = [_norm(t) for t in (search.get("title_ladder") or DEFAULT_LADDER)]
    cur = current_level(search, profile)
    if cur is None or cur not in ladder:
        return None
    found = [i for i, t in enumerate(ladder) if t and _has_phrase(_norm(title), t)]
    if found:
        return max(found) - ladder.index(cur)
    if "" in ladder:
        return ladder.index("") - ladder.index(cur)
    return None


def _title_core(title_phrase, seniority_terms):
    """'lead product manager' -> 'product manager' (strip leading seniority words)."""
    words = title_phrase.split()
    while words and words[0] in seniority_terms:
        words = words[1:]
    return " ".join(words)


# Location credit. A bare substring test against ["New York", "Remote"] gets
# things exactly backwards ("NYC, SF, Seattle" misses, "Remote Poland" matches),
# so: home-city aliases (profile city/state/location + search.locations) count,
# and "remote" counts unless the posting pins it to another country/metro.
_US_ALIASES = (
    "us", "u.s.", "usa", "u.s.a.", "united states", "america", "americas",
    "nationwide", "anywhere in the us", "remote us",
)
# Countries/regions/metros that commonly appear as "Remote <X>". Any that match
# the candidate's own country/city are removed at runtime.
_ELSEWHERE_REMOTE = (
    "canada", "uk", "united kingdom", "england", "ireland", "poland", "spain",
    "portugal", "germany", "france", "netherlands", "india", "singapore",
    "australia", "brazil", "mexico", "japan", "china", "emea", "apac", "latam",
    "europe", "philippines", "argentina", "colombia", "romania", "ukraine",
    "israel", "nigeria", "kenya", "south africa", "new zealand", "korea",
    "united states", "usa",
    # Major metros that appear without their country in location strings.
    "london", "dublin", "berlin", "paris", "amsterdam", "madrid", "barcelona",
    "lisbon", "warsaw", "krakow", "bucharest", "toronto", "vancouver",
    "montreal", "bengaluru", "bangalore", "hyderabad", "mumbai", "delhi", "pune",
    "chennai", "tokyo", "osaka", "seoul", "shanghai", "beijing", "shenzhen",
    "hong kong", "taipei", "sydney", "melbourne", "auckland", "dubai",
    "tel aviv", "sao paulo", "s\u00e3o paulo", "buenos aires", "bogota",
    "mexico city", "guadalajara", "manila", "jakarta", "bangkok", "edinburgh",
    "manchester", "glasgow", "belfast", "cork", "zurich", "geneva", "milan",
    "stockholm", "copenhagen", "oslo", "helsinki", "prague", "budapest",
    "chiba-ken",
)
_COUNTRY_ALIASES = {
    "united states": _US_ALIASES,
    "usa": _US_ALIASES,
    "us": _US_ALIASES,
    "united kingdom": ("uk", "united kingdom", "england", "scotland", "wales", "britain"),
    "canada": ("canada", "canadian"),
}


# Common ways postings abbreviate a metro; extended automatically when the
# candidate's home city is one of these.
_METRO_ALIASES = {
    "new york": ("nyc", "new york city", "ny metro", "manhattan", "brooklyn", "new york, ny"),
    "san francisco": ("sf", "bay area", "san francisco bay area", "sf bay area", "south bay"),
    "los angeles": ("la", "los angeles metro", "santa monica"),
    "washington": ("dc", "washington dc", "washington, dc", "d.c.", "dmv"),
    "boston": ("greater boston", "cambridge, ma"),
    "chicago": ("chicagoland",),
    "seattle": ("greater seattle", "bellevue", "redmond"),
    "austin": ("austin metro",),
    "london": ("greater london",),
}


def home_terms(profile, search):
    """City/state/location aliases identifying the candidate's home base:
    profile city/state/location, search.locations (minus 'remote'), and known
    metro nicknames."""
    raw = [profile.get("city"), profile.get("state"), profile.get("location")]
    raw += list(search.get("locations") or [])
    terms = set()
    for t in raw:
        t = _norm(t)
        if not t or t == "remote":
            continue
        terms.add(t)
        for part in re.split(r"[,/]", t):
            part = part.strip()
            if len(part) >= 2:
                terms.add(part)
    for city, aliases in _METRO_ALIASES.items():
        if city in terms:
            terms.update(aliases)
    return sorted(terms, key=len, reverse=True)


def home_country_terms(profile):
    country = _norm(profile.get("country"))
    return tuple(_COUNTRY_ALIASES.get(country, (country,) if country else ()))


_PRODUCT_WORD = re.compile(r"(?i)(?<!\w)products?(?:'s)?(?!\w)")
_PRODUCT_FAMILY = re.compile(
    r"(?i)(?<!\w)product\s+(operations|ops|strategy|management|platform)(?!\w)"
)


def _word_in(text, term):
    """Whole-token containment: 'ny' must not match inside 'company'."""
    return re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text) is not None


def _location_credit(job, search, profile=None):
    """True when a posting is reachable from the candidate's home base: an
    explicit home-city location, or remote that is not pinned to another
    country/metro."""
    profile = profile or {}
    location = _norm(job.get("location"))
    remote_flag = bool(job.get("remote"))

    homes = home_terms(profile, search)
    if any(_word_in(location, a) for a in homes):
        return True

    mentions_remote = remote_flag or "remote" in location or "distributed" in location
    if not mentions_remote:
        return False
    # Remote, but pinned to a country/metro the candidate cannot work from.
    own = set(homes) | set(home_country_terms(profile))
    if any(_word_in(location, c) for c in _ELSEWHERE_REMOTE if c not in own):
        return False
    # Remote with a home-country qualifier, or remote with no country named at all.
    return True


_BOILERPLATE_SPLIT = re.compile(
    r"(?i)\b(about the role|the role|role overview|what you.ll do|what you will do"
    r"|responsibilities|in this role|position summary|job summary|your impact"
    r"|what you.ll be doing|the opportunity|about this role)\b"
)


def _role_body(desc):
    """The role-specific part of a description, with leading company boilerplate
    removed. Falls back to the whole text when no section header is found."""
    if not desc:
        return ""
    m = _BOILERPLATE_SPLIT.search(desc)
    if m and len(desc) - m.start() >= 200:
        return desc[m.start():]
    return desc


def score_job(job, profile, config):
    title = _norm(job.get("title"))
    desc = _norm(job.get("description"))
    search = (config or {}).get("search") or {}

    seniority = {_norm(t) for t in profile.get("seniority_terms", []) if t}
    target_titles = {_norm(t) for t in profile.get("target_titles", []) if t}
    target_titles |= {_norm(k) for k in search.get("keywords", []) if k}
    keywords = {_norm(k) for k in profile.get("keywords", []) if k}
    domains = {_norm(d) for d in search.get("domain_terms", []) if d}
    domains |= {_norm(d) for d in profile.get("target_domains", []) if d}

    score = 0.0

    # 1. Target-title phrase in the job title (high weight).
    title_core_matched = False
    if any(_has_phrase(title, t) for t in target_titles):
        score += 30
        title_core_matched = True
    else:
        cores = {_title_core(t, seniority) for t in target_titles}
        if any(c and _has_phrase(title, c) for c in cores):
            score += 18
            title_core_matched = True

    # 2. Seniority term in the job title.
    if any(_has_phrase(title, s) for s in seniority):
        score += 10

    # 2b. Career-direction bias (config search.career_bias = "up_or_lateral"):
    # the job title's rung on search.title_ladder relative to the candidate's
    # current level (search.current_level, or derived from profile.current_title).
    # Upward titles are boosted, the current rung is the lateral baseline, each
    # rung down costs more. Below-level titles are below level whatever the
    # function — this must not depend on the word "product" appearing.
    below_level = re.search(r"(?<!\w)(associate|junior|intern|apm|entry)(?!\w)", title)

    if search.get("career_bias", "up_or_lateral") == "up_or_lateral":
        if title_core_matched:
            delta = ladder_delta(title, search, profile)
            if below_level:
                score -= 20  # clearly below level
            elif delta is None:
                pass         # no level information: neutral
            elif delta >= 2:
                score += 8   # clearly upward
            elif delta == 1:
                score += 4   # one rung up
            elif delta == -1:
                score -= 5   # one rung down
            elif delta <= -2:
                score -= 10  # two or more rungs down
        elif _PRODUCT_FAMILY.search(title):
            # "Product Operations Manager", "Product Strategy Lead" — adjacent
            # product-org work ("AI product operations" is a stated target
            # domain). No title credit above, but no penalty either.
            if below_level:
                score -= 20
        elif _PRODUCT_WORD.search(title):
            # The word "product" without a product-management title: sales,
            # support, and engineering reqs ("Account Executive, Product Sales").
            # Word-boundary matched, so "Video Production" is not caught here.
            score -= 20 if below_level else 10
        elif below_level:
            score -= 20

    # 3. Profile keyword overlap in the description, diminishing returns.
    # Scored against the role-specific body only: large employers prefix every
    # posting with identical company boilerplate, which otherwise makes a
    # payments PM and a customer-success rep at the same company score alike.
    kw_hits = sum(1 for k in keywords if _has_phrase(_role_body(desc), k))
    score += 30 * (1 - 0.85 ** kw_hits)

    # 4. Domain-term hits across title + description, diminishing returns.
    blob = title + "\n" + desc
    dom_hits = sum(1 for d in domains if _has_phrase(blob, d))
    score += 20 * (1 - 0.7 ** dom_hits)

    # 5. Location / remote preference.
    if _location_credit(job, search, profile):
        score += 10
    if search.get("remote_only") and not bool(job.get("remote")):
        score -= 15

    # 6. Dream-company boost (config search.dream_score_boost, default 15).
    if job.get("dream"):
        try:
            score += float(search.get("dream_score_boost", 15))
        except (TypeError, ValueError):
            score += 15

    return max(0, min(100, round(score)))


def extract_keywords_hit(job, profile):
    """Profile terms (target titles, seniority, keywords, domains) found in the
    job title or description. Order: titles, seniority, keywords, domains."""
    blob = _norm(job.get("title")) + "\n" + _norm(job.get("description"))
    hits, seen = [], set()
    for term in (
        list(profile.get("target_titles", []))
        + list(profile.get("seniority_terms", []))
        + list(profile.get("keywords", []))
        + list(profile.get("target_domains", []))
    ):
        n = _norm(term)
        if n and n not in seen and _has_phrase(blob, n):
            seen.add(n)
            hits.append(term)
    return hits
