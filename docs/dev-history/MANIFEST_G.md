# MANIFEST — Agent G (deterministic P0 judgment layer)

All features are rule-based and fully offline — no `ANTHROPIC_API_KEY` needed. Every payload
carries a `mode: "basic"` seam (evaluation) or an extensible findings shape (critique) so a
future LLM mode can return the same contract with `mode: "llm"`.

## Files written (owned)

- `backend/evaluation.py` — `evaluate(job, profile, config, inventory)`: 4 scored dimensions
  (`title_seniority`, `skills`, `domain_experience`, `career_alignment`, each `{score,label,notes}`),
  location `PASS/FLAG/FAIL` (NYC + remote-OK + no-relocation rules), honest gaps (verbatim JD
  requirement fragments with zero profile/menu-term overlap; heading-based extraction, bullet
  fallback, sentence fallback for paragraph-only JDs, boilerplate/EEO filter), max-5 strengths,
  weighted recommendation `strong|moderate|weak` (weights 30/30/25/15; location FAIL caps at weak),
  2-sentence summary.
- `backend/review_checks.py` — `critique(job, resume_structure, cover_letter_md, inventory, profile)`
  → `{findings:[{severity,category,message}], counts:{high,medium,info}}`. Checks: missed-keywords
  (top requirement-weighted JD terms absent from flattened resume), weak-verbs, verb-repetition
  (3+ same leading verb), metric-free bullets (info), overlong bullets (>280 chars), skills-mirroring
  (<3 `<strong>` skills), cover letter (>320 words, company missing, role title missing, banned
  openers, generic template phrases). Messages reference bullet `source_refs`.
- `backend/interview_prep.py` — `build_prep(...)` → markdown with: header; **What they read**
  (submitted bullets verbatim + source refs, "know these numbers cold" metric list); **STAR bank**
  (one prompt per submitted bullet + 4 strongest unused line-menu bullets as backup stories);
  **Likely questions** (static PM bank by stage: recruiter screen / hiring manager / product case /
  final, plus questions derived from the resume's own metric claims); **Questions to ask** (8-10,
  JD-keyword-matched pool + defaults); **Company notes** (ONLY paragraphs extracted from stored
  posting text + explicit manual Research TODO checklist — nothing invented); consistency warning.
- `backend/routes_review.py` — blueprint `bp`, mounted at `/api/review`:
  - `POST /<job_id>/evaluate` → runs + persists to settings key `evaluation:<job_id>` (adds
    `job_id`, `evaluated_at`), logs `evaluated` event, returns result. `GET` → stored or 404.
  - `POST /<job_id>/critique` → uses latest `resume_html` meta structure + latest `cover_letter_md`
    content; 400 if no tailored resume; adds `job_id`, `has_cover_letter`.
  - `POST /<job_id>/interview-prep` → writes `data/documents/job_<id>/interview_prep.md`,
    `add_document(kind="interview_prep_md")`, logs `interview_prep`, returns `{doc_id, markdown}`.
    Uses `posting_txt` doc when present, else `job.description`.
  - `GET /insights` → pure SQL: `score_bands` (90+/80-89/70-79/60-69/<60) × status groups
    (`active`=interested/tailoring/tailored/ready, `submitted`=submitting/submitted, `interview`,
    `rejected`), `by_source`, `by_dream` (dream/not_dream), `totals` incl. `in_funnel` and
    `interview_per_submitted` (interview ÷ (submitted+interview); `null` when denominator 0),
    plus `status_groups` legend.

## Shared-file edits (authorized in prompt)

- `backend/db.py` — `DOCUMENT_KINDS` += `"interview_prep_md"`, `"posting_txt"`.
- `backend/app.py` — registered `routes_review.bp` at `/api/review`.
- `backend/docgen.py` (assigned) — `ats_check(pdf_path, job, profile)` via pypdf: never raises;
  `{ok, chars, contact:{name,email,phone}, keywords_found, keywords_total, missing}` (+`reason`
  when not ok). Top ~12 JD keywords, matching-style `_tokens`, generic-token filter.
- `backend/routes_tailor.py` (assigned) — render endpoint now includes `"ats"` in the response and
  in the `resume_pdf` doc meta; approve endpoint snapshots the job description to
  `data/documents/job_<id>/posting.txt` + `add_document(kind="posting_txt")` (skipped when empty,
  best-effort so approve never fails on it).
- Installed `pypdf` into `.venv` (pure Python).

## Verified (real DB, Flask test client)

- `py_compile` clean on all backend files; app constructs; 5 review routes registered.
- **Job 1622 (FanDuel Lead PM Payments, tailored, dream):** evaluate → `strong`, location `PASS`,
  dims title 90 / skills 96 / domain 93 / career 82, 4 honest gaps (e.g. verbatim: "Technical
  fluency: comfortable collaborating deeply with engineering on APIs, payment flows, ledger/wallet
  systems…", "Passion for sports, sports betting, or sports-adjacent products"). GET returns stored copy.
- **Job 1088 (Palantir Backend SWE, London — weak fit):** evaluate → `weak`, location `FAIL`
  ("single non-NY onsite… relocation No"), all dims ≤20, 1 honest gap via the paragraph-JD
  sentence fallback. Critique on it → 400 (no tailored resume). Evaluate/GET on job 999999 → 404.
- **Critique 1622:** 4 findings — missed-keywords (high: fanduel, payment, sports, compliance…),
  verb-repetition ("promoted" ×3 with refs), metric-free (info, 4 refs), overlong §7.1.1 (290 chars).
  Cover-letter rules verified function-level with a synthetic bad letter (all 6 rule types fire).
- **Interview prep 1622:** doc_id returned, all 7 sections present; after approve, company notes
  switch to quoting the stored `posting.txt` ("FanDuel Group is the premier mobile gaming…").
- **Render 1622:** pages=1, `ats` block present — ok:true, chars 5035, contact name/email/phone all
  true, keywords 8/12, missing `[fanduel, payment, sports, compliance]`. `ats_check` on a non-PDF
  and a missing path → `ok:false` with reason, no exception.
- **Approve 1622:** posting.txt written + posting_txt doc added (status was restored to `tailored`
  afterward as test cleanup; approve's status change is its normal contract).
- **GET /api/review/insights** over the real 22 tailored applications: bands 90+:4, 80-89:7,
  70-79:3, 60-69:3, <60:5 (all `active`); dream 18 vs not_dream 4; totals in_funnel 22,
  `interview_per_submitted: null` (nothing submitted yet).
- Job statuses never mutated by evaluate/critique/interview-prep (verified before/after; final DB
  status counts identical: 1581 new / 22 tailored / 2 archived).

## Known gaps

- Honest-gaps matching is term-list based, so a requirement like "Passion for sports…" is flagged
  even though the §17 portfolio bullets cover it — by design (gaps stated, never smoothed over),
  but an LLM mode could soften this with bullet-text reasoning.
- `interview_per_submitted` uses interview ÷ (submitted+interview); rejected jobs are not counted
  as submitted since rejection can occur pre-submission.
- Skills/keyword frequency counts are surface phrase matches (no stemming): "payment" vs
  "payments" count separately in critique missed-keywords.
