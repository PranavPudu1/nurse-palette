# What we took, and from where

The papers behind the Scenario Elicitor, and concretely what each one gave the
tool. The decision-by-decision record is in provenance.md; this is only the
things that materially shape what a participant sees.

## What each paper gave us

| Paper | What we took | Where you see it |
|---|---|---|
| **Driscoll** | The eight topics a participant chooses from, their Table 3 verbatim, including the count of how many of the 24 parents raised each | The topic menu |
| **Driscoll** | The four things the rubric scores, synthesised from their coded moderation themes. Interpretation rather than extraction: no table in the paper contains these four | "How your rule scores" |
| **Driscoll** | The four dimensions a comparison varies: clarity of intent, severity, developmental cues, and where the risk originates | The "varies" tag on each moment |
| **iRULER** | The rubric's shape: named criteria, four ordinal levels each described as observable evidence, and a why-not-higher explanation on every score | The score column and its expanders |
| **iRULER** | Their 100% acceptance rate for AI-suggested revisions, taken as a warning rather than a feature. We built the revision and then removed it | There is no suggest-a-revision button |
| **Ang** | The five reflective question types every question in the tool is generated from. The type is recorded with each answer and never shown, since it names our taxonomy rather than the participant's task | Every question in the tool |
| **PolicyPad** | Two-layer cases: a short synopsis plus the actual conversation, rather than a description of a situation on its own | The case tabs |
| **PolicyPad** | The rule reaches the model as a system prompt over the product defaults, with the parent's instructions winning where they disagree | Not visible |
| **PolicyPad** | Write, test, revise, test again. Both of their testing paths: regenerate the reply, or continue the conversation | "Try it on a case" |
| **Botender** | The quality bar every generated case must clear: drop one the person's stated wishes already settle, nothing that turns on tone alone, each understandable from its own text, and within what the agent can actually do | Case generation |
| **Botender** | Non-action counts as a legitimate answer, so the tool does not only ever elicit restriction | Baseline replies and options |
| **ICAI** | The claim the scored round rests on: if a written policy really captures what someone wants, a model reading only that policy should reproduce their choices | The final round |
| **Robinson** | The counterfactual probe beside each case, which changes one detail to see whether the reasoning holds. Ours is fixed when the case is written and cannot adapt the way a live interviewer would | "As you write, consider" |

## Full citations

| Short name | Citation |
|---|---|
| **Driscoll** | Driscoll, Chen, Shi, Vucharatavintara, Yao, Jin. "Understanding Parents' Desires in Moderating Children's Interactions with GenAI Chatbots through LLM-Generated Probes." CHI '26. 10.1145/3772318.3791622 |
| **iRULER** | Bai, Cheong, Muller, Lim. "iRULER: Intelligible Rubric-Based User-Defined LLM Evaluation for Revision." CHI '26. 10.1145/3772318.3790539 |
| **Ang** | Ang, Gollapalli, Ng. EACL 2023, Table 1. Reproduces the Paul and Elder question taxonomy |
| **PolicyPad** | Feng, Kuo, Chen, Cheong, Holstein, Zhang. "PolicyPad: Collaborative Prototyping of LLM Policies." CHI '26. 10.1145/3772318.3791689 |
| **Botender** | Kuo, Liu, Chen, Seering, Zhang, Zhu, Holstein. "Botender: Supporting Communities in Collaboratively Designing AI Agents through Case-Based Provocations." CHI '26. 10.1145/3772318.3790500 |
| **ICAI** | Findeis, Kaufmann, Hullermeier, Albanie, Mullins. "Inverse Constitutional AI: Compressing Preferences into Principles." ICLR 2025 |
| **Robinson** | Robinson. "Probing in qualitative research interviews: theory and practice." Qualitative Research in Psychology 20, 3 (2023) |
