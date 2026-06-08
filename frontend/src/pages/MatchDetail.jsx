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
  const [kitColors, setKitColors] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        // Fetch baseline data
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

        // Fetch H2H, stadium, and players in parallel
        const [h2hData, stadiumData, homePlayersData, awayPlayersData] = await Promise.all([
          api.getH2H(home.team_code, away.team_code),
          fixtureData.city ? api.getStadium(fixtureData.city) : Promise.resolve({}),
          home.team_id ? api.getPlayers(home.team_id) : Promise.resolve([]),
          away.team_id ? api.getPlayers(away.team_id) : Promise.resolve([])
        ]);

        setH2h(h2hData);
        setStadium(stadiumData);
        setHomePlayers(homePlayersData);
        setAwayPlayers(awayPlayersData);
      } catch (err) {
        console.error(err);
        setError('Failed to load match details.');
      } finally {
        setLoading(false);
      }
    }
    
    if (matchId) {
      loadData();
    }
  }, [matchId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-white"></div>
      </div>
    );
  }

  if (error || !fixture) {
    return (
      <div className="text-center py-24 bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6">
        <div className="text-red-500 text-lg mb-2">⚠️ {error || 'Match not found'}</div>
        <Link 
          to="/fixtures"
          className="px-4 py-2 bg-white text-black font-semibold rounded hover:bg-neutral-200"
        >
          Back to Fixtures
        </Link>
      </div>
    );
  }

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

  // Score display logic
  let scoreHtml = null;
  if (res) {
    const pHome = prediction?.pred_home_goals ?? '?';
    const pAway = prediction?.pred_away_goals ?? '?';
    scoreHtml = (
      <div className="flex flex-col items-center">
        <div className="font-champion text-[3rem] text-white tracking-widest leading-none select-none">
          {res.home_goals} – {res.away_goals}
        </div>
        <div className="font-inter text-[0.75rem] text-gray-500 mt-1 uppercase tracking-wider font-semibold">
          ({pHome}–{pAway} pred)
        </div>
      </div>
    );
  } else if (prediction) {
    const conf = Math.round((prediction.model_confidence || 0) * 100);
    scoreHtml = (
      <div className="flex flex-col items-center">
        <div className="font-champion text-[3rem] text-white tracking-widest leading-none select-none">
          {prediction.pred_home_goals} – {prediction.pred_away_goals}
        </div>
        <div className="font-inter text-[0.75rem] text-gray-400 mt-1 uppercase tracking-wider font-semibold">
          {conf}% confidence
        </div>
      </div>
    );
  } else {
    scoreHtml = (
      <div className="flex flex-col items-center">
        <div className="font-champion text-3xl text-white tracking-widest leading-none select-none">
          {koTime}
        </div>
        <div className="font-inter text-[0.62rem] text-gray-500 mt-1 uppercase tracking-[0.14em] font-black">
          IST
        </div>
      </div>
    );
  }

  // Kit Colors lookup for Probability bar
  const homeColor = kitColors[homeCode]?.home || '#FFFFFF'; // default white
  const awayColor = kitColors[awayCode]?.away || '#888888'; // default grey

  // Win probability calculation
  const showProb = prediction && !res;
  const hProb = showProb ? Math.round((prediction.home_win_prob || 0) * 100) : 0;
  const dProb = showProb ? Math.round((prediction.draw_prob || 0) * 100) : 0;
  const aProb = showProb ? 100 - hProb - dProb : 0; // ensure sum is exactly 100

  // Stadium photo path
  const stadPhotoKey = stadium.photo_key || '';
  const stadName = stadium.name || fixture.venue || 'TBD';
  const stadCity = stadium.city || fixture.city || '';
  const stadCapacity = stadium.capacity ? stadium.capacity.toLocaleString() : '—';

  // Render players columns
  const renderPlayersCol = (players, code) => {
    if (!players || players.length === 0) {
      return <div className="text-[#333] text-[0.78rem] font-medium">—</div>;
    }
    return (
      <div className="flex flex-col gap-2.5">
        {players.map((p) => {
          const photoUrl = getPlayerPhotoUrl(p.photo_key);
          return (
            <div 
              key={p.player_id}
              className="flex items-center gap-3 bg-white/2 border border-[#3a3a3a] rounded-[8px] p-2"
            >
              {photoUrl ? (
                <img 
                  src={photoUrl} 
                  alt={p.full_name}
                  className="w-[36px] h-[36px] rounded-full object-cover border border-[#2a2a2a] shrink-0"
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
              ) : (
                <div className="w-[36px] h-[36px] rounded-full bg-[#141414] border border-[#2a2a2a] flex items-center justify-center shrink-0 font-champion text-[0.8rem] text-gray-500">
                  {p.number}
                </div>
              )}
              <div className="flex flex-col">
                <div className="font-inter text-base font-semibold text-[#e0e0e0] tracking-[0.04em]">
                  {p.full_name}
                </div>
                <div className="font-inter text-[0.9rem] font-semibold text-gray-500 text-left tracking-[0.08em] mt-0.5">
                  {p.number} &middot; {p.position}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="flex flex-col gap-4">
      
      {/* Header and Back Button */}
      <div className="flex items-center justify-center my-2 relative">
        <div className="font-champion text-3xl tracking-wider text-[#F0F0F0] leading-none flex items-baseline justify-center gap-4 text-center">
          MATCH {matchId}
          <span className="font-inter text-sm font-extrabold text-gray-400 tracking-widest uppercase">
            {matchStage} &middot; {koTime} IST
          </span>
        </div>
        <button 
          onClick={() => navigate(-1)}
          className="absolute right-0 flex items-center justify-center w-8 h-8 bg-[#091424] border border-[#242424]/40 hover:border-white/50 hover:text-white rounded-[6px] text-gray-500 font-inter text-xs font-bold transition-all duration-150"
        >
          ✕
        </button>
      </div>

      {/* Main Glass Card */}
      <div className="bg-[#091424] border border-[#242424]/40 rounded-[12px] p-6 md:p-12">
        
        {/* Teams row */}
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] items-center gap-6 md:gap-12 w-full">
          
          {/* Home Team */}
          <div className="flex flex-col items-center md:items-start">
            <div className="flex items-center gap-3">
              <img 
                src={getFlagUrl(homeCode)} 
                alt={`${homeCode} Flag`} 
                className="w-[45px] h-auto object-contain border border-[#1e1e1e]"
                onError={(e) => { e.target.style.display = 'none'; }}
              />
              <span className="font-champion text-[2rem] tracking-wider text-[#F0F0F0] leading-none select-none">
                {homeCode}
              </span>
            </div>
            <div className="font-inter text-[1.25rem] text-[#666] mt-1.5 font-medium">{homeName}</div>
            <div className="flex items-center gap-2 mt-1">
              <span className="font-inter text-sm text-[#444] font-semibold">{homeRank}</span>
              <span className="font-inter text-sm text-[#333]">&middot;</span>
              {renderFormSpans(homeForm)}
            </div>
          </div>

          {/* Score / Time Center */}
          <div className="flex justify-center">{scoreHtml}</div>

          {/* Away Team */}
          <div className="flex flex-col items-center md:items-end">
            <div className="flex items-center gap-3 justify-end">
              <span className="font-champion text-[2rem] tracking-wider text-[#F0F0F0] leading-none select-none">
                {awayCode}
              </span>
              <img 
                src={getFlagUrl(awayCode)} 
                alt={`${awayCode} Flag`} 
                className="w-[45px] h-auto object-contain border border-[#1e1e1e]"
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            </div>
            <div className="font-inter text-[1.25rem] text-[#666] mt-1.5 font-medium">{awayName}</div>
            <div className="flex items-center gap-2 mt-1 justify-end">
              {renderFormSpans(awayForm)}
              <span className="font-inter text-sm text-[#333]">&middot;</span>
              <span className="font-inter text-sm text-[#444] font-semibold">{awayRank}</span>
            </div>
          </div>
        </div>

        {/* Win Probability Bar */}
        {showProb && (
          <div className="mt-8 border-t border-[#242424] pt-8">
            <div className="font-inter text-xs text-gray-400 font-bold tracking-[0.15em] uppercase mb-4 text-center">
              Win Probability
            </div>
            <div className="flex justify-between font-inter text-[0.7rem] font-bold text-gray-400 mb-1.5">
              <span>{homeCode} {hProb}%</span>
              <span>Draw {dProb}%</span>
              <span>{aProb}% {awayCode}</span>
            </div>
            <div className="flex h-[5px] rounded-[3px] overflow-hidden">
              <div style={{ width: `${hProb}%`, backgroundColor: homeColor }} className="opacity-90"></div>
              <div style={{ width: `${dProb}%` }} className="bg-[#333]"></div>
              <div style={{ width: `${aProb}%`, backgroundColor: awayColor }} className="opacity-90"></div>
            </div>
          </div>
        )}

        {/* Stadium Card */}
        {(stadName || stadCity) && (
          <div className="mt-8 border-t border-[#242424] pt-8">
            <div className="font-inter text-xs text-gray-400 font-bold tracking-[0.15em] uppercase mb-4 text-center">
              Venue
            </div>
            <div className="relative border border-[#2a2a2a] rounded-[8px] overflow-hidden h-[200px]">
              {stadPhotoKey ? (
                <div 
                  style={{ backgroundImage: `url(${getStadiumPhotoUrl(stadPhotoKey)})` }} 
                  className="absolute inset-0 bg-cover bg-center"
                />
              ) : (
                <div className="absolute inset-0 bg-[#0B0B0B]" />
              )}
              <div className="absolute inset-0 bg-gradient-to-r from-black/95 via-black/80 to-black/5 md:via-black/70 md:from-black/95"></div>
              <div className="relative z-10 px-8 md:px-12 flex flex-col justify-center h-full items-start">
                <div className="font-champion text-[2rem] text-[#F0F0F0] tracking-wider leading-none">
                  {stadName}
                </div>
                <div className="font-inter text-base text-[#666] mt-1 tracking-[0.04em] font-semibold">
                  {stadCity}
                </div>
                <div className="font-inter text-sm text-[#444] mt-0.5 tracking-[0.04em] font-semibold">
                  Capacity {stadCapacity}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* H2H Stats */}
        {h2h && h2h.available && (
          <div className="mt-8 border-t border-[#242424] pt-8">
            <div className="font-inter text-xs text-gray-400 font-bold tracking-[0.15em] uppercase mb-4 text-center">
              Head-To-Head Record
            </div>
            <div className="grid grid-cols-[1fr_auto_auto_auto_1fr] items-center gap-6 px-8 py-3 bg-white/2 border border-[#3a3a3a] rounded-[8px]">
              <span className="font-champion text-[2rem] text-[#F0F0F0] text-left">
                {homeCode}
              </span>
              <span className="font-champion text-[2rem] text-[#F0f0f0] leading-none">
                {h2h.home_w}
              </span>
              <span className="font-champion text-xl text-gray-500 leading-none px-2">
                &middot; {h2h.draws} &middot;
              </span>
              <span className="font-champion text-[2rem] text-[#F0f0f0] leading-none">
                {h2h.away_w}
              </span>
              <span className="font-champion text-[2rem] text-[#F0F0F0] text-right">
                {awayCode}
              </span>
            </div>
          </div>
        )}

        {/* Key Players */}
        {(homePlayers.length > 0 || awayPlayers.length > 0) && (
          <div className="mt-8 border-t border-[#242424] pt-8">
            <div className="font-inter text-xs text-gray-400 font-bold tracking-[0.15em] uppercase mb-6 text-center">
              Key Players
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <div className="text-[0.8rem] text-gray-500 font-bold tracking-wider mb-2 font-inter">
                  {homeCode} Players
                </div>
                {renderPlayersCol(homePlayers, homeCode)}
              </div>
              <div>
                <div className="text-[0.8rem] text-gray-500 font-bold tracking-wider mb-2 font-inter text-right md:text-left">
                  {awayCode} Players
                </div>
                {renderPlayersCol(awayPlayers, awayCode)}
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
