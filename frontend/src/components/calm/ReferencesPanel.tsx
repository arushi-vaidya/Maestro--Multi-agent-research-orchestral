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
    <CalmCard className="border-2 border-indigo-100 bg-indigo-50/20">
      {/* Header */}
      <div className="mb-4 pb-4 border-b border-indigo-100">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-2 h-2 rounded-full bg-indigo-500" />
          <h3 className="text-sm font-semibold text-indigo-900 font-inter uppercase tracking-wide">
            Research References
          </h3>
        </div>
        <p className="text-xs text-warm-text-light font-inter">
          {references.length} sources collected from {Object.keys(refsByAgent).length} agents
        </p>
      </div>

      {/* References by Agent */}
      <div className="space-y-3">
        {Object.entries(refsByAgent).map(([agentId, refs]) => {
          const getAgentBgColor = (id: string) => {
            switch (id) {
              case 'clinical':
                return 'bg-gradient-to-r from-blue-50 to-blue-100/50 border-blue-200 hover:from-blue-100 hover:to-blue-150';
              case 'market':
                return 'bg-gradient-to-r from-emerald-50 to-emerald-100/50 border-emerald-200 hover:from-emerald-100 hover:to-emerald-150';
              case 'patent':
                return 'bg-gradient-to-r from-purple-50 to-purple-100/50 border-purple-200 hover:from-purple-100 hover:to-purple-150';
              case 'literature':
                return 'bg-gradient-to-r from-orange-50 to-orange-100/50 border-orange-200 hover:from-orange-100 hover:to-orange-150';
              default:
                return 'bg-warm-bg-alt border-warm-divider';
            }
          };

          const getAgentTextColor = (id: string) => {
            switch (id) {
              case 'clinical':
                return 'text-blue-900';
              case 'market':
                return 'text-emerald-900';
              case 'patent':
                return 'text-purple-900';
              case 'literature':
                return 'text-orange-900';
              default:
                return 'text-warm-text';
            }
          };

          return (
          <div key={agentId}>
            {/* Agent Header */}
            <button
              onClick={() => setExpandedAgent(expandedAgent === agentId ? null : agentId)}
              className={`w-full flex items-center justify-between p-3 border rounded-lg transition-colors ${getAgentBgColor(agentId)}`}
            >
              <div className="flex items-center gap-3">
                <div className={`p-1.5 rounded font-semibold ${getAgentTextColor(agentId)}`}>
                  {getAgentIcon(agentId)}
                </div>
                <div className="text-left">
                  <p className={`text-sm font-semibold font-inter capitalize ${getAgentTextColor(agentId)}`}>
                    {getAgentLabel(agentId)}
                  </p>
                  <p className="text-xs text-warm-text-light font-inter">
                    {refs.length} reference{refs.length !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
              {expandedAgent === agentId ? (
                <ChevronUp className={`w-4 h-4 ${getAgentTextColor(agentId)}`} />
              ) : (
                <ChevronDown className={`w-4 h-4 ${getAgentTextColor(agentId)}`} />
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
        );
        })}
      </div>

      {/* Footer Stats */}
      {rosMetadata && (
        <div className="mt-6 pt-4 border-t border-indigo-100">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 rounded-full bg-indigo-500" />
            <p className="text-xs font-semibold text-indigo-900 uppercase tracking-wide font-inter">
              Evidence Distribution
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 text-xs">
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
              <p className="text-emerald-700 font-bold text-lg">{rosMetadata.num_supporting_evidence || 0}</p>
              <p className="text-emerald-600 font-medium">Supporting</p>
            </div>
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-amber-700 font-bold text-lg">{rosMetadata.num_suggesting_evidence || 0}</p>
              <p className="text-amber-600 font-medium">Suggesting</p>
            </div>
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg">
              <p className="text-rose-700 font-bold text-lg">{rosMetadata.num_contradicting_evidence || 0}</p>
              <p className="text-rose-600 font-medium">Contradicting</p>
            </div>
          </div>
        </div>
      )}
    </CalmCard>
  );
};

export default ReferencesPanel;
