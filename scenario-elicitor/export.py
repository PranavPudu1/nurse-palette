"""Assemble the scenario artifact and serialize it.

Two outputs:
  1. A JSON object with the agent, who it is for, the concrete cases, and the
     ideal behavior the person authored for each.
  2. A JSONL benchmark of {situation, at_stake, ideal_behavior} rows, one per
     authored case: run each situation through a model and compare its response
     to the ideal behavior.
"""
from __future__ import annotations
import json


def build_artifact(*, agent: str, frame: dict, description: str, audience: str,
                   scenarios: list[dict], answers: list[dict],
                   confirm: list[dict] | None = None,
                   rubric: list[dict] | None = None,
                   policy: dict | None = None,
                   policy_log: list[dict] | None = None,
                   submitted: bool = False) -> dict:
    return {
        "agent": agent,
        "restated_agent": (frame or {}).get("restated_agent", agent),
        "does": (frame or {}).get("does", ""),
        "audience": audience,
        "description": description,
        "submitted": submitted,
        "rubric": rubric or [],
        # The one policy, and every version of it with what changed and why.
        "policy": (policy or {}).get("principles", []),
        "policy_version": (policy or {}).get("version"),
        "policy_history": [{"version": v.get("version"),
                            "principles": v.get("principles", []),
                            "what_changed": v.get("what_changed", ""),
                            "source": v.get("source", "")}
                           for v in (policy_log or [])],
        "cases": [{"id": s["id"], "category": s.get("category", ""),
                   "title": s.get("title", ""), "situation": s.get("situation", ""),
                   "at_stake": s.get("at_stake", ""),
                   "considerations": s.get("considerations", []),
                   "analysis": s.get("analysis", "")}
                  for s in scenarios],
        "answers": [{"theme": a.get("theme", ""),
                     "case_ids": a.get("case_ids", []),
                     "case_id": a.get("scenario_id"), "title": a.get("title", ""),
                     "situation": a.get("situation", ""),
                     "at_stake": a.get("at_stake", ""),
                     "ideal_behavior": a.get("ideal_behavior", ""),
                     "first_draft": a.get("first_draft", ""),
                     "rubric_levels": a.get("rubric_levels", {}),
                     "rubric_score": a.get("rubric_score"),
                     "n_revisions": a.get("n_revisions", 0),
                     "rule_versions": a.get("rule_versions", []),
                     "n_tests": a.get("n_tests", 0),
                     "why": a.get("why", ""),
                     "reflection": a.get("reflection", [])}
                    for a in answers],
        "confirmations": [{"theme": c.get("theme", ""),
                           "case_id": c.get("scenario_id"),
                           "title": c.get("title", ""),
                           "situation": c.get("situation", ""),
                           "instance": c.get("instance", ""),
                           "user_message": c.get("user_message", ""),
                           "dimension": c.get("dimension", ""),
                           "option_a": c.get("option_a", {}),
                           "option_b": c.get("option_b", {}),
                           "choice": c.get("choice"), "note": c.get("note", ""),
                           "round": c.get("round"),
                           "model_choice": c.get("model_choice", ""),
                           "model_reason": c.get("model_reason", ""),
                           "critique": c.get("critique", ""),
                           "agreed": c.get("agreed")}
                          for c in (confirm or [])],
    }


def to_json(artifact: dict) -> str:
    return json.dumps(artifact, indent=2, ensure_ascii=False)


def to_jsonl(answers: list[dict], *, agent: str = "", audience: str = "") -> str:
    """One row per authored rule: {theme, situation, at_stake, ideal_behavior}.

    A personalized benchmark over agent behaviors: prompt a model with the
    situation and compare its response to ``ideal_behavior``.

    One row per THEME now rather than per case, since that is the unit a rule is
    written for. `at_stake` is still here even though it no longer appears
    anywhere on screen: a row without it says what the agent should do but not
    what it was deciding between, which is most of what makes the row usable.
    """
    lines = []
    for a in answers:
        beh = (a.get("ideal_behavior") or "").strip()
        if not beh:
            continue
        lines.append(json.dumps({
            "agent": agent,
            "audience": audience,
            "theme": a.get("theme", ""),
            "situation": a.get("situation", ""),
            "at_stake": a.get("at_stake", ""),
            "ideal_behavior": beh,
        }, ensure_ascii=False))
    return "\n".join(lines)


def to_confirm_jsonl(confirm: list[dict]) -> str:
    """One row per decisive comparison: {situation, instance, chosen, rejected}.

    The concrete pairwise picks from the confirm step, as a second benchmark over
    boundary behaviors. Ties are skipped.
    """
    lines = []
    for c in confirm:
        ch = c.get("choice")
        if ch not in ("A", "B"):
            continue
        a, b = c.get("option_a", {}), c.get("option_b", {})
        chosen, rejected = (a, b) if ch == "A" else (b, a)
        lines.append(json.dumps({
            "situation": c.get("situation", ""),
            "instance": c.get("instance", ""),
            "dimension": c.get("dimension", ""),
            "chosen": chosen.get("text", ""),
            "rejected": rejected.get("text", ""),
        }, ensure_ascii=False))
    return "\n".join(lines)
