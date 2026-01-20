import React from 'react';
import { CalmBadge } from '../calm';

interface EvidenceItemProps {
  evidence: {
    evidence_id: string;
    source: string;
    agent_id: string;
    quality: string;
    confidence: number;
    reference: string;
  };
  type: 'supporting' | 'contradicting';
}

/**
 * EvidenceItem - Single evidence card for conflict comparison
 * 
 * Design: Minimal, factual, no visual judgment
 * Shows: source, quality, confidence, agent, reference
 */
export const EvidenceItem: React.FC<EvidenceItemProps> = ({ evidence, type }) => {
  const getBadgeVariant = (quality: string) => {
    if (quality === 'HIGH') return 'positive';
    if (quality === 'MEDIUM') return 'info';
    return 'neutral';
  };

  // Extract clickable links from reference
  const formatReference = (ref: string): React.ReactNode => {
    // Check for PMID
    const pmidMatch = ref.match(/PMID[:\s]*(\d+)/i);
    if (pmidMatch) {
      const pmid = pmidMatch[1];
      return (
        <span>
          <a
            href={`https://pubmed.ncbi.nlm.nih.gov/${pmid}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-terracotta-600 hover:text-terracotta-700 underline"
          >
            PMID: {pmid}
          </a>
        </span>
      );
    }

    // Check for NCT (ClinicalTrials.gov)
    const nctMatch = ref.match(/NCT\d+/i);
    if (nctMatch) {
      const nct = nctMatch[0];
      return (
        <span>
          <a
            href={`https://clinicaltrials.gov/study/${nct}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-terracotta-600 hover:text-terracotta-700 underline"
          >
            {nct}
          </a>
        </span>
      );
    }

    // Check for DOI
    const doiMatch = ref.match(/10\.\d{4,}\/[^\s]+/);
    if (doiMatch) {
      const doi = doiMatch[0];
      return (
        <span>
          <a
            href={`https://doi.org/${doi}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-terracotta-600 hover:text-terracotta-700 underline"
          >
            DOI: {doi}
          </a>
        </span>
      );
    }

    // Return plain text if no match
    return <span className="text-warm-text-light">{ref}</span>;
  };

  return (
    <div className="bg-warm-surface border border-warm-divider rounded-lg p-4">
      {/* Header: Quality + Agent */}
      <div className="flex items-center gap-2 mb-3">
        <CalmBadge variant={getBadgeVariant(evidence.quality)}>
          {evidence.quality}
        </CalmBadge>
        <span className="text-xs text-warm-text-subtle font-inter uppercase tracking-wide">
          {evidence.agent_id}
        </span>
      </div>

      {/* Source */}
      <p className="text-sm font-medium text-warm-text font-inter mb-1">
        {evidence.source}
      </p>

      {/* Reference (clickable if PMID/NCT/DOI) */}
      <div className="text-sm font-inter mb-2">
        {formatReference(evidence.reference)}
      </div>

      {/* Confidence */}
      <div className="flex items-center gap-2 text-xs text-warm-text-subtle font-inter">
        <span>Confidence:</span>
        <span className="font-medium text-warm-text">
          {(evidence.confidence * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  );
};
