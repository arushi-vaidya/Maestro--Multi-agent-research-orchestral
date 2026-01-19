import React from 'react';

interface CalmInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
  className?: string;
  multiline?: boolean;
  rows?: number;
}

/**
 * CalmInput - Warm, minimal input component
 */
export const CalmInput: React.FC<CalmInputProps> = ({
  value,
  onChange,
  placeholder,
  label,
  className = '',
  multiline = false,
  rows = 3,
}) => {
  const inputStyles = `
    w-full px-4 py-3 rounded-lg font-inter
    bg-warm-surface border border-warm-divider
    text-warm-text placeholder:text-warm-text-subtle
    focus:outline-none focus:border-terracotta-400
    transition-colors duration-300 ease-out
  `;

  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-warm-text mb-2 font-inter">
          {label}
        </label>
      )}
      {multiline ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          rows={rows}
          className={inputStyles}
        />
      ) : (
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={inputStyles}
        />
      )}
    </div>
  );
};
