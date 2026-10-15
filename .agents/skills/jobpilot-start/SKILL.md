---
name: jobpilot-start
description: Onboard or resume a candidate's private JobPilot workspace in Codex, gather documents, interview for job targets and concrete experience, and establish scoped permissions before research or applications.
---

# JobPilot start

Read [onboarding](../../../docs/ONBOARDING.md) and the authority section of
[the workflow](../../../docs/WORKFLOW.md). Find the repository from this file;
do not assume the author's machine path or use another candidate's records.
This skill records procedure, not consent. No AGENTS.md is required: the explicit
start skill is sufficient. Respect the new user's applicable instructions.

1. Inspect existing `.jobpilot/` profile, experience, answer bank, consents,
   questions and state if present. Preserve them and the latest user task.
   Initialize missing empty records with `scripts/jobpilot_workspace.py init`
   from the repository; never reset an existing candidate or grant.
2. Ask for the current résumé and optional sample cover/writing. Read supplied
   documents, preserve originals privately, verify contact links and ask which
   résumé is approved for uploads. Missing optional samples do not block setup.
3. Interview for target duties/titles/seniority, domains/exclusions, work type,
   prioritized locations/commute/travel/relocation and salary currency/period/
   base floor versus total compensation. No inherited default answers.
4. Conduct a deeper experience interview, one useful question at a time. Record
   actual ownership, decisions/tradeoffs, collaborators, shipped results,
   dates/scale/measurement and gaps. Separate reports from mentees, B2B from
   B2C, prototypes from production and personal contribution from team output.
   Proposed résumé language is a draft, not new evidence or approved upload.
5. Offer import of prior applications/receipts for duplicate protection. Keep
   uncertain evidence unresolved; an empty import is not proof of no history.
6. Inspect actual available tools, then agree separate scoped permissions for
   research/local drafts, browser entry/uploads/final submit and optional
   Gmail/Calendar. Record only actual user grants with source and conditions.
   Never ask for passwords/codes or assume installation authorizes actions.

Persist substantive answers with a short quote, source/date and scope. Reuse
already answered questions and latest corrections. A factual answer does not
accept an agreement; a connector connection does not authorize a message.
Support a bounded ongoing submission grant without repeated routine prompts.
Honor stop/defer/skip immediately; no schedules or agents start by default.

Finish with confirmed profile/approved documents, permission scope, open gaps
and the next useful action. Use `jobpilot-source`, `jobpilot-apply`,
`jobpilot-interview` or `jobpilot-track` only as the user's task requires.
