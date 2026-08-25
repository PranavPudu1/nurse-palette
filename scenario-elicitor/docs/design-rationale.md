# Design rationale: the rubric and the pairwise generation

How the two core generative components of the Scenario Elicitor are designed, what
papers informed them, and where we deliberately depart. Written for the lab
(Min); citations use section and page numbers of the camera-ready PDFs.

**Papers**

- **iRULER**: Bai, J., Cheong, W. S., Muller, P., and Lim, B. Y. 2026. iRULER:
  Intelligible Rubric-Based User-Defined LLM Evaluation for Revision. CHI '26.
  https://doi.org/10.1145/3772318.3790539
- **Parents**: Driscoll, J., Chen, Y., Shi, V., Vucharatavintara, I., Yao, Y.,
  and Jin, H. 2026. Understanding Parents' Desires in Moderating Children's
  Interactions with GenAI Chatbots through LLM-Generated Probes. CHI '26.
  https://doi.org/10.1145/3772318.3791622
- **ICAI**: Findeis, A., Kaufmann, T., Hullermeier, E., Albanie, S., and
  Mullins, R. 2025. Inverse Constitutional AI: Compressing Preferences into
  Principles. ICLR 2025.

---

## 1. The rubric

### Goal

When a person authors "the ideal behavior the agent should take" for a concrete
case, a blank text box produces vague, incomplete statements, and a pre-filled AI
answer produces agreement bias (people accept whatever is there). The rubric is
the middle path: the person writes in their own words, and the system evaluates
the draft against explicit criteria so they can see what is missing and revise.
The rubric also turns each authored behavior into structured data (per-criterion
levels and a weighted score) we can analyze later.

### How iRULER informed it

iRULER's six design guidelines for user-defined feedback are the skeleton
(iRULER §3, p.4): feedback should be **specific** (explicit criteria, DG1),
**scaffolded** (a rubric with levels and weights, DG2), **justified** (why and
why-not explanations, DG3), **actionable** (counterfactual revisions, DG4),
**qualified** and **refinable** (the rubric itself can be judged and edited,
DG5-6). Concretely we adopted:

1. **Structure.** Named criteria, percentage weights summing to 100, and 4
   ordinal levels per criterion, each level a prose descriptor of observable
   evidence (iRULER §4.1.1 p.4 and Appendix B p.25, their JSON rubric format).
   The overall score is their weighted formula, sum(w_k x s_k)/L on a 0-100
   scale with a color band (iRULER §4.1.1; Fig. 2 B2).
2. **Feedback form.** Per criterion, a selected level with a **Why**
   justification and a **Why-not-higher** justification, written in their
   "Overall-Supporting" shape: a one-sentence overall judgment followed by
   bullets citing concrete phrases (iRULER prompt A.1.1 steps 4-6, p.22).
   Why-Not was the most used feature in both of their experiments (Table 4,
   p.25), so we always include it rather than hiding it behind a click.
3. **Actionable revision, minimally.** The "Suggest a minimal revision" button
   targets ONE criterion (the weakest, weight-breaking ties) at its next level
   and follows iRULER's Minimal Modification directive: "If the original text
   already meets a criterion, do not change it" (A.1.2, pp.22-23), with a
   rationale that ties the change to the rubric's own language. The person
   previews and applies or ignores it; iRULER frames this review-and-select as
   the guard against over-reliance (§7.3.1, p.16).
4. **Seeded but editable.** iRULER's core critique is of "generic,
   one-size-fits-all rubrics that overlook specific task goals" (§1, p.2), and
   its position is that rubrics are "evolving rather than static templates"
   (§1, p.2; §7.2, p.16). We therefore ship the rubric as a SEED the person can
   edit in place (names, weights, level descriptors), with every edit logged.
   We chose four criteria, not five: iRULER trimmed their own instrument from
   five to four to reduce load (fn.12, p.10), and their participant R21
   reported being overwhelmed by too many criteria (§6.4.2, p.14).
5. **Honest non-claims.** We do not claim the rubric increases users' sense of
   control: both iRULER experiments found no significant effect on control
   (§6.1.3 p.12; §6.2.3 p.13). Supported claims are quality, helpfulness,
   confidence, and fewer iterations.

### How the Parents paper grounds each criterion's content

The four criteria are not invented; each maps to an empirical finding about how
people specify desired AI behavior:

- **Specific action (30%).** Parents described ideal moderation as "the action
  they wanted the system to take and which part of the interaction they wanted
  changed" (Parents §4.2, p.11), with a concrete vocabulary of 14 operations
  (Table 9, p.29). Level 4 requires both the operation and its target.
- **Scope and boundaries (30%).** "Parents expect strong boundaries that avoid
  seeding new ideas" (§4.2, p.14): moderation should not "expand the child's
  option set." This criterion asks what the agent must NOT do and the condition
  under which the answer flips. It merges our earlier separate "Boundary" and
  "Gray area" criteria, which overlapped; iRULER's rubric-of-rubrics penalizes
  criteria where one piece of evidence scores under multiple criteria
  ("Criteria Alignment," Table 6, p.28).
- **Fits the audience (20%).** The Parents paper reframes developmental fit as
  a SAFETY property, not politeness: "if a child cannot understand the
  vocabulary... they cannot internalize the warning, even if the content is
  factually correct" (§4.2, p.13). Their §5.3 (p.17) lists the tunable
  dimensions we use in the descriptors: content, tone, reading level, depth.
- **Escalation and reasons (20%).** "Defer to Support" was the third most
  common desired behavior (16 of 24 parents, Table 4, p.13): the agent should
  "recognize when a situation is too serious... and defer to human support"
  (§4.2, p.14). And explanation is mandatory even for refusals; the paper's
  refusal code is literally "Refuse Response and Explain" (Table 9, p.29).

### Deliberate departures

- **Seeded rubric rather than authored from blank.** iRULER has users build
  rubrics from an empty table with AI assists (§4.2.1, p.6). For a study
  respondent doing a one-session task, blank-slate rubric authoring is a large
  ask; we seed and allow editing. This implements DG1-DG4 fully and DG5-DG6 in
  a light form.
- **The probing question is not from iRULER.** iRULER never asks the user a
  question; its Why/Why-Not/How-To are questions the user asks of the system.
  Our single probing question after feedback follows the Parents paper's
  interview method: "probing techniques to prompt elaboration, comparisons, and
  consideration of hypothetical variations" (§3.5, p.7).
- **No tracked-diff change cards.** iRULER renders revisions as per-change
  accept/reject diffs (Fig. 3 g-i). Streamlit has no equivalent widget; we show
  the full suggested revision with its rationale and a single Apply/Ignore.
  Noted as a fidelity gap.

---

## 2. The pairwise generation (confirm step)

### Goal

An authored ideal behavior is a stated preference; stated preferences are
unreliable at the boundary (the project's core GATE/OPEN motivation). The
confirm step generates, for each authored case, one **concrete instance** that
is more specific than the case (a named, near yes-or-no situation) plus two
contrasting agent behaviors, and records which one the person prefers. Its three
jobs: confirm what the authored behavior implies, elicit the boundary (what the
agent should NOT do), and resolve edge cases the prose left open.

### Grounding

- **Instances must be more concrete than the case.** This was Min's direct
  feedback (July meetings), matching the Parents paper's method: their probes
  are specific single-turn incidents, and their scenario-selection kept only
  cases parents rated realistic (median realism above 4) yet controversial
  (concern variance above 1.0), i.e. concrete gray-area instances (§3.3, p.6).
  An informative pair sits where reasonable people split.
- **Vary ONE named dimension.** The Parents paper documents the context
  variables along which the same person's desired behavior flips: the child's
  age and maturity (§4.2 p.13, Figs. 7-8), the severity of the situation, the
  intent behind the request ("the intention behind a prompt determined the
  appropriateness of a response," §4.1.3 p.11), and the locus of risk (System
  Risk vs Misuse Risk, Table 14 p.33). The generator must pick the single
  dimension along which the authored behavior is most likely to flip, and the
  chosen dimension is recorded in the data (`dimension` field) so we can
  analyze coverage.
- **No idea-seeding.** The options must not introduce new ideas or options
  beyond the instance, mirroring the boundary expectation in Parents §4.2 p.14.
- **Why pairwise at all: reconstruction.** ICAI validates an extracted
  principle set by whether an LLM applying it can reproduce the original
  pairwise annotations ("annotation reconstruction accuracy," ICAI Abstract and
  Fig. 1). Our confirm picks are exactly the data that later lets us test
  whether the authored behaviors predict the person's actual choices; agreement
  between the authored statement and the confirm picks is the per-person
  version of ICAI's metric (see docs/evaluation-metrics.md).

### Open problem (flagged, not solved)

Choosing WHICH dimension yields the most informative pair is currently an LLM
judgment inside the prompt. A systematic selector (for example, targeting the
dimension with the highest expected disagreement, or cycling dimensions per
person for coverage) is future work; Min called dimension choice "the key" in
the July 29 discussion.
