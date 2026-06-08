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
    
    if (!groupedFixtures[dateStr]) {
      groupedFixtures[dateStr] = [];
    }
    groupedFixtures[dateStr].push(fx);
  });

  return (
    <div>
      {/* Page Title */}
      <h1 className="font-hitmarker text-[5rem] tracking-wider text-[#F0F0F0] leading-none mb-6 text-center">
        FIXTURES
      </h1>

      {/* Render grouped dates */}
      {Object.entries(groupedFixtures).map(([date, matches]) => (
        <div key={date} className="mb-8">
          {/* Date Header */}
          <h2 className="font-inter text-[1.1rem] font-extrabold tracking-widest text-[#aaa] mb-3 text-center">
            {date}
          </h2>

          {/* Matches grid / stack */}
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
              const venue = fx.venue || fx.city || '';

              return (
                <div 
                  key={fx.match_id}
                  onClick={() => navigate(`/match/${fx.match_id}`)}
                  className="block cursor-pointer select-none bg-[#091424] border border-[#242424]/40 hover:border-white/25 rounded-[10px] p-[0.85rem_1.4rem] relative transition-all duration-150 group"
                >
                  {/* Grid 1: Flags & Codes & Kickoff */}
                  <div className="grid grid-cols-[30px_1fr_auto_1fr_30px] items-center gap-[0.6rem] w-full">
                    {/* Home Flag */}
                    <div className="flex items-center justify-center">
                      <img 
                        src={getFlagUrl(homeCode)} 
                        alt={`${homeCode} Flag`} 
                        className="w-[28px] h-auto object-contain border border-[#1e1e1e]"
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                    </div>
                    {/* Home Code */}
                    <div className="font-champion text-2xl tracking-wider text-[#F0F0F0] leading-none">
                      {homeCode}
                    </div>
                    {/* Center: Kickoff Time */}
                    <div className="text-center min-w-[60px] max-w-[90px]">
                      <span className="font-inter text-lg md:text-xl font-extrabold text-white tracking-widest leading-none whitespace-nowrap">
                        {koTime}
                      </span>
                    </div>
                    {/* Away Code */}
                    <div className="font-champion text-2xl tracking-wider text-[#F0F0F0] leading-none text-right">
                      {awayCode}
                    </div>
                    {/* Away Flag */}
                    <div className="flex items-center justify-center">
                      <img 
                        src={getFlagUrl(awayCode)} 
                        alt={`${awayCode} Flag`} 
                        className="w-[28px] h-auto object-contain border border-[#1e1e1e]"
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                    </div>
                  </div>

                  {/* Grid 2: Stats & Metadata */}
                  <div className="grid grid-cols-[1fr_auto_1fr] items-center mt-[0.7rem] pt-[0.6rem] border-t border-[#3a3a3a] text-[0.9rem] font-inter text-gray-400">
                    {/* Home Stats */}
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-500">{homeRank}</span>
                      {renderFormSpans(homeForm)}
                    </div>
                    {/* Match Info */}
                    <div className="text-center text-[#999] text-xs">
                      Match {fx.match_id} &middot; {matchStage} {venue && `· ${venue}`}
                    </div>
                    {/* Away Stats */}
                    <div className="flex items-center gap-2 justify-end">
                      {renderFormSpans(awayForm)}
                      <span className="font-semibold text-gray-500">{awayRank}</span>
                    </div>
                  </div>

                  {/* Arrow overlay */}
                  <div className="absolute inset-0 flex items-center justify-center text-lg text-white/5 group-hover:text-white/20 pointer-events-none transition-colors duration-150">
                    ↗
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
