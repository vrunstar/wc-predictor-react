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
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-white text-black font-semibold rounded hover:bg-neutral-200"
        >
          Retry
        </button>
      </div>
    );
  }

  if (fixtures.length === 0) {
    return (
      <div className="text-center py-24 bg-[#091424] border border-[#242424]/40 rounded-[10px] p-12">
        <div className="text-xl font-bold font-champion tracking-wider text-gray-400">NO UPCOMING FIXTURES</div>
      </div>
    );
  }

  // Group fixtures by date
  const groupedFixtures = {};
  fixtures.forEach((fx) => {
    let dateStr = 'TBD';
    if (fx.kickoff_ist) {
      try {
        const d = new Date(fx.kickoff_ist);
        if (!isNaN(d.getTime())) {
          dateStr = d.toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'long',
            day: 'numeric'
          });
        } else {
          dateStr = fx.matchday_ist || 'TBD';
        }
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
      {/* Page Title */}
      <h1 className="font-champion text-[5rem] tracking-wider text-[#F0F0F0] leading-none mb-6 text-center">
        FIXTURES
      </h1>

      {Object.entries(groupedFixtures).map(([date, matches]) => (
        <div key={date} className="mb-8">
          {/* Date Header */}
          <h2 className="font-inter text-[1.1rem] font-extrabold tracking-widest text-[#aaa] mb-3 text-center">
            {date}
          </h2>

          <div className="flex flex-col gap-3">
            {matches.map((fx) => {
              const home = fx.home || {};
              const away = fx.away || {};
              const homeCode = home.team_code || '???';
              const awayCode = away.team_code || '???';
              const homeRank = ranks[home.team_id] || '—';
              const awayRank = ranks[away.team_id] || '—';
              const homeForm = forms[home.team_id] || '';
              const awayForm = forms[away.team_id] || '';
              const koTime = formatKickoff(fx.kickoff_ist);
              const matchStage = stageLabel(fx.stage, fx.group_name);

              return (
                <div
                  key={fx.match_id}
                  onClick={() => navigate(`/match/${fx.match_id}`)}
                  className="cursor-pointer select-none bg-[#091424] border border-[#242424]/40 hover:border-white/25 rounded-[10px] overflow-hidden transition-all duration-150 group"
                >
                  {/* Home Row */}
                  <div className="flex items-center px-4 py-3 border-b border-[#1e2a3a]">
                    {/* Left: Flag + Team */}
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <img
                        src={getFlagUrl(homeCode)}
                        alt={`${homeCode} flag`}
                        className="w-[26px] h-auto object-contain border border-[#1e1e1e] shrink-0"
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                      <span className="font-champion text-2xl tracking-wider text-[#F0F0F0] leading-none">
                        {homeCode}
                      </span>
                      <span className="font-inter text-xs text-gray-500 font-semibold">
                        {homeRank}
                      </span>
                      <span className="font-inter text-xs text-gray-600 truncate hidden sm:block">
                        {renderFormSpans(homeForm)}
                      </span>
                    </div>

                    {/* Right: Kickoff Time (shown only on home row, spans both via rowspan illusion) */}
                    <div className="flex items-center justify-end pl-4 border-l border-[#2a3a4a] ml-4 min-w-[80px]">
                      <span className="font-inter text-lg font-extrabold text-white tracking-widest whitespace-nowrap">
                        {koTime}
                      </span>
                    </div>
                  </div>

                  {/* Away Row */}
                  <div className="flex items-center px-4 py-3">
                    {/* Left: Flag + Team */}
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <img
                        src={getFlagUrl(awayCode)}
                        alt={`${awayCode} flag`}
                        className="w-[26px] h-auto object-contain border border-[#1e1e1e] shrink-0"
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                      <span className="font-champion text-2xl tracking-wider text-[#F0F0F0] leading-none">
                        {awayCode}
                      </span>
                      <span className="font-inter text-xs text-gray-500 font-semibold">
                        {awayRank}
                      </span>
                      <span className="font-inter text-xs text-gray-600 truncate hidden sm:block">
                        {renderFormSpans(awayForm)}
                      </span>
                    </div>

                    {/* Right: Stage label */}
                    <div className="flex items-center justify-end pl-4 border-l border-[#2a3a4a] ml-4 min-w-[80px]">
                      <span className="font-inter text-xs text-[#666] tracking-wide text-right">
                        {matchStage}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
