# JobPilot

A local, single-user job-application copilot. It pulls fresh postings from the companies you care about, scores them against your profile, tailors your resume to each job description **truthfully** (selecting and reordering real lines from your own inventory, never inventing), drafts cover letters in your voice, lints everything for AI tells, and assists submission with a human "Confirm submit" gate.

Everything runs on your machine: Flask + SQLite + a vanilla-JS UI. Your resume, letters, and profile never leave the repo folder and are gitignored.

Built for product-management job hunts (the bundled best-practice guides and default scoring signals are PM-flavored), but every domain-specific piece is configuration.

## Quick start

```bash
git clone https://github.com/mattmurf77/jobpilot.git && cd jobpilot
./scripts/setup.sh                     # venv, deps, Chromium, local config files
# put your Anthropic API key in .env (optional; see "Modes" below)
.venv/bin/python scripts/onboard.py --resume ~/Documents/my_resume.pdf --cover-letter ~/Documents/my_letter.docx
.venv/bin/python run.py                # http://127.0.0.1:5151
```

Then, in **Settings**: search keywords and locations, the company watchlist (Greenhouse/Lever/Ashby board slugs), and your dream companies (paste any careers URL; the ATS is auto-detected and the board is fetched on every refresh).

Requirements: Python 3.11+, macOS or Linux. Node is not required.

## What `onboard.py` does

Your resume becomes three files under `materials/personal/` (gitignored) plus `data/profile.json`:

| File | What it is | Who uses it |
|---|---|---|
| `resume_line_menu.md` | Every bullet, summary variant, subtitle variant, skill, and a translation table for company-internal jargon, in a numbered format the engine parses | Tailoring engine (selects from it), evaluation (skills coverage), interview prep |
| `resume_template.html` | Your baseline resume in the visual template. The engine keeps this skeleton fixed (employers, titles, dates, education) and rebuilds only bullets, summary, subtitle, and skills per job | Tailoring, PDF/DOCX rendering |
| `cover_letter_reference.md` | Optional. A letter you wrote. The generator matches its structure, length, and voice, and never copies its facts | Cover letters |
| `data/profile.json` | Contact, current role, target titles/domains, keywords, flagship facts, screener answers | Scoring, evaluation, cover letters, auto-fill |

With an API key, Claude drafts these from your resume under a no-invention rule, and the script verifies every number in the drafts appears in your resume text. Without a key it copies annotated templates for you to fill in. **Review the line menu either way**: the engine trusts it completely, so its quality is the ceiling on every tailored resume.

## Workflow

1. **Find Jobs**: Refresh pulls from the Greenhouse/Lever/Ashby watchlist plus RemoteOK and Remotive keyword feeds (all free public APIs), plus your dream companies (Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Workday, Pinpoint, and TeamWork Online boards auto-detected; other careers pages are monitored by page-change detection). Each posting is deduped and scored 0-100. Dream jobs bypass keyword filters and get a score boost. Mark Interested or Skip. LinkedIn/Indeed jobs: "Add job manually" (paste URL or JD text).
2. **Tailor & Review**: per interested job: Tailor resume, Render PDF (1-page enforced, with a length-aware trim loop and an ATS text-layer check), optional cover letter, edit anything, then Approve. Every draft returns voice-lint findings.
3. **Pipeline**: for approved jobs: Auto-fill (Greenhouse/Lever: a visible Chromium fills the form and stops; you click Confirm submit) or assist mode (copy-paste panel) for other sites. Track Submitted, Interview, Rejected. Interview prep and fit evaluation live here too.
4. **Settings**: search config, watchlist, dream companies, profile and screener answers, API key, materials status.

A Claude Code skill ships in `.claude/skills/jobpilot/`: open the repo in Claude Code and say `/jobpilot` to refresh, triage new postings in chat, and act on your picks (`/loop 4h /jobpilot` for a recurring digest).

## Modes

- **LLM mode** (`ANTHROPIC_API_KEY` set): Claude selects and lightly rephrases lines, writes the summary, orders skills, and drafts cover letters. Output is validated before use: every bullet id must exist in the inventory, any number not present in the source line rejects the rephrasing, skills must come from the library. Model is `config.json → tailoring.model` (default `claude-opus-5`).
- **Basic mode** (no key): deterministic keyword-overlap selection, baseline summary, template cover letter flagged for editing. Clearly labeled in the UI. Everything else (discovery, scoring, evaluation, rendering, submission) is identical.

## Guardrails

- Resume and cover-letter content must trace to `materials/personal/`. No fabricated employers, titles, dates, metrics, or skills.
- The voice linter (`backend/voice_check.py`, rules in `materials/guides/writing_voice_guide.md`) flags em-dashes, AI-tell vocabulary, throat-clearing, false-contrast shapes, and zero-contraction letters on every pass.
- The final submit click is always yours. No CAPTCHA bypass, no credentialed scraping, no LinkedIn/Indeed automation.

## Configuration

`config.json` (created from `config.example.json`, gitignored) holds:

- `search`: keywords, domain terms, locations, remote-only, career bias with a `title_ladder` and your `current_level` (derived from your profile's current title if blank), `bonus_signals` (JD terms that earn career-fit credit), dream-company score boost.
- `watchlist`: Greenhouse / Lever / Ashby board slugs. `dream_companies`: managed in Settings.
- `materials`: paths to the files above (relative to the repo, or absolute if you keep them elsewhere). `html_to_pdf_script` is optional; leave blank to render with Playwright's Chromium.
- `tailoring`: model, max bullets per role, one-page enforcement, `menu_slots` (which line-menu sections feed which resume slot), and the optional `projects` section (heading, dates, scope line, trigger terms).

## What stays private

`.gitignore` excludes `.env`, `config.json`, `data/profile.json`, the SQLite DB, generated documents, and `materials/personal/`. If you fork this and push, those never leave your machine. Check `git status` before your first push anyway.

## Layout

- `backend/`: Flask blueprints (`routes_jobs` discovery/scoring, `routes_tailor` tailoring/PDF/cover letters, `routes_review` evaluation/critique/interview prep, `routes_submit` submission/settings); `sources/` one fetcher per job board; `submit/` Playwright filler and assist mode; `line_menu.py` parser, `tailoring.py` engine, `docgen.py` rendering, `voice_check.py` linter, `matching.py` + `evaluation.py` scoring; `db.py` schema.
- `web/`: vanilla JS single page, one module per tab.
- `materials/`: guides (tracked), templates (tracked), personal (gitignored). See `materials/README.md`.
- `scripts/`: `setup.sh`, `onboard.py`.
- `research/`: the research notes behind the guides and the voice rules.
- `docs/`: product spec (`APP_PLAN.md`), internal API contracts (`CONTRACTS.md`), build history.

## License

MIT. See `LICENSE`.
