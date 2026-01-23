/**
 * Graph Node Component
 * Visual representation of a graph node with type-specific styling
 */

import React from 'react';
import { Pill, Activity, FileText, Microscope, AlertCircle, TestTube } from 'lucide-react';

interface GraphNodeData {
  id: string;
  label: string;
  type: 'drug' | 'disease' | 'evidence' | 'target' | 'pathway' | 'adverse' | 'trial' | 'patent' | 'market_signal';
}

interface GraphNodeProps {
  node: GraphNodeData;
  isSelected?: boolean;
  isHighlighted?: boolean;
  onClick?: (node: GraphNodeData) => void;
}

const GraphNode: React.FC<GraphNodeProps> = ({
  node,
  isSelected = false,
  isHighlighted = false,
  onClick,
}) => {
  // Type-specific configuration
  const nodeConfig: Record<string, { icon: React.ElementType; bgColor: string; borderColor: string; textColor: string }> = {
    drug: {
      icon: Pill,
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-500',
      textColor: 'text-blue-700',
    },
    disease: {
      icon: Activity,
      bgColor: 'bg-red-50',
      borderColor: 'border-red-500',
      textColor: 'text-red-700',
    },
    target: {
      icon: TestTube,
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-500',
      textColor: 'text-purple-700',
    },
    pathway: {
      icon: Activity,
      bgColor: 'bg-green-50',
      borderColor: 'border-green-500',
      textColor: 'text-green-700',
    },
    adverse: {
      icon: AlertCircle,
      bgColor: 'bg-amber-50',
      borderColor: 'border-amber-500',
      textColor: 'text-amber-700',
    },
    evidence: {
      icon: FileText,
      bgColor: 'bg-slate-50',
      borderColor: 'border-slate-500',
      textColor: 'text-slate-700',
    },
    trial: {
      icon: Microscope,
      bgColor: 'bg-teal-50',
      borderColor: 'border-teal-500',
      textColor: 'text-teal-700',
    },
    patent: {
      icon: FileText,
      bgColor: 'bg-indigo-50',
      borderColor: 'border-indigo-500',
      textColor: 'text-indigo-700',
    },
    market_signal: {
      icon: Activity,
      bgColor: 'bg-emerald-50',
      borderColor: 'border-emerald-500',
      textColor: 'text-emerald-700',
    },
  };

  const config = nodeConfig[node.type] || nodeConfig.evidence;
  const Icon = config.icon;

  return (
    <div
      onClick={() => onClick?.(node)}
      className={`
        flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition-all cursor-pointer
        ${config.bgColor}
        ${isSelected || isHighlighted ? config.borderColor : 'border-transparent'}
        ${isSelected ? 'shadow-md' : 'hover:shadow-sm'}
      `}
    >
      <div className={`${config.textColor}`}>
        <Icon className="w-4 h-4" />
      </div>
      <span className={`text-sm font-medium ${config.textColor}`}>
        {node.label}
      </span>
      <span className="text-xs text-slate-400 ml-auto">
        {node.type}
      </span>
    </div>
  );
};

export default GraphNode;
