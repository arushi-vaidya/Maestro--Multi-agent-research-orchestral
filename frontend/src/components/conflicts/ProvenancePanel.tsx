import React, { useState } from 'react';
import { CalmCard } from '../calm';

interface ProvenancePanelProps {
  agentsInvolved: string[];
  evidenceCounts: {
    supports: number;
    contradicts: number;
    suggests: number;
  };
}

/**
 * ProvenancePanel - Transparency panel for professors
 * 
 * Design: Collapsible, factual, low-key
 * Shows: How conflicts are evaluated, which agents contributed
 */
export const ProvenancePanel: React.FC<ProvenancePanelProps> = ({
  agentsInvolved,
  evidenceCounts,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <CalmCard className="bg-warm-surface-alt">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between text-left"
      >
        <h3 className="text-base font-semibold text-warm-text font-inter">
          How this conflict was evaluated
        </h3>
        <span className="text-warm-text-subtle text-sm font-inter">
          {isOpen ? '−' : '+'}
        </span>
      </button>

      {isOpen && (
        <div className="mt-4 pt-4 border-t border-warm-divider space-y-4">
          {/* Evidence Distribution */}
          <div>
            <h4 className="text-sm font-medium text-warm-text font-inter mb-2">
              Evidence Distribution
            </h4>
            <div className="space-y-1 text-sm text-warm-text-light font-inter">
              <div className="flex justify-between">
                <span>Supporting:</span>
                <span className="font-medium text-warm-text">{evidenceCounts.supports}</span>
              </div>
              <div className="flex justify-between">
                <span>Contradicting:</span>
                <span className="font-medium text-warm-text">{evidenceCounts.contradicts}</span>
              </div>
              <div className="flex justify-between">
                <span>Suggesting:</span>
                <span className="font-medium text-warm-text">{evidenceCounts.suggests}</span>
              </div>
            </div>
          </div>

          {/* Agents Involved */}
          <div>
            <h4 className="text-sm font-medium text-warm-text font-inter mb-2">
              Agents Involved
            </h4>
            <div className="flex flex-wrap gap-2">
              {agentsInvolved.map((agent) => (
                <span
                  key={agent}
                  className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium font-inter bg-cocoa-100 text-cocoa-700"
                >
                  {agent}
                </span>
              ))}
            </div>
          </div>

          {/* Conflict Detection Method */}
          <div>
            <h4 className="text-sm font-medium text-warm-text font-inter mb-2">
              Conflict Detection Method
            </h4>
            <p className="text-sm text-warm-text-light font-inter leading-relaxed">
              Conflicts are detected using deterministic polarity analysis. Evidence marked as
              SUPPORTS is compared against CONTRADICTS polarities. No LLM inference is used in
              conflict detection—only structured evidence metadata.
            </p>
          </div>

          {/* Ranking Logic */}
          <div>
            <h4 className="text-sm font-medium text-warm-text font-inter mb-2">
              Evidence Ranking Logic
            </h4>
            <p className="text-sm text-warm-text-light font-inter leading-relaxed">
              Dominant evidence is selected using a three-tier ranking system: (1) Evidence quality
              (HIGH preferred over MEDIUM/LOW), (2) Confidence score (0.0-1.0), and (3) Temporal
              weight (recency decay applied). This ranking is deterministic and traceable.
            </p>
          </div>
        </div>
      )}
    </CalmCard>
  );
};
