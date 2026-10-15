# Historical implementation note: résumé tailoring and cover generation

This archived note describes the original app, not the current Codex workflow.
Candidate-specific filenames, résumé menu contents, financial metrics and live
local test artifacts from the original build have been removed from this
shareable working tree. Earlier Git history is unchanged; do not infer that
history was scrubbed or that old tests validate the current edition.

The original implementation added:

- A numbered résumé line-menu parser and a stable baseline résumé skeleton.
- Evidence-constrained bullet selection, numeric-token checks and basic-mode
  fallback when a model response failed validation.
- Résumé/cover rendering, editable drafts and review routes.
- Keyword chips and a preview/download interface in the local Flask app.

These checks can reject some invented numbers or missing bullet IDs, but do not
prove factual truth, current job fit, valid permission or employer acceptance.
One-page trimming and keyword ranking are old app heuristics, not universal
requirements. The maintained portable procedure is [WORKFLOW](../WORKFLOW.md);
current tests live in `tests/`. See [MIGRATION](../MIGRATION.md) before importing
legacy status labels or material.
