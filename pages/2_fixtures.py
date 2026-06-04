import streamlit as st
from datetime import date, datetime
from collections import defaultdict
from db import get_client, fixtures_upcoming, get_team_rank, get_team_form, team_by_id
from utils import format_kickoff, flag_img
import json, base64, re

supabase = get_client()

# Load H2H data once
try:
    with open("static/h2h.json") as f:
        H2H = json.load(f)
except Exception:
    H2H = {}

st.markdown("""
<style>

.page-title {
    font-family:'ChampionGothic',sans-serif; font-weight:900;
    font-size: 5rem;
    letter-spacing: 0.1em;
    color: #F0F0F0;
    margin-bottom: 0.15rem;
}
.date-header {
    font-family: 'Inter', sans-serif;
    font-size: 1.1rem; text-transform: none;
    font-weight: 800;
    letter-spacing: 0.08em;
    color: #aaa;
    margin: 1.5rem 0 0.75rem 0;
}

.fix-card {
    background: rgba(10,10,10,0.50);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 10px;
    border: 1px solid #242424;
    padding: 1.1rem 1.4rem;
    margin-bottom: 0;
}
.fix-card-wrap {
    margin-bottom: 0.75rem;
}
/* Arrow button */
div[data-testid="stButton"] button {
    background: rgba(10,10,10,0.65) !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 6px !important;
    color: #999 !important;
    font-size: 1rem !important;
    font-weight: 400 !important;
    aspect-ratio: 1 !important;
    padding: 0 !important;
    height: 44px !important;
    width: 44px !important;
    min-width: unset !important;
    transition: all 0.15s !important;
    backdrop-filter: blur(14px) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
div[data-testid="stButton"] button:hover {
    color: #FFD700 !important;
    border-color: #FFD700 !important;
    background: rgba(10,10,10,0.65) !important;
}
.no-fixtures {
    background: rgba(20,20,20,0.8); border: 1px solid #222;
    border-radius: 12px; padding: 3rem;
    text-align: center; color: #444;
}
/* Override details button style */
div[data-testid="stButton"] button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid #2a2a2a !important;
    color: #999 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 0.2rem 0.75rem !important;
    border-radius: 4px !important;
    font-weight: 500 !important;
}
div[data-testid="stButton"] button[kind="secondary"]:hover {
    border-color: #FFD700 !important;
    color: #FFD700 !important;
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">FIXTURES</div>', unsafe_allow_html=True)

fixtures = fixtures_upcoming(supabase)

if not fixtures:
    st.markdown('<div class="no-fixtures"><div style="font-size:2rem;">📅</div><div>No upcoming fixtures</div></div>', unsafe_allow_html=True)
    st.stop()

def render_form(form: str) -> str:
    if not form:
        return "<span style='color:#444;'>—</span>"
    color_map = {"W": "#FFD700", "D": "#888", "L": "#EF5350"}
    out = ""
    for ch in form.upper():
        c = color_map.get(ch, "#666")
        out += "<span style='color:" + c + ";font-weight:700;font-size:0.72rem;margin:0 1px;'>" + ch + "</span>"
    return out

# ── Detail dialog ─────────────────────────────────────────────────────────────
@st.dialog("Match Details", width="large")
def show_detail(fx):
    render_detail_card(fx, supabase, mode="fixture")

# ── Group by date and render ──────────────────────────────────────────────────
by_date = defaultdict(list)
for fx in fixtures:
    try:
        d = datetime.fromisoformat(str(fx["kickoff_ist"])).strftime("%A, %B %d")
    except Exception:
        d = str(fx.get("matchday_ist", "TBD"))
    by_date[d].append(fx)

for day, matches in by_date.items():
    st.markdown('<div class="date-header">' + day.upper() + '</div>', unsafe_allow_html=True)

    for fx in matches:
        home      = fx.get("home") or {}
        away      = fx.get("away") or {}
        home_code = home.get("team_code", "???")
        away_code = away.get("team_code", "???")
        home_id   = home.get("team_id")
        away_id   = away.get("team_id")
        group     = fx.get("group_name", "")
        stage     = fx.get("stage", "group")
        venue     = fx.get("venue", fx.get("city", ""))
        kickoff   = fx.get("kickoff_ist", "")

        ko        = format_kickoff(kickoff)
        home_rank = get_team_rank(supabase, home_id) if home_id else "—"
        away_rank = get_team_rank(supabase, away_id) if away_id else "—"
        home_form = render_form(get_team_form(supabase, home_id) if home_id else "")
        away_form = render_form(get_team_form(supabase, away_id) if away_id else "")
        stage_str = ("Group " + group) if stage == "group" and group else stage.replace("_", " ").title()

        home_flag = '<div style="display:flex;align-items:center;justify-content:center;">' + flag_img(home_code, 45) + '</div>'
        away_flag = '<div style="display:flex;align-items:center;justify-content:center;">' + flag_img(away_code, 45) + '</div>'
        home_name = '<div><div style="font-family:\'ChampionGothic\',sans-serif;font-size:1.5rem;letter-spacing:0.1em;color:#F0F0F0;line-height:1;">' + home_code + '</div></div>'
        away_name = '<div style="text-align:right;"><div style="font-family:\'ChampionGothic\',sans-serif;font-size:1.5rem;letter-spacing:0.1em;color:#F0F0F0;line-height:1;">' + away_code + '</div></div>'
        ko_div = '<div style="text-align:center;min-width:60px;max-width:90px;"><div style="font-family:\'Inter\',sans-serif;font-size:clamp(1rem,4vw,1.5rem);font-weight:800;color:#fff;letter-spacing:0.1em;line-height:1;white-space:nowrap;">' + ko + '</div></div>'

        card = f"""
            <div class="fix-card">
            <div style="display:grid;grid-template-columns:30px 1fr auto 1fr 30px;align-items:center;gap:0.6rem;width:100%;">
                {home_flag}
                {home_name}
                {ko_div}
                {away_name}
                {away_flag}
            </div>
            <div style="display:grid;grid-template-columns:1fr auto 1fr;align-items:center;margin-top:0.7rem;padding-top:0.6rem;border-top:1px solid #3a3a3a;font-size:0.9rem;font-family:'Inter',sans-serif;">
                <div style="display:flex;align-items:center;gap:0.5rem;"><span style="color:#888;font-weight:600;">{home_rank}</span>{home_form}</div>
                <div style="text-align:center;color:#999;">Match {fx.get("match_id","")} &middot; {stage_str}{' &middot; ' + venue if venue else ''}</div>
                <div style="display:flex;align-items:center;gap:0.5rem;justify-content:flex-end;">{away_form}<span style="color:#888;font-weight:600;">{away_rank}</span></div>
            </div>
            </div>
            """
        mid = fx["match_id"]
        clickable_card = (
            f'<a href="?page=MatchDetail&match_id={mid}" target="_self" style="text-decoration:none;display:block;position:relative;">'
            + card.replace(
                '<div class="fix-card">',
                '<div class="fix-card" style="position:relative;transition:border-color 0.15s;cursor:pointer;">',
                1
            )
            + '<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:1rem;color:rgba(255,255,255,0.08);pointer-events:none;">↗</div>'
            + '</a>'
        )
        st.markdown(clickable_card, unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:0.75rem;'></div>", unsafe_allow_html=True)