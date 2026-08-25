# Scenario Elicitor

The **scenario-based** preference pipeline, sibling to the feature-based
`preference-elicitor/`. Where that one asks "what do you prefer" (a nurse
schedule), this one asks **"how should an AI agent behave for you"** across
concrete situations, and produces a personalized benchmark of AI behaviors.

This is the second product the advisor (Min) asked for: more directly useful for
testing an AI, seeding a benchmark across domains, or personalizing an agent.

## The pipeline (6 screens)

1. **Agent** - what AI or agent you are setting preferences for. Domain-general,
   with AI-behavior example chips (scheduling assistant, kids' content filter,
   writing assistant, email assistant).
2. **Behavior** - how you want it to behave (optional) and, importantly, **who it
   is for**. Naming the audience keeps the cases concrete.
3. **Cases** - a Farsight-style fan-out: the LLM generates a set of **concrete
   cases** the agent would face, grouped into a few themes, to surface ones you
   had not considered. Each case follows the paper's structure (the case, what is
   at stake, things to weigh, how it plays out, who it affects). Drill into a
   theme; three cases are written for it when you open it.
4. **Respond** - for each case you **author the ideal behavior**, in your own
   words, as a short co-writing loop: you draft, hit **Check** to get per-
   criterion rubric feedback (a level 1-4 per criterion with Why and
   What-the-next-level-takes, plus a weighted 0-100 score and one probing
   question), and can ask for a **minimal revision of your own draft** targeted
   at your weakest criterion, to apply or ignore. The rubric itself is
   viewable and editable. The box starts empty (a model's take is opt-in
   reference only) so you are not just accepting a pre-filled answer. Rubric
   design follows iRULER (Bai et al., CHI '26) and Driscoll et al. (CHI '26);
   see docs/design-rationale.md.
   Each case also opens as a **real exchange** (what the child asks, and how the
   agent replies today), and under your answer there is a **scenario chat**: hit
   **Test my rule** to see the agent answer that same moment while following what
   you wrote, revise and test again to compare v1 against v2, or keep chatting to
   stress-test it. Structure and the two testing paths follow PolicyPad (Feng et
   al., CHI '26, §5.2.2 and §5.2.5); see docs/provenance.md.
5. **Confirm** - for each case you answered, a **concrete comparison**: the LLM
   turns the case into a specific, near yes-or-no instance and offers two
   contrasting behaviors, and you pick the one you prefer. This confirms what was
   learned and probes the boundary (what the agent should not do).
6. **Output** - review and download the benchmark.

## Output

- `agent_preferences.json`: the full profile (agent, audience, cases, the ideal
  behavior you authored for each, and the confirm-step comparisons).
- `agent_benchmark.jsonl`: one `{agent, audience, situation, at_stake,
  ideal_behavior}` row per authored case. A personalized benchmark: run each
  situation through a model and compare its response to your ideal behavior.
- `agent_comparisons.jsonl`: one `{situation, instance, chosen, rejected}` row per
  decisive confirm-step pick, a second benchmark over boundary behaviors.

## Design notes

- **Author the behavior, not a pairwise pick.** The datapoint is (situation ->
  the ideal behavior the agent should take), authored by the person in a co-writing
  loop with rubric feedback (the iRuler draft-feedback-revise idea) rather than
  pre-filled, so they do not just agree with the model. This is the meeting
  direction: a set of (case, ideal behavior) pairs you can test any model against.
- **Pairwise returns as confirmation.** After authoring, the Confirm step uses
  concrete pairwise instances to validate the learned preference and elicit the
  boundary, rather than as the core mechanic.
- **Concrete cases.** Cases are generated at the level of a real reported case,
  following the IRAC framing (case, issue, rule, analysis, conclusion) from the
  legal-opinion elicitation paper Min shared; the person authors the conclusion.
- **Farsight reference.** The cases step emulates Farsight's fan-out (Wang et al.,
  CHI 2024): a diverse, themed set that surfaces non-obvious cases, with per-theme
  an adaptive round that probes where authored rules are ambiguous.
- **Runs with no key.** Every model call degrades to a deterministic offline
  mock, so the whole flow is clickable without an API key.

## Run

```
cd scenario-elicitor
pip install -r requirements.txt
streamlit run app.py
```

Reads an OpenAI key from `st.secrets`, the environment, or a repo-root
`.env.local` (keys `OPENAI_API_KEY`, `OPENAI_KEY`, or `openai`). Model is
`gpt-4o-mini`.

## Online data collection

The app runs as a hosted study instrument (Railway; see `Dockerfile`):

- **Entry gate**: an access code (env `ACCESS_CODE`, default `HAILAB25`) starts
  a real session; the code `TEST` starts a test-mode session flagged and
  excluded from analysis. New respondents fill a short demographics form and
  get a 6-character **resume code**; entering it later restores the session.
- **Persistence**: SQLite at `$DATA_DIR/elicitor.db` (a mounted volume in
  production). `respondents` holds identity + demographics, `events` is an
  append-only log of every draft, check, suggestion, save, edit, and confirm
  pick (all iterations are kept), `snapshots` holds the latest state for
  resume.
- **Revise and submit**: answers can be revised from the review page until
  **Submit my responses** freezes the session.
- **Email results**: with `GMAIL_USER` + `GMAIL_APP_PASSWORD` set, respondents
  can email themselves the profile JSON + benchmark with instructions for using
  them in ChatGPT/Claude. Without the env vars the feature degrades to a note.
- **Capstone poster demo**: the entry screen also has a **Capstone Poster**
  button that starts a session in one click, with no access code and no
  demographics form, for visitors who scan the QR code at the poster session.
  Those sessions are flagged `is_test=1` and tagged `source: "poster"` in their
  `session_start` event, so they stay separable from `TEST` sessions.
- Docs: **`docs/grounding.md`** (what each pipeline step does, what prior work
  informed it, and the prompt that runs it), `docs/provenance.md` (the same by
  source: what was borrowed and how it was changed),
  `docs/design-rationale.md` (rubric + pairwise grounding),
  `docs/evaluation-metrics.md`, `docs/cost-estimation.md`.
