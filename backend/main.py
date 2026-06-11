import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import pandas as pd
from contextlib import asynccontextmanager

from core import db, predictor, scheduler

# Admin token/secret for securing endpoints
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "admin179")

# Lifespan context manager for scheduler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start scheduler on startup
    sched = scheduler.start()
    yield
    # Shutdown scheduler on shutdown
    sched.shutdown()

app = FastAPI(
    title="FIFA World Cup 2026 Predictor API",
    description="Backend API for predicting match outcomes, standings, and results.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas
class LoginRequest(BaseModel):
    email: str
    password: str

class SecretVerifyRequest(BaseModel):
    secret: str

class PredictionUpdate(BaseModel):
    match_id: int
    pred_home_goals: int
    pred_away_goals: int
    predicted_outcome: str
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    model_confidence: float

class ResultUpsert(BaseModel):
    match_id: int
    home_goals: int
    away_goals: int
    outcome: str

class ResultSubmit(BaseModel):
    match_id: int
    home_goals: int
    away_goals: int
    secret: str

class EventUpsert(BaseModel):
    match_id: int
    team_id: int
    player: str
    event: str
    time: Optional[int] = None

# Helper dependency to verify admin secret
def verify_admin_auth(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    # Support both Bearer token and raw secret string
    token = authorization
    if token.startswith("Bearer "):
        token = token[7:]
    if token != ADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin secret"
        )
    return True

# --- API ROUTES ---

@app.get("/api/health")
def health_check():
    return {"status": "ok", "date_ist": str(db.get_ist())}

# TEAMS
@app.get("/api/teams", response_model=List[dict])
def get_all_teams():
    return db.teams_all()

@app.get("/api/teams/{team_id}", response_model=dict)
def get_team_by_id(team_id: int):
    team = db.team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

# FIXTURES
@app.get("/api/fixtures/today", response_model=List[dict])
def get_fixtures_today():
    return db.fixtures_today()

@app.get("/api/fixtures/matchday", response_model=List[dict])
def get_fixtures_matchday():
    return db.fixtures_current_matchday()

@app.get("/api/fixtures/upcoming", response_model=List[dict])
def get_fixtures_upcoming():
    return db.fixtures_upcoming()

@app.get("/api/fixtures/group", response_model=List[dict])
def get_fixtures_group():
    return db.fixtures_group()

@app.get("/api/fixtures/stage/{stage}", response_model=List[dict])
def get_fixtures_by_stage(stage: str):
    return db.fixtures_by_stage(stage)

@app.get("/api/fixtures/{match_id}", response_model=dict)
def get_fixture_by_id(match_id: int):
    fixture = db.fixtures_by_id(match_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    return fixture

# PREDICTIONS
@app.get("/api/predictions", response_model=List[dict])
def get_predictions_all():
    return db.pred_all()

@app.get("/api/predictions/map", response_model=Dict[int, dict])
def get_predictions_map():
    return db.pred_map()

@app.get("/api/predictions/today", response_model=List[dict])
def get_predictions_today():
    return db.pred_today()

@app.post("/api/predictions")
def update_prediction(pred: PredictionUpdate, authenticated: bool = Depends(verify_admin_auth)):
    try:
        return db.pred_updated(pred.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# RESULTS
@app.get("/api/results", response_model=List[dict])
def get_results_all():
    return db.res_all()

@app.get("/api/results/map", response_model=Dict[int, dict])
def get_results_map():
    return db.res_map()

@app.post("/api/results")
def upsert_result(result: ResultUpsert, authenticated: bool = Depends(verify_admin_auth)):
    try:
        return db.res_upsert(result.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# STANDINGS
@app.get("/api/standings", response_model=List[dict])
def get_standings_all():
    return db.standings_all()

@app.get("/api/standings/group/{group_name}", response_model=List[dict])
def get_standings_by_group(group_name: str):
    return db.standings_by_group(group_name)

@app.get("/api/standings/ranks", response_model=Dict[int, str])
def get_standings_ranks():
    return db.rank_map()

@app.get("/api/standings/form", response_model=Dict[int, str])
def get_standings_form():
    return db.form_map()

# STADIUMS & PLAYERS
@app.get("/api/stadiums/{city}", response_model=dict)
def get_stadium_by_city(city: str):
    return db.stadium_by_city(city)

@app.get("/api/players/{team_id}", response_model=List[dict])
def get_players_by_team(team_id: int):
    return db.players_by_team(team_id)

# AUTH / VERIFY
@app.post("/api/auth/verify-secret")
def verify_secret(req: SecretVerifyRequest):
    is_valid = req.secret == ADMIN_SECRET
    return {"valid": is_valid}

@app.post("/api/auth/login")
def auth_login(req: LoginRequest):
    user = db.login(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"status": "success", "user": {"id": user.id, "email": user.email}}

@app.post("/api/auth/logout")
def auth_logout():
    db.logout()
    return {"status": "success"}

# EVENTS
@app.get("/api/fixtures/{match_id}/events", response_model=List[dict])
def get_match_events(match_id: int):
    return db.events_by_match(match_id)

# ADMIN ACTIONS
@app.post("/api/admin/submit-result")
def admin_submit_result(req: ResultSubmit):
    if req.secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Invalid admin secret")
    try:
        db.update_after_res(req.match_id, req.home_goals, req.away_goals)
        return {"status": "success", "message": "Result submitted and stats updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/run-predictions")
def admin_run_predictions(authenticated: bool = Depends(verify_admin_auth)):
    try:
        model, features = predictor.load_model()
        matchday_preds = db.fixtures_current_matchday()
        if matchday_preds:
            earliest_matchday = matchday_preds[0]["fixture"]["matchday_ist"]
            fixtures = [r["fixture"] for r in matchday_preds]
        else:
            all_upcoming = db.fixtures_upcoming()
            pred_map = db.pred_map()
            fixtures = [fx for fx in all_upcoming if fx["match_id"] not in pred_map][:8]

        if not fixtures:
            return {"status": "success", "count": 0, "message": "No fixtures to predict."}

        count = 0
        for fx in fixtures:
            pred = predictor.predict_match(model, features, fx)
            db.pred_updated(pred)
            count += 1
        return {"status": "success", "count": count, "message": f"Successfully generated predictions for {count} match(es)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/admin/events")
def upsert_event(event: EventUpsert, authenticated: bool = Depends(verify_admin_auth)):
    try:
        return db.event_upsert(event.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/events/{event_id}")
def delete_event(event_id: int, authenticated: bool = Depends(verify_admin_auth)):
    try:
        return db.event_delete(event_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# HEAD TO HEAD MATRIX
@app.get("/api/h2h/{home_code}/{away_code}")
def get_h2h(home_code: str, away_code: str):
    BASE_DIR = Path(__file__).parent
    csv_path = BASE_DIR / "data" / "h2h.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="H2H data file not found")
    
    try:
        h2h_df = pd.read_csv(csv_path, index_col="Team")
        
        # Check if codes exist in matrix columns and index
        if home_code not in h2h_df.index or away_code not in h2h_df.columns:
            return {"home_w": 0, "draws": 0, "away_w": 0, "total": 0, "available": False}
            
        raw1 = str(h2h_df.at[home_code, away_code])
        raw2 = str(h2h_df.at[away_code, home_code])
        
        r1 = dict(zip(["W", "D", "L"], map(int, raw1.split("-")))) if raw1 != "-" else {"W": 0, "D": 0, "L": 0}
        r2 = dict(zip(["W", "D", "L"], map(int, raw2.split("-")))) if raw2 != "-" else {"W": 0, "D": 0, "L": 0}
        
        home_w = r1["W"] + r2["L"]
        draws = r1["D"] + r2["D"]
        away_w = r1["L"] + r2["W"]
        total = home_w + draws + away_w
        
        return {
            "home_w": home_w,
            "draws": draws,
            "away_w": away_w,
            "total": total,
            "available": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading H2H data: {str(e)}")

# KIT COLORS
@app.get("/api/kit-colors")
def get_kit_colors():
    # Attempt to load kit colors JSON
    BASE_DIR = Path(__file__).parent
    kit_path = BASE_DIR / "core" / "static" / "kit_colors.json"
    if not kit_path.exists():
        kit_path = BASE_DIR / "static" / "kit_colors.json"
        
    if kit_path.exists():
        import json
        try:
            with open(kit_path) as f:
                return json.load(f)
        except Exception:
            pass
            
    # Default kit colors if file is missing
        return {
    "ALG": { "home": "#ffffff", "away": "#149f7e" },
    "ARG": { "home": "#75AADB", "away": "#081324" },
    "AUS": { "home": "#ffc745", "away": "#065d66" },
    "AUT": { "home": "#d70f22", "away": "#FFFFFF" },
    "BEL": { "home": "#bb1322", "away": "#c0d6db" },
    "BIH": { "home": "#001d5b", "away": "#FFFFFF" },
    "BRA": { "home": "#ffdc4e", "away": "#1a2c59" },
    "CAN": { "home": "#e90203", "away": "#1c1c1c" },
    "CIV": { "home": "#fe7a12", "away": "#faf2e3" },
    "COD": { "home": "#007FFF", "away": "#FFFFFF" },
    "COL": { "home": "#FCD116", "away": "#003087" },
    "CPV": { "home": "#0c45a1", "away": "#FFFFFF" },
    "CRO": { "home": "#C8102E", "away": "#0039A6" },
    "CUW": { "home": "#002B7F", "away": "#ffebb8" },
    "CZE": { "home": "#D52B1E", "away": "#FFFFFF" },
    "ECU": { "home": "#FFD100", "away": "#061630" },
    "EGY": { "home": "#C8102E", "away": "#FFFFFF" },
    "ENG": { "home": "#FFFFFF", "away": "#e03247" },
    "ESP": { "home": "#C8102E", "away": "#ebebe7" },
    "FRA": { "home": "#072F5F", "away": "#c4dcd0" },
    "GER": { "home": "#FFFFFF", "away": "#0e1833" },
    "GHA": { "home": "#FFFFFF", "away": "#f1c741" },
    "HAI": { "home": "#003DA5", "away": "#ffffff" },
    "IRN": { "home": "#ffffff", "away": "#d51b29" },
    "IRQ": { "home": "#ffffff", "away": "#05653f" },
    "JOR": { "home": "#ffffff", "away": "#cc0210" },
    "JPN": { "home": "#003DA5", "away": "#FFFFFF" },
    "KOR": { "home": "#C8102E", "away": "#ab8adc" },
    "KSA": { "home": "#1e4541", "away": "#FFFFFF" },
    "MAR": { "home": "#C8102E", "away": "#ffffff" },
    "MEX": { "home": "#006847", "away": "#FFFFFF" },
    "NED": { "home": "#E25303", "away": "#ffffff" },
    "NOR": { "home": "#C8102E", "away": "#FFFFFF" },
    "NZL": { "home": "#FFFFFF", "away": "#000000" },
    "PAN": { "home": "#e40021", "away": "#ffffff" },
    "PAR": { "home": "#D52B1E", "away": "#36a7bf" },
    "POR": { "home": "#C8102E", "away": "#006633" },
    "QAT": { "home": "#8D1B3D", "away": "#FFFFFF" },
    "RSA": { "home": "#f8d41c", "away": "#0a5543" },
    "SCO": { "home": "#003DA5", "away": "#ef7864" },
    "SEN": { "home": "#ffffff", "away": "#066d48" },
    "SUI": { "home": "#D52B1E", "away": "#bff7cc" },
    "SWE": { "home": "#FECC02", "away": "#113d79" },
    "TUN": { "home": "#ffffff", "away": "#FFFFFF" },
    "TUR": { "home": "#C8102E", "away": "#da0b27" },
    "URU": { "home": "#75AADB", "away": "#101622" },
    "USA": { "home": "#c2243b", "away": "#2e2b34" },
    "UZB": { "home": "#0b378b", "away": "#FFFFFF" }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)