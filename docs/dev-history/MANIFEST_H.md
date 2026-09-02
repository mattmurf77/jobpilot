# MANIFEST_H — Frontend UI for judgment-layer features (Agent H)

## Files written

- `web/js/review.js` (edited)
- `web/js/pipeline.js` (edited)

No shared files touched. No servers started on 5151/5050/5252.

## What was added

### review.js
- **🧭 Evaluate fit** button (before ✨ Tailor) → `POST /api/review/<id>/evaluate`, renders the
  evaluation panel card (`#rv-eval-card`, between the feedback card and the resume card):
  recommendation badge (strong=green / moderate=amber / weak=red) + summary, per-dimension
  score bars (`var(--accent)`, width=score%, clamped 0-100) with label/score/notes, location row
  with PASS/FLAG/FAIL badge + notes, and Strengths / Honest gaps columns (gaps amber).
- On job switch, `GET /api/review/<id>/evaluate` restores a stored evaluation; any error
  (incl. 404 = never evaluated) hides the panel.
- **🔍 Review draft** button (after 📄 Render PDF) → `POST /api/review/<id>/critique`, renders the
  findings panel (`#rv-findings-card`, below the evaluation panel): counts line
  ("2 high · 1 medium · 1 info"), findings ordered high→medium→info (unknown severities render
  last with a grey chip), colored severity chips, and the fix-hint line. Uses a raw `fetch` (only
  place) so a 400 is distinguishable → toast "Tailor a resume first." Findings clear on job
  switch (tracked via `findingsJobId`), but survive same-job refreshes (render/save/tailor).
- **ATS badge** (`#rv-ats-badge`, after the pages badge): from `r.ats` in the render response.
  Green `ATS ✓ 11/12 keywords` when `ok && contact.name && contact.email`; else amber `ATS ⚠`
  with a `title` tooltip listing missing contact fields + keywords. Cached per job in
  `atsBadges{}` so it persists until the next render for that job and clears/restores on job switch.
- All new styles appended to the existing injected `#style-review` element.

### pipeline.js
- `DOC_CHIP_LABELS` += `interview_prep_md: "Interview prep"`, `posting_txt: "Posting snapshot"`.
- **🎤 Interview prep** button on `submitted` and `interview` rows → busy state →
  `POST /api/review/<id>/interview-prep` → success toast + `window.open("/api/documents/file/<doc_id>")`
  + refresh (chip appears from the reloaded docs).
- **Insights card** at the top of the Pipeline board, collapsible, collapsed by default.
  `GET /api/review/insights` fetched alongside the other refresh calls with `.catch(() => null)`
  → card hidden entirely on failure. Renders: score-band funnel table
  (band | active | submitted | interview | rejected, missing values shown as "–"),
  one-line dream-vs-other comparison, interview rate (fraction ≤1 rendered as %).
  Plain table, styles appended to `#style-pipeline`.

## Verification (backend did not exist during this work)

1. `node --check` on both files — pass.
2. Static cross-check: every id referenced via `el()`/`getElementById` exists in the rendered
   template; every emitted `data-act` has a handler branch — all match.
3. **Mock harness test** (no JobPilot server; scratchpad static server on port 8899, since
   removed): copied `app.js`/`review.js`/`pipeline.js`/`style.css` into a scratch page with
   `window.fetch` stubbed to return exact contract-sample JSON. Verified in a live browser:
   - Evaluation panel renders (badge colors, bars, FLAG location, strengths/gaps) from both
     POST (button) and GET (restore on load/job switch); hides on 404.
   - Findings panel: counts line, severity grouping/chips, unknown-severity finding renders
     defensively, hint line; 400 → "Tailor a resume first." toast; clears on job switch.
   - ATS badge: `ATS ✓ 11/12 keywords` with tooltip after render; clears when switching to a
     job without a render this session and restores when switching back.
   - Pipeline: Insights collapsed by default, toggle opens table + dream line + "Interview
     rate: 28.6%"; card hidden when the insights fetch rejects and returns when it recovers.
   - 🎤 Interview prep on Submitted + Interview rows: POST fired, toast shown,
     `window.open("/api/documents/file/40")` called, board refreshed; "Interview prep" and
     "Posting snapshot" chips render.
   - No console errors; screenshots checked for layout.

## Not verified (needs live integration pass)

- Real response shapes from Agent G (mock used the contract verbatim; rendering is defensive
  about missing keys, but nesting drift in `insights` beyond `bands`/`dream`/`interview_rate`
  would just render as "–"/hidden lines).
- Whether `GET /api/submit/documents` includes `interview_prep_md`/`posting_txt` kinds — the
  chip relies on it (chip only appears after refresh if the docs endpoint returns them).
- Popup blockers may suppress `window.open` after the async POST; the doc chip is the fallback.
- `interview_rate` semantics assumed fraction (≤1 → ×100); values >1 rendered as-is with %.

## Known gaps

- Critique 400 detection uses one raw `fetch` instead of `API.post` (status code needed);
  everything else uses the shared helpers.
