# MANIFEST_C — Submission assist + pipeline tracking + settings (Agent C)

## Files written (all within assigned ownership)

| File | Purpose |
|---|---|
| `backend/submit/detector.py` | `detect_ats(url)` → greenhouse (`boards.greenhouse.io` / `job-boards.greenhouse.io`, apply on same page, `#app` anchor appended when no anchor) / lever (`jobs.lever.co`, apply at `<posting>/apply`) / other |
| `backend/submit/playwright_filler.py` | Playwright sync API in a dedicated thread per session (`_Session(threading.Thread)` + command/result queues; module-level `_sessions` registry). `prepare()` launches **headed** chromium, best-effort fills (per-step try/except, `filled`/`skipped`/`notes` report), uploads resume PDF (+ cover letter file or textarea text), detects CAPTCHA iframes (reported, never solved), screenshots to `data/documents/job_<id>/form_filled.png`, then **stops and waits**. `confirm()` clicks submit (GH `#submit_app`/`input[type=submit]`, Lever `button[type=submit]`), screenshots result, closes. `cancel()` closes without submitting. Sessions auto-expire after 30 min. Raises `PlaywrightUnavailable` cleanly when import fails. `headless=` kwarg is a test-only override. |
| `backend/submit/assist.py` | `assist_packet(job, profile, materials)` — ordered copy-paste fields (contact + LinkedIn + screener answers with human labels), latest document per kind with doc ids, apply URL |
| `backend/routes_submit.py` | Replaced stub with all settings + submit endpoints (below) |
| `web/js/pipeline.js` | Replaced stub — grouped pipeline board for `#tab-pipeline` |
| `web/js/settings.js` | Replaced stub — settings cards for `#tab-settings` |

No shared files touched → no `INTEGRATION_NOTES_C.md` needed.

## Endpoints implemented (blueprint mounted at `/api`)

- `GET /api/settings` → `{config, profile, anthropic_key_set, playwright, materials_status}` (key **value** never returned; `materials_status` adds per-path exists check for the Settings Materials card)
- `POST /api/settings/config` — full config object; rejects non-dict, missing, or unknown top-level keys (expected: search, watchlist, materials, tailoring, features)
- `POST /api/settings/profile` — full profile object (non-empty dict)
- `POST /api/settings/apikey` `{key}` — rewrites the `ANTHROPIC_API_KEY=` line in `.env` + sets `os.environ`; key never logged/echoed
- `POST /api/submit/<id>/prepare` — 409 unless status `ready`. Auto path (GH/Lever + playwright + resume_pdf doc exists): runs filler.prepare, status → `submitting`, registers `form_screenshot` doc, returns `{mode:"auto", report, screenshot_doc_id}`. Otherwise (or on any playwright failure) returns `{mode:"assist", packet, note?}` and leaves status `ready`. Accepts optional `{headless: true}` body (test override).
- `POST /api/submit/<id>/confirm` — 409 unless `submitting` + live session; clicks submit, status → `submitted`, registers result screenshot, `log_event("submitted", "auto…")`
- `POST /api/submit/<id>/cancel` — closes session, status `submitting` → `ready`
- `POST /api/submit/<id>/manual-confirm` — status → `submitted`, `log_event("submitted", "manual")`
- `GET /api/submit/<id>/assist` — assist packet
- **Extra (own blueprint, not in cross-agent contract):** `GET /api/submit/documents` → all documents grouped by job id, so the Pipeline board renders doc chips in one call instead of N.

## Frontend

- **pipeline.js**: sections in lifecycle order (Interested / Tailored(+tailoring) / Ready / Submitting / Submitted / Interview / Rejected / Skipped-Archived collapsed) with counts; rows show company — title, status badge, updated date, doc chips opening `/api/documents/file/<id>`; Ready → "🚀 Auto-fill application"; auto mode shows confirm panel (screenshot img, filled/skipped report, CAPTCHA notes, **Confirm submit** with `window.confirm()` double-check, Cancel); assist mode shows copy-per-field panel (navigator.clipboard), open-apply-page link, "I submitted it" → manual-confirm; Submitting rows keep Confirm/Cancel; status dropdown (STATUS_META) on every row; expandable detail with notes textarea (saved via `POST /api/jobs/<id>/status {status: same, notes}`) and event timeline from `/api/events` filtered client-side. Styles injected as `#style-pipeline`; `TabHooks["pipeline"]` registered.
- **settings.js**: cards — Search (keywords/domain terms/locations CSV, remote-only, min score), Company watchlist (GH/Lever slugs + slug-URL hint), Profile (contact/linkedin/title fields), Screener answers (editable rows + add/remove), AI (tailoring + playwright status lines, password key input → POST apikey → toast + `refreshHealth()`), Materials (read-only paths with ✓/✗ exists). Per-section save buttons POST the full config/profile. Styles `#style-settings`; `TabHooks["settings"]` registered.

## Verification performed (all green: 56/56 checks)

1. `py_compile` on all four backend files; `create_app()` constructs and all routes appear in url_map.
2. Flask test client: settings GET shape; config round trip (modify → visible → restored) + 400s for non-dict/missing/unknown keys; profile round trip + 400; apikey with dummy key (line written to `.env`, `os.environ` set, `anthropic_key_set` flips) then `.env` removed (it did not exist before) and env var unset.
3. Detector unit checks (both GH hosts, anchor preservation, lever `/apply` idempotence, other, empty).
4. End-to-end submit flow against a local fixture form (`data/tmp_test_form.html`, greenhouse-style ids, served via `file://`, **headless** test override, detector monkeypatched to "greenhouse"): prepare filled first/last/email/phone/location/LinkedIn, uploaded dummy resume PDF, pasted cover-letter text into the textarea, screenshot saved + registered, status → submitting; double-prepare 409; cancel → ready + browser closed; confirm-without-session 409; full prepare → confirm clicked `#submit_app`, fixture showed "Application received", result screenshot saved, status → submitted, events logged; manual-confirm path; 404s. Fixture, dummy PDFs, test jobs/docs, and `job_<id>` dirs all cleaned up afterwards.
5. `node --check` passed on both JS files; element ids referenced are all rendered by the same module.

## Known gaps / notes

- Auto-fill is exercised against the local fixture, not a live Greenhouse/Lever board (per instructions). Real boards may have extra required questions — those land in the `skipped` report and the headed browser stays open so the user can finish them before confirming. Any prepare-time playwright failure degrades gracefully to assist mode with a `note`.
- Full-page screenshots occasionally flake in chromium ("Unable to capture screenshot"); filler retries and falls back to viewport capture, and a missing screenshot is non-fatal (noted in report).
- One playwright session per job at a time; sessions expire after 30 min (browser closed, nothing submitted).
- Pipeline board reads jobs via Agent A's `GET /api/jobs/?status=…` and saves notes via `POST /api/jobs/<id>/status` — coded to contract (stub returns `[]` in this checkout, board renders empty sections).
