"""Feature ranking view — compact, minimalistic."""
import json
import streamlit as st

from theme import header, FG, MUTED_FG, BORDER, PRIMARY, CARD_BG
from i18n import t

FEATURE_KEYS = [
    "no_consec_nights",
    "weekends_off",
    "long_blocks",
    "no_quick_turn",
    "predictable",
    "self_pick_off",
    "balanced_shifts",
    "partner_aligned",
]


def _label(key: str) -> str:
    return t(f"rank.feat.{key}")


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
        st.session_state.rank_order = list(FEATURE_KEYS)
    if "rank_locked_out" not in st.session_state:
        st.session_state.rank_locked_out = []

    header(t("rank.title"), t("rank.subtitle"))

    st.markdown(
        f'<div class="np-section-title">{t("rank.ranked")}</div>',
        unsafe_allow_html=True,
    )

    # Compact list — one row per item, 4 thin columns.
    for i, key in enumerate(st.session_state.rank_order):
        rank_color = PRIMARY if i < 3 else MUTED_FG
        c1, c2, c3, c4 = st.columns([0.5, 6.5, 1.4, 0.6])

        with c1:
            st.markdown(
                f'<div style="font-size:18px;font-weight:700;color:{rank_color};'
                f'padding-top:10px;text-align:right;">{i + 1}</div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div style="padding:11px 0;font-size:14px;color:{FG};'
                f'border-bottom:1px solid {BORDER};">{_label(key)}</div>',
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
            st.button("✕", key=f"drop_{key}", on_click=_drop, args=(key,),
                      help=t("rank.drop"), use_container_width=True)

    st.write("")

    n_dropped = len(st.session_state.rank_locked_out)
    with st.expander(t("rank.dropped", n=n_dropped),
                     expanded=bool(n_dropped)):
        if not st.session_state.rank_locked_out:
            st.markdown(
                f'<div class="np-muted">{t("rank.empty_drop")}</div>',
                unsafe_allow_html=True,
            )
        for key in st.session_state.rank_locked_out:
            c1, c2 = st.columns([6, 1])
            with c1:
                st.markdown(
                    f'<div style="padding:8px 0;font-size:13px;color:{MUTED_FG};">'
                    f'{_label(key)}</div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.button(t("rank.restore"), key=f"restore_{key}",
                          on_click=_restore, args=(key,),
                          use_container_width=True)

    st.divider()

    with st.expander(t("rank.freeform_label")):
        st.text_area(
            t("rank.freeform_label"),
            key="rank_freeform", label_visibility="collapsed",
            placeholder=t("rank.freeform_ph"),
        )

    payload = {
        "ranked": [{"rank": i + 1, "key": k, "label": _label(k)}
                   for i, k in enumerate(st.session_state.rank_order)],
        "not_important": [{"key": k, "label": _label(k)}
                          for k in st.session_state.rank_locked_out],
        "freeform": st.session_state.get("rank_freeform", ""),
    }

    st.download_button(
        t("rank.download"),
        data=json.dumps(payload, indent=2, ensure_ascii=False),
        file_name="feature_ranking.json",
        mime="application/json",
    )
