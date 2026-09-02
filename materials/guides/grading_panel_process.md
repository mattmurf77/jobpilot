# Dual-Grader Panel Process — resumes & cover letters
*Use for any application worth an independent quality read. Run it in Claude Code with two subagents; the process was refined over three grading rounds on a real Head of Product application.*

## The process
1. **Two independent grader subagents, different lenses, no shared context:**
   - Grader A: senior recruiter, disciplined screen (10-second scan → 60-second read → categories).
   - Grader B: hiring manager (VP-level in the target function), slow read, probes every claim for "tell me more" interview-survivability.
2. **Fresh eyes every round**: graders never see prior rounds' scorecards; score movement then reflects the documents.
3. **Required materials for every grader:**
   - Rubric: `resume_scorecard.md` (14 weighted categories, deal-breakers, weighted /100)
   - **`writing_voice_guide.md` — voice compliance is part of Category 11 and the deal-breaker list**
   - The actual PDF (read the rendered page) + text layer, the cover letter, the live JD, and the rubric's reference docs
   - Stretch-context note when applying above current level: score scope/seniority against the TARGET level
4. **Cross-document consistency audit is mandatory** (years, headcounts, ownership verbs, timelines) — the most common deal-breaker is a resume/letter contradiction.
5. **Reconciliation** (orchestrator): per-category A/B/consensus table, flag >1-point spreads, single fix list in priority order, appended to the running scorecard file.
6. **Expect grader variance of ±4 points between rounds** — read the band and the findings, not the digits. Stop when both graders' findings are either fixed or consciously accepted structural facts.

## Learned checks (verify every time)
- PDF text-layer READING ORDER (extract with pypdf; bullets must follow their roles) — JobPilot's renderer now handles this, verify anyway.
- Hyphenated compounds survive line wrap (no "PartnerDistributed" mangling) — handled by renderer no-wrap spans.
- DOCX companion exists for structure-hungry parsers.
- Voice: run `backend/voice_check.py` on both documents before the panel; fix flags first so graders spend attention on substance.
