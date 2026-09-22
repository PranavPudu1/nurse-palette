"""Prompt builders and strict JSON schemas for the scenario pipeline.

The pipeline elicits how a person wants an AI agent to behave. It fans out
concrete CASES (Farsight-style, at the level of a real reported case, following
the IRAC framing of case, issue, rule, analysis, conclusion) and, for each case,
has the person author the ideal behavior the agent should take. Schemas use
OpenAI Structured Outputs (strict mode).
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

FRAME_SCHEMA = {
    "name": "agent_frame",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "restated_agent": {"type": "string"},
            "does": {"type": "string"},
        },
        "required": ["restated_agent", "does"],
    },
}

SCENARIOS_SCHEMA = {
    "name": "scenarios",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "scenarios": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "category": {"type": "string"},
                        "title": {"type": "string"},
                        "situation": {"type": "string"},
                        "at_stake": {"type": "string"},
                        "considerations": {"type": "array",
                                           "items": {"type": "string"}},
                        "analysis": {"type": "string"},
                        "kind": {"type": "string",
                                 "enum": ["common", "edge_case", "surprising"]},
                        "probe": {"type": "string"},
                        # The concrete exchange that opens the scenario chat.
                        # Structure follows PolicyPad's scenario representation
                        # (Feng et al., CHI '26, §5.2.2 and Fig. 5D): a short
                        # synopsis (our `situation`) plus the actual conversation.
                        "example_exchange": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "user_message": {"type": "string"},
                                "ai_response": {"type": "string"},
                            },
                            "required": ["user_message", "ai_response"],
                        },
                    },
                    "required": ["category", "title", "situation", "at_stake",
                                 "considerations", "analysis", "kind",
                                 "probe", "example_exchange"],
                },
            },
        },
        "required": ["scenarios"],
    },
}

# One agent turn in the scenario chat, plus a one-line note on what the person's
# rule changed. Used for both the unsteered baseline reply and every rule version.
REPLY_SCHEMA = {
    "name": "agent_reply",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "response": {"type": "string"},
            "what_changed": {"type": "string"},
        },
        "required": ["response", "what_changed"],
    },
}

# The seeded rubric for a good ideal-behavior answer. Structure follows iRULER
# (Bai et al., CHI '26, DOI 10.1145/3772318.3790539): named criteria, percentage
# weights summing to 100, and 4 ordinal levels each described as observable
# evidence in parallel structure (their rubric-of-rubrics rewards exactly this).
# Criterion CONTENT is grounded in Driscoll et al., CHI '26 (10.1145/3772318.
# 3791622): action + target span (their §4.2), boundaries that avoid seeding new
# ideas (§4.2), developmental fit as a safety property (§4.2/§5.3), and deferral
# to human support with an explained reason (Table 4). Four criteria, not five:
# iRULER trimmed criteria count to reduce load (their fn.12). The rubric is a
# SEED: the person can edit names, weights, and level descriptors per session
# (iRULER DG6, refinable). See docs/design-rationale.md.
RUBRIC = [
    {
        "name": "Specific action",
        "weight": 30,
        "levels": {
            "4": "Names the exact operation the agent performs and which part of "
                 "the interaction it changes, concretely enough to act on without "
                 "interpretation.",
            "3": "Names a clear operation the agent performs, but leaves the part "
                 "of the interaction it changes implied.",
            "2": "States a general direction or value; the operation has to be "
                 "inferred.",
            "1": "States no identifiable operation; only a sentiment or a "
                 "restatement of the case.",
        },
    },
    {
        "name": "Scope and boundaries",
        "weight": 30,
        "levels": {
            "4": "States what the agent must not do, avoids introducing new ideas "
                 "or options, and names the condition under which the answer "
                 "would change.",
            "3": "States what the agent must not do, but leaves the condition "
                 "under which the answer would change unstated.",
            "2": "Implies a limit without stating what is out of bounds.",
            "1": "Sets no limit; the behavior is unbounded.",
        },
    },
    {
        "name": "Fits the audience",
        "weight": 20,
        "levels": {
            "4": "Names who the behavior is for and adjusts at least two of "
                 "content, tone, reading level, or depth to them.",
            "3": "Names who it is for and adjusts one of content, tone, reading "
                 "level, or depth.",
            "2": "References the audience without adjusting the behavior to them.",
            "1": "Ignores who the agent is acting for.",
        },
    },
    {
        "name": "Escalation and reasons",
        "weight": 20,
        "levels": {
            "4": "States when the agent should stop and hand off, names who it "
                 "hands off to, and gives the reason for the chosen behavior.",
            "3": "States a hand-off point or a reason for the behavior, but not "
                 "both.",
            "2": "Hints that some situations are beyond the agent without saying "
                 "when or to whom it defers.",
            "1": "Gives no hand-off condition and no reason.",
        },
    },
]

N_LEVELS = 4


def overall_score(rubric: list[dict], levels_by_name: dict) -> float:
    """Weighted 0-100 score, iRULER §4.1.1: sum(w_k * s_k) / L."""
    total = 0.0
    for c in rubric:
        s = levels_by_name.get(c["name"], 1)
        total += c["weight"] * int(s)
    return round(total / N_LEVELS, 1)


def rubric_as_text(rubric: list[dict]) -> str:
    lines = []
    for c in rubric:
        lines.append(f"Criterion: {c['name']} (weight {c['weight']}%)")
        for lv in ("4", "3", "2", "1"):
            lines.append(f"  Level {lv}: {c['levels'].get(lv, '')}")
    return "\n".join(lines)


# Feedback on a draft: per criterion a selected level plus Why and Why-not-higher
# explanations (iRULER's two justification types, prompt A.1.1). The probing
# question moved to the case itself (`probe`), shown while writing, per Min's
# flow feedback.
FEEDBACK_SCHEMA = {
    "name": "rubric_feedback",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "criteria": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"},
                        "level": {"type": "integer"},
                        "why": {"type": "string"},
                        "why_not_higher": {"type": "string"},
                    },
                    "required": ["name", "level", "why", "why_not_higher"],
                },
            },
        },
        "required": ["criteria"],
    },
}

# A concrete instance of a case plus two contrasting behaviors, for the confirm
# step. `dimension` records the single context variable being varied (audience
# age/maturity, severity, intent clarity, or locus of risk; Driscoll et al.).
CONFIRM_SCHEMA = {
    "name": "confirm_pairwise",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "dimension": {"type": "string"},
            "instance": {"type": "string"},
            "user_message": {"type": "string"},
            "options": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"label": {"type": "string"},
                                   "text": {"type": "string"}},
                    "required": ["label", "text"],
                },
            },
        },
        "required": ["dimension", "instance", "user_message", "options"],
    },
}


# ---------------------------------------------------------------------------
# Message builders
# ---------------------------------------------------------------------------

def frame_agent_messages(agent: str) -> list[dict]:
    system = (
        "A person wants to set preferences for how an AI agent should behave on "
        "their behalf. Given what they typed, restate the agent cleanly and describe "
        "in one plain sentence what this agent does for them. Do not use em dashes."
    )
    user = f"Agent the person typed:\n\"\"\"\n{agent.strip()}\n\"\"\""
    return [{"role": "system", "content": system},
            {"role": "user", "content": user}]


def _audience_clause(audience: str) -> str:
    a = (audience or "").strip()
    return (f" The agent acts for: {a}. Make every case explicit and concrete about "
            f"this audience." if a else "")


# The concrete-case field spec, shared by the three case generators. The bar is
# a specific, real-feeling case (who it is for, a concrete example), not a topic.
_CASE_FIELDS = (
    "Make each case concrete and specific, at the level of a real reported case, "
    "not a category. For each case give:\n"
    "- category: the short theme it belongs to\n"
    "- title: a short handle for the case\n"
    "- situation: the concrete case in two to four sentences. Name who the agent "
    "is acting for, and include a specific, realistic example of the actual "
    "content, request, or event involved (for instance a concrete news item, "
    "message, or question), not a general description.\n"
    "- at_stake: what could actually go wrong for this specific child if the "
    "agent handles this badly, plus the judgement call that has to be made. Name "
    "the concrete consequence, not the abstract topic. If a child asks how to "
    "help a classmate who is being bullied, 'she steps in and becomes a target "
    "herself' is what is at stake; 'how much to tell her' is not enough.\n"
    "- considerations: an array of 2 to 4 short principles or values that pull in "
    "different directions here\n"
    "- analysis: one or two sentences on how those considerations apply to this "
    "specific case\n"
    "- kind: 'common' for an everyday case, 'edge_case' for a tricky boundary case, "
    "or 'surprising' for one the person is unlikely to have considered\n"
    "- probe: one short counterfactual question that pushes the person to consider "
    "a variation of this case while they answer (a different age or audience, a "
    "more serious version, or an unclear intent), in the style of an interview "
    "probing question\n"
    "- example_exchange: the concrete moment itself, as one exchange. "
    "'user_message' is exactly what the child would type or ask, in their own "
    "words at their age. 'ai_response' is what a mainstream assistant in its "
    "child-appropriate mode would really reply today. Write it at realistic "
    "length and in a realistic voice: real products answer at some length, warmer "
    "and more padded than strictly necessary, often with a follow-up question or "
    "a short list. Apply only the ordinary default safeguards such a product "
    "ships with, and nothing beyond them. The reply may legitimately answer "
    "plainly and let the content through; do not make it extra cautious just "
    "because a parent is watching.\n"
)

# What a mainstream assistant's child-appropriate mode does by default, before
# this parent has said anything. Reconstructed from behaviour these products
# publicly document, not copied from any vendor's system prompt: it exists so the
# "before" in every before/after comparison is a realistic starting point rather
# than a bare model completion. See provenance.py['baseline_reply'].
CHILD_SAFE_DEFAULTS = (
    "You are in the child-appropriate mode such assistants ship with. Its "
    "defaults, and nothing stricter:\n"
    "- vocabulary and framing suited to the child's age\n"
    "- on anything serious, suggest bringing in a parent or another trusted "
    "adult, without refusing to engage\n"
    "- describe difficult events without graphic or gratuitous detail\n"
    "- if self-harm or suicide comes up, respond with care and NAME a specific "
    "way to get help, such as a crisis line the child could contact. A general "
    "suggestion to talk to someone is not enough on its own\n"
    "- no medical, legal, or financial advice beyond general information\n"
    "These are only the product defaults. Do not invent extra restrictions, and "
    "do not become more cautious because a parent might be reading."
)

# Constraints on what counts as a useful case. Adapted from Botender's
# case-generation prompts (Kuo et al., CHI '26, Appendix A.2.1-A.2.4), which
# require cases to be self-evident at the surface, non-trivial, within the
# system's real capabilities, and non-redundant as a set. Reworded for this
# domain; see docs/provenance.md.
_CASE_QUALITY = (
    "Quality bar for the set of cases:\n"
    "- Self-evident: each case must be understandable from its own text. A reader "
    "should see the difficulty without any extra explanation.\n"
    "- Not already settled: only include a case whose right answer is NOT already "
    "determined by what the person has told you they want. If their stated wishes "
    "clearly decide it, the case teaches nothing and should be dropped.\n"
    "- Non-trivial: no cases that turn on wording or tone alone, and none that are "
    "obvious violations everyone would answer the same way.\n"
    "- Actionable: the agent can only allow content through, soften or summarize it, "
    "add context or a warning, decline and explain, or bring the parent in. Do not "
    "write cases that need abilities beyond these.\n"
    "- Varied: cases should differ from each other in setting, content, and who is "
    "involved. An even split across themes is not required; weight the themes that "
    "matter most for this agent.\n"
)


# Default agent for the study's fixed domain (kids' content filter for parents).
KIDS_AGENT = "An AI that curates news and content for my child"

# Kids-domain topic space: the concern taxonomy Driscoll et al. (CHI '26,
# 10.1145/3772318.3791622) coded from interviews with 24 parents, reproduced
# from their Table 3. Their two axial themes split the concerns by SOURCE: the
# first five are about the chatbot's response, the last three about the child's
# own prompt. `raised_by` is the paper's count of unique parents who raised that
# theme, out of 24.
#
# Three texts per theme, because they have three different readers. `name` is
# the paper's own label, kept verbatim so any claim we make stays traceable to
# Table 3. `desc` is written for the model and states the failure mode. `blurb`
# is written for the participant and must stand alone: nobody reaching this
# screen has read the paper, and a label like "Wrong Approach to Delivery" tells
# them nothing on its own. Every blurb is derived from that theme's initial
# codes and parent quotes in Table 3 rather than paraphrased from the title.
#
# Each theme carries two texts. 'desc' is written for the model and states the
# failure mode in the paper's terms. 'blurb' is written for the participant and
# has to stand on its own: nobody reaching this screen has read Driscoll, and a
# bare theme name like "Risky delivery" tells them nothing about what to write a
# rule for. The blurb is what the theme menu and the workspace header show.
KIDS_THEMES = [
    # --- Questionable response from the chatbot -------------------------------
    {"name": "Missing Underlying Meaning", "raised_by": 13,
     "example": 'Your child asks how to get around a blocked site, and the reply talks about the rule instead of asking why they want in.',
     "desc": "the AI answers the surface question and misses the child's "
             "underlying intent or root cause",
     "blurb": "The AI takes the question at face value and answers it, without "
              "working out why your child is asking. One parent described a "
              "reply that focused on the rule-breaking rather than the root "
              "issue, which was that their child wanted into a blocked site."},
    {"name": "Wrong Approach to Delivery", "raised_by": 10,
     "example": 'Asked about a risky stunt from a video, the reply explains it step by step with no word of caution.',
     "desc": "the response is delivered without the risk awareness, usefulness "
             "or structure the moment called for",
     "blurb": "The answer arrives without the care the moment needed. Usually "
              "that meant a reply showing no awareness of how much harm the "
              "subject could do; sometimes an answer that was accurate but of "
              "no practical use, or too disorganised to act on."},
    {"name": "Developmental Mismatch", "raised_by": 8,
     "example": 'A 7-year-old asks why the sky is blue and gets a paragraph about wavelengths and scattering.',
     "desc": "the response is too complex or mature for the child's age, or "
             "contradicts itself",
     "blurb": "The answer is pitched above your child. Parents described replies "
              "using terms their child could not follow, so the child came away "
              "without the main point even though the information was right."},
    {"name": "Emotional Impact", "raised_by": 7,
     "example": 'Asked whether pets die, the reply is accurate about death and leaves your child upset at bedtime.',
     "desc": "the response could scare, upset, or unsettle the child",
     "blurb": "The answer is true but it sits badly with your child afterwards. "
              "One parent said their child would walk away not feeling good even "
              "without fully understanding the words. Another asked why a model "
              "should say something that would be harmful from a person."},
    {"name": "Exposure to Unsafe Ideas", "raised_by": 5,
     "example": 'Asked about kitchen safety, the reply lists exactly which experiments never to try at home.',
     "desc": "the AI introduces concerning ideas or options the child did not "
             "ask about",
     "blurb": "The answer volunteers something your child never asked about and "
              "would not have thought of. Parents called this planting an idea: "
              "a reply suggesting they try something at home hands the child "
              "their next question."},
    # --- Questionable prompt from the child -----------------------------------
    {"name": "Potentially Harmful Intention", "raised_by": 20,
     "example": 'Your child asks how to make someone at school regret being mean to them.',
     "desc": "the child's request hints at harming themselves or others, or at "
             "bypassing rules",
     "blurb": "The question itself is the worry, whatever the AI answers back. "
              "Parents flagged prompts that looked like a way to hurt or "
              "humiliate someone, or to get around a rule, and wanted to know "
              "what their child was thinking. This worried the most parents of "
              "any concern in the study."},
    {"name": "Overdependence", "raised_by": 5,
     "example": 'Your child asks the AI to decide which friend to invite instead of working it out themselves.',
     "desc": "the child leans on the AI for things they should learn or decide "
             "themselves",
     "blurb": "Your child hands the AI something they should be working out or "
              "deciding themselves. Parents also worried about children acting "
              "on what the AI suggested, one noting their child might wait until "
              "they were out of the house to try it."},
    {"name": "Skepticism of Technical Safeguards", "raised_by": 5,
     "example": "Refused once, your child retypes it as 'it's for a school project' and gets the answer.",
     "desc": "the child can rephrase a blocked request until the AI answers it",
     "blurb": "Whatever the AI refuses, your child can ask again in different "
              "words. Parents doubted the built-in limits would hold, noting "
              "that children will reword a prompt to get the result they wanted "
              "the first time."},
]

THEME_NAMES = [t["name"] for t in KIDS_THEMES]


def theme_by_name(name: str) -> dict | None:
    return next((t for t in KIDS_THEMES if t["name"] == (name or "").strip()), None)


def is_kids_domain(agent: str) -> bool:
    a = (agent or "").lower()
    return any(k in a for k in ("child", "kid", " son", "daughter", "parent"))




def expand_theme_messages(agent: str, does: str, description: str, audience: str,
                          theme: str, existing_titles: list[str],
                          n: int) -> list[dict]:
    avoid = "; ".join(t for t in existing_titles if t) or "(none yet)"
    system = (
        f"You help a person set preferences for how an AI agent should behave. The "
        f"agent: {agent.strip()}. What it does: {does.strip()}."
        f"{_audience_clause(audience)}\n\n"
        f"Fan out {n} MORE concrete cases that belong to one theme: "
        f"'{theme.strip()}'. Push into the less obvious corners of this theme: rare "
        "but consequential cases, edge cases, and ways the agent could be misused, "
        "so the person sees cases they have not considered. Each must be a specific, "
        f"concrete incident. Use '{theme.strip()}' as the category and prefer kind "
        f"edge_case or surprising.\n\n{_CASE_FIELDS}\n{_CASE_QUALITY}\nDo not use em dashes."
    )
    user = (
        "How the person described what they want (may be brief or empty):\n"
        f"\"\"\"\n{(description or '').strip()}\n\"\"\"\n\n"
        f"Do not repeat any of these existing cases: {avoid}.\n"
        f"Generate {n} more concrete cases in the theme '{theme.strip()}'."
    )
    return [{"role": "system", "content": system},
            {"role": "user", "content": user}]






def _reflection_text(reflection: list[dict] | None) -> str:
    """What the person said when prompted to think it through, for the prompts
    that judge or revise their draft. Without this, Check and Suggest see only
    the final sentence and none of the reasoning behind it."""
    rows = []
    for r in (reflection or []):
        q, a = (r.get("question") or "").strip(), (r.get("answer") or "").strip()
        if a:
            rows.append(f"- Asked: {q}\n  They said: {a}")
    return "\n".join(rows)


def rubric_feedback_messages(agent: str, does: str, description: str, audience: str,
                             scenario: dict, draft: str,
                             rubric: list[dict],
                             reflection: list[dict] | None = None) -> list[dict]:
    # Instruction shape follows iRULER prompt A.1.1: strict per-criterion level
    # selection, moderate evaluation, Why with concrete examples, Why-not for the
    # next level up, Overall-Supporting structure.
    system = (
        f"You are an expert evaluator helping a person specify how an AI agent "
        f"({agent.strip()}: {does.strip()}) should behave in a specific case."
        f"{_audience_clause(audience)}\n\n"
        "Evaluate their draft answer against this rubric. Each criterion has levels "
        "4 (best) to 1:\n\n"
        f"{rubric_as_text(rubric)}\n\n"
        "Instructions:\n"
        "1. For each criterion, rigorously match the draft against the level "
        "descriptors and select the single level that best matches. Judge only the "
        "draft; do not rewrite it.\n"
        "2. Adopt a moderate evaluation approach: recognize strengths, avoid overly "
        "harsh penalties for minor issues, and focus on overall alignment with the "
        "descriptors.\n"
        "3. For each criterion give 'why': a justification of the selected level. "
        "Use an Overall-Supporting structure: one concise overall sentence, then "
        "2 or 3 short bullet points citing concrete phrases from the draft. Write "
        "it as Markdown with '-' bullets.\n"
        "4. For each criterion give 'why_not_higher': what the draft would need to "
        "reach the next level up, in the same Overall-Supporting structure, citing "
        "the next level's descriptor language. If the selected level is 4, return "
        "an empty string.\n"
        "Reuse the exact criterion names. Do not use em dashes.\n\n"
        "HARD RULE ABOUT THE CONTEXT SECTION. The person may have been asked to "
        "think the case through before writing, and their answers appear under "
        "CONTEXT. That is NOT part of their draft. The level you assign to every "
        "criterion must be justified by the words of the draft ALONE. If the "
        "draft does not say it, it is not there, however clearly they said it in "
        "the context. Never let the context raise a level. Use it for exactly "
        "one thing: in 'why_not_higher', to point out that they evidently care "
        "about something and have not put it in the rule yet."
    )
    cons = ", ".join(scenario.get("considerations") or [])
    user = (
        f"Case ({scenario.get('title', '')}):\n{scenario.get('situation', '')}\n"
        f"What has to be decided: {scenario.get('at_stake', '')}\n"
        f"Things to weigh: {cons}\n\n"
    )
    said = _reflection_text(reflection)
    if said:
        user += ("\n\nCONTEXT, NOT PART OF THE DRAFT. Before writing, they were "
                 f"asked to think the case through and said:\n{said}\n"
                 "Nothing above is in their rule. Do not score it.")
    user += ("\n\nTHE DRAFT TO SCORE, and the only thing you may score:\n"
             f"\"\"\"\n{(draft or '').strip() or '(empty)'}\n\"\"\"")
    return [{"role": "system", "content": system},
            {"role": "user", "content": user}]


# ---------------------------------------------------------------------------
# Reflective questions (Paul and Elder taxonomy)
# ---------------------------------------------------------------------------
# The five Socratic question types from research12.pdf (Ang, Gollapalli, Ng,
# EACL 2023, Table 1), which reproduces the Paul and Elder taxonomy. Their
# catch-all "Others" type is dropped. Socratic questions do not seek a correct
# answer; they provoke introspection and challenge the completeness of a thought.
#
# Ported from the preference-elicitor app, where the same taxonomy drives the
# research-based reflect tab. Two placements here: before the person writes
# anything (grounded in the situation) and after their first Check (grounded in
# what they actually wrote).

SOCRATIC_TYPES = [
    {"key": "clarification", "name": "Clarification",
     "description": "Probe the ambiguities of a thought.",
     "exemplar": "What do you mean by ...?"},
    {"key": "assumptions", "name": "Probing assumptions",
     "description": "Probe the assumptions behind a thought.",
     "exemplar": "Why do you assume ...?"},
    {"key": "reasons", "name": "Probing reasons and evidence",
     "description": "Probe the justifications or evidence behind a thought.",
     "exemplar": "How did you know that ...?"},
    {"key": "implications", "name": "Probing implications and consequences",
     "description": "Probe the impacts or implications of a thought.",
     "exemplar": "If ..., what is likely to happen as a result?"},
    {"key": "viewpoints", "name": "Probing alternative viewpoints",
     "description": "Probe other possible viewpoints.",
     "exemplar": "What else should we consider ...?"},
]

_SOCRATIC_KEYS = [t["key"] for t in SOCRATIC_TYPES]

# How many questions each placement asks. Kept small: five before writing is a
# wall of text in front of an empty box.
N_REFLECT_BEFORE = 2
N_REFLECT_AFTER = 3

REFLECT_SCHEMA = {
    "name": "reflective_questions",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "type": {"type": "string", "enum": _SOCRATIC_KEYS},
                        "question": {"type": "string"},
                    },
                    "required": ["type", "question"],
                },
            },
        },
        "required": ["questions"],
    },
}


def _socratic_catalog() -> str:
    return "\n".join(
        f"- {t['key']}: {t['name']}. {t['description']} Example: {t['exemplar']}"
        for t in SOCRATIC_TYPES)


def _socratic_preamble() -> str:
    return (
        "Generate Socratic questions in the Paul and Elder taxonomy. Socratic "
        "questions do NOT seek a correct answer; they provoke introspection and "
        "challenge the completeness and accuracy of a thought.\n\n"
        "The five question types (type_key: meaning, example):\n"
        f"{_socratic_catalog()}\n\n")


def reflect_before_messages(agent: str, does: str, audience: str,
                            scenario: dict, n: int = N_REFLECT_BEFORE) -> list[dict]:
    """Questions shown above the writing box, before anything is written.

    The person has not stated a thought yet, so these probe the situation and
    what they are about to bring to it, rather than critiquing a draft.

    The hard rule below exists because of a real failure: a question asked why
    the parent assumed standing up for a bullied classmate was the right thing,
    when nothing the parent had written said that. The AI's own case had
    introduced it. Attributing a position to someone who has not taken one reads
    as being put on the defensive, and it corrupts what they write next.
    """
    system = (
        f"A person is about to write how an AI agent ({agent.strip()}: "
        f"{does.strip()}) should behave in the situation below."
        f"{_audience_clause(audience)}\n\n"
        + _socratic_preamble() +
        f"Write exactly {n} questions, of DIFFERENT types, that make this person "
        "examine what they are bringing to this situation before they answer: "
        "what they are taking for granted, what could follow for their child, "
        "where they would draw a line. Ground every question in the "
        "specifics of this situation. Ask short, plain questions. Use the exact "
        "type keys. Do not use em dashes.\n\n"
        "Make every question concrete for a child of exactly this age and "
        "answerable without interpretation. Never ask what the child's or "
        "anyone's 'perspectives' might be in the abstract, and never ask "
        "hypotheticals about the child being a different age. Prefer "
        "questions about what the parent is assuming, what could follow, "
        "and where they would draw a line. If a question could be unclear, "
        "include a brief example inside it, like 'for example, ...'.\n\n"
        "HARD RULE. This person has not written a single word yet, so you know "
        "nothing about what they think. Never state or imply that they believe, "
        "assume, want, or prefer anything. Phrasings like 'why do you assume', "
        "'what makes you think', 'you seem to want' are forbidden, because "
        "whatever they name came from the case, not from them. Ask about the "
        "situation and about what they would want, in the conditional. 'Where "
        "would you want the line to be?' is right. 'Why do you think that is "
        "right?' is wrong."
    )
    # at_stake and considerations are given as material here rather than shown on
    # the case card. Rendered as prose they told the parent what to think before
    # they had thought it; turned into questions they do the opposite.
    weigh = "; ".join(scenario.get("considerations") or [])
    user = (f"Situation: {scenario.get('situation', '')}\n"
            f"What could go wrong here: {scenario.get('at_stake', '')}\n"
            f"Values that pull in different directions: {weigh}")
    return [{"role": "system", "content": system},
            {"role": "user", "content": user}]


N_REFLECT_INTAKE = 2


def reflect_intake_messages(agent: str, does: str, audience: str,
                            n: int = N_REFLECT_INTAKE) -> list[dict]:
    """Questions asked at setup, before any case has been seen.

    Min: "it might be even before they see the specific case... maybe add a few
    more questions when you ask about name and tell me about your kid." Every
    other question in the tool is anchored to a concrete situation, which means
    the first thing a participant thinks about is whatever case we generated.
    These come first and are about the child and the parent's own position, so
    what they bring is theirs rather than a reaction to our material.

    Same five question types and the same schema as the rest; only the subject
    changes, from a case to the person and their child.
    """
    system = (
        f"A person is about to set out how an AI agent ({agent.strip()}: "
        f"{does.strip()}) should behave for someone they are responsible for."
        f"{_audience_clause(audience)}\n\n"
        + _socratic_preamble() +
        f"Write exactly {n} questions, of DIFFERENT types, about this person's "
        "own position before they have seen any specific situation: what they "
        "are taking for granted about what this AI can and cannot do, how much "
        "they want to decide themselves rather than leave to it, and where "
        "they would want lines drawn. Ask short, plain questions. Use the "
        "exact type keys. Do not use em dashes.\n\n"
        "Make every question concrete for a child of exactly this age and "
        "answerable without interpretation. Never ask what the child's or "
        "anyone's 'perspectives' might be in the abstract, and never ask "
        "hypotheticals about the child being a different age. Prefer "
        "questions about what the parent is assuming, what could follow, "
        "and where they would draw a line. If a question could be unclear, "
        "include a brief example inside it, like 'for example, ...'.\n\n"
        "HARD RULE. This person has written nothing yet, so you know nothing "
        "about what they think. Never state or imply that they believe, assume, "
        "want or prefer anything. Ask in the conditional, about what they would "
        "want."
    )
    user = f"The agent acts for: {(audience or 'someone they are responsible for').strip()}."
    return [{"role": "system", "content": system},
            {"role": "user", "content": user}]


def reflect_after_messages(agent: str, does: str, audience: str, scenario: dict,
                           draft: str, n: int = N_REFLECT_AFTER) -> list[dict]:
    """Questions shown after the first Check, grounded in what they wrote.

    Distinct from the rubric: the rubric judges whether the rule is specific
    enough to act on, these ask why the person wants what they wrote.
    """
    system = (
        f"A person has written how an AI agent ({agent.strip()}: {does.strip()}) "
        f"should behave in the situation below.{_audience_clause(audience)}\n\n"
        + _socratic_preamble() +
        "FIRST, judge whether what they wrote is a real attempt at a rule. "
        "If it is empty, a refusal (like 'skip' or 'idk'), keyboard "
        "gibberish, copied filler, or otherwise not about how the AI should "
        "behave, you MUST NOT write grounded questions about it and MUST NOT "
        "invent positions they never took. In that case return exactly ONE "
        "question, of type clarification, that says plainly and kindly that "
        "they have not written a rule yet and asks what they would want the "
        "AI to do in this situation. Nothing else.\n\n"
        f"Otherwise, write up to {n} questions, of DIFFERENT types, grounded "
        "in THEIR OWN WORDING. Quote or name the specific phrase each "
        "question is about. Only write as many questions as the text really "
        f"supports: {n} when it is substantial, fewer when it is thin. Do "
        "not evaluate the answer and do not suggest a rewrite; a separate "
        "rubric does that. Ask only what makes them examine their own "
        "reasoning. Ask short, plain questions. Use the exact type keys. Do "
        "not use em dashes."
    )
    user = (f"Situation: {scenario.get('situation', '')}\n"
            f"What has to be decided: {scenario.get('at_stake', '')}\n\n"
            f"What they wrote:\n\"\"\"\n{(draft or '').strip()}\n\"\"\"")
    return [{"role": "system", "content": system},
            {"role": "user", "content": user}]


# ---------------------------------------------------------------------------
# The policy: written once from what the person has already done, then sharpened
# ---------------------------------------------------------------------------
# There is ONE policy for the whole session. It is first written from the rules
# the person authored per case plus their round-1 picks and reasons, then
# sharpened by their critiques in round 2. It is never rewritten from scratch.
#
# Length is tied to how much the person themselves wrote rather than being a
# fixed number, so the policy cannot win a comparison simply by saying more.

POLICY_MIN_PRINCIPLES = 3
POLICY_MAX_PRINCIPLES = 8




POLICY_PICK_SCHEMA = {
    "name": "policy_pick",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "choice": {"type": "string", "enum": ["A", "B"]},
            "reason": {"type": "string"},
        },
        "required": ["choice", "reason"],
    },
}


def _policy_lines(policy: dict | None) -> str:
    """Render the policy for a prompt.

    Deliberately NOT numbered. When these were sent as "1. ...", the model
    echoed the numbering back inside the principle text, so every revision
    accumulated another "1. " prefix.
    """
    items = (policy or {}).get("principles") or []
    return "\n".join(f"- {p}" for p in items) or "(none yet)"


def _answer_lines(answers: list[dict]) -> str:
    out = []
    for a in answers:
        out.append(f"- Situation: {a.get('situation', '')}\n"
                   f"  They wrote: {a.get('ideal_behavior', '')}")
        why = (a.get("why") or "").strip()
        if why:
            out.append(f"  What mattered most: {why}")
        for r in (a.get("reflection") or []):
            out.append(f"  Q ({r.get('type', '')}): {r.get('question', '')}\n"
                       f"  A: {r.get('answer', '')}")
    return "\n".join(out) or "(none)"


def _pick_lines(picks: list[dict]) -> str:
    out = []
    for p in picks:
        opts = {"A": p.get("option_a", {}), "B": p.get("option_b", {})}
        ch = p.get("choice", "")
        chosen = opts.get(ch, {})
        other = opts.get("B" if ch == "A" else "A", {})
        if ch not in ("A", "B"):
            continue
        out.append(f"- Situation: {p.get('instance', '')}\n"
                   f"  They preferred: {chosen.get('text', '')}\n"
                   f"  Over: {other.get('text', '')}\n"
                   f"  Their reason: {(p.get('note') or '(none given)')}")
    return "\n".join(out) or "(none)"




def policy_pick_messages(agent: str, does: str, audience: str, policy: dict,
                         instance: str, option_a: dict,
                         option_b: dict) -> list[dict]:
    """Make the agent choose between two responses using ONLY the policy."""
    system = (
        f"You are {agent.strip()}: {does.strip()}.{_audience_clause(audience)}\n\n"
        "Below is the policy the parent has written for you. Choose which of the "
        "two responses better follows THAT POLICY. Judge only by the policy, not "
        "by your own preferences about what is best.\n\n"
        "Return 'choice' as 'A' or 'B', and 'reason' as one or two sentences "
        "naming WHICH PART of the policy drove the decision. Quote the principle "
        "you relied on. Do not use em dashes."
    )
    user = (f"The policy:\n{_policy_lines(policy)}\n\n"
            f"Situation: {instance}\n"
            f"Option A: {option_a.get('text', '')}\n"
            f"Option B: {option_b.get('text', '')}")
    return [{"role": "system", "content": system},
            {"role": "user", "content": user}]


# The four context variables along which preferences shift. Three are named
# directly in Driscoll et al. §7 Future Work: "interpretable models that can
# detect moderation-relevant factors ... (such as intent clarity, risk level,
# developmental cues, and when handover is needed)" -> clarity of intent,
# severity of the situation, audience age or maturity. The fourth, source of
# risk, is their Table 14 axial coding (System Risk, harm from how the model
# responds, vs Misuse Risk, harm from what the child does with the output).
# Same §7 sentence also calls for "scenario-based tools that measure these
# factors at scale", which is what this step is. See docs/provenance.md.
CONFIRM_DIMENSIONS = ("audience age or maturity", "severity of the situation",
                      "clarity of intent", "source of risk")


def confirm_pairwise_messages(agent: str, does: str, description: str, audience: str,
                              scenario: dict, ideal_behavior: str,
                              avoid: list[str] | None = None,
                              edge: bool = False,
                              avoid_questions: list[str] | None = None,
                              gaps: list[str] | None = None) -> list[dict]:
    dims = "; ".join(CONFIRM_DIMENSIONS)
    # Later rounds reuse the same situations, so ask for a dimension that has
    # not been used yet; otherwise the person answers the same question twice.
    seen = [d for d in (avoid or []) if d]
    extra = ""
    if seen:
        extra += (" Do NOT vary any of these, they have been used already: "
                  + "; ".join(sorted(set(seen))) + ".")
    prev_q = [q.strip() for q in (avoid_questions or []) if q.strip()]
    if prev_q:
        extra += (" The child already asked these in earlier close calls: "
                  + " | ".join(prev_q[-6:]) +
                  ". Write a DIFFERENT message this time, a fresh way the "
                  "same situation could come up, never a rewording of one "
                  "of those.")
    if gaps:
        extra += (" The person's rule is currently weakest on: "
                  + "; ".join(gaps) +
                  ". Give modest extra weight to moments that would reveal "
                  "how the rule handles those gaps, but do not force every "
                  "close call onto them.")
    if edge:
        extra += (" Push this one further out than an everyday case: pick a "
                  "genuinely hard edge where the person's stated behavior is "
                  "least likely to give a clear answer.")
    system = (
        f"An AI agent ({agent.strip()}: {does.strip()}) is in the case below, and the "
        f"person has authored the ideal behavior they want.{_audience_clause(audience)} "
        "To test the boundary of that preference, first pick the ONE dimension along "
        f"which their stated behavior is most likely to flip: {dims}. Then invent one "
        "concrete instance of this case positioned near that boundary: specific and "
        "named (a real-sounding item, message, or event), near yes-or-no, and more "
        "concrete than the case itself. Then write TWO contrasting ways the agent "
        "could behave in that instance that differ only along the chosen dimension's "
        "boundary, not obviously better or worse, so the person's pick reveals their "
        "limit. Do not introduce new ideas or options beyond the instance itself. "
        "Write 'user_message': exactly what the child types or says in that "
        "moment, in their own words at their age. Both options must read as two "
        "possible REPLIES to that same message, so the person is choosing "
        "between two things the agent could actually say back. "
        "Each option: a short label and one or two sentences of what the agent says. "
        "Return the chosen dimension as 'dimension'. Do not use em dashes."
        + extra
    )
    user = (
        f"Case: {scenario.get('situation', '')}\n"
        f"What has to be decided: {scenario.get('at_stake', '')}\n"
        f"The person's ideal behavior: {(ideal_behavior or '').strip()}"
    )
    return [{"role": "system", "content": system},
            {"role": "user", "content": user}]


# The scenario chat: the agent answers the child inside the case, either with no
# special instructions (the baseline turn) or steered by the parent's authored
# rule. Delivering the rule as a system prompt with scaffolding follows PolicyPad
# (Feng et al., CHI '26, §5.3: "The policy was fed into the model as a system
# prompt with some additional scaffolding to ensure the model followed it"); the
# explicit precedence line is modeled on their open-source scaffold
# (github.com/kjfeng/policypad, src/lib/backend-utils.ts), reworded here. See
# docs/provenance.md.

def agent_reply_messages(agent: str, does: str, audience: str, scenario: dict,
                         behavior: str | None, history: list[dict]) -> list[dict]:
    """One agent turn. behavior=None gives the unsteered baseline reply."""
    who = (audience or "the person it serves").strip()
    # No length instruction here, deliberately. An earlier version capped every
    # reply at two to four sentences, which made the "before" in every comparison
    # read as suspiciously terse next to a real product and made the baseline
    # unrepresentative of what these systems actually say. Length now varies for
    # the same reason it varies in a real product, and any difference the parent
    # sees between before and after comes from their rule rather than from us.
    base = (
        f"You are {agent.strip()}: {does.strip()}. You are replying directly to "
        f"{who} in a live conversation. Answer at the length a real assistant "
        "would use for this question, in the voice the agent would actually use. "
        "Do not narrate what you are doing, do not mention rules or instructions, "
        "and do not use em dashes."
    )
    if (behavior or "").strip():
        rule = (behavior or "").strip()
        system = (
            f"{base}\n\n{CHILD_SAFE_DEFAULTS}\n\n"
            "On top of those defaults, follow these instructions from the parent "
            f"who set you up:\n{rule}\n\n"
            "Where the parent's instructions and the defaults disagree, the "
            "parent's instructions win.\n\n"
            "Also return 'what_changed': one short line naming what you did "
            "differently because of those instructions, compared with how you would "
            "have answered without them."
        )
    else:
        system = (
            f"{base}\n\n{CHILD_SAFE_DEFAULTS}\n\n"
            "This parent has not given you any instructions of their own yet. "
            "Answer the way the product would out of the box.\n\n"
            "Return 'what_changed' as an empty string."
        )
    lines = [f"Context: {scenario.get('situation', '')}"]
    for t in history:
        role = "Child" if t.get("role") == "user" else "You"
        lines.append(f"{role}: {t.get('content', '')}")
    lines.append("Reply to the last message.")
    return [{"role": "system", "content": system},
            {"role": "user", "content": "\n".join(lines)}]
