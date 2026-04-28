"""Background / open-question tab — first stop before the structured exercises.

Two interchangeable formats are offered:
  A. Sliders / radios / number inputs (default)
  B. Rank statements from "agree most" to "agree least"

Both formats persist independently; the JSON download includes whichever
side(s) the user has touched plus the format flag.
"""
import json
import streamlit as st

from theme import header, FG, MUTED_FG, BORDER, PRIMARY
from i18n import t

SHIFT_OPTIONS = ["D", "E", "N"]


def _shift_choices() -> list[str]:
    return [t(f"shift.{c}") for c in SHIFT_OPTIONS]


def _section_open(title: str, help_text: str) -> None:
    st.markdown(
        f'<div class="np-card" style="margin-bottom:14px;">'
        f'<div style="font-size:15px;font-weight:600;color:{FG};margin-bottom:4px;">'
        f'{title}</div>'
        f'<div class="np-muted" style="margin-bottom:10px;">{help_text}</div>',
        unsafe_allow_html=True,
    )


def _section_close() -> None:
    st.markdown('</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------
#  Rank widget (used in version B)
# ------------------------------------------------------------------
def _rank_move(state_key: str, idx: int, delta: int) -> None:
    order = st.session_state[state_key]
    new_idx = idx + delta
    if 0 <= new_idx < len(order):
        order[idx], order[new_idx] = order[new_idx], order[idx]


def _rank_widget(state_key: str, items: list[str]) -> list[int]:
    """Render a compact ▲▼ rank list and return the indices in current order."""
    if state_key not in st.session_state or len(st.session_state[state_key]) != len(items):
        st.session_state[state_key] = list(range(len(items)))
    order = st.session_state[state_key]

    for i, idx in enumerate(order):
        c1, c2, c3 = st.columns([0.5, 7.5, 1.4])
        rank_color = PRIMARY if i == 0 else MUTED_FG
        with c1:
            st.markdown(
                f'<div style="font-size:16px;font-weight:700;color:{rank_color};'
                f'padding-top:9px;text-align:right;">{i + 1}</div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div style="padding:9px 0;font-size:14px;color:{FG};'
                f'border-bottom:1px solid {BORDER};">{items[idx]}</div>',
                unsafe_allow_html=True,
            )
        with c3:
            up_col, down_col = st.columns(2, gap="small")
            with up_col:
                st.button("▲", key=f"{state_key}_up_{i}",
                          on_click=_rank_move, args=(state_key, i, -1),
                          disabled=(i == 0), use_container_width=True)
            with down_col:
                st.button("▼", key=f"{state_key}_dn_{i}",
                          on_click=_rank_move, args=(state_key, i, 1),
                          disabled=(i == len(order) - 1), use_container_width=True)
    return list(order)


# ------------------------------------------------------------------
#  Version A — sliders / radios / numbers
# ------------------------------------------------------------------
def _render_version_a() -> dict:
    answers: dict = {}
    shift_labels = _shift_choices()
    label_to_code = dict(zip(shift_labels, SHIFT_OPTIONS))

    # Q1 — weekday vs weekend
    _section_open(t("bg.q1.title"), t("bg.q1.help"))
    q1_labels = [t(f"bg.q1.s{i}") for i in range(1, 6)]
    q1_choice = st.select_slider(
        t("bg.q1.scale"), options=list(range(1, 6)), value=3,
        format_func=lambda v: q1_labels[v - 1], key="bg_q1_scale",
    )
    q1_notes = st.text_area(t("bg.notes_label"), placeholder=t("bg.q1.notes_ph"),
                            key="bg_q1_notes", label_visibility="collapsed", height=70)
    answers["weekday_vs_weekend"] = {
        "scale_1to5": q1_choice,
        "scale_label": q1_labels[q1_choice - 1],
        "notes": q1_notes,
    }
    _section_close()

    # Q2 — shift type ranking
    _section_open(t("bg.q2.title"), t("bg.q2.help"))
    q2_a, q2_b = st.columns(2)
    with q2_a:
        most = st.radio(t("bg.q2.most"), options=shift_labels, index=0,
                        key="bg_q2_most", horizontal=True)
    with q2_b:
        least = st.radio(t("bg.q2.least"), options=shift_labels, index=2,
                         key="bg_q2_least", horizontal=True)
    q2_notes = st.text_area(t("bg.notes_label"), placeholder=t("bg.q2.notes_ph"),
                            key="bg_q2_notes", label_visibility="collapsed", height=70)
    answers["shift_type_preference"] = {
        "most_preferred": label_to_code.get(most, most),
        "least_preferred": label_to_code.get(least, least),
        "notes": q2_notes,
    }
    _section_close()

    # Q3 — night shifts
    _section_open(t("bg.q3.title"), t("bg.q3.help"))
    q3_stance_options = [t(f"bg.q3.stance.a{i}") for i in range(1, 5)]
    q3_stance = st.radio(t("bg.q3.stance"), options=q3_stance_options, index=1,
                         key="bg_q3_stance")
    q3_max = st.number_input(t("bg.q3.max_label"), min_value=0, max_value=31,
                             value=6, step=1, key="bg_q3_max")
    q3_placement_options = [t(f"bg.q3.placement.a{i}") for i in range(1, 5)]
    q3_placement = st.radio(t("bg.q3.placement"), options=q3_placement_options,
                            index=3, key="bg_q3_placement")
    q3_notes = st.text_area(t("bg.notes_label"), placeholder=t("bg.q3.notes_ph"),
                            key="bg_q3_notes", label_visibility="collapsed", height=70)
    answers["night_shifts"] = {
        "stance": q3_stance,
        "stance_index": q3_stance_options.index(q3_stance) + 1,
        "max_per_month": q3_max,
        "placement": q3_placement,
        "placement_index": q3_placement_options.index(q3_placement) + 1,
        "notes": q3_notes,
    }
    _section_close()

    # Q4 — monthly volume
    _section_open(t("bg.q4.title"), t("bg.q4.help"))
    q4_a, q4_b = st.columns(2)
    with q4_a:
        q4_min = st.number_input(t("bg.q4.min"), 0, 31, 12, 1, key="bg_q4_min")
    with q4_b:
        q4_max = st.number_input(t("bg.q4.max"), 0, 31, 16, 1, key="bg_q4_max")
    q4_stance_options = [t(f"bg.q4.stance.a{i}") for i in range(1, 4)]
    q4_stance = st.radio(t("bg.q4.stance"), options=q4_stance_options, index=1,
                         key="bg_q4_stance", horizontal=True)
    answers["monthly_volume"] = {
        "min": q4_min, "max": q4_max,
        "stance": q4_stance,
        "stance_index": q4_stance_options.index(q4_stance) + 1,
    }
    _section_close()

    # Q5 — difficulty
    _section_open(t("bg.q5.title"), t("bg.q5.help"))
    q5_a, q5_b = st.columns(2)
    with q5_a:
        q5_differ_options = [t(f"bg.q5.differ.a{i}") for i in range(1, 4)]
        q5_differ = st.radio(t("bg.q5.differ"), options=q5_differ_options,
                             index=1, key="bg_q5_differ")
    with q5_b:
        q5_hardest_options = [*shift_labels, t("bg.q5.hardest.equal")]
        q5_hardest = st.radio(t("bg.q5.hardest"), options=q5_hardest_options,
                              index=2, key="bg_q5_hardest")
    q5_affects_options = [t(f"bg.q5.affects.a{i}") for i in range(1, 4)]
    q5_affects = st.radio(t("bg.q5.affects"), options=q5_affects_options,
                          index=1, key="bg_q5_affects", horizontal=True)
    q5_notes = st.text_area(t("bg.notes_label"), placeholder=t("bg.q5.notes_ph"),
                            key="bg_q5_notes", label_visibility="collapsed", height=70)
    answers["difficulty"] = {
        "differs": q5_differ,
        "hardest": label_to_code.get(q5_hardest, q5_hardest),
        "affects_preference": q5_affects,
        "notes": q5_notes,
    }
    _section_close()

    # Q6 — circadian
    _section_open(t("bg.q6.title"), t("bg.q6.help"))
    q6_imp_labels = [t(f"bg.q6.imp.a{i}") for i in range(1, 6)]
    q6_imp = st.select_slider(t("bg.q6.importance"), options=list(range(1, 6)),
                              value=3, format_func=lambda v: q6_imp_labels[v - 1],
                              key="bg_q6_imp")
    q6_dir_options = [t(f"bg.q6.direction.a{i}") for i in range(1, 4)]
    q6_dir = st.radio(t("bg.q6.direction"), options=q6_dir_options, index=2,
                      key="bg_q6_dir", horizontal=True)
    q6_notes = st.text_area(t("bg.notes_label"), placeholder=t("bg.q6.notes_ph"),
                            key="bg_q6_notes", label_visibility="collapsed", height=70)
    answers["circadian"] = {
        "importance_1to5": q6_imp,
        "importance_label": q6_imp_labels[q6_imp - 1],
        "preferred_direction": q6_dir,
        "notes": q6_notes,
    }
    _section_close()

    # Q7 — team / social
    _section_open(t("bg.q7.title"), t("bg.q7.help"))
    q7_labels = [t("bg.q7.imp.a1"), t("bg.q6.imp.a2"), t("bg.q6.imp.a3"),
                 t("bg.q6.imp.a4"), t("bg.q7.imp.a5")]
    q7_imp = st.select_slider(t("bg.q7.importance"), options=list(range(1, 6)),
                              value=3, format_func=lambda v: q7_labels[v - 1],
                              key="bg_q7_imp")
    q7_notes = st.text_area(t("bg.notes_label"), placeholder=t("bg.q7.notes_ph"),
                            key="bg_q7_notes", label_visibility="collapsed", height=70)
    answers["team_dynamics"] = {
        "importance_1to5": q7_imp,
        "importance_label": q7_labels[q7_imp - 1],
        "notes": q7_notes,
    }
    _section_close()

    return answers


# ------------------------------------------------------------------
#  Version B — rank statements
# ------------------------------------------------------------------
def _render_version_b() -> dict:
    answers: dict = {}
    shift_labels = _shift_choices()

    st.markdown(
        f'<div class="np-card-muted" style="margin-bottom:14px;">{t("bg.b.howto")}</div>',
        unsafe_allow_html=True,
    )

    def _rank_block(state_key: str, statements: list[str]) -> dict:
        order = _rank_widget(state_key, statements)
        return {"ranked": [{"rank": i + 1, "statement": statements[idx]}
                           for i, idx in enumerate(order)]}

    # Q1
    _section_open(t("bg.q1.title"), t("bg.q1.help"))
    answers["weekday_vs_weekend"] = _rank_block(
        "bg_b_q1", [t(f"bg.b.q1.s{i}") for i in range(1, 6)],
    )
    _section_close()

    # Q2 — rank shift types directly
    _section_open(t("bg.q2.title"), t("bg.b.q2.intro"))
    answers["shift_type_preference"] = _rank_block("bg_b_q2", shift_labels)
    _section_close()

    # Q3
    _section_open(t("bg.q3.title"), t("bg.q3.help"))
    answers["night_shifts"] = _rank_block(
        "bg_b_q3", [t(f"bg.b.q3.s{i}") for i in range(1, 6)],
    )
    answers["night_shifts"]["max_per_month"] = st.number_input(
        t("bg.q3.max_label"), 0, 31,
        st.session_state.get("bg_q3_max", 6), 1, key="bg_b_q3_max",
    )
    _section_close()

    # Q4 — rank stances + keep numeric floor/ceiling
    _section_open(t("bg.q4.title"), t("bg.q4.help"))
    answers["monthly_volume"] = _rank_block(
        "bg_b_q4", [t(f"bg.b.q4.s{i}") for i in range(1, 4)],
    )
    q4_a, q4_b = st.columns(2)
    with q4_a:
        answers["monthly_volume"]["min"] = st.number_input(
            t("bg.q4.min"), 0, 31,
            st.session_state.get("bg_q4_min", 12), 1, key="bg_b_q4_min",
        )
    with q4_b:
        answers["monthly_volume"]["max"] = st.number_input(
            t("bg.q4.max"), 0, 31,
            st.session_state.get("bg_q4_max", 16), 1, key="bg_b_q4_max",
        )
    _section_close()

    # Q5
    _section_open(t("bg.q5.title"), t("bg.q5.help"))
    answers["difficulty"] = _rank_block(
        "bg_b_q5", [t(f"bg.b.q5.s{i}") for i in range(1, 5)],
    )
    _section_close()

    # Q6
    _section_open(t("bg.q6.title"), t("bg.q6.help"))
    answers["circadian"] = _rank_block(
        "bg_b_q6", [t(f"bg.b.q6.s{i}") for i in range(1, 5)],
    )
    _section_close()

    # Q7
    _section_open(t("bg.q7.title"), t("bg.q7.help"))
    answers["team_dynamics"] = _rank_block(
        "bg_b_q7", [t(f"bg.b.q7.s{i}") for i in range(1, 5)],
    )
    _section_close()

    return answers


# ------------------------------------------------------------------
#  Version C — per-question recommended mix
# ------------------------------------------------------------------
Q7_FACTOR_KEYS = ["coworkers", "charge", "culture", "handoff", "breaks", "workload"]


def _render_version_c() -> dict:
    answers: dict = {}
    shift_labels = _shift_choices()
    label_to_code = dict(zip(shift_labels, SHIFT_OPTIONS))

    # Q1 — slider (1D feature)
    _section_open(t("bg.q1.title"), t("bg.q1.help"))
    q1_labels = [t(f"bg.q1.s{i}") for i in range(1, 6)]
    q1_choice = st.select_slider(
        t("bg.q1.scale"), options=list(range(1, 6)), value=3,
        format_func=lambda v: q1_labels[v - 1], key="bg_c_q1_scale",
    )
    q1_notes = st.text_area(t("bg.notes_label"), placeholder=t("bg.q1.notes_ph"),
                            key="bg_c_q1_notes", label_visibility="collapsed", height=70)
    answers["weekday_vs_weekend"] = {
        "scale_1to5": q1_choice,
        "scale_label": q1_labels[q1_choice - 1],
        "notes": q1_notes,
    }
    _section_close()

    # Q2 — rank D/E/N directly
    _section_open(t("bg.q2.title"), t("bg.b.q2.intro"))
    q2_order = _rank_widget("bg_c_q2", shift_labels)
    q2_notes = st.text_area(t("bg.notes_label"), placeholder=t("bg.q2.notes_ph"),
                            key="bg_c_q2_notes", label_visibility="collapsed", height=70)
    answers["shift_type_preference"] = {
        "ranked": [{"rank": i + 1,
                    "shift": SHIFT_OPTIONS[idx],
                    "label": shift_labels[idx]}
                   for i, idx in enumerate(q2_order)],
        "notes": q2_notes,
    }
    _section_close()

    # Q3 — hybrid (stance + max + placement)
    _section_open(t("bg.q3.title"), t("bg.q3.help"))
    q3_stance_options = [t(f"bg.q3.stance.a{i}") for i in range(1, 5)]
    q3_stance = st.radio(t("bg.q3.stance"), options=q3_stance_options, index=1,
                         key="bg_c_q3_stance")
    q3_max = st.number_input(t("bg.q3.max_label"), 0, 31, 6, 1, key="bg_c_q3_max")
    q3_placement_options = [t(f"bg.q3.placement.a{i}") for i in range(1, 5)]
    q3_placement = st.radio(t("bg.q3.placement"), options=q3_placement_options,
                            index=3, key="bg_c_q3_placement")
    q3_notes = st.text_area(t("bg.notes_label"), placeholder=t("bg.q3.notes_ph"),
                            key="bg_c_q3_notes", label_visibility="collapsed", height=70)
    answers["night_shifts"] = {
        "stance": q3_stance,
        "stance_index": q3_stance_options.index(q3_stance) + 1,
        "max_per_month": q3_max,
        "placement": q3_placement,
        "placement_index": q3_placement_options.index(q3_placement) + 1,
        "notes": q3_notes,
    }
    _section_close()

    # Q4 — numbers + 3-stop stance slider (continuous)
    _section_open(t("bg.q4.title"), t("bg.q4.help"))
    q4_a, q4_b = st.columns(2)
    with q4_a:
        q4_min = st.number_input(t("bg.q4.min"), 0, 31, 12, 1, key="bg_c_q4_min")
    with q4_b:
        q4_max = st.number_input(t("bg.q4.max"), 0, 31, 16, 1, key="bg_c_q4_max")
    q4_stance_labels = [t(f"bg.q4.stance.a{i}") for i in range(1, 4)]
    q4_stance_v = st.select_slider(
        t("bg.q4.stance"), options=[1, 2, 3], value=2,
        format_func=lambda v: q4_stance_labels[v - 1], key="bg_c_q4_stance",
    )
    answers["monthly_volume"] = {
        "min": q4_min, "max": q4_max,
        "stance_1to3": q4_stance_v,
        "stance_label": q4_stance_labels[q4_stance_v - 1],
    }
    _section_close()

    # Q5 — differs radio + rank D/E/N by hardness + affects slider
    _section_open(t("bg.q5.title"), t("bg.q5.help"))
    q5_differ_options = [t(f"bg.q5.differ.a{i}") for i in range(1, 4)]
    q5_differ = st.radio(t("bg.q5.differ"), options=q5_differ_options, index=1,
                         key="bg_c_q5_differ")
    st.markdown(
        f'<div class="np-section-title" style="margin-top:6px;">'
        f'{t("bg.c.q5.rank_label")}</div>',
        unsafe_allow_html=True,
    )
    q5_order = _rank_widget("bg_c_q5_rank", shift_labels)
    q5_affects_options = [t(f"bg.q5.affects.a{i}") for i in range(1, 4)]
    q5_affects_v = st.select_slider(
        t("bg.q5.affects"), options=[1, 2, 3], value=2,
        format_func=lambda v: q5_affects_options[v - 1], key="bg_c_q5_affects",
    )
    q5_notes = st.text_area(t("bg.notes_label"), placeholder=t("bg.q5.notes_ph"),
                            key="bg_c_q5_notes", label_visibility="collapsed", height=70)
    answers["difficulty"] = {
        "differs": q5_differ,
        "hardest_to_easiest": [{"rank": i + 1,
                                "shift": SHIFT_OPTIONS[idx],
                                "label": shift_labels[idx]}
                               for i, idx in enumerate(q5_order)],
        "affects_preference_1to3": q5_affects_v,
        "affects_preference_label": q5_affects_options[q5_affects_v - 1],
        "notes": q5_notes,
    }
    _section_close()

    # Q6 — slider + radio (same shape as A)
    _section_open(t("bg.q6.title"), t("bg.q6.help"))
    q6_imp_labels = [t(f"bg.q6.imp.a{i}") for i in range(1, 6)]
    q6_imp = st.select_slider(t("bg.q6.importance"), options=list(range(1, 6)),
                              value=3, format_func=lambda v: q6_imp_labels[v - 1],
                              key="bg_c_q6_imp")
    q6_dir_options = [t(f"bg.q6.direction.a{i}") for i in range(1, 4)]
    q6_dir = st.radio(t("bg.q6.direction"), options=q6_dir_options, index=2,
                      key="bg_c_q6_dir", horizontal=True)
    q6_notes = st.text_area(t("bg.notes_label"), placeholder=t("bg.q6.notes_ph"),
                            key="bg_c_q6_notes", label_visibility="collapsed", height=70)
    answers["circadian"] = {
        "importance_1to5": q6_imp,
        "importance_label": q6_imp_labels[q6_imp - 1],
        "preferred_direction": q6_dir,
        "notes": q6_notes,
    }
    _section_close()

    # Q7 — slider + multi-select factors
    _section_open(t("bg.q7.title"), t("bg.q7.help"))
    q7_imp_labels = [t("bg.q7.imp.a1"), t("bg.q6.imp.a2"), t("bg.q6.imp.a3"),
                     t("bg.q6.imp.a4"), t("bg.q7.imp.a5")]
    q7_imp = st.select_slider(t("bg.q7.importance"), options=list(range(1, 6)),
                              value=3, format_func=lambda v: q7_imp_labels[v - 1],
                              key="bg_c_q7_imp")
    st.markdown(
        f'<div style="font-size:13px;color:{FG};font-weight:500;'
        f'margin-top:10px;margin-bottom:4px;">'
        f'{t("bg.c.q7.factors_label")}</div>',
        unsafe_allow_html=True,
    )
    selected_factor_keys: list[str] = []
    selected_factor_labels: list[str] = []
    fcol_a, fcol_b = st.columns(2)
    for i, fkey in enumerate(Q7_FACTOR_KEYS):
        flabel = t(f"bg.c.q7.factor.{fkey}")
        target = fcol_a if i % 2 == 0 else fcol_b
        with target:
            if st.checkbox(flabel, key=f"bg_c_q7_factor_{fkey}"):
                selected_factor_keys.append(fkey)
                selected_factor_labels.append(flabel)

    q7_notes = st.text_area(t("bg.notes_label"), placeholder=t("bg.q7.notes_ph"),
                            key="bg_c_q7_notes", label_visibility="collapsed", height=70)
    answers["team_dynamics"] = {
        "importance_1to5": q7_imp,
        "importance_label": q7_imp_labels[q7_imp - 1],
        "factor_keys": selected_factor_keys,
        "factor_labels": selected_factor_labels,
        "notes": q7_notes,
    }
    _section_close()

    return answers


# ------------------------------------------------------------------
#  Public render
# ------------------------------------------------------------------
def render() -> None:
    header(t("bg.title"), t("bg.subtitle"))

    # Format toggle (own row, full width).
    st.markdown(
        f'<div class="np-section-title">{t("bg.format.label")}</div>',
        unsafe_allow_html=True,
    )
    fmt_labels = {"A": t("bg.format.a"), "B": t("bg.format.b"), "C": t("bg.format.c")}
    fmt = st.radio(
        t("bg.format.label"),
        options=["A", "B", "C"],
        index=2,  # default to recommended
        format_func=lambda x: fmt_labels[x],
        horizontal=True, key="bg_format", label_visibility="collapsed",
    )
    st.markdown(
        f'<div class="np-muted" style="margin-bottom:14px;">{t("bg.format.help")}</div>',
        unsafe_allow_html=True,
    )

    renderers = {
        "A": _render_version_a,
        "B": _render_version_b,
        "C": _render_version_c,
    }
    active = renderers[fmt]()
    st.session_state[f"bg_{fmt.lower()}_snapshot"] = active

    payload = {
        "format_used_last": fmt,
        "version_A": st.session_state.get("bg_a_snapshot") or {},
        "version_B": st.session_state.get("bg_b_snapshot") or {},
        "version_C": st.session_state.get("bg_c_snapshot") or {},
    }

    st.divider()
    st.download_button(
        t("bg.download"),
        data=json.dumps(payload, indent=2, ensure_ascii=False),
        file_name="background_answers.json",
        mime="application/json",
    )
