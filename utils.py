import json
import base64
from functools import lru_cache
from pathlib import Path

# ── Kit colors ────────────────────────────────────────────────────────────────
_KIT_PATH = Path(__file__).parent / "static" / "kit_colors.json"

try:
    with open(_KIT_PATH) as f:
        KIT_COLORS: dict = json.load(f)
except Exception:
    KIT_COLORS = {}


def kit_color(team_code: str, role: str) -> str:
    entry = KIT_COLORS.get(team_code, {})
    return entry.get(role, "#2a2a2a")


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "rgba(" + str(r) + "," + str(g) + "," + str(b) + "," + str(alpha) + ")"


def render_form(form: str) -> str:
    if not form:
        return "<span style='color:#444;'>—</span>"
    color_map = {"W": "#00C853", "D": "#FFC107", "L": "#EF5350"}
    out = ""
    for ch in form.upper():
        c = color_map.get(ch, "#666")
        out += "<span style='color:" + c + ";font-weight:700;font-size:0.72rem;margin:0 1px;'>" + ch + "</span>"
    return out


def prob_bar_html(h_prob: float, d_prob: float, a_prob: float,
                  home_code: str, away_code: str, height: int = 4) -> str:
    hc = kit_color(home_code, "home")
    ac = kit_color(away_code, "away")
    return (
        '<div style="display:flex;height:' + str(height) + 'px;border-radius:' + str(height//2) + 'px;overflow:hidden;margin-top:0.6rem;">'
        '<div style="width:' + str(int(h_prob*100)) + '%;background:' + hc + ';opacity:0.9;"></div>'
        '<div style="width:' + str(int(d_prob*100)) + '%;background:#444;"></div>'
        '<div style="width:' + str(int(a_prob*100)) + '%;background:' + ac + ';opacity:0.9;"></div>'
        '</div>'
    )


def form_html(form: str, align: str = "left") -> str:
    """Renders form string like WWDLW as colored letters. W=green D=amber L=red"""
    if not form:
        return "<span style='color:#444;font-size:0.75rem;'>—</span>"
    color_map = {"W": "#0F8633", "D": "#F1DB98", "L": "#CA2220"}
    letters = []
    for ch in form:
        color = color_map.get(ch, "#555")
        letters.append(
            "<span style='color:" + color + ";font-size:0.78rem;"
            "font-weight:700;letter-spacing:0.04em;margin:0 1px;'>" + ch + "</span>"
        )
    return "<div style='text-align:" + align + ";'>" + "".join(letters) + "</div>"



@lru_cache(maxsize=64)
def flag_b64(team_code: str) -> str:
    """Returns base64 encoded flag image as inline src."""
    try:
        path = Path(__file__).parent / "static" / "flags" / f"{team_code}.png"
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{b64}"
    except Exception:
        return ""

def flag_img(team_code: str, width: int = 28) -> str:
    """Returns an <img> tag with base64 encoded flag."""
    src = flag_b64(team_code)
    if not src:
        return ""
    return '<img src="' + src + '" width="' + str(width) + '" style="border-radius:2px;vertical-align:middle;">'


def format_kickoff(kickoff_ist) -> str:
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(kickoff_ist)).strftime("%H:%M")
    except Exception:
        return str(kickoff_ist)[:5] if kickoff_ist else "TBD"


def stage_label(stage: str, group: str = "", rank: str = "") -> str:
    if stage == "group" and group:
        return "Group " + group + (str(rank) if rank else "")
    return stage.replace("_", " ").title()

# ── Detail card renderer ──────────────────────────────────────────────────────
def render_detail_card(fx: dict, supabase, mode: str = "fixture") -> None:
    """
    Renders a match detail card inside an st.dialog.
    mode: 'fixture' | 'prediction' | 'result'
    """
    import streamlit as st
    import json
    import base64
    import re
    from db import team_by_id, pred_by_match, get_team_form

    home      = fx.get("home") or {}
    away      = fx.get("away") or {}
    home_code = home.get("team_code", "???")
    away_code = away.get("team_code", "???")
    home_name = home.get("name", home_code)
    away_name = away.get("name", away_code)
    home_id   = home.get("team_id")
    away_id   = away.get("team_id")
    group     = fx.get("group_name", "")
    stage     = fx.get("stage", "group")
    venue     = fx.get("venue", fx.get("city", ""))
    kickoff   = fx.get("kickoff_ist", "")
    mid       = fx.get("match_id", "")
    stage_str = ("Group " + group) if stage == "group" and group else stage.replace("_", " ").title()
    ko        = format_kickoff(kickoff)

    # ── Load H2H ──────────────────────────────────────────────────────────────
    try:
        with open("static/h2h.json") as f:
            H2H = json.load(f)
    except Exception:
        H2H = {}

    # ── Form ──────────────────────────────────────────────────────────────────
    def get_form(team_id):
        if not team_id: return ""
        raw = get_team_form(supabase, team_id)
        if not raw: return ""
        color_map = {"W": "#FFD700", "D": "#888", "L": "#EF5350"}
        out = ""
        for ch in raw.upper():
            c = color_map.get(ch, "#666")
            out += f"<span style='color:{c};font-weight:700;font-size:0.72rem;margin:0 1px;'>{ch}</span>"
        return out

    home_form = get_form(home_id)
    away_form = get_form(away_id)

    # ── Rank ──────────────────────────────────────────────────────────────────
    try:
        from db import get_team_rank
        home_rank = get_team_rank(supabase, home_id) if home_id else ""
        away_rank = get_team_rank(supabase, away_id) if away_id else ""
    except Exception:
        home_rank = away_rank = ""

    # ── Header ────────────────────────────────────────────────────────────────
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"<div style='font-family:Inter,sans-serif;font-size:0.7rem;color:#555;letter-spacing:0.12em;text-transform:uppercase;'>{stage_str} · Match {mid}</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='font-family:Inter,sans-serif;font-size:0.7rem;color:#555;text-align:right;'>{ko} IST</div>", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#1e1e1e;margin:0.6rem 0;'>", unsafe_allow_html=True)

    # ── Teams row ─────────────────────────────────────────────────────────────
    col_h, col_center, col_a = st.columns([3, 2, 3])

    with col_h:
        st.markdown(
            flag_img(home_code, 36) +
            f"<div style='font-family:ChampionGothic,sans-serif;font-size:1.8rem;color:#fff;letter-spacing:0.06em;margin-top:4px;line-height:1;'>{home_name}</div>"
            f"<div style='font-family:Inter,sans-serif;font-size:0.72rem;color:#555;margin-top:2px;'>{home_code}" + (f" · {home_rank}" if home_rank else "") + "</div>"
            f"<div style='margin-top:5px;'>{home_form}</div>",
            unsafe_allow_html=True
        )

    with col_center:
        if mode == "fixture":
            st.markdown(
                f"<div style='text-align:center;padding-top:0.5rem;'>"
                f"<div style='font-family:ChampionGothic,sans-serif;font-size:2.2rem;color:#fff;letter-spacing:0.1em;line-height:1;'>{ko}</div>"
                f"<div style='font-family:Inter,sans-serif;font-size:0.6rem;color:#444;letter-spacing:0.14em;text-transform:uppercase;margin-top:3px;'>IST</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        elif mode == "prediction":
            pred = pred_by_match(supabase, mid) or {}
            h_goals = pred.get("pred_home_goals", "?")
            a_goals = pred.get("pred_away_goals", "?")
            conf    = int(pred.get("model_confidence", 0) * 100)
            h_prob  = pred.get("home_win_prob", 0)
            d_prob  = pred.get("draw_prob", 0)
            a_prob  = pred.get("away_win_prob", 0)
            hc      = kit_color(home_code, "home")
            ac      = kit_color(away_code, "away")
            st.markdown(
                f"<div style='text-align:center;padding-top:0.3rem;'>"
                f"<div style='font-family:ChampionGothic,sans-serif;font-size:2.2rem;color:#fff;letter-spacing:0.1em;line-height:1;'>{h_goals} – {a_goals}</div>"
                f"<div style='font-family:Inter,sans-serif;font-size:0.7rem;color:#555;margin-top:3px;'>{conf}% confidence</div>"
                f"<div style='display:flex;height:4px;border-radius:2px;overflow:hidden;margin-top:8px;'>"
                f"<div style='width:{int(h_prob*100)}%;background:{hc};opacity:0.9;'></div>"
                f"<div style='width:{int(d_prob*100)}%;background:#444;'></div>"
                f"<div style='width:{int(a_prob*100)}%;background:{ac};opacity:0.9;'></div>"
                f"</div>"
                f"<div style='display:flex;justify-content:space-between;font-family:Inter,sans-serif;font-size:0.65rem;color:#444;margin-top:3px;'>"
                f"<span>{int(h_prob*100)}%</span><span>D {int(d_prob*100)}%</span><span>{int(a_prob*100)}%</span>"
                f"</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        elif mode == "result":
            res_raw = fx.get("results") or {}
            res     = (res_raw[0] if isinstance(res_raw, list) and res_raw else res_raw) or {}
            pred    = pred_by_match(supabase, mid) or {}
            actual_h = res.get("home_goals", "?")
            actual_a = res.get("away_goals", "?")
            pred_h   = pred.get("pred_home_goals", "?")
            pred_a   = pred.get("pred_away_goals", "?")
            st.markdown(
                f"<div style='text-align:center;padding-top:0.3rem;'>"
                f"<div style='font-family:ChampionGothic,sans-serif;font-size:2.2rem;color:#fff;letter-spacing:0.1em;line-height:1;'>{actual_h} – {actual_a}</div>"
                f"<div style='font-family:Inter,sans-serif;font-size:0.85rem;color:#444;margin-top:4px;'>({pred_h}–{pred_a}) pred</div>"
                f"</div>",
                unsafe_allow_html=True
            )

    with col_a:
        st.markdown(
            flag_img(away_code, 36) +
            f"<div style='font-family:ChampionGothic,sans-serif;font-size:1.8rem;color:#fff;letter-spacing:0.06em;margin-top:4px;line-height:1;text-align:right;'>{away_name}</div>"
            f"<div style='font-family:Inter,sans-serif;font-size:0.72rem;color:#555;margin-top:2px;text-align:right;'>{away_code}" + (f" · {away_rank}" if away_rank else "") + "</div>"
            f"<div style='margin-top:5px;text-align:right;'>{away_form}</div>",
            unsafe_allow_html=True
        )

    st.markdown("<hr style='border-color:#1e1e1e;margin:0.75rem 0;'>", unsafe_allow_html=True)

    # ── Venue ─────────────────────────────────────────────────────────────────
    stadium_key = re.sub(r'[^a-z]', '', (venue or '').lower())
    try:
        with open(f'static/stadiums/{stadium_key}.png', 'rb') as f:
            _sb64 = base64.b64encode(f.read()).decode()
        stadium_bg = f"url('data:image/png;base64,{_sb64}')"
    except Exception:
        stadium_bg = "none"

    st.markdown(
        f"<div style='position:relative;border:1px solid #1e1e1e;border-radius:8px;overflow:hidden;height:72px;margin-bottom:1rem;'>"
        f"<div style='position:absolute;inset:0;background-image:{stadium_bg};background-size:cover;background-position:center;'></div>"
        f"<div style='position:absolute;inset:0;background:linear-gradient(to right,rgba(0,0,0,0.95) 40%,rgba(0,0,0,0.2) 100%);'></div>"
        f"<div style='position:relative;z-index:1;padding:0.7rem 1rem;'>"
        f"<div style='font-family:Inter,sans-serif;font-size:0.6rem;color:#444;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:3px;'>Venue</div>"
        f"<div style='font-family:ChampionGothic,sans-serif;font-size:1rem;color:#e0e0e0;letter-spacing:0.06em;'>{venue or 'TBD'}</div>"
        f"</div></div>",
        unsafe_allow_html=True
    )

    # ── H2H ───────────────────────────────────────────────────────────────────
    h2h_rec = H2H.get(home_code, {}).get(away_code)
    h2h_rev = H2H.get(away_code, {}).get(home_code)

    st.markdown("<div style='font-family:Inter,sans-serif;font-size:0.65rem;color:#444;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:8px;'>Head to Head · Since 2000</div>", unsafe_allow_html=True)

    if h2h_rec or h2h_rev:
        def h2h_row(code1, code2, rec):
            return (
                f"<div style='display:grid;grid-template-columns:50px 1fr 50px 1fr 50px;"
                f"align-items:center;gap:6px;margin-bottom:5px;padding:0.5rem 0.75rem;"
                f"background:rgba(10,10,10,0.65);border:1px solid #1e1e1e;border-radius:6px;'>"
                f"<span style='font-family:ChampionGothic,sans-serif;font-size:0.85rem;color:#F0F0F0;'>{code1}</span>"
                f"<span style='text-align:center;color:#FFD700;font-weight:700;font-size:1rem;'>{rec['W']}</span>"
                f"<span style='text-align:center;color:#888;font-weight:700;font-size:1rem;'>{rec['D']}</span>"
                f"<span style='text-align:center;color:#EF5350;font-weight:700;font-size:1rem;'>{rec['L']}</span>"
                f"<span style='text-align:right;font-family:ChampionGothic,sans-serif;font-size:0.85rem;color:#F0F0F0;'>{code2}</span>"
                f"</div>"
            )
        st.markdown(
            "<div style='font-family:Inter,sans-serif;display:grid;grid-template-columns:50px 1fr 50px 1fr 50px;"
            "gap:6px;font-size:0.6rem;color:#444;letter-spacing:0.1em;text-transform:uppercase;"
            "padding:0 0.75rem;margin-bottom:4px;'>"
            "<span></span><span style='text-align:center;'>W</span>"
            "<span style='text-align:center;'>D</span><span style='text-align:center;'>L</span><span></span>"
            "</div>",
            unsafe_allow_html=True
        )
        if h2h_rec:
            st.markdown(h2h_row(home_code, away_code, h2h_rec), unsafe_allow_html=True)
        if h2h_rev:
            st.markdown(h2h_row(away_code, home_code, h2h_rev), unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-family:Inter,sans-serif;font-size:0.82rem;color:#333;'>No H2H data available</div>", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#1e1e1e;margin:0.75rem 0;'>", unsafe_allow_html=True)

    # ── Key players ───────────────────────────────────────────────────────────
    home_data = team_by_id(supabase, home_id) if home_id else {}
    away_data = team_by_id(supabase, away_id) if away_id else {}

    def parse_players(raw):
        if not raw: return []
        return [p.strip() for p in raw.split(",") if p.strip()]

    def player_card(p):
        parts = p.split(":", 1)
        if len(parts) == 2:
            num, name = parts[0].strip(), parts[1].strip()
            return (
                f"<div style='display:flex;align-items:center;gap:8px;"
                f"background:rgba(10,10,10,0.65);border:1px solid #1e1e1e;"
                f"border-radius:6px;padding:6px 10px;margin-bottom:5px;'>"
                f"<span style='font-family:ChampionGothic,sans-serif;font-size:0.9rem;"
                f"color:#FFD700;min-width:28px;'>#{num}</span>"
                f"<span style='font-family:Inter,sans-serif;font-size:0.82rem;color:#e0e0e0;'>{name}</span>"
                f"</div>"
            )
        return f"<div style='font-family:Inter,sans-serif;font-size:0.82rem;color:#e0e0e0;background:rgba(10,10,10,0.65);border:1px solid #1e1e1e;border-radius:6px;padding:6px 10px;margin-bottom:5px;'>{p}</div>"

    home_players = parse_players(home_data.get("key_players", ""))
    away_players = parse_players(away_data.get("key_players", ""))

    if home_players or away_players:
        st.markdown("<div style='font-family:Inter,sans-serif;font-size:0.65rem;color:#444;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:8px;'>Key Players</div>", unsafe_allow_html=True)
        kp1, kp2 = st.columns(2)
        with kp1:
            st.markdown(f"<div style='font-family:ChampionGothic,sans-serif;font-size:0.85rem;color:#888;margin-bottom:6px;letter-spacing:0.08em;'>{home_code}</div>", unsafe_allow_html=True)
            st.markdown("".join(player_card(p) for p in home_players) if home_players else "<div style='color:#333;font-size:0.78rem;'>—</div>", unsafe_allow_html=True)
        with kp2:
            st.markdown(f"<div style='font-family:ChampionGothic,sans-serif;font-size:0.85rem;color:#888;margin-bottom:6px;letter-spacing:0.08em;'>{away_code}</div>", unsafe_allow_html=True)
            st.markdown("".join(player_card(p) for p in away_players) if away_players else "<div style='color:#333;font-size:0.78rem;'>—</div>", unsafe_allow_html=True)

# ── Detail card shared renderer ───────────────────────────────────────────────
import json as _json
import base64 as _base64
import re as _re

def _load_h2h() -> dict:
    try:
        with open(Path(__file__).parent / "static" / "h2h.json") as f:
            return _json.load(f)
    except Exception:
        return {}

def _stadium_bg(venue: str) -> str:
    key = _re.sub(r'[^a-z]', '', (venue or '').lower())
    try:
        with open(Path(__file__).parent / "static" / "stadiums" / f"{key}.png", "rb") as f:
            b64 = _base64.b64encode(f.read()).decode()
        return f"url('data:image/png;base64,{b64}')"
    except Exception:
        return "none"

def _parse_players(raw: str) -> list:
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]

def _player_html(p: str) -> str:
    parts = p.split(":", 1)
    if len(parts) == 2:
        num, name = parts[0].strip(), parts[1].strip()
        return (
            "<div style='display:flex;align-items:center;gap:8px;"
            "background:rgba(10,10,10,0.65);border:1px solid #1e1e1e;"
            "border-radius:6px;padding:6px 10px;margin-bottom:5px;'>"
            "<span style='font-family:ChampionGothic,sans-serif;font-size:0.9rem;"
            "color:#FFD700;min-width:28px;'>#" + num + "</span>"
            "<span style='font-family:Inter,sans-serif;font-size:0.82rem;color:#e0e0e0;'>" + name + "</span>"
            "</div>"
        )
    return (
        "<div style='font-family:Inter,sans-serif;font-size:0.82rem;color:#e0e0e0;"
        "background:rgba(10,10,10,0.65);border:1px solid #1e1e1e;border-radius:6px;"
        "padding:6px 10px;margin-bottom:5px;'>" + p + "</div>"
    )

def render_detail_card(fx: dict, supabase, mode: str = "fixture", pred: dict = None, result: dict = None):
    """
    Renders the shared detail card inside an st.dialog.
    mode: 'fixture' | 'prediction' | 'result'
    pred: prediction dict (for prediction/result modes)
    result: result dict (for result mode)
    """
    import streamlit as st
    from db import team_by_id, get_team_form, get_team_rank

    home      = fx.get("home") or {}
    away      = fx.get("away") or {}
    home_code = home.get("team_code", "???")
    away_code = away.get("team_code", "???")
    home_name = home.get("name", home_code)
    away_name = away.get("name", away_code)
    home_id   = home.get("team_id")
    away_id   = away.get("team_id")
    group     = fx.get("group_name", "")
    stage     = fx.get("stage", "group")
    venue     = fx.get("venue", fx.get("city", ""))
    kickoff   = fx.get("kickoff_ist", "")
    mid       = fx.get("match_id", "")
    ko        = format_kickoff(kickoff)
    stage_str = ("Group " + group) if stage == "group" and group else stage.replace("_", " ").title()
    home_rank = get_team_rank(supabase, home_id) if home_id else "—"
    away_rank = get_team_rank(supabase, away_id) if away_id else "—"

    # Form
    def _form_html(form, align="left"):
        if not form:
            return "<span style='color:#444;font-family:Inter,sans-serif;font-size:0.72rem;'>No recent data</span>"
        color_map = {"W": "#FFD700", "D": "#888", "L": "#EF5350"}
        out = ""
        for ch in form.upper():
            c = color_map.get(ch, "#666")
            out += "<span style='color:" + c + ";font-weight:700;font-size:0.75rem;margin:0 2px;font-family:Inter,sans-serif;'>" + ch + "</span>"
        return "<div style='text-align:" + align + ";margin-top:4px;'>" + out + "</div>"

    home_form = get_team_form(supabase, home_id) if home_id else ""
    away_form = get_team_form(supabase, away_id) if away_id else ""

    # ── Header ────────────────────────────────────────────────────────────────
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"<div style='font-family:Inter,sans-serif;font-size:0.7rem;color:#555;letter-spacing:0.12em;text-transform:uppercase;'>{stage_str} · Match {mid}</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='font-family:Inter,sans-serif;font-size:0.7rem;color:#555;text-align:right;'>{ko} IST</div>", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#1e1e1e;margin:0.6rem 0;'>", unsafe_allow_html=True)

    # ── Teams row ─────────────────────────────────────────────────────────────
    col_h, col_mid, col_a = st.columns([2, 1, 2])

    with col_h:
        st.markdown(
            flag_img(home_code, 36) +
            "<div style='font-family:ChampionGothic,sans-serif;font-size:1.8rem;color:#fff;letter-spacing:0.06em;margin-top:4px;line-height:1;'>" + home_name + "</div>"
            "<div style='font-family:Inter,sans-serif;font-size:0.72rem;color:#555;margin-top:2px;'>" + home_code + " · " + home_rank + "</div>" +
            _form_html(home_form, "left"),
            unsafe_allow_html=True
        )

    with col_mid:
        if mode == "fixture":
            center_html = (
                "<div style='text-align:center;padding-top:0.75rem;'>"
                "<div style='font-family:ChampionGothic,sans-serif;font-size:1.8rem;color:#fff;letter-spacing:0.1em;'>" + ko + "</div>"
                "<div style='font-family:Inter,sans-serif;font-size:0.6rem;color:#444;letter-spacing:0.12em;text-transform:uppercase;margin-top:2px;'>IST</div>"
                "</div>"
            )
        elif mode == "prediction" and pred:
            h_g = pred.get("pred_home_goals", "?")
            a_g = pred.get("pred_away_goals", "?")
            conf = int(pred.get("model_confidence", 0) * 100)
            center_html = (
                "<div style='text-align:center;padding-top:0.5rem;'>"
                "<div style='font-family:ChampionGothic,sans-serif;font-size:1.8rem;color:#fff;letter-spacing:0.1em;'>" + str(h_g) + " – " + str(a_g) + "</div>"
                "<div style='font-family:Inter,sans-serif;font-size:0.7rem;color:#555;margin-top:3px;'>" + str(conf) + "% confidence</div>"
                "</div>"
            )
        elif mode == "result" and result:
            h_g = result.get("home_goals", "?")
            a_g = result.get("away_goals", "?")
            p_h = pred.get("pred_home_goals", "?") if pred else "?"
            p_a = pred.get("pred_away_goals", "?") if pred else "?"
            center_html = (
                "<div style='text-align:center;padding-top:0.5rem;'>"
                "<div style='font-family:ChampionGothic,sans-serif;font-size:1.8rem;color:#fff;letter-spacing:0.1em;'>" + str(h_g) + " – " + str(a_g) + "</div>"
                "<div style='font-family:Inter,sans-serif;font-size:0.8rem;color:#444;margin-top:3px;'>(" + str(p_h) + "–" + str(p_a) + " pred)</div>"
                "</div>"
            )
        else:
            center_html = "<div style='text-align:center;padding-top:0.75rem;font-family:ChampionGothic,sans-serif;font-size:1.2rem;color:#333;'>VS</div>"
        st.markdown(center_html, unsafe_allow_html=True)

    with col_a:
        st.markdown(
            flag_img(away_code, 36) +
            "<div style='font-family:ChampionGothic,sans-serif;font-size:1.8rem;color:#fff;letter-spacing:0.06em;margin-top:4px;line-height:1;text-align:right;'>" + away_name + "</div>"
            "<div style='font-family:Inter,sans-serif;font-size:0.72rem;color:#555;margin-top:2px;text-align:right;'>" + away_code + " · " + away_rank + "</div>" +
            _form_html(away_form, "right"),
            unsafe_allow_html=True
        )

    # ── Prob bar (predictions only) ───────────────────────────────────────────
    if mode == "prediction" and pred:
        h_prob = pred.get("home_win_prob", 0)
        d_prob = pred.get("draw_prob", 0)
        a_prob = pred.get("away_win_prob", 0)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-family:Inter,sans-serif;font-size:0.65rem;color:#444;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:6px;'>Win Probability</div>"
            "<div style='display:flex;justify-content:space-between;font-family:Inter,sans-serif;font-size:0.7rem;color:#555;margin-bottom:4px;'>"
            "<span>" + home_code + " " + str(int(h_prob*100)) + "%</span>"
            "<span>Draw " + str(int(d_prob*100)) + "%</span>"
            "<span>" + str(int(a_prob*100)) + "% " + away_code + "</span>"
            "</div>"
            "<div style='display:flex;height:6px;border-radius:3px;overflow:hidden;'>"
            "<div style='width:" + str(int(h_prob*100)) + "%;background:#FFD700;opacity:0.9;'></div>"
            "<div style='width:" + str(int(d_prob*100)) + "%;background:#444;'></div>"
            "<div style='width:" + str(int(a_prob*100)) + "%;background:#888;opacity:0.9;'></div>"
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("<hr style='border-color:#1e1e1e;margin:0.75rem 0;'>", unsafe_allow_html=True)

    # ── Venue ─────────────────────────────────────────────────────────────────
    stadium_bg = _stadium_bg(venue)
    st.markdown(
        "<div style='position:relative;border:1px solid #1e1e1e;border-radius:8px;overflow:hidden;height:72px;margin-bottom:1rem;'>"
        "<div style='position:absolute;inset:0;background-image:" + stadium_bg + ";background-size:cover;background-position:center;'></div>"
        "<div style='position:absolute;inset:0;background:linear-gradient(to right,rgba(0,0,0,0.95) 40%,rgba(0,0,0,0.2) 100%);'></div>"
        "<div style='position:relative;z-index:1;padding:0.7rem 1rem;'>"
        "<div style='font-family:Inter,sans-serif;font-size:0.6rem;color:#444;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:3px;'>Venue</div>"
        "<div style='font-family:ChampionGothic,sans-serif;font-size:1rem;color:#e0e0e0;letter-spacing:0.06em;'>" + (venue or "TBD") + "</div>"
        "</div></div>",
        unsafe_allow_html=True
    )

    # ── H2H ───────────────────────────────────────────────────────────────────
    h2h_data = _load_h2h()
    h2h_rec = h2h_data.get(home_code, {}).get(away_code)
    h2h_rev = h2h_data.get(away_code, {}).get(home_code)

    st.markdown("<div style='font-family:Inter,sans-serif;font-size:0.65rem;color:#444;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:8px;'>Head to Head · Since 2000</div>", unsafe_allow_html=True)

    if h2h_rec or h2h_rev:
        def h2h_row(c1, c2, rec):
            return (
                "<div style='display:grid;grid-template-columns:1fr 40px 40px 40px 1fr;"
                "align-items:center;gap:6px;margin-bottom:5px;padding:0.5rem 0.75rem;"
                "background:rgba(10,10,10,0.65);border:1px solid #1e1e1e;border-radius:6px;'>"
                "<span style='font-family:ChampionGothic,sans-serif;font-size:0.85rem;color:#F0F0F0;'>" + c1 + "</span>"
                "<span style='text-align:center;color:#FFD700;font-weight:700;font-size:1rem;font-family:Inter,sans-serif;'>" + str(rec["W"]) + "</span>"
                "<span style='text-align:center;color:#888;font-weight:700;font-size:1rem;font-family:Inter,sans-serif;'>" + str(rec["D"]) + "</span>"
                "<span style='text-align:center;color:#EF5350;font-weight:700;font-size:1rem;font-family:Inter,sans-serif;'>" + str(rec["L"]) + "</span>"
                "<span style='text-align:right;font-family:ChampionGothic,sans-serif;font-size:0.85rem;color:#F0F0F0;'>" + c2 + "</span>"
                "</div>"
            )
        st.markdown(
            "<div style='display:grid;grid-template-columns:1fr 40px 40px 40px 1fr;gap:6px;"
            "font-family:Inter,sans-serif;font-size:0.6rem;color:#444;letter-spacing:0.1em;"
            "text-transform:uppercase;padding:0 0.75rem;margin-bottom:4px;'>"
            "<span></span><span style='text-align:center;'>W</span>"
            "<span style='text-align:center;'>D</span><span style='text-align:center;'>L</span><span></span>"
            "</div>",
            unsafe_allow_html=True
        )
        if h2h_rec:
            st.markdown(h2h_row(home_code, away_code, h2h_rec), unsafe_allow_html=True)
        if h2h_rev:
            st.markdown(h2h_row(away_code, home_code, h2h_rev), unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-family:Inter,sans-serif;font-size:0.82rem;color:#333;'>No H2H data available</div>", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#1e1e1e;margin:0.75rem 0;'>", unsafe_allow_html=True)

    # ── Key players ───────────────────────────────────────────────────────────
    home_data = team_by_id(supabase, home_id) if home_id else {}
    away_data = team_by_id(supabase, away_id) if away_id else {}
    home_players = _parse_players(home_data.get("key_players", ""))
    away_players = _parse_players(away_data.get("key_players", ""))

    if home_players or away_players:
        st.markdown("<div style='font-family:Inter,sans-serif;font-size:0.65rem;color:#444;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:8px;'>Key Players</div>", unsafe_allow_html=True)
        kp1, kp2 = st.columns(2)
        with kp1:
            st.markdown("<div style='font-family:ChampionGothic,sans-serif;font-size:0.85rem;color:#888;margin-bottom:6px;letter-spacing:0.08em;'>" + home_code + "</div>", unsafe_allow_html=True)
            st.markdown("".join(_player_html(p) for p in home_players) if home_players else "<div style='color:#333;font-size:0.78rem;font-family:Inter,sans-serif;'>—</div>", unsafe_allow_html=True)
        with kp2:
            st.markdown("<div style='font-family:ChampionGothic,sans-serif;font-size:0.85rem;color:#888;margin-bottom:6px;letter-spacing:0.08em;'>" + away_code + "</div>", unsafe_allow_html=True)
            st.markdown("".join(_player_html(p) for p in away_players) if away_players else "<div style='color:#333;font-size:0.78rem;font-family:Inter,sans-serif;'>—</div>", unsafe_allow_html=True)