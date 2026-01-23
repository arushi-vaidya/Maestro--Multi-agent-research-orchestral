import React from 'react';

interface CalmDividerProps {
  className?: string;
  vertical?: boolean;
}

export const CalmDivider: React.FC<CalmDividerProps> = ({
  className = '',
  vertical = false,
}) => {
  if (vertical) {
    return <div className={`w-px bg-warm-divider ${className}`} />;
  }

  return <div className={`h-px bg-warm-divider ${className}`} />;
};
