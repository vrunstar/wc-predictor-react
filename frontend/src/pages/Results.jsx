import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { stageLabel, getFlagUrl, renderFormSpans } from '../utils/helpers';

export default function Results() {
  const [completed, setCompleted] = useState([]);
  const [ranks, setRanks] = useState({});
  const [forms, setForms] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [predictionsData, ranksData, formsData] = await Promise.all([
          api.getPredictions(),
          api.getStandingsRanks(),
          api.getStandingsForm()
        ]);
        const completedData = predictionsData.filter((pred) => {
          const fx = pred.fixture || {};
          return fx.results !== null && fx.results !== undefined;
        });
        setCompleted(completedData);
        setRanks(ranksData);
        setForms(formsData);
      } catch (err) {
        console.error(err);
        setError('Failed to load completed results.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center py-24">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-white"></div>
    </div>
  );

  if (error) return (
    <div className="text-center bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6">
      <div className="text-red-500 text-lg mb-2">{error}</div>
      <button onClick={() => window.location.reload()} className="px-10 py-1 bg-white text-black font-semibold rounded hover:bg-neutral-200">Retry</button>
    </div>
  );

  if (completed.length === 0) return (
    <div className="text-center py-24 bg-[#091424] border border-[#242424]/40 rounded-[10px] p-12">
      <div className="text-5xl mb-4">🏆</div>
      <div className="text-xl font-bold font-hm_text tracking-wider text-gray-400">NO RESULTS YET</div>
    </div>
  );

  const groupedResults = {};
  completed.forEach((p) => {
    const fx = p.fixture || {};
    let dateStr = 'TBD';
    if (fx.kickoff_ist) {
      try {
        const d = new Date(fx.kickoff_ist);
        dateStr = !isNaN(d.getTime())
          ? d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
          : fx.matchday_ist || 'TBD';
      } catch (e) { dateStr = fx.matchday_ist || 'TBD'; }
    } else { dateStr = fx.matchday_ist || 'TBD'; }
    if (!groupedResults[dateStr]) groupedResults[dateStr] = [];
    groupedResults[dateStr].push(p);
  });

  return (
    <div>
      <h1 className="font-hm_text text-[3rem] md:text-[5.5rem] tracking-wide text-[#F0F0F0] leading-none mb-6 text-center">
        RESULTS
      </h1>

      {Object.entries(groupedResults).map(([date, items]) => (
        <div key={date} className="mb-8">
          <h2 className="font-inter text-[1.1rem] font-extrabold tracking-widest text-[#aaa] uppercase mb-3 text-center">
            {date}
          </h2>

          <div className="flex flex-col gap-3">
            {items.map((p) => {
              const fx = p.fixture || {};
              const home = fx.home || {};
              const away = fx.away || {};
              const homeCode = home.team_code || '???';
              const awayCode = away.team_code || '???';
              const homeRank = ranks[home.team_id] || '—';
              const awayRank = ranks[away.team_id] || '—';
              const homeForm = forms[home.team_id] || '';
              const awayForm = forms[away.team_id] || '';
              const venue = fx.venue || fx.city || '';
              const res = fx.results || {};
              const actualH = res.home_goals ?? '?';
              const actualA = res.away_goals ?? '?';
              const predH = p.pred_home_goals ?? '?';
              const predA = p.pred_away_goals ?? '?';
              const matchStage = stageLabel(fx.stage, fx.group_name);

              return (
                <div
                  key={p.match_id}
                  onClick={() => navigate(`/match/${p.match_id}`)}
                  className="block cursor-pointer select-none bg-[#091424] border border-[#242424]/40 hover:border-white/25 rounded-[10px] p-[0.85rem_1.4rem] relative transition-all duration-150 group"
                >
                  {/* Score Row */}
                  <div className="grid grid-cols-[24px_1fr_auto_1fr_24px] items-center gap-[0.6rem] w-full">
                    <img src={getFlagUrl(homeCode)} alt={homeCode} className="w-[22px] md:w-[26px] h-auto object-contain border border-[#1e1e1e]" onError={(e) => { e.target.style.display = 'none'; }} />
                    <div className="font-hm_text md:font-champion text-[1.375rem] md:text-2xl tracking-wider text-[#F0F0F0] leading-none">{homeCode}</div>
                    <div className="text-center min-w-[110px]">
                      <div className="flex items-baseline justify-center gap-2 md:gap-4">
                        <span className="font-champion text-2xl text-white tracking-widest leading-none">{actualH} – {actualA}</span>
                        <span className="font-inter font-extrabold text-[0.9rem] md:text-[1.1rem] text-gray-500">({predH}–{predA})</span>
                      </div>
                    </div>
                    <div className="font-hm_text md:font-champion text-[1.375rem] md:text-2xl tracking-wider text-[#F0F0F0] leading-none text-right">{awayCode}</div>
                    <img src={getFlagUrl(awayCode)} alt={awayCode} className="w-[22px] md:w-[26px] h-auto object-contain border border-[#1e1e1e] justify-self-end" onError={(e) => { e.target.style.display = 'none'; }} />
                  </div>

                  {/* Meta row — desktop */}
                  <div className="hidden md:grid grid-cols-[1fr_auto_1fr] items-center mt-[0.7rem] pt-[0.6rem] border-t border-[#1e1e1e] text-[0.9rem] font-inter text-gray-400">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-500">{homeRank}</span>
                      {renderFormSpans(homeForm)}
                    </div>
                    <div className="text-center text-[#999] text-xs">
                      Match {fx.match_id} · {matchStage} {venue && `· ${venue}`}
                    </div>
                    <div className="flex items-center gap-2 justify-end">
                      {renderFormSpans(awayForm)}
                      <span className="font-semibold text-gray-500">{awayRank}</span>
                    </div>
                  </div>

                  {/* Meta row — mobile */}
                  <div className="flex md:hidden justify-center mt-[0.5rem] pt-[0.5rem] border-t border-[#1e1e1e]">
                    <span className="font-inter text-[0.72rem] text-[#555] tracking-wider">
                      {venue && `${venue} · `}{matchStage}
                    </span>
                  </div>

                  <div className="absolute inset-0 flex items-center justify-center text-lg text-white/5 group-hover:text-white/20 pointer-events-none transition-colors duration-150">↗</div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}