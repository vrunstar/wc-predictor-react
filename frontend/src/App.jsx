import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Predictions from './pages/Predictions';
import Fixtures from './pages/Fixtures';
import Results from './pages/Results';
import Standings from './pages/Standings';
import Knockouts from './pages/Knockouts';
import Admin from './pages/Admin';
import MatchDetail from './pages/MatchDetail';

function App() {
  return (
    <Router>
      <div className="min-h-screen text-[#F0F0F0] select-none font-inter pb-12 w-full max-w-[100vw] overflow-x-hidden">
        <Navbar />
        {/* Main Content container pushed below fixed navbar */}
        <main className="pt-24 px-4 md:px-8 max-w-[85vw] mx-auto">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/predictions" element={<Predictions />} />
            <Route path="/fixtures" element={<Fixtures />} />
            <Route path="/results" element={<Results />} />
            <Route path="/standings" element={<Standings />} />
            <Route path="/knockouts" element={<Knockouts />} />
            <Route path="/admin" element={<Admin />} />
            <Route path="/match/:matchId" element={<MatchDetail />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
