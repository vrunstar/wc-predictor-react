import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../utils/api';
import { formatKickoff, stageLabel, getFlagUrl } from '../utils/helpers';

// ── Fixture Card ─────────────────────────────────────────────────────────────
function FixtureCard({ fixture, prediction }) {
  const home = fixture.home || {};
  const away = fixture.away || {};
  const homeCode = home.team_code || '???';
  const awayCode = away.team_code || '???';
  const homeName = home.name || homeCode;
  const awayName = away.name || awayCode;

  const results = fixture.results || [];
  const res = results[0] || null;

  const koTime = formatKickoff(fixture.kickoff_ist);
  const [datePart, timePart] = koTime ? koTime.split(' ') : ['TBD', ''];

  const hasResult = !!res;
  const hasPrediction = !!prediction && !res;

  return (
    <Link
      to={`/match/${fixture.match_id}`}
      className="group block bg-[#1a1a1a] hover:bg-[#222] border border-[#2a2a2a] hover:border-[#3a3a3a] rounded-[6px] transition-colors duration-150 overflow-hidden"
    >
      <div className="p-4 flex flex-col gap-3">
        {/* Home team */}
        <TeamRow
          flagUrl={getFlagUrl(homeCode)}
          code={homeCode}
          name={homeName}
          goals={hasResult ? res.home_goals : hasPrediction ? prediction.pred_home_goals : null}
          isPred={hasPrediction}
          isWinner={hasResult && res.home_goals > res.away_goals}
        />

        {/* Away team */}
        <TeamRow
          flagUrl={getFlagUrl(awayCode)}
          code={awayCode}
          name={awayName}
          goals={hasResult ? res.away_goals : hasPrediction ? prediction.pred_away_goals : null}
          isPred={hasPrediction}
          isWinner={hasResult && res.away_goals > res.home_goals}
        />
      </div>

      {/* Footer */}
      <div className="px-4 py-2.5 border-t border-[#252525] flex items-center justify-between">
        <span className="font-mono text-[0.72rem] text-[#555] tracking-[0.04em]">
          {datePart}
        </span>
        <span className="font-mono text-[0.72rem] text-[#555] tracking-[0.04em]">
          {timePart} IST
        </span>
        {hasPrediction && (
          <span className="text-[0.65rem] text-[#444] font-semibold tracking-wider uppercase">
            {Math.round((prediction.model_confidence || 0) * 100)}% conf
          </span>
        )}
        {hasResult && (
          <span className="text-[0.65rem] text-[#444] font-semibold tracking-wider uppercase">
            FT
          </span>
        )}
        {!hasResult && !hasPrediction && (
          <span className="text-[0.65rem] text-[#333] tracking-wider uppercase">
            &nbsp;
          </span>
        )}
      </div>
    </Link>
  );
}

function TeamRow({ flagUrl, code, name, goals, isPred, isWinner }) {
  return (
    <div className="flex items-center gap-3">
      <img
        src={flagUrl}
        alt={code}
        className="w-[22px] h-auto shrink-0 object-contain"
        onError={(e) => { e.target.style.display = 'none'; }}
      />
      <span
        className={`flex-1 font-sans text-[0.9rem] font-medium truncate tracking-[0.01em] ${
          isWinner ? 'text-white' : 'text-[#aaa]'
        }`}
      >
        {name}
      </span>
      {goals !== null && (
        <span
          className={`font-mono text-[0.9rem] font-bold tabular-nums ${
            isPred
              ? 'text-[#555]'
              : isWinner
              ? 'text-white'
              : 'text-[#777]'
          }`}
        >
          {goals}
        </span>
      )}
    </div>
  );
}

// ── Group Section ─────────────────────────────────────────────────────────────
function GroupSection({ label, fixtures, predictionsMap }) {
  return (
    <section>
      <h2 className="font-sans text-[0.78rem] font-semibold text-[#666] tracking-[0.12em] uppercase mb-3">
        {label}
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {fixtures.map((f) => (
          <FixtureCard
            key={f.match_id}
            fixture={f}
            prediction={predictionsMap[f.match_id] || null}
          />
        ))}
      </div>
    </section>
  );
}

// ── Fixtures Page ─────────────────────────────────────────────────────────────
export default function FixturesPage() {
  const [fixtures, setFixtures] = useState([]);
  const [predictionsMap, setPredictionsMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeStage, setActiveStage] = useState('all');

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [fixturesData, predsMap] = await Promise.all([
          api.getFixtures(),
          api.getPredictionsMap(),
        ]);
        setFixtures(fixturesData || []);
        setPredictionsMap(predsMap || {});
      } catch (err) {
        console.error(err);
        setError('Failed to load fixtures.');
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
      </div>
    );
  }

  // Derive unique stages for tab filter
  const stages = ['all', ...Array.from(new Set(fixtures.map((f) => f.stage))).filter(Boolean)];

  const filtered =
    activeStage === 'all' ? fixtures : fixtures.filter((f) => f.stage === activeStage);

  // Group by stage + group_name
  const groups = {};
  for (const f of filtered) {
    const key = stageLabel(f.stage, f.group_name) || 'Other';
    if (!groups[key]) groups[key] = [];
    groups[key].push(f);
  }

  return (
    <div className="min-h-screen bg-[#111] text-white">
      {/* Top nav strip */}
      <header className="border-b border-[#1e1e1e] px-4 md:px-8 py-4 flex items-center justify-between">
        <span className="font-sans text-base font-bold tracking-tight text-white">
          Fixtures
        </span>
        {/* Stage tabs */}
        <nav className="flex items-center gap-1 overflow-x-auto">
          {stages.map((s) => {
            const label =
              s === 'all'
                ? 'All'
                : stageLabel(s, null) || s;
            return (
              <button
                key={s}
                onClick={() => setActiveStage(s)}
                className={`px-3 py-1.5 rounded-[4px] font-sans text-[0.78rem] font-semibold whitespace-nowrap transition-colors duration-100 ${
                  activeStage === s
                    ? 'bg-white text-black'
                    : 'text-[#666] hover:text-[#aaa]'
                }`}
              >
                {label}
              </button>
            );
          })}
        </nav>
      </header>

      {/* Content */}
      <main className="px-4 md:px-8 py-6 flex flex-col gap-8 max-w-[1400px] mx-auto">
        {Object.entries(groups).map(([label, groupFixtures]) => (
          <GroupSection
            key={label}
            label={label}
            fixtures={groupFixtures}
            predictionsMap={predictionsMap}
          />
        ))}
        {Object.keys(groups).length === 0 && (
          <div className="text-center text-[#444] py-16 text-sm">No fixtures found.</div>
        )}
      </main>
    </div>
  );
}
