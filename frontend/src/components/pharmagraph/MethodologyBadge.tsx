/**
 * Methodology Badge Component
 * Displays evidence type with appropriate styling
 */

import React from 'react';

interface MethodologyBadgeProps {
  type: 'in_vitro' | 'in_vivo' | 'clinical_trial' | 'database' | 'review' | 'meta_analysis' | string;
}

const MethodologyBadge: React.FC<MethodologyBadgeProps> = ({ type }) => {
  // Map methodology types to display labels and colors
  const methodologyConfig: Record<string, { label: string; className: string }> = {
    in_vitro: {
      label: 'In Vitro',
      className: 'bg-blue-100 text-blue-700',
    },
    in_vivo: {
      label: 'In Vivo',
      className: 'bg-purple-100 text-purple-700',
    },
    clinical_trial: {
      label: 'Clinical Trial',
      className: 'bg-teal-100 text-teal-700',
    },
    database: {
      label: 'Database',
      className: 'bg-slate-100 text-slate-700',
    },
    review: {
      label: 'Review',
      className: 'bg-amber-100 text-amber-700',
    },
    meta_analysis: {
      label: 'Meta-Analysis',
      className: 'bg-emerald-100 text-emerald-700',
    },
  };

  const config = methodologyConfig[type] || {
    label: type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
    className: 'bg-slate-100 text-slate-600',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${config.className}`}
    >
      {config.label}
    </span>
  );
};

export default MethodologyBadge;
