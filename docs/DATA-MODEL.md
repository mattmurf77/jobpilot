# Private records and three canonical tables

`python3 scripts/jobpilot_workspace.py init` creates `.jobpilot/` relative to the
repository, independent of the shell's current directory. Use `--workspace`
before the subcommand for an alternate private directory; configure Git ignore
and storage access yourself for any location outside this repository. New
records have no candidate facts, permissions, jobs or interview appointments.
JSON is canonical; CSV files under `exports/` are generated views, not writers.
Use UTF-8, schema version 1, stable opaque record IDs and actual ISO dates/times.
Unknown values are JSON `null`, not fabricated placeholders or string `NULL`.

## Supporting records

| File | Content |
|---|---|
| `profile.json` | Contact, targets, location and salary preferences, approved résumé path/hash, onboarding progress |
| `experience.json` | Claims/stories with user/document evidence, dates, scope, metrics and gaps |
| `answer-bank.json` | Exact questions/answers with semantic scope, provenance and supersession; never passwords/codes |
| `consents.json` | Actual grants/revocations, scope/data/destinations, source/time/conditions; empty by default |
| `questions.json` | Unanswered/answered/deferred paired questions and requiredness |
| `state.json` | Latest task, checkpoint, paused state, current writer/browser owner; no automatic schedule |
| `materials/`, `runs/`, `evidence/`, `interviews/` | Supplied files, generated drafts, selection/form/receipt evidence and prep/recordings |

Evidence reference convention: `{ "kind": "user_report", "reference":
"chat message identifier or private relative file path", "observed_at":
"actual ISO timestamp", "summary": "what this source establishes" }`.
Kinds: `employer_portal`, `email`, `user_report`, `document`, `legacy_import`,
`official_listing`, `other`. Preserve source identifiers and full original
private content where needed; summaries are not stronger than their source.
Use strings rather than numeric requisitions to retain leading zeros/full IDs.

## 1. leads.json

Top level: `schema_version`, `leads` array. Each row:

- Required `id`, `company`, `title`, `source`, `jd_url`, `disposition`.
- `date_found`, `date_found_basis`, `date_dispositioned` may be unknown for
  legacy rows. Current discovery uses the actual date; do not use posting date.
- `source_url`, `source_id`, `native_id`, `official_url`, `aliases` with proof,
  `location`, `salary_range`, `salary_details`, `evidence`, `history`.
- `review_status`, `reason`, `next_action`, `selection_path`, `application_id`.

Allowed dispositions are exactly `expired`, `applied`, `not a fit`, `null`.
`expired` needs exact closure evidence, `not a fit` needs a concrete reason,
`applied` needs a valid `application_id`. Null keeps qualification/recovery/
account/legal/unknown salary/uncertain prior-submission holds unresolved.

Keep original salary text in `salary_range`; structured `salary_details` can
store `minimum`, `maximum`, `currency`, `period`, `basis` (`base`, `total`,
`unknown`), `geography`, `bonus`, `equity`, `source_url`, `observed_at`,
`is_estimate`, `current_or_historical`. Do not lose ambiguity by normalizing.
Location can be a human-readable string or structured list of offered offices,
remote jurisdiction, cadence, travel and evidence. Preserve exact wording.

## 2. applications.json

Top level: `schema_version`, `applications`, `unresolved_evidence` arrays.
This table contains actual submitted applications, not selected/filled drafts.
Each row requires `id`, `company`, `title`, `native_id` (nullable when genuinely
unknown), `jd_url`, `status`, `submission` and `evidence`. Include `location`,
`salary_range`, `salary_details`, `lead_ids`, `aliases`, `history`,
`outcome_events`, `current_stage`, `interview_types`, and attachment path/hash
metadata where known. Dates/actor unknown on legacy rows stay unknown.

Status values: `submitted`, `interview`, `assessment`, `offer`, `hired`,
`rejected`, `withdrawn`, `role_closed`, `unknown`.
`submission`: `submitted_at`, `actor` (`user`, `assistant`, `unknown`),
`basis` (`employer_receipt`, `user_report`, `legacy_import`), `evidence` array.
An actual submission requires at least one supporting source. Click-only,
ready/filled status or an ambiguous success cannot enter this table. Legacy
imports may retain a historical label with its actual `legacy_import` basis,
not be upgraded to independently observed employer acceptance.

`outcome_events` append dated status changes, exact application association,
source and reason. Rejections do not delete submission evidence or change a
lead's applied disposition. Record “no response recorded” as an observation,
not proof of rejection. Counting employer-only receipts as new role rows is
forbidden; they may overlap existing applications.

An `unresolved_evidence` item has stable `id`, `company`, source evidence,
candidate role IDs/aliases when supported, `reason`, `next_action`, history and
resolution reference if later resolved. Preserve every relevant group for
duplicate checking. Do not clear unknown receipts based on zero ID matches.

## 3. interviews.json

Top level: `schema_version`, `interviews` array. Each row requires:

- `id`, `application_id`, `job` (readable company/title), `interview_date`
  (ISO datetime or null), `timezone`, `interview_number` (positive or null),
  `interview_type`, `interview_subject`, `recording_link` (nullable), `status`.
- Optional `end_at`, `employer_round_label`, `interviewers`, `transcript_link`,
  `location`, `meeting_link`, `evidence`, `history`, `calendar_event_id`.

Statuses: `requested`, `tentative`, `scheduled`, `rescheduled`, `completed`,
`cancelled`. Never invent an appointment/timezone to populate a row or infer
attendance from a past date. Keep captured chronological number distinct from
an employer's stated round. Preserve old dates on rescheduling. A composite
panel may be one appointment with participants, rather than invented separate
rounds. Link only real recordings; note missing files without fabricating links.

## Maintaining records

Use one writer and read fresh before edits. Generate stable IDs once; merge
only with supported exact identity. Keep original evidence and append changes.
Write JSON atomically (temporary sibling then replace), validate and regenerate
exports. The helper intentionally offers no “mark submitted” shortcut or auto
import inference: Codex must inspect receipt evidence first. Never run coupled
exporters concurrently with another owner's writes.

`validate` checks allowed dispositions/statuses, nonempty evidence for submitted
rows, duplicate IDs/full employer-native identities, applied lead links,
interview references/numbers and empty-grant defaults. It cannot establish
semantic employer identity, actual qualifications or truth of a receipt.
`doctor` checks required records, basic schema and Git ignore. Neither grants
submission approval nor proves privacy of the rest of your repository.
