import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { formatKickoff, getFlagUrl } from '../utils/helpers';

export default function Home() {
  const [todayMatches, setTodayMatches] = useState([]);
  const [completedPredictions, setCompletedPredictions] = useState([]);
  const [metrics, setMetrics] = useState({ total: 0, correct: 0, wrong: 0, accuracy: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scrollProgress, setScrollProgress] = useState(0);

  const navigate = useNavigate();
  const contentRef = useRef(null);

  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const triggerHeight = window.innerHeight * 0.3;
      const progress = Math.min(scrollY / triggerHeight, 1);
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

        const matches = fixturesData.filter(fx => !fx.results || fx.results.length === 0);
        setTodayMatches(matches);

        const completed = predictionsData.filter((pred) => {
          const fx = pred.fixture || {};
          return (fx.results || []).length > 0;
        });
        setCompletedPredictions(completed.slice(0, 4));

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

  const tournamentStart = new Date('2026-06-11T00:00:00');
  const now = new Date();
  const diffDays = Math.ceil((tournamentStart - now) / (1000 * 60 * 60 * 24));
  const countdownText = diffDays > 0 ? `${diffDays} days to go` : 'Tournament underway';

  return (
    <div className="flex flex-col">

      {/* ── SPLASH SECTION ── */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{ zIndex: scrollProgress >= 1 ? -1 : 10 }}
      >
        {/* Blue bg always visible */}
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: "url('/bg.png')" }}
        />

        {/* Dark overlay */}
        <div
          className="absolute inset-0 bg-black"
          style={{ opacity: 0.3 + scrollProgress * 0.35 }}
        />

        {/* Explosion — starts centered full screen, moves to top-left */}
        <img
          src="/wc-logo-exp.png"
          alt=""
          style={{
            position: 'absolute',
            width: `${(1 - scrollProgress) * 80 + scrollProgress * 20}vw`,
            top: `${scrollProgress * 10}px`,
            left: `${(1 - scrollProgress) * 10 + scrollProgress * 0}vw`,
            transform: `translate(${(1 - scrollProgress) * -50 + scrollProgress * 0}%, ${(1 - scrollProgress) * -50 + scrollProgress * 0}%)`,
            marginTop: scrollProgress < 1 ? `${(1 - scrollProgress) * 50}vh` : '0',
            opacity: 1,
            transition: 'none',
            objectFit: 'contain',
          }}
        />

        {/* Scroll hint */}
        <div
          className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
          style={{ opacity: Math.max(0, 1 - scrollProgress * 4) }}
        >
          <span className="font-inter text-xs text-white/60 tracking-widest uppercase">Scroll</span>
          <div className="w-[1px] h-8 bg-white/30 animate-pulse" />
        </div>
      </div>

      {/* ── SPACER — pushes content below the fold ── */}
      <div className="h-screen" />

      {/* ── MAIN CONTENT — slides up as you scroll ── */}
      <div
        ref={contentRef}
        className="relative z-10 flex flex-col gap-6 bg-black/0 pb-16"
        style={{
          transform: `translateY(${(1 - scrollProgress) * 60}px)`,
          opacity: scrollProgress,
          transition: 'opacity 0.1s, transform 0.1s',
        }}
      >
        {/* Hero Section */}
        <div className="relative w-full min-h-[280px] bg-black/40 backdrop-blur-md rounded-[14px] border border-white/10 flex items-center p-8 md:p-12 overflow-hidden">
          <div className="relative z-10 flex flex-col justify-center w-full">
            <div className="text-[#00C853] text-[0.7rem] font-semibold tracking-[0.2em] uppercase mb-2 font-inter">
              {countdownText}
            </div>
            <h1 className="font-champion text-[2.4rem] md:text-[5.5rem] tracking-wider text-[#F0F0F0] leading-[0.95] mb-6 select-none uppercase text-center w-full">
              2026 WORLD CUP<br /> PREDICTOR
            </h1>
            <div className="flex flex-wrap gap-2">
              {[
                `${metrics.total} Predicted`,
                `${metrics.correct} Correct`,
                `${metrics.wrong} Wrong`,
                `${metrics.accuracy}% Accuracy`,
              ].map((label) => (
                <span
                  key={label}
                  className="bg-white/5 border border-white/10 text-white px-[1.2rem] py-[0.55rem] rounded-[20px] text-sm font-semibold tracking-[0.03em] font-inter"
                >
                  {label}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Two Columns */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-4">
          {/* Today's Matches */}
          <div>
            <h2 className="font-champion text-[1.8rem] tracking-[0.08em] text-[#F0F0F0] mb-4 uppercase">
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
                  return (
                    <div
                      key={fx.match_id}
                      onClick={() => navigate(`/match/${fx.match_id}`)}
                      className="cursor-pointer bg-[#091424] border border-[#242424]/40 hover:border-white/25 rounded-[10px] p-[0.85rem_1rem] grid grid-cols-[28px_1fr_auto_1fr_28px] items-center gap-2 transition-all duration-150"
                    >
                      <img src={getFlagUrl(homeCode)} alt={homeCode} className="w-[26px] h-auto object-contain border border-[#1e1e1e]" onError={(e) => { e.target.style.display = 'none'; }} />
                      <span className="font-champion text-[1.2rem] tracking-[0.08em] text-[#F0F0F0]">{homeCode}</span>
                      <span className="font-inter font-black text-[1.4rem] text-white text-center tracking-[0.12em] leading-none min-w-[70px]">{formatKickoff(fx.kickoff_ist)}</span>
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
            <h2 className="font-champion text-[1.8rem] tracking-[0.08em] text-[#F0F0F0] mb-4 uppercase">
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
