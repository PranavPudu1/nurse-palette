"""Pairwise schedule comparison view — single nurse, calendar layout."""
import json
import random
import streamlit as st

from theme import header, FG, MUTED_FG, BORDER, CARD_BG
from i18n import t
from schedule_utils import (
    make_pattern_schedule,
    render_single_calendar,
    schedule_summary,
)

YEAR, MONTH = 2026, 5
PATTERNS = ["balanced", "night-heavy", "block", "random"]
SOLO = ["You"]


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
        "summary_A": schedule_summary({"You": sched_a}),
        "summary_B": schedule_summary({"You": sched_b}),
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

    header(t("compare.title"), t("compare.subtitle"))

    pair = st.session_state.compare_pair
    sched_a = make_pattern_schedule(SOLO, YEAR, MONTH,
                                    pair["A"]["pattern"], pair["A"]["seed"])["You"]
    sched_b = make_pattern_schedule(SOLO, YEAR, MONTH,
                                    pair["B"]["pattern"], pair["B"]["seed"])["You"]

    weekday_labels = [t(f"day.weekday.{d}") for d in
                      ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]]

    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        st.markdown(
            render_single_calendar(YEAR, MONTH, sched_a,
                                   title="A", badge=t("compare.option_a"),
                                   weekday_labels=weekday_labels),
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            render_single_calendar(YEAR, MONTH, sched_b,
                                   title="B", badge=t("compare.option_b"),
                                   weekday_labels=weekday_labels),
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown(
        f'<div class="np-section-title">{t("compare.your_pick")}</div>',
        unsafe_allow_html=True,
    )
    btn_cols = st.columns(3, gap="small")
    with btn_cols[0]:
        if st.button(t("compare.prefer_a"), use_container_width=True,
                     key=f"pref_a_{st.session_state.compare_round}"):
            _record("A", pair, sched_a, sched_b); st.rerun()
    with btn_cols[1]:
        if st.button(t("compare.tie"), use_container_width=True,
                     key=f"pref_tie_{st.session_state.compare_round}"):
            _record("tie", pair, sched_a, sched_b); st.rerun()
    with btn_cols[2]:
        if st.button(t("compare.prefer_b"), use_container_width=True,
                     key=f"pref_b_{st.session_state.compare_round}"):
            _record("B", pair, sched_a, sched_b); st.rerun()

    st.text_input(
        t("compare.why"),
        key=f"why_{st.session_state.compare_round}",
        placeholder=t("compare.why_ph"),
    )

    st.divider()

    st.markdown(
        f'<div style="display:flex;align-items:baseline;gap:12px;margin-bottom:8px;">'
        f'<div style="font-size:15px;font-weight:600;color:{FG};">'
        f'{t("compare.your_responses")}</div>'
        f'<div class="np-muted">'
        f'{t("compare.recorded", n=len(st.session_state.compare_choices))}</div></div>',
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
            f'<th style="{head_style}">{t("compare.col.round")}</th>'
            f'<th style="{head_style}">{t("compare.col.a")}</th>'
            f'<th style="{head_style}">{t("compare.col.b")}</th>'
            f'<th style="{head_style}">{t("compare.col.picked")}</th>'
            f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            t("compare.download"),
            data=json.dumps(st.session_state.compare_choices, indent=2),
            file_name="schedule_comparisons.json",
            mime="application/json",
        )
    else:
        st.markdown(
            f'<div class="np-card-muted">{t("compare.empty")}</div>',
            unsafe_allow_html=True,
        )
