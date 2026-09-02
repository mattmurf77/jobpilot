"""ATS detection: classify a job URL as greenhouse / lever / other and derive the apply URL."""
from urllib.parse import urlparse

GREENHOUSE_HOSTS = {"boards.greenhouse.io", "job-boards.greenhouse.io"}
LEVER_HOSTS = {"jobs.lever.co"}


def detect_ats(url):
    """Return {"ats": "greenhouse"|"lever"|"other", "apply_url": str}.

    - Greenhouse: the apply form lives on the posting page itself (anchor #app/#application).
    - Lever: the apply form lives at <posting-url>/apply.
    """
    if not url:
        return {"ats": "other", "apply_url": url or ""}
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return {"ats": "other", "apply_url": url}

    if host in GREENHOUSE_HOSTS:
        apply_url = url if "#" in url else url + "#app"
        return {"ats": "greenhouse", "apply_url": apply_url}

    if host in LEVER_HOSTS:
        base = url.split("#")[0].split("?")[0].rstrip("/")
        apply_url = base if base.endswith("/apply") else base + "/apply"
        return {"ats": "lever", "apply_url": apply_url}

    return {"ats": "other", "apply_url": url}
