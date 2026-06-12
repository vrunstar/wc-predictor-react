import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import { formatKickoff, stageLabel, getFlagUrl, renderFormSpans } from '../utils/helpers';

const EVENT_TYPES = ['Goal', 'Own_Goal', 'Penalty', 'Yellow_Card', 'Red_Card', 'Injury'];

export default function Admin() {
  const [fixtures, setFixtures] = useState([]);
  const [ranks, setRanks] = useState({});
  const [forms, setForms] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [secret, setSecret] = useState(() => localStorage.getItem('admin_secret') || '');
  const [selectedMatchId, setSelectedMatchId] = useState(null);

  const [homeGoals, setHomeGoals] = useState('');
  const [awayGoals, setAwayGoals] = useState('');
  const [statusMsg, setStatusMsg] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Local event being built
  const [eventTeamId, setEventTeamId] = useState('');
  const [eventPlayer, setEventPlayer] = useState('');
  const [eventType, setEventType] = useState('goal');
  const [eventTime, setEventTime] = useState('');

  // Local list of events (not yet saved)
  const [pendingEvents, setPendingEvents] = useState([]);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [fixturesData, ranksData, formsData] = await Promise.all([
          api.getFixturesAdminPending(),
          api.getStandingsRanks(),
          api.getStandingsForm()
        ]);
        setFixtures(fixturesData);
        setRanks(ranksData);
        setForms(formsData);

        const incomplete = fixturesData.filter(fx => !fx.results || (Array.isArray(fx.results) && fx.results.length === 0));
        if (incomplete.length > 0) setSelectedMatchId(incomplete[0].match_id);
        else if (fixturesData.length > 0) setSelectedMatchId(fixturesData[0].match_id);
      } catch (err) {
        console.error(err);
        setError('Failed to load today\'s fixtures.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleSecretChange = (e) => {
    const val = e.target.value;
    setSecret(val);
    localStorage.setItem('admin_secret', val);
  };

  const currentFx = fixtures.find(fx => fx.match_id === selectedMatchId) || null;
  const home = currentFx?.home || {};
  const away = currentFx?.away || {};
  const homeCode = home.team_code || '???';
  const awayCode = away.team_code || '???';
  const homeRank = ranks[home.team_id] || '—';
  const awayRank = ranks[away.team_id] || '—';
  const homeForm = forms[home.team_id] || '';
  const awayForm = forms[away.team_id] || '';
  const koTime = currentFx ? formatKickoff(currentFx.kickoff_ist) : 'TBD';
  const venue = currentFx?.venue || currentFx?.city || '';
  const matchStage = currentFx ? stageLabel(currentFx.stage, currentFx.group_name) : '';

  const matchTeams = currentFx ? [
    { id: home.team_id, code: homeCode },
    { id: away.team_id, code: awayCode }
  ] : [];

  const handleMatchChange = (e) => {
    setSelectedMatchId(parseInt(e.target.value));
    setHomeGoals('');
    setAwayGoals('');
    setPendingEvents([]);
    setEventTeamId('');
    setEventPlayer('');
    setEventTime('');
    setStatusMsg(null);
  };

  const handleAddEvent = () => {
    if (!eventTeamId || !eventPlayer.trim()) return;
    setPendingEvents(prev => [...prev, {
      team_id: parseInt(eventTeamId),
      team_code: matchTeams.find(t => t.id === parseInt(eventTeamId))?.code || '',
      player: eventPlayer.trim(),
      event: eventType,
      time: eventTime.trim() || null
    }]);
    setEventPlayer('');
    setEventTime('');
  };

  const handleRemoveEvent = (index) => {
    setPendingEvents(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (!secret) { setStatusMsg({ type: 'err', text: 'Admin secret is required' }); return; }
    if (!currentFx) { setStatusMsg({ type: 'err', text: 'No match selected' }); return; }
    if (homeGoals === '' || awayGoals === '') { setStatusMsg({ type: 'err', text: 'Enter goals for both teams' }); return; }

    try {
      setSubmitting(true);
      setStatusMsg(null);

      const res = await api.submitResult(
        currentFx.match_id,
        parseInt(homeGoals),
        parseInt(awayGoals),
        secret
      );

      for (const ev of pendingEvents) {
        await api.addEvent({
          match_id: currentFx.match_id,
          team_code: ev.team_code,
          player: ev.player,
          event: ev.event,
          time: ev.time
        }, secret);
      }

      setStatusMsg({ type: 'ok', text: res.message || `Result + ${pendingEvents.length} event(s) saved.` });

      const updatedFixtures = await api.getFixturesToday();
      setFixtures(updatedFixtures);
      setHomeGoals('');
      setAwayGoals('');
      setPendingEvents([]);
    } catch (err) {
      console.error(err);
      setStatusMsg({ type: 'err', text: err.message || 'Failed to submit.' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleRunPredictions = async () => {
    if (!secret) { setStatusMsg({ type: 'err', text: 'Admin secret is required' }); return; }
    try {
      setSubmitting(true);
      setStatusMsg(null);
      const res = await api.runPredictions(secret);
      setStatusMsg({ type: 'ok', text: res.message || `Predictions generated.` });
    } catch (err) {
      setStatusMsg({ type: 'err', text: err.message || 'Failed to run predictions.' });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center py-24">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-white"></div>
    </div>
  );

  if (error) return (
    <div className="text-center py-24 bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6">
      <div className="text-red-500 text-lg mb-2">{error}</div>
      <button onClick={() => window.location.reload()} className="px-4 py-2 bg-white text-black font-semibold rounded">Retry</button>
    </div>
  );

  return (
    <div className="max-w-[800px] mx-auto flex flex-col gap-6">
      <h1 className="font-hm_text text-[5rem] tracking-wider text-[#F0F0F0] leading-none mb-2 text-center">ADMIN</h1>

      {/* Match selector */}
      <div className="flex flex-col gap-1">
        <label className="text-[0.7rem] text-[#999] tracking-wider font-medium font-inter">Select Match</label>
        <select
          value={selectedMatchId ?? ''}
          onChange={handleMatchChange}
          className="bg-[#0d0d0d] border border-[#242424]/40 text-white px-3 py-2 rounded-[8px] focus:outline-none focus:border-white/25 font-inter text-sm"
        >
          {fixtures.map(fx => {
            const hasResult = fx.results && (!Array.isArray(fx.results) || fx.results.length > 0);
            const label = `#${fx.match_id} · ${fx.home?.team_code || '???'} vs ${fx.away?.team_code || '???'} · ${formatKickoff(fx.kickoff_ist)}${hasResult ? ' (completed)' : ''}`;
            return <option key={fx.match_id} value={fx.match_id}>{label}</option>;
          })}
        </select>
      </div>

      {/* Current Match */}
      {!currentFx ? (
        <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6 text-center text-gray-500 font-inter text-[0.85rem]">
          No match selected
        </div>
      ) : (
        <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-[1.1rem_1.4rem] flex flex-col gap-4">

          {/* Match header */}
          <div className="grid grid-cols-[30px_1fr_auto_1fr_30px] items-center gap-[0.6rem]">
            <img src={getFlagUrl(homeCode)} alt={homeCode} className="w-[26px] h-auto object-contain border border-[#1e1e1e]" onError={(e) => { e.target.style.display = 'none'; }} />
            <div className="font-hm_text text-2xl tracking-wider text-[#F0F0F0] leading-none">{homeCode}</div>
            <div className="text-center min-w-[90px]">
              <span className="font-inter text-xl font-extrabold text-white tracking-widest">{koTime}</span>
            </div>
            <div className="font-hm_text text-2xl tracking-wider text-[#F0F0F0] leading-none text-right">{awayCode}</div>
            <img src={getFlagUrl(awayCode)} alt={awayCode} className="w-[26px] h-auto object-contain border border-[#1e1e1e] justify-self-end" onError={(e) => { e.target.style.display = 'none'; }} />
          </div>

          {/* Meta */}
          <div className="grid grid-cols-[1fr_auto_1fr] items-center pt-[0.6rem] border-t border-[#3a3a3a] text-[0.75rem] font-inter text-gray-400">
            <div className="text-center text-[#999]">Match {currentFx.match_id} · {matchStage} {venue && `· ${venue}`}</div>
          </div>

          {/* Goals input */}
          <div className="grid grid-cols-2 gap-4 pt-2 border-t border-[#1e1e1e]">
            <div className="flex flex-col gap-1">
              <label className="text-[0.7rem] text-[#999] uppercase tracking-wider font-semibold font-inter">Home Goals ({homeCode})</label>
              <input type="number" min="0" placeholder="0" value={homeGoals} onChange={(e) => setHomeGoals(e.target.value)}
                className="bg-[#0d0d0d] border border-[#242424]/40 text-white px-3 py-2 rounded-[8px] focus:outline-none focus:border-white/25 text-center font-inter" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[0.7rem] text-[#999] uppercase tracking-wider font-semibold font-inter">Away Goals ({awayCode})</label>
              <input type="number" min="0" placeholder="0" value={awayGoals} onChange={(e) => setAwayGoals(e.target.value)}
                className="bg-[#0d0d0d] border border-[#242424]/40 text-white px-3 py-2 rounded-[8px] focus:outline-none focus:border-white/25 text-center font-inter" />
            </div>
          </div>

          {/* Events builder */}
          <div className="flex flex-col gap-3 pt-2 border-t border-[#1e1e1e]">
            <div className="font-inter text-[0.65rem] text-gray-500 font-bold tracking-[0.15em] uppercase">Add Events</div>

            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1">
                <label className="text-[0.7rem] text-[#999] uppercase tracking-wider font-semibold font-inter">Team</label>
                <select value={eventTeamId} onChange={(e) => setEventTeamId(e.target.value)}
                  className="bg-[#0d0d0d] border border-[#242424]/40 text-white px-3 py-2 rounded-[8px] focus:outline-none focus:border-white/25 font-inter text-sm">
                  <option value="">Select</option>
                  {matchTeams.map(t => (
                    <option key={t.id} value={t.id}>{t.code}</option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-[0.7rem] text-[#999] tracking-wider font-semibold font-inter">Event</label>
                <select value={eventType} onChange={(e) => setEventType(e.target.value)}
                  className="bg-[#0d0d0d] border border-[#242424]/40 text-white px-3 py-2 rounded-[8px] focus:outline-none focus:border-white/25 font-inter text-sm">
                  {EVENT_TYPES.map(t => (
                    <option key={t} value={t}>{t.replace('_', ' ')}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-[1fr_80px] gap-3">
              <div className="flex flex-col gap-1">
                <label className="text-[0.7rem] text-[#999] tracking-wider font-semibold font-inter">Player</label>
                <input type="text" placeholder="Player" value={eventPlayer} onChange={(e) => setEventPlayer(e.target.value)}
                  className="bg-[#0d0d0d] border border-[#242424]/40 text-white px-3 py-2 rounded-[8px] focus:outline-none focus:border-white/25 font-inter text-sm placeholder-gray-600" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-[0.7rem] text-[#999] tracking-wider font-semibold font-inter">Minute</label>
                <input type="text" placeholder="0" value={eventTime} onChange={(e) => setEventTime(e.target.value)}
                  className="bg-[#0d0d0d] border border-[#242424]/40 text-white px-3 py-2 rounded-[8px] focus:outline-none focus:border-white/25 text-center font-inter text-sm" />
              </div>
            </div>

            <button onClick={handleAddEvent} disabled={!eventTeamId || !eventPlayer.trim()}
              className="bg-[#091424] border border-[#242424]/40 hover:border-white/50 hover:text-white text-[#aaa] disabled:opacity-30 rounded-[8px] p-2.5 font-semibold text-sm tracking-wider uppercase font-inter transition-all duration-150">
              + Add to List
            </button>
          </div>

          {/* Pending events list */}
          {pendingEvents.length > 0 && (
            <div className="flex flex-col gap-2 pt-2 border-t border-[#1e1e1e]">
              <div className="font-inter text-[0.65rem] text-gray-500 font-bold tracking-[0.12em] uppercase">Pending Events ({pendingEvents.length})</div>
              {pendingEvents.map((ev, i) => (
                <div key={i} className="flex items-center justify-between bg-white/2 border border-[#2a2a2a] rounded-[6px] px-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className="font-inter text-xs font-bold text-gray-400">{ev.team_code}</span>
                    <span className="font-inter text-sm text-[#e0e0e0] font-medium flex items-center gap-1">
                      {ev.player}
                      {ev.event === 'penalty' && ' (p)'}
                      {ev.event === 'own_goal' && ' (og)'}
                      {ev.event === 'yellow_card' && <span className="inline-block w-2.5 h-3.5 bg-yellow-400 rounded-[1px]"></span>}
                      {ev.event === 'red_card' && <span className="inline-block w-2.5 h-3.5 bg-red-500 rounded-[1px]"></span>}
                    </span>
                    <span className="font-inter text-xs text-gray-500">{ev.event.replace('_', ' ')}</span>
                    {ev.time && <span className="font-inter text-xs text-gray-600">{ev.time}'</span>}
                  </div>
                  <button onClick={() => handleRemoveEvent(i)} className="text-[#444] hover:text-red-400 font-inter text-xs font-bold transition-colors px-1">x</button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Secret */}
      <input type="password" placeholder="Admin Secret" value={secret} onChange={handleSecretChange}
        className="bg-[#0d0d0d] border border-[#242424]/40 text-white px-4 py-2.5 rounded-[8px] focus:outline-none focus:border-white/25 text-center font-inter placeholder-gray-500" />

      {/* Status */}
      {statusMsg && (
        <div className={`border rounded-[8px] p-[10px_14px] font-inter text-[0.85rem] ${statusMsg.type === 'ok' ? 'bg-[#4CAF50]/10 border-[#4CAF50]/25 text-[#81c784]' : 'bg-[#F44336]/10 border-[#F44336]/25 text-[#e57373]'}`}>
          {statusMsg.text}
        </div>
      )}

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-4">
        <button onClick={handleSubmit} disabled={submitting || !currentFx}
          className="bg-white text-black hover:bg-neutral-200 disabled:opacity-50 rounded-[8px] p-3 font-semibold text-sm tracking-wider uppercase font-inter transition-all duration-150">
          {submitting ? 'Submitting...' : 'SUBMIT RESULT'}
        </button>
        <button onClick={handleRunPredictions} disabled={submitting}
          className="bg-[#091424] border border-[#242424]/40 hover:border-white/50 hover:text-white text-[#aaa] disabled:opacity-50 rounded-[8px] p-3 font-semibold text-sm tracking-wider uppercase font-inter transition-all duration-150">
          {submitting ? 'Generating...' : 'RUN PREDICTIONS'}
        </button>
      </div>
    </div>
  );
}