"""Scenario Elicitor: set preferences for how an AI agent should behave.

A person walks through five screens (agent, describe, situations, choose, output)
and the tool produces a personalized benchmark of (situation, chosen behavior,
rejected behavior). This is the scenario-based pipeline, sibling to the
feature-based preference-elicitor.

Run with:
    cd scenario-elicitor
    streamlit run app.py
"""
import streamlit as st

from theme import setup_page, FG, MUTED_FG
import gate
import llm
import store
import wizard

setup_page("Scenario Elicitor")


def _reset_all() -> None:
    for k in list(st.session_state.keys()):
        if k.startswith("sb_") or k.startswith("_sb_"):
            del st.session_state[k]
    rid = st.session_state.get("resp_id")
    if rid:
        store.log_event(rid, "app", "restart", {})


top_left, top_right = st.columns([7, 2])
with top_left:
    st.markdown(
        f'<div class="np-app-title" style="font-size:25px;color:{FG};">Scenario '
        f'Elicitor</div>'
        f'<div style="color:{MUTED_FG};font-size:13px;">Teach an AI agent how to '
        f'behave by reacting to concrete situations.</div>', unsafe_allow_html=True)
with top_right:
    st.button("Start over", use_container_width=True, type="secondary",
              on_click=_reset_all)

if not llm.is_configured():
    st.info("Demo mode: no OpenAI key found, so the pipeline runs on deterministic "
            "placeholder output. Add a key to .env.local to use the live model.")

st.write("")
if not gate.ready():
    st.stop()
wizard.render()
gate.badge()
