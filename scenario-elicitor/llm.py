"""OpenAI integration for the scenario pipeline.

Plumbing (key discovery, cached client, strict-JSON chat, mock fallback) copied
from the preference-elicitor app. Every public function degrades to a
deterministic offline mock when there is no API key, and never raises: on a live
error it falls back to the mock and attaches an ``_error`` string.
"""
from __future__ import annotations
import hashlib
import json
import re
import os
import random
from pathlib import Path

import streamlit as st

import prompts

MODEL = "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Key discovery: st.secrets, env, then repo-root .env.local
# ---------------------------------------------------------------------------

def _parse_env_file(path: Path) -> dict:
    out = {}
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            out[key.strip()] = val.strip().strip('"').strip("'")
    except OSError:
        pass
    return out


def _env_local() -> dict:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / ".env.local"
        if candidate.exists():
            return _parse_env_file(candidate)
    return {}


_KEY_NAMES = ("OPENAI_API_KEY", "OPENAI_KEY", "openai")


def _api_key() -> str | None:
    try:
        for name in _KEY_NAMES:
            if name in st.secrets:
                return str(st.secrets[name])
    except Exception:
        pass
    for name in _KEY_NAMES:
        if os.environ.get(name):
            return os.environ[name]
    env = _env_local()
    for name in _KEY_NAMES:
        if env.get(name):
            return env[name]
    return None


def is_configured() -> bool:
    return bool(_api_key())


@st.cache_resource(show_spinner=False)
def _client():
    from openai import OpenAI
    return OpenAI(api_key=_api_key())


def _chat_json(messages: list[dict], schema: dict, temperature: float = 0.5) -> dict:
    resp = _client().chat.completions.create(
        model=MODEL, messages=messages,
        response_format={"type": "json_schema", "json_schema": schema},
        temperature=temperature)
    return json.loads(resp.choices[0].message.content)


def _call(messages: list[dict], schema: dict, mock: dict,
          temperature: float = 0.5) -> dict:
    if not is_configured():
        return {**mock, "_mock": True}
    try:
        data = _chat_json(messages, schema, temperature)
        data["_mock"] = False
        return data
    except Exception as exc:  # noqa: BLE001, never break the flow
        return {**mock, "_mock": True, "_error": str(exc)}


def _slug(text: str, fallback: str = "item") -> str:
    keep = [c.lower() if c.isalnum() else "_" for c in (text or "").strip()]
    slug = "".join(keep).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    slug = "_".join(slug.split("_")[:4])
    return slug or fallback


def _rand(*parts: str) -> random.Random:
    seed = int(hashlib.md5("|".join(parts).encode()).hexdigest()[:8], 16)
    return random.Random(seed)


# ---------------------------------------------------------------------------
# Public pipeline functions
# ---------------------------------------------------------------------------

def frame_agent(agent: str) -> dict:
    a = agent.strip() or "an AI agent"
    mock = {"restated_agent": a, "does": f"acts on your behalf for {a}."}
    return _call(prompts.frame_agent_messages(agent), prompts.FRAME_SCHEMA, mock)


def _mock_case(theme: str, does: str, audience: str, i: int) -> dict:
    """One deterministic placeholder CONCRETE case with all IRAC fields.

    Keyed on ``i`` so distinct calls stay distinct (the dedupe-append relies on
    it; real model output varies naturally)."""
    kind = ["common", "edge_case", "surprising"][i % 3]
    who = (audience or "the people it serves").strip()
    return {
        "category": theme,
        "title": f"Case {i + 1}: {theme}",
        "situation": (f"While it {does.strip() or 'acts for you'}, the agent handles "
                      f"a specific request from {who} that falls under {theme} "
                      f"(placeholder example #{i + 1})."),
        "at_stake": "whether the agent should act on its own or check first",
        "considerations": ["being helpful", "being careful",
                           "respecting the person's wishes"],
        "analysis": ("These pull in different directions for this particular request "
                     "(placeholder)."),
        "kind": kind,
        "probe": "How would your answer change if the same request came from "
                 "someone older, or in a more serious form?",
        "example_exchange": {
            "user_message": f"Placeholder question #{i + 1} that {who} would ask "
                            f"in this situation.",
            "ai_response": "A plain, helpful placeholder answer with no special "
                           "instructions applied.",
        },
    }


def generate_scenarios(agent: str, does: str, description: str, audience: str,
                       n: int = 6) -> dict:
    themes = ["everyday requests", "tricky edge cases", "conflicts and limits"]
    scenarios = [_mock_case(themes[i % len(themes)], does, audience, i)
                 for i in range(n)]
    mock = {"scenarios": scenarios}
    return _call(prompts.scenarios_messages(agent, does, description, audience, n),
                 prompts.SCENARIOS_SCHEMA, mock, temperature=0.7)


def expand_theme(agent: str, does: str, description: str, audience: str, theme: str,
                 existing_titles: list[str], n: int = 3) -> dict:
    base = len(existing_titles)
    scenarios = []
    for j in range(n):
        # Offset well past the base generation's indices so the mock stays unique.
        s = _mock_case(theme, does, audience, 100 + base + j)
        s["kind"] = ["edge_case", "surprising"][j % 2]
        s["title"] = f"{theme} case {base + j + 1}"
        scenarios.append(s)
    mock = {"scenarios": scenarios}
    return _call(
        prompts.expand_theme_messages(agent, does, description, audience, theme,
                                      existing_titles, n),
        prompts.SCENARIOS_SCHEMA, mock, temperature=0.8)


def clarifying_situations(agent: str, does: str, description: str, audience: str,
                          answers: list[dict], n: int = 3) -> dict:
    scenarios = []
    for j in range(n):
        s = _mock_case("Tests your answers", does, audience, 200 + j)
        s["kind"] = "surprising"
        s["title"] = f"Tests your answers {j + 1}"
        s["situation"] = (f"A concrete case (#{j + 1}) built to probe where your "
                          f"earlier answers are ambiguous (placeholder example).")
        s["at_stake"] = "which of your stated preferences wins when they collide"
        scenarios.append(s)
    mock = {"scenarios": scenarios}
    return _call(
        prompts.clarifying_situations_messages(agent, does, description, audience,
                                               answers, n),
        prompts.SCENARIOS_SCHEMA, mock, temperature=0.7)


def example_behavior(agent: str, does: str, description: str, audience: str,
                     scenario: dict) -> dict:
    mock = {"text": ("The agent handles it directly, keeps the person informed, and "
                     "flags anything sensitive for them to confirm.")}
    return _call(
        prompts.example_behavior_messages(agent, does, description, audience, scenario),
        prompts.EXAMPLE_SCHEMA, mock, temperature=0.6)


def rubric_feedback(agent: str, does: str, description: str, audience: str,
                    scenario: dict, draft: str, rubric: list[dict],
                    reflection: list[dict] | None = None) -> dict:
    # Deterministic mock: middling levels so the score badge and Why-not-higher
    # render meaningfully on the keyless path.
    mock_levels = {0: 3, 1: 2, 2: 3, 3: 2}
    mock = {
        "criteria": [
            {"name": c["name"], "level": mock_levels.get(i, 2),
             "why": ("Overall, the draft partly addresses this.\n"
                     "- It gestures at the right behavior (placeholder).\n"
                     "- Wording is understandable for this case."),
             "why_not_higher": ("" if mock_levels.get(i, 2) >= 4 else
                                ("Overall, one step is missing for the next "
                                 "level.\n- " + c["levels"].get(
                                     str(mock_levels.get(i, 2) + 1), "")))}
            for i, c in enumerate(rubric)
        ],
    }
    return _call(
        prompts.rubric_feedback_messages(agent, does, description, audience,
                                         scenario, draft, rubric,
                                         reflection=reflection),
        prompts.FEEDBACK_SCHEMA, mock, temperature=0.3)


_LEAD_NUM = re.compile(r"^\s*(?:[-*\u2022]|\d+[.)])\s*")


def _clean_principles(items, cap: int) -> list[str]:
    """Strip any list marker the model copied in from the prompt, and cap."""
    out = []
    for p in items or []:
        text = (p or "").strip()
        prev = None
        while text != prev:                 # "1. 1. x" needs two passes
            prev = text
            text = _LEAD_NUM.sub("", text).strip()
        if text:
            out.append(text)
    return out[:cap]


def policy_write(agent: str, does: str, audience: str, rubric: list[dict],
                 answers: list[dict], picks: list[dict], cap: int) -> dict:
    """The first policy, from the per-case rules plus the round-1 picks."""
    mock = {"principles": [
        (a.get("ideal_behavior") or "").strip()
        for a in answers if (a.get("ideal_behavior") or "").strip()
    ][:cap] or ["Keep it calm and age appropriate, and tell the parent."],
        "what_changed": "Built from the rules you wrote and your first-round choices."}
    data = _call(prompts.policy_write_messages(agent, does, audience, rubric,
                                               answers, picks, cap),
                 prompts.POLICY_SCHEMA, mock)
    data["principles"] = _clean_principles(data.get("principles"), cap)
    return data


def policy_revise(agent: str, does: str, audience: str, rubric: list[dict],
                  policy: dict, instance: str, option_a: dict, option_b: dict,
                  model_choice: str, person_choice: str, critique: str,
                  cap: int) -> dict:
    """Sharpen the same policy from one critique. Never a rewrite."""
    existing = list((policy or {}).get("principles") or [])
    extra = (critique or "").strip()
    mock = {"principles": (existing + ([extra] if extra else []))[:cap],
            "what_changed": "Added what you said about that decision."}
    data = _call(prompts.policy_revise_messages(agent, does, audience, rubric,
                                                policy, instance, option_a,
                                                option_b, model_choice,
                                                person_choice, critique, cap),
                 prompts.POLICY_SCHEMA, mock)
    data["principles"] = _clean_principles(data.get("principles"), cap)
    return data


def policy_pick(agent: str, does: str, audience: str, policy: dict,
                instance: str, option_a: dict, option_b: dict) -> dict:
    """The agent's own choice between two responses, using only the policy."""
    # Deterministic offline pick so the mock path is reproducible: first
    # principle drives it, and A is the fallback.
    principles = (policy or {}).get("principles") or []
    lead = principles[0] if principles else "your policy"
    mock = {"choice": "A",
            "reason": f'Option A follows "{lead[:70]}" more closely.'}
    return _call(prompts.policy_pick_messages(agent, does, audience, policy,
                                              instance, option_a, option_b),
                 prompts.POLICY_PICK_SCHEMA, mock)


def reflect_before(agent: str, does: str, audience: str, scenario: dict) -> dict:
    """Socratic questions shown before the person writes anything."""
    mock = {"questions": [
        {"type": "assumptions",
         "question": "What are you taking for granted about what your child "
                     "already understands here?"},
        {"type": "viewpoints",
         "question": "How would your child describe this moment, and would it "
                     "match how you would describe it?"},
    ][:prompts.N_REFLECT_BEFORE]}
    return _call(prompts.reflect_before_messages(agent, does, audience, scenario),
                 prompts.REFLECT_SCHEMA, mock)


def reflect_after(agent: str, does: str, audience: str, scenario: dict,
                  draft: str) -> dict:
    """Socratic questions grounded in what the person actually wrote."""
    snippet = " ".join((draft or "").split()[:6]) or "what you wrote"
    mock = {"questions": [
        {"type": "clarification",
         "question": f'What exactly do you mean by "{snippet}"?'},
        {"type": "reasons",
         "question": "What makes that the right call for your child rather than "
                     "children in general?"},
        {"type": "implications",
         "question": "If the agent followed that every time, what would your "
                     "child stop coming to you about?"},
    ][:prompts.N_REFLECT_AFTER]}
    return _call(prompts.reflect_after_messages(agent, does, audience, scenario,
                                                draft),
                 prompts.REFLECT_SCHEMA, mock)


def confirm_pairwise(agent: str, does: str, description: str, audience: str,
                     scenario: dict, ideal_behavior: str,
                     avoid: list[str] | None = None, edge: bool = False) -> dict:
    mock = {
        "dimension": "severity of the situation",
        "instance": (f"A specific, near yes-or-no instance of: "
                     f"{scenario.get('title', 'this case')} (placeholder)."),
        "user_message": "can I see the whole thing?",
        "options": [
            {"label": "Go ahead",
             "text": "Sure, here it is. Let me know if you have questions."},
            {"label": "Check first",
             "text": "Let me check with your mom first, then I can show you."},
        ],
    }
    return _call(
        prompts.confirm_pairwise_messages(agent, does, description, audience,
                                          scenario, ideal_behavior,
                                          avoid=avoid, edge=edge),
        prompts.CONFIRM_SCHEMA, mock, temperature=0.7)


def agent_reply(agent: str, does: str, audience: str, scenario: dict,
                behavior: str | None, history: list[dict]) -> dict:
    """One agent turn in the scenario chat. behavior=None gives the baseline."""
    last = ""
    for t in reversed(history or []):
        if t.get("role") == "user":
            last = (t.get("content") or "").strip()
            break
    if (behavior or "").strip():
        mock = {"response": ("Following your instructions, the agent answers "
                             f"carefully and briefly about \"{last[:60]}\", keeps "
                             "the detail age appropriate, and offers to bring you "
                             "in if it goes further (placeholder)."),
                "what_changed": "Shorter, less detail, and offers to involve you."}
    else:
        mock = {"response": (f"A plain, complete answer about \"{last[:60]}\" with "
                             "no special instructions applied (placeholder)."),
                "what_changed": ""}
    return _call(
        prompts.agent_reply_messages(agent, does, audience, scenario, behavior,
                                     history),
        prompts.REPLY_SCHEMA, mock, temperature=0.4)
