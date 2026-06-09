import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { formatKickoff, getFlagUrl } from '../utils/helpers';

export default function Home() {
  const [todayMatches, setTodayMatches] = useState([]);
  const [completedPredictions, setCompletedPredictions] = useState([]);
  const [metrics, setMetrics] = useState({
    total: 0,
    correct: 0,
    wrong: 0,
    accuracy: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const maxScroll = 400;
      const progress = Math.min(scrollY / maxScroll, 1);
      setScrollProgress(progress);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [fixturesData, predictionsData] = await Promise.all([
          api.getFixturesToday(),
          api.getPredictions()
        ]);
        
        // Filter today's matches that are not completed (no results)
        const matches = fixturesData.filter(fx => !fx.results || fx.results.length === 0);
        setTodayMatches(matches);

        // Filter predictions that have results associated with their fixtures
        const completed = predictionsData.filter((pred) => {
          const fx = pred.fixture || {};
          const results = fx.results || [];
          return results.length > 0;
        });
        setCompletedPredictions(completed.slice(0, 4));

        // Calculate metrics
        const total = completed.length;
        let correct = 0;
        completed.forEach((p) => {
          const fx = p.fixture || {};
          const results = fx.results || [];
          const actualOutcome = (results[0] || {}).outcome;
          if (p.predicted_outcome === actualOutcome) {
            correct++;
          }
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

  // Calculate tournament start countdown
  const tournamentStart = new Date('2026-06-11T00:00:00');
  const now = new Date();
  const diffTime = tournamentStart - now;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  const countdownText = diffDays > 0 ? `${diffDays} days to go` : 'Tournament underway';

  return (
    <div className="flex flex-col gap-6">
      {/* Scroll morphing background */}
      <div className="fixed inset-0 -z-10 pointer-events-none">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{
            backgroundImage: "url('/bg.png')",
            opacity: 1 - scrollProgress,
          }}
        />
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{
            backgroundImage: "url('/bg-landing.png')",
            opacity: scrollProgress,
          }}
        />
        <div className="absolute inset-0 bg-black/60" />
      </div>

      {/* Hero Section */}
      <div className="relative w-full min-h-[280px] bg-gradient-to-br from-[#121212] to-[#0d0d0d] rounded-[14px] border border-white/3 shadow-[inset_0_1px_0_rgba(255,255,255,0.04),0_8px_24px_rgba(0,0,0,0.25)] flex items-center p-8 md:p-12 overflow-hidden">
        <div className="relative z-10 flex flex-col justify-center">
          <div className="text-[#00C853] text-[0.7rem] font-semibold tracking-[0.2em] uppercase mb-2 font-inter">
            {countdownText}
          </div>
          <h1 className="font-champion text-[2.4rem] md:text-[5.5rem] tracking-wider text-[#F0F0F0] leading-[0.95] mb-6 select-none uppercase text-center w-full">
            2026 WORLD CUP<br /> PREDICTOR
          </h1>
          <div className="flex flex-wrap gap-2">
            <span className="bg-white/5 border border-white/10 text-white px-[1.2rem] py-[0.55rem] rounded-[20px] text-sm font-semibold tracking-[0.03em] font-inter">
              {metrics.total} Predicted
            </span>
            <span className="bg-white/5 border border-white/10 text-white px-[1.2rem] py-[0.55rem] rounded-[20px] text-sm font-semibold tracking-[0.03em] font-inter">
              {metrics.correct} Correct
            </span>
            <span className="bg-white/5 border border-white/10 text-white px-[1.2rem] py-[0.55rem] rounded-[20px] text-sm font-semibold tracking-[0.03em] font-inter">
              {metrics.wrong} Wrong
            </span>
            <span className="bg-white/5 border border-white/10 text-white px-[1.2rem] py-[0.55rem] rounded-[20px] text-sm font-semibold tracking-[0.03em] font-inter">
              {metrics.accuracy}% Accuracy
            </span>
          </div>
        </div>
      </div>

      {/* Two Columns Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-4">
        {/* Left Column: Today's Matches */}
        <div>
          <h2 className="font-champion text-[1.8rem] tracking-[0.08em] text-[#F0F0F0] mb-4 uppercase">
            TODAY'S MATCHES
          </h2>
          {todayMatches.length === 0 ? (
            <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6 text-center text-gray-500 font-inter text-[0.85rem]">
              No matches today
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {todayMatches.map((fx) => {
                const home = fx.home || {};
                const away = fx.away || {};
                const homeCode = home.team_code || '???';
                const awayCode = away.team_code || '???';
                const centerText = formatKickoff(fx.kickoff_ist);

                return (
                  <div
                    key={fx.match_id}
                    onClick={() => navigate(`/match/${fx.match_id}`)}
                    className="cursor-pointer bg-[#091424] border border-[#242424]/40 hover:border-white/25 rounded-[10px] p-[0.85rem_1rem] grid grid-cols-[28px_1fr_auto_1fr_28px] items-center gap-2 transition-all duration-150"
                  >
                    <img
                      src={getFlagUrl(homeCode)}
                      alt={`${homeCode} Flag`}
                      className="w-[26px] h-auto object-contain border border-[#1e1e1e]"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                    <span className="font-champion text-[1.2rem] tracking-[0.08em] text-[#F0F0F0]">
                      {homeCode}
                    </span>
                    <span className="font-inter font-black text-[1.4rem] text-white text-center tracking-[0.12em] leading-none min-w-[70px]">
                      {centerText}
                    </span>
                    <span className="font-champion text-[1.2rem] tracking-[0.08em] text-[#F0F0F0] text-right">
                      {awayCode}
                    </span>
                    <img
                      src={getFlagUrl(awayCode)}
                      alt={`${awayCode} Flag`}
                      className="w-[26px] h-auto object-contain border border-[#1e1e1e] justify-self-end"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Latest Results */}
        <div>
          <h2 className="font-champion text-[1.8rem] tracking-[0.08em] text-[#F0F0F0] mb-4 uppercase">
            LATEST RESULTS
          </h2>
          {completedPredictions.length === 0 ? (
            <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6 text-center text-gray-500 font-inter text-[0.85rem]">
              No results yet
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {completedPredictions.map((pred) => {
                const fx = pred.fixture || {};
                const home = fx.home || {};
                const away = fx.away || {};
                const homeCode = home.team_code || '???';
                const awayCode = away.team_code || '???';
                const results = fx.results || [];
                const res = results[0] || {};
                const scoreText = `${res.home_goals ?? '?'} – ${res.away_goals ?? '?'}`;

                return (
                  <div
                    key={pred.match_id}
                    onClick={() => navigate(`/match/${pred.match_id}`)}
                    className="cursor-pointer bg-[#091424] border border-[#242424]/40 hover:border-white/25 rounded-[10px] p-[0.85rem_1rem] grid grid-cols-[28px_1fr_auto_1fr_28px] items-center gap-2 transition-all duration-150"
                  >
                    <img
                      src={getFlagUrl(homeCode)}
                      alt={`${homeCode} Flag`}
                      className="w-[26px] h-auto object-contain border border-[#1e1e1e]"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                    <span className="font-champion text-[1.2rem] tracking-[0.08em] text-[#F0F0F0]">
                      {homeCode}
                    </span>
                    <span className="font-inter font-black text-[1.4rem] text-white text-center tracking-[0.12em] leading-none min-w-[70px]">
                      {scoreText}
                    </span>
                    <span className="font-champion text-[1.2rem] tracking-[0.08em] text-[#F0F0F0] text-right">
                      {awayCode}
                    </span>
                    <img
                      src={getFlagUrl(awayCode)}
                      alt={`${awayCode} Flag`}
                      className="w-[26px] h-auto object-contain border border-[#1e1e1e] justify-self-end"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
