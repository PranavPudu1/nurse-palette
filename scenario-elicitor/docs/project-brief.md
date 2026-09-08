# Scenario Elicitor: project brief

Everything you need to get context on the project, in one document: what the
tool is, how to try it, the papers behind it, the design decisions, and the
full citations.

## What this is

Parents rarely get to say, in their own words, how an AI should behave around
their child. This tool lets a parent write that down and then test it.

The parent picks a worry (violence in stories, scary content, romance, and so
on), reads concrete generated situations, and writes one rule per topic. The
tool scores the rule against a rubric, asks questions about the reasoning,
and lets the parent chat with different versions of the rule to compare them.
At the end, a model that has read only the rule makes choices on fresh
situations, and the parent sees whether it chose what they would have chosen.

The output is structured data: the rule, every version of it, the test
conversations, and the parent's own picks with reasons. That data can steer a
model (the rule becomes a system prompt) or evaluate one (did the model
choose what the parent chose).

This is Pranav Pudu's capstone with Dr. Min Kyung Lee (HAI Lab, UT Austin).
The kids' content filter is the concrete domain; the pipeline itself is meant
to work in any domain.

## Try it first

The tool explains itself faster than any document.

- Link: https://scenario-elicitor-production.up.railway.app
- Enter the code TEST. That marks your session as a test, so nothing you do
  counts as study data. Explore freely.
- A laptop is best. Phones work, but the writing space is small.

What you will see, in order:

- First, a short form about you and your child, then a topic menu (eight
  worries, drawn from a study of what parents actually raised).
- Inside a topic, four stages: Consider and write (two reflective questions,
  then you write your rule), Score and revise (a rubric scores the rule and
  explains why each score is not higher), Sharpen (questions about your
  reasoning, quoting your own words), and Test (chat with any saved version
  of your rule, three conversations side by side, including a no-rule
  baseline).
- After saving, three short rounds. Each shows two AI replies to a new
  situation and you pick the one you prefer. In the last round, a model that
  has read only your rule picks too, so you see whether your rule predicts
  you.
- Three topics, then your results and downloads.

Everything is logged (every draft, edit, score, pick, and chat message), and
sessions can be resumed later with a code. Every model call has an offline
fallback, so the whole flow also runs without an API key.

## The papers behind it

Every design decision traces to a paper or to a meeting decision with Min.
What each paper concretely gave the tool:

| Paper | What it gave us |
|---|---|
| The parents paper (Driscoll et al.) | The backbone. The eight topics come straight from their Table 3, with counts of how many parents raised each. The rubric's four criteria are our synthesis of their coded themes (interpretation, not extraction). The four things a comparison varies are also theirs |
| iRULER (Bai et al.) | The rubric's shape: named criteria, four levels described as observable evidence, and a why-not-higher note on every score. Also a warning: their users accepted 100% of AI-suggested revisions, so we built a suggestion feature and then removed it. The parent writes; the AI never writes for them |
| PolicyPad (Feng et al.) | The closest analogue to our testing loop. Cases have two layers (a short summary plus the actual conversation), the rule reaches the model as a system prompt over the product's defaults, and testing follows their write, test, revise, test loop |
| Botender (Kuo et al.) | The quality bar for generated situations: drop any the parent's stated wishes already settle, nothing that turns on tone alone, each understandable on its own, and within what the agent can actually do. Also: doing nothing is a legitimate answer, so the tool does not only elicit restriction |
| ICAI (Findeis et al.) | The claim the scored round rests on: if a written policy really captures what someone wants, a model reading only that policy should reproduce their choices |
| Paul and Elder taxonomy (via Ang et al.) | The five types of reflective question the tool generates from. The type is recorded with each answer but never shown on screen |
| Robinson | The probe beside each case that changes one detail and asks whether your reasoning still holds |

The bigger picture these sit in: Constitutional AI (CAI, Anthropic 2022) aligns a
model to a written set of principles. Collective Constitutional AI (2023)
sources those principles from public input. Pluralistic alignment (Sorensen
et al., 2024) argues models should represent many people's values, not one
average. Our tool is the individual version of that idea: elicit one
person's principles, from concrete situations rather than abstract questions
(the approach GATE, Li et al. 2023, showed works better).

## Design decisions, the short story

- The parent writes the rule, always. The tool asks questions and scores,
  but never writes or suggests text. This comes from iRULER's finding that
  people accept AI suggestions uncritically.
- Concrete situations, not abstract questions. People say more, and more
  honestly, when reacting to a specific moment than when asked their values
  in the abstract.
- Versions are first class. The first draft saves as v1, edits save as v2,
  v3, and so on, and Original is the no-rule baseline. Every chat reply is
  stamped with the version that produced it, and the parent marks which
  version is final.
- Testing stops where the field stops. Neither Botender nor PolicyPad built
  guardrail or automated evaluation layers, and PolicyPad deliberately stayed
  in a sandbox. Our chat testing already matches PolicyPad's level, which is
  the right scope for a proof of concept.
- Honesty about sources. The project distinguishes what was taken directly
  from a paper (the topic menu is Driscoll's Table 3) from what was inspired
  by one (the rubric criteria are our synthesis of their themes).
- The current structure follows Min's September review: one topic at a time,
  the situation pinned on the left with the work on the right, comparison
  rounds per topic, and straight to export after the third topic.

## Full citations

| Short name | Citation |
|---|---|
| The parents paper | Driscoll, Chen, Shi, Vucharatavintara, Yao, Jin. "Understanding Parents' Desires in Moderating Children's Interactions with GenAI Chatbots through LLM-Generated Probes." CHI '26. DOI 10.1145/3772318.3791622 |
| iRULER | Bai, Cheong, Muller, Lim. "iRULER: Intelligible Rubric-Based User-Defined LLM Evaluation for Revision." CHI '26. DOI 10.1145/3772318.3790539 |
| PolicyPad | Feng, Kuo, Chen, Cheong, Holstein, Zhang. "PolicyPad: Collaborative Prototyping of LLM Policies." CHI '26. DOI 10.1145/3772318.3791689 |
| Botender | Kuo, Liu, Chen, Seering, Zhang, Zhu, Holstein. "Botender: Supporting Communities in Collaboratively Designing AI Agents through Case-Based Provocations." CHI '26. DOI 10.1145/3772318.3790500 |
| ICAI | Findeis, Kaufmann, Hullermeier, Albanie, Mullins. "Inverse Constitutional AI: Compressing Preferences into Principles." ICLR 2025 |
| Paul and Elder | Ang, Gollapalli, Ng. EACL 2023, Table 1, which reproduces the Paul and Elder question taxonomy |
| Robinson | Robinson. "Probing in qualitative research interviews: theory and practice." Qualitative Research in Psychology 20(3), 2023 |
| CAI | Bai et al. "Constitutional AI: Harmlessness from AI Feedback." Anthropic, 2022 |
| Collective CAI | Anthropic and the Collective Intelligence Project, 2023 |
| Pluralistic alignment | Sorensen et al. "A Roadmap to Pluralistic Alignment." 2024 |
| GATE | Li, Tamkin, Goodman, Andreas. "Eliciting Human Preferences with Language Models." 2023 |

Questions welcome any time. The repo also has a full changelog and a
decision-by-decision provenance ledger if you ever want the deep end.
