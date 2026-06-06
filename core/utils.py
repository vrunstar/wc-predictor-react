import json
import base64
from functools import lru_cache
from pathlib import Path

# ── Kit colors ────────────────────────────────────────────────────────────────
_KIT_PATH = Path(__file__).parent / "static" / "kit_colors.json"
_ROOT = Path(__file__).parent

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
    return '<img src="' + src + '" width="' + str(width) + '" style="border-radius:0px;vertical-align:middle;">'


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



def img_b64(path: str, width: int = 28) -> str:
    """Returns an <img> tag with base64 encoded image from any path."""
    try:
        full_path = _ROOT / path
        with open(full_path, "rb") as f:
            raw = base64.b64encode(f.read()).decode()
        ext = Path(path).suffix.lstrip(".")
        if ext == "jpg":
            ext = "jpeg"
        src = f"data:image/{ext};base64,{raw}"
        return f'<img src="{src}" width="{width}" style="vertical-align:middle;">'
    except Exception:
        return ""

def b64(path: str) -> str:
    try:
        full_path = _ROOT / path
        with open(full_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""