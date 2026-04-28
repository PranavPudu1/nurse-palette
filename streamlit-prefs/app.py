"""Nurse preference elicitation — single page, tabbed.

Run with:
    cd streamlit-prefs
    streamlit run app.py
"""
import streamlit as st

from theme import setup_page, legend_html, FG, MUTED_FG
from i18n import t, language_picker
from views import welcome, background, compare, rank, ideal, tradeoffs, day_prefs

setup_page("Preferences", icon="🩺")

# Top bar — title left, language picker right.
top_left, top_right = st.columns([7, 1.4])
with top_left:
    st.markdown(
        f'<div style="font-size:22px;font-weight:600;color:{FG};letter-spacing:-0.01em;">'
        f'{t("app.title")}</div>',
        unsafe_allow_html=True,
    )
with top_right:
    language_picker()

with st.sidebar:
    st.markdown(
        f'<div style="font-weight:600;font-size:16px;color:{FG};margin-bottom:4px;">'
        f'{t("app.title")}</div>'
        f'<div style="color:{MUTED_FG};font-size:12px;margin-bottom:18px;">'
        f'{t("app.subtitle")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(legend_html(lambda c: t(f"shift.{c}")), unsafe_allow_html=True)
    st.divider()
    nurse_name = st.text_input(t("app.your_name"),
                               value=st.session_state.get("nurse_name", ""))
    st.session_state["nurse_name"] = nurse_name

tabs = st.tabs([
    t("tab.welcome"),
    t("tab.background"),
    t("tab.compare"),
    t("tab.rank"),
    t("tab.ideal"),
    t("tab.tradeoffs"),
    t("tab.day_prefs"),
])

with tabs[0]: welcome.render()
with tabs[1]: background.render()
with tabs[2]: compare.render()
with tabs[3]: rank.render()
with tabs[4]: ideal.render()
with tabs[5]: tradeoffs.render()
with tabs[6]: day_prefs.render()
