const API_BASE = `${import.meta.env.VITE_API_URL || ''}/api`;

async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  getTeams: () => fetchJson(`${API_BASE}/teams`),
  getTeam: (id) => fetchJson(`${API_BASE}/teams/${id}`),
  getFixturesToday: () => fetchJson(`${API_BASE}/fixtures/matchday`),
  getFixturesUpcoming: () => fetchJson(`${API_BASE}/fixtures/upcoming`),
  getFixturesGroup: () => fetchJson(`${API_BASE}/fixtures/group`),
  getFixturesByStage: (stage) => fetchJson(`${API_BASE}/fixtures/stage/${stage}`),
  getFixture: (id) => fetchJson(`${API_BASE}/fixtures/${id}`),
  getPredictions: () => fetchJson(`${API_BASE}/predictions`),
  getPredictionsMap: () => fetchJson(`${API_BASE}/predictions/map`),
  getPredictionsToday: () => fetchJson(`${API_BASE}/predictions/today`),
  getResults: () => fetchJson(`${API_BASE}/results`),
  getResultsMap: () => fetchJson(`${API_BASE}/results/map`),
  getStandings: () => fetchJson(`${API_BASE}/standings`),
  getStandingsGroup: (group) => fetchJson(`${API_BASE}/standings/group/${group}`),
  getStandingsRanks: () => fetchJson(`${API_BASE}/standings/ranks`),
  getStandingsForm: () => fetchJson(`${API_BASE}/standings/form`),
  getStadium: (city) => fetchJson(`${API_BASE}/stadiums/${encodeURIComponent(city)}`),
  getPlayers: (teamId) => fetchJson(`${API_BASE}/players/${teamId}`),
  getH2H: (homeCode, awayCode) => fetchJson(`${API_BASE}/h2h/${homeCode}/${awayCode}`),
  getKitColors: () => fetchJson(`${API_BASE}/kit-colors`),
  getMatchEvents: (matchId) => fetchJson(`${API_BASE}/fixtures/${matchId}/events`),

  verifySecret: (secret) => fetchJson(`${API_BASE}/auth/verify-secret`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ secret })
  }),
  
  submitResult: (matchId, homeGoals, awayGoals, secret) => fetchJson(`${API_BASE}/admin/submit-result`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ match_id: matchId, home_goals: homeGoals, away_goals: awayGoals, secret })
  }),
  
  runPredictions: (secret) => fetchJson(`${API_BASE}/admin/run-predictions`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${secret}` }
  }),

  addEvent: (event, secret) => fetchJson(`${API_BASE}/admin/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${secret}` },
    body: JSON.stringify(event)
  }),

  deleteEvent: (eventId, secret) => fetchJson(`${API_BASE}/admin/events/${eventId}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${secret}` }
  }),
};
