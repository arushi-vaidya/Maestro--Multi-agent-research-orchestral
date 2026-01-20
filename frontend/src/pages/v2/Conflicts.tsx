/**
 * Conflict Reasoning Page
 * 
 * Purpose: Explain why evidence conflicts, which evidence dominates, and the reasoning behind conflict resolution.
 * Design: Trustworthy, slow, academic, and explainable — not flashy.
 * 
 * Backend: GET /api/conflicts/explanation (READ-ONLY)
 */

import React, { useEffect, useState } from 'react';
import { PageContainer } from '../../components/calm';
import {
  ConflictSummaryCard,
  EvidenceItem,
  DominantEvidencePanel,
  ProvenancePanel,
} from '../../components/conflicts';
import { api } from '../../services/api';
import { useQueryRefresh } from '../../context/QueryContext';
import type { ConflictExplanationResponse } from '../../types/api';

export const Conflicts: React.FC = () => {
  // Query refresh hook
  const { queryCount } = useQueryRefresh();

  const [conflicts, setConflicts] = useState<ConflictExplanationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('[Conflicts] Fetching conflicts data (queryCount:', queryCount, ')');

    setLoading(true);
    setConflicts(null); // Clear old data
    setError(null);

    api.getConflictExplanation()
      .then((data) => {
        console.log('[Conflicts] Conflicts data loaded:', data);
        setConflicts(data);
      })
      .catch((err) => {
        console.error('Error fetching conflict explanation:', err);
        setError('Unable to load conflict data. Please run a query first.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [queryCount]);


  // Extract unique agents from evidence
  const getAgentsInvolved = (): string[] => {
    if (!conflicts) return [];
    
    const agentSet = new Set<string>();
    conflicts.supporting_evidence.forEach((ev) => agentSet.add(ev.agent_id));
    conflicts.contradicting_evidence.forEach((ev) => agentSet.add(ev.agent_id));
    
    return Array.from(agentSet);
  };

  if (loading) {
    return (
      <PageContainer maxWidth="lg">
        <div className="text-center py-12">
          <p className="text-warm-text-light font-inter">Loading conflict analysis...</p>
        </div>
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer maxWidth="lg">
        <div className="text-center py-12">
          <p className="text-warm-text-light font-inter">{error}</p>
        </div>
      </PageContainer>
    );
  }

  if (!conflicts) {
    return null;
  }

  return (
    <PageContainer maxWidth="lg">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-warm-text mb-3 font-inter">
          Conflict Reasoning
        </h1>
        <p className="text-lg text-warm-text-light font-inter">
          Explaining contradictory scientific evidence with provenance and confidence
        </p>
      </div>

      {/* Conflict Summary */}
      <ConflictSummaryCard
        hasConflict={conflicts.has_conflict}
        severity={conflicts.severity}
        explanation={conflicts.explanation}
      />

      {/* Dominant Evidence Explanation (only if conflict exists) */}
      <DominantEvidencePanel
        temporalReasoning={conflicts.temporal_reasoning}
        hasConflict={conflicts.has_conflict}
      />

      {/* Evidence Comparison Panel */}
      {(conflicts.supporting_evidence.length > 0 || conflicts.contradicting_evidence.length > 0) && (
        <div className="grid md:grid-cols-2 gap-8 mb-8">
          {/* Supporting Evidence Column */}
          <div>
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-warm-text font-inter mb-1">
                Supporting Evidence
              </h3>
              <p className="text-sm text-warm-text-light font-inter">
                {conflicts.evidence_counts.supports} evidence{' '}
                {conflicts.evidence_counts.supports !== 1 ? 'pieces' : 'piece'}
              </p>
            </div>
            <div className="space-y-3">
              {conflicts.supporting_evidence.length > 0 ? (
                conflicts.supporting_evidence.map((ev, idx) => (
                  <EvidenceItem key={idx} evidence={ev} type="supporting" />
                ))
              ) : (
                <div className="bg-warm-surface-alt border border-warm-divider rounded-lg p-6 text-center">
                  <p className="text-sm text-warm-text-subtle font-inter">
                    No supporting evidence available
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Contradicting Evidence Column */}
          <div>
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-warm-text font-inter mb-1">
                Contradicting Evidence
              </h3>
              <p className="text-sm text-warm-text-light font-inter">
                {conflicts.evidence_counts.contradicts} evidence{' '}
                {conflicts.evidence_counts.contradicts !== 1 ? 'pieces' : 'piece'}
              </p>
            </div>
            <div className="space-y-3">
              {conflicts.contradicting_evidence.length > 0 ? (
                conflicts.contradicting_evidence.map((ev, idx) => (
                  <EvidenceItem key={idx} evidence={ev} type="contradicting" />
                ))
              ) : (
                <div className="bg-warm-surface-alt border border-warm-divider rounded-lg p-6 text-center">
                  <p className="text-sm text-warm-text-subtle font-inter">
                    No contradicting evidence available
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Provenance & Transparency Panel */}
      <ProvenancePanel
        agentsInvolved={getAgentsInvolved()}
        evidenceCounts={conflicts.evidence_counts}
      />
    </PageContainer>
  );
};
