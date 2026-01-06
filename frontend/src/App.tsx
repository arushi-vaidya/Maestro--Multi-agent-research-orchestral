import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import ResearchPage from './pages/ResearchPage';
import CursorGlow from './components/CursorGlow';
import './App.css';

const App: React.FC = () => {
  return (
    <Router>
      <CursorGlow />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/research" element={<ResearchPage />} />
      </Routes>
    </Router>
  );
};

export default App;
