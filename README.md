# JobPilot: a portable job-search workflow for Codex

Find suitable jobs, draft truthful materials, submit within your permissions,
prepare for interviews and track outcomes. This edition works inside Codex;
the older Flask app is optional. No separate model API key, web server, or
browser automation package is needed for the Codex workflow.

## Start in Codex

1. Clone this repository and open that folder in your own Codex instance:

   ```sh
   git clone https://github.com/mattmurf77/jobpilot.git
   cd jobpilot
   ```

2. Start a new chat in the repository and send:

   > Use $jobpilot-start to onboard me. Ask for my résumé and an optional sample
   > cover letter, interview me about my search and experience, check available
   > tools, and agree permissions before any external actions.

3. Codex creates a local, gitignored `.jobpilot/` workspace and guides you
   through documents, targeting, experience and permissions. You can pause and
   resume; answers already recorded should not be asked again.

Cloning does **not** execute onboarding or grant account access. Codex discovers
repo-local skills in `.agents/skills`; if they do not appear, restart Codex in
this folder, or ask it to read `.agents/skills/jobpilot-start/SKILL.md` explicitly.
See the [official Codex skill guide](https://learn.chatgpt.com/docs/build-skills).
Use a supported current Codex installation and its normal tool approvals.

## What onboarding covers

- Your current résumé, approved contact details and links; an optional letter
  or writing sample to establish your voice.
- Desired duties and title family, seniority, domains, exclusions, work type,
  location priorities, commute/travel/relocation, and salary currency/base floor.
- An experience interview: actual ownership, decisions, results, dates,
  leadership scope, technical depth and where the evidence is still missing.
- Optional prior applications/receipts, so old submissions are protected.
- Separate permissions for research/local drafting, browser data entry/uploads,
  final submission, and optional Gmail or Calendar access. No inherited consent.

You may authorize a bounded set of submissions without approving every routine
step again. Unknown facts, signatures, materially new agreements and sign-ins
still need their own resolution. Passwords and verification codes stay with you
on the service. Schedules and outbound messages are opt-in, not defaults.

## Daily work

| Ask Codex | Skill | Result |
|---|---|---|
| “Find roles that match my profile” | `$jobpilot-source` | Saved leads with current official evidence and ranked fit |
| “Apply to the strongest ready roles in this list” | `$jobpilot-apply` | Verified drafts and authorized submissions, with receipts |
| “Prepare me for my second-round interview” | `$jobpilot-interview` | Role-to-experience mapping, tactics, strategy and practice |
| “Reconcile outcomes from my email” | `$jobpilot-track` | Matched outcomes/interview stages, unresolved receipts preserved |

The three maintained tables are **all leads**, **actual applications**, and
**interview appointments/stages**. Leads use only `expired`, `applied`,
`not a fit`, or `null`; an applied lead remains applied after rejection.
Application outcomes and interview rounds belong in their own tables.

Read [the workflow](docs/WORKFLOW.md), [onboarding](docs/ONBOARDING.md),
[data model](docs/DATA-MODEL.md), and
[best practices and antipatterns](docs/BEST-PRACTICES.md).

## Local helpers

Python 3.10+ is needed only for these standard-library helpers:

```sh
python3 scripts/jobpilot_workspace.py init
python3 scripts/jobpilot_workspace.py doctor
python3 scripts/jobpilot_workspace.py validate
python3 scripts/jobpilot_workspace.py export
python3 -m unittest discover -s tests -p 'test_workspace.py'
```

`init` is idempotent and never overwrites existing files; `validate` checks
schema/link/evidence invariants, not whether an employer actually received an
application. `export` makes CSV views of the JSON tables. No helper opens a
website, installs software, sends data, creates a schedule, or submits a job.
Codex can maintain the documented JSON directly if Python is unavailable.

## Privacy and publication

Keep personal documents, profiles, consents, receipts, browser captures,
recordings and generated materials under `.jobpilot/` (ignored by Git). Avoid
secrets in chat, commands, tracked examples or URLs. Gitignore is **not** a
security boundary and does not remove already tracked files or Git history.
Check `git status` and staged diffs before sharing; use your normal storage,
backup and account-access controls. Files transmitted to an employer, model
provider or connector are subject to that service's handling.

This repository contains generic procedures and empty templates, not the
author's résumé, permissions, submissions or candidate-specific defaults.
Do not use another person's profile or consent as your own.

## Existing app users

The Flask/SQLite application remains a separate legacy surface. It does not
automatically implement the Codex skills, receipt checks or three-table model.
Read [migration and legacy limitations](docs/MIGRATION.md) before using it.
The current workflow deliberately does not treat a click as a submission.
No published release or push is implied by a local checkout update.

MIT licensed; see [LICENSE](LICENSE).
