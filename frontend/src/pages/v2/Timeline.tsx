/**
 * Evidence Timeline - Redesigned
 *
 * STEP 8: Frontend Research Dashboard - Evidence Timeline
 *
 * Purpose:
 * Present evidence evolution over time for a selected Drug → Disease relationship.
 * Shows confidence score evolution, polarity tracking, and chronological organization.
 *
 * Layout:
 * - Top: Page header and filter bar
 * - Left: Confidence summary panel
 * - Right: Vertical chronological timeline
 *
 * Data Sources (READ-ONLY):
 * - GET /api/evidence/timeline (main evidence events)
 * - GET /api/ros/latest (confidence scores)
 *
 * Design Philosophy:
 * "A calm scientific ledger showing how belief evolves over time."
 * Warm minimal palette, professional, trustworthy, not flashy.
 */

import React, { useEffect, useState } from 'react';
import { PageContainer, CalmCard } from '../../components/calm';
import { TimelineRangeSelector } from '../../components/calm/TimelineRangeSelector';
import { EvidenceTimelineCard } from '../../components/calm/EvidenceTimelineCard';
import { ConfidenceSummaryCard } from '../../components/calm/ConfidenceSummaryCard';
import { api } from '../../services/api';
import type { EvidenceTimelineResponse, EvidenceTimelineEvent, ROSViewResponse } from '../../types/api';

/**
 * Timeline.tsx - Main Evidence Timeline Page
 *
 * Responsibilities:
 * 1. Fetch evidence timeline from backend
 * 2. Fetch ROS confidence scores
 * 3. Filter by time range
 * 4. Render left summary panel + right timeline
 * 5. Handle interactions (expand events, change filters)
 *
 * All data comes from backend - no mock data, no inference.
 */
export const Timeline: React.FC = () => {
  // State management
  const [timeline, setTimeline] = useState<EvidenceTimelineResponse | null>(null);
  const [rosData, setRosData] = useState<ROSViewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<'6m' | '1y' | '2y' | '5y' | 'all'>('all');
  const [expandedIndices, setExpandedIndices] = useState<Set<number>>(new Set());

  /**
   * Effect: Load timeline and ROS data on mount
   */
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch timeline events
        const timelineData = await api.getEvidenceTimeline(100);
        setTimeline(timelineData);

        // Fetch latest ROS scores (for confidence panel)
        try {
          const ros = await api.getROSLatest();
          setRosData(ros);
        } catch {
          // ROS data is optional - timeline can still render
          console.warn('Could not fetch ROS data');
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load evidence timeline';
        setError(message);
        console.error('Timeline fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  /**
   * Filter events by time range
   * Handles: 6m, 1y, 2y, 5y, all
   */
  const getFilteredEvents = (events: EvidenceTimelineEvent[]): EvidenceTimelineEvent[] => {
    if (timeRange === 'all') return events;

    const cutoffDate = new Date();
    const rangeMap: Record<string, number> = {
      '6m': 180,
      '1y': 365,
      '2y': 730,
      '5y': 1825,
    };

    const daysAgo = rangeMap[timeRange] || 365;
    cutoffDate.setDate(cutoffDate.getDate() - daysAgo);

    return events.filter((e) => new Date(e.timestamp) >= cutoffDate);
  };

  /**
   * Sort events chronologically: newest at top
   * (Most recent evidence first for better UX)
   */
  const getSortedEvents = (events: EvidenceTimelineEvent[]): EvidenceTimelineEvent[] => {
    return [...events].sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  };

  /**
   * Calculate polarity distribution for filtered events
   */
  const getPolarityStats = () => {
    const stats = {
      SUPPORTS: 0,
      SUGGESTS: 0,
      CONTRADICTS: 0,
    };
    filteredEvents.forEach((e) => {
      stats[e.polarity as keyof typeof stats]++;
    });
    return stats;
  };

  /**
   * Compute confidence metrics
   * - Average confidence across filtered events
   * - Delta: change from first half to second half
   */
  const computeConfidenceMetrics = () => {
    if (filteredEvents.length === 0) {
      return { avgConfidence: 0, delta: 0 };
    }

    const avgConfidence =
      filteredEvents.reduce((sum, e) => sum + e.confidence, 0) / filteredEvents.length;

    // Delta: compare first half to second half
    const midpoint = Math.ceil(filteredEvents.length / 2);
    const firstHalf = filteredEvents.slice(0, midpoint);
    const secondHalf = filteredEvents.slice(midpoint);

    const firstAvg = firstHalf.reduce((sum, e) => sum + e.confidence, 0) / firstHalf.length;
    const secondAvg = 
      secondHalf.length > 0
        ? secondHalf.reduce((sum, e) => sum + e.confidence, 0) / secondHalf.length
        : firstAvg;

    const delta = secondAvg - firstAvg;

    return { avgConfidence, delta };
  };

  // Compute derived data
  const filteredEvents = timeline ? getFilteredEvents(timeline.events) : [];
  const sortedEvents = getSortedEvents(filteredEvents);
  const polarityStats = getPolarityStats();
  const { avgConfidence, delta } = computeConfidenceMetrics();

  /**
   * Toggle expanded state for event card
   */
  const toggleExpanded = (index: number) => {
    const newSet = new Set(expandedIndices);
    if (newSet.has(index)) {
      newSet.delete(index);
    } else {
      newSet.add(index);
    }
    setExpandedIndices(newSet);
  };

  /**
   * Reset all filters and scroll to top
   */
  const handleNewQuery = () => {
    setTimeRange('all');
    setExpandedIndices(new Set());
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // ============================================================================
  // RENDER: LOADING STATE
  // ============================================================================
  if (loading) {
    return (
      <PageContainer maxWidth="7xl">
        <div className="py-16 flex items-center justify-center">
          <p className="text-warm-text-subtle font-inter">Loading timeline...</p>
        </div>
      </PageContainer>
    );
  }

  // ============================================================================
  // RENDER: ERROR STATE
  // ============================================================================
  if (error) {
    return (
      <PageContainer maxWidth="7xl">
        <div className="py-16">
          <p className="text-red-600 font-inter">{error}</p>
        </div>
      </PageContainer>
    );
  }

  // ============================================================================
  // RENDER: EMPTY STATE
  // ============================================================================
  if (!timeline || timeline.events.length === 0) {
    return (
      <PageContainer maxWidth="7xl">
        <div className="py-16 flex items-center justify-center">
          <p className="text-warm-text-subtle font-inter">No evidence timeline available</p>
        </div>
      </PageContainer>
    );
  }

  // ============================================================================
  // RENDER: MAIN TIMELINE PAGE
  // ============================================================================
  return (
    <PageContainer maxWidth="7xl">
      {/* ========================================================================
          TOP BAR — PAGE TITLE & SUBTITLE
          ======================================================================== */}
      <div className="mb-12 flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-bold text-warm-text mb-2 font-inter tracking-tight">
            Evidence Timeline
          </h1>
          <p className="text-sm text-warm-text-light font-inter max-w-2xl leading-relaxed">
            Track how scientific evidence evolves over time for drug repurposing hypotheses
          </p>
        </div>
        <button
          type="button"
          onClick={handleNewQuery}
          className="relative z-50 px-4 py-2 text-xs font-inter font-semibold text-warm-text border border-warm-border hover:bg-warm-bg active:bg-warm-border transition-colors rounded-sm cursor-pointer whitespace-nowrap"
        >
          New Query
        </button>
      </div>

      {/* ========================================================================
          FILTER BAR — TIME RANGE SELECTOR
          ======================================================================== */}
      <div className="mb-8 p-4 bg-warm-bg border border-warm-border rounded-lg">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h3 className="text-xs font-inter font-semibold text-warm-text-subtle tracking-wider mb-2">
              TIME RANGE
            </h3>
            <TimelineRangeSelector 
              selectedRange={timeRange}
              onRangeChange={setTimeRange}
            />
          </div>
          
          <div className="text-right text-xs font-inter text-warm-text-subtle">
            <div className="font-semibold text-warm-text">{filteredEvents.length}</div>
            <div>events shown</div>
          </div>
        </div>
      </div>

      {/* ========================================================================
          TWO-COLUMN LAYOUT: LEFT PANEL (CONFIDENCE) + RIGHT PANEL (TIMELINE)
          ======================================================================== */}
      <div className="grid grid-cols-3 gap-8">
        
        {/* ====================================================================
            LEFT COLUMN (1/3) — CONFIDENCE SUMMARY PANEL
            ==================================================================== */}
        <div className="col-span-1">
          <div className="space-y-6 sticky top-20">
            {/* Confidence Summary Card */}
            <ConfidenceSummaryCard
              confidence={avgConfidence}
              delta={delta}
              rosData={rosData}
              filteredEventsCount={filteredEvents.length}
              polarityStats={polarityStats}
              dateRange={{
                earliest: sortedEvents[sortedEvents.length - 1]?.timestamp || '',
                latest: sortedEvents[0]?.timestamp || '',
              }}
            />

            {/* Evidence Type Breakdown */}
            <CalmCard>
              <div className="space-y-4">
                <h3 className="text-xs font-inter font-semibold text-warm-text-subtle tracking-wider uppercase">
                  Evidence Breakdown
                </h3>
                
                <div className="space-y-3 border-t border-warm-border pt-4">
                  {/* Supporting */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: '#6b8e6f' }}
                      />
                      <span className="text-xs text-warm-text-subtle font-inter">
                        Supporting (+)
                      </span>
                    </div>
                    <span className="text-sm font-semibold text-warm-text font-inter">
                      {polarityStats.SUPPORTS}
                    </span>
                  </div>

                  {/* Suggesting */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: '#d4a574' }}
                      />
                      <span className="text-xs text-warm-text-subtle font-inter">
                        Suggesting (±)
                      </span>
                    </div>
                    <span className="text-sm font-semibold text-warm-text font-inter">
                      {polarityStats.SUGGESTS}
                    </span>
                  </div>

                  {/* Contradicting */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: '#a89668' }}
                      />
                      <span className="text-xs text-warm-text-subtle font-inter">
                        Contradicting (−)
                      </span>
                    </div>
                    <span className="text-sm font-semibold text-warm-text font-inter">
                      {polarityStats.CONTRADICTS}
                    </span>
                  </div>
                </div>

                {/* Total */}
                <div className="border-t border-warm-border pt-3 mt-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-warm-text font-inter">
                      Total Events
                    </span>
                    <span className="text-lg font-bold text-warm-text font-inter">
                      {filteredEvents.length}
                    </span>
                  </div>
                </div>
              </div>
            </CalmCard>

            {/* Date Range Info */}
            <div className="text-xs text-warm-text-subtle font-inter leading-relaxed p-4 border border-warm-border bg-warm-bg rounded-lg">
              <div className="font-semibold text-warm-text mb-2">Date Range</div>
              <div className="space-y-1">
                <div>
                  <span className="text-warm-text-subtle">From:</span>
                  {' '}
                  <span className="text-warm-text font-mono">
                    {sortedEvents.length > 0
                      ? new Date(sortedEvents[sortedEvents.length - 1].timestamp).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                        })
                      : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-warm-text-subtle">To:</span>
                  {' '}
                  <span className="text-warm-text font-mono">
                    {sortedEvents.length > 0
                      ? new Date(sortedEvents[0].timestamp).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                        })
                      : 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            {/* Provenance Note */}
            <div className="text-xs text-warm-text-subtle font-inter leading-relaxed p-3 border border-warm-border rounded-lg italic">
              ✓ All evidence is source-linked and timestamped. No inference.
            </div>
          </div>
        </div>

        {/* ====================================================================
            RIGHT COLUMN (2/3) — VERTICAL CHRONOLOGICAL TIMELINE
            ==================================================================== */}
        <div className="col-span-2">
          <div className="relative pl-10">
            {/* Vertical timeline spine */}
            <div 
              className="absolute left-3.5 top-0 bottom-0 border-l-2 border-warm-border"
              style={{ width: '1px' }}
            />

            {/* Event cards - newest at top */}
            <div className="space-y-6">
              {sortedEvents.length > 0 ? (
                sortedEvents.map((event, idx) => (
                  <div key={`${event.reference_id}-${idx}`} className="relative">
                    {/* Timeline node marker */}
                    <div 
                      className="absolute left-0 w-4 h-4 rounded-full border-2 bg-white -translate-x-1.5 translate-y-6 transition-all duration-200"
                      style={{
                        borderColor: 
                          event.polarity === 'SUPPORTS'
                            ? '#6b8e6f'
                            : event.polarity === 'CONTRADICTS'
                              ? '#a89668'
                              : '#d4a574',
                      }}
                    />

                    {/* Evidence card */}
                    <EvidenceTimelineCard
                      event={event}
                      index={idx}
                      isExpanded={expandedIndices.has(idx)}
                      onToggleExpand={toggleExpanded}
                    />
                  </div>
                ))
              ) : (
                <div className="text-center py-12 text-warm-text-subtle font-inter">
                  No events in selected time range
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};
