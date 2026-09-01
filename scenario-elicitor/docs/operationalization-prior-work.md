# Did the reference systems operationalize their elicited policies?

Min's question from the meeting: before building an instruction / guardrail /
evaluation stack, check what Botender and PolicyPad actually did with the
policies their users produced. Answer: one shipped the policy into a live bot
with no guardrails, the other deliberately stopped at a sandbox. Neither built
a guardrail layer or an automated adherence metric.

## Botender

Kuo, Liu, Chen, Seering, Zhang, Zhu, Holstein. "Botender: Supporting
Communities in Collaboratively Designing AI Agents through Case-Based
Provocations." CHI '26. DOI 10.1145/3772318.3790500 (arXiv 2509.25492).

- **Instruction layer: yes, fully live.** A deployed "task" (trigger prompt +
  action prompt) enters the running Discord bot's instruction set immediately;
  an orchestrator agent decides whether a task triggers, a task agent composes
  the reply. Validated in a five-day field study across six Discord servers
  with real community members.
- **Guardrail layer: none.** No content filter or post-output verification
  anywhere in the deployment path.
- **Evaluation layer: pre-deployment only.** Generated "case-based
  provocations" are voted on by community members before deploy; there is no
  automated adherence metric and no post-deployment measurement.
- Contribution framing: the provocation-driven deliberation process, with
  deployment machinery included but thin.

## PolicyPad

Feng, Kuo, Chen, Cheong, Holstein, Zhang. "PolicyPad: Collaborative
Prototyping of LLM Policies." CHI '26. DOI 10.1145/3772318.3791689 (arXiv
2509.19680).

- **Instruction layer: yes, but sandbox only.** The drafted policy is fed as a
  system prompt to Llama 3.3 70B so the expert designers can regenerate
  scenario responses against the current draft; a snapshot button versions the
  policy and refreshes all scenarios. Only the designers ever interact with
  the policy-informed model; there is no production deployment, and the paper
  says so: "We leave the translation of low- to high-fidelity policies to
  future work."
- **Guardrail layer: none.**
- **Evaluation layer: human-centered.** Automated heuristic flags framed as
  attention-drawing rather than conclusive, an LLM that suggests policy edits
  from expert-edited responses, and human review; no formal test suite or
  adherence metric.
- Contribution framing: explicitly the elicitation and prototyping method, not
  deployment.

## Implication for the Scenario Elicitor

Neither reference system built the guardrail or evaluation layers, and the
closer methodological analogue (PolicyPad) deliberately declined to deploy at
all. So at the proof-of-concept stage, the tool does not need an
operationalization stack to match prior work. Our per-theme test stage (the
parent's rule injected over child-safe defaults, chatted against live) already
matches PolicyPad's level of operationalization; anything beyond that
(guardrails, automated adherence scoring) would exceed both papers and should
only be built if it becomes a core contribution.

## Slack-ready summary

Checked what Botender and PolicyPad do with the elicited policy. Botender
deploys it for real: task prompts go straight into a live Discord bot's
instructions and real users interact with it (5-day field study, 6 servers),
but there is no guardrail layer and evaluation is only pre-deploy community
voting on generated provocation cases. PolicyPad operationalizes only inside
the tool: the policy is a system prompt on Llama 3.3 70B that the expert
designers test against scenarios, and the paper explicitly leaves real
deployment to future work; no guardrails there either. So neither paper built
the instruction/guardrail/evaluation stack end to end, and the one closest to
us stopped at prototyping, which supports keeping our scope at the current
test-with-the-rule stage for the proof of concept.
