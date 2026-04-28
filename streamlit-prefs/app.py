"""Nurse preference elicitation — single page, tabbed.

Run with:
    cd streamlit-prefs
    streamlit run app.py
"""
import streamlit as st

from theme import setup_page, legend_html, FG, MUTED_FG
from views import welcome, compare, rank, ideal, tradeoffs, day_prefs

setup_page("Preferences", icon="🩺")

with st.sidebar:
    st.markdown(
        f'<div style="font-weight:600;font-size:16px;color:{FG};margin-bottom:4px;">'
        f'Nurse Preferences</div>'
        f'<div style="color:{MUTED_FG};font-size:12px;margin-bottom:18px;">'
        f'Help us learn what makes a great schedule for you.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(legend_html(), unsafe_allow_html=True)
    st.divider()
    nurse_name = st.text_input("Your name",
                               value=st.session_state.get("nurse_name", ""))
    st.session_state["nurse_name"] = nurse_name

tab_titles = [
    "Welcome",
    "1 · Compare",
    "2 · Rank",
    "3 · Build ideal",
    "4 · Trade-offs",
    "5 · Day prefs",
]
tabs = st.tabs(tab_titles)

with tabs[0]: welcome.render()
with tabs[1]: compare.render()
with tabs[2]: rank.render()
with tabs[3]: ideal.render()
with tabs[4]: tradeoffs.render()
with tabs[5]: day_prefs.render()
