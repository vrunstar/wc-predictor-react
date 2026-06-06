import zipfile, os, pandas as pd
from collections import defaultdict

CSV = "data/results.csv"

if not os.path.exists(CSV):
    with zipfile.ZipFile(ZIP) as z:
        z.extract(CSV)

df = pd.read_csv(CSV, parse_dates=["date"])
df = df[df["date"].dt.year >= 2000].dropna(subset=["home_score", "away_score"])

TEAMS = {
    "AUT": "Austria", "BEL": "Belgium", "BIH": "Bosnia and Herzegovina",
    "CRO": "Croatia", "CZE": "Czech Republic", "ENG": "England",
    "FRA": "France", "GER": "Germany", "NED": "Netherlands",
    "NOR": "Norway", "POR": "Portugal", "SCO": "Scotland",
    "ESP": "Spain", "SWE": "Sweden", "SUI": "Switzerland", "TUR": "Turkey",
    "ALG": "Algeria", "CPV": "Cape Verde", "COD": "DR Congo",
    "EGY": "Egypt", "GHA": "Ghana", "CIV": "Ivory Coast",
    "MAR": "Morocco", "SEN": "Senegal", "RSA": "South Africa", "TUN": "Tunisia",
    "AUS": "Australia", "IRN": "Iran", "IRQ": "Iraq", "JPN": "Japan",
    "JOR": "Jordan", "QAT": "Qatar", "KSA": "Saudi Arabia",
    "KOR": "South Korea", "UZB": "Uzbekistan",
    "ARG": "Argentina", "BRA": "Brazil", "COL": "Colombia",
    "ECU": "Ecuador", "PAR": "Paraguay", "URU": "Uruguay",
    "CAN": "Canada", "CUW": "Curaçao", "HAI": "Haiti",
    "MEX": "Mexico", "PAN": "Panama", "USA": "United States",
    "NZL": "New Zealand",
}

name_to_code = {v: k for k, v in TEAMS.items()}
teams_set = set(TEAMS.values())
codes = sorted(TEAMS.keys())

df = df[df["home_team"].isin(teams_set) & df["away_team"].isin(teams_set)]

stats = defaultdict(lambda: [0, 0, 0])
for _, r in df.iterrows():
    h, a = r["home_team"], r["away_team"]
    hs, as_ = int(r["home_score"]), int(r["away_score"])
    hc, ac = name_to_code[h], name_to_code[a]
    if hs > as_:
        stats[(hc, ac)][0] += 1; stats[(ac, hc)][2] += 1
    elif hs == as_:
        stats[(hc, ac)][1] += 1; stats[(ac, hc)][1] += 1
    else:
        stats[(hc, ac)][2] += 1; stats[(ac, hc)][0] += 1

matrix = pd.DataFrame("-", index=codes, columns=codes)
for a in codes:
    for b in codes:
        if a != b:
            w, d, l = stats[(a, b)]
            matrix.at[a, b] = f"{w}-{d}-{l}"

matrix.index.name = "Team"
matrix.to_csv("data/h2h.csv")
print("Done → wc2026_h2h.csv")