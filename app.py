import streamlit as st
import base64
from pathlib import Path
from db import get_client

st.set_page_config(
    page_title="FIFA WC 2026 Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Load bg image as base64 ───────────────────────────────────────────────────
def get_base64_font(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

champgothic = get_base64_font("static/fonts/ChampionGothic-Heavyweight.woff2")
tusker_4700 = get_base64_font("static/fonts/TuskerGrotesk-4700Bold.woff2")
tusker_6500 = get_base64_font("static/fonts/TuskerGrotesk-6500Medium.woff2")
tusker_7700 = get_base64_font("static/fonts/TuskerGrotesk-7700Bold.woff2")
zuume_black = get_base64_font("static/fonts/zuume-black.woff2")

font_face_css = (
    "@font-face {"
    "font-family: 'ChampionGothic';"
    "src: url('data:font/woff2;base64," + champgothic + "') format('woff2');"
    "font-weight: 900;"
    "font-style: normal;"
    "}"
) if champgothic else ""


def get_base64_image(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

bg_b64 = get_base64_image("static/bg.png")
logo_b64 = get_base64_image("static/logo.png")
bg_css = f"url('data:image/png;base64,{bg_b64}')" if bg_b64 else "none"

# ── Global CSS ────────────────────────────────────────────────────────────────
# Inject font separately before main CSS
if champgothic:
    st.markdown(
        "<style>@font-face{font-family:'ChampionGothic';"
        "src:url('data:font/woff2;base64," + champgothic + "') format('woff2');"
        "font-weight:900;font-style:normal;}</style>",
        unsafe_allow_html=True
    )

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');



:root {{
    --green:  #D4AF37;
    --dark:   #0A0A0A;
    --card:   #141414;
    --border: #222222;
    --muted:  #d6d6d6;
    --text:   #F0F0F0;
    --nav-h:  60px;
}}

/* ── Reset & background ── */
html, body {{
    margin: 0; padding: 0;
    background-color: var(--dark) !important;
    font-family: 'DM Sans', sans-serif;
}}

[data-testid="stAppViewContainer"] {{
    background-image: {bg_css};
    background-size: cover;
    background-position: center top;
    background-attachment: fixed;
    background-repeat: no-repeat;
    background-color: var(--dark) !important;
}}

/* dark overlay over bg */
[data-testid="stAppViewContainer"]::before {{
    content: '';
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.35 );
    z-index: 0;
    pointer-events: none;
}}

[data-testid="stAppViewContainer"] > * {{
    position: relative;
    z-index: 1;
}}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header,
[data-testid="stDecoration"] {{
    display: none !important;
    visibility: hidden !important;
}}

@media (max-width: 767px) {{
    [data-testid="stSidebar"] {{
        display: block !important;
        visibility: visible !important;
        background: rgba(10,10,10,0.95) !important;
    }}
    [data-testid="collapsedControl"] {{
        display: block !important;
        visibility: visible !important;
    }}
    .wc-navbar {{
        padding: 0 1rem;
    }}
    .wc-nav-links {{
        display: none !important;
    }}
}}

/* ── Push content below navbar ── */
[data-testid="stMainBlockContainer"],
.main .block-container {{
    padding-top: calc(var(--nav-h) + 2rem) !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 85vw;
    margin: 0 auto;
}}

/* ── Nav root wrapper (handles fixed positioning now) ── */
.wc-nav-root {{
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 9999;
}}
.mob-check-input {{
    display: none !important;
}}

/* ── Sticky navbar ── */
.wc-navbar {{
    height: var(--nav-h);
    backdrop-filter: blur(20px) saturate(1.6);
    -webkit-backdrop-filter: blur(20px) saturate(1.6);
    background: rgba(10,10,10,0.65);
    border-bottom: 1px solid rgba(0,0,0,0.50);
    display: flex;
    align-items: center;
    padding: 0 2rem;
    gap: 2rem;
}}

.wc-logo {{
    display: flex;
    align-items: center;
    height: 60px;
    overflow: hidden;
}}

.wc-logo img {{
    height: 42px !important;
    width: auto !important;
    max-width: none !important;
    display: block;
}}

.wc-nav-links {{
    display: flex;
    align-items: center;
    gap: 0.25rem;
    flex: 1;
}}

.wc-nav-link, .wc-nav-link:visited, .wc-nav-link:hover {{
    text-decoration: none !important;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    color: #ccc;
    padding: 0.35rem 0.85rem;
}}
.wc-nav-link:hover {{
    color: #fff;
    background: rgba(255,255,255,0.05);
}}

.wc-nav-link.active {{

    color: var(--green);
    background: rgba(0,200,83,0.08);
    border-color: rgba(0,200,83,0.2);
    font-weight: 600;
}}

/* ── Hamburger button ── */
.mob-toggle {{
    display: none;
    font-size: 1.4rem;
    color: #aaa;
    cursor: pointer;
    margin-left: auto;
    padding: 0 0.5rem;
    user-select: none;
    line-height: 1;
}}
.mob-toggle .close-icon {{ display: none; }}
.mob-toggle .ham-icon   {{ display: inline; }}
.mob-check-input:checked ~ .wc-navbar .mob-toggle .ham-icon   {{ display: none; }}
.mob-check-input:checked ~ .wc-navbar .mob-toggle .close-icon {{ display: inline; }}

/* ── Mobile dropdown ── */
.mobile-nav {{
    display: none;
    flex-direction: column;
    background: rgba(10,10,10,0.97);
    backdrop-filter: blur(14px);
    border-bottom: 1px solid #1e1e1e;
    padding: 0.5rem 0;
}}
.mob-check-input:checked ~ .mobile-nav {{
    display: flex !important;
}}
.mobile-nav .wc-nav-link {{
    padding: 0.75rem 1.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    font-size: 0.95rem;
}}
.mobile-nav .wc-nav-link:last-child {{ border-bottom: none; }}

/* ── Breakpoints ── */
@media (max-width: 767px) {{
    .mob-toggle {{ display: block !important; }}
    .wc-nav-links {{ display: none !important; }}
    .wc-navbar {{ padding: 0 1rem; }}
}}
@media (min-width: 768px) {{
    .mobile-nav {{ display: none !important; }}
}}

/* ── Buttons ── */
.stButton > button {{
    background: #FFD700 !important;
    color: #000 !important;
    border: none !important;
    border-radius: 4px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em;
}}
.stButton > button:hover {{ opacity: 0.85 !important; }}

/* ── Inputs ── */
.stTextInput input, .stNumberInput input, .stSelectbox select {{
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 4px !important;
}}

/* ── Metric cards ── */
[data-testid="metric-container"] {{
    background: rgba(20,20,20,0.8);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem;
    backdrop-filter: blur(8px);
}}

/* ── Global text ── */
*, p, div, span, label {{
    color: var(--text);
}}

hr {{ border-color: var(--border) !important; }}
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: #333; border-radius: 3px; }}
</style>
""", unsafe_allow_html=True)

# ── Scheduler ─────────────────────────────────────────────────────────────────
if "scheduler_started" not in st.session_state:
    try:
        from scheduler import start as start_scheduler
        start_scheduler()
        st.session_state["scheduler_started"] = True
    except Exception:
        st.session_state["scheduler_started"] = False

# ── Pages ─────────────────────────────────────────────────────────────────────
NAV_ITEMS = [
    ("Home",        "pages/0_home.py"),
    ("Predictions", "pages/1_predictions.py"),
    ("Fixtures",    "pages/2_fixtures.py"),
    ("Results",     "pages/3_results.py"),
    ("Standings",   "pages/4_standings.py"),
    ("Knockouts",   "pages/5_ko.py"),
    ("Admin",       "pages/6_admin.py"),
]

HIDDEN_PAGES = {
    "MatchDetail": "pages/0_match_detail.py",
}

if "page" not in st.session_state:
    st.session_state["page"] = "Home"

current = st.session_state["page"]


# ── Render navbar ─────────────────────────────────────────────────────────────
links_html = ""
for label, _ in NAV_ITEMS:
    if label in HIDDEN_PAGES:
        continue
    active_cls = "active" if current == label else ""
    links_html += f'<a class="wc-nav-link {active_cls}" href="?page={label}" target="_self">{label}</a>\n'

navbar_html = (
    '<div class="wc-nav-root">'
    '<input type="checkbox" id="mob-check" class="mob-check-input">'
    '<div class="wc-navbar">'
    '<div class="wc-logo"><img src="data:image/png;base64,' + logo_b64 + ' alt="logo"></div>'
    '<div class="wc-nav-links">' + links_html + '</div>'
    '<label class="mob-toggle" for="mob-check">'
    '<span class="ham-icon">&#9776;</span>'
    '<span class="close-icon">&#10005;</span>'
    '</label>'
    '</div>'
    '<div class="mobile-nav">' + links_html + '</div>'
    '</div>'
)


st.markdown(navbar_html, unsafe_allow_html=True)


# ── Handle query param routing ────────────────────────────────────────────────
params = st.query_params
if "page" in params:
    requested = params["page"]
    valid_pages = [label for label, _ in NAV_ITEMS] + ["MatchDetail"]
    if requested in valid_pages and requested != st.session_state["page"]:
        if "match_id" in params:
            st.session_state["detail_match_id"] = int(params["match_id"])
        st.session_state["page"] = requested
        st.query_params.clear()
        st.rerun()

with st.sidebar:
    st.write("test")

# ── Load current page ─────────────────────────────────────────────────────────
all_pages = dict(NAV_ITEMS) | HIDDEN_PAGES
page_file = all_pages.get(current, "pages/0_home.py")

with open(page_file, "r", encoding="utf-8") as f:
    exec(compile(f.read(), page_file, "exec"), {"__name__": "__main__"})

