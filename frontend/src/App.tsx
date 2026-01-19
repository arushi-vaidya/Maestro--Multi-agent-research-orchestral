import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
// Legacy pages (preserved for backwards compatibility)
import LandingPage from './pages/LandingPage';
import ResearchPage from './pages/ResearchPage';
import CursorGlow from './components/CursorGlow';
// STEP 8: New calm pages
import {
  Landing,
  Hypothesis,
  GraphExplorer,
  Timeline,
  Conflicts,
  Execution,
} from './pages/v2';
import './App.css';

const App: React.FC = () => {
  return (
    <Router>
      <CursorGlow />
      <Routes>
        {/* STEP 8: New calm pages (warm minimalist design) */}
        <Route path="/" element={<Landing />} />
        <Route path="/hypothesis" element={<Hypothesis />} />
        <Route path="/graph" element={<GraphExplorer />} />
        <Route path="/timeline" element={<Timeline />} />
        <Route path="/conflicts" element={<Conflicts />} />
        <Route path="/execution" element={<Execution />} />

        {/* Legacy routes (preserved for backwards compatibility) */}
        <Route path="/legacy" element={<LandingPage />} />
        <Route path="/research" element={<ResearchPage />} />
      </Routes>
    </Router>
  );
};

export default App;
