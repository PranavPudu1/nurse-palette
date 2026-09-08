# Scenario Elicitor: project brief

A short orientation for someone joining the project. What the tool is, how to
try it, the papers behind it, and where the deeper records live. Three pages on
purpose; every section ends with a pointer to the longer version.

## What this is

Parents rarely get to say, in their own words, how an AI should behave around
their child. This tool has a parent write that down and then test it. The
parent picks a worry (violence in stories, scary content, romance and
relationships, and so on), works through concrete generated situations, writes
one rule per topic, scores it against a rubric, tests versions of it in live
chat, and then watches a model apply the rule to fresh choices to see whether
the rule really captures what they meant. The output is structured data: the
rule and every version of it, the test conversations, and the parent's own
picks with reasons. That data can steer a model (the rule becomes a system
prompt) or evaluate one (did the model choose what the parent chose).

This is Pranav Pudu's capstone with Dr. Min Kyung Lee (HAI Lab, UT Austin).
The kids' content filter is the concrete domain; the pipeline itself is meant
to be domain general.

## Try it first

The tool explains itself faster than any document.

- Link: https://scenario-elicitor-production.up.railway.app
- Enter the code TEST. That flags your session as a test so nothing you do
  counts as study data. Explore freely.
- A laptop is best. Phones work, but the writing space is small.

What you will see: a short demographics form, then a topic menu. Inside a
topic, a workspace moves through four stages: Consider and write (two
reflective questions, then your rule), Score and revise (a rubric scores the
rule, with a why-not-higher note per criterion), Sharpen (questions about your
reasoning, grounded in your own wording), and Test (chat with any saved
version of your rule, three conversations side by side, including a no-rule
baseline). After saving, three short rounds show pairs of AI replies; you pick
one, and in the scored round a model reading only your rule picks too, so you
can see whether your rule predicts you. Three topics, then export.

## The pipeline in one paragraph

Describe the agent, describe your child, then per topic: write, score,
sharpen, test, and three comparison rounds. After the third topic the session
goes straight to export. Everything is logged append-only (every draft, check,
edit, pick, and chat turn), sessions are resumable with a code, and every
model call has an offline mock, so the whole flow runs without an API key.

## The literature, in one table

Every design decision traces to a paper or to a meeting decision. The papers and what each one
concretely gave the tool. Full titles and DOIs are in sources.pdf.

| Paper | What it gave us |
|---|---|
| Driscoll et al., CHI '26 (the parents paper) | The backbone. The eight topics come from their Table 3 verbatim, with parent counts. The rubric's four criteria are synthesized from their coded themes (interpretation, not extraction). The four dimensions a comparison varies are theirs |
| iRULER (Bai et al., CHI '26) | The rubric's shape: named criteria, four ordinal levels described as observable evidence, a why-not-higher note per score. Also a warning: their users accepted 100% of AI-suggested revisions, so we built a suggestion feature and then removed it |
| PolicyPad (Feng et al., CHI '26) | The closest methodological analogue. Two-layer cases (synopsis plus the actual conversation), the rule injected as a system prompt over product defaults, and the write, test, revise, test loop |
| Botender (Kuo et al., CHI '26) | The quality bar for generated cases: drop any the person's stated wishes already settle, nothing turning on tone alone, understandable from its own text, within the agent's abilities. Also: non-action is a legitimate answer |
| ICAI (Findeis et al., ICLR 2025) | The claim the scored round rests on: if a written policy captures what someone wants, a model reading only that policy should reproduce their choices |
| Paul and Elder taxonomy (via Ang et al., EACL 2023) | The five Socratic question types every reflective question is generated from. The type is logged but never shown |
| Robinson, Qualitative Research in Psychology 2023 | The counterfactual probe beside each case, which changes one detail to test whether the reasoning holds |

The framing layer above these: Constitutional AI (Bai et al., 2022) aligns a
model to written principles; ours elicits a personal constitution from
concrete situations rather than abstract principles. Collective Constitutional
AI (2023) sources a constitution from public input; ours is the individual
analogue. Pluralistic alignment (Sorensen et al., 2024) argues models should
represent diverse values; this tool elicits one person's slice. GATE (Li et
al., 2023) supports eliciting through concrete examples rather than abstract
questions. A fuller pointer set is in lit-review-starter.md.

## Design decisions, the short story

- One rule per topic, written by the parent, never by the AI. The tool asks
  questions and scores; it does not write. That line comes from iRULER's
  acceptance finding.
- Honest register throughout: the docs distinguish what was derived from a
  paper (the topic menu is Driscoll's Table 3) from what was inspired by one
  (the rubric criteria are our synthesis of their themes).
- Versions are first class. The first draft auto-saves as v1, edits save as
  v2, v3, and so on, and Original is the no-rule baseline, so every chat reply
  is traceable to the exact rule text that produced it and the parent marks
  which version is final.
- Testing stops where the field stops. Neither Botender nor PolicyPad built
  guardrail or automated-evaluation layers; PolicyPad deliberately stayed in a
  sandbox. Our chat testing already matches PolicyPad's level, so
  proof-of-concept scope holds (details in operationalization-prior-work.md).
- The structure follows Min's Sep 1 review: topic-first, a split workspace
  with the case pinned left and staged work on the right, comparison rounds
  per topic, and no end-of-session round.

## Where to read more

- CHANGELOG.md: how the app got its current shape, version by version, with
  the deployment serving each. The fastest way to catch up on decisions.
- provenance.pdf: the decision-by-decision ledger. One row per design
  decision: where you see it, why, and its source. (Its header says v0.4;
  the rows are current through v0.6.)
- sources.pdf: the two tables above in full, with complete citations.
- operationalization-prior-work.md: the Botender and PolicyPad scope question,
  answered.
- A caution: design-rationale.md and grounding.md predate the current
  structure and describe some removed features. Where they disagree with the
  CHANGELOG, trust the CHANGELOG.
