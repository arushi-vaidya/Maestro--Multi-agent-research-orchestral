import React from 'react';

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
  return (
    <div
      className={`
        bg-warm-surface rounded-lg
        border border-warm-divider
        ${noPadding ? '' : 'p-6'}
        ${className}
      `}
    >
      {children}
    </div>
  );
};
