"""Pairwise schedule comparison view."""
import json
import random
import streamlit as st

from theme import header, FG, MUTED_FG, BORDER, CARD_BG
from schedule_utils import (
    make_pattern_schedule,
    render_schedule_html,
    schedule_summary,
)

NURSES = ["You", "A. Patel", "M. Chen", "J. Rivera", "S. Okafor"]
YEAR, MONTH = 2026, 5
PATTERNS = ["balanced", "night-heavy", "block", "random"]


def _new_pair() -> None:
    rng = random.Random(st.session_state.compare_round * 7 + 1)
    a, b = rng.sample(PATTERNS, 2)
    st.session_state.compare_pair = {
        "A": {"pattern": a, "seed": rng.randint(0, 9999)},
        "B": {"pattern": b, "seed": rng.randint(0, 9999)},
    }


def _record(choice: str, pair, sched_a, sched_b) -> None:
    st.session_state.compare_choices.append({
        "round": st.session_state.compare_round + 1,
        "choice": choice,
        "A": pair["A"],
        "B": pair["B"],
        "summary_A": schedule_summary(sched_a),
        "summary_B": schedule_summary(sched_b),
    })
    st.session_state.compare_round += 1
    _new_pair()


def render() -> None:
    if "compare_round" not in st.session_state:
        st.session_state.compare_round = 0
    if "compare_choices" not in st.session_state:
        st.session_state.compare_choices = []
    if "compare_pair" not in st.session_state:
        _new_pair()

    header(
        "Compare two schedules",
        "Imagine each table is your team's next month. Which one would you rather "
        "work? Pick a winner and we'll generate another pair.",
    )

    pair = st.session_state.compare_pair
    sched_a = make_pattern_schedule(NURSES, YEAR, MONTH,
                                    pair["A"]["pattern"], pair["A"]["seed"])
    sched_b = make_pattern_schedule(NURSES, YEAR, MONTH,
                                    pair["B"]["pattern"], pair["B"]["seed"])

    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        st.markdown(
            render_schedule_html(NURSES, sched_a, YEAR, MONTH,
                                 title="Schedule A", badge="Option A"),
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            render_schedule_html(NURSES, sched_b, YEAR, MONTH,
                                 title="Schedule B", badge="Option B"),
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown(
        f'<div class="np-section-title">Your pick</div>',
        unsafe_allow_html=True,
    )
    btn_cols = st.columns(3, gap="small")
    with btn_cols[0]:
        if st.button("← Prefer A", use_container_width=True,
                     key=f"pref_a_{st.session_state.compare_round}"):
            _record("A", pair, sched_a, sched_b)
            st.rerun()
    with btn_cols[1]:
        if st.button("No preference", use_container_width=True,
                     key=f"pref_tie_{st.session_state.compare_round}"):
            _record("tie", pair, sched_a, sched_b)
            st.rerun()
    with btn_cols[2]:
        if st.button("Prefer B →", use_container_width=True,
                     key=f"pref_b_{st.session_state.compare_round}"):
            _record("B", pair, sched_a, sched_b)
            st.rerun()

    st.text_input(
        "Optional: in one phrase, why?",
        key=f"why_{st.session_state.compare_round}",
        placeholder="e.g. 'too many night shifts in B'",
    )

    st.divider()

    st.markdown(
        f'<div style="display:flex;align-items:baseline;gap:12px;margin-bottom:8px;">'
        f'<div style="font-size:15px;font-weight:600;color:{FG};">Your responses</div>'
        f'<div class="np-muted">{len(st.session_state.compare_choices)} comparisons '
        f'recorded</div></div>',
        unsafe_allow_html=True,
    )

    if st.session_state.compare_choices:
        rows = []
        for c in st.session_state.compare_choices[-8:]:
            rows.append(
                f'<tr>'
                f'<td style="padding:6px 10px;border-bottom:1px solid {BORDER};'
                f'color:{FG};">#{c["round"]}</td>'
                f'<td style="padding:6px 10px;border-bottom:1px solid {BORDER};'
                f'color:{FG};">{c["A"]["pattern"]}</td>'
                f'<td style="padding:6px 10px;border-bottom:1px solid {BORDER};'
                f'color:{FG};">{c["B"]["pattern"]}</td>'
                f'<td style="padding:6px 10px;border-bottom:1px solid {BORDER};'
                f'color:{FG};font-weight:600;">{c["choice"]}</td>'
                f'</tr>'
            )
        head_style = (
            f'padding:8px 10px;text-align:left;color:{MUTED_FG};font-size:11px;'
            f'text-transform:uppercase;letter-spacing:0.06em;'
            f'border-bottom:1px solid {BORDER};background:{CARD_BG};'
        )
        st.markdown(
            f'<div class="np-card" style="padding:0;overflow:hidden;">'
            f'<table style="width:100%;border-collapse:collapse;font-size:13px;">'
            f'<thead><tr>'
            f'<th style="{head_style}">Round</th>'
            f'<th style="{head_style}">A pattern</th>'
            f'<th style="{head_style}">B pattern</th>'
            f'<th style="{head_style}">Picked</th>'
            f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "Download responses (JSON)",
            data=json.dumps(st.session_state.compare_choices, indent=2),
            file_name="schedule_comparisons.json",
            mime="application/json",
        )
    else:
        st.markdown(
            '<div class="np-card-muted">No comparisons yet — pick A or B above.</div>',
            unsafe_allow_html=True,
        )
