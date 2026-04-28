"""Build-your-ideal-month view."""
import calendar
import json
from datetime import date

import pandas as pd
import streamlit as st

from theme import (header, legend_html, shift_chip, BORDER, MUTED_FG, FG,
                   GRID_HEADER, ACCENT, CARD_BG, SURFACE_BG)

YEAR, MONTH = 2026, 5
DAYS = calendar.monthrange(YEAR, MONTH)[1]
DAY_ABBR = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
SHIFT_OPTIONS = ["X", "D", "E", "N"]
SHIFT_LONG = {"D": "Day", "E": "Evening", "N": "Night", "X": "Off"}


def render() -> None:
    if "ideal_rows" not in st.session_state:
        st.session_state.ideal_rows = pd.DataFrame(
            [["X"] * 7 for _ in range((DAYS // 7) + 1)],
            columns=DAY_ABBR,
        )

    header(
        "Build your ideal month",
        f"Sketch out what your perfect {calendar.month_name[MONTH]} {YEAR} would "
        "look like. Click a cell to pick Day, Evening, Night, or Off. Use the "
        "totals below to keep yourself honest.",
    )

    st.markdown(legend_html(), unsafe_allow_html=True)

    st.markdown(
        '<div class="np-section-title" style="margin-top:14px;">Edit by week</div>',
        unsafe_allow_html=True,
    )
    edited = st.data_editor(
        st.session_state.ideal_rows,
        num_rows="fixed",
        use_container_width=True,
        hide_index=False,
        column_config={
            day: st.column_config.SelectboxColumn(
                day, options=SHIFT_OPTIONS, required=True, width="small",
            )
            for day in DAY_ABBR
        },
        key="ideal_editor",
    )
    st.session_state.ideal_rows = edited

    st.markdown(
        f'<div class="np-muted" style="margin-top:6px;">'
        f'Each row holds 7 days; the calendar preview pads to the real '
        f'{calendar.month_name[MONTH]} layout.</div>',
        unsafe_allow_html=True,
    )

    flat: list[str] = []
    for _, row in edited.iterrows():
        flat.extend([str(v) for v in row.tolist()])
    flat = flat[:DAYS]
    while len(flat) < DAYS:
        flat.append("X")

    counts = {s: flat.count(s) for s in SHIFT_OPTIONS}
    chips = "".join(
        f'<div style="display:flex;align-items:center;gap:6px;'
        f'padding:6px 10px;background:{CARD_BG};border:1px solid {BORDER};'
        f'border-radius:8px;">{shift_chip(s, 22)}'
        f'<span style="font-size:12px;color:{MUTED_FG};">{SHIFT_LONG[s]}</span>'
        f'<span style="font-size:13px;font-weight:600;color:{FG};">{counts[s]}</span>'
        f'</div>'
        for s in SHIFT_OPTIONS
    )
    st.markdown(
        f'<div class="np-section-title" style="margin-top:18px;">Totals</div>'
        f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px;">{chips}</div>',
        unsafe_allow_html=True,
    )

    first_dow = date(YEAR, MONTH, 1).weekday()
    weeks: list[list[tuple[int | None, str]]] = []
    cur: list[tuple[int | None, str]] = [(None, "")] * first_dow
    for d in range(1, DAYS + 1):
        cur.append((d, flat[d - 1]))
        if len(cur) == 7:
            weeks.append(cur)
            cur = []
    if cur:
        while len(cur) < 7:
            cur.append((None, ""))
        weeks.append(cur)

    st.markdown(
        '<div class="np-section-title">Calendar preview</div>',
        unsafe_allow_html=True,
    )
    head = "".join(
        f'<th style="padding:8px;font-size:11px;color:{MUTED_FG};font-weight:600;'
        f'background:{GRID_HEADER};border-bottom:1px solid {BORDER};text-align:center;">'
        f'{d}</th>'
        for d in DAY_ABBR
    )
    rows_html = ""
    for w in weeks:
        cells = ""
        for i, (day_num, shift) in enumerate(w):
            is_weekend = i >= 5
            if day_num is None:
                bg = SURFACE_BG
                inner = ""
            else:
                bg = ACCENT if is_weekend else CARD_BG
                inner = (
                    f'<div style="font-size:11px;color:{MUTED_FG};font-weight:500;'
                    f'margin-bottom:2px;">{day_num}</div>'
                    f'<div style="display:flex;justify-content:center;">'
                    f'{shift_chip(shift, 26)}</div>'
                )
            cells += (
                f'<td style="padding:6px;background:{bg};color:{FG};'
                f'border:1px solid {BORDER};vertical-align:top;height:64px;">'
                f'{inner}</td>'
            )
        rows_html += f'<tr>{cells}</tr>'

    st.markdown(
        f'<div style="border:1px solid {BORDER};border-radius:10px;overflow:hidden;'
        f'background:{CARD_BG};">'
        f'<table style="width:100%;border-collapse:collapse;color:{FG};">'
        f'<thead><tr>{head}</tr></thead><tbody>{rows_html}</tbody></table></div>',
        unsafe_allow_html=True,
    )

    st.divider()

    with st.expander("Add a note about why this is your ideal"):
        st.text_area(
            "What about this month feels right?",
            key="ideal_freeform",
            label_visibility="collapsed",
            placeholder="e.g. 'I love front-loading nights so the back half is "
                        "family time.'",
        )

    payload = {
        "year": YEAR,
        "month": MONTH,
        "shifts": [{"day": d + 1, "shift": flat[d]} for d in range(DAYS)],
        "totals": counts,
        "note": st.session_state.get("ideal_freeform", ""),
    }

    st.download_button(
        "Download my ideal month (JSON)",
        data=json.dumps(payload, indent=2),
        file_name="ideal_schedule.json",
        mime="application/json",
    )
