import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { formatKickoff, stageLabel, getFlagUrl } from '../utils/helpers';

function FixtureCard({ fx, navigate }) {
  const home = fx.home || {};
  const away = fx.away || {};
  const homeCode = home.team_code || '???';
  const awayCode = away.team_code || '???';
  const homeName = home.name || homeCode;
  const awayName = away.name || awayCode;
  const koTime = formatKickoff(fx.kickoff_ist);

  // Split "13/06/2026 00:30" → date + time
  const parts = koTime ? koTime.split(' ') : [];
  const datePart = parts[0] || 'TBD';
  const timePart = parts[1] || '';

  return (
    <div
      onClick={() => navigate(`/match/${fx.match_id}`)}
      className="cursor-pointer bg-[#1c1c1c] hover:bg-[#242424] border border-[#2a2a2a] hover:border-[#3c3c3c] rounded-[6px] overflow-hidden transition-colors duration-150 select-none"
    >
      {/* Teams */}
      <div className="px-4 pt-4 pb-3 flex flex-col gap-3">
        <TeamRow flagUrl={getFlagUrl(homeCode)} name={homeName} />
        <TeamRow flagUrl={getFlagUrl(awayCode)} name={awayName} />
      </div>

      {/* Footer */}
      <div className="px-4 py-2.5 border-t border-[#252525] flex items-center justify-between">
        <span className="font-sans text-[0.72rem] text-[#555] tracking-[0.02em]">
          {datePart}
        </span>
        <span className="font-sans text-[0.72rem] text-[#555] tracking-[0.02em]">
          {timePart} IST
        </span>
      </div>
    </div>
  );
}

function TeamRow({ flagUrl, name }) {
  return (
    <div className="flex items-center gap-3">
      <img
        src={flagUrl}
        alt={name}
        className="w-[22px] h-auto shrink-0 object-contain"
        onError={(e) => { e.target.style.display = 'none'; }}
      />
      <span className="font-sans text-[0.9rem] font-medium text-[#ccc] truncate">
        {name}
      </span>
    </div>
  );
}

export default function Fixtures() {
  const [fixtures, setFixtures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const fixturesData = await api.getFixturesUpcoming();
        setFixtures(fixturesData || []);
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
        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[#444]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-24">
        <div className="text-red-500 text-sm mb-4">⚠️ {error}</div>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-white text-black text-sm font-semibold rounded hover:bg-neutral-200"
        >
          Retry
        </button>
      </div>
    );
  }

  if (fixtures.length === 0) {
    return (
      <div className="text-center py-24 text-[#444] text-sm">
        No upcoming fixtures.
      </div>
    );
  }

  // Group by stage label
  const groups = {};
  fixtures.forEach((fx) => {
    const key = stageLabel(fx.stage, fx.group_name) || 'Other';
    if (!groups[key]) groups[key] = [];
    groups[key].push(fx);
  });

  return (
    <div className="flex flex-col gap-8">
      {Object.entries(groups).map(([label, matches]) => (
        <section key={label}>
          <h2 className="font-sans text-[0.75rem] font-semibold text-[#555] tracking-[0.12em] uppercase mb-3">
            {label}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {matches.map((fx) => (
              <FixtureCard key={fx.match_id} fx={fx} navigate={navigate} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
