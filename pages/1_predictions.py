import streamlit as st
from datetime import date
from db import get_client, fixtures_today, pred_by_match, pred_updated, get_team_form, get_team_rank
from predictor import load_model, predict_match
from utils import format_kickoff, flag_img

supabase = get_client()

st.markdown("""
<style>
.page-title {
    font-family: 'ChampionGothic', sans-serif;
    font-size: 4rem;
    letter-spacing: 0.08em;
    color: #F0F0F0;
    margin-bottom: 0.15rem;
}
.page-sub {
    font-family: 'Inter', sans-serif;
    font-weight: 800;
    font-size: 1.1rem; color: #555;
    letter-spacing: 0.12em; text-transform: uppercase;
    margin-bottom: 2rem;
}
.pred-card {
    background: rgba(10,10,10,0.50);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border-radius: 10px;
    border: 1px solid #111;
    padding: 1.1rem 1.4rem;
    margin-bottom: 0.75rem;
}
.no-games {
    background: rgba(20,20,20,0.8); border: 1px solid #222;
    border-radius: 12px; padding: 3rem;
    text-align: center; color: #444;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="page-title">TODAY\'S PREDICTIONS</div>'
    '<div class="page-sub">' + date.today().strftime('%A, %B %d') + '</div>',
    unsafe_allow_html=True
)

fixtures = fixtures_today(supabase)

if not fixtures:
    st.markdown('<div class="no-games"><div style="font-size:2rem;">📅</div><div>No matches today</div></div>', unsafe_allow_html=True)
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

    card = (
        '<div class="pred-card">'

        # ── Row 1: teams + score ──────────────────────────────────────────
        '<div style="display:grid;grid-template-columns:28px 1fr auto 1fr 28px;'
        'align-items:center;gap:0.6rem;">'

        # home flag
        + flag_img(home_code, 30) +

        # home code + name
        '<div>'
        '<div style="font-family:\'ChampionGothic\',sans-serif;font-size:1.5rem;'
        'letter-spacing:0.1em;color:#F0F0F0;line-height:1;">' + home_code + '</div>'
        ''
        '</div>'

        # score
        '<div style="text-align:center;min-width:90px;">'
        '<div style="font-family:\'ChampionGothic\',sans-serif;font-size:2rem;'
        'color:#fff;letter-spacing:0.15em;line-height:1;">'
        + str(h_goals) + ' – ' + str(a_goals) +
        '</div>'
        ''
        '</div>'

        # away code + name
        '<div style="text-align:right;">'
        '<div style="font-family:\'ChampionGothic\',sans-serif;font-size:1.5rem;'
        'letter-spacing:0.1em;color:#F0F0F0;line-height:1;">' + away_code + '</div>'
        ''
        '</div>'

        # away flag
        + flag_img(away_code, 30) +

        '</div>'

        # ── Row 2: meta ───────────────────────────────────────────────────
        '<div style="display:grid;grid-template-columns:1fr auto 1fr;'
        'align-items:center;margin-top:0.7rem;padding-top:0.6rem;'
        'border-top:1px solid #1e1e1e;font-size:0.75rem; font-family:\'Inter\',sans-serif">'

        # Left: rank · form
        '<div style="display:flex;align-items:center;gap:0.5rem;">'
        '<span style="color:#888;font-weight:600;">' + home_rank + '</span>'
        + home_form +
        '</div>'

        # Center: time · city · confidence
        '<div style="text-align:center;color:#555;">'
        + ko
        + (' &middot; ' + venue if venue else '')
        + ' &middot; <span style="color:#888;font-weight:600;">' + str(conf) + '% ' + outcome_label + '</span>'
        '</div>'

        # Right: form · rank
        '<div style="display:flex;align-items:center;gap:0.5rem;justify-content:flex-end;">'
        + away_form +
        '<span style="color:#888;font-weight:600;">' + away_rank + '</span>'
        '</div>'

        '</div>'
        '</div>'
    )

    st.markdown(card, unsafe_allow_html=True)