import streamlit as st
from datetime import datetime, timezone, timedelta, date
import pytz
from supabase import create_client, Client


@st.cache_resource
def get_client() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_SERVICE_KEY"]
    )

def get_ist() -> date:
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).date()

# ---------------------------------------------------------------------
# TEAMS
# ---------------------------------------------------------------------
@st.cache_data(ttl=3600)
def teams_all(_supabase: Client) -> list[dict]:
    res = _supabase.table("teams").select("*").execute()
    return res.data

@st.cache_data(ttl=3600)
def team_by_id(_supabase: Client, team_id: int) -> dict:
    res = _supabase.table("teams").select("*").eq("team_id", team_id).single().execute()
    return res.data

# ---------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------
@st.cache_data(ttl=300)
def fixtures_today(_supabase: Client) -> list[dict]:
    today = str(get_ist())
    res = (_supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*), results(*)")
           .eq("matchday_ist", today)
           .order("kickoff_ist")
           .execute())
    return res.data

@st.cache_data(ttl=300)
def fixtures_group(_supabase: Client) -> list[dict]:
    res = (_supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*)")
           .eq("stage", "group")
           .order("kickoff_ist")
           .execute())
    return res.data

@st.cache_data(ttl=300)
def fixtures_by_stage(_supabase: Client, stage: str) -> list[dict]:
    res = (_supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*), results(*)")
           .eq("stage", stage)
           .order("kickoff_ist")
           .execute())
    return res.data

@st.cache_data(ttl=300)
def fixtures_upcoming(_supabase: Client) -> list[dict]:
    today_str = str(get_ist())
    res = (_supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*)")
           .gte("matchday_ist", today_str)
           .neq("status", "completed")
           .order("matchday_ist", desc=False)
           .order("kickoff_ist", desc=False)
           .execute())
    return res.data

@st.cache_data(ttl=300)
def fixtures_by_id(_supabase: Client, match_id: int) -> dict:
    res = (_supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*)")
           .eq("match_id", match_id)
           .single()
           .execute())
    return res.data

# ---------------------------------------------------------------------
# PREDICTIONS
# ---------------------------------------------------------------------

@st.cache_data(ttl=300)
def pred_by_match(_supabase: Client, match_id: int) -> dict | None:
    res = (_supabase.table("prediction")
           .select("*")
           .eq("match_id", match_id)
           .execute())
    return res.data[0] if res.data else None

@st.cache_data(ttl=300)
def pred_today(_supabase: Client) -> list[dict]:
    today = str(get_ist())
    res = (_supabase.table("prediction")
           .select("*, fixture:fixtures!match_id(*, home:teams!home_id(*), away:teams!away_id(*))")
           .eq("fixture.matchday_ist", today)
           .order("generated_at", desc=True)
           .execute())
    return [r for r in res.data if r.get("fixture")]

@st.cache_data(ttl=300)
def pred_all(_supabase: Client) -> list[dict]:
    res = (_supabase.table("prediction")
           .select("*, fixture:fixtures!match_id(*, home:teams!home_id(*), away:teams!away_id(*), results(*))")
           .order("generated_at", desc=True)
           .execute())
    return res.data

def pred_updated(supabase: Client, pred: dict) -> list[dict]:
    res = (supabase.table("prediction")
           .upsert(pred, on_conflict="match_id")
           .execute())
    st.cache_data.clear()
    return res.data

# ---------------------------------------------------------------------
# RESULTS
# ---------------------------------------------------------------------

@st.cache_data(ttl=300)
def res_by_match(_supabase: Client, match_id: int) -> dict | None:
    res = (_supabase.table("results")
           .select("*")
           .eq("match_id", match_id)
           .execute())
    return res.data[0] if res.data else None

@st.cache_data(ttl=300)
def res_all(_supabase: Client) -> list[dict]:
    res = (_supabase.table("results")
           .select("*, fixture:fixtures!match_id(*, home:teams!home_id(*), away:teams!away_id(*))")
           .order("updated_at", desc=True)
           .execute())
    return res.data

def res_upsert(supabase: Client, result: dict) -> dict:
    res = (supabase.table("results")
           .upsert(result, on_conflict="match_id")
           .execute())
    st.cache_data.clear()
    return res.data

# ---------------------------------------------------------------------
# STANDINGS
# ---------------------------------------------------------------------

@st.cache_data(ttl=300)
def standings_by_group(_supabase: Client, group_name: str) -> list[dict]:
    res = (_supabase.table("standings")
           .select("*, team:teams!team_id(name, team_code, fifa_rank)")
           .eq("group_name", group_name)
           .order("points, gd", desc=True)
           .execute())
    return res.data

@st.cache_data(ttl=300)
def standings_all(_supabase: Client) -> list[dict]:
    res = (_supabase.table("standings")
           .select("*, team:teams!team_id(name, team_code, fifa_rank)")
           .order("group_name, points, gd", desc=True)
           .execute())
    return res.data

def standings_update(supabase: Client, team_id: int, updates: dict) -> dict:
    res = (supabase.table("standings")
           .update(updates)
           .eq("team_id", team_id)
           .execute())
    st.cache_data.clear()
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

    def standing(team_id):
        return supabase.table("standings").select("*").eq("team_id", team_id).single().execute().data

    home_standing = standing(home["team_id"])
    away_standing = standing(away["team_id"])

    home_updates = {
        "played":  home_standing["played"] + 1,
        "won":     home_standing["won"]    + (1 if outcome == "H" else 0),
        "drawn":   home_standing["drawn"]  + (1 if outcome == "D" else 0),
        "lost":    home_standing["lost"]   + (1 if outcome == "A" else 0),
        "gf":      home_standing["gf"]     + home_goals,
        "ga":      home_standing["ga"]     + away_goals,
    }
    away_updates = {
        "played":  away_standing["played"] + 1,
        "won":     away_standing["won"]    + (1 if outcome == "A" else 0),
        "drawn":   away_standing["drawn"]  + (1 if outcome == "D" else 0),
        "lost":    away_standing["lost"]   + (1 if outcome == "H" else 0),
        "gf":      away_standing["gf"]     + away_goals,
        "ga":      away_standing["ga"]     + home_goals,
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

    st.cache_data.clear()
    
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

@st.cache_data(ttl=300)
def get_team_form(_supabase: Client, team_id: int, last_n: int = 5) -> str:
    fx_res = (_supabase.table("fixtures")
              .select("match_id, home_id, away_id")
              .or_(f"home_id.eq.{team_id},away_id.eq.{team_id}")
              .eq("status", "completed")
              .order("kickoff_ist", desc=True)
              .limit(last_n)
              .execute())

    if not fx_res.data:
        return ""

    match_ids = [fx["match_id"] for fx in fx_res.data]

    r_res = (_supabase.table("results")
                   .select("match_id, outcome")
                   .in_("match_id", match_ids)
                   .execute())

    r_map = {r["match_id"]: r["outcome"] for r in r_res.data}

    form = ""
    for fx in fx_res.data:
        mid     = fx["match_id"]
        outcome = r_map.get(mid)
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

@st.cache_data(ttl=300)
def get_team_rank(_supabase: Client, team_id: int) -> str:
    """Calculates rank like 'A1' by sorting group standings."""
    try:
        # Get this team's group
        team_row = (_supabase.table("standings")
                    .select("group_name")
                    .eq("team_id", team_id)
                    .single()
                    .execute())
        if not team_row.data:
            return "—"

        group = team_row.data["group_name"]

        group_rows = (_supabase.table("standings")
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

@st.cache_data(ttl=3600)
def stadium_by_city(_supabase: Client, city: str) -> dict:
    try:
        res = (_supabase.table("stadiums")
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

@st.cache_data(ttl=3600)
def players_by_team(_supabase: Client, team_id: int) -> list[dict]:
    try:
        res = (_supabase.table("players")
               .select("*")
               .eq("team_id", team_id)
               .order("number")
               .execute())
        return res.data or []
    except Exception:
        return []
