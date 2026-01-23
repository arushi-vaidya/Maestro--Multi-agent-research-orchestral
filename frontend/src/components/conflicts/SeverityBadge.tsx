import React from 'react';

interface SeverityBadgeProps {
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'NONE';
  hasConflict: boolean;
}

/**
 * SeverityBadge - Displays conflict severity with appropriate styling
 * 
 * Design: Calm, academic, no alarmism
 * - LOW: Soft sage (neutral positive)
 * - MEDIUM: Soft amber (attention, not alarm)
 * - HIGH: Muted terracotta (concern, not panic)
 * - NONE: Soft sage (positive)
 */
export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity, hasConflict }) => {
  const getStyles = () => {
    if (!hasConflict || severity === 'NONE') {
      return 'bg-sage-100 text-sage-700 border-sage-200';
    }
    
    switch (severity) {
      case 'LOW':
        return 'bg-sage-100 text-sage-700 border-sage-200';
      case 'MEDIUM':
        return 'bg-terracotta-100 text-terracotta-700 border-terracotta-200';
      case 'HIGH':
        return 'bg-terracotta-200 text-terracotta-800 border-terracotta-300';
      default:
        return 'bg-cocoa-100 text-cocoa-700 border-cocoa-200';
    }
  };

  const getText = () => {
    if (!hasConflict) {
      return 'No conflicts detected';
    }
    return `Conflicts detected · ${severity} severity`;
  };

  return (
    <span
      className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium font-inter border ${getStyles()}`}
    >
      {getText()}
    </span>
  );
};
