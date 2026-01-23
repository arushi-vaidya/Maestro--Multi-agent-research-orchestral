/**
 * Confidence Scoring Page
 * GET /api/ros/latest, /api/execution/status, /api/conflicts/explanation, /api/evidence/timeline
 */

import React, { useState, useEffect } from 'react';
import { PageContainer, CalmCard, CalmBadge, CalmButton } from '../../components/calm';
import { api } from '../../services/api';
import type {
  ROSViewResponse,
  ExecutionStatusResponse,
  ConflictExplanationResponse,
  EvidenceTimelineResponse,
} from '../../types/api';
import { Scale, AlertTriangle, Loader2, RefreshCw, ArrowRight } from 'lucide-react';

export const ConfidenceScoring: React.FC = () => {
  const [rosData, setRosData] = useState<ROSViewResponse | null>(null);
  const [executionData, setExecutionData] = useState<ExecutionStatusResponse | null>(null); // Fetched but not currently displayed
  const [conflictData, setConflictData] = useState<ConflictExplanationResponse | null>(null);
  const [evidenceData, setEvidenceData] = useState<EvidenceTimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch all required data on component mount
  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch ROS data
      const ros = await api.getROSLatest();
      setRosData(ros);

      // Fetch execution status
      const exec = await api.getExecutionStatus();
      setExecutionData(exec);

      // Fetch conflict data
      const conflict = await api.getConflictExplanation();
      setConflictData(conflict);

      // Fetch evidence timeline
      const evidence = await api.getEvidenceTimeline();
      setEvidenceData(evidence);

      setLoading(false);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load confidence scoring data');
      setLoading(false);
    }
  };

  // Calculate score factors from ROS breakdown
  const getScoreFactors = () => {
    if (!rosData?.breakdown) return [];

    const breakdown = rosData.breakdown;
    return [
      {
        name: 'Evidence Strength',
        weight: breakdown.evidence_strength || 0,
        description: `Aggregated strength of evidence from ${rosData.metadata?.distinct_agents?.length || 0} different agents`
      },
      {
        name: 'Evidence Diversity',
        weight: breakdown.evidence_diversity || 0,
        description: `Multiple evidence types from ${rosData.metadata?.num_supporting_evidence || 0} supporting sources`
      },
      {
        name: 'Recency Boost',
        weight: breakdown.recency_boost || 0,
        description: 'Recent studies and trials provide up-to-date validation'
      },
      {
        name: 'Conflict Penalty',
        weight: breakdown.conflict_penalty || 0,
        description: conflictData?.explanation || 'Evidence conflicts detected'
      },
      {
        name: 'Patent Risk Penalty',
        weight: breakdown.patent_risk_penalty || 0,
        description: 'Patent landscape considerations and IP risks'
      }
    ];
  };

  // Calculate uncertainty sources from conflict data
  const getUncertaintySources = () => {
    if (!conflictData) return [];

    const sources = [];

    if (conflictData.has_conflict) {
      sources.push({
        category: 'Evidence Conflicts',
        level: conflictData.severity?.toLowerCase() || 'moderate',
        description: conflictData.explanation || 'Conflicting evidence detected'
      });
    }

    if (conflictData.temporal_reasoning) {
      sources.push({
        category: 'Temporal Consistency',
        level: 'moderate',
        description: conflictData.temporal_reasoning
      });
    }

    if (rosData?.metadata) {
      const supportRatio = rosData.metadata.num_supporting_evidence /
        (rosData.metadata.num_supporting_evidence + rosData.metadata.num_contradicting_evidence);

      sources.push({
        category: 'Evidence Consensus',
        level: supportRatio > 0.7 ? 'low' : supportRatio > 0.5 ? 'moderate' : 'high',
        description: `${rosData.metadata.num_supporting_evidence} supporting vs ${rosData.metadata.num_contradicting_evidence} contradicting evidence pieces`
      });
    }

    return sources;
  };

  // Calculate evidence summary from timeline data
  const getEvidenceSummary = () => {
    if (!evidenceData?.events) return [];

    const byType = evidenceData.events.reduce((acc: Record<string, { type: string; count: number; positive: number; negative: number; neutral: number }>, event) => {
      const type = event.agent_id || 'other';
      if (!acc[type]) {
        acc[type] = { type, count: 0, positive: 0, negative: 0, neutral: 0 };
      }
      acc[type].count++;

      if (event.polarity === 'SUPPORTS') acc[type].positive++;
      else if (event.polarity === 'CONTRADICTS') acc[type].negative++;
      else acc[type].neutral++;

      return acc;
    }, {});

    return Object.values(byType);
  };

  // Loading state
  if (loading) {
    return (
      <PageContainer maxWidth="lg">
        <div className="min-h-screen bg-warm-bg flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin text-warm-text-light mx-auto mb-4" />
            <p className="text-warm-text-light">Loading confidence scoring data...</p>
          </div>
        </div>
      </PageContainer>
    );
  }

  // Error state
  if (error) {
    return (
      <PageContainer maxWidth="lg">
        <div className="min-h-screen bg-warm-bg flex items-center justify-center">
          <div className="text-center max-w-md">
            <AlertTriangle className="w-12 h-12 text-terracotta-400 mx-auto mb-4" />
            <h2 className="text-lg font-semibold text-warm-text mb-2">No Data Available</h2>
            <p className="text-warm-text-light mb-6">{error}</p>
            <CalmButton onClick={fetchAllData}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </CalmButton>
          </div>
        </div>
      </PageContainer>
    );
  }

  const scoreFactors = getScoreFactors();
  const uncertaintySources = getUncertaintySources();
  const evidenceSummary = getEvidenceSummary();
  const confidenceLevel = rosData?.confidence_level || 'MEDIUM';
  const confidenceScore = rosData?.ros_score || 0;

  return (
    <PageContainer maxWidth="lg">
      <div className="mb-12 animate-calm-fade-in">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 bg-gradient-to-br from-terracotta-500 to-terracotta-600 rounded-xl flex items-center justify-center shadow-md">
            <Scale className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-warm-text mb-2 font-inter tracking-tight">
            Confidence Scoring
          </h1>
        </div>
        <p className="text-lg text-warm-text-light font-inter ml-13">
          Understand the factors contributing to hypothesis confidence scores
        </p>
      </div>

      {/* Current Query Info */}
      <CalmCard className="mb-8">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-warm-text-light">Current Analysis:</span>
          <span className="font-medium text-warm-text">{rosData?.drug}</span>
          <ArrowRight className="w-3 h-3 text-warm-text-light" />
          <span className="font-medium text-warm-text">{rosData?.disease}</span>
          <span className="ml-auto text-warm-text-light">
            Updated: {rosData?.metadata?.computation_timestamp && new Date(rosData.metadata.computation_timestamp).toLocaleDateString()}
          </span>
        </div>
      </CalmCard>

      {/* Main Content */}
      <div className="grid lg:grid-cols-12 gap-8">
        {/* Score Overview */}
        <div className="lg:col-span-4">
          <CalmCard className="sticky top-24">
            {/* Main Score */}
            <div className="text-center mb-6 pb-6 border-b border-warm-divider">
              <p className="text-sm font-medium text-warm-text-light uppercase tracking-wider mb-4">
                Overall Confidence
              </p>
              <div className="flex justify-center mb-4">
                <div className="relative">
                  <div className="w-32 h-32 rounded-full border-8 border-warm-surface-alt flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-warm-text">
                        {confidenceScore.toFixed(1)}
                      </div>
                      <div className="text-xs text-warm-text-light uppercase tracking-wide">
                        {confidenceLevel}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <p className="text-lg font-semibold text-warm-text">
                {rosData?.drug} → {rosData?.disease}
              </p>
            </div>

            {/* Quick Stats */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-warm-text-light">Confidence Level</span>
                <CalmBadge variant={confidenceLevel === 'HIGH' ? 'positive' : confidenceLevel === 'MEDIUM' ? 'info' : 'neutral'}>
                  {confidenceLevel}
                </CalmBadge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-warm-text-light">Total Sources</span>
                <span className="font-medium text-warm-text">
                  {evidenceData?.total_count || 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-warm-text-light">Supporting Evidence</span>
                <span className="font-medium text-warm-text">
                  {rosData?.metadata?.num_supporting_evidence || 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-warm-text-light">Active Agents</span>
                <span className="font-medium text-warm-text">
                  {rosData?.metadata?.distinct_agents?.length || 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-warm-text-light">Last Updated</span>
                <span className="font-medium text-warm-text">
                  {rosData?.metadata?.computation_timestamp && new Date(rosData.metadata.computation_timestamp).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                </span>
              </div>
            </div>

            {/* Score Interpretation */}
            <div className="mt-6 p-4 bg-warm-surface-alt rounded-lg">
              <p className="text-sm text-warm-text-light">
                <strong>Interpretation:</strong> {rosData?.explanation}
              </p>
            </div>
          </CalmCard>
        </div>

        {/* Detailed Analysis */}
        <div className="lg:col-span-8">
          <div className="space-y-6">
            {/* Score Breakdown */}
            <CalmCard>
              <h3 className="text-sm font-medium text-warm-text-light uppercase tracking-wider mb-6">
                Contributing Factors
              </h3>

              <div className="space-y-4">
                {scoreFactors.map((factor, idx) => (
                  <div key={idx} className="border-b border-warm-divider pb-4 last:border-0">
                    <div className="flex items-start justify-between mb-2">
                      <span className="font-medium text-warm-text">{factor.name}</span>
                      <span className={`font-semibold ${
                        factor.weight > 0 ? 'text-sage-600' : 'text-terracotta-600'
                      }`}>
                        {factor.weight > 0 ? '+' : ''}{factor.weight.toFixed(1)}
                      </span>
                    </div>
                    <p className="text-sm text-warm-text-light">{factor.description}</p>

                    {/* Visual bar */}
                    <div className="mt-2 h-2 bg-warm-surface-alt rounded-full overflow-hidden">
                      <div
                        className={`h-full ${factor.weight > 0 ? 'bg-sage-500' : 'bg-terracotta-400'}`}
                        style={{ width: `${Math.min(Math.abs(factor.weight) * 10, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-8 pt-6 border-t border-warm-divider">
                <h4 className="text-sm font-medium text-warm-text mb-3">
                  Methodology
                </h4>
                <p className="text-sm text-warm-text-light leading-relaxed">
                  Confidence scores are computed using a weighted evidence aggregation model
                  that considers study quality, sample sizes, replication status, and mechanistic
                  coherence. Negative evidence is weighted according to study rigor and direct
                  relevance to the therapeutic hypothesis. Scores are calibrated against historical
                  drug repurposing success rates.
                </p>
              </div>
            </CalmCard>

            {/* Uncertainty Sources */}
            <CalmCard>
              <h3 className="text-sm font-medium text-warm-text-light uppercase tracking-wider mb-6">
                Sources of Uncertainty
              </h3>

              <div className="space-y-4">
                {uncertaintySources.length > 0 ? uncertaintySources.map((source, idx) => (
                  <div key={idx} className="p-4 border border-warm-divider rounded-lg">
                    <div className="flex items-start justify-between mb-2">
                      <span className="font-medium text-warm-text">{source.category}</span>
                      <CalmBadge variant={
                        source.level === 'low' ? 'positive' :
                        source.level === 'moderate' ? 'info' :
                        'warning'
                      }>
                        {source.level.toUpperCase()}
                      </CalmBadge>
                    </div>
                    <p className="text-sm text-warm-text-light">{source.description}</p>
                  </div>
                )) : (
                  <p className="text-sm text-warm-text-light text-center py-8">
                    No significant uncertainty sources identified
                  </p>
                )}
              </div>

              {conflictData?.has_conflict && (
                <div className="mt-8 pt-6 border-t border-warm-divider">
                  <h4 className="text-sm font-medium text-warm-text mb-3">
                    Conflict Summary
                  </h4>
                  <div className="text-sm text-warm-text-light space-y-2">
                    <p><strong>Supporting:</strong> {conflictData.evidence_counts?.supports || 0} evidence pieces</p>
                    <p><strong>Contradicting:</strong> {conflictData.evidence_counts?.contradicts || 0} evidence pieces</p>
                    <p><strong>Suggesting:</strong> {conflictData.evidence_counts?.suggests || 0} evidence pieces</p>
                  </div>
                </div>
              )}
            </CalmCard>

            {/* Evidence Summary */}
            <CalmCard>
              <h3 className="text-sm font-medium text-warm-text-light uppercase tracking-wider mb-6">
                Evidence by Agent
              </h3>

              <div className="space-y-4">
                {evidenceSummary.length > 0 ? evidenceSummary.map((item: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-4 border border-warm-divider rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <CalmBadge variant="neutral">
                          {item.type}
                        </CalmBadge>
                        <span className="font-medium text-warm-text capitalize">
                          {item.type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <span className="text-sm text-warm-text-light">
                        {item.count} sources
                      </span>
                    </div>

                    {/* Stacked bar */}
                    <div className="h-3 bg-warm-surface-alt rounded-full overflow-hidden flex">
                      <div
                        className="bg-sage-500 h-full"
                        style={{ width: `${(item.positive / item.count) * 100}%` }}
                      />
                      <div
                        className="bg-warm-surface-alt h-full"
                        style={{ width: `${(item.neutral / item.count) * 100}%` }}
                      />
                      <div
                        className="bg-terracotta-400 h-full"
                        style={{ width: `${(item.negative / item.count) * 100}%` }}
                      />
                    </div>

                    <div className="flex items-center gap-4 mt-2 text-xs text-warm-text-light">
                      <span className="flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-sage-500" />
                        {item.positive} positive
                      </span>
                      <span className="flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-warm-surface-alt" />
                        {item.neutral} neutral
                      </span>
                      <span className="flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-terracotta-400" />
                        {item.negative} negative
                      </span>
                    </div>
                  </div>
                )) : (
                  <p className="text-sm text-warm-text-light text-center py-8">
                    No evidence data available
                  </p>
                )}
              </div>

              {/* Agent distribution */}
              {evidenceData?.agent_distribution && (
                <div className="mt-6 pt-6 border-t border-warm-divider">
                  <h4 className="text-sm font-medium text-warm-text mb-3">
                    Agent Distribution
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(evidenceData.agent_distribution).map(([agent, count]) => (
                      <CalmBadge key={agent} variant="info">
                        {agent}: <strong>{count as number}</strong>
                      </CalmBadge>
                    ))}
                  </div>
                </div>
              )}
            </CalmCard>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};