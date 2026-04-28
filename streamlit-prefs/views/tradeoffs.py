"""Trade-off sliders view — minimalistic."""
import json
import streamlit as st

from theme import header, FG, MUTED_FG, BORDER, PRIMARY
from i18n import t

# Each entry: (key, min, max, default, suffix_key)
# team_alignment_weight + overtime_appetite were dropped — they duplicate
# Background Q7 (team importance) and Q4 (volume / stance) respectively.
QUESTIONS = [
    ("consec_nights_max",          1,  7,  3, "nights"),
    ("weekend_off_freq",           0,  4,  2, "weekends"),
    ("extra_nights_for_weekend",   0,  5,  1, "extra"),
    ("min_rest_hours",             8, 24, 11, "hours"),
    ("predictability_vs_choice",   0,100, 50, ""),
]

SUFFIX = {
    "nights":   {"en": "nights",       "ko": "일"},
    "weekends": {"en": "weekends",     "ko": "회"},
    "extra":    {"en": "extra nights", "ko": "추가"},
    "hours":    {"en": "hours",        "ko": "시간"},
    "":         {"en": "",             "ko": ""},
}


def _suffix(key: str) -> str:
    from i18n import get_lang
    return SUFFIX.get(key, {}).get(get_lang(), SUFFIX.get(key, {}).get("en", ""))


def render() -> None:
    header(t("trade.title"), t("trade.subtitle"))

    results: dict[str, int] = {}

    for q_key, q_min, q_max, q_default, suffix_key in QUESTIONS:
        title = t(f"trade.q.{q_key}")
        helptext = t(f"trade.q.{q_key}.h")

        # Compact row — title + slider + readout pill.
        st.markdown(
            f'<div style="font-size:14px;font-weight:600;color:{FG};margin:14px 0 2px;">'
            f'{title}</div>'
            f'<div class="np-muted" style="margin-bottom:6px;">{helptext}</div>',
            unsafe_allow_html=True,
        )
        slider_col, readout_col = st.columns([5, 1.2])
        with slider_col:
            val = st.slider(
                title,
                min_value=q_min, max_value=q_max, value=q_default,
                key=f"slider_{q_key}",
                label_visibility="collapsed",
            )
        with readout_col:
            sfx = _suffix(suffix_key)
            sfx_str = f" {sfx}" if sfx else ""
            st.markdown(
                f'<div style="margin-top:8px;text-align:center;'
                f'background:#EAF1FA;color:{PRIMARY};border-radius:8px;'
                f'padding:6px 0;font-weight:700;font-size:13px;">'
                f'{val}{sfx_str}</div>',
                unsafe_allow_html=True,
            )
        results[q_key] = val

    st.divider()

    st.markdown(
        f'<div class="np-section-title">{t("trade.forced")}</div>',
        unsafe_allow_html=True,
    )

    forced = {}
    forced["working_christmas"] = st.radio(
        t("trade.f.holiday.q"),
        options=[t("trade.f.holiday.a1"), t("trade.f.holiday.a2"), t("trade.f.holiday.a3")],
        horizontal=True, key="forced_holiday",
    )
    forced["double_or_split"] = st.radio(
        t("trade.f.double.q"),
        options=[t("trade.f.double.a1"), t("trade.f.double.a2"), t("trade.f.double.a3")],
        horizontal=True, key="forced_double",
    )
    forced["short_notice"] = st.radio(
        t("trade.f.notice.q"),
        options=[t("trade.f.notice.a1"), t("trade.f.notice.a2"),
                 t("trade.f.notice.a3"), t("trade.f.notice.a4")],
        horizontal=True, key="forced_notice",
    )

    with st.expander(t("trade.freeform_label")):
        st.text_area(
            t("trade.freeform_label"),
            key="tradeoff_freeform", label_visibility="collapsed",
            placeholder=t("trade.freeform_ph"),
        )

    payload = {
        "sliders": results,
        "forced_choices": forced,
        "freeform": st.session_state.get("tradeoff_freeform", ""),
    }

    st.download_button(
        t("trade.download"),
        data=json.dumps(payload, indent=2, ensure_ascii=False),
        file_name="tradeoffs.json",
        mime="application/json",
    )
