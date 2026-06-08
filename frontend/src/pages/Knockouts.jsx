import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { getFlagUrl } from '../utils/helpers';

// ─── Constants ────────────────────────────────────────────────────────────────
const CARD_W = 130;       // px — must match w-[130px]
const CARD_H = 60;        // px — approximate rendered height of each bracket card
const COL_GAP = 9;        // px — gap between card columns (not connector columns)
const CONNECTOR_W = 28;   // px — width of the SVG connector column
const STUB = 10;          // px — horizontal stub length from card edge into connector

/**
 * SVG connector column between two stages.
 *
 * leftCount  – number of cards in the left column
 * rightCount – number of cards in the right column (half of left)
 * height     – total column height (82vh resolved to px via ref, but we use a
 *              percentage-based approach with SVG viewBox instead)
 *
 * Layout: cards in each column are distributed with justify-around inside an
 * 82vh container, so card centers sit at:
 *   center_i = (i + 0.5) / n  ×  totalHeight   (fractional units 0–1)
 */
function BracketConnector({ leftCount, rightCount }) {
  // We use a viewBox of 0 0 CONNECTOR_W 100 and treat Y as percentages
  const totalH = 100;

  const leftCenters = Array.from({ length: leftCount }, (_, i) =>
    ((i + 0.5) / leftCount) * totalH
  );
  const rightCenters = Array.from({ length: rightCount }, (_, i) =>
    ((i + 0.5) / rightCount) * totalH
  );

  const paths = [];

  rightCenters.forEach((ry, ri) => {
    // Each right card connects to two left cards
    const ly1 = leftCenters[ri * 2];
    const ly2 = leftCenters[ri * 2 + 1];

    if (ly1 === undefined || ly2 === undefined) return;

    const midY = (ly1 + ly2) / 2;
    const x0 = 0;           // left edge (coming from left card stub)
    const x1 = CONNECTOR_W; // right edge (going to right card stub)

    // Left top stub → vertical → midpoint → horizontal to right
    paths.push(
      // Top left stub
      `M ${x0} ${ly1} H ${CONNECTOR_W * 0.45}`,
      // Bottom left stub
      `M ${x0} ${ly2} H ${CONNECTOR_W * 0.45}`,
      // Vertical joiner
      `M ${CONNECTOR_W * 0.45} ${ly1} V ${ly2}`,
      // Horizontal to right
      `M ${CONNECTOR_W * 0.45} ${midY} H ${x1}`
    );
  });

  return (
    <div
      className="shrink-0 self-stretch"
      style={{ width: CONNECTOR_W }}
    >
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${CONNECTOR_W} ${totalH}`}
        preserveAspectRatio="none"
        overflow="visible"
      >
        {paths.map((d, i) => (
          <path
            key={i}
            d={d}
            stroke="#2a3a4a"
            strokeWidth="0.8"
            fill="none"
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </svg>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
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
    if (!fx) return (
      <div className="w-[130px] h-[60px] bg-[#0d0d0d]/40 border border-dashed border-[#2a2a2a] rounded-[6px]" />
    );

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

  /** A column of cards distributed evenly over 82vh */
  const renderColumn = (matches) => (
    <div className="flex flex-col justify-around h-[82vh] shrink-0 w-[130px]">
      {matches.map((fx) => (
        <div key={fx.match_id || (fx.home_label + fx.away_label)}>
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

  return (
    <div className="w-full flex flex-col">
      {/* Title */}
      <h1 className="font-champion text-[clamp(2rem,10vw,5rem)] tracking-wider text-[#F0F0F0] leading-none mb-4 text-center">
        KNOCKOUTS
      </h1>

      {/* Bracket — horizontally scrollable */}
      <div className="flex justify-start xl:justify-center overflow-x-auto select-none py-4 w-full">
        <div className="flex items-stretch gap-0 w-max mx-auto">

          {/* ── Left half: R32 → R16 → QF → SF ── */}
          {renderColumn(r32_l)}
          <BracketConnector leftCount={r32_l.length} rightCount={r16_l.length} />
          {renderColumn(r16_l)}
          <BracketConnector leftCount={r16_l.length} rightCount={qf_l.length} />
          {renderColumn(qf_l)}
          <BracketConnector leftCount={qf_l.length} rightCount={sf_l.length} />
          {renderColumn(sf_l)}
          <BracketConnector leftCount={sf_l.length} rightCount={1} />

          {/* ── Center: Trophy + Final + 3rd ── */}
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

          {/* ── Right half: SF → QF → R16 → R32 (mirrored) ── */}
          <BracketConnector leftCount={1} rightCount={sf_r.length} />
          {renderColumn(sf_r)}
          <BracketConnector leftCount={sf_r.length} rightCount={qf_r.length} />
          {renderColumn(qf_r)}
          <BracketConnector leftCount={qf_r.length} rightCount={r16_r.length} />
          {renderColumn(r16_r)}
          <BracketConnector leftCount={r16_r.length} rightCount={r32_r.length} />
          {renderColumn(r32_r)}

        </div>
      </div>
    </div>
  );
}
