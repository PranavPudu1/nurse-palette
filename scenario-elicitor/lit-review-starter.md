# Lit review starter: the scenario-based pipeline

A starter map, not an exhaustive review, situating the scenario pipeline (elicit
how a person wants an AI to behave, via concrete situations, into a personalized
benchmark). One line each on how it relates. Min asked for a lit review; this is
the pointer set to build it out.

## Closest framing: personal / pluralistic constitutions
- **Constitutional AI** (Bai et al., Anthropic, 2022). Align a model to a written
  set of principles (a "constitution"). Ours elicits a constitution too, but
  grounded in **concrete situations and chosen behaviors** rather than abstract
  principles, and it is **personal** to one user. (Min referenced "the
  constitutional one.")
- **Collective Constitutional AI** (Anthropic / Ganguli et al., 2023). A
  constitution sourced from public input. Ours is the individual analogue:
  personalize the constitution per person.
- **Pluralistic alignment** (Sorensen et al., "A Roadmap to Pluralistic
  Alignment," 2024). Models should represent diverse values, not one aligned
  behavior for everyone. Our tool is a way to elicit one person's slice of that.
  (Min used the phrase "pluralistic alignment.")

## The elicitation UX reference
- **Farsight** (Wang et al., CHI 2024). From a high-level AI prompt, fan out an
  explorable tree of concrete use cases and harms to surface what a builder had
  not considered. This is our reference for the situation-generation step.

## Concrete scenarios vs abstract questions (why scenarios)
- **GATE** (Li et al., 2023). An LM interviews the user; its "generative active
  learning" mode shows concrete examples to react to, which surfaces novel
  considerations. Supports eliciting via concrete situations.
- **Scenario / vignette and conjoint methods** (Hainmueller, Hopkins, Yamamoto,
  2014). People's reactions to realistic scenarios track how they actually
  behave. Justifies scenarios over abstract self-report.
- **Legal-opinion elicitation / case format (the paper Min shared).** Elicits
  expert opinions on complex, concrete cases (mined from Reddit threads) laid out
  in the IRAC structure: Case, then Issue / Rule / Analysis as the information the
  opinion rests on, then Conclusion (p. 2462, Fig. 5). This is our reference for
  (a) how concrete a case must be, including who it is for and a real example, and
  (b) the card structure; the person authors the Conclusion (ideal behavior).
  TODO: pin the exact citation.

## The output as preference data
- **RLHF** (Christiano et al., 2017; Ouyang et al., 2022) and **DPO** (Rafailov
  et al., 2023). Models are aligned from pairwise "chosen vs rejected" comparisons
  over responses. Our JSONL `{situation, chosen, rejected}` is exactly this shape,
  personalized, so it can test or fine-tune an agent.

## The sibling pipeline (feature-based)
- **OPEN** (Handa et al., 2024) and **classic preference/feature elicitation**.
  Domain features plus pairwise learning of weights. This is the feature-based
  product; the scenario pipeline is the alternative representation Min described.

## Authoring the ideal behavior (respond step)
- **Rubric-based writing feedback (the "iRuler" paper, name to confirm).** A user
  authors an evaluation rubric; the system critiques a draft against it and the
  user revises (its Fig. 3 draft -> feedback -> revise flow). We adopt this for the
  co-writing respond step: a generic rubric drives per-criterion feedback and an
  optional suggested revision of the user's own draft. The rubric-authoring angle
  also transfers to the scheduling pipeline (participant-authored priorities).

## Confirming and evaluating the elicited preferences
- **Pairwise + natural-language principles (paper Min shared, name to confirm).**
  Combines pairwise comparison with stated NL principles; informs the Confirm step,
  where concrete pairwise instances validate and probe the boundary of an authored
  behavior. Open sub-problem: which dimension to vary so a pair is informative.
- **Explanation-then-recreate (paper Min shared, name to confirm).** Generate a
  plausible explanation per decision, then test whether an LLM given all the
  explanations can recreate the user's choices. A candidate evaluation for whether
  an elicited preference set is sufficient/faithful (backlog).

## To locate / add
- Case-based or precedent-based alignment (aligning via concrete cases rather
  than rules) is a directly relevant thread; find the specific recent paper(s)
  before citing. Also check 2025-2026 preference-elicitation and personalization
  work Min has not reviewed yet.
- Confirm exact titles/citations for the three papers above.
