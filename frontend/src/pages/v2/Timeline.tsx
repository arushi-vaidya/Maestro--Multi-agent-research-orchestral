/**
 * Evidence Timeline
 * 
 * Academic visualization of evidence evolution over time.
 * Two-column layout: Confidence summary (left) + Chronological evidence (right)
 * 
 * Data contract: GET /api/evidence/timeline only
 * No backend changes, no inferred data, no fake timestamps.
 * 
 * Design: Like a Nature Systems paper figure.
 */

import React, { useEffect, useState } from 'react';
import { PageContainer, CalmCard, ConfidenceEvolutionCard } from '../../components/calm';
import { TimelineRangeSelector } from '../../components/calm/TimelineRangeSelector';
import { TimelineEventCard } from '../../components/calm/TimelineEventCard';
import { api } from '../../services/api';
import type { EvidenceTimelineResponse, EvidenceTimelineEvent } from '../../types/api';

export const Timeline: React.FC = () => {
  const [timeline, setTimeline] = useState<EvidenceTimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<'6m' | '1y' | '2y' | '5y' | 'all'>('all');
  const [expandedIndices, setExpandedIndices] = useState<Set<number>>(new Set());

  useEffect(() => {
    const fetchTimeline = async () => {
      try {
        setLoading(true);
        const data = await api.getEvidenceTimeline(100);
        setTimeline(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load timeline');
        console.error('Timeline fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTimeline();
  }, []);

  // Filter events by time range
  const getFilteredEvents = (events: EvidenceTimelineEvent[]): EvidenceTimelineEvent[] => {
    if (timeRange === 'all') return events;

    const now = new Date();
    const cutoffDate = new Date();
    const rangeMap = {
      '6m': 180,
      '1y': 365,
      '2y': 730,
      '5y': 1825,
    };

    cutoffDate.setDate(cutoffDate.getDate() - rangeMap[timeRange as keyof typeof rangeMap]);
    return events.filter(e => new Date(e.timestamp) >= cutoffDate);
  };

  // Sort events chronologically (oldest first)
  const getSortedEvents = (events: EvidenceTimelineEvent[]): EvidenceTimelineEvent[] => {
    return [...events].sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  };

  const filteredEvents = timeline ? getFilteredEvents(timeline.events) : [];
  const sortedEvents = getSortedEvents(filteredEvents);

  // Calculate polarity distribution for filtered events
  const getPolarityStats = () => {
    const stats = {
      SUPPORTS: 0,
      SUGGESTS: 0,
      CONTRADICTS: 0,
    };
    filteredEvents.forEach(e => {
      stats[e.polarity as keyof typeof stats]++;
    });
    return stats;
  };

  // Calculate average confidence and delta
  const computeConfidenceMetrics = () => {
    if (filteredEvents.length === 0) {
      return { avgConfidence: 0, delta: 0 };
    }

    const avgConfidence =
      filteredEvents.reduce((sum, e) => sum + e.confidence, 0) / filteredEvents.length;

    // Delta: compare first half to second half of events
    const midpoint = Math.ceil(filteredEvents.length / 2);
    const firstHalf = filteredEvents.slice(0, midpoint);
    const secondHalf = filteredEvents.slice(midpoint);

    const firstAvg = firstHalf.reduce((sum, e) => sum + e.confidence, 0) / firstHalf.length;
    const secondAvg = secondHalf.length > 0 
      ? secondHalf.reduce((sum, e) => sum + e.confidence, 0) / secondHalf.length
      : firstAvg;

    const delta = secondAvg - firstAvg;

    return { avgConfidence, delta };
  };

  const polarityStats = getPolarityStats();
  const { avgConfidence, delta } = computeConfidenceMetrics();

  const toggleExpanded = (index: number) => {
    const newSet = new Set(expandedIndices);
    if (newSet.has(index)) {
      newSet.delete(index);
    } else {
      newSet.add(index);
    }
    setExpandedIndices(newSet);
  };

  if (loading) {
    return (
      <PageContainer maxWidth="7xl">
        <div className="py-16 flex items-center justify-center">
          <p className="text-warm-text-subtle font-inter">Loading timeline...</p>
        </div>
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer maxWidth="7xl">
        <div className="py-16">
          <p className="text-red-600 font-inter">{error}</p>
        </div>
      </PageContainer>
    );
  }

  if (!timeline || timeline.events.length === 0) {
    return (
      <PageContainer maxWidth="7xl">
        <div className="py-16 flex items-center justify-center">
          <p className="text-warm-text-subtle font-inter">No evidence timeline available</p>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer maxWidth="7xl">
      {/* Page header */}
      <div className="mb-12">
        <h1 className="text-4xl font-bold text-warm-text mb-3 font-inter tracking-tight">
          EVIDENCE TIMELINE
        </h1>
        <p className="text-warm-text-light font-inter max-w-2xl">
          Chronological view of supporting, suggestive, and conflicting evidence contributing to the hypothesis.
        </p>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-3 gap-8">
        {/* LEFT COLUMN — TEMPORAL SUMMARY */}
        <div className="col-span-1 space-y-6">
          {/* Time Range Selector */}
          <div>
            <h2 className="text-xs font-inter font-semibold text-warm-text-subtle mb-3 tracking-wider">
              TIME RANGE
            </h2>
            <TimelineRangeSelector 
              selectedRange={timeRange}
              onRangeChange={setTimeRange}
            />
          </div>

          {/* Confidence Evolution Card */}
          <CalmCard>
            <ConfidenceEvolutionCard
              confidence={avgConfidence}
              delta={delta}
              fromDate={sortedEvents[0]?.timestamp || new Date().toISOString()}
              toDate={sortedEvents[sortedEvents.length - 1]?.timestamp || new Date().toISOString()}
              supports={polarityStats.SUPPORTS}
              contradicts={polarityStats.CONTRADICTS}
              suggests={polarityStats.SUGGESTS}
            />
          </CalmCard>

          {/* Summary Stats */}
          <CalmCard>
            <div className="space-y-4">
              <h3 className="text-xs font-inter font-semibold text-warm-text-subtle tracking-wider">
                EVIDENCE BREAKDOWN
              </h3>
              
              <div className="space-y-3 border-t border-warm-border pt-3">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-warm-text-subtle font-inter">Total Events</span>
                  <span className="text-lg font-semibold text-warm-text font-inter">
                    {filteredEvents.length}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-xs text-warm-text-subtle font-inter">Supporting</span>
                  <span className="text-sm text-warm-text font-inter">
                    {polarityStats.SUPPORTS}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-xs text-warm-text-subtle font-inter">Suggesting</span>
                  <span className="text-sm text-warm-text font-inter">
                    {polarityStats.SUGGESTS}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-xs text-warm-text-subtle font-inter">Contradicting</span>
                  <span className="text-sm text-warm-text font-inter">
                    {polarityStats.CONTRADICTS}
                  </span>
                </div>

                <div className="border-t border-warm-border pt-3 mt-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-warm-text-subtle font-inter">Date Range</span>
                  </div>
                  <div className="text-xs text-warm-text font-mono mt-1">
                    {sortedEvents[0] && new Date(sortedEvents[0].timestamp).toLocaleDateString()}
                    <span className="mx-1 text-warm-text-subtle">→</span>
                    {sortedEvents[sortedEvents.length - 1] && 
                      new Date(sortedEvents[sortedEvents.length - 1].timestamp).toLocaleDateString()}
                  </div>
                </div>
              </div>
            </div>
          </CalmCard>

          {/* Provenance note */}
          <div className="text-xs text-warm-text-subtle font-inter leading-relaxed p-3 border border-warm-border bg-warm-bg">
            All evidence shown is source-linked and time-stamped.
          </div>
        </div>

        {/* RIGHT COLUMN — CHRONOLOGICAL EVIDENCE TIMELINE */}
        <div className="col-span-2">
          <div className="relative pl-8">
            {/* Vertical hairline connector */}
            <div 
              className="absolute left-1.5 top-0 bottom-0 border-l border-warm-border"
              style={{ width: '1px' }}
            />

            {/* Event cards */}
            <div className="space-y-6">
              {sortedEvents.map((event, idx) => (
                <div key={idx} className="relative">
                  <TimelineEventCard
                    event={event}
                    index={idx}
                    isExpanded={expandedIndices.has(idx)}
                    onToggleExpand={toggleExpanded}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};
