import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { getFlagUrl } from '../utils/helpers';

export default function Knockouts() {
  const [stages, setStages] = useState({
    r32: [], r16: [], qf: [], sf: [], final: null, third: null
  });
  const [slotToCode, setSlotToCode] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeStage, setActiveStage] = useState('r32');

  const navigate = useNavigate();

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [
          r32Data, r16Data, qfData, sfData, finalData, thirdData, standingsData
        ] = await Promise.all([
          api.getFixturesByStage('R32'),
          api.getFixturesByStage('R16'),
          api.getFixturesByStage('QF'),
          api.getFixturesByStage('SF'),
          api.getFixturesByStage('Final'),
          api.getFixturesByStage('3RD'),
          api.getStandings()
        ]);

        const byGroup = {};
        standingsData.forEach((row) => {
          const grp = row.group_name;
          if (!byGroup[grp]) byGroup[grp] = [];
          byGroup[grp].push(row);
        });

        const slots = {};
        Object.entries(byGroup).forEach(([grp, rows]) => {
          const sorted = [...rows].sort((a, b) => {
            if (b.points !== a.points) return b.points - a.points;
            const gdB = b.gd ?? (b.gf - b.ga);
            const gdA = a.gd ?? (a.gf - a.ga);
            if (gdB !== gdA) return gdB - gdA;
            return b.gf - a.gf;
          });
          sorted.forEach((row, idx) => {
            const team = row.team || {};
            if (team.team_code) {
              slots[`${idx + 1}${grp}`] = team.team_code;
            }
          });
        });

        setSlotToCode(slots);
        setStages({
          r32: r32Data,
          r16: r16Data,
          qf: qfData,
          sf: sfData,
          final: finalData[0] || null,
          third: thirdData[0] || null
        });
      } catch (err) {
        console.error(err);
        setError('Failed to load tournament bracket.');
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

  const resolveLabel = (label) => {
    if (!label || label === 'TBD') return { display: 'TBD', flagCode: '', isPlaceholder: true };
    if (label.length === 2 && /^\d$/.test(label[0]) && /^[A-Z]$/.test(label[1])) {
      const code = slotToCode[label];
      if (code) return { display: code, flagCode: code, isPlaceholder: false };
    }
    return { display: label, flagCode: '', isPlaceholder: true };
  };

  const renderTeamRow = (team, label, score) => {
    let display = 'TBD';
    let flagCode = '';
    let isPlaceholder = true;

    if (team && team.team_code) {
      display = team.team_code;
      flagCode = team.team_code;
      isPlaceholder = false;
    } else {
      const resolved = resolveLabel(label);
      display = resolved.display;
      flagCode = resolved.flagCode;
      isPlaceholder = resolved.isPlaceholder;
    }

    return (
      <div className="flex items-center gap-[0.5rem] w-full">
        {flagCode ? (
          <img
            src={getFlagUrl(flagCode)}
            alt={flagCode}
            className="w-[20px] h-[15px] object-cover border border-[#1e1e1e]"
          />
        ) : (
          <div className="w-[20px] h-[15px] bg-[#141414] border border-[#2a2a2a] rounded-[2px]" />
        )}
        {isPlaceholder ? (
          <span className="font-inter text-gray-500 text-[0.8rem] font-medium leading-none truncate max-w-[80px]">
            {display}
          </span>
        ) : (
          <span className="font-champion text-[0.8rem] text-[#F0F0F0] leading-none tracking-wide select-none">
            {display}
          </span>
        )}
        {score !== undefined && score !== null && score !== '' && (
          <span className="font-champion text-[1rem] text-[#00C853] ml-auto leading-none select-none">
            {score}
          </span>
        )}
      </div>
    );
  };

  const renderBracketCard = (fx, isFinal = false) => {
    if (!fx) return <div className="w-[130px] h-[60px] bg-[#0d0d0d]/40 border border-dashed border-[#2a2a2a] rounded-[6px]" />;

    const home = fx.home || {};
    const away = fx.away || {};
    const results = fx.results || [];
    const res = results[0] || {};
    const hasResult = results.length > 0;
    const homeScore = hasResult ? res.home_goals : '';
    const awayScore = hasResult ? res.away_goals : '';
    const borderClass = isFinal ? 'border-white border-2' : 'border-[#2a2a2a] hover:border-white/30';
    const cursorClass = fx.match_id ? 'cursor-pointer' : 'cursor-default';

    return (
      <div
        onClick={() => fx.match_id && navigate(`/match/${fx.match_id}`)}
        className={`bg-[#091424] rounded-[6px] border ${borderClass} ${cursorClass} p-[0.4rem_0.55rem] w-[130px] flex flex-col gap-[0.2rem] shrink-0 transition-all duration-150`}
      >
        <div className="border-b border-[#3a3a3a] pb-[0.2rem]">
          {renderTeamRow(home, fx.home_label, homeScore)}
        </div>
        <div>
          {renderTeamRow(away, fx.away_label, awayScore)}
        </div>
      </div>
    );
  };

  const renderColumn = (matches) => (
    <div className="flex flex-col justify-around h-[82vh] shrink-0">
      {matches.map((fx) => (
        <div key={fx.match_id || fx.home_label + fx.away_label}>
          {renderBracketCard(fx)}
        </div>
      ))}
    </div>
  );

  const r32_l = stages.r32.slice(0, 8);
  const r32_r = stages.r32.slice(8);
  const r16_l = stages.r16.slice(0, 4);
  const r16_r = stages.r16.slice(4);
  const qf_l = stages.qf.slice(0, 2);
  const qf_r = stages.qf.slice(2);
  const sf_l = stages.sf.slice(0, 1);
  const sf_r = stages.sf.slice(1);

  const STAGES = [
    { key: 'r32', label: 'Round of 32' },
    { key: 'r16', label: 'Round of 16' },
    { key: 'qf', label: 'Quarter Finals' },
    { key: 'sf', label: 'Semi Finals' },
    { key: 'final', label: 'Final' },
  ];

  const mobileMatches = {
    r32: [...r32_l, ...r32_r],
    r16: [...r16_l, ...r16_r],
    qf: [...qf_l, ...qf_r],
    sf: [...sf_l, ...sf_r],
    final: [stages.final, stages.third].filter(Boolean),
  }[activeStage] || [];

  return (
    <div className="w-full flex flex-col">
      {/* Title */}
      <h1 className="font-champion text-[clamp(2rem,10vw,5rem)] tracking-wider text-[#F0F0F0] leading-none mb-4 text-center">
        KNOCKOUTS
      </h1>

      {/* Mobile + Desktop bracket — scrollable horizontally */}
      <div className="flex justify-start xl:justify-center overflow-x-auto select-none py-4 scrollbar w-full">
        <div className="grid grid-cols-[repeat(9,130px)] gap-[9px] w-max mx-auto items-center">

          {renderColumn(r32_l)}
          {renderColumn(r16_l)}
          {renderColumn(qf_l)}
          {renderColumn(sf_l)}

          {/* Center: Trophy, Final, 3rd */}
          <div className="flex flex-col items-center justify-center h-[82vh] gap-6 w-[130px] shrink-0">
            <div className="flex-1 flex flex-col items-center justify-end pb-3 gap-2">
              <img
                src="/trophy.png"
                alt="World Cup Trophy"
                className="w-[40px] h-auto object-contain select-none"
              />
              {renderBracketCard(stages.final, true)}
            </div>
            <div className="flex-1 flex flex-col items-center justify-start pt-3 gap-2">
              {renderBracketCard(stages.third, false)}
            </div>
          </div>

          {renderColumn(sf_r)}
          {renderColumn(qf_r)}
          {renderColumn(r16_r)}
          {renderColumn(r32_r)}

        </div>
      </div>
    </div>
  );
}