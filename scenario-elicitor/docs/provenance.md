# Provenance

Every design decision in the tool, where to see it, why it was made, and the
source. Current as of v0.4. One row per decision; anything needing a paragraph
is in [design-rationale.md](design-rationale.md).

Rows marked **ours** are not from any paper. They are listed because a decision
with no source is worth knowing about too.

## Sources

| Short name | Citation |
|---|---|
| **Driscoll** | Driscoll, Chen, Shi, Vucharatavintara, Yao, Jin. "Understanding Parents' Desires in Moderating Children's Interactions with GenAI Chatbots through LLM-Generated Probes." CHI '26. 10.1145/3772318.3791622 |
| **iRULER** | Bai, Cheong, Muller, Lim. "iRULER: Intelligible Rubric-Based User-Defined LLM Evaluation for Revision." CHI '26. 10.1145/3772318.3790539 |
| **PolicyPad** | Feng, Kuo, Chen, Cheong, Holstein, Zhang. "PolicyPad: Collaborative Prototyping of LLM Policies." CHI '26. 10.1145/3772318.3791689 |
| **Botender** | Kuo, Liu, Chen, Seering, Zhang, Zhu, Holstein. "Botender: Supporting Communities in Collaboratively Designing AI Agents through Case-Based Provocations." CHI '26. 10.1145/3772318.3790500 |
| **ICAI** | Findeis, Kaufmann, Hullermeier, Albanie, Mullins. "Inverse Constitutional AI: Compressing Preferences into Principles." ICLR 2025 |
| **Ang** | Ang, Gollapalli, Ng. EACL 2023, Table 1. Reproduces the Paul and Elder question types |
| **Robinson** | Robinson. "Probing in qualitative research interviews." Qualitative Research in Psychology 20, 3 (2023). Driscoll's probing method |

---

## What the participant sees

| Decision | Where you see it | Why | Source |
|---|---|---|---|
| Topics come from eight named parent concerns, not from us | The theme menu, eight cards | Parents were interviewed about real child-chatbot transcripts and their worries were coded into eight themes. Using them means the tool covers what parents actually raised rather than what we assumed | Driscoll Table 3 |
| Each theme shows a plain description and how many of 24 parents raised it | Under each theme name | The paper's labels ("Wrong Approach to Delivery") mean nothing to someone who has not read it, and the count is what makes the menu read as findings rather than our opinion | Driscoll Table 3 |
| One rule per theme, written across three cases | The workspace: three cases, one rule box | A rule written for a single case is a local reaction. Writing one rule that must hold across three makes it a general principle with concrete examples under it | ours, from Min's review |
| Cases are generated per theme, three at a time | Appear when you open a theme | Generating against one named theme lets the category be set in code rather than inferred, so a case cannot land in a bucket the menu cannot reach | Botender A.2.4 (set-level generation) |
| A case is dropped if the person's stated wishes already settle it | Not visible; a filter in the prompt | A case whose answer is already determined teaches nothing. This is the mechanism behind surfacing what someone had not considered | Botender A.2.1 |
| No trivial cases, and each must be self-evident from its own text | Case quality, throughout | A case that turns on tone alone, or that needs explaining, does not provoke a real decision | Botender A.2.1-A.2.3 |
| The agent can only allow, soften, add context, decline, or involve the parent | Case generation prompt | Cases that need abilities the agent does not have cannot be answered | Botender A.2.5 |
| Letting content through is a legitimate answer | Baseline replies and options | Without this the tool only ever elicits restriction | Botender A.1.2 |
| The case card shows the title and situation, nothing else | The workspace | It used to also show what was at stake, the tradeoffs, and how it plays out, which handed the participant the answer before they wrote one | Min's review |
| What is at stake and the competing values become questions, not statements | The "Before you answer" questions | Same content, opposite effect: as prose it tells them what to think, as a question it makes them think | Min's review |
| Every case appears as an actual conversation | Case tabs, chat bubbles | A description of a moment and the moment itself are different things to react to. Two layers, a synopsis plus the exchange | PolicyPad §5.2.2, Fig. 5D |
| The "before" reply is a real product default, not a bare model | The agent's turn in every case | It applies the safeguards a mainstream child mode ships with: age-appropriate wording, pointing to a trusted adult, no graphic detail, a crisis resource on self-harm. Reconstructed from published behaviour; we do not have anyone's real prompt | ours |
| That reply has no length limit | Same | It was capped at two to four sentences, which made the before-state read as unrepresentative next to a real product. Length now varies with the question | Min's review |
| Questions before writing use five question types designed to provoke examination | "Before you answer" | These types exist to make someone examine a thought rather than defend it, and they have no correct answer | Ang Table 1 (Paul and Elder) |
| A pre-write question may never attribute a belief to the participant | The question prompt's HARD RULE | One asked why the parent assumed something the AI's own case had introduced. Attributing a position to someone who has not taken one corrupts what they write next | Min's review |
| Each case carries one counterfactual "what if" question | "As you write, consider" | An interviewer does not take a first answer; they change one detail to see whether the reasoning holds. Ours is fixed at generation time and cannot adapt the way a live interviewer would | Driscoll §3.5, method from Robinson |
| Questions are required, not optional | Save is blocked until answered | Their purpose is to make someone think before writing, and they feed the rubric check, so a skipped one silently weakens it | Min's review |
| The rule is scored on four weighted criteria with four levels each | "How your rule scores" | A rule can be exactly right about what someone wants and still be too vague for an agent to follow. The rubric checks only that narrower thing | iRULER §4.1.1, App. B |
| The four criteria's content comes from what parents said mattered | The criteria names | Specific action, scope, developmental fit, escalation are a synthesis of their coded moderation themes, not a one-to-one mapping | Driscoll §4.2, §5.3 |
| Every criterion shows why it scored, and what the next level needs | The expanders under the score | Feedback that says only "level 2" is not actionable. The why-not-higher was their most used feature | iRULER A.1.1, Table 4 |
| The rubric never sees the reflection answers as scorable text | Not visible; a fence in the prompt | With reflection added, a draft naming nobody scored level 4 on "Fits the audience" in 2 of 3 runs, because the model credited intent the rule did not contain | ours, found in testing |
| No AI rewrites the rule | There is no suggest-a-revision button | It existed and was removed. In the study it came from, participants accepted every suggestion offered, and it is one more generated component needing accuracy validation | iRULER §7.3.1 acceptance rate; removal was Min's call |
| Instead, the participant's own words are quoted back | "Put this in your rule" | If they said something while thinking and their rule does not mention it, the gap is theirs to close in their own language | Min's review |
| The rule can be tested against the conversation at any time | "Try it on a case" | Writing a rule and immediately seeing what it does is the fastest way to find out whether it says what was meant | PolicyPad §5.2.5, Fig. 8 |
| The rule is delivered to the model as a system prompt over the defaults | Not visible | The parent's instructions sit on top of the product defaults and win where they disagree | PolicyPad §5.3 |
| Two rule versions can be asked the same question side by side | "Compare versions" | Seeing one difference at a time is what makes a change legible | Min's review |

## Testing what was written

| Decision | Where you see it | Why | Source |
|---|---|---|---|
| Three rounds run per theme, then three more at the end | After saving a rule, then after all themes | Two different claims. The theme rounds test whether that rule predicts the person's choices; the final rounds test whether one policy built from everything still does | ours, from Min's review |
| Each comparison changes exactly one thing between the two replies | The "varies" tag on each moment | If two things change, a choice says nothing specific. The four dimensions are the child's age, severity, clarity of intent, and where the risk comes from | Driscoll §7 and Table 14 |
| A pick is committed with a reason before anything is revealed | Round 2 and 3 | Seeing the model's answer first would contaminate the reason, and the agreement score would stop measuring anything | ours |
| The buttons come before the reason box, and nothing auto-advances | All rounds | The reason box used to sit above the buttons, asking people to justify a choice they had not made, and one click skipped past it entirely | Min's review |
| In the theme rounds the model follows only that theme's rule | Round 2's reveal | A disagreement then points at a gap in that rule, rather than at an aggregate the person never wrote | ours |
| Round 2 hands the rule box back rather than offering a rewrite | Under the reveal | Same reason the AI revision was removed. Round 3 then scores the edited rule, so the loop measures whether their own revision closed the gap | ours |
| A policy is synthesized from every rule and every pick | After the final round 1 | If a written policy really captures what someone wants, a model following only that policy should make the same choices they did. That is what round 3 measures | ICAI |
| Round 3 is frozen and scored | The last round | Agreement means nothing if the thing being measured changes while measuring it | ours |

## Study mechanics

| Decision | Where you see it | Why | Source |
|---|---|---|---|
| Every generated artifact carries an info icon | The small "i" beside each | A participant can see what produced anything on screen and where the method came from. Also how we keep ourselves honest about what is borrowed | ours |
| Session state is snapshotted after every interaction | Not visible; the resume code | Someone can leave and come back, and a crash does not lose a session | ours |
| Sessions saved before the theme restructure reset to the theme menu | Only if resuming an old code | Per-case answers cannot honestly be reshaped into per-theme ones, so the old work is cleared with an explanation rather than half-restored | ours |
| Four layout prototypes, switchable | A control visible only in test sessions | Min asked to see the options rather than have them described. Not a participant-facing feature | Min's request |
| Study arms exist but randomisation is off | Not visible | Handing a random visitor a version with no rule-writing screen is not a default we want. `STUDY_ARMS=on` enables it | ours |

## Convergent, not borrowed

One row for honesty in the other direction. Putting a published taxonomy into a
generator prompt was already in the tool before Botender was read; Botender
A.2.3 does the same thing with a different taxonomy. What we did take from that
section is the convention of citing the technique and the embedded taxonomy
separately.

## Known gaps

- **Which dimension a comparison varies is a model judgment**, not a selector
  targeting expected disagreement or cycling for coverage. It is recorded in
  each row so coverage can be analysed after the fact. Min called dimension
  choice "the key".
- **Nothing here has been validated with human coders.** Botender ran a
  90-participant study on its case generation; iRULER had two experts rate 96
  essays. We have run neither.
- **The child-safe baseline is a reconstruction** from published behaviour, not
  any vendor's actual instructions.
