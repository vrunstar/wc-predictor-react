import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { formatKickoff, stageLabel, getFlagUrl, renderFormSpans } from '../utils/helpers';

function generateICS(fixtures) {
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//WC 2026 Predictor//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
  ];

  fixtures.forEach((fx) => {
    const home = fx.home || {};
    const away = fx.away || {};
    const homeCode = home.team_code || 'TBD';
    const awayCode = away.team_code || 'TBD';
    const venue = fx.city || fx.venue || '';
    const matchStage = fx.group_name ? `Group ${fx.group_name}` : fx.stage || '';

    let dtstart = '';
    let dtend = '';
    if (fx.kickoff_ist) {
      try {
        const d = new Date(fx.kickoff_ist);
        const pad = (n) => String(n).padStart(2, '0');
        const fmt = (dt) =>
          `${dt.getFullYear()}${pad(dt.getMonth() + 1)}${pad(dt.getDate())}T${pad(dt.getHours())}${pad(dt.getMinutes())}00`;
        dtstart = `TZID=Asia/Kolkata:${fmt(d)}`;
        const end = new Date(d.getTime() + 105 * 60 * 1000);
        dtend = `TZID=Asia/Kolkata:${fmt(end)}`;
      } catch (e) {}
    }

    lines.push('BEGIN:VEVENT');
    lines.push(`UID:wc2026-match-${fx.match_id}@wcpredictor`);
    lines.push(`SUMMARY:${homeCode} vs ${awayCode} - FIFA WC 2026`);
    lines.push(`DESCRIPTION:Match ${fx.match_id} · ${matchStage}`);
    if (venue) lines.push(`LOCATION:${venue}`);
    if (dtstart) lines.push(`DTSTART;${dtstart}`);
    if (dtend) lines.push(`DTEND;${dtend}`);
    lines.push('END:VEVENT');
  });

  lines.push('END:VCALENDAR');
  return lines.join('\r\n');
}

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

  const handleCalendarSync = () => {
    const ics = generateICS(fixtures);
    const blob = new Blob([ics], { type: 'text/calendar;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'wc2026-fixtures.ics';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return (
    <div className="flex items-center justify-center py-24">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-white"></div>
    </div>
  );

  if (error) return (
    <div className="text-center py-24 bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6">
      <div className="text-red-500 text-lg mb-2">{error}</div>
      <button onClick={() => window.location.reload()} className="px-4 py-2 bg-white text-black font-semibold rounded hover:bg-neutral-200">Retry</button>
    </div>
  );

  if (fixtures.length === 0) return (
    <div className="text-center bg-[#091424] border border-[#242424]/40 rounded-[10px] p-8">
      <div className="text-xl font-bold font-FUCB tracking-wider text-gray-400">NO UPCOMING FIXTURES</div>
    </div>
  );

  // Group by matchday_ist
  const groupedFixtures = {};
  fixtures.forEach((fx) => {
    const dateStr = fx.matchday_ist
      ? new Date(fx.matchday_ist + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
      : 'TBD';
    if (!groupedFixtures[dateStr]) groupedFixtures[dateStr] = [];
    groupedFixtures[dateStr].push(fx);
  });

  return (
    <div>
      <div className="flex items-center justify-center mb-6 relative">
        <h1 className="font-FUCB text-[3rem] md:text-[5.5rem] tracking-wide text-[#F0F0F0] leading-none text-center">
          FIXTURES
        </h1>
        <button
          onClick={handleCalendarSync}
          title="Add all fixtures to calendar"
          className="absolute right-0 w-10 h-10 bg-[#091424] border border-[#242424]/40 hover:border-white/40 rounded-[8px] flex items-center justify-center transition-all duration-150 shrink-0"
        >
          <img src="/icons/calendar.svg" alt="calendar" className="w-5 h-5 object-contain opacity-60 hover:opacity-100" />
        </button>
      </div>

      {Object.entries(groupedFixtures).map(([date, matches]) => (
        <div key={date} className="mb-8">
          <h2 className="font-FNR text-[0.8rem] font-medium tracking-widest text-[#aaa] mb-3 text-center">
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
                  <div className="grid grid-cols-[24px_1fr_auto_1fr_24px] items-center gap-[0.6rem] w-full">
                    <img src={getFlagUrl(homeCode)} alt={homeCode} className="w-[22px] md:w-[28px] h-auto object-contain border border-[#1e1e1e]" onError={(e) => { e.target.style.display = 'none'; }} />
                    <div className="font-FUCB md:font-FSEB text-[1.375rem] md:text-2xl tracking-wider text-[#F0F0F0] leading-none">{homeCode}</div>
                    <div className="text-center min-w-[60px] max-w-[90px]">
                      <span className="font-FNR text-lg md:text-xl font-semibold text-white tracking-widest leading-none whitespace-nowrap">{koTime}</span>
                    </div>
                    <div className="font-FUCB md:font-FSEB text-[1.375rem] md:text-2xl tracking-wider text-[#F0F0F0] leading-none text-right">{awayCode}</div>
                    <img src={getFlagUrl(awayCode)} alt={awayCode} className="w-[22px] md:w-[28px] h-auto object-contain border border-[#1e1e1e]" onError={(e) => { e.target.style.display = 'none'; }} />
                  </div>

                  <div className="hidden md:grid grid-cols-[1fr_auto_1fr] items-center mt-[0.7rem] pt-[0.6rem] border-t border-[#3a3a3a] text-[0.9rem] font-FNR text-gray-400">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-500">{homeRank}</span>
                      {renderFormSpans(homeForm)}
                    </div>
                    <div className="text-center text-[#999] text-xs">Match {fx.match_id} · {matchStage} {venue && `· ${venue}`}</div>
                    <div className="flex items-center gap-2 justify-end">
                      {renderFormSpans(awayForm)}
                      <span className="font-semibold text-gray-500">{awayRank}</span>
                    </div>
                  </div>

                  <div className="flex md:hidden justify-center mt-[0.5rem] pt-[0.5rem] border-t border-[#3a3a3a]">
                    <span className="font-FNR text-[0.72rem] text-[#555] tracking-wider">
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