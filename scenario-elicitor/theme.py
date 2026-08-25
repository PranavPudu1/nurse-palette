"""Shared theme + styling helpers. Warm editorial palette, Fraunces + Inter.

Copied from the preference-elicitor app, trimmed to the domain-neutral pieces.
Warm cream surfaces, terracotta primary, gold accent, Fraunces serif headings.
"""
import streamlit as st

# === Palette (warm editorial) ===
PRIMARY = "#D9553A"
PRIMARY_HOVER = "#BF472F"
PRIMARY_SOFT = "#FBEAE2"
SECONDARY = "#8A5A44"
BORDER = "#EAE0D1"
GRID_HEADER = "#F1E7D6"
MUTED_FG = "#746858"         # warm gray, darkened to clear WCAG AA on cream
FG = "#241C15"
ACCENT = "#E9C46A"
WARNING = "#C4762E"
CARD_BG = "#FFFFFF"
SURFACE_BG = "#F5EEE1"
PAGE_BG = "#FAF5EC"

GLOBAL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap');

html, body {{ font-family: 'Inter', system-ui, sans-serif; }}

.stApp {{
    background: radial-gradient(1100px 640px at 84% -14%, #F6E7CE 0%, {PAGE_BG} 58%);
}}

.stMarkdown, .stText, .stTextInput input, .stTextArea textarea,
.stSelectbox, .stRadio, .stSlider, .stDownloadButton, .stButton {{
    font-family: 'Inter', system-ui, sans-serif;
}}

.block-container {{ padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1120px; }}

.np-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 18px;
    padding: 18px 22px;
    box-shadow: 0 1px 2px rgba(60, 42, 20, 0.05),
                0 18px 38px -22px rgba(60, 42, 20, 0.30);
    color: {FG};
}}

.np-card-muted {{
    background: {SURFACE_BG};
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 14px 18px;
    color: {MUTED_FG};
}}

.np-section-title {{
    font-size: 11px; font-weight: 700; color: {PRIMARY};
    text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 8px;
}}

.np-h1 {{
    font-family: 'Fraunces', Georgia, serif;
    font-size: 30px; font-weight: 600; color: {FG};
    letter-spacing: -0.01em; line-height: 1.15; margin-bottom: 4px;
}}

.np-app-title {{
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 600; letter-spacing: -0.01em;
}}

.np-sub {{ color: {MUTED_FG}; font-size: 14.5px; line-height: 1.6; }}
.np-muted {{ color: {MUTED_FG}; font-size: 13px; }}
.np-strong {{ color: {FG}; font-weight: 600; }}

.np-pill {{
    display: inline-block; padding: 3px 11px; border-radius: 999px;
    background: {PRIMARY_SOFT}; color: {PRIMARY_HOVER};
    font-size: 11px; font-weight: 700; letter-spacing: 0.03em;
    border: 1px solid #F1D3C6;
}}

.np-bar-track {{
    background: {SURFACE_BG}; border: 1px solid {BORDER};
    border-radius: 999px; height: 12px; overflow: hidden;
}}
.np-bar-fill {{ background: {PRIMARY}; height: 100%; border-radius: 999px; }}

/* Streamlit buttons: primary = terracotta, secondary = warm ghost */
.stButton > button, .stDownloadButton > button {{
    background: {PRIMARY}; color: #ffffff !important; border: 1px solid {PRIMARY};
    border-radius: 11px; padding: 9px 18px; font-weight: 600;
    box-shadow: 0 8px 18px -12px rgba(217, 85, 58, 0.65);
    transition: background 0.12s, box-shadow 0.12s, transform 0.06s, border-color 0.12s;
}}
.stButton > button *, .stDownloadButton > button * {{ color: #ffffff !important; }}
.stButton > button:hover, .stDownloadButton > button:hover {{
    background: {PRIMARY_HOVER}; border-color: {PRIMARY_HOVER};
    transform: translateY(-1px);
    box-shadow: 0 12px 24px -12px rgba(217, 85, 58, 0.72);
}}

/* Secondary / ghost buttons (st.button(type="secondary")) */
.stButton > button[data-testid="stBaseButton-secondary"] {{
    background: {CARD_BG}; color: {FG} !important; border: 1px solid {BORDER};
    box-shadow: none;
}}
.stButton > button[data-testid="stBaseButton-secondary"] * {{ color: {FG} !important; }}
.stButton > button[data-testid="stBaseButton-secondary"]:hover {{
    background: {SURFACE_BG}; border-color: {PRIMARY};
    color: {PRIMARY_HOVER} !important; transform: none; box-shadow: none;
}}
.stButton > button[data-testid="stBaseButton-secondary"]:hover * {{
    color: {PRIMARY_HOVER} !important;
}}

/* Disabled (covers primary and secondary) */
.stButton > button:disabled, .stDownloadButton > button:disabled,
.stButton > button[data-testid="stBaseButton-secondary"]:disabled {{
    background: {SURFACE_BG}; color: {MUTED_FG} !important; border-color: {BORDER};
    box-shadow: none; transform: none;
}}
.stButton > button:disabled * {{ color: {MUTED_FG} !important; }}

.stTextInput input, .stTextArea textarea {{ border-radius: 11px !important; }}
.stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: {PRIMARY} !important; box-shadow: 0 0 0 3px {PRIMARY_SOFT} !important;
}}

.stTabs [data-baseweb="tab"] {{ color: {MUTED_FG}; font-weight: 500; }}
.stTabs [aria-selected="true"] {{ color: {PRIMARY} !important; }}

[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {{
    color: {MUTED_FG} !important;
}}

details, .stExpander {{ border-radius: 12px !important; }}

/* Info icon: "how was this made" on anything the model produced.
   Opens on hover (desktop), :active (touch press) and :focus / :focus-within
   (tab, and most touch browsers focus on tap). No JS, since Streamlit renders
   this through its markdown pipeline where scripts do not run. */
.np-info {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 15px; height: 15px; margin-left: 6px; vertical-align: middle;
    border-radius: 999px; border: 1px solid {BORDER};
    background: {SURFACE_BG}; color: {MUTED_FG};
    font-family: 'Fraunces', Georgia, serif; font-size: 10px; font-weight: 700;
    font-style: italic; line-height: 1; cursor: help; position: relative;
    user-select: none; outline: none;
}}
.np-info:hover, .np-info:focus {{ border-color: {PRIMARY}; color: {PRIMARY_HOVER}; }}

.np-tip {{
    visibility: hidden; opacity: 0;
    position: absolute; z-index: 9999;
    left: 50%; transform: translateX(-50%); top: calc(100% + 8px);
    width: 300px; max-width: min(300px, 86vw);
    background: {CARD_BG}; color: {FG};
    border: 1px solid {BORDER}; border-radius: 14px; padding: 12px 14px;
    box-shadow: 0 2px 4px rgba(60, 42, 20, 0.06),
                0 22px 44px -20px rgba(60, 42, 20, 0.42);
    font-family: 'Inter', system-ui, sans-serif; font-style: normal;
    font-size: 12.5px; font-weight: 400; line-height: 1.5;
    text-align: left; white-space: normal; cursor: auto;
    transition: opacity 0.12s ease;
}}
/* Columns clip absolutely positioned children, so a tooltip opened inside a
   narrow column was being cut off at the column edge. The layout is three
   columns now, which made it unreadable rather than just tight. Let the tooltip
   escape its column, and centre it under the icon so it spills evenly both ways
   instead of always running off the same side.

   stVerticalBlock is deliberately NOT in this list: st.container(height=...)
   relies on its overflow to scroll, and forcing it visible would break every
   fixed-height pane on the page. */
[data-testid="stHorizontalBlock"],
[data-testid="column"],
[data-testid="stColumn"] {{ overflow: visible !important; }}

.np-info:hover .np-tip,
.np-info:active .np-tip,
.np-info:focus .np-tip,
.np-info:focus-within .np-tip {{ visibility: visible; opacity: 1; }}

.np-tip b {{
    display: block; margin-bottom: 2px; color: {PRIMARY};
    font-size: 9.5px; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase;
}}
.np-tip b ~ b {{ margin-top: 9px; }}
.np-tip i {{ font-style: normal; color: {MUTED_FG}; }}

header[data-testid="stHeader"] {{ background: transparent; }}
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
</style>
"""


def setup_page(title: str, icon: str = "🎛️") -> None:
    st.set_page_config(page_title=f"{title} · Scenario Elicitor",
                       page_icon=icon, layout="wide")
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def header(title: str, subtitle: str = "") -> None:
    sub = (f'<div class="np-sub" style="margin-top:4px;">{subtitle}</div>'
           if subtitle else "")
    st.markdown(f'<div style="margin-bottom:18px;">'
                f'<div class="np-h1">{title}</div>{sub}</div>',
                unsafe_allow_html=True)


def section(label: str) -> None:
    st.markdown(f'<div class="np-section-title">{label}</div>',
                unsafe_allow_html=True)
