import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { formatKickoff, getFlagUrl } from '../utils/helpers';

export default function Home() {
  const [matchdayPreds, setMatchdayPreds] = useState([]);
  const [predsMap, setPredsMap] = useState({});
  const [completedPredictions, setCompletedPredictions] = useState([]);
  const [metrics, setMetrics] = useState({ total: 0, correct: 0, wrong: 0, accuracy: 0 });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('predictions');

  const navigate = useNavigate();

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [matchdayData, predictionsData, predictionsMap] = await Promise.all([
          api.getFixturesMatchday(),
          api.getPredictions(),
          api.getPredictionsMap()
        ]);

        setMatchdayPreds(matchdayData);
        setPredsMap(predictionsMap);

        const completed = predictionsData.filter((pred) => {
          const fx = pred.fixture || {};
          const results = fx.results;
          return results && (Array.isArray(results) ? results.length > 0 : Object.keys(results).length > 0);
        });
        setCompletedPredictions(completed.slice(0, 5));

        const total = completed.length;
        let correct = 0;
        completed.forEach((p) => {
          const actualOutcome = ((p.fixture?.results || [])[0] || {}).outcome;
          if (p.predicted_outcome === actualOutcome) correct++;
        });
        const wrong = total - correct;
        const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0;
        setMetrics({ total, correct, wrong, accuracy });
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // matchday data is prediction rows: { pred_home_goals, pred_away_goals, fixture: {...} }
  const MatchRow = ({ fx, centerText }) => {
    const home = fx.home || {};
    const away = fx.away || {};
    const homeCode = home.team_code || 'TBD';
    const awayCode = away.team_code || 'TBD';
    return (
      <div
        onClick={() => navigate(`/match/${fx.match_id}`)}
        className="cursor-pointer bg-[#091424] border border-[#242424]/40 hover:border-white/25 rounded-[10px] p-[0.85rem_1rem] grid grid-cols-[28px_1fr_auto_1fr_28px] items-center gap-2 transition-all duration-150"
      >
        <img src={getFlagUrl(homeCode)} alt={homeCode} className="w-[26px] h-auto object-contain border border-[#1e1e1e]" onError={(e) => { e.target.style.display = 'none'; }} />
        <span className="font-FNR text-[1.2rem] tracking-[0.08em] text-[#F0F0F0]">{homeCode}</span>
        <span className="font-FNB font-black text-[1.4rem] text-white text-center tracking-[0.12em] leading-none min-w-[70px]">{centerText}</span>
        <span className="font-FNR text-[1.2rem] tracking-[0.08em] text-[#F0F0F0] text-right">{awayCode}</span>
        <img src={getFlagUrl(awayCode)} alt={awayCode} className="w-[26px] h-auto object-contain border border-[#1e1e1e] justify-self-end" onError={(e) => { e.target.style.display = 'none'; }} />
      </div>
    );
  };

  const renderMatchdayRows = () => {
    if (matchdayPreds.length === 0) return (
      <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6 text-center text-gray-500 font-FNR text-[0.85rem]">No upcoming matches</div>
    );
    return (
      <div className="flex flex-col gap-2">
        {matchdayPreds.map((fx) => {
          const pred = predsMap[fx.match_id];
          const centerText = pred?.pred_home_goals != null
            ? `${pred.pred_home_goals} – ${pred.pred_away_goals}`
            : formatKickoff(fx.kickoff_ist);
          return <MatchRow key={fx.match_id} fx={fx} centerText={centerText} />;
        })}
      </div>
    );
  };

  const renderResultRows = () => {
    if (completedPredictions.length === 0) return (
      <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6 text-center text-gray-500 font-FNR text-[0.85rem]">No results yet</div>
    );
    return (
      <div className="flex flex-col gap-2">
        {completedPredictions.map((pred) => {
          const fx = pred.fixture || {};
          const res = Array.isArray(fx.results) ? fx.results[0] || {} : fx.results || {};
          const scoreText = `${res.home_goals ?? '?'} – ${res.away_goals ?? '?'}`;
          return <MatchRow key={pred.match_id} fx={fx} centerText={scoreText} />;
        })}
      </div>
    );
  };

  // Get matchday label from first fixture
  const matchdayLabel = matchdayPreds.length > 0
    ? `MATCHDAY ${matchdayPreds[0]?.matchday_ist || ''}`
    : "TODAY'S MATCHES";

  return (
    <div className="flex flex-col">

      {/* ── DESKTOP: Screen 1 hero ── */}
      <div className="hidden md:flex h-screen items-center justify-center -mt-[60px]">
        <h1 className="font-FUCB text-[13rem] text-[#F0F0F0] leading-[0.9] uppercase select-none text-center">
          2026<br />WORLD CUP<br />PREDICTOR
        </h1>
      </div>

      {/* ── MOBILE: Hero + metrics + tabs all on one screen ── */}
      <div className="flex md:hidden flex-col gap-5 pt-[62px] pb-[80px] px-4 min-h-screen">
        <h1 className="font-FUCB text-[6rem] text-[#F0F0F0] leading-[0.8] uppercase select-none pb-20 -mx-[25px]">
          2026<br />WORLD<br />CUP<br />PREDICTOR
        </h1>

        <div className="grid grid-cols-2 gap-2">
          {[
            { value: metrics.correct, label: 'Correct' },
            { value: metrics.wrong,   label: 'Wrong'   },
            { value: metrics.total,   label: 'Total'   },
            { value: `${metrics.accuracy}%`, label: 'Accuracy' },
          ].map(({ value, label }) => (
            <div key={label} className="bg-[#091424] border border-[#242424]/40 rounded-[8px] p-3 flex flex-col items-start gap-0.5">
              <span className="font-FNB text-[1.4rem] text-[#F0F0F0] leading-none">{value}</span>
              <span className="font-FNR text-[9px] text-[#555] tracking-widest font-semibold">{label}</span>
            </div>
          ))}
        </div>

        <div className="flex border border-[#ffffff]/40 rounded-[8px] overflow-hidden">
          <button onClick={() => setActiveTab('predictions')} className={`flex-1 py-2 text-xs tracking-widest font-semibold font-FNR transition-colors ${activeTab === 'predictions' ? 'bg-white text-black' : 'bg-transparent text-[#c4c4c4]'}`}>
            Predictions
          </button>
          <button onClick={() => setActiveTab('results')} className={`flex-1 py-2 text-xs tracking-widest font-semibold font-FNR transition-colors ${activeTab === 'results' ? 'bg-white text-black' : 'bg-transparent text-[#c4c4c4]'}`}>
            Results
          </button>
        </div>

        {loading ? (
          <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6 text-center text-gray-500 font-FNR text-[0.85rem]">Loading...</div>
        ) : activeTab === 'predictions' ? renderMatchdayRows() : renderResultRows()}
      </div>

      {/* ── DESKTOP: Screen 2 metrics + columns ── */}
      <div className="hidden md:flex flex-col gap-8 pb-16">
        <div className="grid grid-cols-4 gap-4">
          {[
            { value: metrics.correct, label: 'Correct' },
            { value: metrics.wrong,   label: 'Wrong'   },
            { value: metrics.total,   label: 'Total'   },
            { value: `${metrics.accuracy}%`, label: 'Accuracy' },
          ].map(({ value, label }) => (
            <div key={label} className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-5 flex flex-col items-start gap-1">
              <span className="font-FNB text-[2.2rem] text-[#F0F0F0] leading-none">{value}</span>
              <span className="font-FNR text-xs text-[#555] uppercase tracking-widest font-semibold">{label}</span>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-8">
          <div>
            <h2 className="font-FUCB text-[1.8rem] tracking-wide text-[#F0F0F0] mb-4 uppercase">{matchdayLabel}</h2>
            {loading ? (
              <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6 text-center text-gray-500 font-FNR text-[0.85rem]">Loading...</div>
            ) : renderMatchdayRows()}
          </div>
          <div>
            <h2 className="font-FUCB text-[1.8rem] tracking-wide text-[#F0F0F0] mb-4 uppercase">LATEST RESULTS</h2>
            {loading ? (
              <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6 text-center text-gray-500 font-FNR text-[0.85rem]">Loading...</div>
            ) : renderResultRows()}
          </div>
        </div>
      </div>

    </div>
  );
}