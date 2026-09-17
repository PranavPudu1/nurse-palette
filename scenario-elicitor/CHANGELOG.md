# Changelog

Versions of the Scenario Elicitor, newest first. Each entry names what changed
and the Railway deployment serving it, so a build can be pointed at by date
("the one Min reviewed on the 25th") and returned to.

Deployment ids come from `railway deployment list` run in `scenario-elicitor/`.

---

## v0.9 — 2026-09-17 — guided steps, dictation, sturdier failure modes

- **Numbered guidance everywhere**: Consider + write reveals read -> answer
  -> write one sub-step at a time behind Done buttons; Score + revise,
  Sharpen and Test carry big numbered orange section headings (ungated,
  since comparing and editing is a loop). Test reordered: columns first,
  edit box second, final pick last; compare columns bordered and taller.
- **Dictation**: a Dictate mic under every writing box; recording is
  transcribed (gpt-4o-mini-transcribe) and appended to the box.
- **Intake questions wait for a Next button** and regenerate when the age
  changes, so they are always about the child actually described.
- **"skip" failsafe**: refusals and few-word rules never reach the question
  generator; Sharpen explains and offers regeneration instead. Longer
  gibberish gets exactly one nudge question from a hardened prompt.
- **Loud API-failure banner** replaces silent placeholder fallback; info
  icons name the model in use.

Deployment: `5d763d5d-bf38-4f91-831c-b46f92841564`.

---

## v0.8 — 2026-09-16 — Min's review round: follow-the-flow fixes

Everything here traces to the Sep 16 review with Min and Eve.

- **Sharpen reordered**: the rule you wrote (read-only), then the probing
  questions, then the editable box at the end, so revising is the obvious
  last act.
- **Regenerate probing questions** from the current rule, with a staleness
  note when the rule has changed since the questions were made. Old answers
  are logged to events (reflect_after_regen) before being replaced.
- **Gibberish/skip failsafe**: the question prompt writes up to three
  questions instead of exactly three; an empty, refused, or too-thin rule
  gets only what it supports plus a plain nudge to actually write the rule.
  Check now requires a minimally real draft.
- **Test stage swapped**: working box first, compare columns in the middle,
  the final-version pick and Save at the end. One-sentence instructions on
  each section, styled large enough to notice.
- **Model shown**: every info icon on generated content carries a
  "Model: gpt-4o-mini" line.
- **Rubric is view-only** for participants (the editor was an iRULER
  carryover for internal tuning).
- **One nav at a time**: the wizard's bottom Back/Continue disappears inside
  a theme, where it was being mistaken for the stage navigation.

Deployment: `b4ff6441-3955-4e7f-86e6-00c51d64c817`.

---

## v0.7 — 2026-09-02 — usable on phones

- **Mobile sweep, CSS only.** All rules live inside a max-width 700px media
  query, so desktop rendering is untouched. On phones: tighter page padding,
  smaller headings/cards/pills, step pills wrapping two per row, 16px inputs
  (stops the iOS focus zoom), and fixed-height chat panes grow with their
  content (capped at half the viewport) instead of becoming nested scroll
  traps once the columns stack.
- **Gating moved from disabled buttons to click-time validation.** On phones,
  Continue never enabled on the intake screen: text boxes commit on blur, and
  a disabled button cannot receive the tap that would blur them. Continue,
  stage Next, Save as new version, Check my answer, and Save-and-test are now
  always tappable; a blocked tap stays put and says what is missing. Also
  fixes a latent desktop bug where callbacks read text one interaction stale
  (a round-2 edit followed immediately by Save could record the pre-edit
  rule).

Deployment: `a65b1f48-d38a-4610-96e2-89e5c6c134ea`.

---

## v0.6 — 2026-09-02 — first-class versions

- **A version dropdown on every rule box** (Score + revise, Sharpen, Test):
  Original is the empty no-rule baseline, v1 is the first draft (saved
  automatically on leaving Consider + write), and "Save as new version" is the
  single creation point after that. A round-2 edit appends a version too, so
  nothing untitled ever speaks.
- **Per-version persistent chats.** Each version owns its thread; switching the
  dropdown switches threads and loses nothing; every reply is stamped with its
  version.
- **The Test stage redesigned**: final-rule dropdown (with preview and "load
  into the box") beside the working box, and below them three compare columns,
  each chatting with one selected version. The single chat pane, the "Try it on
  a case" button, and the Compare-versions expander are gone.
- **Sharpen keeps the rule box** in the same spot as Score + revise, questions
  below it.
- Export: `rule_versions` is now the version store `[{label, rule}]`, the
  transcript is every thread keyed by version, and the final label is recorded.

Deployment: `ee079327-0252-4cfa-b79a-d403a9054db9`.

---

## v0.5 — 2026-09-01 — the split workspace, staged; no end-of-session rounds

Implements Min's calls from the Sep 1 review, verbatim where possible.

- **Split is the only layout.** The four other prototypes and their switcher
  are gone; the case stays pinned on the left while the work steps down the
  right.
- **Four stages, in her order.** Consider + write (the rule box directly below
  the questions, so the answers stay visible while writing), Score + revise
  (rubric plus a reflections accordion), Sharpen (placeholder after-questions
  that may be cut), Test (chat against the rule, browse and reload versions,
  and mark ONE as final; the marked version is what saves).
- **No all-themes rounds.** Min: after the last theme the session goes straight
  to export. The policy synthesis and its three end-of-session rounds are
  removed; per-theme rounds stay. 18 comparisons per session, down from 27.
- **Round-2 edits are re-recorded** the moment they happen, so the export, the
  menu, and later rounds all test what the person actually revised.
- Defects: version-compare read the wrong response field and always rendered
  empty panes; theme-menu buttons shared the sb_pick_ snapshot prefix and could
  be assigned on resume; the stage and final-version keys were not snapshotted;
  the dead description input threaded an always-empty string into three
  prompts.
- A narrow-viewport note appears on the gate when columns stack; full mobile
  design is deferred until Winnie says whether parents would really use a
  phone.
- New doc: `docs/operationalization-prior-work.md` — Botender ships elicited
  policies into a live bot with no guardrails; PolicyPad stops at a sandbox on
  purpose. Neither builds an evaluation layer, so proof-of-concept scope holds.

Deployment: `30c4c2e8-ee90-4f40-9530-7c9e0efe4260`.

---

## v0.4 — 2026-08-25 — two-level testing, layout prototypes, version control

First version with a git history. Everything before this was reconstructed from
the working tree.

- **The three comparison rounds run twice.** Per theme against the rule just
  written, then again at the end against the policy synthesized from all of
  them. In the theme rounds the model reads only that rule, and round 2 hands
  the rule box back so the person edits their own words rather than accepting a
  rewrite. 27 comparisons per session.
- **Five workspace layouts** behind a switcher visible only in test sessions:
  four new prototypes and the previous layout kept for comparison. All five
  write the same session state.
- **Reflective answers were single-line inputs** showing roughly the first eight
  words. They are text areas now, and every question is required.
- **Two questions at setup**, before any case exists, so what a participant
  brings is theirs rather than a reaction to a case we wrote.
- Answers no longer vanish when a widget stops rendering, which the staged
  layouts would have caused.
- The rubric editor had been orphaned by the layout refactor and is reachable
  again, anchored to the score it edits.
- "Edit this answer" on the review page navigated nowhere; comparison rows now
  record the theme they tested; dropped an export field nothing wrote.
- Both design documents rewritten to one form: what was decided, where you see
  it, why, and the source.
- Dead code removed: the flat six-case generator, the adaptive clarifying round,
  the reference-answer generator.

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
