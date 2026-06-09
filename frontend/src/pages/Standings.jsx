import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import { getFlagUrl } from '../utils/helpers';

export default function Standings() {
  const [standings, setStandings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await api.getStandings();
        setStandings(data);
      } catch (err) {
        console.error(err);
        setError('Failed to load group standings.');
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

  if (standings.length === 0) {
    return (
      <div className="text-center py-24 bg-[#091424] border border-[#242424]/40 rounded-[10px] p-12">
        <div className="text-5xl mb-4">📊</div>
        <div className="text-xl font-bold font-hm_text tracking-wider text-gray-400">NO STANDINGS AVAILABLE</div>
      </div>
    );
  }

  const groupedStandings = {};
  standings.forEach((row) => {
    const grp = row.group_name;
    if (!groupedStandings[grp]) groupedStandings[grp] = [];
    groupedStandings[grp].push(row);
  });

  const sortedGroupNames = Object.keys(groupedStandings).sort();

  return (
    <div className="w-full overflow-x-hidden">
      <h1 className="font-hm_text text-[3rem] md:text-[5.5rem] tracking-wide text-[#F0F0F0] leading-none mb-6 text-center">
        STANDINGS
      </h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {sortedGroupNames.map((grpName) => {
          const teams = [...groupedStandings[grpName]].sort((a, b) => {
            if (b.points !== a.points) return b.points - a.points;
            const gdB = b.gd ?? (b.gf - b.ga);
            const gdA = a.gd ?? (a.gf - a.ga);
            if (gdB !== gdA) return gdB - gdA;
            return b.gf - a.gf;
          });

          return (
            <div key={grpName} className="bg-[#091424] rounded-[10px] border border-[#242424]/40 p-[1rem_1.2rem] flex flex-col gap-2">
              {/* Group header */}
              <div className="font-hm_text text-[1.3rem] tracking-[0.1em] text-[#F0F0F0] border-b border-[#3a3a3a] pb-[0.5rem] mb-[0.4rem] uppercase">
                GROUP {grpName}
              </div>

              {/* Column headers */}
              <div className="grid grid-cols-[1.5fr_0.6fr_0.6fr_0.6fr_0.6fr_0.6fr_0.6fr] text-[0.65rem] text-gray-500 tracking-[0.12em] uppercase font-inter mb-1 px-1">
                <div>Team</div>
                <div className="text-center">P</div>
                <div className="text-center">W</div>
                <div className="text-center">D</div>
                <div className="text-center">L</div>
                <div className="text-center">GD</div>
                <div className="text-center">Pts</div>
              </div>

              {/* Rows */}
              <div className="flex flex-col gap-1">
                {teams.map((row) => {
                  const team = row.team || {};
                  const code = team.team_code || '???';
                  const gd = row.gd ?? (row.gf - row.ga);
                  const gdStr = (gd > 0 ? '+' : '') + gd;

                  return (
                    <div
                      key={row.team_id}
                      className="grid grid-cols-[1.5fr_0.6fr_0.6fr_0.6fr_0.6fr_0.6fr_0.6fr] items-center p-1 py-[0.25rem] rounded hover:bg-white/5 text-[0.82rem] font-inter text-gray-300 transition-colors duration-100"
                    >
                      <div className="flex items-center gap-2">
                        {/* Flag — hidden on mobile */}
                        <img
                          src={getFlagUrl(code)}
                          alt={code}
                          className="hidden sm:block w-[22px] h-auto object-contain border border-[#1e1e1e]"
                          onError={(e) => { e.target.style.display = 'none'; }}
                        />
                        {/* Code — hm_text on mobile, champion on desktop */}
                        <span className="font-hm_text text-[0.85rem] tracking-wider text-[#F0F0F0]">
                          {code}
                        </span>
                      </div>
                      <div className="text-center text-gray-400">{row.played}</div>
                      <div className="text-center text-gray-400">{row.won}</div>
                      <div className="text-center text-gray-400">{row.drawn}</div>
                      <div className="text-center text-gray-400">{row.lost}</div>
                      <div className="text-center text-gray-400">{gdStr}</div>
                      <div className="text-center font-champion text-base text-[#F0F0F0]">{row.points}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
