import streamlit as st
from datetime import date
from db import get_client, fixtures_today, pred_by_match, pred_updated, get_team_form, get_team_rank
from predictor import load_model, predict_match
from utils import format_kickoff, flag_img

supabase = get_client()

st.markdown("""
<style>
.page-title {
    font-family:'ChampionGothic',sans-serif; font-weight:900;
    font-size: 5rem;
    letter-spacing: 0.1em;
    color: #F0F0F0;
    margin-bottom: 0.15rem;
}
.page-sub {
    font-family: 'Inter', sans-serif;
    font-weight: 800;
    font-size: 1.25rem; color: #999;
    letter-spacing: 0.12em; text-transform: none;
    margin-bottom: 2rem;
}
.pred-card {
    background: rgba(10,10,10,0.50);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 10px;
    border: 1px solid #111;
    padding: 1.1rem 1.4rem;
    margin-bottom: 0.75rem;
}
.no-games {
    background: rgba(10,10,10,0.5); border: 1px solid #222;
    border-radius: 12px; padding: 3rem;
    text-align: center; color: #444; font-size: 1.5rem; font-family: 'ChampionGothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="page-title">PREDICTIONS</div>'
    '<div class="page-sub">' + date.today().strftime('%A, %B %d') + '</div>',
    unsafe_allow_html=True
)

fixtures = fixtures_today(supabase)

if not fixtures:
    st.markdown('<div class="no-games"><div>No matches today</div></div>', unsafe_allow_html=True)
    st.stop()

@st.cache_resource
def get_model():
    return load_model()

model, features = get_model()

st.divider()

def render_form(form: str) -> str:
    if not form:
        return "<span style='color:#444;'>—</span>"
    color_map = {"W": "#00C853", "D": "#F1f1f1", "L": "#EF5350"}
    out = ""
    for ch in form.upper():
        c = color_map.get(ch, "#666")
        out += "<span style='color:" + c + ";font-weight:700;font-size:0.72rem;margin:0 1px;'>" + ch + "</span>"
    return out

for fx in fixtures:
    mid       = fx["match_id"]
    home      = fx.get("home", {})
    away      = fx.get("away", {})
    home_name = home.get("name", "—")
    away_name = away.get("name", "—")
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

    pred = pred_by_match(supabase, mid)
    if not pred:
        try:
            pred = predict_match(model, features, fx)
            pred_updated(supabase, pred)
        except Exception:
            pred = {}

    conf          = int(pred.get("model_confidence", 0) * 100)
    h_goals       = pred.get("pred_home_goals", 0)
    a_goals       = pred.get("pred_away_goals", 0)
    outcome       = pred.get("predicted_outcome", "?")
    outcome_label = {"H": home_code, "A": away_code, "D": "Draw"}.get(outcome, "—")

    home_form = render_form(get_team_form(supabase, home_id) if home_id else "")
    away_form = render_form(get_team_form(supabase, away_id) if away_id else "")

    stage_str = ("Group " + group) if stage == "group" and group else stage.replace("_", " ").title()

    # Row 1: flag | code | score | code | flag
    # Row 2: rank · form  |  time · city · conf  |  form · rank

    home_flag_div = '<div style="display:flex;align-items:center;justify-content:center;">' + flag_img(home_code, 45) + '</div>'
    away_flag_div = '<div style="display:flex;align-items:center;justify-content:center;">' + flag_img(away_code, 45) + '</div>'

    card = f"""
    <div class="pred-card" style="position:relative;transition:border-color 0.15s;cursor:pointer;">
    <div style="display:grid;grid-template-columns:30px 1fr auto 1fr 30px;align-items:center;gap:0.6rem;width:100%;">
        {home_flag_div}
        <div>
        <div style="font-family:'ChampionGothic',sans-serif;font-size:1.5rem;letter-spacing:0.1em;color:#F0F0F0;line-height:1;">{home_code}</div>
        </div>
        <div style="text-align:center;min-width:90px;">
        <div style="font-family:'ChampionGothic',sans-serif;font-size:2rem;color:#fff;letter-spacing:0.15em;line-height:1;">{h_goals} – {a_goals}</div>
        </div>
        <div style="text-align:right;">
        <div style="font-family:'ChampionGothic',sans-serif;font-size:1.5rem;letter-spacing:0.1em;color:#F0F0F0;line-height:1;">{away_code}</div>
        </div>
        {away_flag_div}
    </div>
    <div style="display:grid;grid-template-columns:1fr auto 1fr;align-items:center;margin-top:0.7rem;padding-top:0.6rem;border-top:1px solid #3a3a3a;font-size:0.9rem;font-family:'Inter',sans-serif;">
        <div style="display:flex;align-items:center;gap:0.5rem;"><span style="color:#888;font-weight:600;">{home_rank}</span>{home_form}</div>
        <div style="text-align:center;color:#999;">{ko}{(' &middot; ' + venue) if venue else ''} &middot; <span style="color:#888;font-weight:600;">{conf}% {outcome_label}</span></div>
        <div style="display:flex;align-items:center;gap:0.5rem;justify-content:flex-end;">{away_form}<span style="color:#888;font-weight:600;">{away_rank}</span></div>
    </div>
    <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:1rem;color:rgba(255,255,255,0.08);pointer-events:none;">↗</div>
    </div>
    """

    clickable_card = f'<a href="?page=MatchDetail&match_id={mid}" target="_self" style="text-decoration:none;display:block;">{card}</a>'
    st.markdown(clickable_card, unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:0.75rem;'></div>", unsafe_allow_html=True)