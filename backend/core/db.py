import os
import time
from functools import wraps
from datetime import datetime, timezone, timedelta, date
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# TTL Caching System
_CACHED_FUNCTIONS = []

def ttl_cache(ttl: int = 300):
    def decorator(func):
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            def make_hashable(val):
                if isinstance(val, dict):
                    return tuple(sorted((k, make_hashable(v)) for k, v in val.items()))
                elif isinstance(val, (list, tuple)):
                    return tuple(make_hashable(v) for v in val)
                elif isinstance(val, set):
                    return tuple(sorted(make_hashable(v) for v in val))
                return val
            
            key = (make_hashable(args), make_hashable(kwargs))
            now = time.time()
            
            if key in cache:
                cached_val, expires = cache[key]
                if now < expires:
                    return cached_val
            
            val = func(*args, **kwargs)
            cache[key] = (val, now + ttl)
            return val
            
        def cache_clear():
            cache.clear()
            
        wrapper.cache_clear = cache_clear
        _CACHED_FUNCTIONS.append(wrapper)
        return wrapper
    return decorator

def clear_all_caches():
    for func in _CACHED_FUNCTIONS:
        func.cache_clear()


# Initialize Supabase Client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables or .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_ist() -> date:
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).date()

def get_est() -> date:
    est = timezone(timedelta(hours=-5))
    return datetime.now(est).date()

# ---------------------------------------------------------------------
# TEAMS
# ---------------------------------------------------------------------
@ttl_cache(ttl=3600)
def teams_all() -> list[dict]:
    res = supabase.table("teams").select("*").execute()
    return res.data

@ttl_cache(ttl=3600)
def team_by_id(team_id: int) -> dict:
    res = supabase.table("teams").select("*").eq("team_id", team_id).single().execute()
    return res.data

# ---------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------
@ttl_cache(ttl=300)
def fixtures_today() -> list[dict]:
    today = str(get_ist())
    res = (supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*), results(*)")
           .eq("matchday_ist", today)
           .order("kickoff_ist")
           .execute())
    return res.data

@ttl_cache(ttl=300)
def fixtures_group() -> list[dict]:
    res = (supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*)")
           .eq("stage", "group")
           .order("kickoff_ist")
           .execute())
    return res.data

@ttl_cache(ttl=300)
def fixtures_by_stage(stage: str) -> list[dict]:
    res = (supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*), results(*)")
           .eq("stage", stage)
           .order("kickoff_ist")
           .execute())
    return res.data

@ttl_cache(ttl=300)
def fixtures_upcoming() -> list[dict]:
    today_str = str(get_ist())
    res = (supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*)")
           .gte("matchday_ist", today_str)
           .neq("status", "completed")
           .order("matchday_ist", desc=False)
           .order("kickoff_ist", desc=False)
           .execute())
    return res.data

@ttl_cache(ttl=300)
def fixtures_by_id(match_id: int) -> dict:
    res = (supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*), results(*)")
           .eq("match_id", match_id)
           .single()
           .execute())
    return res.data

# ---------------------------------------------------------------------
# PREDICTIONS
# ---------------------------------------------------------------------
@ttl_cache(ttl=300)
def pred_map() -> dict:
    rows = (supabase.table("prediction")
           .select("*")
           .execute()
           .data)
    
    return {
        row["match_id"] : row
        for row in rows
    }

@ttl_cache(ttl=300)
def pred_today() -> list[dict]:
    today = str(get_ist())
    res = (supabase.table("prediction")
           .select("*, fixture:fixtures!match_id(*, home:teams!home_id(*), away:teams!away_id(*))")
           .eq("fixture.matchday_ist", today)
           .order("generated_at", desc=True)
           .execute())
    return [r for r in res.data if r.get("fixture")]

@ttl_cache(ttl=300)
def pred_all() -> list[dict]:
    res = (supabase.table("prediction")
           .select("*, fixture:fixtures!match_id(*, home:teams!home_id(*), away:teams!away_id(*), results(*))")
           .order("generated_at", desc=True)
           .execute())
    return res.data

def pred_updated(pred: dict) -> list[dict]:
    res = (supabase.table("prediction")
           .upsert(pred, on_conflict="match_id")
           .execute())
    clear_all_caches()
    return res.data

# ---------------------------------------------------------------------
# RESULTS
# ---------------------------------------------------------------------
@ttl_cache(ttl=300)
def res_map() -> dict:
    rows = (supabase.table("results")
           .select("*")
           .execute()
           .data)
    return {
        row["match_id"] : row
        for row in rows
    }

@ttl_cache(ttl=300)
def res_all() -> list[dict]:
    res = (supabase.table("results")
           .select("*, fixture:fixtures!match_id(*, home:teams!home_id(*), away:teams!away_id(*))")
           .order("updated_at", desc=True)
           .execute())
    return res.data

def res_upsert(result: dict) -> dict:
    res = (supabase.table("results")
           .upsert(result, on_conflict="match_id")
           .execute())
    clear_all_caches()
    return res.data

# ---------------------------------------------------------------------
# STANDINGS
# ---------------------------------------------------------------------
@ttl_cache(ttl=300)
def standings_by_group(group_name: str) -> list[dict]:
    res = (supabase.table("standings")
           .select("*, team:teams!team_id(name, team_code, fifa_rank)")
           .eq("group_name", group_name)
           .order("points, gd", desc=True)
           .execute())
    return res.data

@ttl_cache(ttl=300)
def standings_all() -> list[dict]:
    res = (supabase.table("standings")
           .select("*, team:teams!team_id(name, team_code, fifa_rank)")
           .order("group_name, points, gd", desc=True)
           .execute())
    return res.data

@ttl_cache(ttl=300)
def rank_map() -> dict:
    rows = standings_all()
    groups = {}
    for row in rows:
        groups.setdefault(row["group_name"], []).append(row)
    ranks = {}
    for group, teams in groups.items():
        teams.sort(
            key=lambda x: (
                x["points"],
                x["gd"],
                x["gf"]
            ),
            reverse=True
        )
        for pos, team in enumerate(teams, start=1):
            ranks[team["team_id"]] = f"{group}{pos}"
    return ranks

def standings_update(team_id: int, updates: dict) -> dict:
    res = (supabase.table("standings")
           .update(updates)
           .eq("team_id", team_id)
           .execute())
    clear_all_caches()
    return res.data

# ---------------------------------------------------------------------
# UPDATE AFTER RESULT
# ---------------------------------------------------------------------
def update_after_res(match_id: int, home_goals: int, away_goals: int) -> None:
    fixture = fixtures_by_id(match_id)
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

    res_upsert({
        "match_id":   match_id,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "outcome":    outcome,
    })

    supabase.table("fixtures").update({"status": "completed"}).eq("match_id", match_id).execute()

    clear_all_caches()
    
    print(f"✓ Match {match_id} — {home['name']} {home_goals}-{away_goals} {away['name']}")
    print(f"  ELO: {home['name']} {home_elo}→{new_home_elo}, {away['name']} {away_elo}→{new_away_elo}")

# ---------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------
def login(email: str, passwd: str):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": passwd})
        return res.user
    except Exception:
        return None

def logout() -> None:
    supabase.auth.sign_out()

# ---------------------------------------------------------------------
# FORM
# ---------------------------------------------------------------------
@ttl_cache(ttl=300)
def form_map(n: int = 5) -> dict:
    fixt = (
        supabase.table("fixtures")
        .select("match_id, home_id, away_id, kickoff_ist")
        .eq("status", "completed")
        .order("kickoff_ist", desc=True)
        .execute()
        .data
    )

    match_ids = [fx["match_id"] for fx in fixt]
    res = (
        supabase.table("results")
        .select("match_id, outcome")
        .execute()
        .data
    )
    outcomes = {
        r["match_id"] : r["outcome"]
        for r in res
    }

    matches = {}

    for fx in fixt:
        matches.setdefault(fx["home_id"], []).append(fx)
        matches.setdefault(fx["away_id"], []).append(fx)

    forms = {}
    for team_id, games in matches.items():
        form = ""
        for fx in games[:n]:
            outcome = outcomes.get(fx["match_id"])
            if not outcome:
                continue
            is_home = fx["home_id"] == team_id
            if outcome == "D":
                form += "D"
            elif (outcome == "H" and is_home) or (outcome == "A" and not is_home):
                form += "W"
            else:
                form += "L"
        forms[team_id] = form
    return forms


# ---------------------------------------------------------------------
# STADIUMS
# ---------------------------------------------------------------------
@ttl_cache(ttl=3600)
def stadium_by_city(city: str) -> dict:
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
@ttl_cache(ttl=3600)
def players_by_team(team_id: int) -> list[dict]:
    try:
        res = (supabase.table("players")
               .select("*")
               .eq("team_id", team_id)
               .order("number")
               .execute())
        return res.data or []
    except Exception:
        return []

# ---------------------------------------------------------------------
# CURRENT MATCHDAY (via predictions)
# ---------------------------------------------------------------------
@ttl_cache(ttl=300)
def fixtures_current_matchday() -> list[dict]:
    today = str(get_est())
    res = (supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*), results(*)")
           .eq("matchday_est", today)
           .neq("status", "completed")
           .order("kickoff_ist")
           .execute())
    return res.data

@ttl_cache(ttl=300)
def fixtures_admin_pending() -> list[dict]:
    today = get_est()
    yesterday = str(today - timedelta(days=1))
    today_str = str(today)
    res = (supabase.table("fixtures")
           .select("*, home:teams!home_id(*), away:teams!away_id(*), results(*)")
           .in_("matchday_est", [yesterday, today_str])
           .neq("status", "completed")
           .order("kickoff_ist")
           .execute())
    return res.data

# ---------------------------------------------------------------------
# EVENTS
# ---------------------------------------------------------------------
@ttl_cache(ttl=60)
def events_by_match(match_id: int) -> list[dict]:
    try:
        res = (supabase.table("events")
               .select("*")
               .eq("match_id", match_id)
               .order("time")
               .execute())
        return res.data or []
    except Exception:
        return []

def event_upsert(event: dict) -> dict:
    res = (supabase.table("events")
           .insert(event)
           .execute())
    events_by_match.cache_clear()
    return res.data

def event_delete(event_id: int) -> dict:
    res = (supabase.table("events")
           .delete()
           .eq("id", event_id)
           .execute())
    clear_all_caches()
    return res.data

