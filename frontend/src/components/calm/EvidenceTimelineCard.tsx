/**
 * EvidenceTimelineCard
 *
 * Individual evidence event card in the chronological timeline.
 *
 * Structure:
 * ┌─────────────────────────────────────────┐
 * │ HEADER: Date | Polarity | Quality | Conf│
 * ├─────────────────────────────────────────┤
 * │ BODY: Title & Summary                   │
 * │ Source Metadata (CT ID, PMID, etc.)    │
 * ├─────────────────────────────────────────┤
 * │ FOOTER: Reference ID | "Show more"      │
 * └─────────────────────────────────────────┘
 *
 * Design:
 * - Polarity-based left border (green/amber/red)
 * - Subtle background tint based on polarity
 * - Expandable for additional details
 * - Source hyperlinks
 * - Clean typography
 */

import React, { useState } from 'react';
import type { EvidenceTimelineEvent } from '../../types/api';

interface EvidenceTimelineCardProps {
  event: EvidenceTimelineEvent;
  index: number;
  isExpanded?: boolean;
  onToggleExpand?: (index: number) => void;
}

/**
 * Helper: Get polarity styling
 */
const getPolarityStyle = (
  polarity: 'SUPPORTS' | 'SUGGESTS' | 'CONTRADICTS',
) => {
  if (polarity === 'SUPPORTS') {
    return {
      borderColor: '#6b8e6f',
      backgroundColor: '#f5f9f6',
      badgeBg: '#6b8e6f',
      badgeText: '#fff',
      label: 'SUPPORTS',
    };
  }
  if (polarity === 'CONTRADICTS') {
    return {
      borderColor: '#a89668',
      backgroundColor: '#faf8f4',
      badgeBg: '#a89668',
      badgeText: '#fff',
      label: 'CONTRADICTS',
    };
  }
  // SUGGESTS
  return {
    borderColor: '#d4a574',
    backgroundColor: '#fdf9f3',
    badgeBg: '#d4a574',
    badgeText: '#fff',
    label: 'SUGGESTS',
  };
};

/**
 * Helper: Get quality styling
 */
const getQualityStyle = (quality: 'LOW' | 'MEDIUM' | 'HIGH') => {
  if (quality === 'HIGH') {
    return {
      bg: '#6b8e6f',
      text: '#fff',
    };
  }
  if (quality === 'MEDIUM') {
    return {
      bg: '#d4a574',
      text: '#fff',
    };
  }
  // LOW
  return {
    bg: '#c4b8aa',
    text: '#fff',
  };
};

/**
 * Helper: Get agent display name
 */
const getAgentDisplay = (agentId: string): string => {
  const map: Record<string, string> = {
    clinical: 'Clinical Trial',
    patent: 'Patent',
    market: 'Market Signal',
    literature: 'Literature Review',
    web: 'Web Search',
  };
  return map[agentId] || agentId;
};

/**
 * Helper: Format date
 */
const formatDate = (timestamp: string): string => {
  const date = new Date(timestamp);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

/**
 * Helper: Build source links
 * Infers link type from reference_id
 */
const getSourceLink = (referenceId: string, source: string): { url?: string; type?: string } => {
  // NCT: ClinicalTrials.gov
  if (referenceId.toUpperCase().startsWith('NCT')) {
    return {
      url: `https://clinicaltrials.gov/study/${referenceId}`,
      type: 'ClinicalTrials.gov',
    };
  }

  // PMID: PubMed
  if (referenceId.toUpperCase().startsWith('PMID:') || /^\d+$/.test(referenceId)) {
    const pmid = referenceId.replace('PMID:', '');
    return {
      url: `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`,
      type: 'PubMed',
    };
  }

  // DOI
  if (referenceId.toUpperCase().startsWith('DOI:')) {
    const doi = referenceId.replace('DOI:', '');
    return {
      url: `https://doi.org/${doi}`,
      type: 'DOI',
    };
  }

  // Generic URL
  if (source && (source.includes('http') || source.includes('www'))) {
    return {
      url: source,
      type: 'Source',
    };
  }

  return {};
};

/**
 * EvidenceTimelineCard Component
 */
export const EvidenceTimelineCard: React.FC<EvidenceTimelineCardProps> = ({
  event,
  index,
  isExpanded = false,
  onToggleExpand,
}) => {
  const [localExpanded, setLocalExpanded] = useState(isExpanded);

  const handleToggle = () => {
    const newExpanded = !localExpanded;
    setLocalExpanded(newExpanded);
    onToggleExpand?.(index);
  };

  const polarityStyle = getPolarityStyle(event.polarity);
  const qualityStyle = getQualityStyle(event.quality);
  const agentDisplay = getAgentDisplay(event.agent_id);
  const formattedDate = formatDate(event.timestamp);
  const sourceLink = getSourceLink(event.reference_id, event.source);

  return (
    <div
      className="border-l-4 rounded-r-lg overflow-hidden transition-all duration-200 bg-white shadow-sm hover:shadow-md"
      style={{
        borderLeftColor: polarityStyle.borderColor,
        borderTopRightRadius: '0.5rem',
        borderBottomRightRadius: '0.5rem',
      }}
    >
      {/* ====================================================================
          HEADER: Date | Polarity | Quality | Confidence
          ==================================================================== */}
      <div
        className="px-5 py-4 border-b border-gray-200"
        style={{
          backgroundColor: polarityStyle.backgroundColor,
        }}
      >
        <div className="flex items-start justify-between gap-4">
          {/* Left: Date + Badges */}
          <div className="flex-1 space-y-3">
            {/* Date */}
            <div className="text-xs font-mono text-warm-text-subtle">
              {formattedDate}
            </div>

            {/* Badge row: Polarity + Quality */}
            <div className="flex flex-wrap gap-2">
              {/* Polarity badge */}
              <div
                className="px-2.5 py-1 text-xs font-semibold rounded text-white"
                style={{
                  backgroundColor: polarityStyle.badgeBg,
                }}
              >
                {polarityStyle.label}
              </div>

              {/* Quality badge */}
              <div
                className="px-2.5 py-1 text-xs font-semibold rounded text-white"
                style={{
                  backgroundColor: qualityStyle.bg,
                }}
              >
                {event.quality}
              </div>
            </div>
          </div>

          {/* Right: Confidence + Delta */}
          <div className="text-right space-y-1 flex-shrink-0">
            <div className="text-xs text-warm-text-subtle">Confidence</div>
            <div className="text-lg font-bold text-warm-text">
              {(event.confidence * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      </div>

      {/* ====================================================================
          BODY: Title (Summary) & Source Metadata
          ==================================================================== */}
      <div className="px-5 py-4 space-y-3">
        {/* Main summary */}
        <p className="text-sm leading-relaxed text-warm-text font-inter">
          {event.summary || 'Evidence supporting hypothesis'}
        </p>

        {/* Source metadata */}
        <div className="text-xs text-warm-text-subtle font-mono space-y-1 border-t border-gray-200 pt-3">
          <div>
            <span className="font-semibold">Source:</span> {event.source}
          </div>
          <div>
            <span className="font-semibold">Agent:</span> {agentDisplay}
          </div>
          {event.reference_id && (
            <div>
              <span className="font-semibold">ID:</span> {event.reference_id}
            </div>
          )}
          {event.recency_weight != null && (
            <div>
              <span className="font-semibold">Recency:</span> {event.recency_weight.toFixed(3)}
            </div>
          )}
        </div>

        {/* Expanded content: Source links */}
        {localExpanded && (
          <div className="border-t border-gray-200 pt-3 space-y-2">
            {sourceLink.url && (
              <div>
                <a
                  href={sourceLink.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-inter text-blue-600 hover:underline inline-flex items-center gap-1"
                >
                  View on {sourceLink.type} →
                </a>
              </div>
            )}

            {/* Additional expanded info */}
            <div className="text-xs text-warm-text-subtle italic">
              All source data retrieved from backend. No inference applied.
            </div>
          </div>
        )}
      </div>

      {/* ====================================================================
          FOOTER: Reference ID | "Show more" button
          ==================================================================== */}
      <div
        className="px-5 py-3 border-t border-gray-200 flex items-center justify-between bg-warm-bg"
        style={{
          backgroundColor: '#f9f8f7',
        }}
      >
        <div className="text-xs font-mono text-warm-text-subtle truncate">
          {event.reference_id}
        </div>
        <button
          onClick={handleToggle}
          className="text-xs font-inter font-semibold text-warm-text hover:text-warm-text-light transition-colors cursor-pointer"
        >
          {localExpanded ? 'Show less' : 'Show more'}
        </button>
      </div>
    </div>
  );
};
