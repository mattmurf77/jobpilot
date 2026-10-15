---
name: jobpilot-track
description: Maintain JobPilot leads, confirmed applications and interview stages; reconcile authorized email evidence and outcomes, dedupe authorized calendar changes, and summarize observed application trends without inventing resolutions.
---

# Track applications and outcomes

Read [the data model](../../../docs/DATA-MODEL.md) and outcome sections of
[the workflow](../../../docs/WORKFLOW.md). Read latest actual scope and fresh
private tables/permissions before writes. Use one writer; preserve original
evidence, history and unknown identities. Do not run a historical import again
for an ordinary update or infer that an interrupted write did not commit.

Maintain three canonical JSON tables, with CSV exports from the helper:
leads (dispositions only expired/applied/not a fit/null), actual submitted
applications (status/outcome evidence), and interview appointments/stages.
An applied lead remains applied after rejection; drafts live under runs, not
as submitted records. Keep source-row counts distinct from exact role counts,
and unresolved employer receipts separate because they may overlap known roles.

For a user-authorized Gmail review use requested time bounds and paginate;
search confirmations, rejections, invitations, assessments, reschedules and
follow-ups. Read complete relevant bodies, retain IDs/timestamps and association
basis. Supplement with broad employer searches rather than requiring native ID
text. Exact matches may update one role; ambiguous employer-only receipts stay
in unresolved evidence. Do not reject all company applications from one role's
rejection. Preserve actor/time/source strength; reconciling historical mail is
not a new submission today. No sending/archive/labels or recruiter/reference
contact is implied by read authorization.

Track requested/tentative/scheduled/rescheduled/cancelled/completed interviews,
timezone, appointment number, employer round label, type, subject and real
recording/transcript links. Preserve changes, not invented attendance. For
explicitly authorized calendar writes, inspect existing events first, use
confirmed actual time/timezone and meeting details, preserve event IDs and
avoid duplicates. Ask for missing time or an authorized tentative hold; do not
invent duration, links, guests or RSVP/send invitations without permission.

Use `python3 scripts/jobpilot_workspace.py validate` then `export` after edits.
Helpers check structure, not receipt truth. Check ignored private files before
sharing. For summaries define cohort/window and missingness; separate invitation
from completed interview, unresolved/no-response from rejection, submitted actor
from reconciliation. Compare observed role scope/domain/seniority/location fit
without causal claims from small samples. State unresolved coverage and next
actions honestly. Do not schedule future checks unless explicitly requested.
