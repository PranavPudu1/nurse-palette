# What we took, and from where

The papers behind the Scenario Elicitor, and concretely what each one gave us.
The full decision-by-decision record is in provenance.md; this is the short
version, one entry per paper.

## Driscoll et al. — the topics, the criteria, and what the comparisons vary

Driscoll, Chen, Shi, Vucharatavintara, Yao, Jin. "Understanding Parents' Desires
in Moderating Children's Interactions with GenAI Chatbots through LLM-Generated
Probes." CHI '26. 10.1145/3772318.3791622

They showed 24 parents real conversations between children and AI chatbots and
coded what worried them. We use their results in three places.

**The eight topics a participant chooses from** are their Table 3 verbatim,
including the count of how many parents raised each. Five are about what the AI
said back, three about what the child asked. Nothing in the topic list is our
guess about what parents care about.

**The four things the rubric scores** are a synthesis of their coded moderation
themes: naming a specific action, setting scope, fitting the child's stage, and
saying when to escalate. This is interpretation rather than extraction; no table
in the paper contains these four.

**The four dimensions a comparison varies** are theirs. Three are named in their
future work (clarity of intent, severity, developmental cues) and the fourth,
where the risk originates, is their system-risk against misuse-risk split.

## iRULER — the shape of the rubric

Bai, Cheong, Muller, Lim. "iRULER: Intelligible Rubric-Based User-Defined LLM
Evaluation for Revision." CHI '26. 10.1145/3772318.3790539

**The rubric's structure**: named criteria, four ordinal levels each described as
observable evidence, and a why-not-higher explanation attached to every score.
Their instrument is three unweighted booleans over a whole document; ours is four
weighted criteria over one rule.

**One thing we took as a warning rather than a feature.** They offer an AI
revision targeting the weakest criterion, and their participants accepted 100% of
the suggestions offered. We built it, then removed it, because a channel that
reliable turns the model's language into the person's stated preference.

## Ang et al. — the reflective questions

Ang, Gollapalli, Ng. EACL 2023, Table 1. Reproduces the Paul and Elder taxonomy.

**The five question types** every reflective question in the tool is generated
from: clarification, probing assumptions, probing reasons and evidence, probing
implications, and probing alternative viewpoints. These questions have no correct
answer; they exist to make someone examine a thought rather than defend it. The
type is recorded with each answer and never shown to the participant, because it
names our taxonomy rather than their task.

## PolicyPad — how a rule is shown, delivered, and tested

Feng, Kuo, Chen, Cheong, Holstein, Zhang. "PolicyPad: Collaborative Prototyping
of LLM Policies." CHI '26. 10.1145/3772318.3791689

**Two-layer cases**: a short synopsis plus the actual conversation, rather than a
description of a situation on its own.

**The rule reaches the model as a system prompt** with scaffolding, and the
precedence line saying the person's instructions win is modelled on their
open-source scaffold.

**Write, test, revise, test again.** Both of their testing paths: regenerate the
reply, or continue the conversation. Ours versions one rule for one topic where
theirs versions a whole policy document.

## Botender — what makes a case worth showing

Kuo, Liu, Chen, Seering, Zhang, Zhu, Holstein. "Botender: Supporting Communities
in Collaboratively Designing AI Agents through Case-Based Provocations." CHI '26.
10.1145/3772318.3790500

**The quality bar every generated case has to clear.** Drop a case whose answer
is already settled by what the person has told us, since it teaches nothing. No
cases that turn on tone alone. Each must be understandable from its own text. And
the agent can only do what it can actually do: allow, soften, add context,
decline, or bring the parent in.

**Non-action counts as an answer**, so the tool does not only ever elicit
restriction.

## Inverse Constitutional AI — why we measure agreement at all

Findeis, Kaufmann, Hullermeier, Albanie, Mullins. "Inverse Constitutional AI:
Compressing Preferences into Principles." ICLR 2025.

**The claim the final round rests on**: if a written set of principles really
captures what someone wants, a model reading only those principles should
reproduce their choices. That is why the tool synthesizes a policy from
everything a person wrote and picked, then freezes it and scores whether it
agrees with them on cases they have not seen.

## Robinson — the probing technique

Robinson. "Probing in qualitative research interviews: theory and practice."
Qualitative Research in Psychology 20, 3 (2023).

**The counterfactual probe** shown beside each case, which changes one detail to
see whether the reasoning holds. Driscoll cites this as their interview method
and we credit both. Ours is weaker than theirs by design: it is one line fixed
when the case is written, and cannot adapt to what the person just said.

## What we did not take

**GATE and OPEN** motivated the project but contributed no mechanism. Their
elicitation is model-driven, which is the thing our design departs from.

**Injecting a published taxonomy into a generation prompt** looks borrowed from
Botender and is not: it was already in the tool before we read them. Recorded
here for honesty in the other direction.

**No human validation.** Botender ran a 90-participant study on its case
generation and iRULER had two experts rate 96 essays. We have run neither.
