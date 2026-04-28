"""Per shift-type / weekday preference heatmap (3x7 grid)."""
import json
import pandas as pd
import streamlit as st

from theme import header, FG, MUTED_FG, BORDER, GRID_HEADER, CARD_BG

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SHIFTS = [
    ("D", "Day",     "hsl(45, 93%, 60%)"),
    ("E", "Evening", "hsl(25, 90%, 55%)"),
    ("N", "Night",   "hsl(270, 50%, 55%)"),
]
RATING_LABEL = {
    -2: "Avoid",
    -1: "Mild no",
    0: "Neutral",
    1: "Mild yes",
    2: "Love it",
}
RATINGS = [-2, -1, 0, 1, 2]


def _cell_color(score: int) -> str:
    if score >= 2: return "#1FA060"
    if score == 1: return "#92D2AE"
    if score == 0: return "#E6EAEF"
    if score == -1: return "#F1B5B5"
    return "#D44A4A"


def _cell_fg(score: int) -> str:
    return "white" if score in (-2, 2) else FG


def render() -> None:
    if "day_pref_df" not in st.session_state:
        st.session_state.day_pref_df = pd.DataFrame(
            [[0] * 7, [0] * 7, [0] * 7],
            index=[label for _, label, _ in SHIFTS],
            columns=DAYS,
        )

    header(
        "Day-by-day preferences",
        "For every shift × weekday combo, rate how much you'd want to work it. "
        "We use this for the soft cost in the schedule optimizer.",
    )

    # Editor — single data_editor handles all 21 ratings, no overflow.
    st.markdown(
        '<div class="np-section-title">Set your ratings (-2 avoid · 0 neutral · +2 love)</div>',
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
            for day in DAYS
        },
        key="day_pref_editor",
    )
    st.session_state.day_pref_df = edited

    # Live heatmap built from the edited frame.
    st.markdown(
        '<div class="np-section-title" style="margin-top:18px;">Heatmap preview</div>',
        unsafe_allow_html=True,
    )
    head_cells = "".join(
        f'<th style="padding:8px;font-size:11px;font-weight:600;color:{MUTED_FG};'
        f'background:{GRID_HEADER};border-bottom:1px solid {BORDER};">{d}</th>'
        for d in DAYS
    )
    body_rows = ""
    for (code, label, swatch) in SHIFTS:
        cells = ""
        for day in DAYS:
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

    legend_chips = "".join(
        f'<div style="display:flex;align-items:center;gap:6px;">'
        f'<div style="width:24px;height:18px;border-radius:4px;'
        f'background:{_cell_color(s)};"></div>'
        f'<span style="font-size:12px;color:{MUTED_FG};">{s:+d} · {RATING_LABEL[s]}</span>'
        f'</div>'
        for s in RATINGS
    )
    st.markdown(
        f'<div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:10px;">'
        f'{legend_chips}</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    with st.expander("Anything special about a particular day?"):
        st.text_area(
            "Free text",
            key="day_pref_freeform",
            label_visibility="collapsed",
            placeholder="e.g. 'Tuesdays I'd rather not have a night shift, kids' "
                        "activities run late.'",
        )

    payload_ratings = []
    for (code, label, _) in SHIFTS:
        for day in DAYS:
            try:
                score = int(edited.loc[label, day])
            except (KeyError, ValueError, TypeError):
                score = 0
            score = max(-2, min(2, score))
            payload_ratings.append({
                "shift": code, "day": day, "score": score,
                "label": RATING_LABEL[score],
            })

    payload = {
        "ratings": payload_ratings,
        "freeform": st.session_state.get("day_pref_freeform", ""),
    }

    st.download_button(
        "Download my preferences (JSON)",
        data=json.dumps(payload, indent=2),
        file_name="day_preferences.json",
        mime="application/json",
    )
