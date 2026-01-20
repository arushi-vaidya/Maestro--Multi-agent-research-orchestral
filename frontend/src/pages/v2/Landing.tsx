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
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-amber-50/30 to-rose-50/20">
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(245,158,11,0.08),transparent_50%),radial-gradient(circle_at_80%_80%,rgba(239,68,68,0.06),transparent_50%)] pointer-events-none" />
      
      <PageContainer maxWidth="lg" className="relative">
        {/* Hero Section with enhanced visual appeal */}
        <div className="text-center mb-32 pt-20 animate-calm-fade-in">
          {/* Animated icon with glow effect */}
          <div className="mb-8 relative inline-block">
            <div className="absolute inset-0 bg-gradient-to-br from-amber-400 to-rose-500 rounded-3xl blur-2xl opacity-30 animate-pulse" />
            <div className="relative inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-amber-500 via-orange-500 to-rose-500 rounded-3xl shadow-2xl transform hover:scale-105 transition-transform duration-300">
              <FileText className="w-12 h-12 text-white drop-shadow-lg" />
            </div>
          </div>
          
          <h1 className="text-7xl font-extrabold bg-gradient-to-r from-slate-900 via-amber-900 to-rose-900 bg-clip-text text-transparent mb-6 font-inter tracking-tight">
            MAESTRO
          </h1>
          
          <div className="inline-block px-6 py-2 mb-6 bg-gradient-to-r from-amber-100 to-rose-100 rounded-full border border-amber-200/50">
            <p className="text-sm font-semibold bg-gradient-to-r from-amber-700 to-rose-700 bg-clip-text text-transparent font-inter tracking-wide">
              POWERED BY AI AGENTS & KNOWLEDGE GRAPHS
            </p>
          </div>
          
          <p className="text-3xl font-bold text-slate-800 mb-4 font-inter max-w-3xl mx-auto leading-tight">
            Multi-Agent Orchestration for Pharmaceutical Intelligence
          </p>
          <p className="text-xl text-slate-600 mb-16 max-w-2xl mx-auto font-inter leading-relaxed">
            Systematic evidence synthesis through distributed intelligence. Leveraging AKGP knowledge graphs and ROS scoring for pharmaceutical research.
          </p>

          <div className="flex items-center justify-center gap-5">
            <button
              onClick={() => navigate('/hypothesis')}
              className="group relative inline-flex items-center gap-3 px-10 py-5 bg-gradient-to-r from-amber-500 to-rose-500 hover:from-amber-600 hover:to-rose-600 text-white rounded-2xl font-bold text-lg shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105 font-inter"
            >
              <span className="relative z-10">Launch Research Console</span>
              <ArrowRight className="w-6 h-6 relative z-10 group-hover:translate-x-1 transition-transform" />
              <div className="absolute inset-0 bg-gradient-to-r from-amber-400 to-rose-400 rounded-2xl blur opacity-50 group-hover:opacity-75 transition-opacity" />
            </button>
            <button
              onClick={() => navigate('/graph')}
              className="inline-flex items-center gap-3 px-10 py-5 text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-50 border-2 border-slate-200 hover:border-amber-300 rounded-2xl font-bold text-lg shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 font-inter"
            >
              <Network className="w-6 h-6" />
              Explore Graph
            </button>
          </div>
        </div>

        {/* Key Features Grid with enhanced styling */}
        <div className="mb-32">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-extrabold text-slate-900 mb-4 font-inter">
              Core Capabilities
            </h2>
            <p className="text-lg text-slate-600 font-inter max-w-2xl mx-auto">
              MAESTRO combines multi-agent systems with advanced knowledge graph technology to deliver comprehensive pharmaceutical intelligence.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="group relative bg-white rounded-3xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 border border-emerald-100 hover:border-emerald-300 transform hover:-translate-y-2">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-emerald-400 to-teal-500 rounded-3xl opacity-0 group-hover:opacity-20 transition-opacity blur" />
              <div className="relative">
                <div className="w-16 h-16 bg-gradient-to-br from-emerald-400 to-teal-600 rounded-2xl flex items-center justify-center shadow-xl mb-6 transform group-hover:scale-110 transition-transform">
                  <Database className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-3 font-inter">
                  AKGP Knowledge Graphs
                </h3>
                <p className="text-slate-600 font-inter leading-relaxed">
                  Structured ingestion of clinical, patent, market, and literature evidence with comprehensive provenance tracking and temporal awareness.
                </p>
              </div>
            </div>

            <div className="group relative bg-white rounded-3xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 border border-purple-100 hover:border-purple-300 transform hover:-translate-y-2">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-400 to-pink-500 rounded-3xl opacity-0 group-hover:opacity-20 transition-opacity blur" />
              <div className="relative">
                <div className="w-16 h-16 bg-gradient-to-br from-purple-400 to-pink-600 rounded-2xl flex items-center justify-center shadow-xl mb-6 transform group-hover:scale-110 transition-transform">
                  <Activity className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-3 font-inter">
                  Conflict Reasoning
                </h3>
                <p className="text-slate-600 font-inter leading-relaxed">
                  Advanced temporal weighting and quality assessment algorithms to systematically resolve contradictory evidence across sources.
                </p>
              </div>
            </div>

            <div className="group relative bg-white rounded-3xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 border border-amber-100 hover:border-amber-300 transform hover:-translate-y-2">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-amber-400 to-orange-500 rounded-3xl opacity-0 group-hover:opacity-20 transition-opacity blur" />
              <div className="relative">
                <div className="w-16 h-16 bg-gradient-to-br from-amber-400 to-orange-600 rounded-2xl flex items-center justify-center shadow-xl mb-6 transform group-hover:scale-110 transition-transform">
                  <Zap className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-3 font-inter">
                  ROS Scoring Engine
                </h3>
                <p className="text-slate-600 font-inter leading-relaxed">
                  Research Opportunity Scoring based on evidence strength, diversity, recency, and patent risk analysis for decision support.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Agent Architecture with premium card design */}
        <div className="mb-32">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-extrabold text-slate-900 mb-4 font-inter">
              Multi-Agent Architecture
            </h2>
            <p className="text-lg text-slate-600 font-inter max-w-2xl mx-auto">
              Four specialized agents orchestrated by a master coordinator for comprehensive pharmaceutical intelligence.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="group relative bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 shadow-md hover:shadow-xl transition-all duration-300 border-l-4 border-blue-500 transform hover:-translate-y-1">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 bg-gradient-to-br from-blue-400 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg transform group-hover:rotate-6 transition-transform">
                  <FileText className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 font-inter">Clinical Trials Agent</h3>
              </div>
              <p className="text-slate-700 font-inter leading-relaxed pl-1">
                Analyzes clinical trial landscapes, success rates, phase distributions, and efficacy data from global trial registries.
              </p>
            </div>

            <div className="group relative bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6 shadow-md hover:shadow-xl transition-all duration-300 border-l-4 border-purple-500 transform hover:-translate-y-1">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 bg-gradient-to-br from-purple-400 to-pink-600 rounded-xl flex items-center justify-center shadow-lg transform group-hover:rotate-6 transition-transform">
                  <Shield className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 font-inter">Patent & IP Agent</h3>
              </div>
              <p className="text-slate-700 font-inter leading-relaxed pl-1">
                Evaluates freedom-to-operate, patent landscapes, filing trends, and competitive IP positioning across jurisdictions.
              </p>
            </div>

            <div className="group relative bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl p-6 shadow-md hover:shadow-xl transition-all duration-300 border-l-4 border-emerald-500 transform hover:-translate-y-1">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 bg-gradient-to-br from-emerald-400 to-teal-600 rounded-xl flex items-center justify-center shadow-lg transform group-hover:rotate-6 transition-transform">
                  <Activity className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 font-inter">Market Intelligence Agent</h3>
              </div>
              <p className="text-slate-700 font-inter leading-relaxed pl-1">
                Provides market sizing, growth forecasts, competitive dynamics, and commercial opportunity assessments.
              </p>
            </div>

            <div className="group relative bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl p-6 shadow-md hover:shadow-xl transition-all duration-300 border-l-4 border-amber-500 transform hover:-translate-y-1">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 bg-gradient-to-br from-amber-400 to-orange-600 rounded-xl flex items-center justify-center shadow-lg transform group-hover:rotate-6 transition-transform">
                  <Database className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 font-inter">Literature Agent</h3>
              </div>
              <p className="text-slate-700 font-inter leading-relaxed pl-1">
                Synthesizes scientific literature, research trends, mechanism of action insights, and emerging therapeutic paradigms.
              </p>
            </div>
          </div>
        </div>

        {/* Footer with gradient */}
        <footer className="relative border-t border-slate-200 pt-16 pb-8 text-center">
          <div className="absolute inset-0 bg-gradient-to-t from-amber-50/50 to-transparent pointer-events-none" />
          <p className="text-base font-bold text-slate-800 font-inter mb-2 relative">
            MAESTRO Research Platform
          </p>
          <p className="text-sm text-slate-500 font-inter relative">
            Multi-Agent Orchestration with AKGP and ROS
          </p>
        </footer>
      </PageContainer>
    </div>
  );
};
