"""Per shift-type / weekday preference heatmap (3x7 grid)."""
import json
import pandas as pd
import streamlit as st

from theme import header, FG, MUTED_FG, BORDER, GRID_HEADER, CARD_BG
from i18n import t

WEEKDAY_KEYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SHIFTS = [
    ("D", "hsl(45, 93%, 60%)"),
    ("E", "hsl(25, 90%, 55%)"),
    ("N", "hsl(270, 50%, 55%)"),
]


def _cell_color(score: int) -> str:
    if score >= 2: return "#1FA060"
    if score == 1: return "#92D2AE"
    if score == 0: return "#E6EAEF"
    if score == -1: return "#F1B5B5"
    return "#D44A4A"


def _cell_fg(score: int) -> str:
    return "white" if score in (-2, 2) else FG


def render() -> None:
    weekday_labels = [t(f"day.weekday.{k}") for k in WEEKDAY_KEYS]
    shift_labels = [t(f"shift.{code}") for code, _ in SHIFTS]

    if "day_pref_df" not in st.session_state:
        st.session_state.day_pref_df = pd.DataFrame(
            [[0] * 7, [0] * 7, [0] * 7],
            index=shift_labels, columns=weekday_labels,
        )
    elif (list(st.session_state.day_pref_df.columns) != weekday_labels
          or list(st.session_state.day_pref_df.index) != shift_labels):
        # Language changed — re-label without losing values.
        df = st.session_state.day_pref_df.copy()
        df.columns = weekday_labels
        df.index = shift_labels
        st.session_state.day_pref_df = df

    header(t("day.title"), t("day.subtitle"))

    st.markdown(
        f'<div class="np-section-title">{t("day.editor_label")}</div>',
        unsafe_allow_html=True,
    )
    edited = st.data_editor(
        st.session_state.day_pref_df,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            day: st.column_config.NumberColumn(
                day, min_value=-2, max_value=2, step=1, format="%d",
                width="small",
            )
            for day in weekday_labels
        },
        key=f"day_pref_editor_{len(weekday_labels)}_{shift_labels[0]}",
    )
    st.session_state.day_pref_df = edited

    st.markdown(
        f'<div class="np-section-title" style="margin-top:18px;">'
        f'{t("day.preview_label")}</div>',
        unsafe_allow_html=True,
    )
    head_cells = "".join(
        f'<th style="padding:8px;font-size:11px;font-weight:600;color:{MUTED_FG};'
        f'background:{GRID_HEADER};border-bottom:1px solid {BORDER};">{d}</th>'
        for d in weekday_labels
    )
    body_rows = ""
    for (code, swatch), label in zip(SHIFTS, shift_labels):
        cells = ""
        for day in weekday_labels:
            try:
                score = int(edited.loc[label, day])
            except (KeyError, ValueError, TypeError):
                score = 0
            score = max(-2, min(2, score))
            cells += (
                f'<td style="padding:6px;text-align:center;border:1px solid {BORDER};'
                f'background:{CARD_BG};">'
                f'<div style="background:{_cell_color(score)};color:{_cell_fg(score)};'
                f'border-radius:6px;padding:10px 0;font-weight:600;font-size:13px;">'
                f'{score:+d}</div></td>'
            )
        body_rows += (
            f'<tr><th style="text-align:left;padding:8px 12px;font-weight:600;'
            f'font-size:13px;color:{FG};background:{CARD_BG};'
            f'border:1px solid {BORDER};">'
            f'<span style="display:inline-block;width:10px;height:10px;border-radius:3px;'
            f'background:{swatch};margin-right:6px;vertical-align:middle;"></span>'
            f'{label}</th>{cells}</tr>'
        )
    st.markdown(
        f'<div style="border:1px solid {BORDER};border-radius:10px;overflow:hidden;'
        f'background:{CARD_BG};">'
        f'<table style="width:100%;border-collapse:collapse;color:{FG};">'
        f'<thead><tr><th style="background:{GRID_HEADER};'
        f'border-bottom:1px solid {BORDER};"></th>{head_cells}</tr></thead>'
        f'<tbody>{body_rows}</tbody></table></div>',
        unsafe_allow_html=True,
    )

    legend_specs = [
        (-2, "day.legend.m2"),
        (-1, "day.legend.m1"),
        ( 0, "day.legend.z"),
        ( 1, "day.legend.p1"),
        ( 2, "day.legend.p2"),
    ]
    legend_chips = "".join(
        f'<div style="display:flex;align-items:center;gap:6px;">'
        f'<div style="width:24px;height:18px;border-radius:4px;'
        f'background:{_cell_color(s)};"></div>'
        f'<span style="font-size:12px;color:{MUTED_FG};">{t(k)}</span>'
        f'</div>'
        for s, k in legend_specs
    )
    st.markdown(
        f'<div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:10px;">'
        f'{legend_chips}</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    with st.expander(t("day.freeform_label")):
        st.text_area(
            t("day.freeform_label"),
            key="day_pref_freeform", label_visibility="collapsed",
            placeholder=t("day.freeform_ph"),
        )

    payload_ratings = []
    for (code, _), label in zip(SHIFTS, shift_labels):
        for day_key, day_label in zip(WEEKDAY_KEYS, weekday_labels):
            try:
                score = int(edited.loc[label, day_label])
            except (KeyError, ValueError, TypeError):
                score = 0
            score = max(-2, min(2, score))
            payload_ratings.append({
                "shift": code, "day": day_key, "score": score,
            })

    payload = {
        "ratings": payload_ratings,
        "freeform": st.session_state.get("day_pref_freeform", ""),
    }

    st.download_button(
        t("day.download"),
        data=json.dumps(payload, indent=2, ensure_ascii=False),
        file_name="day_preferences.json",
        mime="application/json",
    )
