/**
 * TimelineEventCard
 * 
 * Individual event in the chronological timeline.
 * Shows: date, polarity, quality, summary, confidence, reference, agent.
 * 
 * Design: Clean, academic, sourced.
 */

import React, { useState } from 'react';
import type { EvidenceTimelineEvent } from '../../types/api';

interface TimelineEventCardProps {
  event: EvidenceTimelineEvent;
  index: number;
  isExpanded?: boolean;
  onToggleExpand?: (index: number) => void;
}

export const TimelineEventCard: React.FC<TimelineEventCardProps> = ({
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

  // Polarity styling
  const getPolarityStyles = (polarity: string) => {
    if (polarity === 'SUPPORTS') {
      return {
        bg: '#f0f4f0',
        border: '#6b8e6f',
        text: '#6b8e6f',
        label: 'SUPPORTS',
      };
    }
    if (polarity === 'CONTRADICTS') {
      return {
        bg: '#f5f2ee',
        border: '#a89668',
        text: '#a89668',
        label: 'CONTRADICTS',
      };
    }
    return {
      bg: '#f3f1ee',
      border: '#8b7d6b',
      text: '#8b7d6b',
      label: 'SUGGESTS',
    };
  };

  // Quality styling
  const getQualityStyles = (quality: string) => {
    if (quality === 'HIGH') {
      return {
        bg: '#f0f4f0',
        border: '#6b8e6f',
        text: '#6b8e6f',
        filled: true,
      };
    }
    if (quality === 'MEDIUM') {
      return {
        bg: 'transparent',
        border: '#8b7d6b',
        text: '#8b7d6b',
        filled: false,
      };
    }
    return {
      bg: 'transparent',
      border: '#d1c7b8',
      text: '#d1c7b8',
      filled: false,
    };
  };

  const polarity = getPolarityStyles(event.polarity);
  const quality = getQualityStyles(event.quality);

  const eventDate = new Date(event.timestamp);
  const formattedDate = eventDate.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  // Agent display name
  const agentDisplay = {
    clinical: 'Clinical',
    patent: 'Patent',
    market: 'Market',
    literature: 'Literature',
  }[event.agent_id] || event.agent_id;

  return (
    <div
      className="border bg-white transition-all duration-100 cursor-pointer"
      style={{
        borderColor: polarity.border,
        borderWidth: '1px',
        borderLeftWidth: '3px',
      }}
      onClick={handleToggle}
    >
      {/* Timeline connector dot */}
      <div 
        className="absolute left-0 w-4 h-4 rounded-full border-2 -translate-x-1.5 translate-y-6"
        style={{ borderColor: polarity.border, backgroundColor: '#FAFAF9' }}
      />

      {/* Header */}
      <div className="p-4 border-b" style={{ backgroundColor: polarity.bg, borderColor: 'rgba(58, 54, 52, 0.12)' }}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            {/* Date and polarity */}
            <div className="flex items-center gap-3 mb-2">
              <span className="text-xs font-mono" style={{ color: '#A8A39F' }}>
                {formattedDate}
              </span>
              
              {/* Polarity badge */}
              <div
                className="text-xs font-inter font-semibold px-2 py-1 border"
                style={{
                  color: polarity.text,
                  borderColor: polarity.border,
                  backgroundColor: polarity.bg,
                }}
              >
                {polarity.label}
              </div>

              {/* Quality badge */}
              <div
                className="text-xs font-inter font-semibold px-2 py-1 border"
                style={{
                  color: quality.text,
                  borderColor: quality.border,
                  backgroundColor: quality.filled ? quality.bg : 'transparent',
                }}
              >
                {event.quality}
              </div>
            </div>
          </div>

          {/* Confidence score (right) */}
          <div className="text-right">
            <div className="text-xs" style={{ color: '#A8A39F' }}>
              Confidence
            </div>
            <div className="text-lg font-semibold" style={{ color: '#3A3634' }}>
              {event.confidence.toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="p-4">
        <p className="text-sm leading-relaxed mb-3" style={{ color: '#3A3634' }}>
          {event.summary}
        </p>

        {/* Recency weight */}
        {event.recency_weight != null && (
          <div className="text-xs mb-3" style={{ color: '#A8A39F' }}>
            Recency weight: <span className="font-mono">{event.recency_weight.toFixed(3)}</span>
          </div>
        )}

        {/* Expanded content */}
        {localExpanded && (
          <div 
            className="border-t pt-3 mt-3 text-xs space-y-1" 
            style={{ borderColor: 'rgba(58, 54, 52, 0.12)', color: '#A8A39F' }}
          >
            <div><strong>Source:</strong> {event.source}</div>
            <div><strong>Agent:</strong> {agentDisplay}</div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div 
        className="px-4 py-3 border-t flex items-center justify-between"
        style={{ backgroundColor: '#FAFAF9', borderColor: 'rgba(58, 54, 52, 0.12)' }}
      >
        <div className="text-xs font-mono" style={{ color: '#A8A39F' }}>
          {event.reference_id}
        </div>
        <button
          className="text-xs transition-colors"
          style={{ color: '#5C5753' }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#3A3634')}
          onMouseLeave={(e) => (e.currentTarget.style.color = '#5C5753')}
          onClick={(e) => {
            e.stopPropagation();
            handleToggle();
          }}
        >
          {localExpanded ? 'Show less' : 'Show more'}
        </button>
      </div>
    </div>
  );
};
