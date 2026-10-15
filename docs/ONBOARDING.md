# First-run onboarding

Use `jobpilot-start` in the repository. Start from existing private records on
later runs; do not repeat answered questions or reset a user's permissions.
This onboarding is a conversation, not a form that must be completed in one turn.

## 1. Establish documents and local state

Explain what will be stored and ask the user to supply or identify their current
résumé. Read it using supported local tools. Request a sample cover letter or
other personal writing **optionally**; do not block setup if they have none.
Never request private employer/customer data, a password or verification code.
Use `python3 scripts/jobpilot_workspace.py init` to create empty private records.
Ask before copying a document to a new location if the user's sharing scope is
unclear. Put supplied sources in `.jobpilot/materials/`, preserving originals.

Record the approved upload résumé's relative path, SHA256, review date and
status in `profile.json`; do not mark an exploratory rewrite approved. Verify
actual displayed and clickable contact/portfolio links. Extract text from every
page, and use available PDF/document rendering tools for all-page visual QA.
If a format/tool is unavailable, record the limitation instead of claiming QA.

Confirm contact information rather than trusting stale browser autofill.
Ask only for information relevant to the intended applications; optional
demographic answers and references may remain unset. Never assign legal,
work-authorization or demographic defaults from a sample file.

## 2. Interview for search preferences

Ask a few related questions at a time, following the user's answers. Cover:

- What work do they want to own, and what should be excluded? PM is the example
  family, not a license to add program/operations/marketing roles. For PM,
  consider Senior, Lead, Staff, Principal, Technical, qualifying Product Owner,
  and leadership roles according to demonstrated scope, not a fixed title list.
- Domains, customer types, company stages and sizes; strong preferences versus
  mandatory limits. Separate openness from demonstrated specialist experience.
- Location priority, residence, compatible remote countries/states, office
  cadence, commute radius, travel and relocation. Do not infer foreign work
  authorization or a role's location from company headquarters.
- Work type and employment type, start-date constraints, employer exclusions,
  prior relationships and application-frequency restrictions where relevant.
- Minimum and target **base** salary, currency and period; separately desired
  total compensation. Decide how to handle unpublished or ambiguous pay and
  overlapping ranges. Do not silently convert currencies or promise a floor.
- Desired scope and progression: senior IC versus formal management; suitable
  stretch roles and which missing requirements should remain holds.

Persist confirmed preferences with the user's wording/source/date. Keep an
assistant's recommendation separate until adopted. An unresolved preference
does not prohibit useful document setup or a first experience interview.

## 3. Conduct a deeper experience interview

Read the résumé first and choose the highest-value gap. Ask **one focused
experience question per turn** unless the user requests a questionnaire. Build
three or more useful stories as available; no fixed story count is a gate.

For each actual role/project ask: Who had the problem? What did the candidate
personally own? What was decided, why, and what alternative was rejected?
Who collaborated? What shipped? What changed and how was it measured? What
was the baseline, period and scale? What tradeoff or failure changed the plan?
Store a short exact quote and the source, dates, scope and remaining gaps.

Clarify carefully where it changes qualification:

- Exact employment and role dates; related career years versus PM-specific or
  specialist years. Preserve approximate dates as approximate.
- Individual ownership versus team contribution, influence/mentoring versus
  actual direct reports, report count/duration and managing managers.
- B2B versus B2C; internal tools versus externally used products; discovery,
  roadmap, prioritization, engineering/design delivery and outcome ownership.
- Hands-on technical work versus coordination; architecture/data/API ownership
  with a concrete example rather than a list of vendor names.
- Prototypes, personal projects and daily AI tools versus shipped production
  features, real users, model evaluation, adoption/revenue and measured scale.
- Observed versus modeled/forecasted outcomes; percentage points versus relative
  change; funnel-step conversion versus an end-to-end business result.

A user report is valid evidence of what it actually says. Do not require a
public link for every private accomplishment; do not invent unstated metrics.
If a figure is unavailable use a defensible qualitative result. Label estimates
and their basis. Preserve later corrections and retain superseded history.
Show a compact synthesis at natural pauses: supported stories, proposed bullet
wording, role implications and material gaps. Do not silently promote draft
claims into the approved résumé or legal answer bank.

## 4. Import optional history and agree permissions

Ask whether there is an existing submission tracker, old confirmations,
interview list or calendar to reconcile. Preserve original files privately.
Import confirmed rows with their real evidence strength; legacy status labels
are not fresh employer receipts. Put employer-only or ambiguous confirmations
in `applications.json.unresolved_evidence`, not separate fabricated roles.
An empty tracker never proves there were no prior applications.

Use the permissions discussion in [WORKFLOW](WORKFLOW.md). Record grants only
after an actual user instruction, with the destination/action/data scope,
source and time, conditions and expiry if any. For example, a user may approve
research and local drafts now, review each submission, or authorize submission
for a named queue using approved materials. None is assumed by installation.

Check the tools actually available: web research, local PDF/document tooling,
supported employer browser, optional Gmail and Google Calendar. Connector access
is not permission for every action. If absent, offer supplied job links,
manual uploads or exported receipts; do not invent a connection or install a
plugin without the necessary authorization. A model subscription does not
guarantee browser/connector capabilities on every machine.

## 5. Close with a reviewable starting point

Summarize confirmed targets, evidence, approved résumé, permission scope and
open questions. Mark onboarding `in_progress` or `ready_for_research` based on
actual state, never `ready_to_submit` merely because setup completed. Propose
the next concrete action within permission. No background run or schedule is
created. When restarting, resume the private checklist and latest user scope.
