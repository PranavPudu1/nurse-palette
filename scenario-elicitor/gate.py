"""Entry gate: access code, demographics, and resume-later.

Runs before the wizard. State lives under a resp_ prefix (separate from the
wizard's sb_ keys, so "Start over" resets answers without losing identity).

Access codes: ACCESS_CODE env (default HAILAB25) starts a real session; the
literal code TEST starts a test-mode session flagged is_test=1 and excluded
from analysis. Resume: the 6-character code shown at entry restores the saved
session state.

There is also a codeless side door for the capstone poster: the "Capstone
Poster" button creates a flagged demo session in one click, skipping the code
and the demographics form (see _begin_demo).
"""
from __future__ import annotations

import os

import streamlit as st

from theme import header, section, FG, MUTED_FG
import conditions
import store

AGE_RANGES = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
GENDERS = ["Prefer not to say", "Woman", "Man", "Non-binary", "Self-described"]
# Child age bands follow Driscoll et al.'s developmental groups.
CHILD_AGES = ["Not applicable", "6-8", "9-12", "13-15", "16-18"]


def _access_code() -> str:
    return os.environ.get("ACCESS_CODE", "HAILAB25").strip().upper()


def _capture_prolific() -> None:
    """Pick up Prolific's URL params once (standard integration: the study URL
    carries PROLIFIC_PID). resp_pid survives in session state afterwards."""
    ss = st.session_state
    if ss.get("_resp_qp_done"):
        return
    ss["_resp_qp_done"] = True
    try:
        qp = st.query_params
        pid = (qp.get("PROLIFIC_PID") or "").strip()
        if pid:
            ss["resp_pid"] = pid
        if pid or (qp.get("src") or "").lower() == "prolific":
            ss["resp_prolific_mode"] = True
    except Exception:
        pass


def _begin_new() -> None:
    ss = st.session_state
    name = (ss.get("gate_name") or "").strip()
    if not name:
        ss["_gate_error"] = "Please enter a name or initials."
        return
    pid = (ss.get("resp_pid") or (ss.get("gate_pid") or "").strip())
    if ss.get("resp_prolific_mode") and not pid:
        ss["_gate_error"] = "Please enter your Prolific ID."
        return
    child_age = ss.get("gate_child", CHILD_AGES[0])
    # Balanced across arms rather than an independent coin flip per person: with
    # a noisy outcome and small cells, equal cell sizes matter more than
    # independence. Test sessions are excluded from the counts.
    cond = conditions.assign_arm(store.condition_counts())
    rid, code = store.create_respondent(
        name=name,
        age_range=ss.get("gate_age", ""),
        gender=ss.get("gate_gender", ""),
        ai_familiarity=int(ss.get("gate_ai", 3)),
        occupation=(ss.get("gate_occ") or "").strip(),
        child_age="" if child_age == CHILD_AGES[0] else child_age,
        prolific_id=pid,
        is_test=bool(ss.get("resp_test")),
        condition=cond,
    )
    ss["resp_id"] = rid
    ss["resp_code"] = code
    ss["resp_name"] = name
    ss["sb_condition"] = cond
    # Seed the audience so the cases are concrete about the child from the start.
    if child_age != CHILD_AGES[0]:
        # Carried so the next page can prefill rather than ask again. It used to
        # only seed a free-text audience field, which the participant then had
        # to answer a second time in their own words.
        ss["resp_child_age"] = child_age
        if not (ss.get("sb_audience") or "").strip():
            ss["sb_audience"] = f"my child, age {child_age}"
    ss.pop("_gate_error", None)
    store.log_event(rid, "gate", "session_start",
                    {"is_test": bool(ss.get("resp_test")),
                     "prolific": bool(pid), "child_age": child_age,
                     "condition": cond})
    # Logged separately so the arm is recoverable from the event stream even if
    # the respondents row or the snapshot is ever lost.
    store.log_event(rid, "gate", "condition_assign", {"condition": cond})


def _resume() -> None:
    ss = st.session_state
    code = (ss.get("gate_resume") or "").strip().upper()
    row = store.get_by_code(code)
    if not row:
        ss["_gate_error"] = "No session found for that code."
        return
    snap = store.load_snapshot(row["id"])
    for k, v in snap.items():
        ss[k] = v
    ss["resp_id"] = row["id"]
    ss["resp_code"] = row["resume_code"]
    ss["resp_name"] = row["name"] or ""
    ss["resp_test"] = bool(row["is_test"])
    ss["resp_submitted"] = bool(row["submitted_at"])
    # The stored arm wins over anything in the snapshot, so a session always
    # resumes into the sequence it was assigned.
    ss["sb_condition"] = row.get("condition") or conditions.DEFAULT_ARM
    if row.get("completion_code"):
        ss["resp_completion"] = row["completion_code"]
    if row.get("prolific_id"):
        ss["resp_pid"] = row["prolific_id"]
    ss.pop("_gate_error", None)
    store.log_event(row["id"], "gate", "session_resume", {})


def _begin_demo() -> None:
    """One-click entry for someone standing at the capstone poster.

    Skips both the access code and the demographics form: a poster visitor has
    seconds, not minutes. The session is created directly (ready() gates on
    resp_id, not resp_gate_ok), flagged is_test so it never counts as study
    data, and tagged source=poster in the session_start event so poster traffic
    stays separable from TEST sessions in the log.
    """
    ss = st.session_state
    # Not randomised: a poster visitor should see the fullest version of the
    # pipeline, not whichever baseline the balancer happens to hand out. Study
    # arms are assigned in _begin_new only. STUDY_ARM still overrides for demos.
    cond = conditions._forced_arm() or conditions.DEFAULT_ARM
    rid, code = store.create_respondent(
        name="Capstone poster visitor",
        age_range="", gender="", ai_familiarity=3, occupation="",
        child_age="", prolific_id="", is_test=True, condition=cond,
    )
    ss["sb_condition"] = cond
    ss["resp_gate_ok"] = True
    ss["resp_test"] = True
    ss["resp_demo"] = True
    ss["resp_id"] = rid
    ss["resp_code"] = code
    ss["resp_name"] = "Capstone poster visitor"
    # Seed an audience so the cases are concrete from the first screen; with no
    # demographics form there is nothing else to derive it from.
    if not (ss.get("sb_audience") or "").strip():
        ss["sb_audience"] = "my child, age 9-12"
    ss["resp_child_age"] = "9-12"
    ss.pop("_gate_error", None)
    store.log_event(rid, "gate", "session_start",
                    {"is_test": True, "prolific": False, "child_age": "",
                     "source": "poster", "condition": cond})
    store.log_event(rid, "gate", "condition_assign",
                    {"condition": cond, "source": "poster"})


def _check_code() -> None:
    ss = st.session_state
    entered = (ss.get("gate_code") or "").strip().upper()
    admin = os.environ.get("ADMIN_CODE", "").strip().upper()
    if entered == "TEST":
        ss["resp_gate_ok"] = True
        ss["resp_test"] = True
        ss.pop("_gate_error", None)
    elif entered == _access_code():
        ss["resp_gate_ok"] = True
        ss["resp_test"] = False
        ss.pop("_gate_error", None)
    elif admin and entered == admin:
        ss["resp_admin"] = True
        ss.pop("_gate_error", None)
    else:
        ss["_gate_error"] = "That access code is not recognized."


def _render_admin() -> None:
    """Verification sheet: who participated, their Prolific ID and completion
    code, and whether they submitted. Used to approve people on Prolific."""
    header("Respondents", "Verification view. Compare completion codes against "
                          "Prolific submissions, then approve there.")
    rows = store.list_respondents()
    if not rows:
        st.info("No respondents yet.")
        return
    st.dataframe(rows, use_container_width=True)
    csv_lines = ["respondent_id,name,prolific_id,completion_code,resume_code,"
                 "created_at,submitted_at,is_test,condition,child_age"]
    for r in rows:
        csv_lines.append(",".join(str(r.get(k) if r.get(k) is not None else "")
                                  .replace(",", " ")
                                  for k in ("id", "name", "prolific_id",
                                            "completion_code", "resume_code",
                                            "created_at", "submitted_at",
                                            "is_test", "condition", "child_age")))
    st.download_button("Download CSV", data="\n".join(csv_lines),
                       file_name="respondents.csv", mime="text/csv")


def ready() -> bool:
    """True when a respondent session is active; otherwise renders the gate."""
    ss = st.session_state
    _capture_prolific()
    if ss.get("resp_admin"):
        _render_admin()
        return False
    if ss.get("resp_id"):
        if ss.get("resp_demo"):
            st.info("Poster demo. Try anything you like; nothing here goes into "
                    "the study.")
        elif ss.get("resp_test"):
            st.info("Test mode: this session is flagged as a test and excluded "
                    "from analysis.")
        return True

    if not ss.get("resp_gate_ok"):
        header("Welcome",
               "This is a research study session. Enter the access code you were "
               "given to begin.")
        st.text_input("Access code", key="gate_code", max_chars=20,
                      help="The code from your invitation. Enter TEST to try the "
                           "tool without contributing data.")
        st.button("Enter", on_click=_check_code)
        if ss.get("_gate_error"):
            st.error(ss["_gate_error"])
        # Visitors arriving from the capstone poster have no code. Separated by
        # a divider so it reads as a side door, not part of the study path.
        st.markdown(f'<div style="margin:18px 0 10px;border-top:1px solid #E5DCCC;'
                    f'padding-top:14px;color:{MUTED_FG};font-size:14px;">'
                    f'Here from the capstone poster?</div>',
                    unsafe_allow_html=True)
        st.button("Capstone Poster", key="gate_demo", type="secondary",
                  on_click=_begin_demo,
                  help="Try the pipeline right now. No code needed, and nothing "
                       "you enter is used in the study.")
        return False

    header("Before you start",
           "A few details for the study, then you can begin. Or resume a "
           "previous session with your code.")
    left, right = st.columns([1.3, 1], gap="large")
    with left:
        section("Start a new session")
        if ss.get("resp_prolific_mode") and not ss.get("resp_pid"):
            st.text_input("Prolific ID", key="gate_pid", max_chars=32,
                          help="Your 24-character Prolific ID, so we can approve "
                               "your submission.")
        elif ss.get("resp_pid"):
            st.caption(f"Prolific ID captured: {ss['resp_pid']}")
        st.text_input("Name or initials", key="gate_name", max_chars=60)
        st.selectbox("Age range", AGE_RANGES, key="gate_age")
        st.selectbox("Your child's age group (if applicable)", CHILD_AGES,
                     key="gate_child",
                     help="If you are setting up an agent for your child, their "
                          "age keeps the cases realistic for them.")
        st.selectbox("Gender (optional)", GENDERS, key="gate_gender")
        st.slider("How familiar are you with AI tools?", 1, 5, 3, key="gate_ai",
                  help="1 = not at all familiar, 5 = very familiar")
        st.text_input("Occupation (optional)", key="gate_occ", max_chars=80)
        st.button("Begin", on_click=_begin_new, type="primary")
    with right:
        section("Resume a session")
        st.markdown('<div class="np-sub" style="margin-bottom:8px;">Enter the '
                    '6-character code you were shown when you started.</div>',
                    unsafe_allow_html=True)
        st.text_input("Resume code", key="gate_resume", max_chars=6)
        st.button("Resume", on_click=_resume, type="secondary")
    if ss.get("_gate_error"):
        st.error(ss["_gate_error"])
    return False


def badge() -> None:
    """Small footer with the resume code, shown on every step."""
    ss = st.session_state
    if ss.get("resp_code"):
        st.markdown(
            f'<div style="font-size:12px;color:{MUTED_FG};margin-top:6px;">'
            f'Your resume code: <b style="color:{FG};">{ss["resp_code"]}</b>. '
            f'Save it to continue this session later.</div>',
            unsafe_allow_html=True)
