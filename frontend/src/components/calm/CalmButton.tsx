import React from 'react';

interface CalmButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  disabled?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

/**
 * CalmButton - Restrained button with warm colors
 *
 * Design: Minimal, calm interactions, opacity transitions only
 */
export const CalmButton: React.FC<CalmButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  disabled = false,
  className = '',
  type = 'button',
}) => {
  const baseStyles = 'px-6 py-3 rounded-lg font-inter font-medium transition-all duration-300 ease-out';

  const variantStyles = {
    primary: 'bg-terracotta-500 text-white hover:bg-terracotta-600 disabled:opacity-50 disabled:cursor-not-allowed',
    secondary: 'bg-warm-surface-alt text-warm-text border border-warm-divider hover:bg-warm-surface disabled:opacity-50',
    ghost: 'text-warm-text-light hover:text-warm-text hover:bg-warm-surface-alt disabled:opacity-50',
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseStyles} ${variantStyles[variant]} ${className}`}
    >
      {children}
    </button>
  );
};
