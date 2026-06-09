import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { formatKickoff, getFlagUrl } from '../utils/helpers';

export default function Home() {
  const [todayMatches, setTodayMatches] = useState([]);
  const [completedPredictions, setCompletedPredictions] = useState([]);
  const [metrics, setMetrics] = useState({ total: 0, correct: 0, wrong: 0, accuracy: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [fixturesData, predictionsData] = await Promise.all([
          api.getFixturesToday(),
          api.getPredictions()
        ]);

        const matches = fixturesData.filter(fx => !fx.results || fx.results.length === 0);
        setTodayMatches(matches);

        const completed = predictionsData.filter((pred) => {
          const fx = pred.fixture || {};
          return (fx.results || []).length > 0;
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
        setError('Failed to load dashboard data.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="flex flex-col">

      {/* ── SCREEN 1: Landing ── */}
      <div className="h-screen flex items-center justify-center px-4 md:px-0 -mt-[60px]">
        <h1 className="font-hm-text text-[3.2rem] md:text-[8rem] text-[#F0F0F0] leading-[0.9] uppercase select-none text-center">
          2026<br />WORLD CUP<br />PREDICTOR
        </h1>
      </div>

      {/* ── SCREEN 2: Metrics + Columns ── */}
      <div className="flex flex-col gap-8 pb-24 md:pb-16 px-4 md:px-0">

        {/* Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { value: metrics.correct, label: 'Correct' },
            { value: metrics.wrong,   label: 'Wrong'   },
            { value: metrics.total,   label: 'Total'   },
            { value: `${metrics.accuracy}%`, label: 'Accuracy' },
          ].map(({ value, label }) => (
            <div
              key={label}
              className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-5 flex flex-col items-start gap-1"
            >
              <span className="font-hm-text text-[2.2rem] text-[#F0F0F0] leading-none">{value}</span>
              <span className="font-inter text-xs text-[#555] uppercase tracking-widest font-semibold">{label}</span>
            </div>
          ))}
        </div>

        {/* Two Columns */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

          {/* Today's Predictions */}
          <div>
            <h2 className="font-hm-text text-[1.8rem] tracking-wide text-[#F0F0F0] mb-4 uppercase">
              TODAY'S MATCHES
            </h2>
            {loading ? (
              <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6 text-center text-gray-500 font-inter text-[0.85rem]">Loading...</div>
            ) : todayMatches.length === 0 ? (
              <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6 text-center text-gray-500 font-inter text-[0.85rem]">No matches today</div>
            ) : (
              <div className="flex flex-col gap-2">
                {todayMatches.map((fx) => {
                  const home = fx.home || {};
                  const away = fx.away || {};
                  const homeCode = home.team_code || 'TBD';
                  const awayCode = away.team_code || 'TBD';
                  const pred = fx.prediction || {};
                  const centerText = pred.pred_home_goals != null
                    ? `${pred.pred_home_goals} – ${pred.pred_away_goals}`
                    : formatKickoff(fx.kickoff_ist);
                  return (
                    <div
                      key={fx.match_id}
                      onClick={() => navigate(`/match/${fx.match_id}`)}
                      className="cursor-pointer bg-[#091424] border border-[#242424]/40 hover:border-white/25 rounded-[10px] p-[0.85rem_1rem] grid grid-cols-[28px_1fr_auto_1fr_28px] items-center gap-2 transition-all duration-150"
                    >
                      <img src={getFlagUrl(homeCode)} alt={homeCode} className="w-[26px] h-auto object-contain border border-[#1e1e1e]" onError={(e) => { e.target.style.display = 'none'; }} />
                      <span className="font-champion text-[1.2rem] tracking-[0.08em] text-[#F0F0F0]">{homeCode}</span>
                      <span className="font-inter font-black text-[1.4rem] text-white text-center tracking-[0.12em] leading-none min-w-[70px]">{centerText}</span>
                      <span className="font-champion text-[1.2rem] tracking-[0.08em] text-[#F0F0F0] text-right">{awayCode}</span>
                      <img src={getFlagUrl(awayCode)} alt={awayCode} className="w-[26px] h-auto object-contain border border-[#1e1e1e] justify-self-end" onError={(e) => { e.target.style.display = 'none'; }} />
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Latest Results */}
          <div>
            <h2 className="font-hm-text text-[1.8rem] tracking-wide text-[#F0F0F0] mb-4 uppercase">
              LATEST RESULTS
            </h2>
            {loading ? (
              <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6 text-center text-gray-500 font-inter text-[0.85rem]">Loading...</div>
            ) : completedPredictions.length === 0 ? (
              <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6 text-center text-gray-500 font-inter text-[0.85rem]">No results yet</div>
            ) : (
              <div className="flex flex-col gap-2">
                {completedPredictions.map((pred) => {
                  const fx = pred.fixture || {};
                  const home = fx.home || {};
                  const away = fx.away || {};
                  const homeCode = home.team_code || 'TBD';
                  const awayCode = away.team_code || 'TBD';
                  const res = (fx.results || [])[0] || {};
                  const scoreText = `${res.home_goals ?? '?'} – ${res.away_goals ?? '?'}`;
                  return (
                    <div
                      key={pred.match_id}
                      onClick={() => navigate(`/match/${pred.match_id}`)}
                      className="cursor-pointer bg-[#091424] border border-[#242424]/40 hover:border-white/25 rounded-[10px] p-[0.85rem_1rem] grid grid-cols-[28px_1fr_auto_1fr_28px] items-center gap-2 transition-all duration-150"
                    >
                      <img src={getFlagUrl(homeCode)} alt={homeCode} className="w-[26px] h-auto object-contain border border-[#1e1e1e]" onError={(e) => { e.target.style.display = 'none'; }} />
                      <span className="font-champion text-[1.2rem] tracking-[0.08em] text-[#F0F0F0]">{homeCode}</span>
                      <span className="font-inter font-black text-[1.4rem] text-white text-center tracking-[0.12em] leading-none min-w-[70px]">{scoreText}</span>
                      <span className="font-champion text-[1.2rem] tracking-[0.08em] text-[#F0F0F0] text-right">{awayCode}</span>
                      <img src={getFlagUrl(awayCode)} alt={awayCode} className="w-[26px] h-auto object-contain border border-[#1e1e1e] justify-self-end" onError={(e) => { e.target.style.display = 'none'; }} />
                    </div>
                  );
                })}
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
