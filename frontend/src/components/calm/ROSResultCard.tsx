/**
 * ROS Result Card
 * Displays research opportunity score with breakdown
 */

import React from 'react';
import type { ROSViewResponse } from '../../types/api';
import { CalmCard, CalmBadge } from './index';
import { CheckCircle } from 'lucide-react';

interface ROSResultCardProps {
  rosData: ROSViewResponse;
}

const getConfidenceBadgeClass = (level: string): string => {
  switch (level) {
    case 'HIGH':
      return 'bg-sage-100 text-sage-700 border-sage-200';
    case 'MEDIUM':
      return 'bg-amber-100 text-amber-700 border-amber-200';
    case 'LOW':
      return 'bg-rose-100 text-rose-700 border-rose-200';
    default:
      return 'bg-warm-bg-alt text-warm-text-light border-warm-divider';
  }
};

const getScoreColor = (score: number): string => {
  if (score >= 7) return 'text-sage-700';
  if (score >= 4) return 'text-amber-700';
  return 'text-rose-700';
};

const getScoreBgColor = (score: number): string => {
  if (score >= 7) return 'bg-sage-50';
  if (score >= 4) return 'bg-amber-50';
  return 'bg-rose-50';
};

export const ROSResultCard: React.FC<ROSResultCardProps> = ({ rosData }) => {
  const breakdown = rosData.breakdown || {};
  const metadata = rosData.metadata || {};

  return (
    <CalmCard className="mb-8 border border-warm-divider">
      {/* Header */}
      <div className="flex items-start justify-between mb-6 pb-4 border-b border-warm-divider">
        <div className="flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-sage-600 flex-shrink-0" />
          <h3 className="text-sm font-semibold text-warm-text font-inter uppercase tracking-wide">
            Research Opportunity Score
          </h3>
        </div>
        <CalmBadge className={getConfidenceBadgeClass(rosData.confidence_level)}>
          {rosData.confidence_level} CONFIDENCE
        </CalmBadge>
      </div>

      {/* Score + Hypothesis */}
      <div className="grid md:grid-cols-2 gap-6 mb-6">
        {/* Score */}
        <div className={`rounded-lg p-4 ${getScoreBgColor(rosData.ros_score)}`}>
          <p className="text-xs text-warm-text-subtle font-inter uppercase tracking-wide mb-2">
            ROS Score
          </p>
          <div className="flex items-baseline gap-2">
            <span className={`text-4xl font-bold font-inter ${getScoreColor(rosData.ros_score)}`}>
              {rosData.ros_score.toFixed(1)}
            </span>
            <span className="text-lg text-warm-text-light font-inter">/10</span>
          </div>
        </div>

        {/* Hypothesis */}
        <div>
          <p className="text-xs text-warm-text-subtle font-inter uppercase tracking-wide mb-2">
            Analyzed Hypothesis
          </p>
          <div className="flex flex-col gap-1">
            <p className="text-sm font-semibold text-warm-text font-inter">
              {rosData.drug}
            </p>
            <p className="text-xs text-warm-text-light font-inter">for</p>
            <p className="text-sm font-semibold text-warm-text font-inter">
              {rosData.disease}
            </p>
          </div>
        </div>
      </div>

      {/* Explanation */}
      <div className="bg-warm-bg-alt rounded-lg px-4 py-3 mb-6 border border-warm-divider">
        <p className="text-sm text-warm-text font-inter leading-relaxed">
          {rosData.explanation}
        </p>
      </div>

      {/* Score Breakdown */}
      <div className="mb-6">
        <p className="text-xs font-semibold text-warm-text uppercase tracking-wide mb-3 font-inter">
          Score Components
        </p>
        <div className="space-y-2">
          {/* Evidence Strength */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-warm-text font-inter">Evidence Strength</span>
            <div className="flex items-center gap-3">
              <div className="w-24 h-2 bg-warm-divider rounded-full overflow-hidden">
                <div
                  className="h-full bg-sage-600 rounded-full"
                  style={{
                    width: `${Math.min((breakdown.evidence_strength || 0) / 3.5 * 100, 100)}%`,
                  }}
                />
              </div>
              <span className="text-sm font-semibold text-warm-text w-10 text-right font-inter">
                {(breakdown.evidence_strength || 0).toFixed(1)}
              </span>
            </div>
          </div>

          {/* Evidence Diversity */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-warm-text font-inter">Evidence Diversity</span>
            <div className="flex items-center gap-3">
              <div className="w-24 h-2 bg-warm-divider rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 rounded-full"
                  style={{
                    width: `${Math.min((breakdown.evidence_diversity || 0) / 2 * 100, 100)}%`,
                  }}
                />
              </div>
              <span className="text-sm font-semibold text-warm-text w-10 text-right font-inter">
                {(breakdown.evidence_diversity || 0).toFixed(1)}
              </span>
            </div>
          </div>

          {/* Recency Boost */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-warm-text font-inter">Recency Boost</span>
            <div className="flex items-center gap-3">
              <div className="w-24 h-2 bg-warm-divider rounded-full overflow-hidden">
                <div
                  className="h-full bg-purple-600 rounded-full"
                  style={{
                    width: `${Math.min((breakdown.recency_boost || 0) / 2 * 100, 100)}%`,
                  }}
                />
              </div>
              <span className="text-sm font-semibold text-warm-text w-10 text-right font-inter">
                {(breakdown.recency_boost || 0).toFixed(1)}
              </span>
            </div>
          </div>

          {/* Conflict Penalty */}
          {(breakdown.conflict_penalty || 0) !== 0 && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-warm-text font-inter">Conflict Penalty</span>
              <div className="flex items-center gap-3">
                <div className="w-24 h-2 bg-warm-divider rounded-full overflow-hidden">
                  <div
                    className="h-full bg-rose-600 rounded-full"
                    style={{
                      width: `${Math.min(Math.abs((breakdown.conflict_penalty || 0)) / 1 * 100, 100)}%`,
                    }}
                  />
                </div>
                <span className="text-sm font-semibold text-rose-700 w-10 text-right font-inter">
                  {(breakdown.conflict_penalty || 0).toFixed(1)}
                </span>
              </div>
            </div>
          )}

          {/* Patent Risk */}
          {(breakdown.patent_risk_penalty || 0) !== 0 && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-warm-text font-inter">Patent Risk</span>
              <div className="flex items-center gap-3">
                <div className="w-24 h-2 bg-warm-divider rounded-full overflow-hidden">
                  <div
                    className="h-full bg-amber-600 rounded-full"
                    style={{
                      width: `${Math.min(Math.abs((breakdown.patent_risk_penalty || 0)) / 1.5 * 100, 100)}%`,
                    }}
                  />
                </div>
                <span className="text-sm font-semibold text-amber-700 w-10 text-right font-inter">
                  {(breakdown.patent_risk_penalty || 0).toFixed(1)}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Metadata */}
      {metadata && (
        <div className="grid md:grid-cols-4 gap-4 pt-4 border-t border-warm-divider">
          <div>
            <p className="text-xs text-warm-text-subtle font-inter uppercase tracking-wide mb-1">
              Supporting Evidence
            </p>
            <p className="text-lg font-bold text-sage-700 font-inter">
              {metadata.num_supporting_evidence || 0}
            </p>
          </div>
          <div>
            <p className="text-xs text-warm-text-subtle font-inter uppercase tracking-wide mb-1">
              Contradicting Evidence
            </p>
            <p className="text-lg font-bold text-rose-700 font-inter">
              {metadata.num_contradicting_evidence || 0}
            </p>
          </div>
          <div>
            <p className="text-xs text-warm-text-subtle font-inter uppercase tracking-wide mb-1">
              Active Agents
            </p>
            <p className="text-lg font-bold text-blue-700 font-inter">
              {(metadata.distinct_agents && metadata.distinct_agents.length) || 0}
            </p>
          </div>
          <div>
            <p className="text-xs text-warm-text-subtle font-inter uppercase tracking-wide mb-1">
              Analysis Time
            </p>
            <p className="text-sm text-warm-text font-inter">
              {metadata.computation_timestamp
                ? new Date(metadata.computation_timestamp).toLocaleTimeString()
                : 'N/A'}
            </p>
          </div>
        </div>
      )}
    </CalmCard>
  );
};
