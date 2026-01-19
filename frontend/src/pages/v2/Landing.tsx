/**
 * Landing Page - STEP 8
 *
 * Design: Calm, academic positioning
 * Inspiration: Claude.ai × Linear × Arc Browser
 *
 * ❌ No flashy animations
 * ❌ No particle effects
 * ✅ Warm minimalism
 * ✅ Academic tone
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Database, Activity, FileText } from 'lucide-react';
import { PageContainer, CalmButton, CalmCard } from '../../components/calm';

export const Landing: React.FC = () => {
  const navigate = useNavigate();

  return (
    <PageContainer maxWidth="lg">
      {/* Hero Section - Calm, Academic */}
      <div className="text-center mb-24 animate-calm-fade-in">
        <h1 className="text-5xl font-bold text-warm-text mb-6 font-inter tracking-tight">
          MAESTRO
        </h1>
        <p className="text-xl text-warm-text-light mb-4 font-inter max-w-2xl mx-auto leading-relaxed">
          Multi-Agent Orchestration for Pharmaceutical Intelligence
        </p>
        <p className="text-base text-warm-text-lighter mb-12 max-w-xl mx-auto font-inter">
          Systematic evidence synthesis through distributed intelligence.
        </p>

        <CalmButton
          onClick={() => navigate('/hypothesis')}
          className="inline-flex items-center gap-2"
        >
          Launch Research Console
          <ArrowRight className="w-4 h-4" />
        </CalmButton>
      </div>

      {/* Methodology Overview */}
      <div className="mb-24">
        <h2 className="text-2xl font-semibold text-warm-text mb-8 text-center font-inter">
          Methodology
        </h2>

        <div className="grid md:grid-cols-3 gap-6">
          <CalmCard>
            <div className="flex items-start gap-4">
              <Database className="w-6 h-6 text-terracotta-500 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-warm-text mb-2 font-inter">
                  Knowledge Graph Construction
                </h3>
                <p className="text-sm text-warm-text-light font-inter leading-relaxed">
                  Structured ingestion of clinical, patent, market, and literature evidence with provenance tracking.
                </p>
              </div>
            </div>
          </CalmCard>

          <CalmCard>
            <div className="flex items-start gap-4">
              <Activity className="w-6 h-6 text-terracotta-500 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-warm-text mb-2 font-inter">
                  Conflict Reasoning
                </h3>
                <p className="text-sm text-warm-text-light font-inter leading-relaxed">
                  Temporal weighting and quality assessment to resolve contradictory evidence.
                </p>
              </div>
            </div>
          </CalmCard>

          <CalmCard>
            <div className="flex items-start gap-4">
              <FileText className="w-6 h-6 text-terracotta-500 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-warm-text mb-2 font-inter">
                  Research Opportunity Scoring
                </h3>
                <p className="text-sm text-warm-text-light font-inter leading-relaxed">
                  Deterministic heuristic scoring based on evidence strength, diversity, and patent risk.
                </p>
              </div>
            </div>
          </CalmCard>
        </div>
      </div>

      {/* Citation-style Footer */}
      <footer className="border-t border-warm-divider pt-12 text-center">
        <p className="text-sm text-warm-text-lighter font-inter">
          MAESTRO Research Platform
        </p>
        <p className="text-xs text-warm-text-subtle font-inter mt-2">
          Multi-Agent Orchestration with AKGP and ROS
        </p>
      </footer>
    </PageContainer>
  );
};
