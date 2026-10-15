# Migrating from the original app snapshot

Edition 2 adds the Codex workflow and private three-table model. Existing Flask,
SQLite, rendering and source-adapter code remain for compatibility. Installing
the Codex workflow does not start the app or connect any account. Do not run
the old setup/onboard scripts to start the new path; use `$jobpilot-start`.

## Separate systems, explicit migration

The optional app uses `data/profile.json`, `config.json`, `materials/personal/`
and `data/jobpilot.db`; Codex uses `.jobpilot/`. There is **no automatic sync**.
Choose one canonical writer. Do not let legacy status changes overwrite
reviewed application outcomes or dedupe evidence. Back up originals privately.

For a requested import:

1. Read the old profile/materials and ask which résumé is currently approved.
   Old `screener_answers`, including work eligibility and demographics, are
   unverified until the new user actually confirms them. Samples are not facts.
2. Import source rows to leads, keeping full native IDs, original sources and
   unknown historical dates. A score does not establish current fit or openness.
3. Inspect submitted/interview/rejected rows and original receipts. Preserve
   true legacy provenance; do not invent a receipt, submission actor or date.
   An ambiguous employer confirmation belongs in unresolved evidence.
4. Import actual interview appointments/rounds with known details and evidence.
   Do not infer completed attendance from old status flags.
5. Validate new tables and compare counts by distinct role and source row.
   Retain originals; no destructive backfill or implicit deletion is needed.

## Legacy limitations

- App setup installs dependencies/browser and may use a separately configured
  Anthropic API key. The Codex workflow requires neither. No model availability
  is promised by the old example model name; configure a supported model if
  choosing the optional app.
- The original keyword scores, title ladder, dream-company boosts and one-page
  output are heuristics, not qualification proof or a universal résumé rule.
  Codex asks the user for targets and document length instead of inheriting them.
- The older SQLite lifecycle is not the three-table schema. It does not by
  itself implement exact unresolved receipt reconciliation, separate multiple
  interview stages, scoped permission provenance or current official fit gates.
- Legacy automated browser submission is disabled in this edition pending an
  independently verified receipt-aware implementation. Use supported Codex
  browser tools within permission, or the employer site manually. Do not call
  hidden application endpoints to restore it. The copy/paste assist view is
  preparation, not proof of submission.
- No email/calendar integration or scheduled polling is included by default.
  Codex may use connected tools only when available and authorized; manual
  supplied confirmations are a valid fallback.
- The older Claude skill is a legacy entrypoint, not a second source of current
  policy. It points to the portable workflow and does not trigger `/loop` or
  treat an interrupted click as failed acceptance.

## Sharing an updated fork

Only generic skills, docs, scripts, tests and empty example files belong in Git.
Review tracked content **and history**; ignore rules do not untrack past files.
Do not publish another user's résumé, claims, authorization evidence, receipts,
audio, account state or screenshots. This edition does not rewrite old Git
history. Existing copyright attribution is retained under the MIT license.

## Change record

- **Edition 1:** local Flask/SQLite app, source adapters, résumé/cover tools and
  Claude operating skill.
- **Edition 2, 2026-10-14:** Codex-first start/experience interview, scoped
  permissions, five repo-local skills, private records and three tables,
  evidence-based outcomes, safer duplicate/retry rules, interview prep and
  optional connector workflows. No inherited candidate state or publication
  action is part of onboarding.
