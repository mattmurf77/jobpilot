# Writing Voice Guide — application materials

*Rules for resumes and cover letters that read as written by a person, not generated. Built from AI-tells research (`research/writing_research_ai_tells_catalog.md`, `research/writing_research_humanize_techniques.md`) and several grading-panel rounds. JobPilot enforces the hard rules mechanically in `backend/voice_check.py` on every tailoring, edit, and cover-letter pass. Add your own rulings at the bottom; the linter follows the hard rules, you follow the rest.*

## Hard rules (the linter blocks or flags these)

1. **No em-dashes.** Anywhere: body text, subtitles, titles, PDF metadata. Use commas, colons, semicolons, periods, or the template's `·` separator.
2. **No AI-tell lexicon.** Banned words and stems: delve, showcase/showcasing, pivotal, tapestry, testament, realm, intricate, meticulous, boasts, crucial, foster(ing), leverage, seamless, robust, "evolving landscape", "underscores", "in today's", "results-driven", "detail-oriented", "passionate professional", "honest gap".
3. **No meta or throat-clearing statements.** "Let me be direct/clear", "I am writing to express", "It's important to note", "I would like to take this opportunity".
4. **No false-contrast constructions.** "It's not X, it's Y" and "not just X, but Y" shapes.
5. **No aphorism zingers.** Too-neat crafted punchlines read as AI. If a sentence sounds like a pull-quote, rewrite it as a plain statement. Treat this as the highest-weight tell; the linter only approximates it, so a human pass is required.
6. **No empty connective clauses.** Transition lines that carry no information ("As the industry evolves, ..."). Every clause must add a fact or a claim.
7. **Use contractions in cover letters** (I'm, I'd, I've, wouldn't). Zero contractions in a letter is itself an AI tell. Resume bullets don't need them; a summary may use them sparingly.
8. **Resume bullets start with an action verb.** Present tense for current-role ongoing responsibilities (Runs, Manages, Owns), past tense for completed work (Scaled, Launched, Led, Built).
9. **Numbers must trace to sources** (the line menu, the baseline resume, or your own explicit statements) **and must be consistent across documents**: years of experience, headcounts, ownership verbs (led vs. helped), timelines. A resume/letter contradiction is the most common grading-panel deal-breaker; every revision pass re-checks cross-document consistency.
10. **Don't echo the target JD's phrasing back verbatim.** Recruiters flag it as copy-paste. Engage with the company's content by adding to it, not parroting it.

## Style targets (the linter warns; judgment applies)

11. **Vary sentence length.** Follow long sentences with short ones. Uniform rhythm reads machine-made.
12. **Uneven paragraphs are good.** Don't equalize paragraph sizes.
13. **Break tricolon chains.** One three-item list is fine; several in a row is a pattern. Lists of four or more items read as inventory, not tricolon, and are acceptable for genuine enumerations.
14. **Concrete over abstract.** One only-you-could-know specific beats any amount of polish.
15. **Cover letter architecture.** If you supply a letter you wrote yourself as `materials/personal/cover_letter_reference.md`, the generator matches its paragraph architecture, length, and voice (it never copies its facts unless they are also in your resume facts). Without a reference letter, the default is the four-paragraph hook, value, fit, close structure from `cover_letter_best_practices.md`, under 300 words.
16. **Collaboration framing** for cross-team plans ("in partnership with the teams that own those products"), not solo land-grabs.
17. **Resume bolding.** No inline bold inside bullets or the skills line. Bold only your name, section headings, company names, and titles. Never bold lead-in labels ("Growth:"), which map to a default chatbot bullet format. See `research/resume_bolding_research_2026-09-02.md`.

## Process rule

Every revision pass (tailor, manual edit, cover-letter generation, any rewrite):

1. Read the `voice` findings JobPilot returns (or run `backend/voice_check.py` directly); fix flags or consciously waive them.
2. Re-check cross-document consistency for any number or verb touched.
3. Read the changed passage aloud once; mark stumbles. The ear beats every rule.

## Your rulings (add here)

Record your own phrasing decisions so future drafts honor them. Examples of the kind of thing that belongs here:

- A company-internal term and the external phrase you use instead ("Automation control group" becomes "on the Inbound Sales team").
- How you count tenure ("ten years across sales and product" vs. "seven years in product") and which frame to use where.
- Sign-off convention for letters ("Sincerely," plus full name).
- Notation choices ("0:1" rather than "zero-to-one").
- Phrases you have retired and never want to see again.
