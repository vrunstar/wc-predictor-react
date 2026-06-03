import streamlit as st
from datetime import date
import base64
from db import get_client, fixtures_today, pred_all
from utils import format_kickoff, flag_img

supabase = get_client()

st.markdown("""
<style>
.section-title {
    font-family: 'Gilker', sans-serif;
    font-size: 1.8rem;
    letter-spacing: 0.08em;
    color: #F0F0F0;
    margin: 2rem 0 1rem 0;
}
.home-card {
    background: rgba(10,10,10,0.65);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-radius: 10px;
    border: 1px solid #242424;
    padding: 0.85rem 1rem;
    margin-bottom: 0.5rem;
    display: grid;
    grid-template-columns: 28px 1fr auto 1fr 28px;
    align-items: center;
    gap: 0.5rem;
}
.hc-code {
    font-family: 'Gilker', sans-serif;
    font-size: 1.2rem;
    letter-spacing: 0.08em;
    color: #F0F0F0;
}
.hc-center {
    font-family: 'Inter', sans-serif;
    font-weight: 900;
    font-size: 1.4rem;
    color: #fff;
    text-align: center;
    letter-spacing: 0.12em;
    line-height: 1;
}
.no-content {
    background: rgba(10,10,10,0.65);
    border: 1px solid #242424;
    border-radius: 10px;
    padding: 1.5rem;
    text-align: center;
    color: #444;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
try:
    with open("static/bg.png", "rb") as f:
        _bg = base64.b64encode(f.read()).decode()
    bg_url = "url('data:image/png;base64," + _bg + "')"
except Exception:
    bg_url = "none"

tournament_start = date(2026, 6, 11)
days_left = (tournament_start - date.today()).days
countdown = str(days_left) + " days to go" if days_left > 0 else "Tournament underway"

st.markdown("""
<style>
.hero {
    position: relative;
    width: 100%;
    min-height: 280px;
    background-image: """ + bg_url + """;
    background-size: cover;
    background-position: center;
    border-radius: 12px;
    overflow: hidden;
    display: flex;
    align-items: center;
    padding: 3rem;
    margin-bottom: 1rem;
    box-sizing: border-box;
}
.hero::before {
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.55);
    border-radius: 12px;
}
.hero-content { position: relative; z-index: 1; }
.hero-tag {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #00C853;
    font-weight: 600;
    margin-bottom: 0.75rem;
}
.hero-title {
    font-family: 'ChampionGothic', sans-serif;
    font-size: clamp(3rem, 6vw, 5.5rem);
    line-height: 0.95;
    color: #F0F0F0;
    letter-spacing: 0.04em;
    margin-bottom: 1rem;
}
.hero-sub {
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    color: #888;
    max-width: 420px;
    line-height: 1.6;
    margin-bottom: 1.5rem;
}
.hero-pills { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.pill {
    background: rgba(255,200,255,0.1);
    border: 1px solid rgba(255, 255, 255,0.25);
    color: #fff;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 500;
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.05em;
}
</style>
<div class="hero">
  <div class="hero-content">
    <div class="hero-title">WORLD CUP 2026<br> PREDICTOR</div>
    <div class="hero-sub">Predictions for all 104 matches across USA, Canada &amp; Mexico.</div>
    <div class="hero-pills">
      <span class="pill">USA · Canada · Mexico</span>
      <span class="pill">48 Teams · 12 Groups</span>
      <span class="pill">""" + countdown + """</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────
fixtures  = fixtures_today(supabase)
matches   = [fx for fx in fixtures if not fx.get("results")]
all_preds = pred_all(supabase)
completed = [p for p in all_preds if p.get("fixture", {}).get("results")][:4]

# ── Cards ─────────────────────────────────────────────────────────────────────
def match_card(fx):
    home      = fx.get("home") or {}
    away      = fx.get("away") or {}
    home_code = home.get("team_code", "???")
    away_code = away.get("team_code", "???")
    center    = format_kickoff(fx.get("kickoff_ist", ""))
    return (
        '<div class="home-card">'
        + flag_img(home_code, 26)
        + '<span class="hc-code">' + home_code + '</span>'
        + '<div class="hc-center">' + center + '</div>'
        + '<span class="hc-code" style="text-align:right;">' + away_code + '</span>'
        + flag_img(away_code, 26)
        + '</div>'
    )

def result_card(pred):
    fx        = pred.get("fixture") or {}
    home      = fx.get("home") or {}
    away      = fx.get("away") or {}
    home_code = home.get("team_code", "???")
    away_code = away.get("team_code", "???")
    res_raw   = fx.get("results") or {}
    res       = (res_raw[0] if isinstance(res_raw, list) and res_raw else res_raw) or {}
    center    = str(res.get("home_goals", "?")) + " – " + str(res.get("away_goals", "?"))
    return (
        '<div class="home-card">'
        + flag_img(home_code, 26)
        + '<span class="hc-code">' + home_code + '</span>'
        + '<div class="hc-center">' + center + '</div>'
        + '<span class="hc-code" style="text-align:right;">' + away_code + '</span>'
        + flag_img(away_code, 26)
        + '</div>'
    )

# ── Layout ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-title">TODAY\'S MATCHES</div>', unsafe_allow_html=True)
    if not matches:
        st.markdown('<div class="no-content">No matches today</div>', unsafe_allow_html=True)
    else:
        for fx in matches:
            st.markdown(match_card(fx), unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-title">LATEST RESULTS</div>', unsafe_allow_html=True)
    if not completed:
        st.markdown('<div class="no-content">No results yet</div>', unsafe_allow_html=True)
    else:
        for p in completed:
            st.markdown(result_card(p), unsafe_allow_html=True)