/**
 * Landing Page - Enhanced Design
 * Modern, professional pharmaceutical intelligence platform
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Database, Activity, FileText, Network, Shield, Zap } from 'lucide-react';
import { PageContainer, CalmButton, CalmCard } from '../../components/calm';

export const Landing: React.FC = () => {
  const navigate = useNavigate();

  return (
    <PageContainer maxWidth="lg">
      {/* Hero Section */}
      <div className="text-center mb-24 animate-calm-fade-in">
        <div className="mb-6 inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-terracotta-500 to-terracotta-600 rounded-2xl shadow-xl">
          <FileText className="w-10 h-10 text-white" />
        </div>
        <h1 className="text-6xl font-bold text-warm-text mb-6 font-inter tracking-tight">
          MAESTRO
        </h1>
        <p className="text-2xl text-warm-text mb-4 font-inter max-w-3xl mx-auto leading-relaxed">
          Multi-Agent Orchestration for Pharmaceutical Intelligence
        </p>
        <p className="text-lg text-warm-text-light mb-12 max-w-2xl mx-auto font-inter leading-relaxed">
          Systematic evidence synthesis through distributed intelligence. Leveraging AKGP knowledge graphs and ROS scoring for pharmaceutical research.
        </p>

        <div className="flex items-center justify-center gap-4">
          <CalmButton
            onClick={() => navigate('/hypothesis')}
            className="inline-flex items-center gap-2 shadow-lg hover:shadow-xl transition-shadow text-lg px-8 py-4"
          >
            Launch Research Console
            <ArrowRight className="w-5 h-5" />
          </CalmButton>
          <button
            onClick={() => navigate('/graph')}
            className="inline-flex items-center gap-2 px-8 py-4 text-warm-text-light hover:text-warm-text border-2 border-warm-divider hover:border-terracotta-300 rounded-xl font-semibold transition-all font-inter"
          >
            <Network className="w-5 h-5" />
            Explore Graph
          </button>
        </div>
      </div>

      {/* Key Features Grid */}
      <div className="mb-24">
        <h2 className="text-3xl font-bold text-warm-text mb-4 text-center font-inter">
          Core Capabilities
        </h2>
        <p className="text-center text-warm-text-light mb-12 font-inter max-w-2xl mx-auto">
          MAESTRO combines multi-agent systems with advanced knowledge graph technology to deliver comprehensive pharmaceutical intelligence.
        </p>

        <div className="grid md:grid-cols-3 gap-6">
          <CalmCard className="hover:shadow-xl transition-shadow border-2 border-transparent hover:border-terracotta-100">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-xl flex items-center justify-center shadow-md flex-shrink-0">
                <Database className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-warm-text mb-2 font-inter">
                  AKGP Knowledge Graphs
                </h3>
                <p className="text-sm text-warm-text-light font-inter leading-relaxed">
                  Structured ingestion of clinical, patent, market, and literature evidence with comprehensive provenance tracking and temporal awareness.
                </p>
              </div>
            </div>
          </CalmCard>

          <CalmCard className="hover:shadow-xl transition-shadow border-2 border-transparent hover:border-terracotta-100">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-purple-600 rounded-xl flex items-center justify-center shadow-md flex-shrink-0">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-warm-text mb-2 font-inter">
                  Conflict Reasoning
                </h3>
                <p className="text-sm text-warm-text-light font-inter leading-relaxed">
                  Advanced temporal weighting and quality assessment algorithms to systematically resolve contradictory evidence across sources.
                </p>
              </div>
            </div>
          </CalmCard>

          <CalmCard className="hover:shadow-xl transition-shadow border-2 border-transparent hover:border-terracotta-100">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-amber-600 rounded-xl flex items-center justify-center shadow-md flex-shrink-0">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-warm-text mb-2 font-inter">
                  ROS Scoring Engine
                </h3>
                <p className="text-sm text-warm-text-light font-inter leading-relaxed">
                  Research Opportunity Scoring based on evidence strength, diversity, recency, and patent risk analysis for decision support.
                </p>
              </div>
            </div>
          </CalmCard>
        </div>
      </div>

      {/* Agent Architecture */}
      <div className="mb-24">
        <h2 className="text-3xl font-bold text-warm-text mb-4 text-center font-inter">
          Multi-Agent Architecture
        </h2>
        <p className="text-center text-warm-text-light mb-12 font-inter max-w-2xl mx-auto">
          Four specialized agents orchestrated by a master coordinator for comprehensive pharmaceutical intelligence.
        </p>

        <div className="grid md:grid-cols-2 gap-6">
          <CalmCard className="border-l-4 border-blue-500 shadow-lg">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <FileText className="w-5 h-5 text-blue-600" />
              </div>
              <h3 className="text-lg font-bold text-warm-text font-inter">Clinical Trials Agent</h3>
            </div>
            <p className="text-sm text-warm-text-light font-inter leading-relaxed">
              Analyzes clinical trial landscapes, success rates, phase distributions, and efficacy data from global trial registries.
            </p>
          </CalmCard>

          <CalmCard className="border-l-4 border-purple-500 shadow-lg">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-purple-600" />
              </div>
              <h3 className="text-lg font-bold text-warm-text font-inter">Patent & IP Agent</h3>
            </div>
            <p className="text-sm text-warm-text-light font-inter leading-relaxed">
              Evaluates freedom-to-operate, patent landscapes, filing trends, and competitive IP positioning across jurisdictions.
            </p>
          </CalmCard>

          <CalmCard className="border-l-4 border-emerald-500 shadow-lg">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                <Activity className="w-5 h-5 text-emerald-600" />
              </div>
              <h3 className="text-lg font-bold text-warm-text font-inter">Market Intelligence Agent</h3>
            </div>
            <p className="text-sm text-warm-text-light font-inter leading-relaxed">
              Provides market sizing, growth forecasts, competitive dynamics, and commercial opportunity assessments.
            </p>
          </CalmCard>

          <CalmCard className="border-l-4 border-amber-500 shadow-lg">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                <Database className="w-5 h-5 text-amber-600" />
              </div>
              <h3 className="text-lg font-bold text-warm-text font-inter">Literature Agent</h3>
            </div>
            <p className="text-sm text-warm-text-light font-inter leading-relaxed">
              Synthesizes scientific literature, research trends, mechanism of action insights, and emerging therapeutic paradigms.
            </p>
          </CalmCard>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-warm-divider pt-12 text-center">
        <p className="text-sm text-warm-text-light font-inter font-semibold mb-2">
          MAESTRO Research Platform
        </p>
        <p className="text-xs text-warm-text-subtle font-inter">
          Multi-Agent Orchestration with AKGP and ROS
        </p>
      </footer>
    </PageContainer>
  );
};
