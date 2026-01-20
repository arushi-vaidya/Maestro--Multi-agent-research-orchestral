/**
 * Conflict Summary Card
 * Displays conflict analysis summary
 */

import React from 'react';
import type { ConflictExplanationResponse } from '../../types/api';
import { CalmCard, CalmBadge } from './index';
import { AlertTriangle } from 'lucide-react';

interface ConflictSummaryProps {
  conflict: ConflictExplanationResponse;
}

const getSeverityBadgeClass = (severity: string): string => {
  switch (severity) {
    case 'HIGH':
      return 'bg-rose-100 text-rose-700 border-rose-200';
    case 'MEDIUM':
      return 'bg-amber-100 text-amber-700 border-amber-200';
    case 'LOW':
      return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    default:
      return 'bg-sage-100 text-sage-700 border-sage-200';
  }
};

const getSeverityIcon = (severity: string) => {
  switch (severity) {
    case 'HIGH':
      return <AlertTriangle className="w-4 h-4" />;
    case 'MEDIUM':
      return <AlertTriangle className="w-4 h-4" />;
    default:
      return null;
  }
};

export const ConflictSummary: React.FC<ConflictSummaryProps> = ({ conflict }) => {
  if (!conflict.has_conflict && conflict.severity === 'NONE') {
    return null;
  }

  const { supporting_evidence, contradicting_evidence, evidence_counts } = conflict;

  return (
    <CalmCard className="mb-8 border border-warm-divider">
      {/* Header */}
      <div className="flex items-start justify-between mb-4 pb-4 border-b border-warm-divider">
        <div className="flex items-center gap-3">
          {getSeverityIcon(conflict.severity)}
          <h3 className="text-sm font-semibold text-warm-text font-inter uppercase tracking-wide">
            Conflict Analysis
          </h3>
        </div>
        <CalmBadge className={getSeverityBadgeClass(conflict.severity)}>
          {conflict.severity === 'NONE' ? 'No Conflicts' : `${conflict.severity} Severity`}
        </CalmBadge>
      </div>

      {/* Explanation */}
      <div className="bg-warm-bg-alt rounded-lg px-4 py-3 mb-4 border border-warm-divider">
        <p className="text-sm text-warm-text font-inter leading-relaxed">
          {conflict.explanation}
        </p>
      </div>

      {/* Evidence Counts */}
      <div className="grid md:grid-cols-3 gap-3 mb-4">
        <div>
          <p className="text-xs text-warm-text-subtle font-inter uppercase tracking-wide mb-1">
            Supporting
          </p>
          <p className="text-lg font-bold text-sage-700 font-inter">
            {evidence_counts?.supports || 0}
          </p>
        </div>
        <div>
          <p className="text-xs text-warm-text-subtle font-inter uppercase tracking-wide mb-1">
            Suggesting
          </p>
          <p className="text-lg font-bold text-blue-700 font-inter">
            {evidence_counts?.suggests || 0}
          </p>
        </div>
        <div>
          <p className="text-xs text-warm-text-subtle font-inter uppercase tracking-wide mb-1">
            Contradicting
          </p>
          <p className="text-lg font-bold text-rose-700 font-inter">
            {evidence_counts?.contradicts || 0}
          </p>
        </div>
      </div>

      {/* Temporal reasoning */}
      {conflict.temporal_reasoning && (
        <div className="pt-3 border-t border-warm-divider">
          <p className="text-xs text-warm-text-subtle font-inter uppercase tracking-wide mb-2">
            Temporal Reasoning
          </p>
          <p className="text-sm text-warm-text font-inter leading-relaxed">
            {conflict.temporal_reasoning}
          </p>
        </div>
      )}
    </CalmCard>
  );
};
