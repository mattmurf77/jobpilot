---
name: jobpilot
description: >
  Run the JobPilot job-hunt cycle from Claude Code: refresh all job sources
  (watchlist boards, keyword feeds, dream companies), triage what's new against
  the candidate's profile, and act on the user's picks (tailor resume, render
  1-page PDF, evaluate fit). Use when the user says /jobpilot, "check for new
  jobs", "any new jobs?", "refresh the job search", "run the job pipeline",
  "what's new on the dream companies", or wants a new-postings digest. Combine
  with /loop for recurring checks (e.g. "/loop 4h /jobpilot"). NOT for editing
  the JobPilot app's code; this skill OPERATES the app.
---

# JobPilot — fetch, triage, and act on new jobs

JobPilot is the local job-application app in this repository (Flask + SQLite;
docs: `README.md`, `docs/APP_PLAN.md`). This skill runs one hunt cycle. The
candidate is whoever `data/profile.json` describes; never assume anything about
them that is not in the profile or the materials under `materials/personal/`.

## Hard rules

- **The user picks; you never auto-advance.** Never set a job to `interested`,
  `ready`, or beyond without an explicit pick in this conversation. Never call
  any `/api/submit/*` endpoint; submission always happens in the app UI with
  the human confirm gate.
- Resume content comes only from the tailoring engine (no-fabrication
  guardrails live in the app); never hand-edit resume facts.
- Use the app's own venv: `.venv/bin/python` from the repo root. Do not
  `pip install` anything.

## Cycle

Run everything through the Flask test client (no server needed):

```python
# cwd must be the repo root
from backend.app import create_app
c = create_app().test_client()
```

### 1. Refresh

`r = c.post("/api/jobs/refresh")` (takes 40-90s; timeout >= 300s).
Capture `fetched / new / new_dream / per_source / errors`. A single generic
careers-page timeout is usually noise; any other error, surface it.

### 2. Triage digest

Read the last-run marker, then update it (settings table, via `backend.db`):
`get_setting("skill_jobpilot_last_run")`; after triage,
`set_setting("skill_jobpilot_last_run", db.utcnow())`.

Query new-since-last-run rows (fall back to "today" if no marker):
`status='new' AND created_at > <marker>`, plus ALWAYS include current
`dream=1 AND status='new'` jobs with score >= 60 even if older (dream jobs
deserve repeat visibility until picked or skipped).

Present ONE table sorted by score: `id · score · dream · company · title ·
location · posted`. Cap ~20 rows; say how many were held back. Below it, call
out (a) any 85+ scorer, (b) any dream-company role matching a target title, in
a sentence each. If nothing new: say so in one line; don't pad.

### 3. Act on picks

When the user names jobs (by id, company, or "the Acme one"):

1. `c.post(f"/api/jobs/{id}/status", json={"status": "interested"})`
2. `c.post(f"/api/tailor/{id}")`: report mode (`llm` vs `basic`; basic means
   no ANTHROPIC_API_KEY in `.env`; remind once per session, not per job)
3. `c.post(f"/api/tailor/{id}/render")`: must return `pages: 1`; report the
   ATS block (`ok` / missing keywords)
4. `c.post(f"/api/review/{id}/evaluate")`: report recommendation, weighted
   score, location gate, and the honest-gaps list verbatim
5. Point them at the app for final review/approval:
   `.venv/bin/python run.py` -> `http://127.0.0.1:5151`. Approval and
   submission stay in the UI.

Cover letters only on request: `c.post(f"/api/tailor/{id}/cover-letter")`.

**Voice enforcement (mandatory on every draft and revision):** tailor, save,
and cover-letter responses include a `voice` findings list from
`backend/voice_check.py` (rules: the voice guide at `config.json ->
materials.voice_guide`). Report any flags and fix them (or get the user's
explicit waiver) before the document is presented or approved. When writing
letter/resume prose in-session, follow the voice guide from the FIRST draft.
For an independent quality read, run the panel in
`materials/guides/grading_panel_process.md` with the rubric in
`materials/guides/resume_scorecard.md`.

### 4. Close the loop

End with a one-line pipeline pulse from `/api/review/insights` (or DB counts):
`X interested · Y tailored · Z ready · N submitted · interviews M`. If
anything sits in `ready` for >3 days, nudge: those are approved but unsubmitted.
**Any job in `submitting` is an ALERT, not a status**: an auto-fill was
prepared but the Confirm click never happened and the browser session has
likely expired (30-min TTL); the application was NOT sent. Surface it
immediately with the fix: POST /api/submit/<id>/cancel to reset to ready, then
redo auto-fill + Confirm in the UI.

## Notes

- New dream companies are added in the app's Settings tab (live "Test & add"
  validator), not by editing config.json here.
- If refresh reports every source failing, the network is down or the venv is
  broken; stop and report rather than retrying in a loop.
