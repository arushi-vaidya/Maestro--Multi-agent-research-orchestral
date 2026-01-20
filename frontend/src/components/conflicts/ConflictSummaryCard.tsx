import React from 'react';
import { CalmCard } from '../calm';
import { SeverityBadge } from './SeverityBadge';

interface ConflictSummaryCardProps {
  hasConflict: boolean;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'NONE';
  explanation: string;
}

/**
 * ConflictSummaryCard - Top-level conflict summary
 * 
 * Design: Neutral, academic, calm
 * Purpose: Quickly explain the situation without drama
 */
export const ConflictSummaryCard: React.FC<ConflictSummaryCardProps> = ({
  hasConflict,
  severity,
  explanation,
}) => {
  return (
    <CalmCard className="mb-8">
      <div className="flex items-start justify-between gap-6 mb-4">
        <div className="flex-shrink-0">
          <SeverityBadge severity={severity} hasConflict={hasConflict} />
        </div>
      </div>

      <div className="prose prose-warm max-w-none">
        <p className="text-base text-warm-text font-inter leading-relaxed m-0">
          {explanation}
        </p>
      </div>
    </CalmCard>
  );
};
