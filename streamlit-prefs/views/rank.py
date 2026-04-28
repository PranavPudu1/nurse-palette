"""Feature ranking view."""
import json
import streamlit as st

from theme import header, FG, MUTED_FG, BORDER, PRIMARY

DEFAULT_FEATURES = [
    ("no_consec_nights", "No more than 2 nights in a row"),
    ("weekends_off",     "At least every other weekend off"),
    ("long_blocks",      "Long blocks of work + long blocks off (4-on / 4-off)"),
    ("no_quick_turn",    "No 'quick turnarounds' (night → day next morning)"),
    ("predictable",      "Predictable, repeating pattern week to week"),
    ("self_pick_off",    "I can pick my off days each month"),
    ("balanced_shifts",  "Even mix of day / evening / night"),
    ("partner_aligned",  "Aligned with a coworker's schedule"),
]
LABELS = dict(DEFAULT_FEATURES)


def _move(idx: int, delta: int) -> None:
    order = st.session_state.rank_order
    new_idx = idx + delta
    if 0 <= new_idx < len(order):
        order[idx], order[new_idx] = order[new_idx], order[idx]


def _drop(key: str) -> None:
    st.session_state.rank_order.remove(key)
    st.session_state.rank_locked_out.append(key)


def _restore(key: str) -> None:
    st.session_state.rank_locked_out.remove(key)
    st.session_state.rank_order.append(key)


def render() -> None:
    if "rank_order" not in st.session_state:
        st.session_state.rank_order = [f[0] for f in DEFAULT_FEATURES]
    if "rank_locked_out" not in st.session_state:
        st.session_state.rank_locked_out = []

    header(
        "Rank what matters most",
        "Use ▲ / ▼ to reorder. #1 = the rule that affects your quality of life "
        "the most. Move anything you genuinely don't care about to the bottom panel.",
    )

    st.markdown(
        '<div class="np-section-title">Ranked (most → least important)</div>',
        unsafe_allow_html=True,
    )

    for i, key in enumerate(st.session_state.rank_order):
        badge_color = PRIMARY if i < 3 else "#8B96A6"
        c1, c2, c3, c4 = st.columns([0.7, 7, 1.0, 1.6])
        with c1:
            st.markdown(
                f'<div class="np-rank-badge" style="background:{badge_color};'
                f'margin-top:6px;">{i + 1}</div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div class="np-rank-row">{LABELS[key]}</div>',
                unsafe_allow_html=True,
            )
        with c3:
            up_col, down_col = st.columns(2, gap="small")
            with up_col:
                st.button("▲", key=f"up_{key}", on_click=_move, args=(i, -1),
                          disabled=(i == 0), use_container_width=True)
            with down_col:
                st.button("▼", key=f"dn_{key}", on_click=_move, args=(i, 1),
                          disabled=(i == len(st.session_state.rank_order) - 1),
                          use_container_width=True)
        with c4:
            st.button("Not important", key=f"drop_{key}",
                      on_click=_drop, args=(key,),
                      use_container_width=True)

    st.write("")

    with st.expander(
        f"Doesn't matter to me  ({len(st.session_state.rank_locked_out)})",
        expanded=bool(st.session_state.rank_locked_out),
    ):
        if not st.session_state.rank_locked_out:
            st.markdown(
                '<div class="np-muted">Move items here if you don\'t care about them.</div>',
                unsafe_allow_html=True,
            )
        for key in st.session_state.rank_locked_out:
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(
                    f'<div class="np-rank-row-disabled">{LABELS[key]}</div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.button("Restore", key=f"restore_{key}",
                          on_click=_restore, args=(key,),
                          use_container_width=True)

    st.divider()

    with st.expander("Anything else? (free text)"):
        st.text_area(
            "Other things that matter to you in a schedule",
            key="rank_freeform", label_visibility="collapsed",
            placeholder="e.g. I prefer to keep Wednesdays free for school pickup.",
        )

    payload = {
        "ranked": [{"rank": i + 1, "key": k, "label": LABELS[k]}
                   for i, k in enumerate(st.session_state.rank_order)],
        "not_important": [{"key": k, "label": LABELS[k]}
                          for k in st.session_state.rank_locked_out],
        "freeform": st.session_state.get("rank_freeform", ""),
    }

    st.download_button(
        "Download my ranking (JSON)",
        data=json.dumps(payload, indent=2),
        file_name="feature_ranking.json",
        mime="application/json",
    )
