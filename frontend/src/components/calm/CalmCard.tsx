import React from 'react';
import { cn } from '../../lib/utils';

interface CalmCardProps {
  children: React.ReactNode;
  className?: string;
  noPadding?: boolean;
}

/**
 * CalmCard - Warm, minimal card component
 *
 * Design: Subtle background step, no heavy shadows, hairline dividers
 */
export const CalmCard: React.FC<CalmCardProps> = ({
  children,
  className = '',
  noPadding = false,
}) => {
  const base = 'bg-warm-surface rounded-lg border border-warm-divider';
  const padding = noPadding ? '' : 'p-6';

  return <div className={cn(base, padding, className)}>{children}</div>;
};
