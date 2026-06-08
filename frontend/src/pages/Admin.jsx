import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import { formatKickoff, stageLabel, getFlagUrl, renderFormSpans } from '../utils/helpers';

export default function Admin() {
  const [fixtures, setFixtures] = useState([]);
  const [ranks, setRanks] = useState({});
  const [forms, setForms] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Form states
  const [secret, setSecret] = useState(() => localStorage.getItem('admin_secret') || '');
  const [homeGoals, setHomeGoals] = useState('');
  const [awayGoals, setAwayGoals] = useState('');
  const [statusMsg, setStatusMsg] = useState(null); // { type: 'ok'|'err', text: '' }
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [fixturesData, ranksData, formsData] = await Promise.all([
          api.getFixturesToday(),
          api.getStandingsRanks(),
          api.getStandingsForm()
        ]);
        setFixtures(fixturesData);
        setRanks(ranksData);
        setForms(formsData);
      } catch (err) {
        console.error(err);
        setError('Failed to load today\'s fixtures for administration.');
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

  // Find first incomplete match today
  const incomplete = fixtures.filter(fx => !fx.results || fx.results.length === 0);
  const currentFx = incomplete[0] || null;

  const handleSubmitResult = async (e) => {
    e.preventDefault();
    if (!secret) {
      setStatusMsg({ type: 'err', text: 'Admin secret is required' });
      return;
    }
    if (!currentFx) {
      setStatusMsg({ type: 'err', text: 'No match available to update' });
      return;
    }
    if (homeGoals === '' || awayGoals === '') {
      setStatusMsg({ type: 'err', text: 'Enter goals for both teams' });
      return;
    }

    try {
      setSubmitting(true);
      setStatusMsg(null);
      
      const res = await api.submitResult(
        currentFx.match_id, 
        parseInt(homeGoals), 
        parseInt(awayGoals), 
        secret
      );
      
      setStatusMsg({ type: 'ok', text: res.message || 'Result saved. ELO & standings updated successfully.' });
      
      // Reload fixtures to reflect updates
      const updatedFixtures = await api.getFixturesToday();
      setFixtures(updatedFixtures);
      setHomeGoals('');
      setAwayGoals('');
    } catch (err) {
      console.error(err);
      setStatusMsg({ type: 'err', text: err.message || 'Failed to submit result.' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleRunPredictions = async () => {
    if (!secret) {
      setStatusMsg({ type: 'err', text: 'Admin secret is required' });
      return;
    }

    try {
      setSubmitting(true);
      setStatusMsg(null);
      
      const res = await api.runPredictions(secret);
      
      setStatusMsg({ type: 'ok', text: res.message || `Predictions generated for today's matches.` });
    } catch (err) {
      console.error(err);
      setStatusMsg({ type: 'err', text: err.message || 'Failed to run predictions.' });
    } finally {
      setSubmitting(false);
    }
  };

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

  return (
    <div className="max-w-[500px] mx-auto flex flex-col gap-6">
      {/* Title */}
      <h1 className="font-champion text-[5rem] tracking-wider text-[#F0F0F0] leading-none mb-2 text-center">
        ADMIN
      </h1>

      {/* Incomplete Match display */}
      {!currentFx ? (
        <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-6 text-center text-gray-500 font-inter text-[0.85rem]">
          No incomplete matches today
        </div>
      ) : (
        <div className="bg-[#091424] border border-[#242424]/40 rounded-[10px] p-[1.1rem_1.4rem]">
          {/* Match Row */}
          <div className="grid grid-cols-[30px_1fr_auto_1fr_30px] items-center gap-[0.6rem] w-full">
            <div className="flex items-center justify-center">
              <img
                src={getFlagUrl(homeCode)}
                alt={`${homeCode} Flag`}
                className="w-[26px] h-auto object-contain border border-[#1e1e1e]"
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            </div>
            <div className="font-champion text-2xl tracking-wider text-[#F0F0F0] leading-none">
              {homeCode}
            </div>
            <div className="text-center min-w-[90px]">
              <span className="font-inter text-xl font-extrabold text-white tracking-widest leading-none">
                {koTime}
              </span>
            </div>
            <div className="font-champion text-2xl tracking-wider text-[#F0F0F0] leading-none text-right">
              {awayCode}
            </div>
            <div className="flex items-center justify-center">
              <img
                src={getFlagUrl(awayCode)}
                alt={`${awayCode} Flag`}
                className="w-[26px] h-auto object-contain border border-[#1e1e1e]"
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            </div>
          </div>

          {/* Metadata Subrow */}
          <div className="grid grid-cols-[1fr_auto_1fr] items-center mt-[0.7rem] pt-[0.6rem] border-t border-[#3a3a3a] text-[0.75rem] font-inter text-gray-400">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-500">{homeRank}</span>
              {renderFormSpans(homeForm)}
            </div>
            <div className="text-center text-[#999]">
              Match {currentFx.match_id} &middot; {matchStage} {venue && `· ${venue}`}
            </div>
            <div className="flex items-center gap-2 justify-end">
              {renderFormSpans(awayForm)}
              <span className="font-semibold text-gray-500">{awayRank}</span>
            </div>
          </div>

          {/* Score Input Form */}
          <form onSubmit={handleSubmitResult} className="mt-4 flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-[0.7rem] text-[#999] uppercase tracking-wider font-semibold font-inter">
                  Home Goals ({homeCode})
                </label>
                <input
                  type="number"
                  min="0"
                  placeholder="0"
                  value={homeGoals}
                  onChange={(e) => setHomeGoals(e.target.value)}
                  className="bg-[#0d0d0d] border border-[#242424]/40 text-white px-3 py-2 rounded-[8px] focus:outline-none focus:border-white/25 text-center font-inter"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-[0.7rem] text-[#999] uppercase tracking-wider font-semibold font-inter">
                  Away Goals ({awayCode})
                </label>
                <input
                  type="number"
                  min="0"
                  placeholder="0"
                  value={awayGoals}
                  onChange={(e) => setAwayGoals(e.target.value)}
                  className="bg-[#0d0d0d] border border-[#242424]/40 text-white px-3 py-2 rounded-[8px] focus:outline-none focus:border-white/25 text-center font-inter"
                />
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Secret Input */}
      <div className="flex flex-col gap-1 w-full mt-2">
        <input
          type="password"
          placeholder="Admin Secret"
          value={secret}
          onChange={handleSecretChange}
          className="bg-[#0d0d0d] border border-[#242424]/40 text-white px-4 py-2.5 rounded-[8px] focus:outline-none focus:border-white/25 text-center font-inter placeholder-gray-500"
        />
      </div>

      {/* Status Messages */}
      {statusMsg && (
        <div 
          className={`border rounded-[8px] p-[10px_14px] font-inter text-[0.85rem] ${
            statusMsg.type === 'ok' 
              ? 'bg-[#4CAF50]/10 border-[#4CAF50]/25 text-[#81c784]' 
              : 'bg-[#F44336]/10 border-[#F44336]/25 text-[#e57373]'
          }`}
        >
          {statusMsg.text}
        </div>
      )}

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-4 mt-2">
        <button
          onClick={handleSubmitResult}
          disabled={submitting || !currentFx}
          className="bg-white text-black hover:bg-neutral-200 disabled:opacity-50 disabled:bg-white/50 disabled:text-black/50 rounded-[8px] p-3 font-semibold text-sm tracking-wider uppercase font-inter transition-all duration-150 shadow"
        >
          {submitting ? 'Submitting...' : 'SUBMIT RESULT'}
        </button>
        <button
          onClick={handleRunPredictions}
          disabled={submitting}
          className="bg-[#091424] border border-[#242424]/40 hover:border-white/50 hover:text-white text-[#aaa] disabled:opacity-50 rounded-[8px] p-3 font-semibold text-sm tracking-wider uppercase font-inter transition-all duration-150"
        >
          {submitting ? 'Generating...' : 'RUN PREDICTIONS'}
        </button>
      </div>
    </div>
  );
}
