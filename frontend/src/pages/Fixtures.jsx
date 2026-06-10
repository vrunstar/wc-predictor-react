import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { formatKickoff, stageLabel, getFlagUrl, renderFormSpans } from '../utils/helpers';

export default function Fixtures() {
  const [fixtures, setFixtures] = useState([]);
  const [ranks, setRanks] = useState({});
  const [forms, setForms] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [fixturesData, ranksData, formsData] = await Promise.all([
          api.getFixturesUpcoming(),
          api.getStandingsRanks(),
          api.getStandingsForm()
        ]);
        setFixtures(fixturesData);
        setRanks(ranksData);
        setForms(formsData);
      } catch (err) {
        console.error(err);
        setError('Failed to load upcoming fixtures.');
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
      <div className="text-center py-24 bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6">
        <div className="text-red-500 text-lg mb-2">⚠️ {error}</div>
        <button onClick={() => window.location.reload()} className="px-4 py-2 bg-white text-black font-semibold rounded hover:bg-neutral-200">Retry</button>
      </div>
    );
  }

  if (fixtures.length === 0) {
    return (
      <div className="text-center bg-[#091424] border border-[#242424]/40 rounded-[10px] p-8">
        <div className="text-xl font-bold font-hm_text tracking-wider text-gray-400">NO UPCOMING FIXTURES</div>
      </div>
    );
  }

  const groupedFixtures = {};
  fixtures.forEach((fx) => {
    let dateStr = 'TBD';
    if (fx.kickoff_ist) {
      try {
        const d = new Date(fx.kickoff_ist);
        dateStr = !isNaN(d.getTime())
          ? d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
          : fx.matchday_ist || 'TBD';
      } catch (e) {
        dateStr = fx.matchday_ist || 'TBD';
      }
    } else {
      dateStr = fx.matchday_ist || 'TBD';
    }
    if (!groupedFixtures[dateStr]) groupedFixtures[dateStr] = [];
    groupedFixtures[dateStr].push(fx);
  });

  return (
    <div>
      <h1 className="font-hm_text text-[3rem] md:text-[5.5rem] tracking-wide text-[#F0F0F0] leading-none mb-6 text-center">
        FIXTURES
      </h1>

      {Object.entries(groupedFixtures).map(([date, matches]) => (
        <div key={date} className="mb-8">
          <h2 className="font-inter text-[0.8rem] font-medium tracking-widest text-[#aaa] mb-3 text-center">
            {date}
          </h2>

          <div className="flex flex-col gap-3">
            {matches.map((fx) => {
              const home = fx.home || {};
              const away = fx.away || {};
              const homeCode = home.team_code || 'TBD';
              const awayCode = away.team_code || 'TBD';
              const homeRank = ranks[home.team_id] || '—';
              const awayRank = ranks[away.team_id] || '—';
              const homeForm = forms[home.team_id] || '';
              const awayForm = forms[away.team_id] || '';
              const koTime = formatKickoff(fx.kickoff_ist);
              const matchStage = stageLabel(fx.stage, fx.group_name);
              const venue = fx.venue || fx.city || '';

              return (
                <div
                  key={fx.match_id}
                  onClick={() => navigate(`/match/${fx.match_id}`)}
                  className="block cursor-pointer select-none bg-[#091424] border border-[#242424]/40 hover:border-white/25 rounded-[10px] p-[0.85rem_1.4rem] relative transition-all duration-150 group"
                >
                  {/* Score Row */}
                  <div className="grid grid-cols-[24px_1fr_auto_1fr_24px] items-center gap-[0.6rem] w-full">
                    <div className="flex items-center justify-center">
                      <img src={getFlagUrl(homeCode)} alt={homeCode} className="w-[22px] md:w-[28px] h-auto object-contain border border-[#1e1e1e]" onError={(e) => { e.target.style.display = 'none'; }} />
                    </div>
                    <div className="font-hm_text md:font-champion text-[1.375rem] md:text-2xl tracking-wider text-[#F0F0F0] leading-none">
                      {homeCode}
                    </div>
                    <div className="text-center min-w-[60px] max-w-[90px]">
                      <span className="font-inter text-lg md:text-xl font-semibold text-white tracking-widest leading-none whitespace-nowrap">
                        {koTime}
                      </span>
                    </div>
                    <div className="font-hm_text md:font-champion text-[1.375rem] md:text-2xl tracking-wider text-[#F0F0F0] leading-none text-right">
                      {awayCode}
                    </div>
                    <div className="flex items-center justify-center">
                      <img src={getFlagUrl(awayCode)} alt={awayCode} className="w-[22px] md:w-[28px] h-auto object-contain border border-[#1e1e1e]" onError={(e) => { e.target.style.display = 'none'; }} />
                    </div>
                  </div>

                  {/* Meta row — desktop */}
                  <div className="hidden md:grid grid-cols-[1fr_auto_1fr] items-center mt-[0.7rem] pt-[0.6rem] border-t border-[#3a3a3a] text-[0.9rem] font-inter text-gray-400">
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

                  {/* Meta row — mobile: city · time only */}
                  <div className="flex md:hidden justify-center mt-[0.5rem] pt-[0.5rem] border-t border-[#3a3a3a]">
                    <span className="font-inter text-[0.72rem] text-[#555] tracking-wider">
                      Match {fx.match_id} · {matchStage} {venue && `· ${venue}`}
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
