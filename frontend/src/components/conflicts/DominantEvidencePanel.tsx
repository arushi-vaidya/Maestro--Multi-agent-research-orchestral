import React from 'react';
import { CalmCard } from '../calm';

interface DominantEvidencePanelProps {
  temporalReasoning: string | null;
  hasConflict: boolean;
}

/**
 * DominantEvidencePanel - Explains why certain evidence dominates
 * 
 * Design: Highlighted but calm, academic explanation
 * Shows: Ranking logic (Quality → Confidence → Temporal)
 */
export const DominantEvidencePanel: React.FC<DominantEvidencePanelProps> = ({
  temporalReasoning,
  hasConflict,
}) => {
  if (!hasConflict || !temporalReasoning) {
    return null;
  }

  return (
    <CalmCard className="mb-8 bg-sage-50 border-sage-200">
      <div className="mb-3">
        <h3 className="text-lg font-semibold text-warm-text font-inter">
          Why This Evidence Dominates
        </h3>
      </div>

      <div className="prose prose-warm max-w-none">
        <p className="text-base text-warm-text font-inter leading-relaxed mb-4">
          {temporalReasoning}
        </p>

        <div className="text-sm text-warm-text-light font-inter space-y-1">
          <p className="font-medium text-warm-text mb-2">Conflict resolution priority:</p>
          <ol className="list-decimal list-inside space-y-1 ml-2">
            <li>Evidence quality (HIGH &gt; MEDIUM &gt; LOW)</li>
            <li>Confidence score (higher confidence preferred)</li>
            <li>Temporal recency (newer evidence weighted higher)</li>
          </ol>
        </div>
      </div>
    </CalmCard>
  );
};
