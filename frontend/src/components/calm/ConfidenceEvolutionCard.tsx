/**
 * ConfidenceEvolutionCard
 * 
 * Compact KPI summary of evidence confidence evolution.
 * 
 * Design: Claude / Linear / Arc aesthetic
 * - Large confidence number for instant understanding
 * - Delta trend indicator
 * - Segmented contribution bar
 * - Summary statistics
 * 
 * This is NOT a full timeline chart - it's an insight card.
 */

import React from 'react';

interface ConfidenceEvolutionCardProps {
  /** Current confidence score (0-1 or 0-100) */
  confidence: number;
  
  /** Change from previous period (+/- points) */
  delta: number;
  
  /** Start date in ISO format */
  fromDate: string;
  
  /** End date in ISO format */
  toDate: string;
  
  /** Count of supporting evidence */
  supports: number;
  
  /** Count of contradicting evidence */
  contradicts: number;
  
  /** Count of suggestive evidence */
  suggests: number;
}

export const ConfidenceEvolutionCard: React.FC<ConfidenceEvolutionCardProps> = ({
  confidence,
  delta,
  fromDate,
  toDate,
  supports,
  contradicts,
  suggests,
}) => {
  // Format confidence as 0-100 scale if needed
  const displayConfidence = confidence > 1 ? confidence : Math.round(confidence * 100);
  const displayDelta = Math.round(delta * 100) || delta;
  
  // Parse dates for display
  const fromD = new Date(fromDate);
  const toD = new Date(toDate);
  const fromMonth = fromD.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  const toMonth = toD.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  
  // Calculate total for segmented bar
  const total = supports + suggests + contradicts;
  const supportPercent = total > 0 ? (supports / total) * 100 : 0;
  const suggestPercent = total > 0 ? (suggests / total) * 100 : 0;
  const contradictPercent = total > 0 ? (contradicts / total) * 100 : 0;
  
  // Determine delta color and icon
  const isDeltaPositive = delta >= 0;
  const deltaColor = isDeltaPositive ? '#6b8e6f' : '#a89668';
  const deltaLabel = isDeltaPositive ? '+' : '';
  
  return (
    <div className="w-full space-y-6">
      {/* TOP SECTION: Confidence + Delta */}
      <div className="flex items-start justify-between">
        <div>
          {/* Confidence number */}
          <div className="text-5xl font-semibold" style={{ color: '#3A3634', letterSpacing: '-0.02em' }}>
            {displayConfidence}
          </div>
          
          {/* Subtitle with date range */}
          <div className="text-xs text-warm-text-subtle font-inter mt-2">
            {fromMonth === toMonth ? `as of ${toMonth}` : `since ${fromMonth}`}
          </div>
        </div>
        
        {/* Delta badge */}
        <div
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-sm text-xs font-inter font-semibold"
          style={{
            backgroundColor: isDeltaPositive ? 'rgba(107, 142, 111, 0.08)' : 'rgba(168, 150, 104, 0.08)',
            color: deltaColor,
          }}
        >
          <span>{isDeltaPositive ? '↗' : '↘'}</span>
          <span>
            {deltaLabel}
            {Math.abs(displayDelta)} points
          </span>
        </div>
      </div>

      {/* CONTRIBUTION BAR */}
      {total > 0 && (
        <div className="space-y-2">
          {/* Segmented bar */}
          <div className="flex h-2 rounded-full overflow-hidden gap-0.5" style={{ backgroundColor: 'rgba(58, 54, 52, 0.08)' }}>
            {supportPercent > 5 && (
              <div
                className="transition-all duration-300"
                style={{
                  width: `${supportPercent}%`,
                  backgroundColor: '#6b8e6f',
                }}
              />
            )}
            {suggestPercent > 5 && (
              <div
                className="transition-all duration-300"
                style={{
                  width: `${suggestPercent}%`,
                  backgroundColor: '#8b7d6b',
                }}
              />
            )}
            {contradictPercent > 5 && (
              <div
                className="transition-all duration-300"
                style={{
                  width: `${contradictPercent}%`,
                  backgroundColor: '#a89668',
                }}
              />
            )}
          </div>
          
          {/* Legend */}
          <div className="flex gap-3 text-xs text-warm-text-subtle font-inter">
            {supports > 0 && (
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#6b8e6f' }} />
                <span>{supports} support</span>
              </div>
            )}
            {suggests > 0 && (
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#8b7d6b' }} />
                <span>{suggests} suggest</span>
              </div>
            )}
            {contradicts > 0 && (
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#a89668' }} />
                <span>{contradicts} contradict</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SUMMARY STATS */}
      <div className="space-y-2 border-t border-warm-border pt-4">
        <div className="flex justify-between items-center text-xs">
          <span className="text-warm-text-subtle">Total evidence</span>
          <span className="font-semibold text-warm-text">{total}</span>
        </div>
        
        {supports > 0 && (
          <div className="flex justify-between items-center text-xs">
            <span className="text-warm-text-subtle">Supports</span>
            <span className="font-semibold" style={{ color: '#6b8e6f' }}>
              +{supports}
            </span>
          </div>
        )}
        
        {contradicts > 0 && (
          <div className="flex justify-between items-center text-xs">
            <span className="text-warm-text-subtle">Contradicts</span>
            <span className="font-semibold" style={{ color: '#a89668' }}>
              -{contradicts}
            </span>
          </div>
        )}
        
        {suggests > 0 && (
          <div className="flex justify-between items-center text-xs">
            <span className="text-warm-text-subtle">Suggests</span>
            <span className="font-semibold text-warm-text">{suggests}</span>
          </div>
        )}
      </div>
    </div>
  );
};
