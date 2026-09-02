# MANIFEST — Agent A (Job discovery & scoring, feature F1)

Date: 2026-06-10

## Files written

| File | What it is |
|---|---|
| `backend/sources/__init__.py` | Shared HTTP/HTML helpers (browser UA, 15s timeout, HTML→text stripper) + `FETCHERS` registry |
| `backend/sources/greenhouse.py` | Greenhouse boards API per watchlist slug (`content=true`, unescape + strip HTML) |
| `backend/sources/lever.py` | Lever postings API per watchlist slug (`descriptionPlain`, `createdAt` ms → ISO) |
| `backend/sources/remoteok.py` | RemoteOK feed (browser UA, skips metadata element 0, client-side keyword filter, salary_min/max formatting) |
| `backend/sources/remotive.py` | Remotive search per config keyword (limit 50, HTML→text, dedupe across keywords) |
| `backend/sources/manual.py` | Manual ingest: URL fetch (title/company parse from `<title>`, visible text ≤20k chars) and/or pasted JD; never raises — returns error strings |
| `backend/matching.py` | `score_job` (0–100, deterministic) + `extract_keywords_hit` (terms list for "why this scored N") |
| `backend/routes_jobs.py` | Replaced stub with the full `/api/jobs` blueprint |
| `web/js/find.js` | Replaced stub: full Find tab (toolbar, chips, card grid, detail drawer, manual-add form), `<style id="style-find">`, `TabHooks["find"]` |

## Endpoints implemented (prefix `/api/jobs` set in app.py)

- `GET /api/jobs/` — filters `status` (comma list, validated), `min_score` (int, 400 on garbage), `q` (title/company/description LIKE)
- `GET /api/jobs/<id>` — job + `score_reasons` (matched profile terms); 404 when missing
- `POST /api/jobs/refresh` — all 4 fetchers, per-source AND per-job try/except; upserts via `db.upsert_job`; scores **new** jobs only (never clobbers user state); returns `{fetched, new, per_source, errors}`
- `POST /api/jobs/<id>/status` — validates against `db.JOB_STATUSES`, optional `notes`, logs `status_change`
- `POST /api/jobs/manual` — ingests `{url?, title?, company?, description?}`, status starts `new`, scored, logs `fetched`, returns job + `score_reasons` + `created`

## Scoring model (matching.py)

Title phrase match 30 (core-title partial 18) + seniority-in-title 10 + profile-keyword overlap in JD 30 (diminishing, 0.85^n) + domain terms 20 (diminishing, 0.7^n) + location/remote 10; `remote_only` miss −15; clamped 0–100. Word-boundary phrase matching handles terms like "0-to-1" and "AI".

## Verification results (all CONTRACTS.md steps run)

1. **py_compile** — all 8 backend files: PASS.
2. **App constructs / routes registered** — `create_app()` OK; url_map shows `/api/jobs/`, `/api/jobs/<int:job_id>`, `/api/jobs/<int:job_id>/status`, `/api/jobs/manual`, `/api/jobs/refresh`.
3. **Real network calls via Flask test client** (DB now seeded with this data):
   - `POST /refresh` → 200, **fetched 1074, new 1074**. Per source (real jobs returned):
     - **greenhouse: 1041** (stripe, ramp, brex, plaid, affirm, gusto, mercury, lithic)
     - **lever: 0** — both configured slugs (`highnote`, `found`) 404; fetcher verified working against live boards (palantir → 222 jobs, octoenergy → 164). See `INTEGRATION_NOTES_A.md`.
     - **remoteok: 6** (after client-side keyword filter)
     - **remotive: 27** (deduped across 4 keyword searches)
   - List: 200, 500 jobs (db limit). Scores 32–88; 24 jobs ≥70. Top: "Principal Product Manager, Cash Flow" @ Gusto, score 88, reasons incl. lending/SMB/AI.
   - Filters: `status=new&min_score=70&q=product` → 24; `min_score=abc` → 400; `status=bogus` → 400.
   - Get one → 200 with `score_reasons`; missing id → 404.
   - Status: → interested 200; invalid status → 400; logged `status_change` events confirmed.
   - Manual: real URL-only ingest (live Gusto posting) → title "Principal Product Manager, Cash Flow", company "Gusto, Inc.", score 80, 12.8k-char description; paste-only → score 85; `not-a-url` → 400; dead domain → 400 with clear message; empty body → 400.
4. **JS** — `node --check` PASS; every element id referenced exists in the module's own rendered HTML; shared helpers (`API`, `toast`, `escapeHtml`, `statusBadge`, `TabHooks`, `switchToTab`) all exist in `web/js/app.js`.
5. **Browser preview (Flask on port 5252 — NOT 5151/5050)** — verified live: card grid with score bands/Remote badge/source tags, summary line ("500 jobs · 500 new"), detail drawer (JD text with line breaks, matched-keyword chips, external link), Interested → action toast "Tailor now →", Interested chip filter, card "Tailor now →" → `switchToTab("review", {jobId})` confirmed (context `{jobId: 927}` delivered), search `q=lending` + min-score 70 → 12 jobs, manual-add form → job created (then test rows deleted from DB). Zero console errors.

## DB state left for the orchestrator

1074 real jobs seeded (1 marked `interested` from flow testing: Gusto "Principal Product Manager, Cash Flow"). Fabricated test jobs were deleted.

## Known gaps

- Lever returns 0 with the current config watchlist (stale slugs) — fetcher itself proven against live boards; config fix requested in `INTEGRATION_NOTES_A.md`.
- RemoteOK yields few PM jobs (6) — feed is dev-heavy; keyword filter is working as designed.
- Greenhouse API has no salary field → salary shown only for RemoteOK/Remotive jobs.
- `refresh` is synchronous (~30–60s over 10 boards); the UI shows a spinner and the per-request timeout is 15s, but a very slow board still delays the response.
- Manual URL ingest grabs visible page text; JS-rendered job pages (some LinkedIn views) may yield thin descriptions — pasting the JD is the designed fallback and the form says so.
- `.claude/launch.json` (JobPilot) added for preview tooling only — not app code.
