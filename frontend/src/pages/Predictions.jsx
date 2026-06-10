import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { formatKickoff, stageLabel, getFlagUrl, renderFormSpans } from '../utils/helpers';

export default function Predictions() {
  const [fixtures, setFixtures] = useState([]);
  const [predictions, setPredictions] = useState({});
  const [ranks, setRanks] = useState({});
  const [forms, setForms] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [fixturesData, predictionsData, ranksData, formsData] = await Promise.all([
          api.getFixturesToday(),
          api.getPredictionsMap(),
          api.getStandingsRanks(),
          api.getStandingsForm()
        ]);
        setFixtures(fixturesData);
        setPredictions(predictionsData);
        setRanks(ranksData);
        setForms(formsData);
      } catch (err) {
        console.error(err);
        setError('Failed to load predictions.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-white"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6">
        <div className="text-red-500 text-lg mb-2"> {error} </div>
        <button onClick={() => window.location.reload()} className="px-10 py-1 bg-white text-black font-semibold rounded hover:bg-neutral-200">Retry</button>
      </div>
    );
  }

  if (fixtures.length === 0) {
    return (
      <div className="text-center bg-[#091424] border border-[#242424]/40 rounded-[10px] p-12">
        <div className="text-xl font-bold font-hm_text tracking-wider text-gray-400">No matches today</div>
      </div>
    );
  }

  const todayStr = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

  return (
    <div>
      {/* Title */}
      <div className="mb-6 text-center">
        <h1 className="font-hm_text text-[3rem] md:text-[5.5rem] tracking-wide text-[#F0F0F0] leading-none mb-1">
          PREDICTIONS
        </h1>
        <div className="font-inter font-extrabold text-sm md:text-xl text-[#999] tracking-widest uppercase">
          {todayStr}
        </div>
      </div>

      <hr className="border-[#222] my-6" />

      {/* Fixtures list */}
      <div className="flex flex-col gap-3">
        {fixtures.map((fx) => {
          const home = fx.home || {};
          const away = fx.away || {};
          const homeCode = home.team_code || '???';
          const awayCode = away.team_code || '???';
          const homeRank = ranks[home.team_id] || '—';
          const awayRank = ranks[away.team_id] || '—';
          const homeForm = forms[home.team_id] || '';
          const awayForm = forms[away.team_id] || '';
          const koTime = formatKickoff(fx.kickoff_ist);
          const venue = fx.venue || fx.city || '';
          const pred = predictions[fx.match_id] || {};
          const conf = Math.round((pred.model_confidence || 0) * 100);
          const hGoals = pred.pred_home_goals ?? '?';
          const aGoals = pred.pred_away_goals ?? '?';
          const outcome = pred.predicted_outcome || '?';
          let outcomeLabel = '—';
          if (outcome === 'H') outcomeLabel = homeCode;
          else if (outcome === 'A') outcomeLabel = awayCode;
          else if (outcome === 'D') outcomeLabel = 'Draw';

          return (
            <div
              key={fx.match_id}
              onClick={() => navigate(`/match/${fx.match_id}`)}
              className="block cursor-pointer select-none bg-[#091424] border border-[#111]/40 hover:border-white/25 rounded-[10px] p-[0.85rem_1.4rem] relative transition-all duration-150 group"
            >
              {/* Score Row */}
              <div className="grid grid-cols-[30px_1fr_auto_1fr_30px] items-center gap-[0.6rem] w-full">
                <div className="flex items-center justify-center">
                  <img src={getFlagUrl(homeCode)} alt={homeCode} className="w-[28px] h-auto object-contain border border-[#1e1e1e]" onError={(e) => { e.target.style.display = 'none'; }} />
                </div>

                {/* Home code — hm_text on mobile, champion on desktop */}
                <div className="font-hm_text md:font-champion text-2xl tracking-wider text-[#F0F0F0] leading-none">
                  {homeCode}
                </div>

                <div className="text-center min-w-[90px]">
                  <span className="font-champion text-[2rem] text-white tracking-widest leading-none">
                    {hGoals} – {aGoals}
                  </span>
                </div>

                {/* Away code — hm_text on mobile, champion on desktop */}
                <div className="font-hm_text md:font-champion text-2xl tracking-wider text-[#F0F0F0] leading-none text-right">
                  {awayCode}
                </div>

                <div className="flex items-center justify-center">
                  <img src={getFlagUrl(awayCode)} alt={awayCode} className="w-[28px] h-auto object-contain border border-[#1e1e1e]" onError={(e) => { e.target.style.display = 'none'; }} />
                </div>
              </div>

              {/* Meta row — desktop: rank + form + venue/time/conf */}
              <div className="hidden md:grid grid-cols-[1fr_auto_1fr] items-center mt-[0.7rem] pt-[0.6rem] border-t border-[#3a3a3a] text-[0.9rem] font-inter text-gray-400">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-500">{homeRank}</span>
                  {renderFormSpans(homeForm)}
                </div>
                <div className="text-center text-[#999] text-xs">
                  {koTime} {venue && `· ${venue}`} · <span className="font-semibold text-gray-500">{conf}% {outcomeLabel}</span>
                </div>
                <div className="flex items-center gap-2 justify-end">
                  {renderFormSpans(awayForm)}
                  <span className="font-semibold text-gray-500">{awayRank}</span>
                </div>
              </div>

              {/* Meta row — mobile: city · time · confidence only */}
              <div className="flex md:hidden justify-center mt-[0.5rem] pt-[0.5rem] border-t border-[#3a3a3a]">
                <span className="font-inter text-[0.72rem] text-[#555] tracking-wider">
                  {venue && `${venue} · `}{koTime} · <span className="text-gray-400 font-semibold">{conf}% {outcomeLabel}</span>
                </span>
              </div>

              <div className="absolute inset-0 flex items-center justify-center text-lg text-white/5 group-hover:text-white/20 pointer-events-none transition-colors duration-150">↗</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
