import joblib as jb
import json
import numpy as np
import pandas as pd
from datetime import datetime
import pytz
from db import (
    get_client, get_ist,
    fixtures_today, pred_updated,
    pred_by_match
)

MODEL = 'model/wc_predictor.pkl'
FEATURES = 'model/features.json'

def load_model():
    model = jb.load(MODEL)
    with open(FEATURES, 'r') as file:
        features = json.load(file)
    return model, features

def build(fixture: dict) -> dict:
    home = fixture['home']
    away = fixture['away']

    elo_diff = home['elo_rating'] - away['elo_rating']

    return {'elo_diff' : elo_diff}

def predict_match(model, features: list, fixture: dict) -> dict:
    feats = build(fixture)

    X = pd.DataFrame([feats])[features]

    probs = model.predict_proba(X)[0]
    classes = model.classes_
    prob_map = dict(zip(classes, probs))

    home_prob = prob_map.get('H', 0)
    draw_prob = prob_map.get('D', 0)
    away_prob = prob_map.get('A', 0)

    outcome = max(prob_map, key=prob_map.get)

    confidence = max(probs)

    return {
        'match_id' : fixture['match_id'],
        'home_win_prob' : round(home_prob, 4),
        'draw_prob' : round(draw_prob, 4),
        'away_win_prob' : round(away_prob, 4),
        'predicted_outcome' : outcome,
        'pred_home_goals' : est_goals(fixture['home'], fixture['away'], outcome),
        'pred_away_goals' : est_goals(fixture['away'], fixture['home'], outcome, reverse=True),
        'model_confidence' : round(float(confidence), 4),
        'model_version' : 'v1.0'        
    }

def est_goals(team: dict, opp: dict, outcome: str, reverse: bool = False) -> int:
    base_xg = team['avg_xg']
    opp_xga = opp['avg_xga']

    expected = (base_xg + opp_xga) / 2

    if not reverse:
        if outcome == 'H':
            expected *= 1.1
        elif outcome == 'A':
            expected *= 0.85
    else:
        if outcome == 'A':
            expected *= 1.1
        elif outcome == 'H':
            expected *= 0.85

    return max(0, round(expected))  

def predict_today():
    supabase = get_client()
    model, features = load_model()

    fixtures = fixtures_today(supabase)

    if not fixtures:
        print(f"No Games Today {get_ist}")

    for fixture in fixtures:
        exists = pred_by_match(supabase, fixture['match_id'])
        if exists:
            print(f"Already Predicted : {fixture['home']['name']} vs {fixture['away']['name']}")
            continue

        pred = predict_match(model, features, fixture)
        pred_updated(supabase, pred)

        print(f"✓ {fixture['home']['name']} vs {fixture['away']['name']}")
        print(f" H : {pred['home_win_prob']} | D : {pred['draw_prob']}  | A : {pred['away_win_prob']}")
        print(f" Predicted {pred['predicted_outcome']} | Confidence : {pred['model_confidence']}")
        print(f" Goals : {pred['pred_home_goals']} - {pred['pred_away_goals']}")

if __name__ == "__main__":
    predict_today()