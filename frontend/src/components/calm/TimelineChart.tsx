/**
 * TimelineChart - Confidence Evolution Visualization
 * 
 * SCIENTIFIC VISUALIZATION (NOT a decorative chart)
 * 
 * This component:
 * 1. Aggregates discrete evidence events into time buckets
 * 2. Computes net confidence per bucket using weighted polarity scoring
 * 3. Normalizes to [-1, +1] range for trend visualization
 * 4. Renders 2D area chart with separate polarity traces
 * 
 * DATA TRANSFORMATION LOGIC:
 * 
 * For each time bucket (day or month depending on range):
 *   score = Σ (confidence × recency_weight × polarity_multiplier)
 * 
 * Where:
 *   SUPPORTS      → +1.0 multiplier
 *   SUGGESTS      → +0.5 multiplier  
 *   CONTRADICTS   → -1.0 multiplier
 * 
 * This produces a signed confidence trend reflecting evidence balance.
 * 
 * Design: Academic, deterministic, explainable to peers
 */

import React, { useMemo } from 'react';
import type { EvidenceTimelineEvent } from '../../types/api';

interface TimelineChartProps {
  events: EvidenceTimelineEvent[];
  timeRange: '6m' | '1y' | '2y' | '5y' | 'all';
}

interface BucketData {
  date: string;
  supports: number;
  suggests: number;
  contradicts: number;
}

export const TimelineChart: React.FC<TimelineChartProps> = ({ events, timeRange }) => {
  /**
   * Compute aggregated bucket data from discrete events
   * Deterministic pure function - no side effects
   */
  const chartData = useMemo(() => {
    if (!events || events.length === 0) return null;

    console.debug('[TimelineChart] Raw events:', events.length);
    console.debug('[TimelineChart] Event details:', events.slice(0, 5).map(e => ({
      timestamp: e.timestamp,
      confidence: e.confidence,
      polarity: e.polarity,
      recency_weight: e.recency_weight
    })));

    // STEP 1: Determine bucketing strategy based on time range
    const getBucketKey = (date: Date): string => {
      if (timeRange === '6m' || timeRange === '1y') {
        // Day-level bucketing for short ranges
        return date.toISOString().split('T')[0]; // YYYY-MM-DD
      } else {
        // Month-level bucketing for long ranges
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        return `${year}-${month}`; // YYYY-MM
      }
    };

    // STEP 2: Build buckets with polarity-weighted confidence
    const buckets = new Map<string, BucketData>();

    events.forEach(event => {
      const eventDate = new Date(event.timestamp);
      const bucketKey = getBucketKey(eventDate);

      // Initialize bucket if needed
      if (!buckets.has(bucketKey)) {
        buckets.set(bucketKey, {
          date: bucketKey,
          supports: 0,
          suggests: 0,
          contradicts: 0,
        });
      }

      const bucket = buckets.get(bucketKey)!;
      const weight = event.recency_weight ?? 1.0;
      const weightedConfidence = event.confidence * weight;

      // STEP 3: Accumulate into polarity buckets
      if (event.polarity === 'SUPPORTS') {
        bucket.supports += weightedConfidence;
      } else if (event.polarity === 'SUGGESTS') {
        bucket.suggests += weightedConfidence;
      } else if (event.polarity === 'CONTRADICTS') {
        bucket.contradicts += weightedConfidence;
      }
    });

    // STEP 4: Sort chronologically
    const sortedBuckets = Array.from(buckets.values()).sort((a, b) =>
      a.date.localeCompare(b.date)
    );

    console.debug('[TimelineChart] Aggregated buckets:', sortedBuckets.length);
    console.debug('[TimelineChart] Bucket values:', sortedBuckets.map(b => ({
      date: b.date,
      supports: b.supports.toFixed(3),
      suggests: b.suggests.toFixed(3),
      contradicts: b.contradicts.toFixed(3)
    })));

    // STEP 5: Check for temporal spread
    if (sortedBuckets.length <= 1) {
      console.warn('[TimelineChart] Insufficient temporal spread');
      return {
        buckets: sortedBuckets,
        hasInsufficientSpread: true,
      };
    }

    return {
      buckets: sortedBuckets,
      hasInsufficientSpread: false,
    };
  }, [events, timeRange]);

  if (!chartData || chartData.buckets.length === 0) {
    return (
      <div
        className="w-full flex items-center justify-center text-warm-text-subtle text-xs"
        style={{ height: '200px' }}
      >
        No events in this time range
      </div>
    );
  }

  if (chartData.hasInsufficientSpread) {
    return (
      <div
        className="w-full flex flex-col items-center justify-center text-warm-text-subtle text-xs space-y-2 p-4"
        style={{ height: '200px', backgroundColor: 'rgba(58, 54, 52, 0.04)' }}
      >
        <div style={{ height: '2px', width: '60%', backgroundColor: '#8b7d6b' }} />
        <span>Insufficient temporal spread for trend analysis</span>
      </div>
    );
  }

  const buckets = chartData.buckets;
  
  // Calculate scaling: use both min and max to show variation
  const allValues = buckets.flatMap(b => [b.supports, b.suggests, b.contradicts]);
  const maxScore = Math.max(...allValues, 0.1); // Avoid division by zero
  const minScore = Math.min(...allValues, 0);
  const scoreRange = maxScore - minScore || 1;

  console.debug('[TimelineChart] Scaling - Min:', minScore, 'Max:', maxScore, 'Range:', scoreRange);

  return (
    <div className="w-full space-y-4">
      {/* CHART AREA */}
      <div
        className="w-full relative"
        style={{
          height: '200px',
          borderBottom: '1px solid rgba(58, 54, 52, 0.12)',
        }}
      >
        {/* ZERO BASELINE */}
        <div
          className="absolute w-full"
          style={{
            top: '50%',
            height: '1px',
            backgroundColor: 'rgba(58, 54, 52, 0.1)',
          }}
        />

        {/* BARS CONTAINER */}
        <div className="flex items-end justify-between gap-0.5 h-full p-2">
          {buckets.map((bucket, idx) => {
            // Calculate total height for this bucket
            const totalScore = bucket.supports + bucket.suggests + bucket.contradicts;
            
            // Normalize to 0-100 range, using full range for better visibility
            const normalizedScore = ((totalScore - minScore) / scoreRange) * 100;
            const barHeightPercent = Math.max(5, Math.min(100, normalizedScore)); // 5-100%

            // Sub-heights for stacked segments
            const supportRatio = totalScore > 0 ? bucket.supports / totalScore : 0;
            const suggestRatio = totalScore > 0 ? bucket.suggests / totalScore : 0;
            const contradictRatio = totalScore > 0 ? bucket.contradicts / totalScore : 0;

            const supportHeight = barHeightPercent * supportRatio;
            const suggestHeight = barHeightPercent * suggestRatio;
            const contradictHeight = barHeightPercent * contradictRatio;

            return (
              <div key={idx} className="flex-1 flex items-end justify-center h-full">
                {/* STACKED BARS BY POLARITY */}
                <div className="w-full flex flex-col items-center justify-end gap-0" style={{ height: `${barHeightPercent}%` }}>
                  {/* SUPPORTS (top) */}
                  {supportHeight > 0 && (
                    <div
                      style={{
                        height: `${supportHeight}%`,
                        width: '100%',
                        backgroundColor: '#6b8e6f',
                        opacity: 0.85,
                        minHeight: '2px',
                      }}
                      title={`${bucket.date}: Supports ${bucket.supports.toFixed(2)}`}
                    />
                  )}

                  {/* SUGGESTS (middle) */}
                  {suggestHeight > 0 && (
                    <div
                      style={{
                        height: `${suggestHeight}%`,
                        width: '100%',
                        backgroundColor: '#8b7d6b',
                        opacity: 0.75,
                        minHeight: '2px',
                      }}
                      title={`${bucket.date}: Suggests ${bucket.suggests.toFixed(2)}`}
                    />
                  )}

                  {/* CONTRADICTS (bottom) */}
                  {contradictHeight > 0 && (
                    <div
                      style={{
                        height: `${contradictHeight}%`,
                        width: '100%',
                        backgroundColor: '#a89668',
                        opacity: 0.75,
                        minHeight: '2px',
                      }}
                      title={`${bucket.date}: Contradicts ${bucket.contradicts.toFixed(2)}`}
                    />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* TIME AXIS LABELS */}
      <div className="flex justify-between text-xs text-warm-text-subtle font-mono px-2">
        <span>{buckets[0]?.date}</span>
        <span>{buckets[buckets.length - 1]?.date}</span>
      </div>

      {/* LEGEND */}
      <div className="flex gap-4 text-xs text-warm-text-subtle font-inter pt-2 border-t border-warm-border">
        <div className="flex items-center gap-1.5">
          <div
            className="w-3 h-3"
            style={{ backgroundColor: '#6b8e6f' }}
          />
          <span>Supports</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div
            className="w-3 h-3"
            style={{ backgroundColor: '#8b7d6b' }}
          />
          <span>Suggests</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div
            className="w-3 h-3"
            style={{ backgroundColor: '#a89668' }}
          />
          <span>Contradicts</span>
        </div>
      </div>
    </div>
  );
};
