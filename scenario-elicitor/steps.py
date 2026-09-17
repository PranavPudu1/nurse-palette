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


def _llm_failure_banner(data: dict) -> None:
    """A loud, page-level banner when a generation call failed.

    The quiet fallback exists so offline tests run; in a live session it made
    an out-of-credits API account look like a broken app (placeholder cases
    with no explanation, Sep 16). Errors are surfaced where they happen."""
    err = (data or {}).get("_error", "")
    if not err:
        return
    hint = (" The OpenAI account is out of credits; add credits at "
            "platform.openai.com under Billing."
            if "credit" in err or "insufficient_quota" in err else "")
    st.error("The AI service returned an error, so placeholder content is "
             f"shown instead of real results.{hint}\n\nDetails: {err}")


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


def _intake_ready() -> None:
    st.session_state["sb_intake_ready"] = True


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
    # Nothing generates until the person confirms the age and name are right:
    # the questions used to appear instantly, built from the default age
    # before anyone had picked one.
    if "sb_rqi" not in ss and not ss.get("sb_intake_ready"):
        st.write("")
        _instruction("When the age and name above look right, continue. Two "
                     "short questions about you and your child come next.")
        st.button("Next: two quick questions", key="sb_intake_go",
                  type="primary", on_click=_intake_ready)
        return
    # The questions are minted for a specific age. They used to generate off
    # the default (9-12) the instant the page opened, so picking 16-18 left
    # questions about a much younger child on screen. Changing the age
    # regenerates them; the name does not (it changes on every keystroke).
    age = (ss.get("sb_age_input") or "").strip()
    if ss.get("sb_rqi") is not None and "sb_rqi_age" not in ss:
        ss["sb_rqi_age"] = age    # sessions from before this existed
    if ss.get("sb_rqi") and ss.get("sb_rqi_age") != age:
        old = [{"question": (q.get("question") or "").strip(),
                "answer": (ss.get(f"sb_rai_{i}") or "").strip()}
               for i, q in enumerate(ss.get("sb_rqi") or [])]
        store.log_event(_rid(), "describe", "reflect_intake_regen",
                        {"age_from": ss.get("sb_rqi_age"), "age_to": age,
                         "previous": old})
        for i in range(len(ss.get("sb_rqi") or [])):
            ss.pop(f"sb_rai_{i}", None)
            ss.pop(f"w_sb_rai_{i}", None)
        ss.pop("sb_rqi", None)
    if "sb_rqi" not in ss:
        with st.spinner("Preparing two questions..."):
            rq = llm.reflect_intake(ss.sb_agent, _does(), who)
        ss["sb_rqi"] = rq.get("questions") or []
        ss["sb_rqi_age"] = age
        _llm_failure_banner(rq)
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


# --- versions and their chats -------------------------------------------------
# Versions are first-class. v1 is the first draft, saved automatically on
# leaving Consider + write ("1 is the first rule"); later versions are created
# with "Save as new version"; a round-2 edit appends one automatically, so
# nothing untitled ever speaks. "Original" is the baseline: no rule at all.
# Every version keeps its own persistent chat thread, so a reply can always be
# traced to the version that produced it. The testing paths follow PolicyPad,
# Feng et al. CHI '26, §5.2.5. See docs/provenance.md.

ORIGINAL = "Original"


def _vers(idx: int) -> list[str]:
    """The saved rule texts for this theme; entry n-1 is version v{n}."""
    return st.session_state.setdefault(f"sb_vers_{idx}", [])


def _vlabels(idx: int, include_original: bool = True) -> list[str]:
    labels = [f"v{n + 1}" for n in range(len(_vers(idx)))]
    return ([ORIGINAL] + labels) if include_original else labels


def _vrule(idx: int, label: str) -> str:
    """Rule text for a version label; Original (and anything unknown) is empty."""
    if label and label.startswith("v"):
        try:
            return _vers(idx)[int(label[1:]) - 1]
        except (ValueError, IndexError):
            return ""
    return ""


def _save_version(idx: int, text: str | None = None) -> str:
    """Append text (default: the box) as the next version and select it."""
    ss = st.session_state
    text = (ss.get(f"sb_answer_{idx}") or "" if text is None else text).strip()
    if not text:
        return ""
    vers = _vers(idx)
    if not (vers and vers[-1].strip() == text):
        vers.append(text)
        store.log_event(_rid(), "themes", "save_version",
                        {"theme": ss.get("sb_theme"), "label": f"v{len(vers)}",
                         "rule": text})
    label = f"v{len(vers)}"
    ss[f"sb_vsel_{idx}"] = label
    ss[f"w_sb_vsel_{idx}"] = label
    return label


def _select_version(idx: int) -> None:
    """Dropdown change: load that version's text into the box (Original: empty)."""
    ss = st.session_state
    label = ss.get(f"w_sb_vsel_{idx}", ORIGINAL)
    ss[f"sb_vsel_{idx}"] = label
    text = _vrule(idx, label)
    ss[f"sb_answer_{idx}"] = text
    ss[f"w_sb_answer_{idx}"] = text


def _chats(idx: int) -> dict:
    return st.session_state.setdefault(f"sb_chats_{idx}", {})


def _thread(idx: int, label: str, scenario: dict) -> dict:
    """One persistent chat thread per version.

    Original seeds from the case's example exchange (the baseline reply already
    exists, no API call). A rule version starts empty; its first reply is
    generated under that rule when the person asks.
    """
    chats = _chats(idx)
    if label not in chats:
        turns = []
        if label == ORIGINAL:
            ex = scenario.get("example_exchange") or {}
            if ex.get("user_message"):
                turns.append({"role": "user", "content": ex["user_message"]})
            if ex.get("ai_response"):
                turns.append({"role": "assistant", "content": ex["ai_response"],
                              "version": ORIGINAL, "rule": "", "what_changed": ""})
        chats[label] = {"turns": turns}
    return chats[label]


def _default_question(scenario: dict) -> str:
    return ((scenario.get("example_exchange") or {}).get("user_message") or "").strip()


def _request_ask(idx: int, k: int) -> None:
    msg = (st.session_state.get(f"sb_cq_{idx}_{k}") or "").strip()
    if msg:
        st.session_state["_sb_ask"] = (idx, k, msg)
        st.session_state[f"sb_cq_{idx}_{k}"] = ""


def _request_ask_default(idx: int, k: int, msg: str) -> None:
    st.session_state["_sb_ask"] = (idx, k, msg)


def _ask_version(idx: int, k: int, scenario: dict, msg: str) -> None:
    """Ask one version a question, inside its own thread."""
    ss = st.session_state
    label = ss.get(f"sb_cmpv_{idx}_{k}") or ORIGINAL
    rule = _vrule(idx, label)
    turns = _thread(idx, label, scenario)["turns"]
    turns.append({"role": "user", "content": msg})
    with st.spinner(f"Asking {label}..."):
        data = llm.agent_reply(ss.sb_agent, _does(), ss.sb_audience, scenario,
                               rule or None, turns)
    turns.append({"role": "assistant",
                  "content": (data.get("response") or "").strip(),
                  "version": label, "rule": rule,
                  "what_changed": (data.get("what_changed") or "").strip(),
                  "_mock": data.get("_mock"), "_error": data.get("_error")})
    store.log_event(_rid(), "themes", "chat",
                    {"case_idx": idx, "version": label, "message": msg,
                     "reply": turns[-1]["content"]})


def _render_thread(idx: int, label: str, scenario: dict, height: int = 240) -> None:
    turns = _thread(idx, label, scenario)["turns"]
    with st.container(height=height, border=False):
        if not turns:
            st.caption("No conversation yet. Ask the question below.")
        for t in turns:
            if t["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(f"**{_who()}**  \n{t['content']}")
            else:
                _mock_note(t)
                with st.chat_message("assistant"):
                    ikey = ("rule_reply" if (t.get("rule") or "").strip()
                            else "baseline_reply")
                    st.markdown(f"**{t.get('version', label)}** "
                                f"{provenance.icon(ikey)}  \n{t['content']}",
                                unsafe_allow_html=True)
                    if t.get("what_changed"):
                        st.caption(f"What this version changed: {t['what_changed']}")


def _ui_compare_column(idx: int, k: int, scenario: dict) -> None:
    """One compare column: pick a version, see its thread, ask it things."""
    ss = st.session_state
    options = ["Pick a version..."] + _vlabels(idx)
    cur = ss.get(f"sb_cmpv_{idx}_{k}") or options[0]
    if cur not in options:
        cur = options[0]
    pick = st.selectbox(f"Column {k + 1} version", options,
                        index=options.index(cur), key=f"w_sb_cmpv_{idx}_{k}",
                        label_visibility="collapsed")
    if pick == options[0]:
        ss[f"sb_cmpv_{idx}_{k}"] = ""
        st.caption("Each column chats with one version, so you can compare "
                   "them side by side.")
        return
    ss[f"sb_cmpv_{idx}_{k}"] = pick
    _render_thread(idx, pick, scenario, height=320)
    dq = _default_question(scenario)
    if dq and not _thread(idx, pick, scenario)["turns"]:
        st.button(f"Ask the case's question", key=f"sb_dq_{idx}_{k}",
                  type="secondary", use_container_width=True,
                  on_click=_request_ask_default, args=(idx, k, dq))
    st.text_input("Ask this version", key=f"sb_cq_{idx}_{k}",
                  placeholder=f"Ask {pick} something...",
                  label_visibility="collapsed",
                  on_change=_request_ask, args=(idx, k))


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
        # Versions are first-class now: the trajectory is the version store,
        # and the transcript is every version's own thread.
        "rule_versions": [{"label": f"v{n + 1}", "rule": r}
                          for n, r in enumerate(_vers(idx))],
        "n_tests": sum(1 for th in _chats(idx).values()
                       for t in th.get("turns", [])
                       if t.get("role") == "assistant" and (t.get("rule") or "").strip()),
        "final_version": ss.get(f"sb_final_label_{idx}", ""),
        "transcript": {label: th.get("turns", [])
                       for label, th in _chats(idx).items()},
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


def _mic(canonical: str) -> None:
    """A dictation popover for a writing box.

    Streamlit cannot overlay an icon inside a text area, so the mic is a
    compact popover button under the box. The transcription runs inline
    rather than in a callback so its spinner renders inside the popover.
    Transcribed text is appended to what is already in the box, never
    overwriting it, and lands in both the canonical and widget keys.
    """
    ss = st.session_state
    mkey = f"w_mic_{canonical}"
    with st.popover("🎤 Dictate", help="Speak instead of typing. Record, "
                                       "then put the words in the box."):
        audio = st.audio_input("Record, then stop", key=mkey,
                               label_visibility="collapsed")
        if audio is not None and st.button("Put it in the box",
                                           key=f"micgo_{canonical}",
                                           type="primary"):
            with st.spinner("Transcribing..."):
                out = llm.transcribe(audio.getvalue())
            if out.get("_error"):
                err = out["_error"]
                hint = (" The OpenAI account is out of credits."
                        if "credit" in err or "insufficient_quota" in err
                        else "")
                st.error(f"Transcription failed.{hint}\n\n{err}")
            elif out.get("_mock"):
                st.error("No API key is configured, so dictation is "
                         "unavailable in this session.")
            elif not out.get("text"):
                st.warning("Nothing was heard in that recording. Try again "
                           "a little closer to the mic.")
            else:
                existing = (ss.get(canonical) or "").strip()
                merged = (existing + " " + out["text"]).strip()
                ss[canonical] = merged
                ss[f"w_{canonical}"] = merged
                ss.pop(mkey, None)   # reset the recorder
                store.log_event(_rid(), "dictate", "transcribed",
                                {"box": canonical,
                                 "chars": len(out["text"])})
                st.rerun()


def _kept_text(canonical: str, label: str, mic: bool = True, **kw) -> str:
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
    if mic:
        _mic(canonical)
    return val


def _live(key: str) -> str:
    """The freshest text for a mirrored box.

    Widget state (the w_ key) updates the moment a button is tapped, but the
    canonical key only catches up when the box next renders. Validation that
    runs inside a click callback must therefore read the widget key first, or
    it judges the text as it was one interaction ago. On phones that was a
    dead end: gating buttons were disabled on stale-empty state, and a disabled
    button cannot receive the tap that would refresh it.
    """
    ss = st.session_state
    v = ss.get(f"w_{key}")
    return str(v) if v is not None else str(ss.get(key) or "")


def _answered(key: str) -> bool:
    return len(_live(key).strip()) >= MIN_ANSWER


_REFUSALS = {"skip", "idk", "no", "na", "n/a", "none", "nothing", "-", "."}


def _too_thin(draft: str) -> bool:
    """A draft with nothing to ask questions about.

    Deterministic guard in front of the question generator: prompt
    instructions alone did not stop the model from producing three polished
    questions about the rule "skip". Catches refusals and few-word drafts;
    longer gibberish is the prompt's job.
    """
    d = (draft or "").strip()
    return (not d or d.lower() in _REFUSALS or len(d) < 20
            or len(d.split()) < 4)


def _show_flash(key: str) -> None:
    """Show and clear a one-shot validation message set by a click handler."""
    msg = st.session_state.pop(key, None)
    if msg:
        st.warning(msg)


def _instruction(text: str) -> None:
    """A what-to-do line, deliberately bigger than a caption.

    Min asked for one-sentence instructions on each section that people
    actually notice; st.caption renders too small for that."""
    st.markdown(f'<div class="np-sub" style="margin:2px 0 10px;color:{FG};">'
                f'{text}</div>', unsafe_allow_html=True)


_CW_STEPS = ("Read the three conversations on the left.",
             "Answer the questions below.",
             "Write one rule that should hold across all of them.")


def _cw_header(sub: int) -> None:
    """Consider + write's three sub-steps: done ones dimmed with a check,
    the current one big and bold, later ones dimmed. The screen reveals one
    sub-step at a time instead of showing everything at once."""
    rows = []
    for i, text in enumerate(_CW_STEPS):
        if i < sub:
            badge_bg, badge_fg, badge = SURFACE_BG, MUTED_FG, "&#10003;"
            style = f"font-size:13px;color:{MUTED_FG};"
        elif i == sub:
            badge_bg, badge_fg, badge = PRIMARY, "#fff", str(i + 1)
            style = f"font-size:17px;font-weight:700;color:{FG};"
        else:
            badge_bg, badge_fg, badge = SURFACE_BG, MUTED_FG, str(i + 1)
            style = f"font-size:13px;color:{MUTED_FG};"
        rows.append(
            f'<div style="display:flex;align-items:baseline;gap:9px;'
            f'margin-bottom:6px;">'
            f'<span style="flex:0 0 auto;display:inline-flex;'
            f'align-items:center;justify-content:center;width:21px;'
            f'height:21px;border-radius:999px;background:{badge_bg};'
            f'color:{badge_fg};font-size:12px;font-weight:700;">{badge}'
            f'</span><span style="{style}line-height:1.45;">{text}'
            f'</span></div>')
    st.markdown(f'<div style="margin:2px 0 14px;">{"".join(rows)}</div>',
                unsafe_allow_html=True)


def _section_step(n: int, text: str) -> None:
    """A big numbered orange section heading. Same family as _cw_header but
    single-line and ungated: on screens where the sections form a loop
    (compare, edit, compare again), the numbers give the reading order
    without locking anything."""
    st.markdown(
        f'<div style="display:flex;align-items:baseline;gap:9px;'
        f'margin:4px 0 10px;">'
        f'<span style="flex:0 0 auto;display:inline-flex;align-items:center;'
        f'justify-content:center;width:23px;height:23px;border-radius:999px;'
        f'background:{PRIMARY};color:#fff;font-size:13px;font-weight:700;">'
        f'{n}</span>'
        f'<span style="font-size:17px;font-weight:700;color:{PRIMARY};'
        f'line-height:1.4;">{text}</span></div>',
        unsafe_allow_html=True)


def _section_num(n: int, label: str) -> None:
    """A section title carrying the step number it corresponds to, so the
    checklist at the top of the write screen maps visibly onto the page."""
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:8px;'
        f'margin-bottom:8px;">'
        f'<span style="flex:0 0 auto;display:inline-flex;align-items:center;'
        f'justify-content:center;width:19px;height:19px;border-radius:999px;'
        f'background:{PRIMARY};color:#fff;font-size:11px;font-weight:700;">'
        f'{n}</span>'
        f'<span class="np-section-title" style="margin-bottom:0;">{label}'
        f'</span></div>', unsafe_allow_html=True)


def _cw_sub(idx: int) -> int:
    return int(st.session_state.get(f"sb_cw_{idx}", 0))


def _cw_done_reading(idx: int) -> None:
    st.session_state[f"sb_cw_{idx}"] = 1


def _cw_done_answering(idx: int) -> None:
    ss = st.session_state
    sync_widget_mirrors()
    missing = _unanswered(idx, "b")
    if missing:
        ss[f"_flash_cw_{idx}"] = _needs(len(missing),
                                        len(_question_slots(idx, "b")))
        return
    ss[f"sb_cw_{idx}"] = 2


def sync_widget_mirrors() -> None:
    """Copy every mounted mirrored widget's value back to its canonical key.

    Called from navigation callbacks: without it, text typed right before
    tapping Back or Continue is dropped, because the mirror normally happens
    only when the box renders again, and navigation unmounts it first.
    """
    ss = st.session_state
    for k in list(ss.keys()):
        if isinstance(k, str) and k.startswith("w_sb_") and isinstance(ss[k], str):
            ss[k[2:]] = ss[k]


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


def _render_rubric_view() -> None:
    """The rubric, readable but no longer editable.

    The editable form was an iRULER carryover, useful while the rubric was
    being tuned internally. Min: in this context it is not going to be
    editable. It stays visible because seeing the criteria helps people aim
    their rule (Eve: the rubric would guide what the rule should look like).
    """
    ss = st.session_state
    with st.expander("View the rubric your rule is checked against"):
        st.caption("Your rule is scored on these criteria. Higher levels are "
                   "more specific and more actionable.")
        for c in ss.sb_rubric:
            st.markdown(f"**{c['name']}** ({c['weight']}%)")
            for v in range(4, 0, -1):
                st.caption(f"Level {v}: {c['levels'][str(v)]}")


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
            data = llm.expand_theme(ss.sb_agent, _does(), "",
                                    ss.sb_audience, theme, titles, want)
        _llm_failure_banner(data)
        # theme= forces the category, so a near-miss from the model cannot land
        # a case in a bucket no theme card can reach.
        _append_new(_ingest_scenarios(data, theme=theme))
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
        st.button("Revise this rule", key=f"sb_open_{name}", type="secondary",
                  use_container_width=True, on_click=_open_theme, args=(name,))
    else:
        st.button("Write a rule for this", key=f"sb_open_{name}", type="primary",
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
    _section_num(2, "How your rule scores")
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
    _render_rubric_view()

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
# The workspace: the split layout, staged as the meeting set it
# ---------------------------------------------------------------------------
# Min chose the split prototype and fixed the stage order, so the other
# prototypes and their switcher are gone. The case holds the left column and
# never moves; the work steps down the right through four stages:
#   1. Consider + write   the questions first, the rule box directly below
#                         them, so the answers stay visible while writing
#   2. Score + revise     the same rule box checked against the rubric, with
#                         the reflections one click away in an accordion
#   3. Sharpen            the after-questions alone; a placeholder Min may cut
#   4. Test               the chat is the stage: try the rule, browse and
#                         reload versions, and mark ONE as final before saving


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
    _section_num(2, "Before you answer")
    st.caption("There is no right answer. What you write here is used when your "
               "rule is checked, so answer all of them before you write.")
    probe = (scenario.get("probe") or "").strip()
    if probe:
        _render_one_question(f"sb_rap_{idx}", "As you write, consider", probe,
                             "probe")
    _render_reflection(idx, "b", ss[f"sb_rqb_{idx}"])


def _ui_after(idx: int) -> None:
    """The after-questions on Sharpen, about the rule as written.

    They only exist after the first rubric check generates them; before that
    the stage says so instead of sitting empty. The regenerate button exists
    because the questions were minted from one draft and the rule moves on;
    Min asked for a way to bring them back in line with the current text.
    """
    ss = st.session_state
    qs = ss.get(f"sb_rqa_{idx}")
    if not qs and ss.get(f"sb_rqa_thin_{idx}"):
        _instruction("Your rule is only a few words, so there is nothing to "
                     "ask about yet. Write what the AI should do, what it "
                     "should not do, and how to handle the hard part, then "
                     "generate your questions.")
        st.button("Generate questions from my current rule",
                  key=f"sb_regen_{idx}", type="primary",
                  on_click=_regen_questions_click, args=(idx,))
        _show_flash(f"_flash_regen_{idx}")
        return
    if not qs:
        st.caption("These questions unlock after you check your rule on the "
                   "previous stage. They are optional either way.")
        return
    _instruction("Answer these questions about your reasoning. They are "
                 "optional, and there are no wrong answers.")
    _render_reflection(idx, "a", qs)
    if len(qs) < prompts.N_REFLECT_AFTER:
        st.caption("Write more in your rule and regenerate to get more "
                   "questions.")
    src = (ss.get(f"sb_rqa_src_{idx}") or "").strip()
    live = _live(f"sb_answer_{idx}").strip()
    if src and live and src != live:
        st.caption("Your rule changed since these questions were made. "
                   "Regenerate to match what it says now.")
    st.button("New questions from my current rule", key=f"sb_regen_{idx}",
              type="secondary",
              help="Rereads the rule as it stands and asks fresh questions "
                   "about it. Your current answers are kept in the study log.",
              on_click=_regen_questions_click, args=(idx,))
    _show_flash(f"_flash_regen_{idx}")


def _ui_rule(idx: int, height: int = 200) -> None:
    """The plain rule box, for Consider + write only: the first draft has no
    versions yet, so no dropdown until it is saved as v1 on leaving the stage."""
    _section_num(3, "Your rule for this theme")
    _kept_text(
        f"sb_answer_{idx}", "Your rule", height=height,
        label_visibility="collapsed",
        placeholder="One rule that should hold across all three of these "
                    "conversations. Say what the AI should do, what it should "
                    "not do, and how to handle the hard part.")


def _save_version_click(idx: int) -> None:
    ss = st.session_state
    draft = _live(f"sb_answer_{idx}").strip()
    if not draft:
        ss[f"_flash_vers_{idx}"] = "Write the rule first, then save it as a version."
        return
    if draft == _vrule(idx, ss.get(f"sb_vsel_{idx}", ORIGINAL)).strip():
        ss[f"_flash_vers_{idx}"] = ("No changes since the selected version, so "
                                    "there is nothing new to save.")
        return
    ss[f"sb_answer_{idx}"] = draft
    _save_version(idx)


def _check_click(idx: int) -> None:
    ss = st.session_state
    draft = _live(f"sb_answer_{idx}").strip()
    if len(draft) < MIN_ANSWER:
        ss[f"_flash_vers_{idx}"] = "Write your rule first, then check it."
        return
    ss[f"sb_answer_{idx}"] = draft
    _flag("_sb_check")


def _regen_questions_click(idx: int) -> None:
    ss = st.session_state
    draft = _live(f"sb_answer_{idx}").strip()
    if _too_thin(draft):
        ss[f"_flash_regen_{idx}"] = ("The rule is still only a few words. "
                                     "Write what you want the AI to do, then "
                                     "generate questions about it.")
        return
    ss[f"sb_answer_{idx}"] = draft
    _flag("_sb_requestions")


def _ui_rule_versioned(idx: int, height: int = 170, check: bool = False,
                       step: int | None = None) -> None:
    """The rule box with its version dropdown on the title row.

    The dropdown answers "which version is this?" at all times: selecting one
    loads its text (Original loads empty), and "Save as new version" is the
    single place versions are born after v1. Streamlit cannot overlay a widget
    inside a text area, so "top right of the text box" renders as a compact
    selectbox on the box's title row.
    """
    ss = st.session_state
    labels = _vlabels(idx)
    cur = ss.get(f"sb_vsel_{idx}") or (labels[-1] if len(labels) > 1 else ORIGINAL)
    if cur not in labels:
        cur = labels[-1]
    ss[f"sb_vsel_{idx}"] = cur
    head, dd = st.columns([2.4, 1], gap="small")
    with head:
        if step is None:
            section("Your rule for this theme")
        else:
            _section_num(step, "Your rule for this theme")
    with dd:
        st.selectbox("Version", labels, index=labels.index(cur),
                     key=f"w_sb_vsel_{idx}", label_visibility="collapsed",
                     on_change=_select_version, args=(idx,),
                     help="Which version is in the box right now. Picking one "
                          "loads it; Original is empty (no rule).")
    draft = _kept_text(
        f"sb_answer_{idx}", "Your rule", height=height,
        label_visibility="collapsed",
        placeholder="Edit the rule here, then save it as a new version.").strip()
    b1, b2 = st.columns(2, gap="small")
    b1.button("Save as new version", key=f"sb_savev_{idx}",
              use_container_width=True, type="secondary",
              help="Keeps the selected version and adds this text as the next one.",
              on_click=_save_version_click, args=(idx,))
    if check:
        b2.button("Check my answer", key=f"sb_check_{idx}",
                  use_container_width=True, type="primary",
                  on_click=_check_click, args=(idx,))
    _show_flash(f"_flash_vers_{idx}")


# ---- stages ----------------------------------------------------------------

_STAGES = ("Consider + write", "Score + revise", "Sharpen", "Test")

# How the two columns split, by stage. The case stays on the left except while
# testing, when the versions take its place (the conversation lives in the
# chat there). The working column widens where the work is.
_C_SPLIT = {0: [1, 1.7], 1: [1, 1.3], 2: [1, 1.3], 3: [1, 1.6]}


def _stage(idx: int) -> int:
    return int(st.session_state.get(f"sb_stage_{idx}", 0))


def _set_stage(idx: int, n: int) -> None:
    st.session_state[f"sb_stage_{idx}"] = max(0, min(len(_STAGES) - 1, n))


def _leave_consider(idx: int) -> None:
    """Stage 0 -> 1 captures the first draft and saves it as v1."""
    ss = st.session_state
    if not (ss.get(f"sb_first_{idx}") or "").strip():
        ss[f"sb_first_{idx}"] = (ss.get(f"sb_answer_{idx}") or "").strip()
    _save_version(idx)   # "1 is the first rule"
    _set_stage(idx, 1)


def _try_next(idx: int, cur: int) -> None:
    """Advance a stage, gating at click time rather than by disabling the
    button. A disabled button never receives the tap that would commit the
    just-typed text (the mobile dead end), so Next is always tappable and
    explains what is missing instead."""
    ss = st.session_state
    sync_widget_mirrors()
    if cur == 0:
        missing = _unanswered(idx, "b")
        if missing:
            ss[f"_flash_stage_{idx}"] = _needs(len(missing),
                                               len(_question_slots(idx, "b")))
            return
        if not _live(f"sb_answer_{idx}").strip():
            ss[f"_flash_stage_{idx}"] = ("With this information, write your "
                                         "rule to continue.")
            return
        _leave_consider(idx)
    else:
        _set_stage(idx, cur + 1)


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
    """Forward out of Consider + write needs the questions AND a first draft;
    everything else is free. Back never gates."""
    ss = st.session_state
    cur = _stage(idx)
    missing = _unanswered(idx, "b") if cur == 0 else []
    no_rule = cur == 0 and not (ss.get(f"sb_answer_{idx}") or "").strip()
    c1, c2 = st.columns([1, 1], gap="small")
    if cur > 0:
        c1.button("Back", key=f"sb_stback_{idx}_{cur}", use_container_width=True,
                  type="secondary", on_click=_set_stage, args=(idx, cur - 1))
    if cur < len(_STAGES) - 1:
        c2.button(f"Next: {_STAGES[cur + 1]}", key=f"sb_stnext_{idx}_{cur}",
                  use_container_width=True, type="primary",
                  on_click=_try_next, args=(idx, cur))
    if missing:
        st.caption(_needs(len(missing), len(_question_slots(idx, "b"))))
    elif no_rule:
        st.caption("With this information, write your rule to continue.")
    _show_flash(f"_flash_stage_{idx}")


# ---- the Test stage: versions and the final pick ---------------------------




def _ui_final_panel(idx: int) -> None:
    """The final-rule picker: the dropdown IS the final selection.

    Min: people may decide version four was the best of six, so the final
    version is chosen explicitly rather than assumed to be the last one.
    """
    ss = st.session_state
    section("Your final rule")
    labels = _vlabels(idx, include_original=False)
    if not labels:
        st.caption("Save a version of your rule first.")
        return
    cur = ss.get(f"sb_final_{idx}")
    if cur not in labels:
        cur = labels[-1]
        ss[f"sb_final_{idx}"] = cur
    pick = st.selectbox("Final version", labels, index=labels.index(cur),
                        key=f"w_sb_final_{idx}", label_visibility="collapsed",
                        help="The version the comparisons will test and the "
                             "export keeps.")
    ss[f"sb_final_{idx}"] = pick
    st.markdown(f'<div class="np-card-muted" style="font-size:13px;">'
                f'{_vrule(idx, pick)}</div>', unsafe_allow_html=True)
    st.button("Load this version into the box", key=f"sb_loadv_{idx}",
              type="secondary", use_container_width=True,
              on_click=_load_final_into_box, args=(idx,))


def _load_final_into_box(idx: int) -> None:
    ss = st.session_state
    label = ss.get(f"sb_final_{idx}", "")
    rule = _vrule(idx, label)
    if rule:
        ss[f"sb_answer_{idx}"] = rule
        ss[f"w_sb_answer_{idx}"] = rule
        ss[f"sb_vsel_{idx}"] = label
        ss[f"w_sb_vsel_{idx}"] = label
        store.log_event(_rid(), "themes", "load_version",
                        {"theme": ss.sb_theme, "label": label})


def _ui_save(theme: str, cases: list[dict], idx: int) -> None:
    """Save the marked final version and move on to the comparisons."""
    ss = st.session_state
    missing = _unanswered(idx, "b")
    final = _vrule(idx, ss.get(f"sb_final_{idx}", "")).strip()
    st.button("Save this rule and test it", key=f"sb_save_{idx}", type="primary",
              use_container_width=True,
              on_click=_save_final, args=(theme, cases, idx))
    if missing:
        st.caption(_needs(len(missing), len(_question_slots(idx, "b"))))
    elif not final:
        st.caption("Pick your final version to continue.")
    _show_flash(f"_flash_save_{idx}")


def _save_final(theme: str, cases: list[dict], idx: int) -> None:
    """The marked version becomes the rule of record before saving."""
    ss = st.session_state
    sync_widget_mirrors()
    missing = _unanswered(idx, "b")
    if missing:
        ss[f"_flash_save_{idx}"] = _needs(len(missing),
                                          len(_question_slots(idx, "b")))
        return
    label = ss.get(f"sb_final_{idx}", "")
    rule = _vrule(idx, label).strip()
    if not rule:
        ss[f"_flash_save_{idx}"] = "Pick your final version to continue."
        return
    ss[f"sb_answer_{idx}"] = rule
    ss[f"w_sb_answer_{idx}"] = rule
    ss[f"sb_final_label_{idx}"] = label
    _save_theme_rule(theme, cases)


# ---- the workspace ---------------------------------------------------------

def _workspace(idx: int, theme: str, cases: list[dict], scenario: dict) -> None:
    """Split: the case holds the left, the work steps down the right.

    The Test stage breaks the split: the final-rule picker and the working box
    share the top row, and below them three columns each chat with one version,
    side by side.
    """
    ss = st.session_state
    cur = _stage(idx)
    draft = (ss.get(f"sb_answer_{idx}") or "").strip()
    if cur == 3:
        # Three numbered sections, ungated: comparing and editing is a loop,
        # so the numbers give the reading order without locking anything.
        _render_stage_rail(idx)
        _section_step(1, "Compare the versions you wrote")
        _instruction("Pick a version in each column and ask it questions. "
                     "Original is the agent with no rule at all.")
        c0, c1, c2 = st.columns(3, gap="medium")
        for k, col in enumerate((c0, c1, c2)):
            with col, st.container(border=True):
                _ui_compare_column(idx, k, scenario)
        st.divider()
        _section_step(2, "Update your rule, if you want")
        _instruction("Edit it here and save it as a new version, then "
                     "compare again above.")
        _ui_rule_versioned(idx, height=130)
        st.divider()
        _section_step(3, "Pick your final version and save it")
        fincol, savecol = st.columns([1.3, 1], gap="medium")
        with fincol:
            _instruction("The version you pick here is your rule of record.")
            _ui_final_panel(idx)
        with savecol:
            _instruction("Then save it. The next screens test this rule.")
            _ui_save(theme, cases, idx)
        _render_stage_nav(idx)
        return
    left, right = st.columns(_C_SPLIT[cur], gap="medium")
    with left:
        _ui_cases(cases)
    with right:
        _render_stage_rail(idx)
        if cur == 0:
            sub = _cw_sub(idx)
            _cw_header(sub)
            if sub == 0:
                st.button("Done reading", key=f"sb_cwr_{idx}", type="primary",
                          on_click=_cw_done_reading, args=(idx,))
            elif sub == 1:
                _ui_before(idx, scenario)
                st.button("Done answering", key=f"sb_cwa_{idx}",
                          type="primary",
                          on_click=_cw_done_answering, args=(idx,))
                _show_flash(f"_flash_cw_{idx}")
            else:
                _ui_before(idx, scenario)
                _instruction("Use your answers above: say what the AI "
                             "should do, what it should not do, and how to "
                             "handle the hard part.")
                _ui_rule(idx, height=150)
        elif cur == 1:
            _instruction("Workshop your rule: check it against the rubric, "
                         "edit, and save new versions as it improves.")
            _ui_rule_versioned(idx, height=170, check=True, step=1)
            with st.expander("Your reflections"):
                answered = [r for r in _reflection_answers(idx)
                            if r["placement"] == "before"]
                if not answered:
                    st.caption("Nothing written yet.")
                for r in answered:
                    st.markdown(f"**{r['question']}**")
                    st.markdown(r["answer"])
            _render_scores(ss.get(f"sb_fb_{idx}"), ss.sb_rubric, idx, draft)
            if ss.get(f"sb_fb_{idx}"):
                _instruction("Use this feedback to edit your rule above and "
                             "check it again, or go to Sharpen when you are "
                             "happy with it.")
        else:
            # Sharpen reads top to bottom the way Min described it: the rule
            # you wrote, shown not editable; the questions about it; then the
            # box to revise it, each under a numbered heading.
            _section_step(1, "The rule you wrote")
            _render_rule_reminder(idx)
            _section_step(2, "Answer the questions about it")
            _ui_after(idx)
            _section_step(3, "Sharpen your rule")
            _instruction("Use your answers to sharpen the rule here, then "
                         "save it as a new version.")
            _ui_rule_versioned(idx, height=150)
        if cur != 0 or _cw_sub(idx) == 2:
            _render_stage_nav(idx)


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

    revisiting = theme in (ss.get("sb_themes_done") or [])
    count = (f"Revising a finished theme" if revisiting and
             n_done >= wizard.N_THEMES else
             f"Theme {min(n_done + 1, wizard.N_THEMES)} of {wizard.N_THEMES}")
    header(meta["name"], f"{count}. {meta['blurb']}")
    st.button("Back to the themes", key="sb_back_themes", type="secondary",
              on_click=_close_theme)
    _workspace(idx, theme, cases, scenario)


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
                ss.sb_agent, _does(), "", ss.sb_audience, scenario, draft,
                ss.sb_rubric, reflection=_reflection_answers(idx))
        ss[f"sb_lastfb_{idx}"] = ss[f"sb_fb_{idx}"]
        ss[f"sb_nrev_{idx}"] = ss.get(f"sb_nrev_{idx}", 0) + 1
        if f"sb_rqa_{idx}" not in ss:
            if _too_thin(draft):
                # No API call for "skip": Sharpen explains instead of asking
                # invented questions about a rule that is not there.
                ss[f"sb_rqa_thin_{idx}"] = True
                store.log_event(_rid(), "themes", "reflect_after_thin",
                                {"theme": ss.sb_theme, "draft": draft})
            else:
                with st.spinner("Reading what you wrote..."):
                    rq = llm.reflect_after(ss.sb_agent, _does(),
                                           ss.sb_audience, scenario, draft)
                ss[f"sb_rqa_{idx}"] = rq.get("questions") or []
                ss[f"sb_rqa_src_{idx}"] = draft
                ss.pop(f"sb_rqa_thin_{idx}", None)
                store.log_event(_rid(), "themes", "reflect_after",
                                {"theme": ss.sb_theme,
                                 "questions": ss[f"sb_rqa_{idx}"]})
        store.log_event(_rid(), "themes", "check",
                        {"theme": ss.sb_theme, "draft": draft,
                         "levels": _levels_by_name(ss[f"sb_fb_{idx}"]),
                         "n_check": ss[f"sb_nrev_{idx}"]})
    if ss.get("_sb_requestions"):
        del ss["_sb_requestions"]
        draft = (ss.get(f"sb_answer_{idx}") or "").strip()
        ss.pop(f"sb_rqa_thin_{idx}", None)
        # The old questions and whatever was typed under them go to the event
        # log before being replaced: iterations are data, not scratch.
        pairs = []
        for i, q in enumerate(ss.get(f"sb_rqa_{idx}") or []):
            k = f"sb_raa_{idx}_{i}"
            pairs.append({"question": (q.get("question") or "").strip(),
                          "answer": (ss.get(k) or "").strip()})
            ss.pop(k, None)
            ss.pop(f"w_{k}", None)
        with st.spinner("Rereading your rule..."):
            rq = llm.reflect_after(ss.sb_agent, _does(), ss.sb_audience,
                                   scenario, draft)
        ss[f"sb_rqa_{idx}"] = rq.get("questions") or []
        ss[f"sb_rqa_src_{idx}"] = draft
        store.log_event(_rid(), "themes", "reflect_after_regen",
                        {"theme": ss.sb_theme, "previous": pairs,
                         "questions": ss[f"sb_rqa_{idx}"]})
    pending = ss.get("_sb_ask")
    if pending and pending[0] == idx:
        del ss["_sb_ask"]
        _ask_version(idx, pending[1], scenario, pending[2])


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
# The theme testing loop: three rounds, per theme, against the rule just written
# ---------------------------------------------------------------------------
# The rounds test one claim: does MY RULE capture what I want? What the model
# follows is that one theme's rule and nothing else, so a disagreement points
# at a gap in the rule rather than at some aggregate the person never wrote.
# There is no second loop at the end: Min cut the all-themes round, so after
# the last theme the session goes straight to export.
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
            data = llm.confirm_pairwise(ss.sb_agent, _does(), "",
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
    _record_pick(cmp, choice, i)
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
    # A round-2 edit lives in the rule box; without re-recording it here the
    # saved answer, the menu, the export and later rounds' generation would all
    # keep the pre-edit text while the person believes they revised it.
    theme = cmp.get("theme", "")
    if theme:
        idx = _theme_index(theme)
        live = _live(f"sb_answer_{idx}").strip()
        stored = (_theme_answer(theme) or {}).get("ideal_behavior", "")
        if live and live != stored:
            ss[f"sb_answer_{idx}"] = live
            _save_version(idx, live)   # the edit becomes a version too
            cases = _theme_cases(theme)
            _record_answer(cases[0] if cases else {"id": -1, "title": theme,
                                                   "situation": "",
                                                   "at_stake": ""},
                           theme=theme, case_ids=[c["id"] for c in cases])
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


def _render_rule_reminder(idx: int, title: str = "Your rule") -> None:
    """The rule under test, always on screen while it is being tested."""
    rule = (st.session_state.get(f"sb_answer_{idx}") or "").strip()
    if not rule:
        return
    st.markdown(f'<div class="np-card-muted" style="margin-bottom:10px;">'
                f'<div class="np-section-title">{title}</div>'
                f'<div class="np-muted">{rule}</div></div>',
                unsafe_allow_html=True)


_LAST_ROUND = 3


def _record_pick(cmp: dict, choice: str, i: int) -> None:
    """Commit a pick and the reason for it.

    The index is passed rather than read at callback time, because the item on
    screen is not guaranteed to be the one the counter points at.

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


def _row_for(cmp_id: str) -> dict | None:
    return next((r for r in st.session_state.sb_confirm
                 if r.get("id") == cmp_id), None)


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
        agent=ss.sb_agent, frame=ss.sb_frame or {},
        audience=ss.sb_audience, intake_reflection=_intake_answers(),
        scenarios=ss.sb_scenarios, answers=ss.sb_answers,
        confirm=ss.sb_confirm, rubric=ss.sb_rubric,
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
    "output": render_output,
}


def render(key: str) -> None:
    _RENDERERS[key]()
