# Feature extraction: ai-job-search → JobPilot

Source: `~/Downloads/ai-job-search-master.zip` (MadsLorentzen/ai-job-search — Claude Code
job-application workspace, Danish market). Reviewed 2026-06-11.

## Architecture contrast

| | ai-job-search (zip) | JobPilot |
|---|---|---|
| Shape | Claude Code workspace: slash commands + skill md files, human runs each step in chat | Local Flask app + SQLite + web UI, autonomous fetch/score/render |
| Discovery | Bun CLI scrapers for 6 Danish portals + LinkedIn URL builder | 6 ATS APIs + dream-company monitoring (Workday/TWO/etc.), auto-refresh, dedupe, scoring |
| Tailoring | LLM drafts LaTeX CV/cover from templates each time | Deterministic/LLM selection from vetted line menu, no-fabrication validation, provenance, 1-page enforced |
| Submission | None (user submits manually) | Playwright auto-fill + human confirm gate, assist mode |
| Tracking | CSV + per-application folder archive | SQLite statuses, events, documents |
| Post-application | **Strong**: /interview prep, /outcome capture, /upskill gap analysis | Thin: status changes only |

Verdict: keep JobPilot's engine; adopt the zip's *judgment layer* — evaluation, critique,
research, and everything after "submitted."

## P0 (implemented 2026-06-11, deterministic — no API key required)
1. Multi-dimensional fit evaluation (4 scored dimensions + PASS/FLAG/FAIL location,
   honest-gaps rule: verbatim unmet requirements) — `backend/evaluation.py`
2. Draft critique checklist (reviewer-agent stand-in: missed JD keywords, weak/repeated
   verbs, metric-free/overlong bullets, skills mirroring, cover-letter checks) —
   `backend/review_checks.py`
3. ATS parseability check on every rendered PDF (pypdf extraction; contact + JD-keyword
   survival) — `backend/docgen.py::ats_check`
4. Interview prep pack from submitted materials (STAR bank, metric drill list, staged
   question sets, no-invented-company-facts rule) — `backend/interview_prep.py`
5. Outcome insights funnel (score band / source / dream conversion) + posting snapshot
   at approve time — `backend/routes_review.py::insights`, kind `posting_txt`

## P1 backlog
6. Skill-gap heatmap + learning plan (`/upskill` pattern)
7. Company-research-enriched cover letters (verify-before-use rule)
8. Behavioral/voice profile doc in `config.materials`, consumed by cover letters + critique
9. Application-deadline extraction into Pipeline

## P2 backlog
10. Local salary-benchmark lookup (pluggable `salary_data.json`)
11. On-demand LLM shortlist re-rank

### Explicitly NOT porting
LaTeX/moderncv pipeline; Danish portal scrapers/Bun CLIs; CSV tracker; fork-and-fill /setup.

### LLM upgrade path (when ANTHROPIC_API_KEY lands)
Evaluation → LLM-graded dimensions incl. culture fit; critique → hiring-manager-proxy
reviewer agent with structured edit suggestions; interview prep → live company research +
interviewer angles + mock interview; cover letters → research-enriched. The deterministic
versions above remain the permanent fallback.
