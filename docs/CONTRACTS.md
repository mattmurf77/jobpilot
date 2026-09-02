# JobPilot — Shared Contracts for Feature Agents

Read this fully before writing code. Read `APP_PLAN.md` for product intent.

## Environment

- Project root: the repository root (paths below are relative to it).
- Python: `.venv/bin/python` (3.11+). Installed per `requirements.txt`: flask, requests, python-dotenv, anthropic, playwright (+ chromium), pypdf, python-docx.
- Server: `run.py` → Flask on **http://127.0.0.1:5151**, serves `web/` statically and `/api/*` blueprints.
- Do NOT `pip install` anything new without adding it to `requirements.txt`. Do NOT start a server on 5151 while another instance is running. For functional tests use `flask.testing` test client (`create_app().test_client()`) or call functions directly.

## File ownership — HARD RULE

You may create/overwrite ONLY the files assigned to you in your prompt. Shared files (`backend/app.py`, `backend/db.py`, `backend/profile_store.py`, `web/index.html`, `web/js/app.js`, `web/css/style.css`, `config.example.json`, `data/profile.example.json`, `run.py`) are READ-ONLY. If you need a change in a shared file, write the request into `INTEGRATION_NOTES_<your-letter>.md` at the project root; the orchestrator applies it.

## Backend conventions

- Each routes file exposes `bp = Blueprint(...)`. Prefixes are set in `app.py`: jobs → `/api/jobs`, tailor → `/api/tailor`, submit/settings → `/api`.
- Use `backend.db` helpers (read `backend/db.py`): `upsert_job, list_jobs, get_job, update_job, add_document, list_documents, latest_document, log_event, list_events, get_setting, set_setting`. Job statuses and document kinds are defined there — use them exactly.
- Config: `from backend.app import load_config, save_config`. Profile: `from backend.profile_store import load_profile, save_profile`.
- Errors: return `jsonify({"error": "human-readable message"}), 4xx/5xx`. Never let exceptions leak HTML 500s — wrap risky externals (network, subprocess, playwright) in try/except.
- Log every meaningful lifecycle action with `db.log_event(job_id, type, detail)` (e.g. `fetched`, `status_change`, `tailored`, `pdf_rendered`, `cover_letter`, `submit_prepared`, `submitted`).
- Generated files go under `data/documents/job_<id>/` (create dirs as needed); register each via `db.add_document`.

## Frontend conventions

- Vanilla JS, no frameworks, no build step. Your module owns exactly one tab panel: render into `document.getElementById("tab-<name>")`.
- Use helpers from `web/js/app.js` (read it): `API.get/post`, `toast(msg, kind)`, `escapeHtml(s)`, `statusBadge(status)`, `STATUS_META`, `TabHooks`, `switchToTab(name, ctx)` / `consumeTabContext()`.
- Register `TabHooks["<name>"] = yourRefreshFn;` and also render once at script load.
- ALWAYS pipe user/job/JD strings through `escapeHtml` before innerHTML.
- Scope styles: inject a `<style>` element from your own JS file (id `style-<name>`); do not edit `style.css`. Reuse existing classes (`card`, `btn`, `btn-primary`, `badge`, `empty-state`, `field`, `spinner`) before inventing new ones.
- Look: clean, light, Linear-ish; the base CSS sets variables — use `var(--accent)` etc.

## Cross-feature API surface (who serves whom)

Agent A serves: `GET /api/jobs/` (`?status=a,b&min_score=&q=`), `GET /api/jobs/<id>`, `POST /api/jobs/refresh`, `POST /api/jobs/<id>/status` `{status, notes?}`, `POST /api/jobs/manual` `{url?, title?, company?, description?}`.

Agent B serves: `POST /api/tailor/<job_id>` (run tailoring → resume_html doc), `POST /api/tailor/<job_id>/render` (→ resume_pdf, returns `{doc_id, pages}`), `POST /api/tailor/<job_id>/cover-letter`, `POST /api/tailor/<job_id>/cover-letter/render`, `POST /api/tailor/<job_id>/save` `{kind, content}` (user edits), `GET /api/tailor/<job_id>/materials` (latest docs incl. content + doc ids), `POST /api/tailor/<job_id>/approve` (→ status `ready`).

Agent C serves: `GET /api/settings`, `POST /api/settings/config`, `POST /api/settings/profile`, `POST /api/settings/apikey`, `POST /api/submit/<job_id>/prepare`, `POST /api/submit/<job_id>/confirm`, `POST /api/submit/<job_id>/cancel`, `POST /api/submit/<job_id>/manual-confirm`, `GET /api/submit/<job_id>/assist`.

Existing (orchestrator-owned): `GET /api/health` → `{ok, anthropic_key, playwright}` (also on `window.HEALTH`), `GET /api/events`, `GET /api/documents/file/<doc_id>` (serves a stored document inline — usable as iframe src / download href).

If you call a sibling agent's endpoint from your UI, code against the contract above even though the implementation may not exist yet in your checkout.

## Non-negotiable product guardrails

- Resume/cover content must trace to source materials (paths in `config.json → materials`, relative to the repo root). Never fabricate employers, titles, dates, metrics, or skills. LLM outputs are validated before use; numbers not present in source lines are rejected.
- No CAPTCHA bypass, no credentialed scraping, no LinkedIn/Indeed automation. Final submit requires explicit user confirmation.
- `ANTHROPIC_API_KEY` may be absent: every LLM feature needs a working deterministic fallback and the UI labels which mode ran.

## Verification before you finish

1. `.venv/bin/python -m py_compile <each backend file you wrote>`
2. `.venv/bin/python -c "from backend.app import create_app; app=create_app(); print([str(r) for r in app.url_map.iter_rules()])"` — your routes appear, app constructs.
3. Exercise your endpoints with the Flask test client (happy path + one error path). Network-dependent code: hit the real public APIs once (they're free/no-auth) — if offline, mock and say so.
4. `node --check` is NOT needed for JS; instead re-read your JS for syntax and verify every element id you reference exists in your own rendered HTML.
5. Write `MANIFEST_<letter>.md` at project root: files written, endpoints implemented, what you tested and the results, known gaps.
