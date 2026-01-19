/**
 * Evidence Timeline
 * GET /api/evidence/timeline
 */

import React, { useEffect, useState } from 'react';
import { PageContainer, CalmCard, CalmBadge } from '../../components/calm';
import { api } from '../../services/api';
import type { EvidenceTimelineResponse } from '../../types/api';

export const Timeline: React.FC = () => {
  const [timeline, setTimeline] = useState<EvidenceTimelineResponse | null>(null);

  useEffect(() => {
    api.getEvidenceTimeline().then(setTimeline).catch(console.error);
  }, []);

  const polarityColor = (polarity: string) => {
    if (polarity === 'SUPPORTS') return 'positive';
    if (polarity === 'CONTRADICTS') return 'warning';
    return 'neutral';
  };

  return (
    <PageContainer maxWidth="lg">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-warm-text mb-2 font-inter">
          Evidence Timeline
        </h1>
        <p className="text-warm-text-light font-inter">
          Chronological view of evidence with temporal decay weights.
        </p>
      </div>

      {timeline && (
        <>
          <CalmCard className="mb-8">
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-warm-text-subtle font-inter">Total Events</div>
                <div className="text-2xl font-semibold text-warm-text font-inter">
                  {timeline.total_count}
                </div>
              </div>
              <div>
                <div className="text-warm-text-subtle font-inter">Date Range</div>
                <div className="text-sm text-warm-text font-inter">
                  {timeline.date_range.earliest && new Date(timeline.date_range.earliest).toLocaleDateString()}
                  {' → '}
                  {timeline.date_range.latest && new Date(timeline.date_range.latest).toLocaleDateString()}
                </div>
              </div>
              <div>
                <div className="text-warm-text-subtle font-inter">Agents</div>
                <div className="text-sm text-warm-text font-inter">
                  {Object.keys(timeline.agent_distribution).join(', ')}
                </div>
              </div>
            </div>
          </CalmCard>

          <div className="space-y-4">
            {timeline.events.map((event, idx) => (
              <CalmCard key={idx}>
                <div className="flex items-start gap-4">
                  <div className="text-xs text-warm-text-subtle font-inter w-24 flex-shrink-0">
                    {new Date(event.timestamp).toLocaleDateString()}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <CalmBadge variant={polarityColor(event.polarity) as any}>
                        {event.polarity}
                      </CalmBadge>
                      <CalmBadge variant="info">{event.quality}</CalmBadge>
                      <span className="text-xs text-warm-text-subtle font-inter">
                        {event.agent_id}
                      </span>
                    </div>
                    <p className="text-sm text-warm-text font-inter">{event.summary}</p>
                    <p className="text-xs text-warm-text-subtle font-inter mt-1">
                      {event.reference_id}
                    </p>
                  </div>
                  <div className="text-right text-xs text-warm-text-subtle font-inter w-16">
                    {event.confidence.toFixed(2)}
                  </div>
                </div>
              </CalmCard>
            ))}
          </div>
        </>
      )}
    </PageContainer>
  );
};
