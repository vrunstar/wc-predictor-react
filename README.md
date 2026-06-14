# ```2026 World Cup Predictor```

A full-stack FIFA World Cup 2026 match prediction app.

**Live :**  [vrunstar-wc-predictor.vercel.app](https://vrunstar-wc-predictor.vercel.app)

---

## ```What it does```

WC 2026 Predictor uses a machine learning model to predict scorelines, outcomes, and win probabilities for every match in the tournament — group stage through the final. Predictions generate automatically once a day, standings and ELO ratings update after every result, and the app tracks its own accuracy throughout.

---

## ```Stack```

| Category | Tech |
|---|---|
| Frontend | React 19, Vite 8, Tailwind CSS 3, React Router DOM 7, Lucide React |
| Backend | FastAPI, Uvicorn, Python-multipart, APScheduler, Pytz |
| Data & ML | Supabase (PostgreSQL + client SDK), scikit-learn, pandas, numpy, joblib, python-dotenv |
| Deployment | Vercel (frontend), Render (backend), GitHub |

---

## ```Features```

**Predictions**
- ML model predicts scoreline, outcome, and win probabilities for each matchday
- Predictions auto-generate daily at 12:00 IST via APScheduler
- Confidence scores and win probability bars per match

**Fixtures & Results**
- All 104 group + knockout fixtures, grouped by matchday
- Add to Calendar (.ics) export for all upcoming fixtures

**Standings**
- Live group tables with points, GD, and recent form
- ELO ratings recalculated after every result

**Knockouts**
- Full 32-team bracket with SVG connector paths
- Mobile: stage tabs (R32 → Final) with left-to-right bracket view

**Match Detail**
- Head-to-head record, stadium info with map link
- Win probability bar with team kit colors
- Match events timeline — goals, cards, penalties
- Key player cards

**Admin**
- Password-protected panel for entering results and match events
- Manual prediction trigger

---

## ```Project Structure```

```
wc-predictor-react/
├── frontend/          # React + Vite app
│   ├── src/
│   │   ├── pages/     # Fixtures, Results, Predictions, Standings, Knockouts, MatchDetail, Home, Admin
│   │   ├── components/# Navbar
│   │   └── utils/     # api.js, helpers.js
│   └── public/
│       ├── fonts/     # Hitmarker, ChampionGothic
│       └── icons/
└── backend/           # FastAPI app
    ├── main.py        # API endpoints
    ├── core/
    │   ├── db.py          # Supabase queries + TTL cache
    │   ├── predictor.py   # ML model + prediction logic
    │   └── scheduler.py   # Daily prediction job (12:00 IST)
    └── model/         # Trained model + feature config
```

---

## ```How predictions work```

1. **Features**: home/away ELO rating, FIFA rank, average xG, average xGA, recent form (last 5 matches)
2. **Output**: predicted scoreline, win/draw/loss probabilities, confidence score
3. **After each result**: ELO ratings update with K=40, standings recalculate
4. **Schedule**: runs daily at 12:00 IST — after overnight matches finish, before evening kickoffs

---

## ```Local Setup```

**Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

`backend/.env`
```
SUPABASE_URL=your_url
SUPABASE_SERVICE_KEY=your_key
ADMIN_SECRET=your_secret
```

`frontend/.env`
```
VITE_API_URL=http://localhost:8000
```

---

*Built by [@vrunstar](https://github.com/vrunstar)*
