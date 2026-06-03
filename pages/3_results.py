import streamlit as st
from datetime import date
from collections import defaultdict
from db import get_client, pred_all, get_team_rank, get_team_form
from utils import format_kickoff, flag_img

supabase = get_client()

st.markdown("""
<style>
.page-title {
    font-family: 'ChampionGothic', 'Inter', sans-serif;
    font-size: 4rem;
    letter-spacing: 0.08em;
    color: #F0F0F0;
    margin-bottom: 0.15rem;
}
.page-sub {
    font-size: 0.9rem; color: #555;
    letter-spacing: 0.12em; text-transform: uppercase;
    margin-bottom: 2rem;
}
.date-header {
    font-family:'Inter', sans-serif;
    font-weight: 800;
    font-size: 1.1rem;
    letter-spacing: 0.08em;
    color: #aaa;
    margin: 1.5rem 0 0.75rem 0;
}
.res-card {
    background: rgba(10,10,10,0.5);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-radius: 10px;
    border: 1px solid #242424;
    padding: 1.1rem 1.4rem;
    margin-bottom: 0.75rem;
}
.no-results {
    background: rgba(20,20,20,0.8); border: 1px solid #222;
    border-radius: 12px; padding: 3rem;
    text-align: center; color: #444;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="page-title">RESULTS</div>',
    unsafe_allow_html=True
)

all_preds = pred_all(supabase)
completed = [p for p in all_preds if p.get("fixture", {}) and p.get("fixture", {}).get("results")]

if not completed:
    st.markdown('<div class="no-results"><div style="font-size:2rem;">📊</div><div>No results yet</div></div>', unsafe_allow_html=True)
    st.stop()

def render_form(form: str) -> str:
    if not form:
        return "<span style='color:#444;'>—</span>"
    color_map = {"W": "#00C853", "D": "#FFC107", "L": "#EF5350"}
    out = ""
    for ch in form.upper():
        c = color_map.get(ch, "#666")
        out += "<span style='color:" + c + ";font-weight:700;font-size:0.72rem;margin:0 1px;'>" + ch + "</span>"
    return out

# Group by date
by_date = defaultdict(list)
for p in completed:
    fx = p.get("fixture", {})
    try:
        from datetime import datetime
        d = datetime.fromisoformat(str(fx.get("kickoff_ist", ""))).strftime("%A, %B %d")
    except Exception:
        d = "Unknown Date"
    by_date[d].append(p)

for day, preds in by_date.items():
    st.markdown('<div class="date-header">' + day.upper() + '</div>', unsafe_allow_html=True)

    for p in preds:
        fx      = p.get("fixture", {})
        results = fx.get("results", [])
        result  = results[0] if isinstance(results, list) and results else results or {}

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

        # Actual score
        actual_h   = result.get("home_goals", "?")
        actual_a   = result.get("away_goals", "?")
        actual_out = result.get("outcome", "?")

        # Predicted score
        pred_h   = p.get("pred_home_goals", "?")
        pred_a   = p.get("pred_away_goals", "?")
        pred_out = p.get("predicted_outcome", "?")

        correct = actual_out == pred_out
        correct_color = "#00C853" if correct else "#EF5350"
        correct_label = "✓" if correct else "✗"

        match_id  = fx.get("match_id", "")
        stage_str = ("Group " + group) if stage == "group" and group else stage.replace("_", " ").title()

        card = (
            '<div class="res-card">'

            # ── Row 1: flag | code | scores | code | flag ─────────────────
            '<div style="display:grid;grid-template-columns:28px 1fr auto 1fr 28px;'
            'align-items:center;gap:0.6rem;">'

            + flag_img(home_code, 30) +

            '<div>'
            '<div style="font-family:\'ChampionGothic\',sans-serif;font-size:1.5rem;'
            'letter-spacing:0.1em;color:#F0F0F0;line-height:1;">' + home_code + '</div>'
            '</div>'

            # Score center: actual big + predicted small inline
            '<div style="text-align:center;min-width:110px;">'
            '<div style="display:flex;align-items:baseline;justify-content:center;gap:1rem;">'
            '<div style="font-family:\'ChampionGothic\',sans-serif;font-size:1.5rem;'
            'color:#fff;letter-spacing:0.15em;line-height:1;">'
            + str(actual_h) + ' – ' + str(actual_a) +
            '</div>'
            '<div style="font-family:\'Inter\',sans-serif;font-weight:800;font-size:1.2rem;color:#666;">'
            '( ' + str(pred_h) + '–' + str(pred_a) + ' )'
            '</div>'
            '</div>'
            '</div>'

            '<div style="text-align:right;">'
            '<div style="font-family:\'ChampionGothic\',sans-serif;font-size:1.5rem;'
            'letter-spacing:0.1em;color:#F0F0F0;line-height:1;">' + away_code + '</div>'
            '</div>'

            + flag_img(away_code, 30) +

            '</div>'

            # ── Row 2: meta ───────────────────────────────────────────────
            '<div style="display:grid;grid-template-columns:1fr auto 1fr;'
            'align-items:center;margin-top:0.7rem;padding-top:0.6rem;'
            'border-top:1px solid #1e1e1e;font-size:0.75rem;font-family:\'Inter\',sans-serif;">'

            '<div style="display:flex;align-items:center;gap:0.5rem;">'
            '<span style="color:#888;font-weight:600;">' + home_rank + '</span>'
            + home_form +
            '</div>'

            '<div style="text-align:center;color:#555;">'
            'Match ' + str(match_id)
            + (' &middot; ' + venue if venue else '')
            + '</div>'

            '<div style="display:flex;align-items:center;gap:0.5rem;justify-content:flex-end;">'
            + away_form +
            '<span style="color:#888;font-weight:600;">' + away_rank + '</span>'
            '</div>'

            '</div>'
            '</div>'
        )

        st.markdown(card, unsafe_allow_html=True)