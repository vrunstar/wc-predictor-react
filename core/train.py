import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, classification_report
from sklearn.utils.class_weight import compute_sample_weight as csw
import joblib as jb 
import os
import json

TEAM_MAP = {
    "Türkiye" : 'Turkey',
    'USA' : 'United States',
    'Czechia' : 'Czech Republic'
}

def load_data() -> pd.DataFrame:
    df = pd.read_csv('data/results.csv')
    df['date'] = pd.to_datetime(df['date'])
    df = df[df['date'] >= '2000-01-01'].copy()
    df = df.dropna(subset=['home_score', 'away_score'])
    df = df.sort_values('date').reset_index(drop=True)
    return df

def elo_engine(df: pd.DataFrame, k: int = 40, base: float = 1500.0) -> dict:
    elo = {}

    for _, row in df.iterrows():
        home = row['home_team']
        away = row['away_team']

        if home not in elo:
            elo[home] = base
        if away not in elo:
            elo[away] = base
        
        home_elo = elo[home]
        away_elo = elo[away]

        x_home = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
        x_away = 1 - x_home

        if row['home_score'] > row['away_score']:
            home_actual, away_actual = 1.0, 0.0
        elif row['home_score'] == row['away_score']:
            home_actual, away_actual = 0.5, 0.5
        else:
            home_actual, away_actual = 0.0, 1.0

        elo[home] = round(home_elo + k * (home_actual - x_home), 2)
        elo[away] = round(away_elo + k * (away_actual - x_away), 2)
    
    return elo

def build(df: pd.DataFrame, k: int = 40, base: float = 1500.0) -> pd.DataFrame:
    elo = {}
    rows = []

    for _, row in df.iterrows():
        home = row['home_team']
        away = row['away_team']

        if home not in elo:
            elo[home] = base
        if away not in elo:
            elo[away] = base

        home_elo = elo[home]
        away_elo = elo[away]

        xh = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
        xa = 1 - xh

        if row['home_score'] > row['away_score']:
            outcome = 'H'
            home_actual, away_actual = 1.0, 0.0
        elif row['home_score'] == row['away_score']:
            outcome = 'D'
            home_actual, away_actual = 0.5, 0.5
        else:
            outcome = 'A'
            home_actual, away_actual = 0.0, 1.0

        rows.append({
            'home_elo' : home_elo,
            'away__elo' : away_elo,
            'elo_diff' : home_elo - away_elo,
            'expected_home' : xh,
            'outcome' : outcome
        })

        elo[home] = round(home_elo + k * (home_actual - xh), 2)
        elo[away] = round(away_elo + k * (away_actual - xa), 2)

    final_elo = elo
    return pd.DataFrame(rows), final_elo

def train():
    print("Loading Data ...")
    df = load_data()
    print(f"Matches Loaded : {len(df)}")

    print("Building training dataset with ELO ...")
    train_df, final_elo = build(df)
    print(f"Training Rows : {len(train_df)}")
    print(f"Outcome Distribution : \n{train_df['outcome'].value_counts()}")

    features = ['elo_diff']
    X = train_df[features]
    y = train_df['outcome']

    split_idx = int(len(train_df) * 0.8)

    X_train = X.iloc[ : split_idx]
    X_test = X.iloc[split_idx : ]
    y_train = y.iloc[:split_idx]
    y_test  = y.iloc[split_idx:]

    print(f"Train: {len(X_train)} matches | Test: {len(X_test)} matches")

    weights = csw(class_weight='balanced', y=y_train)

    print("Training Model ...")
    base_model = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        random_state=69
    )

    model = CalibratedClassifierCV(base_model, cv=5, method='isotonic')
    model.fit(X_train, y_train, sample_weight=weights)

    y_pred = model.predict(X_test)
    print(f"\nAccuracy : {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred))

    os.makedirs('model', exist_ok=True)
    jb.dump(model, 'model/wc_predictor.pkl')
    print("✓ Model saved to model/wc_predictor.pkl")

    with open('model/features.json', 'w') as f:
        json.dump(features, f)
    print("✓ Features saved to model/features.json")

    elo_df = pd.DataFrame([
        {'team' : team, 'computed_elo' : rating}
        for team, rating in final_elo.items()
    ])

    elo_df.to_csv('data/computed_elo.csv', index=False)
    print("✓ Final ELO saved to data/computed_elo.csv")

    return model

if __name__ == "__main__":
    train()