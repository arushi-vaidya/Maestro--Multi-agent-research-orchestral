/**
 * References Panel
 * Displays all collected references from agents with hyperlinks
 */

import React, { useState } from 'react';
import { CalmCard, CalmBadge } from './index';
import { ExternalLink, ChevronDown, ChevronUp, FileText, Lightbulb, Beaker, BarChart3 } from 'lucide-react';

export interface Reference {
  type: string;
  title: string;
  source: string;
  date: string;
  url: string;
  relevance: number;
  agentId: string;
}

interface ReferencesPanelProps {
  references: Reference[];
  rosMetadata?: {
    num_supporting_evidence?: number;
    num_contradicting_evidence?: number;
    num_suggesting_evidence?: number;
    distinct_agents?: string[];
  };
}

const getAgentIcon = (agentId: string) => {
  switch (agentId) {
    case 'clinical':
      return <Beaker className="w-4 h-4" />;
    case 'market':
      return <BarChart3 className="w-4 h-4" />;
    case 'patent':
      return <Lightbulb className="w-4 h-4" />;
    case 'literature':
      return <FileText className="w-4 h-4" />;
    default:
      return <FileText className="w-4 h-4" />;
  }
};

const getAgentLabel = (agentId: string) => {
  switch (agentId) {
    case 'clinical':
      return 'Clinical Trials';
    case 'market':
      return 'Market Intelligence';
    case 'patent':
      return 'Patents';
    case 'literature':
      return 'Literature';
    default:
      return agentId;
  }
};

const getTypeColor = (type: string) => {
  switch (type) {
    case 'patent':
      return 'bg-purple-50 text-purple-700 border-purple-200';
    case 'paper':
    case 'literature':
      return 'bg-blue-50 text-blue-700 border-blue-200';
    case 'clinical-trial':
      return 'bg-green-50 text-green-700 border-green-200';
    case 'market-report':
      return 'bg-orange-50 text-orange-700 border-orange-200';
    default:
      return 'bg-gray-50 text-gray-700 border-gray-200';
  }
};

const getRelevanceColor = (relevance: number) => {
  if (relevance >= 0.8) return 'text-sage-700';
  if (relevance >= 0.6) return 'text-amber-700';
  return 'text-rose-700';
};

const ReferencesPanel: React.FC<ReferencesPanelProps> = ({ references, rosMetadata }) => {
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);
  const [expandedRef, setExpandedRef] = useState<Set<string>>(new Set());

  // Group references by agent
  const refsByAgent = references.reduce((acc, ref) => {
    if (!acc[ref.agentId]) {
      acc[ref.agentId] = [];
    }
    acc[ref.agentId].push(ref);
    return acc;
  }, {} as Record<string, Reference[]>);

  const toggleRef = (refId: string) => {
    const newSet = new Set(expandedRef);
    if (newSet.has(refId)) {
      newSet.delete(refId);
    } else {
      newSet.add(refId);
    }
    setExpandedRef(newSet);
  };

  return (
    <CalmCard className="border border-warm-divider">
      {/* Header */}
      <div className="mb-4 pb-4 border-b border-warm-divider">
        <h3 className="text-sm font-semibold text-warm-text font-inter uppercase tracking-wide mb-2">
          Research References
        </h3>
        <p className="text-xs text-warm-text-light font-inter">
          {references.length} sources collected from {Object.keys(refsByAgent).length} agents
        </p>
      </div>

      {/* References by Agent */}
      <div className="space-y-3">
        {Object.entries(refsByAgent).map(([agentId, refs]) => (
          <div key={agentId}>
            {/* Agent Header */}
            <button
              onClick={() => setExpandedAgent(expandedAgent === agentId ? null : agentId)}
              className="w-full flex items-center justify-between p-3 bg-warm-bg-alt border border-warm-divider rounded-lg hover:bg-warm-divider/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="p-1.5 bg-white border border-warm-divider rounded">
                  {getAgentIcon(agentId)}
                </div>
                <div className="text-left">
                  <p className="text-sm font-semibold text-warm-text font-inter capitalize">
                    {getAgentLabel(agentId)}
                  </p>
                  <p className="text-xs text-warm-text-light font-inter">
                    {refs.length} reference{refs.length !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
              {expandedAgent === agentId ? (
                <ChevronUp className="w-4 h-4 text-warm-text-subtle" />
              ) : (
                <ChevronDown className="w-4 h-4 text-warm-text-subtle" />
              )}
            </button>

            {/* Expanded References */}
            {expandedAgent === agentId && (
              <div className="mt-2 ml-3 space-y-2 border-l-2 border-warm-divider pl-3">
                {refs.map((ref, idx) => {
                  const refId = `${agentId}-${idx}`;
                  const isExpanded = expandedRef.has(refId);

                  return (
                    <div key={refId} className="bg-white border border-warm-divider rounded-lg overflow-hidden">
                      {/* Reference Summary */}
                      <button
                        onClick={() => toggleRef(refId)}
                        className="w-full p-3 hover:bg-warm-bg-alt transition-colors text-left"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <CalmBadge className={`text-xs capitalize ${getTypeColor(ref.type)}`}>
                                {ref.type}
                              </CalmBadge>
                              <span className={`text-xs font-semibold ${getRelevanceColor(ref.relevance)}`}>
                                {(ref.relevance * 100).toFixed(0)}% relevant
                              </span>
                            </div>
                            <p className="text-sm font-medium text-warm-text font-inter line-clamp-2 mb-1">
                              {ref.title}
                            </p>
                            <p className="text-xs text-warm-text-light font-inter line-clamp-1">
                              {ref.source} • {ref.date}
                            </p>
                          </div>
                          <div className="flex-shrink-0 ml-2">
                            {ref.url ? (
                              <a
                                href={ref.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(e) => e.stopPropagation()}
                                className="p-1.5 hover:bg-warm-divider rounded transition-colors"
                                title="Open reference"
                              >
                                <ExternalLink className="w-4 h-4 text-sage-600" />
                              </a>
                            ) : (
                              <div className="p-1.5" />
                            )}
                          </div>
                        </div>
                      </button>

                      {/* Expanded Details */}
                      {isExpanded && (
                        <div className="px-3 py-2 bg-warm-bg-alt border-t border-warm-divider text-xs space-y-1">
                          {ref.url && (
                            <p className="break-all text-warm-text-light font-inter">
                              <span className="font-semibold text-warm-text">URL: </span>
                              <a
                                href={ref.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sage-600 hover:underline"
                              >
                                {ref.url}
                              </a>
                            </p>
                          )}
                          <p className="text-warm-text-light font-inter">
                            <span className="font-semibold text-warm-text">Source: </span>
                            {ref.source}
                          </p>
                          <p className="text-warm-text-light font-inter">
                            <span className="font-semibold text-warm-text">Type: </span>
                            {ref.type}
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer Stats */}
      {rosMetadata && (
        <div className="mt-6 pt-4 border-t border-warm-divider">
          <p className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wide mb-2 font-inter">
            Evidence Distribution
          </p>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="p-2 bg-sage-50 border border-sage-100 rounded">
              <p className="text-sage-700 font-semibold">{rosMetadata.num_supporting_evidence || 0}</p>
              <p className="text-sage-600">Supporting</p>
            </div>
            <div className="p-2 bg-amber-50 border border-amber-100 rounded">
              <p className="text-amber-700 font-semibold">{rosMetadata.num_suggesting_evidence || 0}</p>
              <p className="text-amber-600">Suggesting</p>
            </div>
            <div className="p-2 bg-rose-50 border border-rose-100 rounded">
              <p className="text-rose-700 font-semibold">{rosMetadata.num_contradicting_evidence || 0}</p>
              <p className="text-rose-600">Contradicting</p>
            </div>
          </div>
        </div>
      )}
    </CalmCard>
  );
};

export default ReferencesPanel;
