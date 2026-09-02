# Resume Scorecard — Template

A weighted 14-category rubric for grading a resume against 2026 best practices, eye-tracking data, FAANG / senior-PM hiring rubrics, and AI screening criteria. Designed to be filled out per resume version (or per resume × target JD pairing) and produce an actionable score with prioritized fixes.

**How to use:**
1. Copy this file into a new file named `scorecard_<resume-version>_<target-role>_<YYYYMMDD>.md`.
2. Fill in the **Setup** block at the top.
3. Walk each category in order; pick the 1–5 anchor that matches and capture evidence/notes.
4. Run the **Deal-Breakers** check — any one fails the resume regardless of score.
5. Compute the weighted score and translate to a grade.
6. Use the **Top-3 Fixes** block at the bottom to prioritize the next iteration.

**References built into this scorecard:**
- `resume_best_practices.md` — formatting, length, ATS, action verbs, hard-to-quantify framing
- `cover_letter_best_practices.md` — companion document scoring
- `hr_resume_review_research.md` — F-pattern scan, six fixation points, FAANG rubrics, senior+ scope signals

---

## Setup

| Field | Value |
|---|---|
| **Resume version / filename** | _____ |
| **Target role title** | _____ |
| **Target company** | _____ |
| **Seniority level** | APM / PM / Sr PM / Lead / Group / Director / VP |
| **Industry slant** | Big Tech · B2B SaaS · Sportsbook · AI · Sports Mgmt · other: _____ |
| **JD link or reference** | _____ |
| **Reviewer** | self / Claude / peer / coach / recruiter |
| **Review date** | YYYY-MM-DD |
| **Read order followed** | 10-second scan first → 60-second read → category-by-category |

### Pre-review ATS sanity check (do this before scoring)
- [ ] Resume is native PDF or DOCX (not scanned, not exported from Pages without text-selection check)
- [ ] Copied/pasted into a plain-text editor → structure stays readable
- [ ] No multi-column / sidebars / tables / text boxes / images / icons that break parsing (or you've consciously accepted ATS risk)
- [ ] Standard section headers present (`Experience`, `Education`, `Skills`, etc.)
- [ ] Dates formatted consistently throughout
- [ ] LinkedIn URL works and matches resume on titles + dates

> If 2+ of these fail, score Category 2 (ATS / AI Compatibility) at 1–2 regardless of other strengths.

---

## Scoring categories (14 weighted)

Weights sum to 100. Each category is scored 1–5 with anchored descriptors. Weighted contribution = `score × weight`. Final score = sum of weighted contributions / 5 = **out of 100**.

| # | Category | Weight |
|---|---|---|
| 1 | First-impression / 10-second scan | 10 |
| 2 | ATS / AI compatibility | 15 |
| 3 | Header & identity | 4 |
| 4 | Professional summary | 8 |
| 5 | Experience structure & chronology | 8 |
| 6 | Bullet quality & achievement density | 15 |
| 7 | Scope & seniority signal | 10 |
| 8 | Judgment & trade-off signal | 5 |
| 9 | Domain & technical fluency | 6 |
| 10 | Tailoring to JD | 8 |
| 11 | Language & tone | 4 |
| 12 | Length & density | 3 |
| 13 | Memorability & differentiation | 2 |
| 14 | Polish (typos, consistency, LinkedIn match) | 2 |

Total weight = **100**.

---

### 1. First-impression / 10-second scan — *weight 10*

The recruiter's first 10 seconds. Per eye-tracking data, attention concentrates on the six fixation points (name → title → employer → previous employer/dates → education → first bullet under most-recent role).

**Anchors**
- **5** — Name, current title, current employer instantly readable; first bullet under current role is your single strongest, quantified, role-relevant claim; visual hierarchy guides the eye through the F-scan; looks professional at a glance.
- **4** — All six fixation points findable in <5 s; first bullet is strong but not the strongest available; formatting is clean.
- **3** — Identity readable; first bullet is generic or unquantified; layout is okay but doesn't reward the F-scan.
- **2** — Reader has to hunt for current title or employer; first bullet is a duty, not an outcome; format pulls eye in wrong directions.
- **1** — Looks amateur, decorated, or template-y; key info buried; current role unclear in first 10 s.

**Score:** ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5

**Evidence / notes:**
> _What does the eye land on first? What's the first complete sentence the reader gets? Time yourself doing a 10-second scan and write what you came away with._

---

### 2. ATS / AI compatibility — *weight 15*

Will it parse correctly, score well on AI screeners, and survive automated keyword/skill matching?

**Sub-checks** (each is binary; tally before scoring)
- [ ] Single-column layout (or accepted ATS risk and submitted only via direct hiring-manager channel)
- [ ] No tables, text boxes, headers/footers, columns, images, or icons in the parsed area
- [ ] Standard section headers
- [ ] Native PDF/DOCX with selectable text
- [ ] Top 5 JD must-haves present in body of resume verbatim
- [ ] Target role title echoed in summary or header
- [ ] Acronyms paired with full forms ("Generative AI / GenAI", "Role-Based Access Control / RBAC")
- [ ] No keyword stuffing (density above ~3%) or invisible-text gimmicks
- [ ] Achievement density (bullets w/ a number or proxy) ≥ 75%
- [ ] Filename is professional: `FirstLast_Resume_Company.pdf`

**Anchors**
- **5** — All sub-checks pass; resume mirrors JD must-haves naturally and appears at top of AI-screened pile.
- **4** — 8–9 of 10 sub-checks pass; one minor friction point.
- **3** — 6–7 pass; resume parses but loses on JD keyword alignment.
- **2** — 3–5 pass; format breaks the parser or content is duties-heavy.
- **1** — Hard ATS failures (multi-column, scanned PDF, no JD alignment) — likely auto-screened out.

**Score:** ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5

**Evidence / notes:**
> _List failures explicitly. Run through Jobscan or Resume Worded for confirmation._

---

### 3. Header & identity — *weight 4*

The header block: name, location, contact, links.

**Sub-checks**
- [ ] Full name, prominent (largest type on page)
- [ ] City + State (no full street address)
- [ ] Professional email (no `xXgamerXx@…` or current-employer email)
- [ ] Phone in standard format
- [ ] LinkedIn URL — custom slug, not /in/abcd1234 default
- [ ] Portfolio / personal site / GitHub if relevant to role (especially AI / technical PM)
- [ ] No photo / DOB / marital status

**Anchors**
- **5** — All present, clean, and amplified by an extra credibility link (GitHub, Medium, portfolio) tailored to role.
- **4** — All standard items present, well-formatted.
- **3** — Most items present; missing LinkedIn or portfolio where it'd add value.
- **2** — Email or LinkedIn unprofessional; full address present.
- **1** — Photo, DOB, marital status, or other unprofessional content.

**Score:** ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5

**Evidence / notes:**
> _

---

### 4. Professional summary — *weight 8*

The summary block. Two-to-four sentences that frame the candidate for *this* role.

**Sub-checks**
- [ ] Echoes the target title verbatim (or close)
- [ ] Anchors to a flagship metric or scope claim
- [ ] Names domain expertise relevant to the JD
- [ ] No clichés ("results-driven," "passionate," "proven track record")
- [ ] No first-person pronoun if standard ("I am a…" → "Lead Product Manager with…")
- [ ] Reads as framing, not as a duplicate of bullets below

**Anchors**
- **5** — Sharp, specific, on-target. Echoes JD title, leads with scale-defining metric, names domain match. Could only describe this candidate.
- **4** — Strong and specific; one element (metric, title echo, or domain) softer than ideal.
- **3** — Generic-sounding but accurate; could fit several candidates.
- **2** — Reads as boilerplate; clichés present; no metric.
- **1** — Self-serving objective ("seeking a role that…") or absent.

**Score:** ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5

**Evidence / notes:**
> _

---

### 5. Experience structure & chronology — *weight 8*

How experience is organized and laid out.

**Sub-checks**
- [ ] Reverse-chronological
- [ ] Most-recent role gets the most bullets
- [ ] Older roles compressed (1–3 bullets each)
- [ ] Promotion history visible (stacked entries, separate entries, or noted in bullets)
- [ ] Date format consistent across all roles
- [ ] Company names + locations consistent
- [ ] Each role has a 1-line scope statement before bullets (recommended for senior+)

**Anchors**
- **5** — Reverse-chrono, recency-weighted, promotion arc visible, scope statements lead each role.
- **4** — Clean structure; promotion arc visible but not amplified.
- **3** — Structure works but recency weighting is off (older role gets equal bullets).
- **2** — Inconsistent date formats or unclear progression.
- **1** — Functional resume / non-chronological / dates obscured / promotion arc invisible.

**Score:** ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5

**Evidence / notes:**
> _

---

### 6. Bullet quality & achievement density — *weight 15*

The most-weighted category — this is where senior+ resumes earn or lose interviews.

**Sub-checks**
- [ ] Every bullet starts with a strong action verb
- [ ] No "Responsible for / Worked on / Helped with / Tasked with / Duties included"
- [ ] ≥ 75% of bullets contain a quantified outcome (number, %, $, scale proxy)
- [ ] Bullets follow Action-Verb + Task + Result structure
- [ ] Past tense for past roles, present tense for current role (consistent)
- [ ] Most-recent role's first bullet is the single strongest claim on the resume
- [ ] No filler bullets (a bullet that says "Collaborated with team" with no outcome should be cut)

**Achievement density quick math**
- Total bullets: _____
- Bullets with ≥1 number / % / $ / scope proxy: _____
- Density: _____%

**Anchors**
- **5** — ≥85% density. Every bullet earns its line. Action verbs varied and strong. First bullet of current role is a flagship.
- **4** — 75–84% density. Bullets are outcome-led; one or two could be sharper.
- **3** — 60–74% density. Mix of outcomes and duties; clearly room to tighten.
- **2** — 40–59% density. Bullets read as duties more than achievements. Action verbs weak.
- **1** — <40% density. Reads as a job description.

**Score:** ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5

**Evidence / notes:**
> _List the 3 weakest bullets explicitly so they're easy to rewrite._

---

### 7. Scope & seniority signal — *weight 10*

Is the candidate operating at the level the JD targets? (Per Karpiak Consulting: scope determines relevance.)

**Sub-checks**
- [ ] Each senior role names team size, $ owned, # products, geos, or customer count where relevant
- [ ] Decision rights stated for owned scope ("sole product owner of pricing")
- [ ] Cross-functional leadership shown (eng + design + data + GTM)
- [ ] Strategic altitude appropriate ("set strategy" vs "executed strategy") — match to JD level
- [ ] People-leadership signal at Director+ (hired N, mentored N, leveled N, retained N)
- [ ] Comparative scope claim where applicable ("operated at scope typical of one level up")

**Anchors**
- **5** — Scope is unambiguous, named, and matches target level. Reader can level-place candidate in 5 seconds.
- **4** — Scope visible; one or two roles could be sharper on size or remit.
- **3** — Scope present but inconsistent across roles; reader has to guess level once or twice.
- **2** — Scope mostly absent or vague; reads sub-target-level.
- **1** — Reads as junior; "helped" / "assisted" / "participated in" language; can't level-place.

**Score:** ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5

**Evidence / notes:**
> _Senior+ specifically: did the resume signal manager/IC track explicitly?_

---

### 8. Judgment & trade-off signal — *weight 5*

The most heavily-weighted senior+ PM trait per 2026 hiring research. Concrete moments of trade-offs under constraint, decisions with incomplete data, named pivots/sunsets.

**Sub-checks** (1+ per senior role recommended)
- [ ] At least one bullet shows a trade-off owned, not just a win
- [ ] At least one bullet shows constraint navigation (deadline, budget, compliance, headcount)
- [ ] At least one bullet shows a real pivot, sunset, or reframe (not just "shipped X")
- [ ] At least one bullet shows mechanism, not just outcome ("by shifting from feature-factory to outcome-led planning")
- [ ] Decision rationale named where relevant ("picked X over Y because…")

**Anchors**
- **5** — Multiple bullets show trade-offs, mechanisms, and constraint-navigation. Reads as a senior decision-maker.
- **4** — At least one role explicitly demonstrates judgment under constraint.
- **3** — Implied but never shown.
- **2** — All-wins narrative; no constraints, no mechanism.
- **1** — Wins claimed but unsupported / undefendable.

**Score:** ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5

**Evidence / notes:**
> _

---

### 9. Domain & technical fluency — *weight 6*

Tools, stack, vocabulary specific to the target industry.

**Sub-checks**
- [ ] Tools listed by brand name (Jira, Amplitude, Mixpanel, Looker, Figma, etc.)
- [ ] SQL / data tool fluency named if PM role expects it
- [ ] Domain vocabulary matches target industry (lending → underwriting/KYC/disclosures; AI → LLM/RAG/eval; sportsbook → handle/hold/parlay; SaaS → ARR/NRR/churn)
- [ ] AI/LLM specifics named if AI PM role (model selection, eval harness, prompt eng, RAG)
- [ ] Skills section grouped by category (Product / Domain / Tools / Methodologies / Soft)
- [ ] No outdated or filler skills ("Microsoft Office", "Internet research", "PowerPoint")

**Anchors**
- **5** — Reads as fluent in target domain. Stack named specifically. Vocab matches JD.
- **4** — Largely fluent; one or two gaps on stack or vocab.
- **3** — Generic PM skills; domain not surfaced.
- **2** — Off-domain or outdated skills present.
- **1** — Reads as someone outside the domain trying to enter it.

**Score:** ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5

**Evidence / notes:**
> _

---

### 10. Tailoring to JD — *weight 8*

How well the resume mirrors *this specific* JD (vs. a generic resume).

**Sub-checks**
- [ ] Top 5 JD must-haves visibly addressed in resume body (not just skills section)
- [ ] JD-mirrored phrasing used naturally (not pasted)
- [ ] Bullet ordering aligns with JD priorities (most-relevant bullets up top per role)
- [ ] Summary echoes target role title
- [ ] Industry vocabulary mirrors JD's industry framing
- [ ] No off-target experience over-amplified at the cost of relevant experience

**Anchors**
- **5** — Reads as written for this JD. Top-5 must-haves all answered. JD-mirrored phrasing throughout.
- **4** — 4 of 5 must-haves clearly addressed; minor reorder would tighten further.
- **3** — Resume is generic across applications; JD must-haves only partly addressed.
- **2** — Mismatched; JD must-haves invisible or buried.
- **1** — One-size-fits-all resume submitted to a senior+ role.

**Score:** ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5

**Evidence / notes:**
> _List the 5 JD must-haves and tag each as ✓ / partial / ✗ in the resume._

---

### 11. Language & tone — *weight 4*

> **Voice compliance (added 2026-08-05):** score against `writing_voice_guide.md` (same folder). Hard rules — no em-dashes, no AI-tell lexicon, no meta-statements or false-contrast shapes, no aphorism zingers, contractions in cover letters, action-verb bullet openers — are scoring anchors here; use JobPilot `backend/voice_check.py` output as evidence.

The voice of the resume. Sharpens the read at all levels; especially important at senior+.

**Sub-checks**
- [ ] Active voice throughout
- [ ] Strong, varied action verbs (no repetition of "Led" 12 times)
- [ ] No clichés ("results-driven," "synergy," "rockstar," "ninja," "guru," "team player," "passionate")
- [ ] No buzzword soup
- [ ] Tense consistent within roles
- [ ] No first-person pronouns ("I led" → "Led")
- [ ] No apologetic or insecure language

**Anchors**
- **5** — Crisp, varied, confident. No clichés. Reads like the candidate's actual voice.
- **4** — Strong but a few repeated verbs or one cliché.
- **3** — Functional but bland. Several stale verbs.
- **2** — Multiple clichés or buzzwords. Reads as templated.
- **1** — Buzzword-saturated, cliché-saturated, or passive throughout.

**Score:** ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5

**Evidence / notes:**
> _Flag cliché phrases and repeated verbs explicitly._

---

### 12. Length & density — *weight 3*

Right length for the level; right density (no waste, no over-cramming).

**Sub-checks**
- [ ] Length matches stated preference (1 page if user-preferred; 2 page if senior+ and content-justified)
- [ ] Page 1 stands alone (recruiter could read only page 1 and form an opinion)
- [ ] No orphan single-bullet roles
- [ ] No padding / filler / fluff
- [ ] Older roles compressed appropriately
- [ ] Margins ≥ 0.5"; font size ≥ 10pt body

**Anchors**
- **5** — Right length; every line earns its place; page 1 stands alone.
- **4** — Right length; one or two bullets could be cut.
- **3** — Slightly over or under target; one role is over-amplified.
- **2** — 3-page resume for a 5-year career, or 1-page resume for a 20-year senior career; or fonts under 10pt.
- **1** — Wildly mis-sized; unreadable density; or padded with empty bullets.

**Score:** ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5

**Evidence / notes:**
> _

---

### 13. Memorability & differentiation — *weight 2*

What makes this candidate stick in the recruiter's stack? (See research doc, section 8 — the differentiation pyramid.)

**Sub-checks** (count how many apply)
- [ ] One scale-defining number on page 1 ($1.4B / 280K MAU / 47 of top 50 enterprises)
- [ ] Career arc tells a story (sales → PM → senior PM is a story)
- [ ] A recognizable program or launch named
- [ ] An unusual transition or background that's a credential
- [ ] A specific named decision under constraint
- [ ] A recognized credential (invited cohort / named program / high-prestige employer)

**Anchors**
- **5** — 4+ memorability hooks; one of them is impossible to miss on page 1.
- **4** — 2–3 hooks, well-placed.
- **3** — 1–2 hooks; competent but doesn't stick.
- **2** — Reads as every other resume in the stack.
- **1** — Forgettable across the board.

**Score:** ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5

**Evidence / notes:**
> _Name the single most memorable element on this resume. If you can't, that's the score._

---

### 14. Polish — *weight 2*

Hygiene that gets resumes auto-rejected when missing.

**Sub-checks**
- [ ] Zero typos
- [ ] Zero grammar errors
- [ ] Consistent capitalization (esp. job titles, acronyms, proper nouns)
- [ ] Consistent punctuation in bullets (all end with period, or none do)
- [ ] LinkedIn matches resume on titles, employers, dates
- [ ] No copy-paste residue (wrong company name in summary, etc.)
- [ ] Filename is professional and descriptive

**Anchors**
- **5** — Zero issues across all sub-checks.
- **4** — One minor inconsistency (e.g., one bullet ends w/ period, others don't).
- **3** — Two minor issues.
- **2** — One major issue (typo, LinkedIn mismatch, copy-paste residue).
- **1** — Multiple typos / grammar errors / wrong company name.

**Score:** ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5

**Evidence / notes:**
> _

---

## Deal-Breakers — auto-fail audit

If any of these is true, the resume scores **F regardless of weighted total**. Fix before any further iteration.

- [ ] **Violates a hard rule of `writing_voice_guide.md`** (em-dashes, AI-tell lexicon, aphorism zingers, or cross-document number/verb inconsistency) — added 2026-08-05
- [ ] **Typo or grammar error present**
- [ ] **Wrong company name or wrong role title** anywhere on the resume (copy-paste residue)
- [ ] **Format breaks ATS** (multi-column, scanned PDF, image-only, no text-selectable layer) AND submitting via portal/ATS
- [ ] **LinkedIn ↔ resume mismatch** on titles, employers, or dates
- [ ] **Photo / DOB / marital status / full street address** present (US context)
- [ ] **Inflated or undefendable claim** that can't be substantiated in interview
- [ ] **Cliché-saturated objective** ("Results-driven professional seeking opportunity to leverage my synergy…")
- [ ] **No JD-tailoring** (generic resume submitted to senior+ role)
- [ ] **Outdated/irrelevant skills** dominating skills section ("Microsoft Office," "Internet research")

> Tally: ___ deal-breakers triggered. *Any* trigger → resume is F until fixed.

---

## Score computation

| # | Category | Weight | Score (1–5) | Weighted (= Weight × Score / 5) |
|---|---|---|---|---|
| 1 | First-impression / 10-second scan | 10 | ____ | ____ |
| 2 | ATS / AI compatibility | 15 | ____ | ____ |
| 3 | Header & identity | 4 | ____ | ____ |
| 4 | Professional summary | 8 | ____ | ____ |
| 5 | Experience structure & chronology | 8 | ____ | ____ |
| 6 | Bullet quality & achievement density | 15 | ____ | ____ |
| 7 | Scope & seniority signal | 10 | ____ | ____ |
| 8 | Judgment & trade-off signal | 5 | ____ | ____ |
| 9 | Domain & technical fluency | 6 | ____ | ____ |
| 10 | Tailoring to JD | 8 | ____ | ____ |
| 11 | Language & tone | 4 | ____ | ____ |
| 12 | Length & density | 3 | ____ | ____ |
| 13 | Memorability & differentiation | 2 | ____ | ____ |
| 14 | Polish | 2 | ____ | ____ |
| | **Total** | **100** | | **____ / 100** |

### Grade band
- **A — 90–100** — Interview-ready. Submit. Iterate only if a key JD changes.
- **B — 80–89** — Strong. Tighten the lowest-scoring categories before sending to dream targets.
- **C — 70–79** — Functional. Needs a real revision pass; do not send to top-tier targets in current state.
- **D — 60–69** — Major revision required. Likely getting screened out by AI or recruiters.
- **F — Below 60 OR any deal-breaker** — Not ready. Stop and rebuild before any submission.

**Final score:** ____ / 100 → **Grade: ____**

---

## Top-3 fixes for next iteration

Based on the lowest-scoring categories above and the auto-fail audit, prioritize the next three changes. Each fix should be specific, named, and verifiable on the next review.

### Fix 1 — *the highest-leverage change*
- **Category affected:** _____
- **Current score:** _____
- **What to change:** _____
- **Target outcome:** raise this category to ____ ; raise total score by ~____ points

### Fix 2
- **Category affected:** _____
- **Current score:** _____
- **What to change:** _____
- **Target outcome:** _____

### Fix 3
- **Category affected:** _____
- **Current score:** _____
- **What to change:** _____
- **Target outcome:** _____

---

## Reviewer's overall comment

Free-form 3–5 sentences capturing the gut-feel review and what would land this in front of the hiring manager vs. in the archive pile.

> _

---

## Quick interpretation guide

| If lowest-scoring categories are… | The fix is usually… |
|---|---|
| 1 (10-second scan) + 13 (memorability) | Lead the resume with a flagship metric and rework the first bullet under the current role |
| 2 (ATS/AI) | Rebuild as single column with standard headers; mirror JD must-haves verbatim |
| 4 (summary) | Rewrite summary to echo target title + lead with scale-defining metric + name domain |
| 6 (bullets) + 11 (language) | Rewrite all bullets as Action-Verb + Task + Result; cut "responsible for" entirely |
| 7 (scope) + 8 (judgment) | Add scope statements per role; insert 1–2 trade-off bullets at senior+ roles |
| 10 (JD tailoring) | List the JD's top-5 must-haves and audit resume bullet-by-bullet against them |
| 12 (length) | Compress older roles to 1–2 bullets; tighten current role's bullets to highest-impact |
| 14 (polish) | Proofread aloud; reconcile resume vs. LinkedIn; rename file to professional convention |

---

## Reference docs (in this folder)
- `resume_best_practices.md` — full 2026 best-practice playbook
- `cover_letter_best_practices.md` — companion document
- `hr_resume_review_research.md` — 2026 hiring research (eye-tracking, FAANG rubrics, senior+ signals)
- `resume_line_menu.md` — the candidate's bullet menu (for sourcing replacement bullets when scoring identifies weak ones)

---

*Scorecard v1.0 — calibrated against 2026 best-practice and hiring research. Adjust weights at top of file if the target role meaningfully changes the priority mix (e.g., for a heavily-design-aware company, raise category 13 weight; for an AI PM role, raise category 9 weight).*
