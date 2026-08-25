# Changelog

Versions of the Scenario Elicitor, newest first. Each entry names what changed
and the Railway deployment serving it, so a build can be pointed at by date
("the one Min reviewed on the 25th") and returned to.

Deployment ids come from `railway deployment list` run in `scenario-elicitor/`.

---

## v0.3 — 2026-08-17 — theme-first restructure

Deployment `37f83c47-d774-4445-8cc8-d95bb3b7d17c`. First version under version
control; everything before this was reconstructed from the working tree and has
no recoverable source.

- Rules are written **one per theme** rather than one per case. A participant
  picks 3 of Driscoll's 8 concerns, sees 3 cases for each, and writes one rule.
- The eight themes carry their paper names, parent counts, and plain-language
  descriptions on screen. Previously the names were sent to the model and never
  shown, and one theme (Skepticism of Technical Safeguards) was missing.
- The case card stopped showing `at_stake`, `considerations`, `analysis` and
  `affects` before the rule is written. That content now feeds the reflective
  question generator instead.
- The baseline AI reply lost its "two to four sentences" cap and gained a
  reconstructed child-safe product default. Replies went from ~35 to ~78 words.
- Pre-write questions may no longer attribute a belief to the participant.
- The AI "Suggest a minimal revision" was removed entirely, replaced by a nudge
  quoting the participant's own reflection answers back at them.
- Comparisons ask which before why, and never auto-advance.
- Three-column workspace; rule-version comparison; tooltips no longer clipped by
  their column.
- A session saved before this version resumes to the theme menu with an
  explanation rather than half-restoring into a shape that no longer exists.

## v0.2 — 2026-08-12 — transparency pass

Deployment `c5599fd0-109f-4c23-9ce7-014a64d45c2e`, now removed from Railway and
not recoverable. Info icons on every generated artifact, the probe merged into
the pre-write reflection block, reflection feeding the rubric check, and the
three-round comparison structure.

## v0.1 — earlier

Pre-version-control. Not recoverable.
