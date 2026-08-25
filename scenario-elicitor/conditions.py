"""Study arms, and the step sequence each one walks.

The study compares different ways of promoting reflection: a top-down arm where
the person writes the policy and reflective questions prompt revision, a
bottom-up arm where the person makes pairwise choices and a model writes the
policy from their reasons, and two baselines.

Why this module exists: `wizard.STEPS` used to be a single static list. Streamlit
serves every session from one process, so a per-participant sequence cannot be
done by mutating module state. Everything routes through `steps_for()` instead,
which reads the arm off the session.

Adding a step: put it in STEP_LIBRARY, list its key in the arms that use it, and
register a renderer in steps._RENDERERS. Nothing else needs to change.

The `themes` step is one key with two modes, a menu and a workspace, rather than
two keys. A participant moves between them many times (pick a theme, write its
rule, come back for the next), which is a loop inside one step and not forward
travel through the wizard. Splitting it would have put a stepper pill on a screen
people revisit three times and broken Back.

Note on the non-default arms: only `c1` has been reworked for the theme-first
flow. `c2` and `base_b` skip rule writing entirely, so they currently reach the
comparisons with no authored rules to compare against. That is latent rather
than live, since `randomisation_on()` is false and every session gets `c1`.
"""
from __future__ import annotations

import os
import random

import streamlit as st

# key -> the stepper pill label and the screen title. Arms reference keys only,
# so a label change lands everywhere at once.
STEP_LIBRARY: dict[str, dict] = {
    "agent":     {"title": "The agent", "short": "Choose the agent"},
    "describe":  {"title": "How it should behave", "short": "Say who it is for"},
    "themes":    {"title": "What worries you", "short": "Write your rules"},
    "confirm":   {"title": "Confirm with comparisons",
                  "short": "Compare two behaviors"},
    "output":    {"title": "Your preferences", "short": "Export"},
}

# Sequences grow as the later steps land. Anything listed here must have a
# renderer registered, or dispatch raises KeyError.
ARMS: dict[str, dict] = {
    "c1": {
        "label": "Top-down",
        "blurb": "Write the policy for each situation; reflective questions and "
                 "the rubric prompt revision.",
        "steps": ["agent", "describe", "themes", "confirm", "output"],
    },
    "c2": {
        "label": "Bottom-up",
        "blurb": "Make pairwise choices and explain them; a model writes the "
                 "policy from those reasons.",
        "steps": ["agent", "describe", "themes", "confirm", "output"],
    },
    "base_a": {
        "label": "Baseline, free text",
        "blurb": "Write the policy in one box, with no structure and no feedback.",
        "steps": ["agent", "describe", "themes", "output"],
    },
    "base_b": {
        "label": "Baseline, comparisons only",
        "blurb": "Make pairwise choices. No policy is written by the person.",
        "steps": ["agent", "describe", "themes", "confirm", "output"],
    },
}

DEFAULT_ARM = "c1"


def _forced_arm() -> str:
    """STUDY_ARM pins every new session to one arm, for testing and demos."""
    want = os.environ.get("STUDY_ARM", "").strip().lower()
    return want if want in ARMS else ""


def randomisation_on() -> bool:
    """Multi-arm randomisation is OFF unless explicitly switched on.

    The tool ships as ONE complete pipeline: every session gets the full flow.
    The alternative arms exist for the study Min's doc describes, but handing a
    random visitor a version with no rule-writing screen is not a behaviour we
    want by default. Set STUDY_ARMS=on to enable randomisation for the study.
    """
    return os.environ.get("STUDY_ARMS", "").strip().lower() in ("1", "on", "true")


def assign_arm(counts: dict[str, int] | None = None) -> str:
    """Pick the arm for a new participant.

    Returns the full pipeline unless randomisation is switched on. When it is,
    assignment is balanced rather than a coin flip: fill whichever arm has the
    fewest real respondents so far, ties broken randomly. Over a run that tracks
    equal cell sizes far more tightly, which matters when the outcome is noisy
    and N per cell is small.
    """
    forced = _forced_arm()
    if forced:
        return forced
    if not randomisation_on():
        return DEFAULT_ARM
    counts = counts or {}
    fewest = min(counts.get(a, 0) for a in ARMS)
    return random.choice([a for a in ARMS if counts.get(a, 0) == fewest])


def arm() -> str:
    """The current session's arm, always a valid key."""
    a = st.session_state.get("sb_condition") or DEFAULT_ARM
    return a if a in ARMS else DEFAULT_ARM


def steps_for(condition: str | None = None) -> list[dict]:
    """The ordered step dicts for an arm: [{key, title, short}, ...]."""
    a = condition if condition in ARMS else arm()
    return [dict(STEP_LIBRARY[k], key=k) for k in ARMS[a]["steps"]]


def label(condition: str | None = None) -> str:
    return ARMS.get(condition or arm(), {}).get("label", "")
