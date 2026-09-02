# JobPilot — Plan Doc

**App name:** JobPilot (working title)
**Tagline:** Find jobs, tailor the resume truthfully, apply with one approval click.

## Vision & Premise

A local, single-user web app (Flask + SQLite, runs on your machine, opens in the browser) that runs your job-application pipeline end to end:

1. **Find** — pulls fresh job postings from free job APIs + a configurable company watchlist, scores each against your profile, and presents them as cards.
2. **Pick** — the user marks jobs Interested / Skipped. Nothing happens without a pick.
3. **Tailor** — for each interested job, the app analyzes the job description and produces a tailored one-page resume by **selecting and reordering real bullets from the existing Resume Line Menu** — never inventing experience — plus a cover letter when wanted. Rendered to PDF with Playwright's Chromium (or an optional external html-to-pdf script), matching the resume's visual template.
4. **Review & Submit** — side-by-side review of JD vs. tailored materials with inline editing. On approval, the app assists submission: full form-fill automation for Greenhouse/Lever boards (Playwright, with a final human "Submit" gate), and an assisted mode (open page + materials ready to paste/attach) for everything else.

**Hard guardrail:** the tailoring engine may rephrase, reorder, emphasize, and translate jargon (per the generalization guide) but must never fabricate employers, titles, dates, metrics, or skills. Every bullet must trace to a line in the source materials.

## Source materials (ground truth)

All under `materials/` (see `materials/README.md`). Personal files live in `materials/personal/` (gitignored) and are drafted from your resume by `scripts/onboard.py`:

| File | Role in JobPilot |
|---|---|
| `materials/personal/resume_template.html` | Visual template + baseline resume content |
| `materials/personal/resume_line_menu.md` | The bullet inventory the tailor selects from (with §0.5 audience translation) |
| `materials/personal/cover_letter_reference.md` | Optional: a letter you wrote, used as a voice/structure exemplar |
| `materials/guides/resume_generalization_guide.md` | Jargon-translation rules applied to every external application |
| `materials/guides/resume_best_practices.md`, `cover_letter_best_practices.md`, `writing_voice_guide.md` | Style constraints for tailoring, cover letters, and the voice linter |

Candidate profile lives in `data/profile.json` (gitignored): contact, current role, target titles/domains, keywords, cover-letter facts, screener answers.

## Core features

### F1 — Job discovery & scoring
- Sources (all free, no auth): **Greenhouse boards API** (`boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true`) and **Lever postings API** (`api.lever.co/v0/postings/{slug}?mode=json`) over a configurable company watchlist; **RemoteOK** (`remoteok.com/api`) and **Remotive** (`remotive.com/api/remote-jobs?search=`) keyword feeds; **manual ingest** (paste a URL or raw JD text — covers LinkedIn/Indeed where scraping is off-limits).
- **Dream companies (added 2026-06-10):** `config.json → dream_companies` lists `{name, url}` career sites the user cares most about. ATS auto-detected from the URL (Greenhouse / Lever / Ashby / Workable / SmartRecruiters / **Workday** public APIs; anything else falls back to page-snapshot diffing of the careers page). Fetched on every refresh regardless of keyword filters (light title filter only: search keywords, "product", or "hiring" on generic pages), stored with `dream=1`, score boosted by `search.dream_score_boost` (15), surfaced via a 💜 Dream filter chip + badge in Find, managed in Settings with a live "Test & add" validator. The shipped list is empty; add your own in Settings.
- **Ashby watchlist (integration fix):** Ramp and Plaid moved off Greenhouse to Ashby; `watchlist.ashby` + `backend/sources/ashby.py` cover them in the broad feed (215 postings on first fetch).
- Each job is deduped (source + external id), stored in SQLite, and scored 0–100 by keyword overlap between the JD and profile keywords (title match weighted, seniority match, domain terms: lending/fintech/payments/SMB/PM).
- UI: "Find" tab — refresh button, filter by score/source/keyword, job cards (title, company, location, salary if present, score badge, posted date) with **Interested** / **Skip** actions and a detail drawer showing the full JD.

### F2 — Resume tailoring + cover letters
- Pipeline per interested job: extract JD requirements → select best-matching bullets per role from the line menu → apply audience translation → reorder skills line to mirror JD phrases → adjust subtitle/summary variant → render into the HTML template → PDF (1-page enforced, auto-retry trimming a bullet if it overflows).
- **LLM mode** (when `ANTHROPIC_API_KEY` is in `.env`): Claude (claude-sonnet-4-6) does selection/translation/summary, constrained by a strict system prompt: *output must quote source lines verbatim or lightly rephrase; any metric/employer/date/skill not present in sources is forbidden*. Response is structured JSON (selected bullet IDs + rephrasings + skills order + summary), validated against the source inventory before rendering — rephrasings with numbers not present in the source line are rejected.
- **Deterministic fallback** (no key): keyword-overlap bullet selection from the line menu, stock summary variant, skills reordered by JD term frequency. Clearly labeled "basic tailoring" in the UI.
- Cover letter: generated on demand (LLM mode) following `cover_letter_best_practices.md`; editable in UI; rendered to PDF in a matching template. Fallback: structured template with profile facts + JD company/role slotted in, flagged for manual editing.
- UI: "Review" tab — JD on the left; tailored resume (rendered HTML) on the right; per-bullet provenance ("from line menu §4.2"); editable; **Approve materials** button gates submission.
- **Optional Projects section:** line menu §17 holds side-project bullets. When a JD contains a configured trigger term (`config.json → tailoring.projects.triggers`), or with no triggers when the bullets overlap the JD's vocabulary, the engine renders a Projects role-block between Experience and Skills (2-3 bullets). The 1-page trim loop is length-aware and has staged fallbacks: projects scope line → earlier-impact block → education course-detail truncation.

### F3 — Submission assist + pipeline tracking
- **Auto mode (Greenhouse & Lever hosted application forms):** Playwright (headed Chromium so the user can watch) navigates to the apply URL, fills name/email/phone/location/LinkedIn from profile, uploads resume PDF + cover letter, fills free-text "why us" from the cover letter when present, screenshots the completed form — then **stops**. The final Submit click happens only after the user clicks "Confirm submit" in JobPilot (or clicks it themselves in the browser window). No CAPTCHA bypass ever; if a CAPTCHA or login wall appears, drop to assist mode.
- **Assist mode (everything else):** opens the apply URL, shows a copy-paste panel (each profile field + materials with copy buttons), marks the application "submitted (manual)" when the user confirms.
- Pipeline tab: kanban-ish list — New → Interested → Tailored → Ready → Submitted → (Heard back / Rejected / Interview) with timestamps and notes.

### F4 — Settings & profile
- Search config: keywords, locations, remote-only toggle, company watchlist (Greenhouse/Lever slugs), min score.
- Profile editor: contact fields, links, work-auth answers (e.g., "authorized to work in US", "require sponsorship: no"), default answers for common screener questions.
- API key entry (stored in `.env`, never committed), source-materials paths.

## Data flow (the loop that matters)

Fetch → score → user picks → tailor → user approves → submit → track outcome. Outcomes feed back: submitted/interview/rejected per source + score band are shown on the Find tab so search config can be tuned. (Personal tool — no viral/monetization loops by design.)

## Technology

| Piece | Choice | Why |
|---|---|---|
| Backend | Python 3 / Flask, SQLite (`data/jobpilot.db`) | Matches the user's existing stack (Fantasy Trade Finder); zero-ops local |
| Frontend | Vanilla HTML/CSS/JS single page, 4 tabs | Same as user's other projects; no build step |
| LLM | Anthropic API, `claude-sonnet-4-6`, optional | Tailoring quality; deterministic fallback keeps app useful without it |
| PDF | Existing `html-to-pdf` Node skill | Already proven to produce the exact 1-page resume |
| Browser automation | Playwright (Python, Chromium, headed) | Greenhouse/Lever form fill; graceful degrade to assist mode if not installed |

## Architecture / file ownership

```
JobPilot/
├── run.py                 # Flask dev server, port 5151
├── backend/
│   ├── app.py             # app factory, registers blueprints, serves web/
│   ├── db.py              # schema + helpers (jobs, documents, events, settings)
│   ├── profile_store.py   # profile.json load/save
│   ├── routes_jobs.py     # Blueprint: /api/jobs/* (sources, scoring, status)   [Agent A]
│   ├── sources/*.py       # greenhouse, lever, remoteok, remotive, manual      [Agent A]
│   ├── matching.py        # JD keyword scoring                                  [Agent A]
│   ├── routes_tailor.py   # Blueprint: /api/tailor/*                            [Agent B]
│   ├── tailoring.py       # LLM + fallback selection engine                     [Agent B]
│   ├── docgen.py          # HTML render + PDF via node skill                    [Agent B]
│   ├── cover_letter.py    #                                                     [Agent B]
│   ├── routes_submit.py   # Blueprint: /api/submit/* + /api/settings/*          [Agent C]
│   └── submit/*.py        # playwright_filler, assist                           [Agent C]
├── web/
│   ├── index.html         # tab skeleton + shared chrome (owned by orchestrator)
│   ├── css/style.css
│   └── js/app.js (shared) + find.js [A] + review.js [B] + pipeline.js + settings.js [C]
├── data/                  # db, profile.json, generated documents (gitignored)
├── config.json            # search config, paths, feature flags
└── .env                   # ANTHROPIC_API_KEY (gitignored)
```

DB schema (db.py): `jobs(id, source, external_id, url, title, company, location, remote, salary, description, posted_at, score, status, notes, created_at, updated_at)` with UNIQUE(source, external_id); `documents(id, job_id, kind, path, meta, created_at)` kind ∈ resume_html|resume_pdf|cover_letter_md|cover_letter_pdf|form_screenshot; `events(id, job_id, type, detail, created_at)`; `settings(key, value)`.

Job status enum (single source of truth, db.py): `new, interested, skipped, tailoring, tailored, ready, submitting, submitted, interview, rejected, archived`.

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| Resume fabrication by LLM | Structured-output validation against source inventory; numbers not in source ⇒ rejected; provenance shown per bullet; user approval gate |
| ATS ToS / bot detection | Only public no-auth APIs for discovery; form-fill runs in a visible browser at human pace, user triggers final submit; manual assist for LinkedIn/Indeed |
| Python 3.14 wheel gaps (playwright) | Playwright optional import; app fully functional in assist mode without it |
| 1-page overflow on tailored PDF | Render-and-check loop (mdls page count), trim lowest-priority bullet and re-render |
| No API key present | Deterministic fallback tailoring, UI labels it and recommends adding the key |

## Success metrics (personal-tool scale)

North star: **applications submitted per week with <10 min of user time each**. Supporting: jobs surfaced/week, interested-rate, tailor-approval-without-edits rate, interview rate per source.

## Build phases

1. Foundation: scaffold, venv, db, app factory, stub blueprints, web skeleton — server runs, tabs render. *(orchestrator)*
2. Core features: Agents A/B/C in parallel per file-ownership map above.
3. Merge + integration pass, real-data smoke test (fetch real postings, tailor one, render PDF).
4. Infrastructure-lite: event log, error surfacing in UI, `run.sh`, README.
