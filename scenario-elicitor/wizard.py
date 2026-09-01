"""Wizard skeleton: session state, progress stepper, and nav.

The step sequence is per-arm and lives in conditions.py; this module walks
whatever sequence the session's arm defines. Per screen bodies live in steps.py;
render() dispatches to them (local import to avoid a circular dependency).

Position is tracked by step KEY, not by index. An index alone breaks the moment
arms have different lengths: a session snapshotted at index 5 under a six-step
arm and resumed under a four-step arm would index off the end.
"""
from __future__ import annotations

import copy

import streamlit as st

from theme import (PRIMARY, PRIMARY_HOVER, PRIMARY_SOFT, ACCENT, SURFACE_BG,
                   BORDER, FG, MUTED_FG)
import conditions
import prompts
import store

def steps() -> list[dict]:
    """This session's ordered steps. Labels live in conditions.STEP_LIBRARY."""
    return conditions.steps_for()


def cur_index() -> int:
    """Index of the current step within THIS arm, guaranteed in range.

    Prefers the stored step key. Falls back to the legacy ordinal, clamped, so
    sessions snapshotted before keys existed (or under a longer arm) resume onto
    a real step instead of raising IndexError.
    """
    seq = steps()
    keys = [s["key"] for s in seq]
    key = st.session_state.get("sb_step_key")
    if key in keys:
        return keys.index(key)
    try:
        i = int(st.session_state.get("sb_step", 0) or 0)
    except (TypeError, ValueError):
        i = 0
    return max(0, min(i, len(seq) - 1))


def _set_index(i: int) -> None:
    """Move to a position, keeping the index and the key in sync."""
    seq = steps()
    i = max(0, min(int(i), len(seq) - 1))
    st.session_state.sb_step = i
    st.session_state.sb_step_key = seq[i]["key"]


def goto_key(key: str) -> None:
    """Jump to a step by key. No-op if this arm does not include it."""
    keys = [s["key"] for s in steps()]
    if key in keys:
        _set_index(keys.index(key))


# How many themes a participant works through, and how many cases they see for
# each. Min: "maybe we only limit to three cases for now, we don't give them an
# option." Three of the seven themes keeps the session inside a Prolific-sized
# window while still covering more than one kind of concern.
N_THEMES = 3
N_CASES_PER_THEME = 3


def init() -> None:
    ss = st.session_state
    ss.setdefault("sb_condition", conditions.DEFAULT_ARM)
    ss.setdefault("sb_step", 0)
    # Resolve position once per run so a restored index can never point past the
    # end of this arm's sequence.
    _set_index(cur_index())
    # The study's fixed domain is preselected; free text and chips still work.
    ss.setdefault("sb_agent", prompts.KIDS_AGENT)
    ss.setdefault("sb_frame", None)
    ss.setdefault("sb_desc", "")
    ss.setdefault("sb_audience", "")        # who the agent is for (concreteness)
    ss.setdefault("sb_scenarios", None)     # list of concrete case dicts once generated
    ss.setdefault("sb_next_id", 0)
    ss.setdefault("sb_idx", 0)              # current case within a theme
    ss.setdefault("sb_answers", [])         # one authored rule per theme
    # Theme-first state. sb_theme is the theme being worked on, or None for the
    # menu; the whole `themes` step routes on it. sb_tphase moves the workspace
    # from writing the rule to the comparisons that test it.
    ss.setdefault("sb_theme", None)
    ss.setdefault("sb_tphase", "write")      # "write" | "test"
    ss.setdefault("sb_tround", 1)            # round within a theme's testing loop
    ss.setdefault("sb_themes_done", [])      # theme names with a saved rule
    ss.setdefault("sb_examples", {})        # case_id -> {"text": ...} example cache
    ss.setdefault("sb_confirm", [])         # every pick, across all rounds
    ss.setdefault("sb_confirm_cache", {})   # legacy, kept so old snapshots load
    ss.setdefault("sb_cmp", {})             # "theme:round" -> [comparison, ...]
    ss.setdefault("sb_revealed", {})        # reveal flags per comparison
    ss.setdefault("sb_rubric", copy.deepcopy(prompts.RUBRIC))  # editable per session
    ss.setdefault("sb_submitted", False)    # frozen after final submission
    _migrate_pre_themes()


def _migrate_pre_themes() -> None:
    """Send a session saved before the theme restructure back to the menu.

    Answers used to be one per case; they are now one per theme, and the step
    keys they were saved under ("scenarios", "respond") no longer exist in any
    arm. Left alone, cur_index() clamps such a snapshot to the LAST step, so
    someone resuming an old code would land on the export screen holding one
    stale answer. There is no honest way to reshape per-case answers into
    per-theme ones, so the old work is cleared and they restart at the menu.
    """
    ss = st.session_state
    answers = ss.get("sb_answers") or []
    if not answers or all(a.get("theme") for a in answers):
        return
    ss.sb_answers = []
    ss.sb_confirm = []
    ss.sb_cmp = {}
    ss.sb_revealed = {}
    ss.sb_theme = None
    ss.sb_tphase = "write"
    ss.sb_themes_done = []
    goto_key("themes")
    st.warning("This tool changed since you last used it: rules are now written "
               "per topic rather than per case. Your earlier answers could not "
               "be carried over, so you are starting from the topic list.")


def new_id() -> int:
    i = st.session_state.sb_next_id
    st.session_state.sb_next_id += 1
    return i


def goto(i: int) -> None:
    _set_index(i)
    st.rerun()


def can_advance(key: str) -> bool:
    ss = st.session_state
    if key == "agent":
        return bool(ss.sb_agent.strip())
    if key == "describe":
        # Same rule as everywhere else: a question that can be skipped does not
        # make anyone think. Nothing to answer until they have named an
        # audience, so an empty audience does not trap them here.
        import steps
        if not (ss.get("sb_audience") or "").strip():
            return True
        return not [k for k, _ in steps._intake_slots() if not steps._answered(k)]
    if key == "themes":
        # Forward travel is only allowed from the menu, never from inside a
        # theme: Continue on the workspace would silently abandon a half-written
        # rule. The workspace supplies its own way back to the menu.
        if ss.get("sb_theme"):
            return False
        return len(ss.get("sb_themes_done") or []) >= N_THEMES
    return True  # agent is preselected, output is last


def _stepper_html(steps: list, cur: int) -> str:
    """The pipeline as a row of named pills: current filled, done checked, rest quiet."""
    n = len(steps)
    eyebrow = (f'<div class="np-app-title" style="font-size:13px;color:{MUTED_FG};'
               f'margin-bottom:6px;">Step {cur + 1} of {n}</div>')
    pills = []
    for i, s in enumerate(steps):
        short = s.get("short", s["title"])
        if i == cur:
            bg, fg, bd, wt, lead = PRIMARY_HOVER, "#ffffff", PRIMARY_HOVER, 700, f"{i + 1}"
        elif i < cur:
            bg, fg, bd, wt, lead = PRIMARY_SOFT, PRIMARY_HOVER, "#F1D3C6", 600, "&#10003;"
        else:
            bg, fg, bd, wt, lead = SURFACE_BG, MUTED_FG, BORDER, 500, f"{i + 1}"
        # The labels are phrases now, so they wrap rather than truncate: an
        # ellipsised "Write and test a r..." defeats the point of naming them.
        # align-items:stretch keeps every pill the height of the tallest.
        pills.append(
            f'<div style="flex:1;min-width:0;text-align:center;padding:9px 8px;'
            f'border-radius:9px;background:{bg};color:{fg};border:1px solid {bd};'
            f'font-size:11.5px;font-weight:{wt};line-height:1.25;'
            f'display:flex;align-items:center;justify-content:center;">'
            f'<span style="opacity:0.7;">{lead}</span>&nbsp;{short}</div>')
    return (eyebrow + '<div style="display:flex;gap:6px;margin-bottom:2px;'
            'align-items:stretch;">' + "".join(pills) + "</div>")


def _stepper() -> None:
    st.markdown(_stepper_html(steps(), cur_index()), unsafe_allow_html=True)


def _advance(delta: int) -> None:
    ss = st.session_state
    _set_index(cur_index() + delta)
    rid = ss.get("resp_id")
    if rid:
        store.log_event(rid, ss.sb_step_key, "nav",
                        {"step_index": ss.sb_step, "condition": conditions.arm()})


def _nav() -> None:
    seq = steps()
    cur = cur_index()
    key = seq[cur]["key"]
    c1, _, c3 = st.columns([1.3, 4, 1.3])
    with c1:
        if cur > 0:
            st.button("Back", use_container_width=True, key="sb_nav_back",
                      type="secondary", on_click=_advance, args=(-1,))
    with c3:
        if cur < len(seq) - 1:
            st.button("Continue", use_container_width=True, key="sb_nav_cont",
                      disabled=not can_advance(key), on_click=_advance, args=(1,))


def render() -> None:
    init()
    _stepper()
    st.write("")
    import steps as step_bodies  # local import avoids a circular dependency
    step_bodies.render(steps()[cur_index()]["key"])
    st.divider()
    _nav()
    # Autosave: upsert the latest sb_* state so the session can resume later.
    rid = st.session_state.get("resp_id")
    if rid:
        store.save_snapshot(rid, dict(st.session_state))
