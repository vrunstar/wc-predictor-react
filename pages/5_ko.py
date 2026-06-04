import streamlit as st
from db import get_client, fixtures_by_stage, standings_all
from utils import flag_img, img_b64

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
    font-size: 0.9rem; color: #999;
    letter-spacing: 0.12em; text-transform: uppercase;
    margin-bottom: 2rem;
}
.bracket-outer { overflow-x: auto; width: 100%; display: flex; justify-content: center; }
.bracket-wrap {
    display: grid;
    grid-template-columns: repeat(9, 140px);
    gap: 8px;
    min-width: 1100px;
    height: 88vh;
    align-items: stretch;
    margin: 0 auto;
}
.bracket-col {
    display: flex;
    flex-direction: column;
    height: 88vh;
}
.bk-card {
    background: rgba(10,10,10,0.5);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-radius: 6px;
    border: 1px solid #2a2a2a;
    padding: 0.4rem 0.55rem;
    width: 140px;
    box-sizing: border-box;
    flex-shrink: 0;
}
.final-card {
    background: rgba(10,10,10,0.5);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-radius: 6px;
    border: 1px solid #FFD700;
    padding: 0.4rem 0.55rem;
    width: 140px;
    box-sizing: border-box;
    flex-shrink: 0;
}
.bk-team-top {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    padding-bottom: 0.2rem;
    margin-bottom: 0.2rem;
    border-bottom: 1px solid #3a3a3a;
}
.bk-team-bot {
    display: flex;
    align-items: center;
    gap: 0.3rem;
}
.bk-code {
    font-family: 'ChampionGothic', sans-serif;
    font-size: 0.75rem;
    letter-spacing: 0.06em;
    color: #F0F0F0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100px;
}
.bk-score {
    font-family: 'ChampionGothic', sans-serif;
    font-size: 0.75rem;
    color: #00C853;
    margin-left: auto;
}
.center-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 88vh;
    gap: 0.4rem;
    width: 140px;
}
.trophy { font-size: 2rem; }
.final-label {
    font-family: 'ChampionGothic', sans-serif;
    font-size: 0.65rem;
    color: ;#FFD700
    letter-spacing: 0.12em;
}
.third-label {
    font-family: 'ChampionGothic', sans-serif;
    font-size: 0.65rem;
    color: #999;
    letter-spacing: 0.12em;
    margin-top: 1rem;
}

</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="page-title">KNOCKOUTS</div>',
    unsafe_allow_html=True
)

# ── Build slot → team_code lookup from standings ──────────────────────────────
from collections import defaultdict

all_standings = standings_all(supabase)
by_group = defaultdict(list)
for row in all_standings:
    by_group[row["group_name"]].append(row)

slot_to_code = {}
for grp, rows in by_group.items():
    sorted_rows = sorted(rows, key=lambda x: (-x["points"], -x.get("gd", 0), -x.get("gf", 0)))
    for i, row in enumerate(sorted_rows, start=1):
        team = row.get("team", {})
        code = team.get("team_code", "")
        if code:
            slot_to_code[str(i) + grp] = code

def resolve_label(label: str) -> tuple:
    """Returns (display_code, team_code_for_flag).
    If label is a simple slot like '1A', resolve to team code.
    If it's complex like '3ABCDF', leave as-is.
    """
    if not label or label == "TBD":
        return "TBD", ""

    if len(label) == 2 and label[0].isdigit() and label[1].isalpha():
        code = slot_to_code.get(label, "")
        if code:
            return code, code
        return label, ""
    return label, ""

def team_html(display, flag_code, score, is_placeholder):
    flag = flag_img(flag_code, 13) if flag_code else ""
    if is_placeholder:
        span = '<span style="font-family:Inter,sans-serif;font-size:0.7rem;color:#666;letter-spacing:0.02em;">' + display + '</span>'
    else:
        span = '<span class="bk-code">' + display + '</span>'
    sc = '<span class="bk-score">' + score + '</span>' if score else ""
    return flag + span + sc

def bk_card_html(fx, is_final=False):
    home   = fx.get("home") or {}
    away   = fx.get("away") or {}
    res    = fx.get("results", [])
    result = res[0] if isinstance(res, list) and res else {}

    if home.get("team_code"):
        h_display, h_flag_code, h_ph = home["team_code"], home["team_code"], False
    else:
        h_display, h_flag_code = resolve_label(fx.get("home_label", "TBD"))
        h_ph = not bool(h_flag_code)

    if away.get("team_code"):
        a_display, a_flag_code, a_ph = away["team_code"], away["team_code"], False
    else:
        a_display, a_flag_code = resolve_label(fx.get("away_label", "TBD"))
        a_ph = not bool(a_flag_code)

    h_score = str(result.get("home_goals", "")) if result else ""
    a_score = str(result.get("away_goals", "")) if result else ""
    cls     = "final-card" if is_final else "bk-card"

    return (
        '<div class="' + cls + '">'
        '<div class="bk-team-top">' + team_html(h_display, h_flag_code, h_score, h_ph) + '</div>'
        '<div class="bk-team-bot">' + team_html(a_display, a_flag_code, a_score, a_ph) + '</div>'
        '</div>'
    )


def spacer(flex=1):
    return '<div style="flex:' + str(flex) + ';min-height:4px;"></div>'

def build_col(matches):
    html = '<div class="bracket-col" style="display:flex;flex-direction:column;justify-content:space-around;height:88vh;">'
    for fx in matches:
        html += bk_card_html(fx)
    html += '</div>'
    return html

def get_stage(stage):
    return fixtures_by_stage(supabase, stage)

r32 = get_stage("R32")
r16 = get_stage("R16")
qf  = get_stage("QF")
sf  = get_stage("SF")
fn  = get_stage("Final")
trd = get_stage("3RD")

r32_l, r32_r = r32[:8], r32[8:]
r16_l, r16_r = r16[:4], r16[4:]
qf_l,  qf_r  = qf[:2],  qf[2:]
sf_l,  sf_r  = sf[:1],  sf[1:]
final_fx      = fn[0]  if fn  else None
third_fx      = trd[0] if trd else None

center = (
    '<div class="center-col">'
    '<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;padding-bottom:0.4rem;gap:0.3rem;">'
    + img_b64('static/trophy.png', 40) +
    '<div class="final-label"> </div>'
    + (bk_card_html(final_fx, is_final=True) if final_fx else '')
    + '</div>'
    '<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;padding-top:0.4rem;gap:0.3rem;">'
    '<div class="third-label"> </div>'
    + (bk_card_html(third_fx) if third_fx else '')
    + '</div>'
    '</div>'
)

bracket = (
    '<div class="bracket-outer">'
    '<div class="bracket-wrap">'
    + build_col(r32_l)
    + build_col(r16_l)
    + build_col(qf_l)
    + build_col(sf_l)
    + center
    + build_col(sf_r)
    + build_col(qf_r)
    + build_col(r16_r)
    + build_col(r32_r)
    + '</div></div>'
)

st.markdown(
    '<div style="margin-left:calc(-50vw + 50%);margin-right:calc(-50vw + 50%);width:100vw;">'
    + bracket +
    '</div>',
    unsafe_allow_html=True
)