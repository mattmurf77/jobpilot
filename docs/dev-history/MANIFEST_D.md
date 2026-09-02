# MANIFEST — Agent D (Dream Companies monitoring)

Date: 2026-06-10

## Files written / edited

| File | Change |
|---|---|
| `backend/sources/dream.py` | NEW. `resolve` (URL-pattern ATS detection + name-as-slug probing), per-ATS fetchers (greenhouse/lever reuse Agent A's parsers via single-slug watchlists; ashby/workable/smartrecruiters new), light title filter (config keywords OR "product"), generic careers-page fallback with snapshot diffing, `fetch_company` / `fetch_all` / registry-compatible `fetch` |
| `backend/sources/__init__.py` | Registered `"dream": dream.fetch` in `FETCHERS` |
| `backend/matching.py` | Component 6: `+search.dream_score_boost` (default 15) for `dream` jobs, inside the existing 0–100 clamp; deterministic |
| `backend/routes_jobs.py` | `GET /` accepts `dream=1` → `list_jobs(dream_only=True)`; refresh returns `new_dream` + per-dream-source counts (`dream-greenhouse`, `dream-ashby`, …) with per-company error isolation; NEW `POST /dream/resolve` |
| `web/js/find.js` | 💜 Dream filter chip, 💜 Dream badge on cards + detail drawer, refresh toast appends "N from dream companies" when > 0 |
| `web/js/settings.js` | "💜 Dream companies" card after Watchlist: rows (name, URL, ATS chip, postings count, Remove), add form with "Test & add" → `/dream/resolve`, inline result (detected ATS + sample titles), hint line; scoped styles in the existing style block |
| `config.json` | Seeded `dream_companies`: Anthropic (greenhouse), OpenAI (ashby), Chime (greenhouse) — all verified live |
| `INTEGRATION_NOTES_D.md` | One required orchestrator change (see Known gaps) |

## New settings-table keys

- `dream_resolved:<name>` — cached `{ats, slug}` so probing runs once per company
- `dream_snapshot:<name>` — `[{title, url}]` link snapshot for generic careers pages

## Verification results

1. **py_compile** — all 4 backend files: PASS.
2. **App constructs** — `create_app()` OK; url_map includes `/api/jobs/dream/resolve`.
3. **Live `POST /api/jobs/dream/resolve`** (real network, Flask test client):
   - Anthropic → greenhouse/anthropic, **373 postings**
   - OpenAI → ashby/openai, **724 postings**
   - Chime (generic `careers.chime.com/jobs/` URL → name-probe path) → greenhouse/chime, **67 postings**
   - Error paths: missing url → 400; non-http url → 400.
4. **Live `POST /api/jobs/refresh`** — 200 in 11s, no errors. fetched 1390, new 316, **new_dream 94**. Per source: dream-ashby 56 (OpenAI), dream-greenhouse 38 (Anthropic 26 + Chime 12), greenhouse 1041, lever 222, remoteok 6, remotive 27.
5. **`GET /api/jobs/?dream=1`** — 200, 94 jobs, all `dream=1`. Boost verified: top job ("Product Manager, Consumer" @ Anthropic) scores 77 with the flag vs 62 without (+15). Combo filters (`dream=1&q=product&min_score=70` → 7) work.
6. **Generic fallback (real page: `oxide.computer/careers`)** — resolve → `generic` (after probing); first run ingested 9 jobs (source `dream-generic`, dream=True, real 5–8k-char descriptions); second run → 0 (idempotent); after removing one link from the stored snapshot, third run re-detected exactly that 1 link. Test settings rows deleted afterward (no fixtures, no job rows created).
7. **Browser preview (port 5252, zero console errors/warnings)** — 💜 Dream chip filters to 94 cards, every card and the detail drawer show the 💜 badge; Settings card renders after Watchlist with all 3 seed rows (ATS chips, Remove buttons); live "Test & add" with Ramp → inline "✓ Ramp: detected ashby (slug ramp) — 110 postings found" + 5 sample titles. Append-to-config blocked by the config-key allowlist (see below); test row cleaned up.
8. **JS** — `node --check` PASS on both files; all referenced element ids exist in their module's own rendered HTML.

## DB state left for the orchestrator

1,392 jobs (the pre-existing 1,076 untouched; +316 new from the live refresh, of which 94 dream rows from Anthropic/OpenAI/Chime — real data, kept per instructions). Settings table has only the 3 seed `dream_resolved:*` rows.

## Known gaps

- **REQUIRED orchestrator fix** (`INTEGRATION_NOTES_D.md`): add `"dream_companies"` to `EXPECTED_CONFIG_KEYS` in `backend/routes_submit.py` (not my file). Until then `POST /api/settings/config` 400s on the now-present `dream_companies` key — this blocks ALL Settings saves (search/watchlist too), not just the dream card. The dream card's test+resolve works now; the final append-and-save will work as soon as the key is allowed.
- SmartRecruiters descriptions need one API call per posting — fetched only for postings passing the light filter, capped at 40 per refresh (`SR_DETAIL_CAP`); list fetch reads the first 100 postings.
- Generic fallback can't see JS-rendered careers pages (e.g. fly.io yields only an RSS link); ATS boards are the designed path, and the Settings hint says so.
- Removing a dream company leaves its `dream_resolved:`/`dream_snapshot:` settings rows (harmless; reused on re-add) and keeps already-ingested jobs (by design — they're real postings).
