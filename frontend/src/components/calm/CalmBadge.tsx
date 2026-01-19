import React from 'react';

interface CalmBadgeProps {
  children: React.ReactNode;
  variant?: 'neutral' | 'positive' | 'warning' | 'info';
  className?: string;
}

export const CalmBadge: React.FC<CalmBadgeProps> = ({
  children,
  variant = 'neutral',
  className = '',
}) => {
  const variantStyles = {
    neutral: 'bg-cocoa-100 text-cocoa-700',
    positive: 'bg-sage-100 text-sage-700',
    warning: 'bg-terracotta-100 text-terracotta-700',
    info: 'bg-warm-surface-alt text-warm-text-light border border-warm-divider',
  };

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium font-inter ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
