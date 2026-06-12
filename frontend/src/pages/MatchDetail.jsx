import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { formatKickoff, stageLabel, getFlagUrl, getStadiumPhotoUrl, getPlayerPhotoUrl, renderFormSpans } from '../utils/helpers';

export default function MatchDetail() {
  const { matchId } = useParams();
  const navigate = useNavigate();

  const [fixture, setFixture] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [ranks, setRanks] = useState({});
  const [forms, setForms] = useState({});
  const [stadium, setStadium] = useState({});
  const [h2h, setH2h] = useState(null);
  const [homePlayers, setHomePlayers] = useState([]);
  const [awayPlayers, setAwayPlayers] = useState([]);
  const [events, setEvents] = useState([]);
  const [kitColors, setKitColors] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('home');

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [fixtureData, predictionsMap, ranksData, formsData, kitColorsData] = await Promise.all([
          api.getFixture(parseInt(matchId)),
          api.getPredictionsMap(),
          api.getStandingsRanks(),
          api.getStandingsForm(),
          api.getKitColors()
        ]);

        setFixture(fixtureData);
        setPrediction(predictionsMap[parseInt(matchId)] || null);
        setRanks(ranksData);
        setForms(formsData);
        setKitColors(kitColorsData);

        const home = fixtureData.home || {};
        const away = fixtureData.away || {};

        const [h2hData, stadiumData, homePlayersData, awayPlayersData, eventsData] = await Promise.all([
          api.getH2H(home.team_code, away.team_code),
          fixtureData.city ? api.getStadium(fixtureData.city) : Promise.resolve({}),
          home.team_id ? api.getPlayers(home.team_id) : Promise.resolve([]),
          away.team_id ? api.getPlayers(away.team_id) : Promise.resolve([]),
          api.getMatchEvents(parseInt(matchId))
        ]);

        setH2h(h2hData);
        setStadium(stadiumData);
        setHomePlayers(homePlayersData);
        setAwayPlayers(awayPlayersData);
        setEvents(eventsData || []);
        setActiveTab(home.team_code || 'home');
      } catch (err) {
        console.error(err);
        setError('Failed to load match details.');
      } finally {
        setLoading(false);
      }
    }
    if (matchId) loadData();
  }, [matchId]);

  if (loading) return (
    <div className="flex items-center justify-center py-24">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-white"></div>
    </div>
  );

  if (error || !fixture) return (
    <div className="text-center py-24 bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6">
      <div className="text-red-500 text-lg mb-2">{error || 'Match not found'}</div>
      <Link to="/fixtures" className="px-4 py-2 bg-white text-black font-semibold rounded hover:bg-neutral-200">Back to Fixtures</Link>
    </div>
  );

  const home = fixture.home || {};
  const away = fixture.away || {};
  const homeCode = home.team_code || '???';
  const awayCode = away.team_code || '???';
  const homeName = home.name || homeCode;
  const awayName = away.name || awayCode;
  const homeRank = ranks[home.team_id] || '—';
  const awayRank = ranks[away.team_id] || '—';
  const homeForm = forms[home.team_id] || '';
  const awayForm = forms[away.team_id] || '';
  const results = fixture.results || [];
  const res = results[0] || null;
  const matchStage = stageLabel(fixture.stage, fixture.group_name);
  const koTime = formatKickoff(fixture.kickoff_ist);
  const homeColor = kitColors[homeCode]?.home || '#FFFFFF';
  const awayColor = kitColors[awayCode]?.away || '#888888';
  const showProb = prediction && !res;
  const hProb = showProb ? Math.round((prediction.home_win_prob || 0) * 100) : 0;
  const dProb = showProb ? Math.round((prediction.draw_prob || 0) * 100) : 0;
  const aProb = showProb ? 100 - hProb - dProb : 0;
  const stadPhotoKey = stadium.photo_key || '';
  const stadName = stadium.name || fixture.venue || 'TBD';
  const stadCity = stadium.city || fixture.city || '';
  const stadCapacity = stadium.capacity ? stadium.capacity.toLocaleString() : '—';
  const stadMapsUrl = `https://www.google.com/maps/search/${encodeURIComponent(stadName + ' ' + stadCity)}`;

  const scoreBlock = res ? (
    <div className="flex flex-col items-center">
      <div className="font-FSEB text-[2.5rem] md:text-[3rem] text-white tracking-widest leading-none select-none">
        {res.home_goals} – {res.away_goals}
      </div>
      <div className="font-FNR text-[0.72rem] text-gray-500 mt-1  tracking-wider font-semibold">
        ({prediction?.pred_home_goals ?? '?'}–{prediction?.pred_away_goals ?? '?'} pred)
      </div>
    </div>
  ) : prediction ? (
    <div className="flex flex-col items-center">
      <div className="font-FSEB text-[2.5rem] md:text-[3rem] text-white tracking-widest leading-none select-none">
        {prediction.pred_home_goals} – {prediction.pred_away_goals}
      </div>
      <div className="font-FNR text-[0.72rem] text-gray-400 mt-1  tracking-wider font-semibold">
        {Math.round((prediction.model_confidence || 0) * 100)}% conf
      </div>
    </div>
  ) : (
    <div className="flex flex-col items-center">
      <div className="font-FSEB text-[2.5rem] md:text-[3rem] text-white tracking-widest leading-none select-none">
        {koTime}
      </div>
      <div className="font-FNR text-[0.62rem] text-gray-500 mt-1  tracking-[0.14em] font-black">IST</div>
    </div>
  );

  const CardRect = ({ type }) => {
    if (type === 'yellow_card') return <span className="inline-block w-[10px] h-[14px] bg-yellow-400 rounded-[2px] ml-1 shrink-0 align-middle" />;
    if (type === 'red_card') return <span className="inline-block w-[10px] h-[14px] bg-red-600 rounded-[2px] ml-1 shrink-0 align-middle" />;
    return null;
  };

  const eventSuffix = (type) => {
    if (type === 'own_goal') return ' (og)';
    if (type === 'penalty') return ' (p)';
    return '';
  };

  const renderEventsTimeline = () => (
    <div className="flex flex-col gap-1.5">
      {events.map((ev, i) => {
        const isHome = ev.team_id === home.team_id;
        const suffix = eventSuffix(ev.event);
        return (
          <div key={i} className="grid grid-cols-[1fr_44px_1fr] items-center gap-1">
            <div className="flex items-center justify-end">
              {isHome && (
                <span className="font-FNR text-[0.78rem] text-[#e0e0e0] text-right flex items-center gap-1">
                  {ev.player}{suffix}<CardRect type={ev.event} />
                </span>
              )}
            </div>
            <div className="font-FNR text-[0.68rem] text-[#555] font-bold text-center whitespace-nowrap">
              {ev.time ? `${ev.time}'` : '—'}
            </div>
            <div className="flex items-center">
              {!isHome && (
                <span className="font-FNR text-[0.78rem] text-[#e0e0e0] flex items-center gap-1">
                  {ev.player}{suffix}<CardRect type={ev.event} />
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );

  const renderPlayersCol = (players) => {
    if (!players || players.length === 0) return <div className="text-[#333] text-[0.78rem] font-medium">—</div>;
    return (
      <div className="flex flex-col gap-2.5">
        {players.map((p) => {
          const photoUrl = getPlayerPhotoUrl(p.photo_key);
          const googleUrl = `https://www.google.com/search?q=${encodeURIComponent(p.full_name + ' footballer')}`;
          return (
            <a key={p.player_id} href={googleUrl} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-3 bg-white/2 border border-[#3a3a3a] rounded-[8px] p-2 hover:border-white/30 transition-colors">
              {photoUrl ? (
                <img src={photoUrl} alt={p.full_name} className="w-[45px] h-[45px] rounded-full object-cover border border-[#2a2a2a] shrink-0" onError={(e) => { e.target.style.display = 'none'; }} />
              ) : (
                <div className="w-[45px] h-[45px] rounded-full bg-[#141414] border border-[#2a2a2a] flex items-center justify-center shrink-0 font-FSEB text-[0.8rem] text-gray-500">{p.number}</div>
              )}
              <div className="flex flex-col">
                <div className="font-FNR text-sm font-semibold text-[#e0e0e0] tracking-[0.04em]">{p.full_name}</div>
                <div className="font-FNR text-[0.75rem] font-semibold text-gray-500 tracking-[0.08em] mt-0.5">{p.number} · {p.position}</div>
              </div>
            </a>
          );
        })}
      </div>
    );
  };

  return (
    <div className="flex flex-col gap-4">

      {/* Header — desktop only */}
      <div className="hidden md:flex items-center justify-center my-2 relative">
        <div className="font-FSEB text-3xl tracking-wider text-[#F0F0F0] leading-none flex items-baseline justify-center gap-4 text-center">
          MATCH {matchId}
          <span className="font-FNR text-sm font-extrabold text-gray-400 tracking-widest ">{matchStage}</span>
        </div>
        <button onClick={() => navigate(-1)} className="absolute right-0 flex items-center justify-center w-8 h-8 bg-[#091424] border border-[#242424]/40 hover:border-white/50 hover:text-white rounded-[6px] text-gray-500 font-FNR text-xs font-bold transition-all duration-150">x</button>
      </div>

      {/* ── MOBILE ── */}
      <div className="flex md:hidden flex-col gap-3 pb-24">

        {/* Hero card */}
        <div className="bg-[#091424] border border-[#242424]/40 rounded-[12px] p-4 flex flex-col gap-3 -mx-3">
          {/* Top row: Match · Stage + close */}
          <div className="flex items-center justify-between">
            <span className="font-FNR text-xl tracking-wider text-[#F0F0F0] leading-none">
              MATCH {matchId} <span className="font-FNR text-xs font-extrabold text-gray-400 tracking-widest ">{matchStage}</span>
            </span>
            <button onClick={() => navigate(-1)} className="flex items-center justify-center w-7 h-7 bg-[#0d1a2a] border border-[#242424]/40 hover:border-white/50 hover:text-white rounded-[6px] text-gray-500 font-FNR text-xs font-bold transition-all duration-150">x</button>
          </div>

          {/* Teams row */}
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <img src={getFlagUrl(homeCode)} alt={homeCode} className="w-[28px] h-auto object-contain border border-[#1e1e1e] shrink-0" onError={(e) => { e.target.style.display = 'none'; }} />
                <span className="font-FSEB text-[1.6rem] tracking-wider text-[#F0F0F0] leading-none">{homeCode}</span>
              </div>
              <span className="font-FNR text-xs text-[#444] font-medium">{homeName}</span>
            </div>
            <div className="flex justify-center">{scoreBlock}</div>
            <div className="flex flex-col gap-1 items-end">
              <div className="flex items-center gap-2">
                <span className="font-FSEB text-[1.6rem] tracking-wider text-[#F0F0F0] leading-none">{awayCode}</span>
                <img src={getFlagUrl(awayCode)} alt={awayCode} className="w-[28px] h-auto object-contain border border-[#1e1e1e] shrink-0" onError={(e) => { e.target.style.display = 'none'; }} />
              </div>
              <span className="font-FNR text-xs text-[#444] font-medium text-right">{awayName}</span>
            </div>
          </div>

          {/* Rank + Form */}
          <div className="grid grid-cols-[1fr_auto_1fr] items-center border-t border-[#242424] pt-3">
            <div className="flex items-center gap-2">
              <span className="font-FNR text-xs text-[#555] font-semibold">{homeRank}</span>
              {renderFormSpans(homeForm)}
            </div>
            <div className="w-px h-4 bg-[#333] mx-2" />
            <div className="flex items-center gap-2 justify-end">
              {renderFormSpans(awayForm)}
              <span className="font-FNR text-xs text-[#555] font-semibold">{awayRank}</span>
            </div>
          </div>

          {/* Win probability */}
          {showProb && (
            <div className="border-t border-[#242424] pt-3">
              <div className="flex justify-between font-FNR text-[0.65rem] font-bold text-gray-400 mb-1.5">
                <span>{homeCode} {hProb}%</span>
                <span>Draw {dProb}%</span>
                <span>{aProb}% {awayCode}</span>
              </div>
              <div className="flex h-[4px] rounded-[2px] overflow-hidden">
                <div style={{ width: `${hProb}%`, backgroundColor: homeColor }} className="opacity-90" />
                <div style={{ width: `${dProb}%` }} className="bg-[#333]" />
                <div style={{ width: `${aProb}%`, backgroundColor: awayColor }} className="opacity-90" />
              </div>
            </div>
          )}
        </div>

        {/* Venue */}
        {(stadName || stadCity) && (
          <a href={stadMapsUrl} target="_blank" rel="noopener noreferrer" className="relative border border-[#2a2a2a] rounded-[10px] overflow-hidden h-[140px] block -mx-3">
            {stadPhotoKey ? <div style={{ backgroundImage: `url(${getStadiumPhotoUrl(stadPhotoKey)})` }} className="absolute inset-0 bg-cover bg-center" /> : <div className="absolute inset-0 bg-[#0B0B0B]" />}
            <div className="absolute inset-0 bg-black/70" />
            <div className="relative z-10 flex flex-col justify-center items-center h-full text-center px-4">
              <div className="font-FSEB text-[1.4rem] text-[#F0F0F0] tracking-wider leading-none">{stadName}</div>
              <div className="font-FNR text-xs text-[#666] mt-1 font-semibold">{stadCity} · {stadCapacity}</div>
            </div>
          </a>
        )}

        {/* H2H */}
        {h2h && h2h.available && (
          <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-3 -mx-3">
            <div className="font-FNR text-[0.6rem] text-gray-500 font-bold tracking-[0.15em]  mb-2 text-center">Head-To-Head</div>
            <div className="flex items-center justify-center gap-3">
              <span className="font-FSEB text-[2rem] text-green-400 leading-none">{h2h.home_w}</span>
              <span className="font-FSEB text-lg text-gray-500 leading-none">–</span>
              <span className="font-FSEB text-[2rem] text-gray-400 leading-none">{h2h.draws}</span>
              <span className="font-FSEB text-lg text-gray-500 leading-none">–</span>
              <span className="font-FSEB text-[2rem] text-red-400 leading-none">{h2h.away_w}</span>
            </div>
          </div>
        )}

        {/* Events */}
        {res && events.length > 0 && (
          <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-3 -mx-3">
            <div className="font-FNR text-[0.6rem] text-gray-500 font-bold tracking-[0.15em]  mb-3 text-center">Match Events</div>
            {renderEventsTimeline()}
          </div>
        )}

        {/* Key Players */}
        {!res && (homePlayers.length > 0 || awayPlayers.length > 0) && (
          <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-3 -mx-3">
            <div className="font-FNR text-[0.6rem] text-gray-500 font-bold tracking-[0.15em]  mb-3 text-center">Key Players</div>
            <div className="flex mb-3 border border-[#2a2a2a] rounded-[6px] overflow-hidden">
              <button onClick={() => setActiveTab(homeCode)} className={`flex-1 py-1.5 font-FSEB text-sm tracking-wider transition-colors ${activeTab === homeCode ? 'bg-white text-black' : 'bg-transparent text-[#555]'}`}>{homeCode}</button>
              <button onClick={() => setActiveTab(awayCode)} className={`flex-1 py-1.5 font-FSEB text-sm tracking-wider transition-colors ${activeTab === awayCode ? 'bg-white text-black' : 'bg-transparent text-[#555]'}`}>{awayCode}</button>
            </div>
            {activeTab === homeCode ? renderPlayersCol(homePlayers) : renderPlayersCol(awayPlayers)}
          </div>
        )}

      </div>

      {/* ── DESKTOP ── */}
      <div className="hidden md:flex flex-col gap-0">
        <div className="bg-[#091424] border border-[#242424]/40 rounded-[12px] p-12">

          {/* Teams */}
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-12 w-full">
            <div className="flex flex-col items-start">
              <div className="flex items-center gap-3">
                <img src={getFlagUrl(homeCode)} alt={homeCode} className="w-[45px] h-auto object-contain border border-[#1e1e1e]" onError={(e) => { e.target.style.display = 'none'; }} />
                <span className="font-FSEB text-[2rem] tracking-wider text-[#F0F0F0] leading-none select-none">{homeCode}</span>
              </div>
              <div className="font-FNR text-[1.25rem] text-[#666] mt-1.5 font-medium">{homeName}</div>
              <div className="flex items-center gap-2 mt-1">
                <span className="font-FNR text-sm text-[#444] font-semibold">{homeRank}</span>
                <span className="font-FNR text-sm text-[#333]">·</span>
                {renderFormSpans(homeForm)}
              </div>
            </div>
            <div className="flex justify-center">{scoreBlock}</div>
            <div className="flex flex-col items-end">
              <div className="flex items-center gap-3 justify-end">
                <span className="font-FSEB text-[2rem] tracking-wider text-[#F0F0F0] leading-none select-none">{awayCode}</span>
                <img src={getFlagUrl(awayCode)} alt={awayCode} className="w-[45px] h-auto object-contain border border-[#1e1e1e]" onError={(e) => { e.target.style.display = 'none'; }} />
              </div>
              <div className="font-FNR text-[1.25rem] text-[#666] mt-1.5 font-medium">{awayName}</div>
              <div className="flex items-center gap-2 mt-1 justify-end">
                {renderFormSpans(awayForm)}
                <span className="font-FNR text-sm text-[#333]">·</span>
                <span className="font-FNR text-sm text-[#444] font-semibold">{awayRank}</span>
              </div>
            </div>
          </div>

          {/* Win Probability */}
          {showProb && (
            <div className="mt-8 border-t border-[#242424] pt-8">
              <div className="font-FNR text-xs text-gray-400 font-bold tracking-[0.15em]  mb-4 text-center">Win Probability</div>
              <div className="flex justify-between font-FNR text-[0.7rem] font-bold text-gray-400 mb-1.5">
                <span>{homeCode} {hProb}%</span>
                <span>Draw {dProb}%</span>
                <span>{aProb}% {awayCode}</span>
              </div>
              <div className="flex h-[5px] rounded-[3px] overflow-hidden">
                <div style={{ width: `${hProb}%`, backgroundColor: homeColor }} className="opacity-90" />
                <div style={{ width: `${dProb}%` }} className="bg-[#333]" />
                <div style={{ width: `${aProb}%`, backgroundColor: awayColor }} className="opacity-90" />
              </div>
            </div>
          )}

          {/* Venue */}
          {(stadName || stadCity) && (
            <div className="mt-8 border-t border-[#242424] pt-8">
              <div className="font-FNR text-xs text-gray-400 font-bold tracking-[0.15em]  mb-4 text-center">Venue</div>
              <a href={stadMapsUrl} target="_blank" rel="noopener noreferrer" className="relative border border-[#2a2a2a] rounded-[8px] overflow-hidden h-[200px] block hover:border-white/30 transition-colors">
                {stadPhotoKey ? <div style={{ backgroundImage: `url(${getStadiumPhotoUrl(stadPhotoKey)})` }} className="absolute inset-0 bg-cover bg-center" /> : <div className="absolute inset-0 bg-[#0B0B0B]" />}
                <div className="absolute inset-0 bg-gradient-to-r from-black/95 via-black/70 to-black/5" />
                <div className="relative z-10 px-12 flex flex-col justify-center h-full items-start">
                  <div className="font-FSEB text-[2rem] text-[#F0F0F0] tracking-wider leading-none">{stadName}</div>
                  <div className="font-FNR text-base text-[#666] mt-1 tracking-[0.04em] font-semibold">{stadCity}</div>
                  <div className="font-FNR text-sm text-[#444] mt-0.5 tracking-[0.04em] font-semibold">Capacity {stadCapacity}</div>
                </div>
              </a>
            </div>
          )}

          {/* H2H */}
          {h2h && h2h.available && (
            <div className="mt-8 border-t border-[#242424] pt-8">
              <div className="font-FNR text-xs text-gray-400 font-bold tracking-[0.15em]  mb-4 text-center">Head-To-Head Record</div>
              <div className="flex items-center justify-center gap-3 px-6 py-4 bg-white/2 border border-[#3a3a3a] rounded-[8px]">
                <span className="font-FSEB text-[2.5rem] text-green-400 leading-none">{h2h.home_w}</span>
                <span className="font-FSEB text-xl text-gray-500 leading-none">–</span>
                <span className="font-FSEB text-[2.5rem] text-gray-400 leading-none">{h2h.draws}</span>
                <span className="font-FSEB text-xl text-gray-500 leading-none">–</span>
                <span className="font-FSEB text-[2.5rem] text-red-400 leading-none">{h2h.away_w}</span>
              </div>
              <div className="flex justify-between font-FNR text-[0.7rem] text-[#444] font-bold tracking-wider mt-2 px-1">
                <span>{homeCode}</span><span>DRAW</span><span>{awayCode}</span>
              </div>
            </div>
          )}

          {/* Events — if result exists */}
          {res && events.length > 0 && (
            <div className="mt-8 border-t border-[#242424] pt-8">
              <div className="font-FNR text-xs text-gray-400 font-bold tracking-[0.15em]  mb-4 text-center">Match Events</div>
              {renderEventsTimeline()}
            </div>
          )}

          {/* Key Players — only if no result */}
          {!res && (homePlayers.length > 0 || awayPlayers.length > 0) && (
            <div className="mt-8 border-t border-[#242424] pt-8">
              <div className="font-FNR text-xs text-gray-400 font-bold tracking-[0.15em]  mb-6 text-center">Key Players</div>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <div className="text-[0.8rem] text-gray-500 font-bold tracking-wider mb-2 font-FNR">{homeCode} Players</div>
                  {renderPlayersCol(homePlayers)}
                </div>
                <div>
                  <div className="text-[0.8rem] text-gray-500 font-bold tracking-wider mb-2 font-FNR">{awayCode} Players</div>
                  {renderPlayersCol(awayPlayers)}
                </div>
              </div>
            </div>
          )}

        </div>
      </div>

    </div>
  );
}