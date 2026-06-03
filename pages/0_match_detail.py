import streamlit as st
from db import get_client, fixtures_by_id, pred_by_match, get_team_form, get_team_rank, players_by_team, stadium_by_city
from utils import flag_img, format_kickoff
import pandas as pd
import base64, re
from functools import lru_cache
from pathlib import Path

supabase = get_client()

mid = st.session_state.get("detail_match_id")
if not mid:
    st.markdown("<div style='color:#555;font-family:Inter,sans-serif;text-align:center;padding:4rem;'>No match selected.</div>", unsafe_allow_html=True)
    st.stop()

# ── Data ──────────────────────────────────────────────────────────────────────
fx           = fixtures_by_id(supabase, mid)
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
home_rank    = get_team_rank(supabase, home_id) if home_id else "—"
away_rank    = get_team_rank(supabase, away_id) if away_id else "—"
pred         = pred_by_match(supabase, mid)
result       = (fx.get("results") or [None])[0] if isinstance(fx.get("results"), list) else fx.get("results")
home_form    = get_team_form(supabase, home_id) if home_id else ""
away_form    = get_team_form(supabase, away_id) if away_id else ""
home_players = players_by_team(supabase, home_id) if home_id else []
away_players = players_by_team(supabase, away_id) if away_id else []
stadium      = stadium_by_city(supabase, venue) if venue else {}

# ── H2H from CSV ──────────────────────────────────────────────────────────────
try:
    h2h_df = pd.read_csv("data/h2h.csv", index_col="Team")
    raw1   = str(h2h_df.at[home_code, away_code])  # home as home team
    raw2   = str(h2h_df.at[away_code, home_code])  # away as home team
    r1 = dict(zip(["W","D","L"], map(int, raw1.split("-")))) if raw1 != "-" else {"W":0,"D":0,"L":0}
    r2 = dict(zip(["W","D","L"], map(int, raw2.split("-")))) if raw2 != "-" else {"W":0,"D":0,"L":0}
    h2h = {
        "home_w": r1["W"] + r2["L"],
        "draws":  r1["D"] + r2["D"],
        "away_w": r1["L"] + r2["W"],
    }
except Exception:
    h2h = None

# ── Image helpers ─────────────────────────────────────────────────────────────
@lru_cache(maxsize=32)
def _load_img(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

def stadium_img(photo_key: str) -> str:
    if not photo_key:
        return "none"
    b64 = _load_img(f"static/stadium/{photo_key}")
    return f"url('data:image/png;base64,{b64}')" if b64 else "none"

def player_img(photo_key: str) -> str:
    if not photo_key:
        return ""
    b64 = _load_img(f"static/players/{photo_key}")
    if not b64:
        return ""
    return f"<img src='data:image/png;base64,{b64}' style='width:44px;height:44px;border-radius:50%;object-fit:cover;border:1px solid #2a2a2a;flex-shrink:0;'>"

# ── Form helper ───────────────────────────────────────────────────────────────
def form_html(form, align="left"):
    if not form:
        return "<span style='color:#333;font-family:Inter,sans-serif;font-size:0.72rem;'>—</span>"
    cmap = {"W": "#FFD700", "D": "#888", "L": "#EF5350"}
    out = "".join(
        "<span style='color:" + cmap.get(ch, "#666") + ";font-weight:700;font-size:0.78rem;"
        "margin:0 2px;font-family:Inter,sans-serif;'>" + ch + "</span>"
        for ch in form.upper()
    )
    return "<div style='text-align:" + align + ";margin-top:5px;'>" + out + "</div>"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stButton button {
    background: rgba(10,10,10,0.65) !important;
    border: 1px solid #242424 !important;
    border-radius: 6px !important;
    color: #555 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em !important;
}
.stButton button:hover {
    border-color: #FFD700 !important;
    color: #FFD700 !important;
}
</style>
""", unsafe_allow_html=True)

SEP   = "border:none;border-top:1px solid #1e1e1e;margin:1.5rem 0 1.25rem 0;"
LABEL = ("font-family:Inter,sans-serif;font-size:0.62rem;color:#444;"
         "letter-spacing:0.15em;text-transform:uppercase;margin-bottom:10px;display:block;")

# ── Back ──────────────────────────────────────────────────────────────────────
if st.button("← Fixtures"):
    st.session_state["page"] = "Fixtures"
    st.rerun()

st.markdown("<br>", unsafe_allow_html=True)
# ── Full page card ────────────────────────────────────────────────────────────
st.markdown(
    "<div style='background:rgba(10,10,10,0.65);backdrop-filter:blur(14px);"
    "-webkit-backdrop-filter:blur(14px);border-radius:12px;border:1px solid #242424;"
    "padding:2rem;'>",
    unsafe_allow_html=True
)
# ── Match meta ────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-family:Inter,sans-serif;font-size:0.7rem;color:#555;"
    "letter-spacing:0.12em;text-transform:uppercase;margin-bottom:1.25rem;'>"
    + stage_str + " · Match " + str(mid) + " · " + ko + " IST</div>",
    unsafe_allow_html=True
)



# ── Section 1: Teams + Score ──────────────────────────────────────────────────
col_h, col_score, col_a = st.columns([5, 3, 5])

with col_h:
    st.markdown(
        flag_img(home_code, 44) +
        "<div style='font-family:ChampionGothic,sans-serif;font-size:2.4rem;"
        "letter-spacing:0.06em;color:#F0F0F0;line-height:1;margin-top:8px;'>" + home_code + "</div>"
        "<div style='font-family:Inter,sans-serif;font-size:0.8rem;color:#666;"
        "margin-top:4px;'>" + home_name + "</div>"
        "<div style='display:flex;align-items:center;gap:0.75rem;margin-top:4px;'>"
        "<span style='font-family:Inter,sans-serif;font-size:0.72rem;color:#444;'>" + home_rank + "</span>"
        + form_html(home_form, "left") +
        "</div>",
        unsafe_allow_html=True
    )

with col_score:
    if result:
        h_g = str(result.get("home_goals", "?"))
        a_g = str(result.get("away_goals", "?"))
        p_h = str(pred.get("pred_home_goals", "?")) if pred else "?"
        p_a = str(pred.get("pred_away_goals", "?")) if pred else "?"
        score_block = (
            "<div style='text-align:center;padding-top:0.75rem;'>"
            "<div style='font-family:ChampionGothic,sans-serif;font-size:3.2rem;"
            "color:#fff;letter-spacing:0.12em;line-height:1;'>" + h_g + " – " + a_g + "</div>"
            "<div style='font-family:Inter,sans-serif;font-size:0.78rem;color:#444;margin-top:6px;'>"
            "(" + p_h + "–" + p_a + " pred)</div>"
            "</div>"
        )
    elif pred:
        h_g = str(pred.get("pred_home_goals", "?"))
        a_g = str(pred.get("pred_away_goals", "?"))
        conf = int(pred.get("model_confidence", 0) * 100)
        score_block = (
            "<div style='text-align:center;padding-top:0.75rem;'>"
            "<div style='font-family:ChampionGothic,sans-serif;font-size:3.2rem;"
            "color:#fff;letter-spacing:0.12em;line-height:1;'>" + h_g + " – " + a_g + "</div>"
            "<div style='font-family:Inter,sans-serif;font-size:0.78rem;color:#555;margin-top:6px;'>"
            + str(conf) + "% confidence</div>"
            "</div>"
        )
    else:
        score_block = (
            "<div style='text-align:center;padding-top:0.75rem;'>"
            "<div style='font-family:ChampionGothic,sans-serif;font-size:2.4rem;"
            "color:#fff;letter-spacing:0.12em;line-height:1;'>" + ko + "</div>"
            "<div style='font-family:Inter,sans-serif;font-size:0.65rem;color:#444;"
            "letter-spacing:0.14em;text-transform:uppercase;margin-top:5px;'>IST</div>"
            "</div>"
        )
    st.markdown(score_block, unsafe_allow_html=True)

with col_a:
    st.markdown(
        "<div style='text-align:right;'>"
        + flag_img(away_code, 44) +
        "<div style='font-family:ChampionGothic,sans-serif;font-size:2.4rem;"
        "letter-spacing:0.06em;color:#F0F0F0;line-height:1;margin-top:8px;'>" + away_code + "</div>"
        "<div style='font-family:Inter,sans-serif;font-size:0.8rem;color:#666;"
        "margin-top:4px;'>" + away_name + "</div>"
        "<div style='display:flex;align-items:center;justify-content:flex-end;gap:0.75rem;margin-top:4px;'>"
        + form_html(away_form, "right") +
        "<span style='font-family:Inter,sans-serif;font-size:0.72rem;color:#444;'>" + away_rank + "</span>"
        "</div>",
        unsafe_allow_html=True
    )

# ── Section 2: Win probability ────────────────────────────────────────────────
if pred and not result:
    h_prob = pred.get("home_win_prob", 0)
    d_prob = pred.get("draw_prob", 0)
    a_prob = pred.get("away_win_prob", 0)
    st.markdown("<hr style='" + SEP + "'>", unsafe_allow_html=True)
    st.markdown("<span style='" + LABEL + "'>Win Probability</span>", unsafe_allow_html=True)
    st.markdown(
        "<div style='display:flex;justify-content:space-between;font-family:Inter,sans-serif;"
        "font-size:0.72rem;color:#555;margin-bottom:7px;'>"
        "<span>" + home_code + " · " + str(int(h_prob*100)) + "%</span>"
        "<span>Draw · " + str(int(d_prob*100)) + "%</span>"
        "<span>" + str(int(a_prob*100)) + "% · " + away_code + "</span>"
        "</div>"
        "<div style='display:flex;height:5px;border-radius:3px;overflow:hidden;'>"
        "<div style='width:" + str(int(h_prob*100)) + "%;background:#FFD700;opacity:0.9;'></div>"
        "<div style='width:" + str(int(d_prob*100)) + "%;background:#333;'></div>"
        "<div style='width:" + str(int(a_prob*100)) + "%;background:#888;opacity:0.9;'></div>"
        "</div>",
        unsafe_allow_html=True
    )

# ── Section 3: Venue ──────────────────────────────────────────────────────────
st.markdown("<hr style='" + SEP + "'>", unsafe_allow_html=True)
st.markdown("<span style='" + LABEL + "'>Venue</span>", unsafe_allow_html=True)

photo_key  = stadium.get("photo_key", "")
stad_name  = stadium.get("name", venue or "TBD")
stad_city  = stadium.get("city", "")
stad_cap   = f"{stadium.get('capacity', 0):,}" if stadium.get("capacity") else "—"
stad_bg    = stadium_img(photo_key)
print(photo_key)
st.markdown(
    "<div style='position:relative;border:1px solid #2a2a2a;border-radius:8px;"
    "overflow:hidden;height:100px;'>"
    "<div style='position:absolute;inset:0;background-image:" + stad_bg + ";"
    "background-size:cover;background-position:center;'></div>"
    "<div style='position:absolute;inset:0;background:linear-gradient(to right,"
    "rgba(0,0,0,0.97) 35%,rgba(0,0,0,0.15) 100%);'></div>"
    "<div style='position:relative;z-index:1;padding:0.9rem 1.2rem;'>"
    "<div style='font-family:ChampionGothic,sans-serif;font-size:1.1rem;"
    "color:#F0F0F0;letter-spacing:0.06em;line-height:1.2;'>" + stad_name + "</div>"
    "<div style='font-family:Inter,sans-serif;font-size:0.75rem;color:#666;margin-top:3px;'>" + stad_city + "</div>"
    "<div style='font-family:Inter,sans-serif;font-size:0.72rem;color:#444;margin-top:1px;'>Capacity " + stad_cap + "</div>"
    "</div></div>",
    unsafe_allow_html=True
)

# ── Section 4: H2H ────────────────────────────────────────────────────────────
st.markdown("<hr style='" + SEP + "'>", unsafe_allow_html=True)
st.markdown("<span style='" + LABEL + "'>Head to Head · Since 2000</span>", unsafe_allow_html=True)

if h2h:
    total = h2h["home_w"] + h2h["draws"] + h2h["away_w"]
    st.markdown(
        "<div style='display:grid;grid-template-columns:1fr auto auto auto 1fr;"
        "align-items:center;gap:1rem;padding:0.85rem 1.25rem;"
        "background:rgba(255,255,255,0.02);border:1px solid #1e1e1e;border-radius:8px;'>"

        # Home team
        "<div style='font-family:ChampionGothic,sans-serif;font-size:1.1rem;"
        "color:#F0F0F0;'>" + home_code + "</div>"

        # Home wins
        "<div style='text-align:center;'>"
        "<div style='font-family:ChampionGothic,sans-serif;font-size:1.6rem;"
        "color:#FFD700;line-height:1;'>" + str(h2h["home_w"]) + "</div>"
        "<div style='font-family:Inter,sans-serif;font-size:0.55rem;color:#333;"
        "letter-spacing:0.1em;text-transform:uppercase;margin-top:2px;'>W</div>"
        "</div>"

        # Draws
        "<div style='text-align:center;'>"
        "<div style='font-family:ChampionGothic,sans-serif;font-size:1.6rem;"
        "color:#555;line-height:1;'>" + str(h2h["draws"]) + "</div>"
        "<div style='font-family:Inter,sans-serif;font-size:0.55rem;color:#333;"
        "letter-spacing:0.1em;text-transform:uppercase;margin-top:2px;'>D</div>"
        "</div>"

        # Away wins
        "<div style='text-align:center;'>"
        "<div style='font-family:ChampionGothic,sans-serif;font-size:1.6rem;"
        "color:#EF5350;line-height:1;'>" + str(h2h["away_w"]) + "</div>"
        "<div style='font-family:Inter,sans-serif;font-size:0.55rem;color:#333;"
        "letter-spacing:0.1em;text-transform:uppercase;margin-top:2px;'>W</div>"
        "</div>"

        # Away team
        "<div style='font-family:ChampionGothic,sans-serif;font-size:1.1rem;"
        "color:#F0F0F0;text-align:right;'>" + away_code + "</div>"

        "</div>"
        "<div style='font-family:Inter,sans-serif;font-size:0.65rem;color:#333;"
        "margin-top:6px;text-align:center;'>" + str(total) + " matches total</div>",
        unsafe_allow_html=True
    )
else:
    st.markdown("<div style='font-family:Inter,sans-serif;font-size:0.82rem;color:#333;'>No H2H data available</div>", unsafe_allow_html=True)

# ── Section 5: Key players ────────────────────────────────────────────────────
if home_players or away_players:
    st.markdown("<hr style='" + SEP + "'>", unsafe_allow_html=True)
    st.markdown("<span style='" + LABEL + "'>Key Players</span>", unsafe_allow_html=True)

    def render_players(players):
        html = ""
        for p in players:
            num      = p.get("number", "")
            name     = p.get("full_name", "")
            position = p.get("position", "")
            photo    = player_img(p.get("photo_key", ""))
            html += (
                "<div style='display:flex;align-items:center;gap:10px;"
                "background:rgba(255,255,255,0.02);border:1px solid #1e1e1e;"
                "border-radius:8px;padding:8px 10px;margin-bottom:6px;'>"
                + (photo if photo else
                   "<div style='width:44px;height:44px;border-radius:50%;background:#1a1a1a;"
                   "border:1px solid #2a2a2a;flex-shrink:0;display:flex;align-items:center;"
                   "justify-content:center;font-family:ChampionGothic,sans-serif;"
                   "font-size:0.85rem;color:#333;'>" + str(num) + "</div>") +
                "<div>"
                "<div style='font-family:Inter,sans-serif;font-size:0.85rem;"
                "color:#e0e0e0;font-weight:500;'>" + name + "</div>"
                "<div style='font-family:Inter,sans-serif;font-size:0.7rem;"
                "color:#555;margin-top:1px;'>#" + str(num) + " · " + position + "</div>"
                "</div>"
                "</div>"
            )
        return html

    kp1, kp2 = st.columns(2)
    with kp1:
        st.markdown(
            "<div style='font-family:ChampionGothic,sans-serif;font-size:0.9rem;"
            "color:#666;margin-bottom:8px;letter-spacing:0.08em;'>" + home_code + "</div>"
            + (render_players(home_players) if home_players else
               "<div style='color:#333;font-size:0.78rem;font-family:Inter,sans-serif;'>—</div>"),
            unsafe_allow_html=True
        )
    with kp2:
        st.markdown(
            "<div style='font-family:ChampionGothic,sans-serif;font-size:0.9rem;"
            "color:#666;margin-bottom:8px;letter-spacing:0.08em;'>" + away_code + "</div>"
            + (render_players(away_players) if away_players else
               "<div style='color:#333;font-size:0.78rem;font-family:Inter,sans-serif;'>—</div>"),
            unsafe_allow_html=True
        )

st.markdown("</div>", unsafe_allow_html=True)