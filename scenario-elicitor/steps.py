"""The six screen bodies for the scenario wizard.

Reads and writes st.session_state under an sb_ prefix and reuses the theme
helpers. Generative screens call the LLM lazily on first entry and cache the
result. Text inputs mirror into stable non-widget keys so values survive step
navigation (Streamlit clears widget keys when their widget leaves the page).

Flow: agent -> describe (+ who it is for) -> concrete cases -> author the ideal
behavior per case (rubric-guided co-writing) -> confirm with concrete pairwise
comparisons -> review, submit, download or email the benchmark.
"""
from __future__ import annotations

import os

import streamlit as st

from theme import (header, section, FG, MUTED_FG, PRIMARY, ACCENT, BORDER,
                   SURFACE_BG)
import export
import llm
import mailer
import prompts
import provenance
import store
import wizard


def _rid() -> str:
    return st.session_state.get("resp_id", "")


def _goto(key: str) -> None:
    """Jump to a step by key. Safe if this arm does not contain it."""
    wizard.goto_key(key)


# Domain-general, AI-behavior example chips.
# The domain-general agent chips. Retained deliberately: the study is locked to
# the kids' content filter (see domain_locked), and setting DOMAIN_LOCK=off brings
# this picker, and the general case prompts, straight back.
EXAMPLES = [
    {"label": "Scheduling assistant",
     "value": "An AI that manages my work shifts and swaps"},
    {"label": "Kids' content filter",
     "value": "An AI that curates news and content for my child"},
    {"label": "Writing assistant",
     "value": "An AI that drafts and edits my writing"},
    {"label": "Email assistant",
     "value": "An AI that triages and replies to my email"},
]


def _does() -> str:
    return (st.session_state.sb_frame or {}).get("does", "")


def _mock_note(data: dict) -> None:
    if data.get("_error"):
        with st.expander("Model error (showing a fallback)"):
            st.code(data["_error"])
    if data.get("_mock"):
        st.caption("Demo mode: no API key found, so these are placeholder results.")


# ---------------------------------------------------------------------------
# Step 0: Agent
# ---------------------------------------------------------------------------

def _set_example(value: str) -> None:
    st.session_state.sb_agent = value
    st.session_state.sb_agent_input = value
    st.session_state.sb_frame = None


def domain_locked() -> bool:
    """The study runs one domain: everyone configures the kids' content filter.

    The domain-general picker (other agent types, free text) is kept in the code
    and comes back by setting DOMAIN_LOCK=off, so nothing is lost.
    """
    return os.environ.get("DOMAIN_LOCK", "kids").strip().lower() != "off"


def render_agent() -> None:
    ss = st.session_state
    if domain_locked():
        ss.sb_agent = prompts.KIDS_AGENT
        header("The agent you are setting up",
               "In this study everyone works with the same agent, so answers can be "
               "compared. You will teach it how to behave by reacting to concrete "
               "situations it would face with your child.")
        st.markdown(
            f'<div class="np-card" style="margin-bottom:12px;">'
            f'<div class="np-section-title">The agent</div>'
            f'<div style="font-size:20px;font-weight:700;color:{FG};'
            f'margin-bottom:6px;">An AI that curates news and content for my child</div>'
            f'<div class="np-sub">It decides what reaches your child and how things '
            f'get explained: which videos and articles come through, how questions '
            f'about the news get answered, and when you should be told.</div></div>',
            unsafe_allow_html=True)
        st.caption("Next you will say who it is for and how you want it to behave.")
        return

    header("What AI or agent are you setting preferences for?",
           "You will teach it how to behave on your behalf, by reacting to concrete "
           "cases. It can be any agent, in any domain.")
    section("Examples")
    cols = st.columns(len(EXAMPLES))
    for col, ex in zip(cols, EXAMPLES):
        col.button(ex["label"], key=f"sb_ex_{ex['label']}", use_container_width=True,
                   type="secondary", on_click=_set_example, args=(ex["value"],))
    st.write("")
    st.session_state.setdefault("sb_agent_input", st.session_state.sb_agent)
    st.text_input("The agent", key="sb_agent_input",
                  placeholder="e.g. an AI that manages my work shifts",
                  help="Name the AI or agent whose behavior you want to shape. It "
                       "can be anything: a scheduler, a content filter, a writing "
                       "helper, an email triager.")
    if st.session_state.sb_agent != st.session_state.sb_agent_input:
        st.session_state.sb_agent = st.session_state.sb_agent_input
        st.session_state.sb_frame = None


# ---------------------------------------------------------------------------
# Step 1: Describe (how it should behave + who it is for)
# ---------------------------------------------------------------------------

def render_describe() -> None:
    """One page: who the child is, then two questions about them.

    This used to open with a restatement of the agent, a card explaining what
    the next step would do, a free-text "who is this agent for", and an optional
    "how it should behave" box. The age was already collected at sign-up, so the
    audience question asked the same thing twice, and none of the explanatory
    text told the person anything they needed in order to answer.

    What is left is the two things we do not already know, and the questions.
    """
    ss = st.session_state
    if ss.sb_frame is None and ss.sb_agent.strip():
        with st.spinner("Reading the agent..."):
            ss.sb_frame = llm.frame_agent(ss.sb_agent)

    header("About your child",
           "So the situations we show you are about the right child.")

    known = (ss.get("resp_child_age") or "").strip()
    ages = ["6-8", "9-12", "13-15", "16-18"]
    ss.setdefault("sb_age_input", known if known in ages else "9-12")
    c1, c2 = st.columns([1, 1.4], gap="medium")
    with c1:
        st.selectbox("How old is your child?", ages, key="sb_age_input",
                     index=ages.index(ss["sb_age_input"]))
    with c2:
        st.text_input("Their name, if you want to use it", key="sb_name_input",
                      placeholder="optional")

    name = (ss.get("sb_name_input") or "").strip()
    age = ss.get("sb_age_input") or "9-12"
    # The name, when given, goes into the audience string so the generated
    # situations say "Maya asks..." rather than "the child asks...". That is the
    # whole reason to collect it.
    ss.sb_audience = (f"{name}, my child, age {age}" if name
                      else f"my child, age {age}")

    _render_intake_questions()
    slots = _intake_slots()
    missing = [k for k, _ in slots if not _answered(k)]
    if slots and missing:
        st.caption(_needs(len(missing), len(slots)))


def _intake_slots() -> list[tuple[str, str]]:
    qs = st.session_state.get("sb_rqi") or []
    return [(f"sb_rai_{i}", _TYPE_NAMES.get((q.get("type") or "").strip(),
                                            "Reflect"))
            for i, q in enumerate(qs) if (q.get("question") or "").strip()]


def _intake_answers() -> list[dict]:
    ss = st.session_state
    out = []
    for i, q in enumerate(ss.get("sb_rqi") or []):
        ans = (ss.get(f"sb_rai_{i}") or "").strip()
        if ans:
            out.append({"placement": "intake", "type": (q.get("type") or "").strip(),
                        "question": q.get("question", ""), "answer": ans})
    return out


def _render_intake_questions() -> None:
    """Two questions asked here, before any case has been generated.

    Everywhere else the questions hang off a concrete situation, which means the
    first thing a participant considers is a case we wrote. These come first and
    are about them and their child, so what they bring to the cases is their
    own.
    """
    ss = st.session_state
    who = (ss.get("sb_audience") or "").strip()
    if not who:
        return          # nothing to ask about until they say who this is for
    if "sb_rqi" not in ss:
        with st.spinner("Preparing two questions..."):
            rq = llm.reflect_intake(ss.sb_agent, _does(), who)
        ss["sb_rqi"] = rq.get("questions") or []
        store.log_event(_rid(), "describe", "reflect_intake",
                        {"questions": ss["sb_rqi"]})
    if not ss["sb_rqi"]:
        return
    st.write("")
    section("Before we start")
    st.caption("Two questions about you and your child, before you see any "
               "situations. Answer both to continue.")
    for i, q in enumerate(ss["sb_rqi"]):
        text = (q.get("question") or "").strip()
        if text:
            _render_one_question(f"sb_rai_{i}",
                                 _TYPE_NAMES.get((q.get("type") or "").strip(),
                                                 "Reflect"),
                                 text, "reflect_before")


# ---------------------------------------------------------------------------
# Step 2: Cases (Farsight fan-out, concrete)
# ---------------------------------------------------------------------------

def _ingest_scenarios(data: dict, theme: str = "") -> list[dict]:
    """Normalize generated cases. `theme` overrides whatever category the model
    returned.

    The override matters now that the UI groups by theme. SCENARIOS_SCHEMA types
    `category` as a bare string with no enum, so the model is free to return a
    near-miss like "Missing real meaning", and a near-miss would put the case in
    a bucket that no theme card can reach. When we asked for one theme we already
    know the answer, so we stop asking.
    """
    out = []
    for s in (data.get("scenarios") or []):
        cons = s.get("considerations") or []
        if isinstance(cons, str):
            cons = [cons]
        out.append({"id": wizard.new_id(),
                    "category": (theme or s.get("category") or "General").strip(),
                    "title": (s.get("title") or "Case").strip(),
                    "situation": (s.get("situation") or "").strip(),
                    "at_stake": (s.get("at_stake") or "").strip(),
                    "considerations": [c.strip() for c in cons if c and c.strip()],
                    "analysis": (s.get("analysis") or "").strip(),
                    "kind": (s.get("kind") or "common").strip(),
                    "probe": (s.get("probe") or "").strip(),
                    "example_exchange": {
                        "user_message": ((s.get("example_exchange") or {})
                                         .get("user_message") or "").strip(),
                        "ai_response": ((s.get("example_exchange") or {})
                                        .get("ai_response") or "").strip()}})
    return out


def _norm(text: str) -> str:
    return " ".join((text or "").lower().split())


def _append_new(items: list[dict]) -> int:
    """Append only cases not already present (by normalized title/situation)."""
    ss = st.session_state
    existing = ss.sb_scenarios or []
    seen = {_norm(s["title"]) for s in existing} | {_norm(s["situation"]) for s in existing}
    added = 0
    for s in items:
        if _norm(s["title"]) in seen or _norm(s["situation"]) in seen:
            continue
        existing.append(s)
        seen.add(_norm(s["title"]))
        seen.add(_norm(s["situation"]))
        added += 1
    ss.sb_scenarios = existing
    return added














def _kind_badge(kind: str) -> str:
    if kind not in ("edge_case", "surprising"):
        return ""
    label = "Non-obvious" if kind == "surprising" else "Edge case"
    return (f'<span style="display:inline-block;white-space:nowrap;padding:2px 9px;'
            f'border-radius:999px;background:{ACCENT};color:{FG};font-size:10px;'
            f'font-weight:700;letter-spacing:0.04em;text-transform:uppercase;">'
            f'{label}</span>')




def _situation_card(s: dict) -> str:
    """A concrete case: its title, and what happens. Nothing else.

    This card used to carry four more rows: what is at stake, things to weigh,
    how it plays out, and who it affects. All four are gone from the screen, on
    Min's reading that they answered the question for the parent before the
    parent had answered it: "this case is almost giving the answer to the
    participant before they write their own answer." "Things to weigh" was the
    worst of them, since it handed over the exact tradeoff the rule is supposed
    to resolve.

    at_stake and considerations are still generated and still travel: they are
    given to the pre-write question generator as material, so the same content
    now arrives as a question instead of an answer. at_stake is also still
    exported, since it is what makes a benchmark row usable.
    """
    badge = _kind_badge(s.get("kind", ""))
    return (
        f'<div class="np-card" style="margin-bottom:12px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-'
        f'start;gap:8px;"><div style="font-weight:700;color:{FG};">{s["title"]}'
        f'</div>'
        f'{badge}</div>'
        f'<div class="np-sub" style="margin-top:4px;">{s["situation"]}</div></div>')


def _who() -> str:
    return (st.session_state.get("sb_audience") or "").strip() or "the person"


def _render_example_chat(scenario: dict, key: str = "") -> None:
    """The case as an actual conversation, not a description of one.

    Rendered as chat bubbles rather than a muted card so it reads the way the
    moment would really look, and so it matches the chat on the writing screen.
    """
    ex = scenario.get("example_exchange") or {}
    if not (ex.get("user_message") or ex.get("ai_response")):
        return
    st.markdown('<div class="np-section-title">How it comes up</div>',
                unsafe_allow_html=True)
    if ex.get("user_message"):
        with st.chat_message("user"):
            st.markdown(f"**{_who()}**  \n{ex['user_message']}")
    if ex.get("ai_response"):
        with st.chat_message("assistant"):
            st.markdown(f"**The agent today** {provenance.icon('baseline_reply')}  \n"
                        f"{ex['ai_response']}", unsafe_allow_html=True)


# --- the scenario chat: one linear transcript ---------------------------------
# Two testing paths (re-answer under the current rule, and continue the
# conversation to stress-test) plus version-stamped replies follow PolicyPad,
# Feng et al. CHI '26, §5.2.5 and Fig. 8. See docs/provenance.md.
#
# The transcript is a SINGLE ordered list. Render order is list order, so a reply
# can never appear above the message it answers.

def _chat_state(idx: int, scenario: dict) -> dict:
    """{"turns": [{role, content, version?, rule?, what_changed?}, ...]}"""
    ss = st.session_state
    key = f"sb_chat_{idx}"
    if key not in ss:
        ex = scenario.get("example_exchange") or {}
        turns = []
        if ex.get("user_message"):
            turns.append({"role": "user", "content": ex["user_message"]})
        if ex.get("ai_response"):
            turns.append({"role": "assistant", "content": ex["ai_response"],
                          "version": "No rule yet", "rule": "", "what_changed": ""})
        ss[key] = {"turns": turns}
    return ss[key]


def _history_for_model(turns: list[dict]) -> list[dict]:
    """History up to and including the last user message.

    Trailing assistant turns are dropped so a re-test answers the child's last
    question again instead of replying to the agent's own previous answer.
    """
    out = list(turns)
    while out and out[-1]["role"] == "assistant":
        out.pop()
    return out


def _n_tests(turns: list[dict]) -> int:
    """Only explicit "Test my rule" presses are versions.

    Follow-up replies also run under the current rule, but they answer a new
    question rather than re-answering the same one, so they do not bump v-number.
    """
    return sum(1 for t in turns if t.get("tested"))


def _request_test(idx: int) -> None:
    st.session_state["_sb_test"] = idx


def _request_followup(idx: int) -> None:
    msg = (st.session_state.get(f"sb_followup_{idx}") or "").strip()
    if msg:
        st.session_state["_sb_followup"] = (idx, msg)


def _run_test(idx: int, scenario: dict, rule: str) -> None:
    """Answer the child's latest message again under the current rule."""
    ss = st.session_state
    state = _chat_state(idx, scenario)
    turns = state["turns"]
    rule = (rule or "").strip()
    # Nothing to learn from re-running the identical rule on the same question.
    # A follow-up since the last test means there is a new question to answer, so
    # only block when the very last turn is a test with this same rule.
    last = turns[-1] if turns else None
    if (last and last["role"] == "assistant" and last.get("tested")
            and (last.get("rule") or "").strip() == rule):
        st.toast("That is the same rule you just tested. Edit it, then test again.")
        return
    history = _history_for_model(turns)
    with st.spinner("Asking the agent again, following your rule..."):
        data = llm.agent_reply(ss.sb_agent, _does(), ss.sb_audience, scenario,
                               rule, history)
    n = _n_tests(turns) + 1
    turns.append({"role": "assistant", "content": (data.get("response") or "").strip(),
                  "version": f"Your rule v{n}", "rule": rule, "tested": True,
                  "what_changed": (data.get("what_changed") or "").strip(),
                  "_mock": data.get("_mock"), "_error": data.get("_error")})
    store.log_event(_rid(), "respond", "test_rule",
                    {"case_idx": idx, "version": n, "rule": rule,
                     "reply": turns[-1]["content"]})


def _run_followup(idx: int, scenario: dict, rule: str, msg: str) -> None:
    """Continue the conversation to stress-test the current rule."""
    ss = st.session_state
    state = _chat_state(idx, scenario)
    turns = state["turns"]
    rule = (rule or "").strip()
    turns.append({"role": "user", "content": msg})
    with st.spinner("Sending it to the agent..."):
        data = llm.agent_reply(ss.sb_agent, _does(), ss.sb_audience, scenario,
                               rule or None, turns)
    n = _n_tests(turns)
    turns.append({"role": "assistant", "content": (data.get("response") or "").strip(),
                  "version": (f"Following your rule v{n}" if rule and n
                              else ("Following your rule" if rule else "No rule yet")),
                  "rule": rule, "tested": False, "what_changed": "",
                  "_mock": data.get("_mock"), "_error": data.get("_error")})
    store.log_event(_rid(), "respond", "continue_chat",
                    {"case_idx": idx, "message": msg, "reply": turns[-1]["content"]})


def _render_scenario_chat(idx: int, scenario: dict) -> None:
    state = _chat_state(idx, scenario)
    turns = state["turns"]

    section("The conversation")
    st.caption("How this plays out. Write your rule below, then test it and watch "
               "the agent answer again.")
    for t in turns:
        if t["role"] == "user":
            with st.chat_message("user"):
                st.markdown(f"**{_who()}**  \n{t['content']}")
        else:
            _mock_note(t)
            with st.chat_message("assistant"):
                ikey = "rule_reply" if (t.get("rule") or "").strip() else "baseline_reply"
                st.markdown(f"**{t.get('version', 'The agent')}** "
                            f"{provenance.icon(ikey)}  \n{t['content']}",
                            unsafe_allow_html=True)
                if t.get("what_changed"):
                    st.caption(f"What your rule changed: {t['what_changed']}")
    st.text_input("Keep chatting", key=f"sb_followup_{idx}",
                  placeholder=f"Type what {_who()} says next, to test your rule "
                              f"further...",
                  label_visibility="collapsed",
                  on_change=_request_followup, args=(idx,))




# ---------------------------------------------------------------------------
# Step 3: Respond (co-writing: draft -> rubric feedback -> optional apply)
# ---------------------------------------------------------------------------



def _flag(name: str) -> None:
    st.session_state[name] = True


def _levels_by_name(fb: dict) -> dict:
    return {c.get("name", ""): int(c.get("level", 1))
            for c in (fb or {}).get("criteria", [])}


def _record_answer(scenario: dict, theme: str = "",
                   case_ids: list[int] | None = None) -> None:
    """Save the rule. One row per THEME now, not one per case.

    Revisiting a theme replaces its row rather than appending a second one, so
    "revise this rule" from the menu cannot produce two rules for one theme.
    """
    ss = st.session_state
    idx = ss.sb_idx
    val = (ss.get(f"sb_answer_{idx}") or "").strip()
    if not val:
        return
    live_fb = ss.get(f"sb_fb_{idx}")
    fb = live_fb or ss.get(f"sb_lastfb_{idx}") or {}
    levels = _levels_by_name(fb)
    answer = {
        "theme": theme, "case_ids": list(case_ids or []),
        "scenario_id": scenario["id"], "title": scenario["title"],
        "situation": scenario["situation"], "at_stake": scenario.get("at_stake", ""),
        "ideal_behavior": val,
        "first_draft": ss.get(f"sb_first_{idx}", ""),
        "rubric_levels": levels,
        "rubric_score": prompts.overall_score(ss.sb_rubric, levels) if levels else None,
        # False when the saved text changed after the last check, so the recorded
        # levels describe an earlier draft than the one being saved.
        "levels_current": bool(live_fb),
        "n_revisions": ss.get(f"sb_nrev_{idx}", 0),
        # The test-revise trajectory, read off the transcript: every agent turn
        # with the rule that produced it.
        "rule_versions": [{"label": t.get("version", ""), "rule": t.get("rule", ""),
                           "reply": t.get("content", "")}
                          for t in (ss.get(f"sb_chat_{idx}") or {}).get("turns", [])
                          if t.get("role") == "assistant"],
        "n_tests": _n_tests((ss.get(f"sb_chat_{idx}") or {}).get("turns", [])),
        "transcript": (ss.get(f"sb_chat_{idx}") or {}).get("turns", []),
        "reflection": _reflection_answers(idx)}
    # One row per theme. Rewriting a theme replaces its row rather than adding a
    # second, whether that happens by picking it again from the menu or by
    # revising from the review page.
    prev = next((i for i, a in enumerate(ss.sb_answers)
                 if a.get("theme") == theme), None)
    if prev is not None:
        ss.sb_answers[prev] = answer
        store.log_event(_rid(), "themes", "answer_edit", answer)
    else:
        ss.sb_answers.append(answer)
        store.log_event(_rid(), "themes", "answer_save", answer)




_SCORE_BANDS = [(85, "Excellent", "#2E7D4F"), (70, "Good", "#8A6D1B"),
                (55, "Fair", "#B07A16"), (0, "Needs work", "#B0472F")]


# --- reflective questions (Paul and Elder, research12.pdf) --------------------
# Two placements, per the design: one set under the situation before anything is
# written, one set after the first Check grounded in what the person wrote. These
# ask why the person wants what they want; the rubric separately judges whether
# the rule is specific enough to act on. Answers are required: their purpose is
# to make someone think before writing, and an unanswered question does not do
# that. They also feed the rubric check, so a skipped one silently weakens it.

_TYPE_NAMES = {t["key"]: t["name"] for t in prompts.SOCRATIC_TYPES}


MIN_ANSWER = 3          # characters, enough to reject whitespace and stray keys


def _kept_text(canonical: str, label: str, **kw) -> str:
    """A text box whose contents survive the widget being unmounted.

    Streamlit garbage-collects widget state as soon as a widget stops being
    rendered. The staged layouts move the rule box and the question boxes off
    screen between stages, which silently emptied everything the person had
    typed the moment they pressed Next.

    So the value lives in a plain session key that nothing unmounts, and the
    widget is seeded from it and writes back to it. Every reader elsewhere keeps
    using the plain key and does not need to know a widget was involved.
    """
    ss = st.session_state
    val = st.text_area(label, value=ss.get(canonical, ""), key=f"w_{canonical}",
                       **kw)
    ss[canonical] = val
    return val


def _answered(key: str) -> bool:
    return len((st.session_state.get(key) or "").strip()) >= MIN_ANSWER


def _render_one_question(key: str, label: str, text: str, info_key: str) -> None:
    """A question and a box to answer it in. Nothing else.

    Each question used to sit in a bordered card carrying a pill with its
    Socratic type ("Probing assumptions"), a provenance icon, and a red "needed"
    tag, with the answer box floating underneath. Four pieces of chrome around
    one sentence, and the type name means nothing to a parent: it labels our
    taxonomy, not their task. The type is still recorded in the data, where it
    is actually used.

    What is left is the question, styled as the box's own label so the two read
    as one control, and the box. `label` is kept in the signature because
    callers pass it and _question_slots uses it for validation messages.

    The answer box is a text_area, not a text_input, which showed roughly the
    first eight words and hid the rest behind the cursor.
    """
    st.markdown(f'<div class="np-q">{text}</div>', unsafe_allow_html=True)
    _kept_text(key, text, height=88,
               placeholder="a sentence or two is plenty",
               label_visibility="collapsed")


def _question_slots(idx: int, slot: str) -> list[tuple[str, str]]:
    """(answer key, label) for every question in one slot, in display order.

    Keyed by POSITION, not by Socratic type. Two questions of the same type in
    one slot used to share a single answer box, silently merging two answers
    into one.
    """
    ss = st.session_state
    out = []
    if slot == "b":
        sc = _theme_scenario(idx)
        if (sc.get("probe") or "").strip():
            out.append((f"sb_rap_{idx}", "As you write, consider"))
    key = f"sb_rq{slot}_{idx}"
    for i, q in enumerate(ss.get(key) or []):
        if (q.get("question") or "").strip():
            out.append((f"sb_ra{slot}_{idx}_{i}",
                        _TYPE_NAMES.get((q.get("type") or "").strip(), "Reflect")))
    return out


def _unanswered(idx: int, slot: str) -> list[str]:
    return [label for key, label in _question_slots(idx, slot) if not _answered(key)]


def _needs(n_missing: int, n_total: int) -> str:
    """The message shown when questions are still blank.

    Counts, not names. The names were the Socratic type of each question
    ("Probing assumptions"), which labelled our taxonomy rather than anything on
    screen, so a message listing them pointed at nothing the person could see.
    """
    if not n_missing:
        return ""
    if n_missing == n_total:
        return ("Answer both questions to continue." if n_total == 2
                else f"Answer all {n_total} questions to continue.")
    return ("One question still needs an answer." if n_missing == 1
            else f"{n_missing} questions still need an answer.")


def _render_reflection(idx: int, slot: str, questions: list[dict]) -> None:
    """slot is 'b' (before writing) or 'a' (after the first check)."""
    info_key = "reflect_before" if slot == "b" else "reflect_after"
    for i, q in enumerate(questions or []):
        text = (q.get("question") or "").strip()
        if not text:
            continue
        _render_one_question(f"sb_ra{slot}_{idx}_{i}",
                             _TYPE_NAMES.get((q.get("type") or "").strip(),
                                             "Reflect"), text, info_key)


def _reflection_answers(idx: int) -> list[dict]:
    """Everything the person typed into any of the three sets.

    Used for saving, for the export, and as input to Check and Suggest so what
    they said before writing actually shapes the feedback on what they wrote.
    """
    ss = st.session_state
    out = []
    probe_ans = (ss.get(f"sb_rap_{idx}") or "").strip()
    if probe_ans:
        # The probe belongs to this theme's own case. This used to index the
        # flat scenario list by idx, which is a THEME number, so it reported
        # some unrelated case's probe as the question that was answered.
        out.append({"placement": "before", "type": "probe",
                    "question": (_theme_scenario(idx).get("probe") or "").strip(),
                    "answer": probe_ans})
    for slot, key in (("b", f"sb_rqb_{idx}"), ("a", f"sb_rqa_{idx}")):
        for i, q in enumerate(ss.get(key) or []):
            ans = (ss.get(f"sb_ra{slot}_{idx}_{i}") or "").strip()
            if ans:
                out.append({"placement": "before" if slot == "b" else "after",
                            "type": (q.get("type") or "").strip(),
                            "question": q.get("question", ""), "answer": ans})
    return out


def _render_feedback(fb: dict, rubric: list[dict]) -> None:
    """Weighted score badge + per-criterion Why / Why-not-higher expanders."""
    levels = _levels_by_name(fb)
    score = prompts.overall_score(rubric, levels) if levels else 0
    band, color = next((b, c) for cut, b, c in _SCORE_BANDS if score >= cut)
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:12px;margin:10px 0 6px;">'
        f'<div style="background:{color};color:#fff;border-radius:999px;'
        f'padding:8px 16px;font-weight:700;font-size:15px;">{score:g} / 100</div>'
        f'<div style="color:{color};font-weight:600;">{band}</div>'
        f'<div class="np-muted">weighted across the rubric'
        f'{provenance.icon("rubric")}</div></div>',
        unsafe_allow_html=True)
    weights = {c["name"]: c["weight"] for c in rubric}
    for c in fb.get("criteria", []):
        name, level = c.get("name", ""), int(c.get("level", 1))
        with st.expander(f"{name}: level {level} of 4  ({weights.get(name, '?')}%)"):
            st.markdown(f"**Why level {level}**\n\n{c.get('why', '')}")
            if c.get("why_not_higher"):
                st.markdown(f"**What level {level + 1} would take**\n\n"
                            f"{c['why_not_higher']}")


def _save_rubric_edits() -> None:
    ss = st.session_state
    new_rubric = []
    for i, c in enumerate(ss.sb_rubric):
        name = (ss.get(f"sb_rname_{i}") or c["name"]).strip() or c["name"]
        weight = int(ss.get(f"sb_rweight_{i}", c["weight"]))
        lines = [ln.strip() for ln in
                 (ss.get(f"sb_rlevels_{i}") or "").splitlines() if ln.strip()]
        levels = dict(c["levels"])
        for j, ln in enumerate(lines[:4]):
            levels[str(4 - j)] = ln
        new_rubric.append({"name": name, "weight": weight, "levels": levels})
    total = sum(c["weight"] for c in new_rubric) or 1
    for c in new_rubric:   # normalize so weights always sum to 100
        c["weight"] = round(c["weight"] * 100 / total)
    drift = 100 - sum(c["weight"] for c in new_rubric)
    new_rubric[0]["weight"] += drift
    ss.sb_rubric = new_rubric
    store.log_event(_rid(), "respond", "rubric_edit", {"rubric": new_rubric})


def _render_rubric_editor() -> None:
    ss = st.session_state
    with st.expander("View or adjust the rubric"):
        st.caption("Your answers are checked against this rubric. Edit anything: "
                   "names, weights, or the level descriptions (top line = level 4, "
                   "best). Weights are normalized to 100.")
        with st.form("sb_rubric_form"):
            for i, c in enumerate(ss.sb_rubric):
                col1, col2 = st.columns([3, 1], gap="small")
                col1.text_input("Criterion", value=c["name"], key=f"sb_rname_{i}")
                col2.number_input("Weight %", min_value=0, max_value=100,
                                  value=int(c["weight"]), key=f"sb_rweight_{i}")
                st.text_area("Levels 4 to 1, one per line",
                             value="\n".join(c["levels"][str(v)]
                                             for v in range(4, 0, -1)),
                             key=f"sb_rlevels_{i}", height=110)
            st.form_submit_button("Save rubric", on_click=_save_rubric_edits)




# ---------------------------------------------------------------------------
# Steps 3 and 4, merged: pick a theme, then write one rule for it
# ---------------------------------------------------------------------------
# Cases used to arrive as one undifferentiated list of six, each getting its own
# rule. They now arrive under a theme, three at a time, and a theme gets ONE
# rule. The point is the claim it lets us make: a participant authors a general
# principle and then sees it tested against concrete cases, rather than writing
# six local reactions that never generalise.
#
# One step key, two modes. `sb_theme` is None on the menu and set inside a
# theme; `sb_tphase` moves a theme from writing its rule to the comparisons that
# test it. People move between menu and workspace three times, which is a loop
# inside one step rather than forward travel, so it is not two wizard steps.

N_THEME_CMPS = 2      # round-1 comparisons per theme, run inline
_PANE_H = 430         # px, the fixed height of the conversation pane


def _theme_cases(theme: str) -> list[dict]:
    return [s for s in (st.session_state.sb_scenarios or [])
            if s.get("category") == theme]


def _theme_index(theme: str) -> int:
    """A theme's stable slot, used to key every per-theme session value.

    Position in THEME_NAMES rather than a running counter, so the keys for a
    theme are the same whether it was worked on first or last, and revisiting a
    theme finds what was written the first time.
    """
    names = prompts.THEME_NAMES
    return names.index(theme) if theme in names else 0


def _theme_scenario(idx: int) -> dict:
    """The case a theme's per-theme values hang off: its first, or {} if none."""
    ss = st.session_state
    if idx < len(prompts.THEME_NAMES):
        cases = _theme_cases(prompts.THEME_NAMES[idx])
        if cases:
            return cases[0]
    return {}


def _theme_answer(theme: str) -> dict | None:
    return next((a for a in st.session_state.sb_answers
                 if a.get("theme") == theme), None)


def _ensure_theme_cases(theme: str) -> list[dict]:
    """Three cases for this theme, generated on first entry and then reused."""
    ss = st.session_state
    if ss.sb_scenarios is None:
        ss.sb_scenarios = []
    have = _theme_cases(theme)
    want = wizard.N_CASES_PER_THEME - len(have)
    if want > 0:
        titles = [s["title"] for s in ss.sb_scenarios]
        with st.spinner("Writing cases for this theme..."):
            data = llm.expand_theme(ss.sb_agent, _does(), ss.sb_desc,
                                    ss.sb_audience, theme, titles, want)
        # theme= forces the category, so a near-miss from the model cannot land
        # a case in a bucket no theme card can reach.
        _append_new(_ingest_scenarios(data, theme=theme))
        ss["_sb_scen_meta"] = {k: data.get(k) for k in ("_mock", "_error")}
        have = _theme_cases(theme)
    return have


def _open_theme(theme: str) -> None:
    ss = st.session_state
    ss.sb_theme = theme
    ss.sb_tphase = "write"
    ss.sb_tround = 1
    ss.sb_tcidx = 0


def _close_theme() -> None:
    ss = st.session_state
    ss.sb_theme = None
    ss.sb_tphase = "write"


# ---------------------------------------------------------------------------
# The menu
# ---------------------------------------------------------------------------

def _render_theme_menu() -> None:
    ss = st.session_state
    done = list(ss.get("sb_themes_done") or [])
    n_want = wizard.N_THEMES
    header("What worries you",
           f"Pick a kind of problem and write one rule for it. Choose "
           f"{n_want} in all. You have finished {len(done)}.")

    st.markdown(
        f'<div class="np-sub" style="margin-bottom:10px;">Researchers showed 24 '
        f'parents real conversations between children and AI chatbots and asked '
        f'what worried them. These are the eight kinds of answer that came '
        f'back.{provenance.icon("theme")} Pick whichever matter most to '
        f'you.</div>', unsafe_allow_html=True)

    themes = prompts.KIDS_THEMES
    for row_start in range(0, len(themes), 2):
        cols = st.columns(2, gap="medium")
        for col, t in zip(cols, themes[row_start:row_start + 2]):
            with col:
                _theme_card(t, t["name"] in done)

    st.write("")
    if len(done) >= n_want:
        st.success(f"You have written rules for {len(done)} themes. Continue to "
                   "compare them against some close calls.")
    else:
        st.caption(f"Pick {n_want - len(done)} more to continue.")


def _theme_card(t: dict, is_done: bool) -> None:
    """One theme, with what it means. The blurb is not decoration.

    Min, on seeing only the names: "they will not know what missing the real
    meaning [means] just from the title... nobody would have read the paper."
    """
    name = t["name"]
    tick = ('<span style="color:#2E7D4F;font-weight:700;"> done</span>'
            if is_done else "")
    n = t.get("raised_by")
    count = (f'<div class="np-muted" style="margin-top:6px;font-size:11.5px;">'
             f'raised by {n} of the 24 parents interviewed</div>' if n else "")
    st.markdown(
        f'<div class="np-card" style="margin-bottom:6px;min-height:150px;">'
        f'<div style="font-weight:700;color:{FG};">{name}{tick}</div>'
        f'<div class="np-sub" style="margin-top:4px;">{t["blurb"]}</div>'
        f'{count}</div>',
        unsafe_allow_html=True)
    if is_done:
        ans = _theme_answer(name)
        with st.expander("Your rule for this theme"):
            st.write((ans or {}).get("ideal_behavior", ""))
        st.button("Revise this rule", key=f"sb_pick_{name}", type="secondary",
                  use_container_width=True, on_click=_open_theme, args=(name,))
    else:
        st.button("Write a rule for this", key=f"sb_pick_{name}", type="primary",
                  use_container_width=True, on_click=_open_theme, args=(name,))


# ---------------------------------------------------------------------------
# The workspace
# ---------------------------------------------------------------------------

_STOP = {"about", "would", "should", "there", "their", "which", "where", "these",
         "those", "think", "thing", "things", "really", "maybe", "because",
         "could", "might", "want", "wants", "wanted", "just", "like", "know"}


def _content_words(text: str) -> set[str]:
    return {w.strip(".,!?;:'\"").lower() for w in (text or "").split()
            if len(w.strip(".,!?;:'\"")) > 4} - _STOP


def _unincorporated(idx: int, draft: str) -> list[dict]:
    """Reflection answers whose content does not appear in the rule yet.

    This backs the nudge that replaced the AI revision. Min: "there's no
    instruction that tells people to write out based on these answers... we just
    need to tell them, now you reflected on these, update your rule." The check
    is deliberately shallow, a word overlap, because the claim it makes on
    screen is only that the rule does not MENTION the thing yet.
    """
    have = _content_words(draft)
    out = []
    for r in _reflection_answers(idx):
        ans = (r.get("answer") or "").strip()
        words = _content_words(ans)
        if len(ans.split()) >= 4 and words and not (words & have):
            out.append(r)
    return out




def _render_score_bar(name: str, level: int | None, weight: int) -> str:
    filled = level or 0
    cells = "".join(
        f'<span style="display:inline-block;width:15px;height:8px;border-radius:2px;'
        f'margin-right:3px;background:{PRIMARY if k < filled else BORDER};"></span>'
        for k in range(4))
    lab = f"{level} of 4" if level else "not checked"
    return (f'<div style="display:flex;justify-content:space-between;'
            f'align-items:center;gap:8px;margin:5px 0;">'
            f'<span class="np-muted" style="flex:1;">{name}</span>'
            f'<span style="white-space:nowrap;">{cells}</span>'
            f'<span class="np-muted" style="width:66px;text-align:right;">{lab}</span>'
            f'</div>')


def _render_scores(fb: dict | None, rubric: list[dict], idx: int,
                   draft: str) -> None:
    """The rubric, compact, beside the writing box rather than under it.

    Four bars are always on screen; the reasoning stays in expanders. Min could
    not see the rubric at all while writing, and four open expanders is most of
    a screen. The column also renders before any check has run, greyed, so the
    layout does not jump when feedback arrives and move the box someone is
    typing into.
    """
    section("How your rule scores")
    levels = _levels_by_name(fb) if fb else {}
    if fb:
        score = prompts.overall_score(rubric, levels)
        band, colour = next((b for b in _SCORE_BANDS if score >= b[0]),
                            _SCORE_BANDS[-1])[1:]
        st.markdown(
            f'<div style="margin-bottom:6px;"><span class="np-pill" '
            f'style="background:{colour};color:#fff;">{score:g} / 100</span> '
            f'<span class="np-muted">{band}</span>'
            f'{provenance.icon("rubric")}</div>', unsafe_allow_html=True)
    else:
        st.caption("Write a rule and press Check to see how specific it is.")
    st.markdown(
        "".join(_render_score_bar(c["name"], levels.get(c["name"]), c["weight"])
                for c in rubric), unsafe_allow_html=True)

    if fb:
        for c in (fb.get("criteria") or []):
            with st.expander(f"{c.get('name', '')}: what would move this up"):
                st.markdown(f"**Why level {c.get('level')}**")
                st.write(c.get("why", ""))
                st.markdown(f"**What level {min(4, int(c.get('level', 1)) + 1)} "
                            f"would take**")
                st.write(c.get("why_not_higher", ""))

    # Adjusting the rubric lives with the rubric. It used to sit full width at
    # the bottom of the page and was silently dropped when the workspace was
    # split into layouts; anchoring it here means every layout gets it and none
    # can lose it again. Collapsed, it costs one line.
    _render_rubric_editor()

    # The nudge that replaced the AI revision: their own words, pointed at the
    # box beside this column, with no generated text to accept.
    missing = _unincorporated(idx, draft) if draft else []
    if missing:
        st.markdown('<div class="np-card-muted" style="margin-top:10px;">'
                    '<div class="np-section-title">Put this in your rule</div>'
                    '<div class="np-muted">You said these when you were thinking '
                    'it through, and your rule does not mention them yet. Edit '
                    'the box to include what still matters.</div>' +
                    "".join(f'<div class="np-sub" style="margin-top:6px;">'
                            f'&ldquo;{m["answer"]}&rdquo;</div>'
                            for m in missing[:2]) +
                    '</div>', unsafe_allow_html=True)


def _versions_for(idx: int, draft: str) -> list[tuple[str, str]]:
    """Every rule version this case has seen, newest last, for the compare panes."""
    turns = (st.session_state.get(f"sb_chat_{idx}") or {}).get("turns", [])
    out: list[tuple[str, str]] = [("No rule yet", "")]
    for t in turns:
        if t.get("role") != "assistant" or not t.get("tested"):
            continue
        label, rule = t.get("version", ""), (t.get("rule") or "").strip()
        if rule and rule not in [r for _, r in out]:
            out.append((label, rule))
    if draft and draft not in [r for _, r in out]:
        out.append(("Your rule now", draft))
    return out


def _run_version_compare(idx: int, scenario: dict, question: str,
                         left: str, right: str) -> None:
    ss = st.session_state
    ss[f"sb_vcmp_{idx}"] = {"question": question, "left": None, "right": None}
    for slot, rule in (("left", left), ("right", right)):
        data = llm.agent_reply(ss.sb_agent, _does(), ss.sb_audience, scenario,
                               rule or None,
                               [{"role": "user", "content": question}])
        ss[f"sb_vcmp_{idx}"][slot] = (data.get("reply") or "").strip()
    store.log_event(_rid(), "themes", "version_compare",
                    {"case_idx": idx, "question": question,
                     "left_rule": left, "right_rule": right})


def _render_version_compare(idx: int, scenario: dict, draft: str) -> None:
    """Ask one question of two rule versions and read the answers side by side.

    Min: "have people compare the baseline no rule yet versus rule version one
    or version two. The single difference is really helpful." Two panes only,
    because she raised the clutter problem in the same breath: "what if they
    keep revising it five times."
    """
    ss = st.session_state
    versions = _versions_for(idx, draft)
    labels = [v[0] for v in versions]
    rules = dict(versions)

    with st.expander("Compare versions", expanded=bool(ss.get(f"sb_vcmp_{idx}"))):
        st.caption("Ask the same question of two versions of your rule and see "
                   "what actually changed.")
        c1, c2 = st.columns(2, gap="small")
        left = c1.selectbox("Left", labels, index=0, key=f"sb_vleft_{idx}")
        right = c2.selectbox("Right", labels, index=len(labels) - 1,
                             key=f"sb_vright_{idx}")
        ex = scenario.get("example_exchange") or {}
        q = st.text_input("Ask both", key=f"sb_vq_{idx}",
                          value=ss.get(f"sb_vq_{idx}", ex.get("user_message", "")),
                          placeholder="what should your child be able to ask?")
        if st.button("Ask", key=f"sb_vgo_{idx}", disabled=not (q or "").strip()):
            with st.spinner("Asking both versions..."):
                _run_version_compare(idx, scenario, q.strip(),
                                     rules.get(left, ""), rules.get(right, ""))

        got = ss.get(f"sb_vcmp_{idx}")
        if got:
            st.markdown(f'<div class="np-muted" style="margin:8px 0 4px;">'
                        f'<b>{_who()}:</b> {got["question"]}</div>',
                        unsafe_allow_html=True)
            p1, p2 = st.columns(2, gap="medium")
            for pane, label, key in ((p1, left, "left"), (p2, right, "right")):
                with pane:
                    icon = (provenance.icon("baseline_reply")
                            if not rules.get(label) else
                            provenance.icon("rule_reply"))
                    st.markdown(f'<div class="np-section-title">{label}{icon}</div>',
                                unsafe_allow_html=True)
                    st.markdown(f'<div class="np-card">{got[key] or ""}</div>',
                                unsafe_allow_html=True)


def _save_theme_rule(theme: str, cases: list[dict]) -> None:
    """Save one rule for the theme, then move to the comparisons that test it."""
    ss = st.session_state
    idx = ss.sb_idx
    val = (ss.get(f"sb_answer_{idx}") or "").strip()
    if not val:
        return
    _record_answer(cases[0] if cases else {"id": -1, "title": theme,
                                           "situation": "", "at_stake": ""},
                   theme=theme, case_ids=[c["id"] for c in cases])
    done = list(ss.get("sb_themes_done") or [])
    if theme not in done:
        done.append(theme)
    ss.sb_themes_done = done
    ss.sb_tphase = "test"
    ss.sb_tround = 1
    ss.sb_tcidx = 0


# ---------------------------------------------------------------------------
# The workspace, in four layouts
# ---------------------------------------------------------------------------
# Four prototypes exist so Min can be shown the options rather than described
# them. They are a review affordance, not a feature: the switcher only appears
# in test sessions.
#
# All four compose the same primitives below and write the same session keys, so
# switching mid-theme cannot lose work and no layout can pass a test the others
# fail. What differs is only how each earns space, because the hard constraint
# is that a theme must fit one viewport without the page scrolling, and the
# case, its conversation, the questions, the rule box and the rubric do not fit
# together at any honest font size.

LAYOUTS = {
    "A": ("Staged", "One step at a time under a pinned case."),
    "B": ("Workbench", "Everything visible at once, in three columns."),
    "C": ("Split", "Case holds the left half; work steps down the right."),
    "D": ("Conversation", "The chat is the page; work docks beneath it."),
    "O": ("Original", "What was live before this pass, for comparison."),
}
_DEFAULT_LAYOUT = "A"


def _layout() -> str:
    got = st.session_state.get("sb_layout")
    return got if got in LAYOUTS else _DEFAULT_LAYOUT


def _render_layout_switcher() -> None:
    """Visible only in test sessions. A participant must never see this."""
    if not st.session_state.get("resp_test"):
        return
    keys = list(LAYOUTS)
    st.radio("Layout prototype", keys, key="sb_layout", horizontal=True,
             index=keys.index(_layout()),
             format_func=lambda k: f"{k} · {LAYOUTS[k][0]}")
    st.caption(LAYOUTS[_layout()][1])


# ---- the pieces every layout is built from --------------------------------

def _ui_cases(cases: list[dict]) -> None:
    """The theme's cases as conversations, one per tab.

    No fixed-height container. Each case used to sit in one, which put a second
    scrollbar inside the page: the situation was at the top and the exchange
    below the fold, so reading the conversation meant scrolling a pane rather
    than looking at the screen. A tab shows one case at a time, and one case is
    short enough to fit.

    """
    st.markdown(f'<div class="np-section-title">The conversations'
                f'{provenance.icon("case")}</div>', unsafe_allow_html=True)
    if not cases:
        st.info("No cases for this theme yet.")
        return
    tabs = st.tabs([f"Case {i + 1}" for i in range(len(cases))])
    for tab, sc in zip(tabs, cases):
        with tab:
            st.markdown(_situation_card(sc), unsafe_allow_html=True)
            _render_example_chat(sc)


def _ui_before(idx: int, scenario: dict) -> None:
    """The questions asked before anything is written. All required."""
    ss = st.session_state
    if f"sb_rqb_{idx}" not in ss:
        with st.spinner("Preparing a couple of questions to consider..."):
            rq = llm.reflect_before(ss.sb_agent, _does(), ss.sb_audience, scenario)
        ss[f"sb_rqb_{idx}"] = rq.get("questions") or []
        store.log_event(_rid(), "themes", "reflect_before",
                        {"theme": ss.sb_theme, "questions": ss[f"sb_rqb_{idx}"]})
    section("Before you answer")
    st.caption("There is no right answer. What you write here is used when your "
               "rule is checked, so answer all of them before you write.")
    probe = (scenario.get("probe") or "").strip()
    if probe:
        _render_one_question(f"sb_rap_{idx}", "As you write, consider", probe,
                             "probe")
    _render_reflection(idx, "b", ss[f"sb_rqb_{idx}"])


def _ui_after(idx: int) -> None:
    """The questions asked about what was actually written. Only after a check."""
    ss = st.session_state
    if not ss.get(f"sb_rqa_{idx}"):
        return
    section("Now that you have written it")
    st.caption("These ask about your reasoning, not whether the rule is good.")
    _render_reflection(idx, "a", ss[f"sb_rqa_{idx}"])


def _ui_rule(idx: int, height: int = 200) -> None:
    """The rule box and the two things you can do with it."""
    ss = st.session_state
    section("Your rule for this theme")
    draft = _kept_text(
        f"sb_answer_{idx}", "Your rule", height=height,
        label_visibility="collapsed",
        placeholder="One rule that should hold across all three of these "
                    "conversations. Say what the AI should do, what it should "
                    "not do, and how to handle the hard part.").strip()
    b1, b2 = st.columns(2, gap="small")
    b1.button("Check my answer", key=f"sb_check_{idx}", use_container_width=True,
              type="primary", disabled=not draft, on_click=_flag,
              args=("_sb_check",))
    b2.button("Try it on a case", key=f"sb_test_{idx}", use_container_width=True,
              type="secondary", disabled=not draft,
              help="Answers the first conversation again, following your rule.",
              on_click=_request_test, args=(idx,))


def _ui_tried(idx: int, cases: list[dict], height: int = 260) -> None:
    ss = st.session_state
    if not (ss.get(f"sb_chat_{idx}") or {}).get("turns") or not cases:
        return
    section("Your rule, tried out")
    with st.container(height=height, border=False):
        _render_scenario_chat(idx, cases[0])


def _ui_save(theme: str, cases: list[dict], idx: int) -> None:
    ss = st.session_state
    missing = _unanswered(idx, "b")
    no_rule = not (ss.get(f"sb_answer_{idx}") or "").strip()
    st.button("Save this rule and test it", key=f"sb_save_{idx}", type="primary",
              use_container_width=True, disabled=bool(missing) or no_rule,
              on_click=_save_theme_rule, args=(theme, cases))
    if missing:
        st.caption(_needs(len(missing), len(_question_slots(idx, "b"))))
    elif no_rule:
        st.caption("Write your rule to continue.")


# ---- stage handling, for the layouts that step ----------------------------

_STAGES = ("Consider", "Write", "Sharpen")


def _stage(idx: int) -> int:
    return int(st.session_state.get(f"sb_stage_{idx}", 0))


def _set_stage(idx: int, n: int) -> None:
    st.session_state[f"sb_stage_{idx}"] = max(0, min(len(_STAGES) - 1, n))


def _render_stage_rail(idx: int) -> None:
    cur = _stage(idx)
    cells = "".join(
        f'<span class="np-pill" style="margin-right:6px;'
        f'background:{PRIMARY if k == cur else SURFACE_BG};'
        f'color:{"#fff" if k == cur else MUTED_FG};">{k + 1}. {name}</span>'
        for k, name in enumerate(_STAGES))
    st.markdown(f'<div style="margin-bottom:8px;">{cells}</div>',
                unsafe_allow_html=True)


def _render_stage_nav(idx: int) -> None:
    """Forward is gated on the questions; back never is."""
    cur = _stage(idx)
    missing = _unanswered(idx, "b") if cur == 0 else []
    c1, c2 = st.columns([1, 1], gap="small")
    if cur > 0:
        c1.button("Back", key=f"sb_stback_{idx}_{cur}", use_container_width=True,
                  type="secondary", on_click=_set_stage, args=(idx, cur - 1))
    if cur < len(_STAGES) - 1:
        c2.button(f"Next: {_STAGES[cur + 1]}", key=f"sb_stnext_{idx}_{cur}",
                  use_container_width=True, type="primary",
                  disabled=bool(missing),
                  on_click=_set_stage, args=(idx, cur + 1))
    if missing:
        st.caption(_needs(len(missing), len(_question_slots(idx, "b"))))


# ---- the four layouts ------------------------------------------------------

def _layout_a(idx, theme, cases, scenario) -> None:
    """Staged: the case is pinned and one working block sits under it."""
    _ui_cases(cases)
    st.divider()
    _render_stage_rail(idx)
    cur = _stage(idx)
    if cur == 0:
        _ui_before(idx, scenario)
    elif cur == 1:
        left, right = st.columns([1.3, 1], gap="medium")
        with left:
            _ui_rule(idx, height=220)
        with right:
            _render_scores(st.session_state.get(f"sb_fb_{idx}"),
                           st.session_state.sb_rubric, idx,
                           (st.session_state.get(f"sb_answer_{idx}") or "").strip())
    else:
        left, right = st.columns([1, 1], gap="medium")
        with left:
            _ui_after(idx)
            _ui_tried(idx, cases, 220)
        with right:
            _render_version_compare(idx, scenario,
                                    (st.session_state.get(f"sb_answer_{idx}")
                                     or "").strip())
    _render_stage_nav(idx)
    if cur == len(_STAGES) - 1:
        _ui_save(theme, cases, idx)


def _layout_b(idx, theme, cases, scenario) -> None:
    """Workbench: everything at once, three columns, nothing hidden."""
    ss = st.session_state
    draft = (ss.get(f"sb_answer_{idx}") or "").strip()
    scores, middle, asks = st.columns([1, 1.35, 1], gap="medium")
    with scores:
        _render_scores(ss.get(f"sb_fb_{idx}"), ss.sb_rubric, idx, draft)
    with middle:
        _ui_cases(cases)
        _ui_rule(idx, height=170)
    with asks:
        _ui_before(idx, scenario)
        _ui_after(idx)
    _ui_save(theme, cases, idx)


# How the two columns split, by stage. The case stays on the left throughout,
# but it does not need half the screen while someone is typing three answers
# into the other half, so the working column widens where the work is.
_C_SPLIT = {0: [1, 1.7], 1: [1, 1.3], 2: [1, 1.3]}


def _layout_c(idx, theme, cases, scenario) -> None:
    """Split: the case holds the left, the work steps down the right.

    The right column used to be a fixed-height scrolling container that was
    shorter than its own contents, so on the first stage the answer boxes sat
    below a nested scrollbar and there was no way to tell they were there.
    Nothing here scrolls inside the page any more.
    """
    ss = st.session_state
    cur = _stage(idx)
    left, right = st.columns(_C_SPLIT[cur], gap="medium")
    with left:
        _ui_cases(cases)
    with right:
        _render_stage_rail(idx)
        if cur == 0:
            _ui_before(idx, scenario)
        elif cur == 1:
            _ui_rule(idx, height=190)
            _render_scores(ss.get(f"sb_fb_{idx}"), ss.sb_rubric, idx,
                           (ss.get(f"sb_answer_{idx}") or "").strip())
        else:
            _ui_after(idx)
            _render_version_compare(idx, scenario,
                                    (ss.get(f"sb_answer_{idx}") or "").strip())
            _ui_tried(idx, cases, 200)
        _render_stage_nav(idx)
        if cur == len(_STAGES) - 1:
            _ui_save(theme, cases, idx)


def _layout_d(idx, theme, cases, scenario) -> None:
    """Conversation-led: the chat is the page, the work docks beneath it."""
    ss = st.session_state
    _ui_cases(cases)
    st.divider()
    t_ask, t_rule, t_score, t_ver = st.tabs(
        ["Questions", "Your rule", "Score", "Versions"])
    with t_ask:
        _ui_before(idx, scenario)
        _ui_after(idx)
    with t_rule:
        _ui_rule(idx, height=180)
        _ui_tried(idx, cases, 200)
    with t_score:
        _render_scores(ss.get(f"sb_fb_{idx}"), ss.sb_rubric, idx,
                       (ss.get(f"sb_answer_{idx}") or "").strip())
    with t_ver:
        _render_version_compare(idx, scenario,
                                (ss.get(f"sb_answer_{idx}") or "").strip())
    _ui_save(theme, cases, idx)


def _layout_o(idx, theme, cases, scenario) -> None:
    """The layout that was live before this pass, kept so the four new ones can
    be judged against something rather than against a description of it.

    Unchanged on purpose, including the parts the new layouts improve on: it
    scrolls, and the questions and the score compete for the same vertical space
    as the conversation.
    """
    ss = st.session_state
    draft = (ss.get(f"sb_answer_{idx}") or "").strip()
    scores, middle, asks = st.columns([1, 1.35, 1], gap="medium")
    with scores:
        _render_scores(ss.get(f"sb_fb_{idx}"), ss.sb_rubric, idx, draft)
    with middle:
        _ui_cases(cases)
        st.write("")
        _ui_rule(idx, height=170)
        _ui_tried(idx, cases, 300)
    with asks:
        _ui_before(idx, scenario)
        _ui_after(idx)
    st.write("")
    _render_version_compare(idx, scenario, draft)
    st.write("")
    _ui_save(theme, cases, idx)


_LAYOUT_FNS = {"A": _layout_a, "B": _layout_b, "C": _layout_c, "D": _layout_d,
               "O": _layout_o}


def _render_theme_workspace() -> None:
    ss = st.session_state
    theme = ss.sb_theme
    meta = prompts.theme_by_name(theme) or {"name": theme, "blurb": ""}
    cases = _ensure_theme_cases(theme)
    idx = _theme_index(theme)
    ss.sb_idx = idx
    scenario = cases[0] if cases else {"id": -1, "title": theme, "situation": "",
                                       "at_stake": "", "considerations": [],
                                       "probe": "", "example_exchange": {}}
    n_done = len(ss.get("sb_themes_done") or [])

    _handle_workspace_actions(idx, scenario, cases)

    header(meta["name"],
           f"Theme {min(n_done + 1, wizard.N_THEMES)} of {wizard.N_THEMES}. "
           f"{meta['blurb']}")
    st.button("Back to the themes", key="sb_back_themes", type="secondary",
              on_click=_close_theme)
    _render_layout_switcher()
    _LAYOUT_FNS[_layout()](idx, theme, cases, scenario)


def _handle_workspace_actions(idx: int, scenario: dict, cases: list[dict]) -> None:
    """Deferred button work, so spinners render where the content will land."""
    ss = st.session_state
    draft = (ss.get(f"sb_answer_{idx}") or "").strip()
    if ss.get("_sb_check"):
        del ss["_sb_check"]
        if f"sb_first_{idx}" not in ss:
            ss[f"sb_first_{idx}"] = draft
        with st.spinner("Checking your rule against the rubric..."):
            ss[f"sb_fb_{idx}"] = llm.rubric_feedback(
                ss.sb_agent, _does(), ss.sb_desc, ss.sb_audience, scenario, draft,
                ss.sb_rubric, reflection=_reflection_answers(idx))
        ss[f"sb_lastfb_{idx}"] = ss[f"sb_fb_{idx}"]
        ss[f"sb_nrev_{idx}"] = ss.get(f"sb_nrev_{idx}", 0) + 1
        if f"sb_rqa_{idx}" not in ss:
            with st.spinner("Reading what you wrote..."):
                rq = llm.reflect_after(ss.sb_agent, _does(), ss.sb_audience,
                                       scenario, draft)
            ss[f"sb_rqa_{idx}"] = rq.get("questions") or []
            store.log_event(_rid(), "themes", "reflect_after",
                            {"theme": ss.sb_theme,
                             "questions": ss[f"sb_rqa_{idx}"]})
        store.log_event(_rid(), "themes", "check",
                        {"theme": ss.sb_theme, "draft": draft,
                         "levels": _levels_by_name(ss[f"sb_fb_{idx}"]),
                         "n_check": ss[f"sb_nrev_{idx}"]})
    if ss.get("_sb_test") == idx:
        del ss["_sb_test"]
        _run_test(idx, scenario, draft)
    pending = ss.get("_sb_followup")
    if pending and pending[0] == idx:
        del ss["_sb_followup"]
        _run_followup(idx, scenario, draft, pending[1])
        ss[f"sb_followup_{idx}"] = ""


def render_themes() -> None:
    """One step, three screens: the menu, a theme's workspace, its comparisons."""
    ss = st.session_state
    if ss.get("sb_submitted"):
        st.info("Your responses have been submitted, so this step is read-only. "
                "Continue to the last step to see and download your results.")
        return
    if not ss.get("sb_theme"):
        _render_theme_menu()
    elif ss.get("sb_tphase") == "test":
        _render_theme_test()
    else:
        _render_theme_workspace()


# ---------------------------------------------------------------------------
# Round 1, inline, scoped to the theme just written
# ---------------------------------------------------------------------------
# The theme testing loop
# ---------------------------------------------------------------------------
# The same three rounds run twice, at two levels, because they test two
# different claims.
#
#   Here, per theme, against the rule just written:
#       does MY RULE capture what I want?
#   In render_confirm, at the end, against the synthesized policy:
#       does the POLICY capture it, across everything I wrote?
#
# What the model follows in these rounds is that one theme's rule and nothing
# else, so a disagreement points at a gap in the rule rather than at some
# aggregate the person never wrote.
#
# Round 2 hands the rule box back rather than offering a rewrite. The AI
# revision was removed earlier on Min's reasoning that people accept whatever
# the model puts in front of them; reintroducing it here would undo that and add
# another generated component needing accuracy validation. Round 3 then scores
# the edited rule, so the loop measures whether the person's own revision
# actually closed the gap they were shown.

N_THEME_ROUND = 2      # comparisons per theme round; 3 rounds x 3 themes


def _theme_key(theme: str, rnd: int) -> str:
    return f"{theme}:{rnd}"


def _theme_rule(theme: str) -> str:
    """The rule as it stands now, including any round-2 edit."""
    ss = st.session_state
    live = (ss.get(f"sb_answer_{_theme_index(theme)}") or "").strip()
    if live:
        return live
    return ((_theme_answer(theme) or {}).get("ideal_behavior") or "").strip()


def _theme_cmps(theme: str, rnd: int) -> list[dict]:
    """This theme's comparisons for one round, generated once and cached."""
    ss = st.session_state
    key = _theme_key(theme, rnd)
    if key in ss.sb_cmp:
        return ss.sb_cmp[key]
    ans = _theme_answer(theme)
    if not ans:
        return []
    used = [c.get("dimension", "") for r in ss.sb_cmp.values() for c in r]
    out = []
    with st.spinner("Building a couple of close calls..."):
        for k in range(N_THEME_ROUND):
            data = llm.confirm_pairwise(ss.sb_agent, _does(), ss.sb_desc,
                                        ss.sb_audience, ans, _theme_rule(theme),
                                        avoid=used, edge=(rnd > 1))
            opts = list(data.get("options") or [])
            while len(opts) < 2:
                opts.append({"label": f"Option {len(opts) + 1}",
                             "text": "(no option)"})
            dim = (data.get("dimension") or "").strip()
            used.append(dim)
            out.append({
                "id": f"{theme[:12]}r{rnd}i{k}", "round": rnd, "theme": theme,
                "level": "theme",
                "scenario_id": ans.get("scenario_id"),
                "title": ans.get("title", ""), "situation": ans.get("situation", ""),
                "instance": (data.get("instance") or "").strip(),
                "user_message": (data.get("user_message") or "").strip(),
                "dimension": dim, "options": opts[:2],
                "_mock": data.get("_mock"), "_error": data.get("_error")})
    ss.sb_cmp[key] = out
    return out


def _rule_answer(cmp: dict, theme: str) -> dict:
    """What this theme's rule picks, cached on the item.

    Reuses the policy picker with a one-principle policy rather than adding a
    prompt: it already takes a principle list and returns a choice plus the line
    that decided it, which is exactly what a single rule needs.
    """
    ss = st.session_state
    if "model" not in cmp:
        rule = _theme_rule(theme)
        with st.spinner("Applying your rule..."):
            data = llm.policy_pick(ss.sb_agent, _does(), ss.sb_audience,
                                   {"principles": [rule] if rule else []},
                                   cmp.get("instance", ""),
                                   cmp["options"][0], cmp["options"][1])
        cmp["model"] = {"choice": (data.get("choice") or "A").strip().upper()[:1],
                        "reason": (data.get("reason") or "").strip(),
                        "rule": rule, "_mock": data.get("_mock")}
    return cmp["model"]


def _theme_commit(cmp: dict, i: int) -> None:
    """Record the pick. Round 1 moves on; rounds 2 and 3 reveal in place."""
    ss = st.session_state
    choice = ss.get(f"sb_pick_{cmp['id']}")
    if not choice:
        return
    _record_pick(cmp, choice, i, advance=False)
    if cmp["round"] == 1:
        ss.sb_tcidx = ss.get("sb_tcidx", 0) + 1
    else:
        ss.sb_revealed[cmp["id"]] = True


def _theme_after_reveal(cmp: dict, i: int) -> None:
    """Close out a revealed item: record what the rule did, then move on."""
    ss = st.session_state
    row = _row_for(cmp["id"])
    model = cmp.get("model") or {}
    if row is not None:
        row["model_choice"] = model.get("choice", "")
        row["model_reason"] = model.get("reason", "")
        row["agreed"] = bool(row.get("choice") == model.get("choice"))
        row["rule_at_test"] = model.get("rule", "")
        store.log_event(_rid(), "themes", "theme_scored",
                        {"comparison": cmp["id"], "theme": cmp.get("theme"),
                         "round": cmp["round"], "person": row.get("choice"),
                         "model": model.get("choice"), "agreed": row["agreed"]})
    ss.sb_tcidx = ss.get("sb_tcidx", 0) + 1


def _theme_advance_round() -> None:
    ss = st.session_state
    ss.sb_tround = ss.get("sb_tround", 1) + 1
    ss.sb_tcidx = 0
    store.log_event(_rid(), "themes", "theme_round_start",
                    {"theme": ss.sb_theme, "round": ss.sb_tround})


def _theme_agreement(theme: str) -> tuple[int, int]:
    rows = [r for r in st.session_state.sb_confirm
            if r.get("theme") == theme and r.get("round") == 3
            and r.get("model_choice")]
    return sum(1 for r in rows if r.get("agreed")), len(rows)


_THEME_ROUND_INTRO = {
    1: "Pick the reply you prefer and say why. Nothing is revealed yet.",
    2: "Pick and say why. Then you will see what your rule chose, and can "
       "change the rule if it got this wrong.",
    3: "Pick and say why. Then you will see what your rule chose. This round "
       "is scored and the rule no longer changes.",
}


def _render_theme_test() -> None:
    ss = st.session_state
    theme = ss.sb_theme
    idx = _theme_index(theme)
    rnd = ss.get("sb_tround", 1)
    cmps = _theme_cmps(theme, rnd)
    i = ss.get("sb_tcidx", 0)

    if not cmps:
        st.info("No comparisons could be built for this theme.")
        st.button("Back to the themes", key="sb_done_theme", type="primary",
                  on_click=_close_theme)
        return

    # ---- round finished ---------------------------------------------------
    if i >= len(cmps):
        if rnd < _LAST_ROUND:
            header(theme, f"Round {rnd} of {_LAST_ROUND} done.")
            if rnd == 1:
                st.success("Next you will see what your rule decides on its "
                           "own, and can change it where it gets something "
                           "wrong.")
            else:
                st.success("Your rule is settled. The last round is scored: you "
                           "will see what it decides, but nothing changes.")
            st.button(f"Start round {rnd + 1}", type="primary",
                      key=f"sb_tr_{theme}_{rnd}", on_click=_theme_advance_round)
            return
        agreed, total = _theme_agreement(theme)
        header(theme, "This theme is done.")
        if total:
            st.success(f"On the scored round your rule chose the same as you on "
                       f"**{agreed} of {total}**.")
        st.button("Back to the themes", key="sb_done_theme", type="primary",
                  on_click=_close_theme)
        return

    cmp = cmps[i]
    _mock_note(cmp)
    revealed = rnd > 1 and ss.sb_revealed.get(cmp["id"], False)

    header(theme, f"Round {rnd} of {_LAST_ROUND}. Close call {i + 1} of "
                  f"{len(cmps)}. {_THEME_ROUND_INTRO[rnd]}")
    _render_rule_reminder(idx)
    _render_moment(cmp)

    model = _rule_answer(cmp, theme) if revealed else {}
    _render_options(cmp, highlight=model.get("choice", "") if revealed else "",
                    mine=ss.get(f"sb_pick_{cmp['id']}", ""))

    if not revealed:
        chosen = _render_pick_controls(cmp, rnd, i)
        st.button("Continue", key=f"sb_tgo_{cmp['id']}", type="primary",
                  disabled=not chosen, on_click=_theme_commit, args=(cmp, i))
        if not chosen:
            st.caption("Pick one to continue.")
        elif rnd > 1:
            st.caption("What your rule chose stays hidden until you continue, "
                       "so what you write is your own view rather than a "
                       "reaction to it.")
        return

    row = _row_for(cmp["id"]) or {}
    same = row.get("choice") == model.get("choice")
    tone = "#2E7D4F" if same else "#B0472F"
    verdict = ("Your rule agrees with you here."
               if same else "Your rule chose differently from you.")
    yours = "left" if row.get("choice") == "A" else "right"
    st.markdown(
        f'<div class="np-card" style="margin:10px 0;border-color:{tone};">'
        f'<div class="np-section-title" style="color:{tone};">{verdict}'
        f'{provenance.icon("model_pick")}</div>'
        f'<div class="np-sub"><b>You chose the {yours}.</b> Your rule chose '
        f'because: {model.get("reason", "")}</div></div>',
        unsafe_allow_html=True)

    if rnd == 2:
        section("Change your rule, if it got this wrong")
        st.caption("This is your rule, not a suggestion from us. Edit it and "
                   "the next comparisons use what you write here.")
        _kept_text(f"sb_answer_{idx}", "Your rule", height=150,
                   label_visibility="collapsed")
        st.button("Save and continue", type="primary",
                  key=f"sb_tafter_{cmp['id']}", on_click=_theme_after_reveal,
                  args=(cmp, i))
    else:
        st.button("Next", type="primary", key=f"sb_tafter_{cmp['id']}",
                  on_click=_theme_after_reveal, args=(cmp, i))
        st.caption("This round is scored. Nothing you do here changes the rule.")


def _render_rule_reminder(idx: int) -> None:
    """The rule under test, always on screen while it is being tested."""
    rule = (st.session_state.get(f"sb_answer_{idx}") or "").strip()
    if not rule:
        return
    st.markdown(f'<div class="np-card-muted" style="margin-bottom:10px;">'
                f'<div class="np-section-title">Your rule</div>'
                f'<div class="np-muted">{rule}</div></div>',
                unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Step 5: Comparisons, in three rounds
# ---------------------------------------------------------------------------
# One policy is built and then sharpened across three rounds of pairwise
# comparisons. In every round the person commits to a pick AND a reason before
# anything the model did is revealed; seeing the model first would contaminate
# the reason, and the whole measurement rests on that reason being their own.
#
#   Round 1  pick + why. The model is not involved and nothing is revealed.
#            -> the policy is written from the rules they authored per case
#               plus these picks and reasons.
#   Round 2  pick + why, then reveal the model's pick and its reason, then they
#            say what it got wrong. That critique sharpens the SAME policy.
#   Round 3  pick + why, then reveal. Nothing is editable. This is the score.
#
# Round 2 revises after each item, so later items in that round are decided by
# an already-sharpened policy. Round 3 never revises, so its policy is fixed for
# the whole round and the agreement number means something.

N_ROUND2 = 3      # sharpening items
N_ROUND3 = 3      # scored items
_LAST_ROUND = 3


def _cmp_key(rnd: int) -> str:
    return str(rnd)


def _round_cmps(rnd: int) -> list[dict]:
    """The comparisons for a round, generated once and cached."""
    ss = st.session_state
    store_ = ss.sb_cmp
    key = _cmp_key(rnd)
    if key in store_:
        return store_[key]

    answers = ss.sb_answers
    used = [c.get("dimension", "") for r in store_.values() for c in r]
    out = []
    if rnd == 1:
        targets = list(answers)
    else:
        n = N_ROUND2 if rnd == 2 else N_ROUND3
        # Cycle back through their cases so later rounds stay on the same
        # material, but ask for a different dimension each time so they are not
        # answering the same question again.
        targets = [answers[i % len(answers)] for i in range(n)] if answers else []

    with st.spinner("Building the comparisons..."):
        for k, ans in enumerate(targets):
            data = llm.confirm_pairwise(ss.sb_agent, _does(), ss.sb_desc,
                                        ss.sb_audience, ans,
                                        ans.get("ideal_behavior", ""),
                                        avoid=used, edge=(rnd > 1))
            opts = list(data.get("options") or [])
            while len(opts) < 2:
                opts.append({"label": f"Option {len(opts) + 1}",
                             "text": "(no option)"})
            dim = (data.get("dimension") or "").strip()
            used.append(dim)
            out.append({
                "id": f"r{rnd}i{k}",
                "round": rnd, "level": "final", "theme": ans.get("theme", ""),
                "scenario_id": ans.get("scenario_id"),
                "title": ans.get("title", ""),
                "situation": ans.get("situation", ""),
                "instance": (data.get("instance") or "").strip(),
                "user_message": (data.get("user_message") or "").strip(),
                "dimension": dim,
                "options": opts[:2],
                "_mock": data.get("_mock"), "_error": data.get("_error"),
            })
    store_[key] = out
    return out


def _policy_cap() -> int:
    return prompts.policy_cap(len(st.session_state.sb_answers))


def _write_policy() -> None:
    """First policy: their per-case rules plus their round-1 picks and reasons."""
    ss = st.session_state
    with st.spinner("Writing your policy from everything you have said..."):
        data = llm.policy_write(ss.sb_agent, _does(), ss.sb_audience, ss.sb_rubric,
                                ss.sb_answers, ss.sb_confirm, _policy_cap())
    ss.sb_policy = {"principles": data.get("principles") or [],
                    "what_changed": (data.get("what_changed") or "").strip(),
                    "version": 1, "_mock": data.get("_mock"),
                    "_error": data.get("_error")}
    ss.sb_policy_log = [dict(ss.sb_policy, source="round 1")]
    store.log_event(_rid(), "confirm", "policy_write",
                    {"principles": ss.sb_policy["principles"],
                     "from_answers": len(ss.sb_answers),
                     "from_picks": len(ss.sb_confirm)})


def _model_answer(cmp: dict) -> dict:
    """The model's pick and reason for one comparison, cached on the item.

    Computed at reveal time using whatever the policy is at that moment, so a
    round-2 revision is reflected in the next item. The policy version used is
    stored with it, so every model answer stays attributable after the fact.
    """
    ss = st.session_state
    if "model" not in cmp:
        pol = ss.sb_policy or {"principles": []}
        with st.spinner("Applying your policy..."):
            data = llm.policy_pick(ss.sb_agent, _does(), ss.sb_audience, pol,
                                   cmp.get("instance", ""),
                                   cmp["options"][0], cmp["options"][1])
        cmp["model"] = {"choice": (data.get("choice") or "A").strip().upper()[:1],
                        "reason": (data.get("reason") or "").strip(),
                        "policy_version": pol.get("version", 1),
                        "_mock": data.get("_mock")}
    return cmp["model"]


def _record_pick(cmp: dict, choice: str, i: int, advance: bool = False) -> None:
    """Commit a pick and the reason for it.

    The index is passed rather than read off ss.sb_cidx at callback time. It used
    to be read, which was safe only because the item on screen was always
    cmps[sb_cidx]; round 1 now runs per theme against its own counter, so the
    assumption no longer holds.

    Nothing here advances the screen. Round 1 used to jump straight to the next
    comparison the instant a side was clicked, which is what Min meant by "don't
    make it go automatically to the next page" and also meant the reason box was
    gone before it could be filled in.
    """
    ss = st.session_state
    rnd = cmp["round"]
    row = {
        "id": cmp["id"], "round": rnd,
        "theme": cmp.get("theme", ""), "level": cmp.get("level", "final"),
        "scenario_id": cmp.get("scenario_id"), "title": cmp.get("title", ""),
        "situation": cmp.get("situation", ""),
        "instance": cmp.get("instance", ""), "dimension": cmp.get("dimension", ""),
        "user_message": cmp.get("user_message", ""),
        "option_a": cmp["options"][0], "option_b": cmp["options"][1],
        "choice": choice,
        "note": (ss.get(f"sb_cnote_{rnd}_{i}") or "").strip(),
    }
    prev = _row_for(cmp["id"])
    if prev is not None:
        ss.sb_confirm[ss.sb_confirm.index(prev)] = row
    else:
        ss.sb_confirm.append(row)
    store.log_event(_rid(), "confirm", "confirm_pick", row)
    if rnd > 1 and cmp.get("level") != "theme":
        ss.sb_revealed[f"{rnd}_{i}"] = True
    if advance:
        ss.sb_cidx += 1


def _row_for(cmp_id: str) -> dict | None:
    return next((r for r in st.session_state.sb_confirm
                 if r.get("id") == cmp_id), None)


def _apply_critique(cmp: dict, i: int) -> None:
    """Sharpen the policy from what the person said about the model's choice."""
    ss = st.session_state
    rnd = cmp["round"]
    critique = (ss.get(f"sb_crit_{rnd}_{i}") or "").strip()
    row = _row_for(cmp["id"]) or {}
    model = cmp.get("model") or {}
    if critique:
        with st.spinner("Sharpening your policy..."):
            data = llm.policy_revise(
                ss.sb_agent, _does(), ss.sb_audience, ss.sb_rubric,
                ss.sb_policy, cmp.get("instance", ""),
                cmp["options"][0], cmp["options"][1],
                model.get("choice", ""), row.get("choice", ""), critique,
                _policy_cap())
        ver = (ss.sb_policy or {}).get("version", 1) + 1
        ss.sb_policy = {"principles": data.get("principles") or [],
                        "what_changed": (data.get("what_changed") or "").strip(),
                        "version": ver, "_mock": data.get("_mock")}
        ss.sb_policy_log.append(dict(ss.sb_policy, source=f"critique on {cmp['id']}"))
        store.log_event(_rid(), "confirm", "policy_revise",
                        {"comparison": cmp["id"], "critique": critique,
                         "version": ver,
                         "principles": ss.sb_policy["principles"]})
    if row is not None:
        row["critique"] = critique
        row["model_choice"] = model.get("choice", "")
        row["model_reason"] = model.get("reason", "")
        row["agreed"] = bool(row.get("choice") == model.get("choice"))
    ss.sb_cidx += 1


def _next_scored(cmp: dict, i: int) -> None:
    """Round 3: record what the model did, change nothing."""
    ss = st.session_state
    row = _row_for(cmp["id"])
    model = cmp.get("model") or {}
    if row is not None:
        row["model_choice"] = model.get("choice", "")
        row["model_reason"] = model.get("reason", "")
        row["agreed"] = bool(row.get("choice") == model.get("choice"))
        store.log_event(_rid(), "confirm", "scored_item",
                        {"comparison": cmp["id"], "person": row.get("choice"),
                         "model": model.get("choice"), "agreed": row["agreed"],
                         "policy_version": model.get("policy_version")})
    ss.sb_cidx += 1


def _advance_round() -> None:
    ss = st.session_state
    if ss.sb_round == 1:
        _write_policy()
    ss.sb_round += 1
    ss.sb_cidx = 0
    store.log_event(_rid(), "confirm", "round_start", {"round": ss.sb_round})


def _restart_confirm() -> None:
    ss = st.session_state
    ss.sb_cidx = 0
    ss.sb_round = 1
    ss.sb_confirm = []
    ss.sb_cmp = {}
    ss.sb_revealed = {}
    ss.sb_policy = None
    ss.sb_policy_log = []
    store.log_event(_rid(), "confirm", "confirm_restart", {})


def agreement() -> tuple[int, int]:
    """(agreed, total) over the scored round only."""
    rows = [r for r in st.session_state.sb_confirm
            if r.get("round") == _LAST_ROUND and "agreed" in r]
    return sum(1 for r in rows if r["agreed"]), len(rows)


def _render_policy(expanded: bool = False) -> None:
    pol = st.session_state.sb_policy or {}
    items = pol.get("principles") or []
    if not items:
        return
    body = "".join(f'<li style="margin-bottom:4px;">{p}</li>' for p in items)
    with st.expander(f"Your policy so far ({len(items)} principles)", expanded=expanded):
        st.markdown(f'<ol class="np-sub" style="padding-left:18px;">{body}</ol>'
                    f'<div class="np-muted">Where this came from'
                    f'{provenance.icon("policy")}</div>',
                    unsafe_allow_html=True)
        if pol.get("what_changed"):
            st.caption(f"Last change: {pol['what_changed']}")


def _render_options(cmp: dict, highlight: str = "", mine: str = "") -> None:
    """The two candidate responses.

    `highlight` marks the model's choice once revealed. `mine` marks the
    person's own pick before that, so clicking a side shows visibly that it
    landed: picking no longer jumps to the next screen, so without this there
    would be no feedback at all.
    """
    col_a, col_b = st.columns(2, gap="medium")
    for col, letter in ((col_a, "A"), (col_b, "B")):
        opt = cmp["options"][0 if letter == "A" else 1]
        picked = highlight == letter
        is_mine = (not highlight) and mine == letter
        border = "#2E7D4F" if picked else (PRIMARY if is_mine else BORDER)
        tag = ('<span class="np-pill" style="background:#E4F1E8;color:#2E7D4F;">'
               'the agent chose this</span>' if picked else
               ('<span class="np-pill">your pick</span>' if is_mine else ""))
        with col:
            st.markdown(
                f'<div class="np-card" style="border-color:{border};'
                f'border-width:{"2px" if (picked or is_mine) else "1px"};">'
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:center;gap:8px;margin-bottom:4px;">'
                f'<span style="font-weight:700;color:{FG};">{opt["label"]}</span>'
                f'{tag}</div>'
                f'<div class="np-sub">{opt["text"]}</div></div>',
                unsafe_allow_html=True)


def _render_moment(cmp: dict) -> None:
    """The situation being decided, plus what the child actually said."""
    dim = cmp.get("dimension", "")
    dim_html = (f'<span class="np-pill" style="margin-left:8px;">varies: {dim}</span>'
                if dim else "")
    st.markdown(
        f'<div class="np-card" style="margin-bottom:10px;">'
        f'<div class="np-section-title">The moment{dim_html}'
        f'{provenance.icon("comparison")}</div>'
        f'<div class="np-sub">{cmp.get("instance", "")}</div></div>',
        unsafe_allow_html=True)
    if cmp.get("user_message"):
        with st.chat_message("user"):
            st.markdown(f"**{_who()}**  \n{cmp['user_message']}")


def _set_pick(cmp: dict, choice: str) -> None:
    st.session_state[f"sb_pick_{cmp['id']}"] = choice


def _commit_pick(cmp: dict, i: int) -> None:
    """Commit the pick and move the screen on.

    Round 1 reveals nothing, so committing has to advance or the same
    comparison renders again with the pick already recorded. Rounds 2 and 3
    stay put, because the reveal and what follows it happen on this screen.
    """
    choice = st.session_state.get(f"sb_pick_{cmp['id']}")
    if choice:
        _record_pick(cmp, choice, i, advance=(cmp["round"] == 1))


def _render_pick_controls(cmp: dict, rnd: int, i: int) -> str:
    """Which first, then why, then an explicit continue.

    Min: "make the button first, the preferred left and right, and then ask them
    to write the answer, and don't make it go automatically to the next page."
    The reason box used to sit ABOVE the buttons, which asked people to justify
    a choice they had not made yet, and clicking a side in round 1 skipped
    straight past it.
    """
    ss = st.session_state
    b1, b2 = st.columns(2, gap="small")
    b1.button("Prefer left", key=f"sb_ca_{rnd}_{i}", use_container_width=True,
              on_click=_set_pick, args=(cmp, "A"))
    b2.button("Prefer right", key=f"sb_cb_{rnd}_{i}", use_container_width=True,
              on_click=_set_pick, args=(cmp, "B"))
    chosen = ss.get(f"sb_pick_{cmp['id']}", "")
    if chosen:
        st.text_input("Why this one?", key=f"sb_cnote_{rnd}_{i}",
                      placeholder="what tipped it")
    return chosen


def render_confirm() -> None:
    ss = st.session_state
    if ss.get("sb_submitted"):
        st.info("Your responses have been submitted, so this step is read-only. "
                "Continue to the last step to see and download your results.")
        return
    if not ss.sb_answers:
        st.info("Write a rule for at least one case first (previous step).")
        return

    rnd = ss.sb_round
    # These are the FINAL rounds, over the policy synthesized from every theme.
    # The per-theme rounds in _render_theme_test tested each rule on its own;
    # these test whether one policy built from all of them still predicts the
    # same person. Round 1 runs here as well as per theme, and its picks feed
    # the synthesis, so the policy is written from rules plus every pick made
    # anywhere in the session.
    cmps = _round_cmps(rnd)
    if not cmps:
        st.info("No comparisons could be built. Go back and save an answer first.")
        return

    i = ss.sb_cidx

    # ---- round finished -----------------------------------------------------
    if i >= len(cmps):
        if rnd < _LAST_ROUND:
            header("Comparisons",
                   f"Round {rnd} of {_LAST_ROUND} done.")
            if rnd == 1:
                st.success("Next, one policy gets written from every rule you "
                           "wrote and every choice you made. Then you will see "
                           "how it decides on its own.")
            else:
                st.success("Your policy has been sharpened. The last round is "
                           "scored: you will see what it decides, but nothing "
                           "changes any more.")
            _render_policy()
            st.button(f"Start round {rnd + 1}", type="primary",
                      on_click=_advance_round)
            return
        agreed, total = agreement()
        header("Comparisons", "All three rounds are done.")
        if total:
            st.success(f"On the final round your policy chose the same as you on "
                       f"**{agreed} of {total}**.")
            st.caption("This is the scored round: the policy was frozen and "
                       "nothing you did changed it.")
        _render_policy(expanded=True)
        st.button("Start over", type="secondary", on_click=_restart_confirm)
        st.caption("Continue to see and download your results.")
        return

    cmp = cmps[i]
    _mock_note(cmp)
    revealed = ss.sb_revealed.get(f"{rnd}_{i}", False)

    intro = {
        1: "Pick the reply you prefer and say why. Nothing is revealed yet.",
        2: "Pick and say why. Then you will see what your policy chose, and can "
           "tell it what to do differently.",
        3: "Pick and say why. Then you will see what your policy chose. This "
           "round is scored, and nothing changes any more.",
    }[rnd]
    header(f"Round {rnd} of {_LAST_ROUND}",
           f"Comparison {i + 1} of {len(cmps)}. {intro}")
    if rnd > 1:
        _render_policy()

    # ---- the moment, as a conversation ------------------------------------
    _render_moment(cmp)

    # ---- the two candidate replies, highlighted in place once revealed -----
    model = _model_answer(cmp) if revealed else {}
    _render_options(cmp, highlight=model.get("choice", "") if revealed else "",
                    mine=ss.get(f"sb_pick_{cmp['id']}", ""))

    # ---- the action zone, which grows in place rather than replacing --------
    if not revealed:
        chosen = _render_pick_controls(cmp, rnd, i)
        st.button("Continue", key=f"sb_cgo_{rnd}_{i}", type="primary",
                  disabled=not chosen, on_click=_commit_pick, args=(cmp, i))
        if not chosen:
            st.caption("Pick one to continue.")
        elif rnd > 1:
            st.caption("Your policy has already decided this one. It stays hidden "
                       "until you continue, so what you write is your own view "
                       "rather than a reaction to it.")
        return

    row = _row_for(cmp["id"]) or {}
    same = row.get("choice") == model.get("choice")
    tone = "#2E7D4F" if same else "#B0472F"
    verdict = ("You and your policy agree." if same
               else "Your policy chose differently from you.")
    yours = "left" if row.get("choice") == "A" else "right"
    st.markdown(
        f'<div class="np-card" style="margin:10px 0;border-color:{tone};">'
        f'<div class="np-section-title" style="color:{tone};">{verdict}'
        f'{provenance.icon("model_pick")}</div>'
        f'<div class="np-sub"><b>You chose the {yours}.</b> '
        f'Your policy chose because: {model.get("reason", "")}</div></div>',
        unsafe_allow_html=True)

    if rnd == 2:
        st.text_area("What should it have done, and why?",
                     key=f"sb_crit_{rnd}_{i}", height=90,
                     placeholder="Say what you think of that decision and how it "
                                 "should behave differently. Leave blank to "
                                 "change nothing.")
        st.button("Apply and continue", type="primary",
                  key=f"sb_crit_go_{rnd}_{i}", on_click=_apply_critique,
                  args=(cmp, i))
        st.caption("Your policy is updated from what you write here, and the next "
                   "comparison uses the updated version.")
    else:
        st.button("Next", type="primary", key=f"sb_next_{rnd}_{i}",
                  on_click=_next_scored, args=(cmp, i))
        st.caption("This round is scored. Nothing you do here changes the policy.")


# ---------------------------------------------------------------------------
# Step 4: Output
# ---------------------------------------------------------------------------

def _start_edit(theme: str) -> None:
    """From the review page: reopen a theme's workspace to revise its rule.

    This used to call _goto("respond"), a step key removed when the flow became
    theme-first. goto_key no-ops on an unknown key, so the button set the
    editing state and then went nowhere.
    """
    ans = _theme_answer(theme)
    if not ans:
        return
    idx = _theme_index(theme)
    st.session_state[f"sb_answer_{idx}"] = ans.get("ideal_behavior", "")
    _open_theme(theme)
    _goto("themes")
    store.log_event(_rid(), "output", "edit_start", {"theme": theme})


def _submit_all() -> None:
    ss = st.session_state
    ss.sb_submitted = True
    rid = _rid()
    if rid:
        store.mark_submitted(rid)
        ss["resp_completion"] = store.set_completion_code(rid)
        store.log_event(rid, "output", "submit",
                        {"n_answers": len(ss.sb_answers),
                         "n_confirm": len(ss.sb_confirm),
                         "completion_code": ss["resp_completion"]})


def render_output() -> None:
    ss = st.session_state
    if not ss.sb_answers:
        st.info("Author some behaviors first (previous step).")
        return
    artifact = export.build_artifact(
        agent=ss.sb_agent, frame=ss.sb_frame or {}, description=ss.sb_desc,
        audience=ss.sb_audience, intake_reflection=_intake_answers(),
        scenarios=ss.sb_scenarios, answers=ss.sb_answers,
        confirm=ss.sb_confirm, rubric=ss.sb_rubric,
        policy=ss.get("sb_policy"), policy_log=ss.get("sb_policy_log"),
        submitted=bool(ss.get("sb_submitted")))

    header("Your preferences",
           "How you want this agent to behave, as concrete cases with your ideal "
           "behavior for each.")
    st.success(f"Collected {len(ss.sb_answers)} authored behaviors for "
               f"{(ss.sb_frame or {}).get('restated_agent', ss.sb_agent)}.")

    for a in ss.sb_answers:
        score = a.get("rubric_score")
        score_html = (f'<span class="np-pill" style="margin-left:8px;">rubric '
                      f'{score:g}/100</span>' if score else "")
        st.markdown(
            f'<div class="np-card" style="margin-bottom:10px;">'
            f'<div class="np-muted">{a["title"]}{score_html}</div>'
            f'<div class="np-sub" style="margin:2px 0 6px;">{a["situation"]}</div>'
            f'<div class="np-strong">Ideal behavior: {a.get("ideal_behavior", "")}</div>'
            f'</div>', unsafe_allow_html=True)

    if not ss.get("sb_submitted"):
        themes = [a["theme"] for a in ss.sb_answers if a.get("theme")]
        if themes:
            section("Revise before you submit")
            pick = st.selectbox("Pick a rule to revise", options=themes,
                                key="sb_edit_pick")
            st.button("Edit this rule", type="secondary",
                      on_click=_start_edit, args=(pick,))

    decisive = [c for c in ss.sb_confirm if c.get("choice") in ("A", "B")]
    if decisive:
        section("Boundary comparisons")
        for c in decisive:
            ch = c["choice"]
            chosen = c["option_a"] if ch == "A" else c["option_b"]
            st.markdown(
                f'<div class="np-card" style="margin-bottom:10px;">'
                f'<div class="np-muted">{c.get("instance", "")}</div>'
                f'<div class="np-strong" style="margin-top:4px;">Preferred: '
                f'{chosen.get("text", "")}</div></div>', unsafe_allow_html=True)

    st.divider()
    section("Download the benchmark")
    st.caption("Each row is a case and your ideal behavior. Run the situation through "
               "a model and compare its response to your ideal behavior. The "
               "comparisons file adds boundary picks from the confirm step.")
    c1, c2 = st.columns(2)
    profile_json = export.to_json(artifact)
    benchmark_jsonl = export.to_jsonl(ss.sb_answers, agent=ss.sb_agent,
                                      audience=ss.sb_audience)
    c1.download_button("Full profile (JSON)", data=profile_json,
                       file_name="agent_preferences.json", mime="application/json",
                       use_container_width=True)
    c2.download_button("Benchmark (JSONL)", data=benchmark_jsonl,
                       file_name="agent_benchmark.jsonl", mime="application/jsonl",
                       use_container_width=True)
    if decisive:
        st.download_button("Boundary comparisons (JSONL)",
                           data=export.to_confirm_jsonl(ss.sb_confirm),
                           file_name="agent_comparisons.jsonl",
                           mime="application/jsonl", use_container_width=True)

    st.divider()
    if ss.get("sb_submitted"):
        st.success("Your responses are submitted. Thank you for taking part. You "
                   "can still download or email your results above and below.")
        code = ss.get("resp_completion")
        if code:
            st.markdown(
                f'<div class="np-card" style="text-align:center;margin:8px 0;">'
                f'<div class="np-section-title">Your completion code</div>'
                f'<div style="font-family:Menlo,monospace;font-size:24px;'
                f'font-weight:700;letter-spacing:3px;">{code}</div>'
                f'<div class="np-muted" style="margin-top:6px;">If you came from '
                f'Prolific, return to the study page and enter this code to '
                f'confirm your submission.</div></div>', unsafe_allow_html=True)
    else:
        section("Submit your responses")
        st.caption("Submitting finalizes your answers for the study. You can revise "
                   "any answer above before you submit, and every version you save "
                   "is kept.")
        st.button("Submit my responses", type="primary", on_click=_submit_all)

    section("Email me my results")
    if mailer.is_configured():
        st.text_input("Your email address", key="sb_email",
                      placeholder="you@example.com",
                      help="We send your profile JSON and benchmark, with "
                           "instructions for using them in ChatGPT or Claude.")
        if st.button("Send my results", type="secondary"):
            addr = (ss.get("sb_email") or "").strip()
            if "@" not in addr or "." not in addr.split("@")[-1]:
                st.error("Please enter a valid email address.")
            else:
                with st.spinner("Sending..."):
                    err = mailer.send_results(addr, profile_json, benchmark_jsonl)
                if err:
                    st.error(f"Could not send the email: {err}")
                else:
                    rid = _rid()
                    if rid:
                        store.set_email(rid, addr)
                        store.log_event(rid, "output", "email_sent", {"to": addr})
                    st.success("Sent. Check your inbox (and spam folder).")
    else:
        st.caption("Emailing results is not configured on this server. Use the "
                   "download buttons above instead.")


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_RENDERERS = {
    "agent": render_agent,
    "describe": render_describe,
    "themes": render_themes,
    "confirm": render_confirm,
    "output": render_output,
}


def render(key: str) -> None:
    _RENDERERS[key]()
