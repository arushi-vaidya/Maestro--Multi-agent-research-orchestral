/**
 * Evidence Timeline Preview
 * Displays condensed evidence events
 */

import React from 'react';
import type { EvidenceTimelineResponse } from '../../types/api';
import { CalmCard, CalmBadge } from './index';
import { TrendingUp } from 'lucide-react';

interface EvidenceTimelinePreviewProps {
  timeline: EvidenceTimelineResponse;
  limit?: number;
}

const getPolarityBadgeClass = (polarity: string): string => {
  switch (polarity) {
    case 'SUPPORTS':
      return 'bg-sage-100 text-sage-700 border-sage-200';
    case 'SUGGESTS':
      return 'bg-blue-100 text-blue-700 border-blue-200';
    case 'CONTRADICTS':
      return 'bg-rose-100 text-rose-700 border-rose-200';
    default:
      return 'bg-warm-bg-alt text-warm-text-light border-warm-divider';
  }
};

const getQualityBadgeClass = (quality: string): string => {
  switch (quality.toUpperCase()) {
    case 'HIGH':
      return 'bg-sage-50 text-sage-700';
    case 'MEDIUM':
      return 'bg-amber-50 text-amber-700';
    case 'LOW':
      return 'bg-rose-50 text-rose-700';
    default:
      return 'bg-warm-bg-alt text-warm-text-light';
  }
};

const AGENT_LABELS: Record<string, string> = {
  clinical: 'Clinical',
  patent: 'Patent',
  market: 'Market',
  literature: 'Literature',
};

const getAgentLabel = (agentId: string): string => {
  return AGENT_LABELS[agentId.toLowerCase()] || agentId;
};

export const EvidenceTimelinePreview: React.FC<EvidenceTimelinePreviewProps> = ({
  timeline,
  limit = 5,
}) => {
  if (!timeline.events || timeline.events.length === 0) {
    return null;
  }

  const events = timeline.events.slice(0, limit);

  return (
    <CalmCard className="mb-8 border border-warm-divider">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4 pb-4 border-b border-warm-divider">
        <TrendingUp className="w-5 h-5 text-blue-600 flex-shrink-0" />
        <h3 className="text-sm font-semibold text-warm-text font-inter uppercase tracking-wide">
          Recent Evidence
        </h3>
        <span className="text-xs text-warm-text-light font-inter ml-auto">
          {events.length} of {timeline.total_count} events
        </span>
      </div>

      {/* Events List */}
      <div className="space-y-3">
        {events.map((event, index) => (
          <div key={event.reference_id || index} className="rounded-lg border border-warm-divider p-3">
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex-1">
                <p className="text-sm font-semibold text-warm-text font-inter line-clamp-2">
                  {event.summary || event.source || 'Evidence'}
                </p>
              </div>
              <div className="flex gap-2 flex-wrap justify-end">
                <CalmBadge className={getPolarityBadgeClass(event.polarity)}>
                  {event.polarity}
                </CalmBadge>
                <CalmBadge className={getQualityBadgeClass(event.quality)}>
                  {event.quality}
                </CalmBadge>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-warm-text-light font-inter">
              <span>{getAgentLabel(event.agent_id)}</span>
              {event.timestamp && (
                <span>
                  {new Date(event.timestamp).toLocaleDateString()} at{' '}
                  {new Date(event.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* View more link */}
      {timeline.total_count > limit && (
        <div className="mt-4 pt-4 border-t border-warm-divider">
          <p className="text-xs text-blue-600 font-inter font-semibold">
            View {timeline.total_count - limit} more events →
          </p>
        </div>
      )}
    </CalmCard>
  );
};
