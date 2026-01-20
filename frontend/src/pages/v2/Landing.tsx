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
    <div className="min-h-screen bg-white">
      {/* Subtle gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-indigo-50/30 via-white to-white pointer-events-none" />
      
      <PageContainer maxWidth="lg" className="relative">
        {/* Hero Section with clean minimal design */}
        <div className="text-center mb-32 pt-20 animate-calm-fade-in">
          {/* Clean icon with subtle shadow */}
          <div className="mb-8 relative inline-block">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-indigo-600 rounded-2xl shadow-lg hover:shadow-xl transition-shadow duration-300">
              <FileText className="w-10 h-10 text-white" />
            </div>
          </div>
          
          <h1 className="text-7xl font-extrabold text-slate-900 mb-6 font-inter tracking-tight">
            MAESTRO
          </h1>
          
          <div className="inline-block px-5 py-2 mb-6 bg-indigo-50 rounded-full border border-indigo-100">
            <p className="text-sm font-semibold text-indigo-700 font-inter tracking-wide">
              POWERED BY AI AGENTS & KNOWLEDGE GRAPHS
            </p>
          </div>
          
          <p className="text-3xl font-bold text-slate-800 mb-4 font-inter max-w-3xl mx-auto leading-tight">
            Multi-Agent Orchestration for Pharmaceutical Intelligence
          </p>
          <p className="text-xl text-slate-600 mb-16 max-w-2xl mx-auto font-inter leading-relaxed">
            Systematic evidence synthesis through distributed intelligence. Leveraging AKGP knowledge graphs and ROS scoring for pharmaceutical research.
          </p>

          <div className="flex items-center justify-center gap-4">
            <button
              onClick={() => navigate('/hypothesis')}
              className="inline-flex items-center gap-3 px-10 py-5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold text-lg shadow-lg hover:shadow-xl transition-all duration-300 font-inter"
            >
              <span>Launch Research Console</span>
              <ArrowRight className="w-6 h-6" />
            </button>
            <button
              onClick={() => navigate('/graph')}
              className="inline-flex items-center gap-3 px-10 py-5 text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-50 border-2 border-slate-200 hover:border-indigo-300 rounded-xl font-bold text-lg shadow-md hover:shadow-lg transition-all duration-300 font-inter"
            >
              <Network className="w-6 h-6" />
              Explore Graph
            </button>
          </div>
        </div>

        {/* Key Features Grid with clean minimal design */}
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
            <div className="bg-white rounded-2xl p-8 shadow-md hover:shadow-xl transition-shadow duration-300 border border-slate-100">
              <div className="w-14 h-14 bg-indigo-600 rounded-xl flex items-center justify-center shadow-md mb-6">
                <Database className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3 font-inter">
                AKGP Knowledge Graphs
              </h3>
              <p className="text-slate-600 font-inter leading-relaxed">
                Structured ingestion of clinical, patent, market, and literature evidence with comprehensive provenance tracking and temporal awareness.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-8 shadow-md hover:shadow-xl transition-shadow duration-300 border border-slate-100">
              <div className="w-14 h-14 bg-emerald-600 rounded-xl flex items-center justify-center shadow-md mb-6">
                <Activity className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3 font-inter">
                Conflict Reasoning
              </h3>
              <p className="text-slate-600 font-inter leading-relaxed">
                Advanced temporal weighting and quality assessment algorithms to systematically resolve contradictory evidence across sources.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-8 shadow-md hover:shadow-xl transition-shadow duration-300 border border-slate-100">
              <div className="w-14 h-14 bg-indigo-600 rounded-xl flex items-center justify-center shadow-md mb-6">
                <Zap className="w-7 h-7 text-white" />
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

        {/* Agent Architecture with premium card design */}
        <div className="mb-32">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-extrabold text-slate-900 mb-4 font-inter">
              Multi-Agent Architecture
            </h2>
            <p className="text-lg text-slate-600 font-inter max-w-2xl mx-auto">
              Four specialized agents orchestrated by a master coordinator for comprehensive pharmaceutical intelligence.
            </p>
          </div>clean professional cards */}
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
            <div className="bg-white rounded-2xl p-6 shadow-md hover:shadow-lg transition-shadow duration-300 border-l-4 border-indigo-600">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
                  <FileText className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 font-inter">Clinical Trials Agent</h3>
              </div>
              <p className="text-slate-700 font-inter leading-relaxed pl-1">
                Analyzes clinical trial landscapes, success rates, phase distributions, and efficacy data from global trial registries.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-md hover:shadow-lg transition-shadow duration-300 border-l-4 border-emerald-600">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-emerald-600 rounded-lg flex items-center justify-center shadow-sm">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 font-inter">Patent & IP Agent</h3>
              </div>
              <p className="text-slate-700 font-inter leading-relaxed pl-1">
                Evaluates freedom-to-operate, patent landscapes, filing trends, and competitive IP positioning across jurisdictions.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-md hover:shadow-lg transition-shadow duration-300 border-l-4 border-indigo-600">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
                  <Activity className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 font-inter">Market Intelligence Agent</h3>
              </div>
              <p className="text-slate-700 font-inter leading-relaxed pl-1">
                Provides market sizing, growth forecasts, competitive dynamics, and commercial opportunity assessments.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-md hover:shadow-lg transition-shadow duration-300 border-l-4 border-emerald-600">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-emerald-600 rounded-lg flex items-center justify-center shadow-sm">
                  <Database className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 font-inter">Literature Agent</h3>
              </div>
              <p className="text-slate-700 font-inter leading-relaxed pl-1">
                Synthesizes scientific literature, research trends, mechanism of action insights, and emerging therapeutic paradigms.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="border-t border-slate-200 pt-16 pb-8 text-center">
          <p className="text-base font-bold text-slate-800 font-inter mb-2">
            MAESTRO Research Platform
          </p>
          <p className="text-sm text-slate-500 font-inter