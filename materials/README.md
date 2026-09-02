# materials/

Everything JobPilot's tailoring and cover-letter engines are allowed to draw from.

| Path | Tracked? | What it is |
|---|---|---|
| `guides/` | yes | Generic best practices: resume, cover letter, writing voice, jargon translation, grading rubric, panel process. Edit to taste; the voice guide's hard rules are mirrored in `backend/voice_check.py`. |
| `templates/` | yes | Annotated skeletons for the three personal files below. `scripts/onboard.py` fills them from your resume. |
| `personal/` | **no (gitignored)** | Your own files: `resume_line_menu.md` (bullet inventory), `resume_template.html` (baseline resume + visual template), optional `cover_letter_reference.md` (a letter you wrote, used as a voice exemplar). |

`config.json → materials` points at these paths. Relative paths are resolved from the repo root; absolute paths work too if you keep your materials elsewhere.

**Guardrail:** the engines select, reorder, and lightly rephrase lines from `personal/`; they never invent employers, titles, dates, metrics, or skills. A number that does not appear in a source line is rejected. So the quality ceiling is the quality of your line menu: review every line `onboard.py` drafts.
