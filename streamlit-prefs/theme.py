"""Shared theme + styling helpers to match the React app's palette."""
import streamlit as st

# HSL values lifted from src/index.css so the look stays consistent.
SHIFT_COLORS = {
    "D": {"bg": "hsl(45, 93%, 60%)",  "fg": "hsl(40, 50%, 20%)",  "label": "Day"},
    "E": {"bg": "hsl(25, 90%, 55%)",  "fg": "hsl(0, 0%, 100%)",   "label": "Evening"},
    "N": {"bg": "hsl(270, 50%, 55%)", "fg": "hsl(0, 0%, 100%)",   "label": "Night"},
    "X": {"bg": "hsl(210, 15%, 92%)", "fg": "hsl(215, 10%, 40%)", "label": "Off"},
}

PRIMARY = "#2870BE"
PRIMARY_HOVER = "#1F5B9B"
BORDER = "#D6DEE7"
GRID_HEADER = "#F1F4F8"
MUTED_FG = "#5A6573"
FG = "#101827"
ACCENT = "#DAE3EC"
WARNING = "#E89A2D"
CARD_BG = "#FFFFFF"
SURFACE_BG = "#FAFBFC"

# Note: scoped to .np-* classes only — no broad selectors that bleed into widgets.
GLOBAL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

html, body {{
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
}}

.block-container {{
    padding-top: 1.4rem;
    padding-bottom: 3rem;
    max-width: 1240px;
}}

/* === Custom np-* surfaces === */
.np-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 18px 22px;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    color: {FG};
}}

.np-card-muted {{
    background: {SURFACE_BG};
    border: 1px dashed {BORDER};
    border-radius: 12px;
    padding: 14px 18px;
    color: {MUTED_FG};
}}

.np-section-title {{
    font-size: 11px;
    font-weight: 600;
    color: {MUTED_FG};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}}

.np-h1 {{
    font-size: 24px;
    font-weight: 600;
    color: {FG};
    letter-spacing: -0.01em;
    margin-bottom: 4px;
}}

.np-sub {{
    color: {MUTED_FG};
    font-size: 14px;
    line-height: 1.5;
}}

.np-muted {{
    color: {MUTED_FG};
    font-size: 13px;
}}

.np-strong {{
    color: {FG};
    font-weight: 600;
}}

.np-pill {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    background: {ACCENT};
    color: {FG};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
}}

.np-rank-badge {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    color: white;
    font-weight: 700;
    font-size: 13px;
}}

.np-rank-row {{
    padding: 9px 12px;
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
    font-size: 14px;
    color: {FG};
}}

.np-rank-row-disabled {{
    padding: 9px 12px;
    background: {SURFACE_BG};
    border: 1px dashed {BORDER};
    border-radius: 8px;
    font-size: 13px;
    color: {MUTED_FG};
}}

/* === Streamlit primary buttons (white text inside) === */
.stButton > button,
.stDownloadButton > button {{
    background: {PRIMARY};
    color: white !important;
    border: 1px solid {PRIMARY};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    transition: filter 0.12s, background 0.12s;
}}
.stButton > button *,
.stDownloadButton > button * {{
    color: white !important;
}}
.stButton > button:hover,
.stDownloadButton > button:hover {{
    background: {PRIMARY_HOVER};
    border-color: {PRIMARY_HOVER};
    color: white !important;
}}
.stButton > button:disabled,
.stDownloadButton > button:disabled {{
    background: {ACCENT};
    color: {MUTED_FG} !important;
    border-color: {BORDER};
}}
.stButton > button:disabled * {{
    color: {MUTED_FG} !important;
}}

/* === Streamlit tabs === */
.stTabs [data-baseweb="tab-list"] {{
    gap: 2px;
    border-bottom: 1px solid {BORDER};
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent;
    border-radius: 8px 8px 0 0;
    padding: 10px 18px;
    font-weight: 500;
    color: {MUTED_FG};
}}
.stTabs [aria-selected="true"] {{
    color: {PRIMARY} !important;
    background: {CARD_BG};
    border-bottom: 2px solid {PRIMARY};
    font-weight: 600;
}}

/* === Sidebar polish === */
section[data-testid="stSidebar"] {{
    background: {SURFACE_BG};
    border-right: 1px solid {BORDER};
}}

/* === Hide default Streamlit chrome === */
header[data-testid="stHeader"] {{ background: transparent; }}
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
</style>
"""


def setup_page(title: str, icon: str = "🩺") -> None:
    st.set_page_config(page_title=f"{title} · Nurse Preferences",
                       page_icon=icon, layout="wide")
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def shift_chip(letter: str, size: int = 32) -> str:
    """Single shift cell, mirrors ShiftCell.tsx."""
    s = SHIFT_COLORS.get(letter, SHIFT_COLORS["X"])
    return (
        f'<div style="display:inline-flex;align-items:center;justify-content:center;'
        f'width:{size}px;height:{size}px;margin:1px;border-radius:6px;'
        f'background:{s["bg"]};color:{s["fg"]};font-weight:600;font-size:12px;'
        f'border:1px solid rgba(0,0,0,0.04);">{letter if letter != "X" else ""}</div>'
    )


def legend_html() -> str:
    items = []
    for code, meta in SHIFT_COLORS.items():
        items.append(
            f'<div style="display:flex;align-items:center;gap:6px;color:{MUTED_FG};">'
            f'{shift_chip(code, 22)}'
            f'<span style="font-size:12px;color:{MUTED_FG};">{meta["label"]}</span>'
            f'</div>'
        )
    return (
        '<div style="display:flex;gap:18px;flex-wrap:wrap;align-items:center;'
        'margin:6px 0 4px;">'
        + "".join(items) + '</div>'
    )


def header(title: str, subtitle: str = "") -> None:
    sub = f'<div class="np-sub" style="margin-top:4px;">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div style="margin-bottom:18px;">'
        f'<div class="np-h1">{title}</div>{sub}</div>',
        unsafe_allow_html=True,
    )
