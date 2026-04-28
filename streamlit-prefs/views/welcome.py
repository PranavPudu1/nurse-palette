"""Welcome / overview tab."""
import streamlit as st

from theme import header, FG, MUTED_FG, BORDER


def render() -> None:
    header(
        "Welcome",
        "Five short exercises to capture what matters most when we build your "
        "schedule. Use the tabs above to walk through them in any order.",
    )

    cards = [
        ("Compare schedules",
         "Two months side by side — pick the one you'd rather work.",
         "≈ 3 min"),
        ("Rank what matters",
         "Order the rules by how much they affect your quality of life.",
         "≈ 2 min"),
        ("Build your ideal month",
         "Fill a blank calendar with shifts — show us your dream month.",
         "≈ 5 min"),
        ("Trade-offs",
         "Sliders for the hard questions: how many nights for a free weekend?",
         "≈ 2 min"),
        ("Day-by-day preference",
         "Rate every shift / weekday combo on a quick heatmap.",
         "≈ 3 min"),
    ]

    cols = st.columns(3, gap="medium")
    for i, (title, body, length) in enumerate(cards):
        with cols[i % 3]:
            st.markdown(
                f'<div class="np-card" style="height:100%;margin-bottom:14px;">'
                f'<div class="np-section-title">{length}</div>'
                f'<div style="font-size:16px;font-weight:600;color:{FG};margin-bottom:6px;">'
                f'{title}</div>'
                f'<div class="np-muted">{body}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        f'<div class="np-muted" style="border-top:1px solid {BORDER};padding-top:16px;'
        f'margin-top:18px;">Your responses are stored locally in this session only — '
        f'each tab has a download button to export your answers as JSON.</div>',
        unsafe_allow_html=True,
    )
