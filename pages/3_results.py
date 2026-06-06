import streamlit as st
from datetime import date
from collections import defaultdict
from core.db import pred_map, rank_map, form_map
from core.utils import format_kickoff, flag_img, render_form

predictions = pred_map()
forms = form_map()
ranks = rank_map()

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
    font-size: 0.9rem; color: #999;
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
    font-family:'ChampionGothic',sans-serif; font-weight:900;
    background: rgba(20,20,20,0.8); border: 1px solid #222;
    border-radius: 12px; padding: 3rem;
    text-align: center; color: #444;
    font-size: 2rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="page-title">RESULTS</div>',
    unsafe_allow_html=True
)

all_preds = pred_map()
completed = [p for p in all_preds if p.get("fixture", {}) and p.get("fixture", {}).get("results")]

if not completed:
    st.markdown('<div class="no-results"><div>No results yet</div></div>', unsafe_allow_html=True)
    st.stop()

def render_form(form: str) -> str:
    if not form:
        return "<span style='color:#444;'>—</span>"
    color_map = {"W": "#00C853", "D": "#BCBCBC", "L": "#EF5350"}
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
        home_rank = ranks.get(home_id, "—")
        away_rank = ranks.get(away_id, "—")
        home_form = render_form(forms.get(home_id, ""))
        away_form = render_form(forms.get(away_id, ""))

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

        home_flag_div = '<div style="display:flex;align-items:center;justify-content:center;">' + flag_img(home_code, 26) + '</div>'
        away_flag_div = '<div style="display:flex;align-items:center;justify-content:center;">' + flag_img(away_code, 26) + '</div>'

        card = f"""
        <div class="res-card" style="position:relative;transition:border-color 0.15s;cursor:pointer;">
        <div style="display:grid;grid-template-columns:30px 1fr auto 1fr 30px;align-items:center;gap:0.6rem;width:100%;">
            {home_flag_div}
            <div><div style="font-family:'ChampionGothic',sans-serif;font-size:1.5rem;letter-spacing:0.1em;color:#F0F0F0;line-height:1;">{home_code}</div></div>
            <div style="text-align:center;min-width:110px;">
            <div style="display:flex;align-items:baseline;justify-content:center;gap:1rem;">
                <div style="font-family:'ChampionGothic',sans-serif;font-size:1.5rem;color:#fff;letter-spacing:0.15em;line-height:1;">{actual_h} – {actual_a}</div>
                <div style="font-family:'Inter',sans-serif;font-weight:800;font-size:1.2rem;color:#666;">( {pred_h}–{pred_a} )</div>
            </div>
            </div>
            <div style="text-align:right;"><div style="font-family:'ChampionGothic',sans-serif;font-size:1.5rem;letter-spacing:0.1em;color:#F0F0F0;line-height:1;">{away_code}</div></div>
            {away_flag_div}
        </div>
        <div style="display:grid;grid-template-columns:1fr auto 1fr;align-items:center;margin-top:0.7rem;padding-top:0.6rem;border-top:1px solid #1e1e1e;font-size:0.9rem;font-family:'Inter',sans-serif;">
            <div style="display:flex;align-items:center;gap:0.5rem;"><span style="color:#888;font-weight:600;">{home_rank}</span>{home_form}</div>
            <div style="text-align:center;color:#999;">Match {match_id}{(' &middot; ' + venue) if venue else ''}</div>
            <div style="display:flex;align-items:center;gap:0.5rem;justify-content:flex-end;">{away_form}<span style="color:#888;font-weight:600;">{away_rank}</span></div>
        </div>
        <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:1rem;color:rgba(255,255,255,0.08);pointer-events:none;">↗</div>
        </div>
        """

        mid = fx.get("match_id")
        clickable_card = f'<a href="?page=MatchDetail&match_id={mid}" target="_self" style="text-decoration:none;display:block;">{card}</a>'
        st.markdown(clickable_card, unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:0.75rem;'></div>", unsafe_allow_html=True)