# Integration notes — Agent D (Dream Companies monitoring)

One shared-file change is required; everything else landed in my own files.

## 1. `backend/routes_submit.py` — add `dream_companies` to `EXPECTED_CONFIG_KEYS` (REQUIRED)

Line 20:

```python
EXPECTED_CONFIG_KEYS = {"search", "watchlist", "materials", "tailoring", "features"}
```

must become:

```python
EXPECTED_CONFIG_KEYS = {"search", "watchlist", "materials", "tailoring", "features", "dream_companies"}
```

Why: `config.json` now has a top-level `dream_companies` key (orchestrator schema change +
my seeds). The Settings tab round-trips the FULL config through `POST /api/settings/config`,
which currently rejects it with `config has unknown keys: dream_companies` (400). This breaks
**every** Settings save (search, watchlist, dream card), not just my feature — it is a
pre-existing integration gap from the config schema change, surfaced by my testing.

`routes_submit.py` is not in my assigned file list, so I did not touch it.

## 2. FYI (no action needed)

- `web/js/app.js` / `index.html` / `style.css`: no changes needed — the Dream UI reuses
  existing helpers and scoped styles injected from my own JS files.
- New settings-table keys in use: `dream_resolved:<name>` (cached ATS resolution) and
  `dream_snapshot:<name>` (generic-page link snapshots). Removing a dream company in the UI
  does not delete these rows; they are harmless and reused if the company is re-added.
