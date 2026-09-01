# Scenario Elicitor

The **scenario-based** preference pipeline, sibling to the feature-based
`preference-elicitor/`. Where that one asks "what do you prefer" (a nurse
schedule), this one asks **"how should an AI agent behave for you"** across
concrete situations, and produces a personalized benchmark of AI behaviors.

This is the second product the advisor (Min) asked for: more directly useful for
testing an AI, seeding a benchmark across domains, or personalizing an agent.

## The pipeline (4 steps)

1. **Agent** - locked to the study domain by default (an AI that curates news
   and content for your child); `DOMAIN_LOCK=off` restores the domain-general
   chips.
2. **About your child** - who the agent acts for (age band, optional name) and
   two required intake reflection questions.
3. **Themes** - eight worry themes from Driscoll et al.'s parent interviews.
   You write one rule per theme, three themes total, in a split workspace: the
   theme's three concrete cases stay pinned on the left while the work steps
   down the right through four stages.
   - **Consider + write**: required reflection questions with the rule box
     directly below them, so your answers stay visible while you write.
   - **Score + revise**: the same rule, scored against the rubric (level 1-4
     per criterion with Why and What-the-next-level-takes), your reflections
     one click away in an accordion. Rubric design follows iRULER (Bai et al.,
     CHI '26) and Driscoll et al. (CHI '26); see docs/design-rationale.md.
   - **Sharpen**: optional after-questions (a placeholder that may be cut).
   - **Test**: chat against the rule (the two testing paths follow PolicyPad,
     Feng et al., CHI '26), browse every version your testing produced, reload
     any of them, and **mark one as final** - the marked version is what saves.
   Saving leads into **three comparison rounds for that theme**: round 1 you
   pick between two close-call behaviors and say why; round 2 reveals what
   your rule chose and hands the rule box back so you can close the gap; round
   3 reveals and scores, changing nothing. Then back to the theme menu. After
   the third theme, the session goes **straight to export** - there is no
   end-of-session comparison round.
4. **Output** - review each theme's final rule, revise before submitting,
   download or email the exports, submit to lock the session (Prolific
   completion code shown).

## Output

- `agent_preferences.json`: the full profile (agent, audience, cases, one rule
  per theme with its version trajectory and reflections, every comparison
  pick with what the rule chose and whether you agreed).
- `agent_benchmark.jsonl`: one `{agent, audience, theme, situation, at_stake,
  ideal_behavior}` row per theme.
- `agent_comparisons.jsonl`: one `{situation, instance, dimension, chosen,
  rejected}` row per decisive pick.

## Design notes

- **Author the rule, then test it against your own picks.** The datapoint is
  (theme -> the rule the person authored), written from an empty box with
  rubric feedback rather than pre-filled, so people do not just accept the
  model's words. The per-theme rounds then measure whether the rule actually
  chooses like its author.
- **Commit-then-reveal.** In every round the person picks and gives a reason
  before anything the model did is shown.
- **Concrete cases.** Cases are generated at the level of a real reported
  case (the IRAC framing from the legal-opinion elicitation paper); themes and
  their parent counts come from Driscoll et al.'s Table 3.
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
  append-only log of every draft, check, save, edit, version load, and
  comparison pick (all iterations are kept), `snapshots` holds the latest state for
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
