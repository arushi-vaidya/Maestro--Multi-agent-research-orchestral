/**
 * TimelineRangeSelector
 * 
 * Client-side time range filter buttons.
 * 6m | 1y | 2y | 5y | All
 */

import React from 'react';

interface TimelineRangeSelectorProps {
  selectedRange: '6m' | '1y' | '2y' | '5y' | 'all';
  onRangeChange: (range: '6m' | '1y' | '2y' | '5y' | 'all') => void;
}

export const TimelineRangeSelector: React.FC<TimelineRangeSelectorProps> = ({
  selectedRange,
  onRangeChange,
}) => {
  const ranges = [
    { value: '6m', label: '6m' },
    { value: '1y', label: '1y' },
    { value: '2y', label: '2y' },
    { value: '5y', label: '5y' },
    { value: 'all', label: 'All' },
  ] as const;

  return (
    <div className="flex gap-2">
      {ranges.map((range) => (
        <button
          key={range.value}
          onClick={() => onRangeChange(range.value)}
          className={`px-3 py-2 text-xs font-inter font-semibold border transition-colors ${
            selectedRange === range.value
              ? 'border-warm-text bg-warm-text text-white'
              : 'border-warm-border text-warm-text-light hover:text-warm-text hover:border-warm-text-light'
          }`}
        >
          {range.label}
        </button>
      ))}
    </div>
  );
};
