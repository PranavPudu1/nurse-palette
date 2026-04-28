"""Welcome / overview tab."""
import streamlit as st

from theme import header, FG, BORDER
from i18n import t


def render() -> None:
    header(t("welcome.title"), t("welcome.body"))

    cards = [
        ("welcome.card.background", "welcome.minutes.5"),
        ("welcome.card.compare",    "welcome.minutes.3"),
        ("welcome.card.rank",       "welcome.minutes.2"),
        ("welcome.card.ideal",      "welcome.minutes.5"),
        ("welcome.card.tradeoffs",  "welcome.minutes.2"),
        ("welcome.card.day_prefs",  "welcome.minutes.3"),
    ]

    cols = st.columns(3, gap="medium")
    for i, (base, time_key) in enumerate(cards):
        with cols[i % 3]:
            st.markdown(
                f'<div class="np-card" style="height:100%;margin-bottom:14px;">'
                f'<div class="np-section-title">{t(time_key)}</div>'
                f'<div style="font-size:16px;font-weight:600;color:{FG};margin-bottom:6px;">'
                f'{t(base + ".title")}</div>'
                f'<div class="np-muted">{t(base + ".body")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        f'<div class="np-muted" style="border-top:1px solid {BORDER};padding-top:16px;'
        f'margin-top:18px;">{t("welcome.privacy")}</div>',
        unsafe_allow_html=True,
    )
