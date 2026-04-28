"""Trade-off sliders view."""
import json
import streamlit as st

from theme import header, FG, MUTED_FG, BORDER

QUESTIONS = [
    {
        "key": "consec_nights_max",
        "title": "Maximum nights in a row you'd accept",
        "help": "Beyond this, fatigue / safety becomes a real concern.",
        "min": 1, "max": 7, "default": 3, "suffix": "nights",
    },
    {
        "key": "weekend_off_freq",
        "title": "Minimum weekends off per month",
        "help": "Out of ~4 weekends.",
        "min": 0, "max": 4, "default": 2, "suffix": "weekends",
    },
    {
        "key": "extra_nights_for_weekend",
        "title": "Extra night shifts you'd trade for one extra weekend off",
        "help": "How much more night work would you accept to free up a weekend?",
        "min": 0, "max": 5, "default": 1, "suffix": "extra nights",
    },
    {
        "key": "min_rest_hours",
        "title": "Minimum rest between shifts (hours)",
        "help": "Below this, you'd push back even if it's legally allowed.",
        "min": 8, "max": 24, "default": 11, "suffix": "hours",
    },
    {
        "key": "predictability_vs_choice",
        "title": "Predictable rotation  ←→  Pick-your-own each month",
        "help": "0 = give me a fixed cycle I can plan my life around. "
                "100 = let me bid every month, even if it's irregular.",
        "min": 0, "max": 100, "default": 50, "suffix": "",
    },
    {
        "key": "team_alignment_weight",
        "title": "How much do you want shifts aligned with a teammate?",
        "help": "0 = doesn't matter; 100 = strongly prefer working with my partner.",
        "min": 0, "max": 100, "default": 30, "suffix": "",
    },
    {
        "key": "overtime_appetite",
        "title": "Extra hours per month you'd voluntarily pick up",
        "help": "Capacity for OT, not a commitment.",
        "min": 0, "max": 60, "default": 8, "suffix": "hours",
    },
]


def render() -> None:
    header(
        "Trade-offs",
        "Real schedules force compromises. Use the sliders to tell us where your "
        "line is — there's no right answer, just yours.",
    )

    results: dict[str, int] = {}

    for q in QUESTIONS:
        st.markdown(
            f'<div class="np-card" style="margin-bottom:12px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
            f'gap:18px;margin-bottom:6px;">'
            f'<div style="font-size:14px;font-weight:600;color:{FG};">{q["title"]}</div>'
            f'</div>'
            f'<div class="np-muted" style="margin-bottom:8px;">{q["help"]}</div>',
            unsafe_allow_html=True,
        )
        val = st.slider(
            q["title"],
            min_value=q["min"], max_value=q["max"], value=q["default"],
            key=f"slider_{q['key']}",
            label_visibility="collapsed",
        )
        suffix = f" {q['suffix']}" if q["suffix"] else ""
        st.markdown(
            f'<div style="text-align:right;font-size:13px;color:{MUTED_FG};'
            f'margin-top:-6px;">'
            f'Your answer: <span class="np-strong">{val}{suffix}</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
        results[q["key"]] = val

    st.divider()

    st.markdown(
        '<div class="np-section-title">Forced choices</div>',
        unsafe_allow_html=True,
    )

    forced = {}
    forced["working_christmas"] = st.radio(
        "If you had to work either Christmas Day or New Year's Eve, which?",
        options=["Christmas Day", "New Year's Eve", "I'd swap with someone else"],
        horizontal=True,
        key="forced_holiday",
    )
    forced["double_or_split"] = st.radio(
        "Pick one: a 12-hour double-shift OR two split 6-hour shifts the same day.",
        options=["12-hour double", "Two 6-hour splits", "Neither, refuse"],
        horizontal=True,
        key="forced_double",
    )
    forced["short_notice"] = st.radio(
        "How short is too short for a shift-change request?",
        options=["< 24 hrs", "< 48 hrs", "< 1 week", "Anything is fine"],
        horizontal=True,
        key="forced_notice",
    )

    with st.expander("Anything else we should know about your trade-offs?"):
        st.text_area(
            "Free text",
            key="tradeoff_freeform",
            label_visibility="collapsed",
            placeholder="e.g. 'I can do back-to-back nights but not after a "
                        "holiday weekend.'",
        )

    payload = {
        "sliders": results,
        "forced_choices": forced,
        "freeform": st.session_state.get("tradeoff_freeform", ""),
    }

    st.download_button(
        "Download my trade-offs (JSON)",
        data=json.dumps(payload, indent=2),
        file_name="tradeoffs.json",
        mime="application/json",
    )
