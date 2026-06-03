import os
from datetime import datetime, date
import pytz
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

# Try multiple locations to find .env
for _env_path in [
    Path(__file__).parent / ".env",
    Path.cwd() / ".env",
]:
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path, override=True)
        break

def get_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise Exception("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment")
    return create_client(url, key)

def get_ist() -> date:
    return datetime.now(pytz.timezone("Asia/Kolkata")).date()

# ---------------------------------------------------------------------
# TEAMS
# ---------------------------------------------------------------------

def teams_all(supabase: Client) -> list[dict]:
    res = supabase.table("teams").select("*").execute()
    return res.data

def team_by_id(supabase: Client, team_id: int) -> dict:
    res = supabase.table("teams").select("*").eq("team_id", team_id).single().execute()
    return res.data

# ---------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------

def fixtures_today(supabase: Client) -> list[dict]:
    today = str(get_ist())
    res = (supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*), results(*)")
           .eq("matchday_ist", today)
           .order("kickoff_ist")
           .execute())
    return res.data

def fixtures_group(supabase: Client) -> list[dict]:
    res = (supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*)")
           .eq("stage", "group")
           .order("kickoff_ist")
           .execute())
    return res.data

def fixtures_by_stage(supabase: Client, stage: str) -> list[dict]:
    res = (supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*), results(*)")
           .eq("stage", stage)
           .order("kickoff_ist")
           .execute())
    return res.data

def fixtures_upcoming(supabase: Client) -> list[dict]:
    today = str(get_ist())
    res = (supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*)")
           .gte("matchday_ist", today)
           .neq("status", "completed")
           .order("kickoff_ist")
           .execute())
    return res.data

def fixtures_by_id(supabase: Client, match_id: int) -> dict:
    res = (supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*)")
           .eq("match_id", match_id)
           .single()
           .execute())
    return res.data

# ---------------------------------------------------------------------
# PREDICTIONS
# ---------------------------------------------------------------------

def pred_by_match(supabase: Client, match_id: int) -> dict | None:
    res = (supabase.table("prediction")
           .select("*")
           .eq("match_id", match_id)
           .execute())
    return res.data[0] if res.data else None

def pred_today(supabase: Client) -> list[dict]:
    today = str(get_ist())
    res = (supabase.table("prediction")
           .select("*, fixture:fixtures!match_id(*, home:teams!home_id(*), away:teams!away_id(*))")
           .eq("fixture.matchday_ist", today)
           .order("generated_at", desc=True)
           .execute())
    return [r for r in res.data if r.get("fixture")]

def pred_all(supabase: Client) -> list[dict]:
    res = (supabase.table("prediction")
           .select("*, fixture:fixtures!match_id(*, home:teams!home_id(*), away:teams!away_id(*), results(*))")
           .order("generated_at", desc=True)
           .execute())
    return res.data

def pred_updated(supabase: Client, pred: dict) -> list[dict]:
    res = (supabase.table("prediction")
           .upsert(pred, on_conflict="match_id")
           .execute())
    return res.data

# ---------------------------------------------------------------------
# RESULTS
# ---------------------------------------------------------------------

def res_by_match(supabase: Client, match_id: int) -> dict | None:
    res = (supabase.table("results")
           .select("*")
           .eq("match_id", match_id)
           .execute())
    return res.data[0] if res.data else None

def res_all(supabase: Client) -> list[dict]:
    res = (supabase.table("results")
           .select("*, fixture:fixtures!match_id(*, home:teams!home_id(*), away:teams!away_id(*))")
           .order("updated_at", desc=True)
           .execute())
    return res.data

def res_upsert(supabase: Client, result: dict) -> dict:
    res = (supabase.table("results")
           .upsert(result, on_conflict="match_id")
           .execute())
    return res.data

# ---------------------------------------------------------------------
# STANDINGS
# ---------------------------------------------------------------------

def standings_by_group(supabase: Client, group_name: str) -> list[dict]:
    res = (supabase.table("standings")
           .select("*, team:teams!team_id(name, team_code, fifa_rank)")
           .eq("group_name", group_name)
           .order("points, gd", desc=True)
           .execute())
    return res.data

def standings_all(supabase: Client) -> list[dict]:
    res = (supabase.table("standings")
           .select("*, team:teams!team_id(name, team_code, fifa_rank)")
           .order("group_name, points, gd", desc=True)
           .execute())
    return res.data

def standings_update(supabase: Client, team_id: int, updates: dict) -> dict:
    res = (supabase.table("standings")
           .update(updates)
           .eq("team_id", team_id)
           .execute())
    return res.data

# ---------------------------------------------------------------------
# UPDATE AFTER RESULT
# ---------------------------------------------------------------------

def update_after_res(supabase: Client, match_id: int, home_goals: int, away_goals: int) -> None:
    fixture = fixtures_by_id(supabase, match_id)
    home = fixture["home"]
    away = fixture["away"]

    if home_goals > away_goals:
        outcome = "H"
        home_actual, away_actual = 1.0, 0.0
    elif home_goals == away_goals:
        outcome = "D"
        home_actual, away_actual = 0.5, 0.5
    else:
        outcome = "A"
        home_actual, away_actual = 0.0, 1.0

    k = 40
    home_elo = home["elo_rating"]
    away_elo = away["elo_rating"]

    expected_home = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
    expected_away = 1 - expected_home

    new_home_elo = round(home_elo + k * (home_actual - expected_home), 2)
    new_away_elo = round(away_elo + k * (away_actual - expected_away), 2)

    supabase.table("teams").update({"elo_rating": new_home_elo}).eq("team_id", home["team_id"]).execute()
    supabase.table("teams").update({"elo_rating": new_away_elo}).eq("team_id", away["team_id"]).execute()

    def get_standing(team_id):
        return supabase.table("standings").select("*").eq("team_id", team_id).single().execute().data

    home_standing = get_standing(home["team_id"])
    away_standing = get_standing(away["team_id"])

    home_updates = {
        "played":  home_standing["played"] + 1,
        "won":     home_standing["won"]    + (1 if outcome == "H" else 0),
        "drawn":   home_standing["drawn"]  + (1 if outcome == "D" else 0),
        "lost":    home_standing["lost"]   + (1 if outcome == "A" else 0),
        "gf":      home_standing["gf"]     + home_goals,
        "ga":      home_standing["ga"]     + away_goals,
        "gd":      home_standing.get("gd", 0) + (home_goals - away_goals),
        "points":  home_standing["points"] + (3 if outcome == "H" else 1 if outcome == "D" else 0),
    }
    away_updates = {
        "played":  away_standing["played"] + 1,
        "won":     away_standing["won"]    + (1 if outcome == "A" else 0),
        "drawn":   away_standing["drawn"]  + (1 if outcome == "D" else 0),
        "lost":    away_standing["lost"]   + (1 if outcome == "H" else 0),
        "gf":      away_standing["gf"]     + away_goals,
        "ga":      away_standing["ga"]     + home_goals,
        "gd":      away_standing.get("gd", 0) + (away_goals - home_goals),
        "points":  away_standing["points"] + (3 if outcome == "A" else 1 if outcome == "D" else 0),
    }

    supabase.table("standings").update(home_updates).eq("team_id", home["team_id"]).execute()
    supabase.table("standings").update(away_updates).eq("team_id", away["team_id"]).execute()

    res_upsert(supabase, {
        "match_id":   match_id,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "outcome":    outcome,
    })

    supabase.table("fixtures").update({"status": "completed"}).eq("match_id", match_id).execute()

    print(f"✓ Match {match_id} — {home['name']} {home_goals}-{away_goals} {away['name']}")
    print(f"  ELO: {home['name']} {home_elo}→{new_home_elo}, {away['name']} {away_elo}→{new_away_elo}")

# ---------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------

def login(supabase: Client, email: str, passwd: str):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": passwd})
        return res.user
    except Exception:
        return None

def logout(supabase: Client) -> None:
    supabase.auth.sign_out()

# ---------------------------------------------------------------------
# FORM
# ---------------------------------------------------------------------

def get_team_form(supabase: Client, team_id: int, last_n: int = 5) -> str:
    """Returns form string like 'WWDLW' from last N completed matches."""
    fx_res = (supabase.table("fixtures")
              .select("match_id, home_id, away_id")
              .or_(f"home_id.eq.{team_id},away_id.eq.{team_id}")
              .eq("status", "completed")
              .order("kickoff_ist", desc=True)
              .limit(last_n)
              .execute())

    if not fx_res.data:
        return ""

    match_ids = [fx["match_id"] for fx in fx_res.data]

    results_res = (supabase.table("results")
                   .select("match_id, outcome")
                   .in_("match_id", match_ids)
                   .execute())

    results_map = {r["match_id"]: r["outcome"] for r in results_res.data}

    form = ""
    for fx in fx_res.data:
        mid     = fx["match_id"]
        outcome = results_map.get(mid)
        if not outcome:
            continue
        is_home = fx["home_id"] == team_id
        if outcome == "D":
            form += "D"
        elif (outcome == "H" and is_home) or (outcome == "A" and not is_home):
            form += "W"
        else:
            form += "L"
    return form

# ---------------------------------------------------------------------
# RANK LOOKUP
# ---------------------------------------------------------------------

def get_team_rank(supabase: Client, team_id: int) -> str:
    """Returns rank string like 'A1' from standings table."""
    try:
        res = (supabase.table("standings")
               .select("group_name, position")
               .eq("team_id", team_id)
               .single()
               .execute())
        if res.data:
            group = res.data.get("group_name", "")
            pos   = res.data.get("position", "")
            if group and pos:
                return str(group) + str(pos)
    except Exception:
        pass
    return "—"

# ---------------------------------------------------------------------
# RANK LOOKUP (calculated, no position column)
# ---------------------------------------------------------------------

def get_team_rank(supabase: Client, team_id: int) -> str:
    """Calculates rank like 'A1' by sorting group standings."""
    try:
        # Get this team's group
        team_row = (supabase.table("standings")
                    .select("group_name")
                    .eq("team_id", team_id)
                    .single()
                    .execute())
        if not team_row.data:
            return "—"

        group = team_row.data["group_name"]

        group_rows = (supabase.table("standings")
                      .select("team_id, points, gd, gf")
                      .eq("group_name", group)
                      .order("points", desc=True)
                      .order("gd", desc=True)
                      .order("gf", desc=True)
                      .execute())

        for i, row in enumerate(group_rows.data, start=1):
            if row["team_id"] == team_id:
                return group + str(i)
    except Exception:
        pass
    return "—"

# ---------------------------------------------------------------------
# STADIUMS
# ---------------------------------------------------------------------

def stadium_by_city(supabase: Client, city: str) -> dict:
    try:
        res = (supabase.table("stadiums")
               .select("*")
               .eq("city", city)
               .single()
               .execute())
        return res.data or {}
    except Exception:
        return {}

# ---------------------------------------------------------------------
# PLAYERS
# ---------------------------------------------------------------------

def players_by_team(supabase: Client, team_id: int) -> list[dict]:
    try:
        res = (supabase.table("players")
               .select("*")
               .eq("team_id", team_id)
               .order("number")
               .execute())
        return res.data or []
    except Exception:
        return []