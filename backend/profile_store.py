"""Load/save the candidate profile.

data/profile.example.json  - tracked, a blank template
data/profile.json          - gitignored, the user's own profile; created from
                             the example on first load (or by scripts/onboard.py).
"""
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_PATH = os.path.join(ROOT, "data", "profile.json")
PROFILE_EXAMPLE_PATH = os.path.join(ROOT, "data", "profile.example.json")


def _ensure_profile():
    if not os.path.exists(PROFILE_PATH) and os.path.exists(PROFILE_EXAMPLE_PATH):
        os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
        shutil.copyfile(PROFILE_EXAMPLE_PATH, PROFILE_PATH)


def load_profile():
    _ensure_profile()
    with open(PROFILE_PATH) as f:
        return json.load(f)


def save_profile(profile):
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
    with open(PROFILE_PATH, "w") as f:
        json.dump(profile, f, indent=2)
    return profile


def display_name(profile):
    """Full name for documents; falls back to first+last, then a placeholder."""
    name = (profile.get("name") or "").strip()
    if not name:
        name = " ".join(x for x in [profile.get("first_name"), profile.get("last_name")] if x).strip()
    return name or "Your Name"


def file_stem(profile):
    """Name for generated filenames: preferred + last name when a preferred
    name is set ('Matt_Murphy'), else the full name ('Jane_Q_Doe')."""
    import re
    preferred = (profile.get("preferred_name") or "").strip()
    last = (profile.get("last_name") or "").strip()
    name = f"{preferred} {last}".strip() if preferred and last else display_name(profile)
    stem = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
    return stem or "Resume"


def signature(profile):
    """Sign-off name for letters (full name, per the voice guide)."""
    return display_name(profile)
