/**
 * Input Component
 * Basic text input for search and forms
 */

import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  // Additional props can be added here
}

export const Input: React.FC<InputProps> = ({
  className = '',
  ...props
}) => {
  const baseStyles = 'w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400 focus:border-transparent transition-all';

  return (
    <input
      className={`${baseStyles} ${className}`}
      {...props}
    />
  );
};
