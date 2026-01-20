/**
 * Conflict & Explanation Page
 * GET /api/conflicts/explanation
 */

import React, { useEffect, useState } from 'react';
import { PageContainer, CalmCard, CalmBadge } from '../../components/calm';
import { api } from '../../services/api';
import { useQueryRefresh } from '../../context/QueryContext';
import type { ConflictExplanationResponse } from '../../types/api';

export const Conflicts: React.FC = () => {
  // Query refresh hook
  const { queryCount } = useQueryRefresh();

  const [conflicts, setConflicts] = useState<ConflictExplanationResponse | null>(null);

  useEffect(() => {
    console.log('[Conflicts] Fetching conflicts data (queryCount:', queryCount, ')');
    setConflicts(null); // Clear old data
    api.getConflictExplanation()
      .then((data) => {
        console.log('[Conflicts] Conflicts data loaded:', data);
        setConflicts(data);
      })
      .catch(console.error);
  }, [queryCount]);

  const severityVariant = (severity: string) => {
    if (severity === 'HIGH') return 'warning';
    if (severity === 'MEDIUM') return 'info';
    return 'neutral';
  };

  return (
    <PageContainer maxWidth="lg">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-warm-text mb-2 font-inter">
          Conflict & Explanation
        </h1>
        <p className="text-warm-text-light font-inter">
          Detected conflicts with temporal reasoning and dominant evidence.
        </p>
      </div>

      {conflicts && (
        <>
          <CalmCard className="mb-8">
            <div className="flex items-center gap-4 mb-4">
              <CalmBadge variant={severityVariant(conflicts.severity) as any}>
                {conflicts.severity} SEVERITY
              </CalmBadge>
              <span className="text-sm text-warm-text-light font-inter">
                {conflicts.has_conflict ? 'Conflict Detected' : 'No Conflict'}
              </span>
            </div>
            <p className="text-warm-text font-inter leading-relaxed">{conflicts.explanation}</p>
            {conflicts.temporal_reasoning && (
              <p className="text-sm text-warm-text-light font-inter mt-4">
                <strong>Temporal Reasoning:</strong> {conflicts.temporal_reasoning}
              </p>
            )}
          </CalmCard>

          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="font-semibold text-warm-text mb-4 font-inter">
                Supporting Evidence ({conflicts.evidence_counts.supports})
              </h3>
              <div className="space-y-3">
                {conflicts.supporting_evidence.map((ev, idx) => (
                  <CalmCard key={idx} noPadding>
                    <div className="p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <CalmBadge variant="positive">{ev.quality}</CalmBadge>
                        <span className="text-xs text-warm-text-subtle font-inter">
                          {ev.agent_id}
                        </span>
                      </div>
                      <p className="text-sm text-warm-text font-inter">{ev.reference}</p>
                      <p className="text-xs text-warm-text-subtle font-inter mt-1">
                        Confidence: {ev.confidence.toFixed(2)}
                      </p>
                    </div>
                  </CalmCard>
                ))}
              </div>
            </div>

            <div>
              <h3 className="font-semibold text-warm-text mb-4 font-inter">
                Contradicting Evidence ({conflicts.evidence_counts.contradicts})
              </h3>
              <div className="space-y-3">
                {conflicts.contradicting_evidence.map((ev, idx) => (
                  <CalmCard key={idx} noPadding>
                    <div className="p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <CalmBadge variant="warning">{ev.quality}</CalmBadge>
                        <span className="text-xs text-warm-text-subtle font-inter">
                          {ev.agent_id}
                        </span>
                      </div>
                      <p className="text-sm text-warm-text font-inter">{ev.reference}</p>
                      <p className="text-xs text-warm-text-subtle font-inter mt-1">
                        Confidence: {ev.confidence.toFixed(2)}
                      </p>
                    </div>
                  </CalmCard>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </PageContainer>
  );
};
