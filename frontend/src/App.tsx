import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
// Legacy pages (preserved for backwards compatibility)
import LandingPage from './pages/LandingPage';
import ResearchPage from './pages/ResearchPage';
import Navbar from './components/Navbar';
// STEP 8: New calm pages
import {
  Landing,
  Hypothesis,
  GraphExplorer,
  Timeline,
  Conflicts,
  Execution,
  ConfidenceScoring,
} from './pages/v2';
// Query context for cross-page state management
import { QueryProvider } from './context/QueryContext';
import './App.css';

const AppContent: React.FC = () => {
  const location = useLocation();
  const isLegacyRoute = location.pathname.startsWith('/legacy') || location.pathname === '/research';

  return (
    <>
      {!isLegacyRoute && <Navbar />}
      <Routes>
        {/* STEP 8: New calm pages (warm minimalist design) */}
        <Route path="/" element={<Landing />} />
        <Route path="/hypothesis" element={<Hypothesis />} />
        <Route path="/graph" element={<GraphExplorer />} />
        <Route path="/timeline" element={<Timeline />} />
        <Route path="/conflicts" element={<Conflicts />} />
        <Route path="/execution" element={<Execution />} />
        <Route path="/confidence" element={<ConfidenceScoring />} />

        {/* Legacy routes (preserved for backwards compatibility) */}
        <Route path="/legacy" element={<LandingPage />} />
        <Route path="/research" element={<ResearchPage />} />
      </Routes>
    </>
  );
};

const App: React.FC = () => {
  return (
    <QueryProvider>
      <Router>
        <AppContent />
      </Router>
    </QueryProvider>
  );
};

export default App;
