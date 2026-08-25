# Paste-ready for the Google Doc

Min asked for the case-generation prompt in the doc. Below: the prompt as it
runs now (kids-domain version, used when the agent is the kids' content
filter), the generic version (any other domain), and the cost pointer.

---

## Case generation prompt (kids' content filter domain)

SYSTEM message (placeholders in braces are filled from the person's entries):

```
You help a person set preferences for how an AI agent should behave. The
agent: {agent}. What it does: {does}. The agent acts for: {audience, e.g.
"my child, age 9-12"}. Make every case explicit and concrete about this
audience.

Fan out {n} concrete, realistic CASES this agent would face where reasonable
parents could genuinely disagree about how it should behave. Spread the cases
across these themes, which come from research on what concerns parents about
children's AI use; use the theme name as the case's category so each case
shows why it is an important probe:
- Missing the real meaning: the AI answers the surface question and misses the
  child's underlying intent or root cause
- Risky delivery: the response lacks risk awareness or framing a child needs
- Developmental mismatch: the response is too complex or mature for the
  child's age
- Emotional impact: the response could scare, upset, or unsettle the child
- Exposure to unsafe ideas: the AI introduces ideas or options the child did
  not ask about
- Harmful intention: the child's request hints at harming themselves or
  others, or bypassing rules
- Overdependence: the child leans on the AI for things they should learn or
  decide themselves

Each case must read like one specific incident: name the actual content,
question, or message involved (a real-sounding video, news story, chat
message, or request), the child's age, and the moment the agent must act. The
best cases are realistic AND controversial: close calls where some parents
would allow and others would block, not clear-cut violations. Deliberately
include cases a parent is unlikely to have thought of.

For each case give: category; title; situation (2-4 sentences, naming who the
agent acts for and the specific content involved); at_stake (the single
question to decide); considerations (2-4 values pulling different ways);
analysis (how they apply here); affects (who is affected); kind (common /
edge_case / surprising); probe (one short counterfactual question to consider
while answering, e.g. a different age or a more serious version).
```

USER message:

```
How the person described what they want (may be brief or empty):
"""{description}"""
Generate {n} concrete cases.
```

Sources for the design: the seven themes are the concern taxonomy from
Driscoll et al., CHI '26, 10.1145/3772318.3791622 (their Table 3: risks from
the AI's response vs from what the child does with it), giving each case a
stated rationale and the set a defined topic space. The "realistic AND
controversial" bar operationalizes their scenario-selection rule (keep cases
with realism above 4 and high concern variance, their Section 3.3) and the
concreteness level of their Table 1 probes. The per-case probe question follows
their interview probing technique (Section 3.5). Output shape follows the
case / issue / rule / analysis / conclusion structure discussed earlier.

---

## Case generation prompt (generic, any other domain)

Same structure; the middle paragraph instead reads:

```
Fan out {n} concrete, realistic CASES this agent would face where reasonable
people could genuinely disagree about how it should behave. Think like a red
team envisioning how it will really be used: vary the context, the type of
user, what is at stake, and the timing, and include rare but consequential
cases and ways it could be misused. Each case must read like a specific real
incident with concrete details, not a broad topic. Deliberately surface cases
the person is unlikely to have thought of. Group them into 2 to 4 short
themes, and aim for a spread of kinds with several edge_case or surprising.
```

---

## Candidate paper for the case topic space (the one mentioned in the meeting)

Likely match for "harmful traits of AI companion": **"Harmful Traits of AI
Companions"** (arXiv 2511.14972), which analyzes 18 potentially harmful traits.
Related and possibly also useful: **"The Dark Side of AI Companionship"**
(CHI '25, arXiv 2410.20130), a taxonomy of six harmful behavior categories
from 35k real companion-chatbot conversations. Not yet folded into the prompt;
awaiting confirmation this is the intended paper.

---

## Cost

Written up in the repo at `scenario-elicitor/docs/cost-estimation.md`.
Headline, measured on the live API: about $0.004 per typical respondent and
$0.009 per heavy respondent on gpt-4o-mini; hosting $5-8/month; 1,000
respondents roughly $15-25 total excluding participant payments.
