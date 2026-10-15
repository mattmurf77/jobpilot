---
name: jobpilot
description: Use the legacy local JobPilot app for explicitly requested sourcing or draft preparation in Claude Code, while following the portable workflow and preserving uncertain submissions. Codex users should start with jobpilot-start.
---

# JobPilot legacy app entrypoint

The current portable workflow is [WORKFLOW](../../../docs/WORKFLOW.md), with
[onboarding](../../../docs/ONBOARDING.md) and
[migration limitations](../../../docs/MIGRATION.md). In Codex use the
`.agents/skills/jobpilot-*` skills; no Flask server or API key is required there.

For an explicitly requested legacy app task, read only the actual user's
`data/profile.json`, private materials and current permission. Empty example
answers are unknown. Older facts or template defaults are not user statements.
Use `.venv/bin/python` only if the user has chosen and set up the app; do not
install dependencies, start schedules or call employer endpoints implicitly.

Source only within current scope and read exact official full descriptions
before selection. Keyword scores, dream boosts and title ladders are heuristics,
not eligibility. Use the user's chosen document length and truthful evidence;
never fabricate qualifications, metrics or a candidate-authored answer.

Legacy browser submission routes are disabled: the UI's confirmation click was
not independent receipt proof. Copy/paste assist is preparation only. Use the
authorized supported browser or employer site, preserve actual settled receipt
evidence, then reconcile the canonical tables. No hidden submit endpoint calls.

If a job remains `submitting`, acceptance is **unknown**, not proven failed.
Do not reset and retry merely because its browser session expired. Inspect the
portal/receipt and authorized broad employer/time-window mail, read full bodies,
and retry only after non-acceptance is established and corrected. Generic
employer confirmations stay unresolved until matched. The old SQLite lifecycle
does not sync automatically with `.jobpilot/` canonical tables.

Do not create a `/loop` or any schedule without a separate explicit request.
Honor stop/defer, protect prior submissions, save checkpoints and close completed
or sign-in-gated tabs after preserving evidence. Report actual prepared versus
submitted counts and remaining holds; no arbitrary adjacent-role padding.
