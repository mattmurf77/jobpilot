# Integration notes — Agent A

One shared-file change requested. Everything else integrated cleanly.

## 1. `config.json` — Lever watchlist slugs are stale (orchestrator-owned file)

Both configured Lever slugs 404 against the live API (verified 2026-06-10):

- `https://api.lever.co/v0/postings/highnote?mode=json` → 404
- `https://api.lever.co/v0/postings/found?mode=json` → 404

These companies appear to have moved off Lever (or renamed their boards). The fetcher
itself works — verified against live boards: `palantir` → 222 jobs, `octoenergy` → 164 jobs.

**Request:** replace `watchlist.lever` in `config.json` with currently-live Lever slugs
relevant to Matt's fintech/PM search. Suggested check before committing (each should
return JSON, not 404):

```
curl -s "https://api.lever.co/v0/postings/<slug>?mode=json" | head -c 200
```

No code change needed on my side — `refresh` already reports the failure in its
`errors` array and the other sources are unaffected.

## FYI (no action needed)

- `POST /api/jobs/refresh` left the DB seeded with 1074 real jobs; one (Gusto
  "Principal Product Manager, Cash Flow", id 927) is `interested` from flow testing —
  a ready-made input for Agent B's tailor pipeline.
- `GET /api/jobs/<id>` returns `score_reasons` (matched profile terms) — Agent B's
  Review tab is welcome to reuse it.
- Added `.claude/launch.json` (JobPilot root) with a preview config that runs the app
  on port 5252 to respect the "no 5151/5050" rule. Harmless to keep or delete.
