import streamlit as st
from core.utils import flag_img, format_kickoff
import pandas as pd
import base64, re
from functools import lru_cache
from pathlib import Path
from core.db import (
    fixtures_by_id,
    pred_map,
    form_map,
    rank_map,
    players_by_team,
    stadium_by_city
)

predictions = pred_map()
forms = form_map()
ranks = rank_map()

mid = st.session_state.get("detail_match_id")
if not mid:
    st.markdown("<div style='color:#999;font-family:Inter,sans-serif;text-align:center;padding:4rem;'>No match selected.</div>", unsafe_allow_html=True)
    st.stop()

# ── Data ──────────────────────────────────────────────────────────────────────
fx           = fixtures_by_id(mid)
home         = fx.get("home") or {}
away         = fx.get("away") or {}
home_code    = home.get("team_code", "???")
away_code    = away.get("team_code", "???")
home_name    = home.get("name", home_code)
away_name    = away.get("name", away_code)
home_id      = home.get("team_id")
away_id      = away.get("team_id")
group        = fx.get("group_name", "")
stage        = fx.get("stage", "group")
venue        = fx.get("venue", fx.get("city", ""))
kickoff      = fx.get("kickoff_ist", "")
ko           = format_kickoff(kickoff)
stage_str    = ("Group " + group) if stage == "group" and group else stage.replace("_", " ").title()
home_rank    = ranks.get(home_id, "—")
away_rank    = ranks.get(away_id, "—")
pred         = predictions.get(mid)
result       = (fx.get("results") or [None])[0] if isinstance(fx.get("results"), list) else fx.get("results")
home_form    = forms.get(home_id, "")
away_form    = forms.get(away_id, "")
home_players = players_by_team(home_id) if home_id else []
away_players = players_by_team(away_id) if away_id else []
stadium      = stadium_by_city(venue) if venue else {}

# ── H2H ───────────────────────────────────────────────────────────────────────
try:
    h2h_df = pd.read_csv("data/h2h.csv", index_col="Team")
    raw1   = str(h2h_df.at[home_code, away_code])
    raw2   = str(h2h_df.at[away_code, home_code])
    r1 = dict(zip(["W","D","L"], map(int, raw1.split("-")))) if raw1 != "-" else {"W":0,"D":0,"L":0}
    r2 = dict(zip(["W","D","L"], map(int, raw2.split("-")))) if raw2 != "-" else {"W":0,"D":0,"L":0}
    h2h = {"home_w": r1["W"] + r2["L"], "draws": r1["D"] + r2["D"], "away_w": r1["L"] + r2["W"]}
except Exception as e:
    st.exception(e)
    h2h = None

# ── Image helpers ─────────────────────────────────────────────────────────────
def _load_b64(path: str) -> str:
    try:
        with open(Path(path), "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return "" 
    
def player_img_tag(photo_key: str, num: str) -> str:
    b64 = _load_b64(str(Path("static") / "players" / photo_key)) if photo_key else ""
    if b64:
        return (
            "<img src='data:image/png;base64," + b64 + "' "
            "style='width:60px;height:60px;border-radius:50%;object-fit:cover;"
            "border:1px solid #2a2a2a;flex-shrink:0;'>"
        )
    return (
        "<div style='width:40px;height:40px;border-radius:50%;background:#141414;"
        "border:1px solid #2a2a2a;flex-shrink:0;display:flex;align-items:center;"
        "justify-content:center;font-family:ChampionGothic,sans-serif;"
        "font-size:0.8rem;color:#444;'>" + str(num) + "</div>"
    )

def stadium_bg(photo_key: str) -> str:
    b64 = _load_b64(str(Path("static") / "stadium" / photo_key)) if photo_key else ""
    return 'url("data:image/png;base64,' + b64 + '")' if b64 else "none"

# ── HTML helpers ──────────────────────────────────────────────────────────────
def form_html(form: str, align: str = "left") -> str:
    if not form:
        return "<span style='color:#333;font-family:Inter,sans-serif;font-size:0.72rem;'>—</span>"
    cmap = {"W": "#FFD700", "D": "#888", "L": "#EF5350"}
    out = "".join(
        "<span style='color:" + cmap.get(ch, "#666") + ";font-weight:700;"
        "font-size:0.75rem;margin:0 1px;font-family:Inter,sans-serif;'>" + ch + "</span>"
        for ch in form.upper()
    )
    return out

SEP = "<div style='border-top:1px solid rgba(255,255,255,0.0);margin:1.25rem 0;'></div>"
LABEL = "<div style='font-family:Inter,sans-serif;font-size:1.5rem;color:#999;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:10px;text-align:center;'>"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stButton button {
    background: rgba(10,10,10,0.65) !important;
    border: 1px solid #242424 !important;
    border-radius: 6px !important;
    color: #999 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em !important;
}
.stButton button:hover {
    border-color: #FFD700 !important;
    color: #FFD700 !important;
}
.stButton button {
    font-family: 'Inter', sans-serif !important;
}
* {
    text-transform: none;
}
</style>
""", unsafe_allow_html=True)

# ── Back + Title ──────────────────────────────────────────────────────────────
st.markdown(
    "<div style='display:flex;align-items:center;justify-content:space-between;margin:0.5rem 0 1.25rem 0;'>"
    "<div style='font-family:ChampionGothic,sans-serif;font-size:2rem;"
    "letter-spacing:0.08em;color:#F0F0F0;line-height:1;'>"
    "MATCH " + str(mid) +
    "<span style='font-family:Inter,sans-serif;font-size:1rem;color:#999;"
    "letter-spacing:0.12em;text-transform:uppercase;margin-left:1rem;vertical-align:middle;'>"
    + stage_str + " · " + ko + " IST</span>"
    "</div>"
    "<a href='?page=Fixtures' target='_self' style='text-decoration:none;display:flex;"
    "align-items:center;justify-content:center;width:32px;height:32px;"
    "background:rgba(10,10,10,0.65);backdrop-filter:blur(14px);"
    "-webkit-backdrop-filter:blur(14px);border:1px solid #242424;"
    "border-radius:6px;color:#666;"
    "font-size:0.85rem;flex-shrink:0;transition:all 0.15s;'>"
    "✕</a>"
    "</div>",
    unsafe_allow_html=True
)

# ── Score block ───────────────────────────────────────────────────────────────
if result:
    h_g = str(result.get("home_goals", "?"))
    a_g = str(result.get("away_goals", "?"))
    p_h = str(pred.get("pred_home_goals", "?")) if pred else "?"
    p_a = str(pred.get("pred_away_goals", "?")) if pred else "?"
    score_html = (
        "<div style='font-family:ChampionGothic,sans-serif;font-size:3rem;"
        "color:#fff;letter-spacing:0.15em;line-height:1;'>" + h_g + " – " + a_g + "</div>"
        "<div style='font-family:Inter,sans-serif;font-size:0.75rem;color:#444;margin-top:4px;'>"
        "(" + p_h + "–" + p_a + " pred)</div>"
    )
elif pred:
    h_g = str(pred.get("pred_home_goals", "?"))
    a_g = str(pred.get("pred_away_goals", "?"))
    conf = int(pred.get("model_confidence", 0) * 100)
    score_html = (
        "<div style='font-family:ChampionGothic,sans-serif;font-size:3rem;"
        "color:#fff;letter-spacing:0.15em;line-height:1;'>" + h_g + " – " + a_g + "</div>"
        "<div style='font-family:Inter,sans-serif;font-size:0.75rem;color:#999;margin-top:4px;'>"
        + str(conf) + "% confidence</div>"
    )
else:
    score_html = (
        "<div style='font-family:ChampionGothic,sans-serif;font-size:2rem;"
        "color:#fff;letter-spacing:0.15em;line-height:1;'>" + ko + "</div>"
        "<div style='font-family:Inter,sans-serif;font-size:0.62rem;color:#444;"
        "letter-spacing:0.14em;text-transform:uppercase;margin-top:4px;'>IST</div>"
    )

# ── Win prob bar ──────────────────────────────────────────────────────────────
if pred and not result:
    h_prob = pred.get("home_win_prob", 0)
    d_prob = pred.get("draw_prob", 0)
    a_prob = pred.get("away_win_prob", 0)
    prob_html = (
        SEP +
        LABEL + "Win Probability</div>"
        "<div style='display:flex;justify-content:space-between;font-family:Inter,sans-serif;"
        "font-size:0.7rem;color:#999;margin-bottom:6px;'>"
        "<span>" + home_code + " " + str(int(h_prob*100)) + "%</span>"
        "<span>Draw " + str(int(d_prob*100)) + "%</span>"
        "<span>" + str(int(a_prob*100)) + "% " + away_code + "</span>"
        "</div>"
        "<div style='display:flex;height:5px;border-radius:3px;overflow:hidden;'>"
        "<div style='width:" + str(int(h_prob*100)) + "%;background:#FFD700;opacity:0.9;'></div>"
        "<div style='width:" + str(int(d_prob*100)) + "%;background:#333;'></div>"
        "<div style='width:" + str(int(a_prob*100)) + "%;background:#888;opacity:0.9;'></div>"
        "</div>"
    )
else:
    prob_html = ""

# ── Venue ─────────────────────────────────────────────────────────────────────
photo_key = stadium.get("photo_key", "")
stad_name = stadium.get("name", venue or "TBD")
stad_city = stadium.get("city", "")
stad_cap  = "{:,}".format(stadium.get("capacity", 0)) if stadium.get("capacity") else "—"
stad_bg   = stadium_bg(photo_key)

venue_html = (
    SEP +
    LABEL +
    "<div style='position:relative;border:1px solid #2a2a2a;border-radius:8px;"
    "overflow:hidden;height:200px;'>"
    "<div style='position:absolute;inset:0;background-image:" + stad_bg + ";"
    "background-size:cover;background-position:center;'></div>"
    "<div style='position:absolute;inset:0;background:linear-gradient(to right,"
    "rgba(0,0,0,0.95 ) 35%,rgba(0,0,0,0.05) 90%);'></div>"
    "<div style='position:relative;z-index:1;padding:1.25rem 3rem;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;height:100%;'>"
    "<div style='font-family:ChampionGothic,sans-serif;font-size:2rem;"
    "color:#F0F0F0;letter-spacing:0.06em;line-height:1.2;'>" + stad_name + "</div>"
    "<div style='font-family:Inter,sans-serif;font-size:1.5rem;color:#666;margin-top:2px;letter-spacing: 0.04em; '>" + stad_city + "</div>"
    "<div style='font-family:Inter,sans-serif;font-size:1.25rem;color:#444;margin-top:1px;letter-spacing: 0.04em;'>Capacity " + stad_cap + "</div>"
    "</div></div>"
)

# ── H2H ───────────────────────────────────────────────────────────────────────
if h2h:
    total = h2h["home_w"] + h2h["draws"] + h2h["away_w"]
    h2h_html = (
        SEP +
        LABEL + 
        "<div style='display:grid;grid-template-columns:1fr auto auto auto 1fr;"
        "align-items:center;gap:1.5rem;padding:0.75rem 2rem;"
        "background:rgba(255,255,255,0.02);border:1px solid #3a3a3a;border-radius:8px;'>"
        "<span style='font-family:ChampionGothic,sans-serif;font-size:2rem;color:#F0F0F0;text-align:left;'>" + home_code + "</span>"
        "<div style='text-align:center;'>"
        "<div style='font-family:ChampionGothic,sans-serif;font-size:2rem;color:#F0f0f0;line-height:1;'>" + str(h2h["home_w"]) + "  -  " + "</div>"
        "</div>"
        "<div style='text-align:center;'>"
        "<div style='font-family:ChampionGothic,sans-serif;font-size:2rem;color:#f0f0f0;line-height:1;'>" + str(h2h["draws"]) + "</div>"
        "</div>"
        "<div style='text-align:center;'>"
        "<div style='font-family:ChampionGothic,sans-serif;font-size:2rem;color:#f0f0f0;line-height:1;'>" + "  -  " + str(h2h["away_w"]) + "</div>"
        "</div>"
        "<span style='font-family:ChampionGothic,sans-serif;font-size:2rem;color:#F0F0F0;text-align:right;'>" + away_code + "</span>"
        "</div>"
    )
else:
    h2h_html = (
        "<div style='background:rgba(10,10,10,0.65);backdrop-filter:blur(14px);"
        "-webkit-backdrop-filter:blur(14px);border:1px solid #242424;border-radius:8px;"
        "padding:1rem 1.4rem;text-align:center;font-family:Inter,sans-serif;"
        "font-size:1rem;color:#444;'>No H2H data available</div>"
    )

# ── Key players ───────────────────────────────────────────────────────────────
def players_col(players, code):
    html = (
        "<div>"
        "<div style='font-family:ChampionGothic,sans-serif;font-size:0.9rem;"
        "color:#666;margin-bottom:8px;letter-spacing:0.08em;'> </div>"
    )
    if players:
        for p in players:
            num      = str(p.get("number", ""))
            name     = p.get("full_name", "")
            position = p.get("position", "")
            photo    = player_img_tag(p.get("photo_key", ""), num)
            html += (
                "<div style='display:flex;align-items:center;gap:8px;"
                "background:rgba(255,255,255,0.02);border:1px solid #3a3a3a;"
                "border-radius:8px;padding:8px 10px;margin-bottom:5px;'>"
                + photo +
                "<div>"
                "<div style='font-family:Inter,sans-serif;font-size:1.25rem;"
                "color:#e0e0e0;font-weight:600;letter-spacing:0.08em;letter-spacing: 0.04em;'>" + name + "</div>"
                "<div style='font-family:Inter,sans-serif;font-size:0.9rem;font-weight:600;"
                "color:#888;margin-top:1px;text-align:left;letter-spacing:0.08em;'>" + num + " · " + position + "</div>"
                "</div></div>"
            )
    else:
        html += "<div style='color:#333;font-size:0.78rem;font-family:Inter,sans-serif;'>—</div>"
    html += "</div>"
    return html

if home_players or away_players:
    kp_html = (
        SEP +
        LABEL + "Key Players</div>"
        "<div style='display:grid;grid-template-columns:1fr 1fr;gap:1rem;'>"
        + players_col(home_players, home_code)
        + players_col(away_players, away_code)
        + "</div>"
    )
else:
    kp_html = ""

# ── Assemble full card ────────────────────────────────────────────────────────
card = (
    "<div style='background:rgba(10,10,10,0.65);backdrop-filter:blur(14px);"
    "-webkit-backdrop-filter:blur(14px);border-radius:12px;border:1px solid #242424;"
    "padding:3rem;'>"

    # Teams row
    "<div style='display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:1rem;'>"

    # Home
    "<div>"
    "<div style='display:flex;align-items:center;gap:1rem;'>"
    + flag_img(home_code, 45) +
    "<div style='font-family:ChampionGothic,sans-serif;font-size:2rem;"
    "letter-spacing:0.08em;color:#F0F0F0;line-height:1;'>" + home_code + "</div>"
    "</div>"
    "<div style='font-family:Inter,sans-serif;font-size:1.25rem;color:#666;margin-top:5px;'>" + home_name + "</div>"
    "<div style='display:flex;align-items:center;gap:0.5rem;margin-top:3px;'>"
    "<span style='font-family:Inter,sans-serif;font-size:0.9rem;color:#444;'>" + home_rank + "</span>"
    "<span style='font-family:Inter,sans-serif;font-size:0.9rem;color:#333;'>·</span>"
    + form_html(home_form) +
    "</div>"
    "</div>"

    # Score
    "<div style='text-align:center;'>" + score_html + "</div>"

    # Away
    "<div style='text-align:right;'>"
    "<div style='display:flex;align-items:center;justify-content:flex-end;gap:0.5rem;'>"
    "<div style='font-family:ChampionGothic,sans-serif;font-size:2rem;"
    "letter-spacing:0.08em;color:#F0F0F0;line-height:1;'>" + away_code + "</div>"
    + flag_img(away_code, 45) +
    "</div>"
    "<div style='font-family:Inter,sans-serif;font-size:1.25rem;color:#666;margin-top:5px;'>" + away_name + "</div>"
    "<div style='display:flex;align-items:center;justify-content:flex-end;gap:0.5rem;margin-top:3px;'>"
    + form_html(away_form) +
    "<span style='font-family:Inter,sans-serif;font-size:0.9rem;color:#333;'>·</span>"
    "<span style='font-family:Inter,sans-serif;font-size:0.9rem;color:#444;'>" + away_rank + "</span>"
    "</div>"
    "</div>"

    "</div>"  # end teams grid

    + prob_html
    + venue_html
    + h2h_html
    + kp_html

    + "</div>"  # end card
)

st.markdown(card, unsafe_allow_html=True)