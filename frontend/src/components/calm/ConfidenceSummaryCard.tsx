/**
 * ConfidenceSummaryCard
 *
 * Left-side confidence summary panel for Evidence Timeline.
 *
 * Shows:
 * - Big confidence number (0-100 or 0-1 scale)
 * - Delta indicator (↗ green for positive, ↘ red for negative)
 * - Mini evolution indicator
 * - Evidence breakdown (supporting, suggesting, contradicting)
 * - Optional ROS data integration
 *
 * Design: Claude × Linear × Arc aesthetic
 * - Large, legible confidence number
 * - Color-coded polarity (green/amber/red)
 * - Calm, minimal layout
 */

import React from 'react';
import type { ROSViewResponse } from '../../types/api';

interface PolarityStats {
  SUPPORTS: number;
  SUGGESTS: number;
  CONTRADICTS: number;
}

interface DateRange {
  earliest: string;
  latest: string;
}

interface ConfidenceSummaryCardProps {
  /** Confidence score (0-1 or 0-100) */
  confidence: number;

  /** Change in confidence (+/- points) */
  delta: number;

  /** Optional ROS data for additional context */
  rosData?: ROSViewResponse | null;

  /** Count of filtered events */
  filteredEventsCount: number;

  /** Polarity breakdown */
  polarityStats: PolarityStats;

  /** Date range for events */
  dateRange: DateRange;
}

export const ConfidenceSummaryCard: React.FC<ConfidenceSummaryCardProps> = ({
  confidence,
  delta,
  rosData,
  filteredEventsCount,
  polarityStats,
  dateRange,
}) => {
  // Normalize confidence to 0-100 scale
  const displayConfidence = confidence > 1 ? Math.round(confidence) : Math.round(confidence * 100);

  // Determine delta styling
  const isDeltaPositive = delta >= 0;
  const deltaColor = isDeltaPositive ? '#6b8e6f' : '#a89668';
  const deltaIcon = isDeltaPositive ? '↗' : '↘';
  const displayDelta = Math.abs(delta > 1 ? Math.round(delta) : Math.round(delta * 100));

  // Parse date range for display
  const fromDate = new Date(dateRange.earliest);
  const toDate = new Date(dateRange.latest);
  const fromMonth = fromDate.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  const toMonth = toDate.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });

  // Calculate total for proportional breakdown
  const totalEvents = polarityStats.SUPPORTS + polarityStats.SUGGESTS + polarityStats.CONTRADICTS;
  const supportPercent = totalEvents > 0 ? (polarityStats.SUPPORTS / totalEvents) * 100 : 0;
  const suggestPercent = totalEvents > 0 ? (polarityStats.SUGGESTS / totalEvents) * 100 : 0;
  const contradictPercent = totalEvents > 0 ? (polarityStats.CONTRADICTS / totalEvents) * 100 : 0;

  return (
    <div className="space-y-6 bg-warm-surface border border-warm-divider rounded-lg p-6">
      {/* ====================================================================
          SECTION 1: CONFIDENCE SCORE + DELTA
          ==================================================================== */}
      <div className="space-y-3">
        <div className="flex items-baseline justify-between gap-4">
          {/* Big confidence number */}
          <div>
            <div 
              className="text-6xl font-bold" 
              style={{ color: '#3A3634', letterSpacing: '-0.03em' }}
            >
              {displayConfidence}
            </div>
            <div className="text-xs text-warm-text-subtle font-inter mt-1">
              Confidence Score
            </div>
          </div>

          {/* Delta badge */}
          <div
            className="flex flex-col items-center gap-1 px-3 py-2 rounded-lg border text-center"
            style={{
              borderColor: deltaColor,
              backgroundColor: `${isDeltaPositive ? 'rgba(107, 142, 111' : 'rgba(168, 150, 104'}, 0.08)`,
            }}
          >
            <div className="text-2xl" style={{ color: deltaColor }}>
              {deltaIcon}
            </div>
            <div className="text-xs font-semibold" style={{ color: deltaColor }}>
              {displayDelta} pts
            </div>
          </div>
        </div>

        {/* Date range subtitle */}
        <div className="text-xs text-warm-text-subtle font-inter">
          {fromMonth === toMonth ? `as of ${toMonth}` : `since ${fromMonth}`}
        </div>
      </div>

      {/* ====================================================================
          SECTION 2: MINI EVOLUTION BARS
          ==================================================================== */}
      <div className="space-y-2 border-t border-warm-border pt-4">
        <div className="text-xs font-inter font-semibold text-warm-text-subtle tracking-wider">
          EVIDENCE DISTRIBUTION
        </div>

        {/* Segmented bar showing polarity proportions */}
        <div className="flex h-2 gap-0 rounded-full overflow-hidden bg-warm-bg border border-warm-border">
          {supportPercent > 0 && (
            <div
              className="bg-opacity-80"
              style={{
                width: `${supportPercent}%`,
                backgroundColor: '#6b8e6f',
              }}
              title={`Supporting: ${polarityStats.SUPPORTS}`}
            />
          )}
          {suggestPercent > 0 && (
            <div
              className="bg-opacity-80"
              style={{
                width: `${suggestPercent}%`,
                backgroundColor: '#d4a574',
              }}
              title={`Suggesting: ${polarityStats.SUGGESTS}`}
            />
          )}
          {contradictPercent > 0 && (
            <div
              className="bg-opacity-80"
              style={{
                width: `${contradictPercent}%`,
                backgroundColor: '#a89668',
              }}
              title={`Contradicting: ${polarityStats.CONTRADICTS}`}
            />
          )}
        </div>

        {/* Legend */}
        <div className="text-xs text-warm-text-subtle font-inter space-y-1 pt-1">
          <div>
            {supportPercent > 0 && (
              <span>
                Supporting: <span className="font-semibold text-warm-text">{polarityStats.SUPPORTS}</span>
                {suggestPercent > 0 || contradictPercent > 0 ? ' • ' : ''}
              </span>
            )}
            {suggestPercent > 0 && (
              <span>
                Suggesting: <span className="font-semibold text-warm-text">{polarityStats.SUGGESTS}</span>
                {contradictPercent > 0 ? ' • ' : ''}
              </span>
            )}
            {contradictPercent > 0 && (
              <span>
                Contradicting: <span className="font-semibold text-warm-text">{polarityStats.CONTRADICTS}</span>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* ====================================================================
          SECTION 3: ROS DATA (if available)
          ==================================================================== */}
      {rosData && (
        <div className="space-y-2 border-t border-warm-border pt-4">
          <div className="text-xs font-inter font-semibold text-warm-text-subtle tracking-wider">
            ROS SCORE
          </div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-warm-text">
                {Math.round(rosData.ros_score)}
              </div>
              <div className="text-xs text-warm-text-subtle">
                {rosData.confidence_level}
              </div>
            </div>
            <div className="text-right text-xs text-warm-text-subtle space-y-0.5">
              <div>
                Supporting: <span className="font-semibold text-warm-text">{rosData.metadata.num_supporting_evidence}</span>
              </div>
              <div>
                Contradicting: <span className="font-semibold text-warm-text">{rosData.metadata.num_contradicting_evidence}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ====================================================================
          SECTION 4: TREND INDICATOR
          ==================================================================== */}
      <div className="space-y-2 border-t border-warm-border pt-4">
        <div className="text-xs font-inter font-semibold text-warm-text-subtle tracking-wider">
          TREND
        </div>
        <div 
          className="text-xs font-inter leading-relaxed p-3 rounded border"
          style={{
            borderColor: isDeltaPositive ? '#6b8e6f' : '#a89668',
            backgroundColor: `${isDeltaPositive ? 'rgba(107, 142, 111' : 'rgba(168, 150, 104'}, 0.08)`,
            color: '#3A3634',
          }}
        >
          {isDeltaPositive ? (
            <span>
              Evidence is becoming <span style={{ color: deltaColor }}>stronger</span> over time
              ({displayDelta} pts increase)
            </span>
          ) : (
            <span>
              Evidence is becoming <span style={{ color: deltaColor }}>weaker</span> over time
              ({displayDelta} pts decrease)
            </span>
          )}
        </div>
      </div>

      {/* ====================================================================
          SECTION 5: SUMMARY
          ==================================================================== */}
      <div className="space-y-1 border-t border-warm-border pt-4 text-xs font-inter text-warm-text-subtle">
        <div>
          <span>Total Evidence Events:</span>
          {' '}
          <span className="font-semibold text-warm-text">{filteredEventsCount}</span>
        </div>
        <div>
          <span>Time Window:</span>
          {' '}
          <span className="font-semibold text-warm-text font-mono">
            {fromMonth} → {toMonth}
          </span>
        </div>
      </div>
    </div>
  );
};
