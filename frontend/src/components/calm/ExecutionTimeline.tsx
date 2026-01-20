/**
 * ExecutionTimeline Component
 * 
 * Displays real-time agent execution status in a calm, linear timeline
 * Pure text + subtle badges, no spinners or progress bars
 */

import React from 'react';
import type { ExecutionStatusResponse } from '../../types/api';
import { CalmCard } from './index';

interface ExecutionTimelineProps {
  status: ExecutionStatusResponse | null;
}

const AGENT_LABELS: Record<string, string> = {
  clinical: 'Clinical Trials',
  patent: 'Patent & IP',
  market: 'Market Intelligence',
  literature: 'Literature',
  akgp: 'AKGP Ingestion',
  conflict: 'Conflict Reasoning',
  ros: 'ROS Scoring',
};

const getAgentLabel = (agentId: string): string => {
  return AGENT_LABELS[agentId] || agentId.charAt(0).toUpperCase() + agentId.slice(1);
};

const getStatusBadgeClass = (
  agentId: string,
  completed: string[],
  failed: string[]
): { bg: string; text: string; dot: string } => {
  if (failed.includes(agentId)) {
    return {
      bg: 'bg-rose-50',
      text: 'text-rose-700',
      dot: 'bg-rose-400',
    };
  }
  if (completed.includes(agentId)) {
    return {
      bg: 'bg-sage-50',
      text: 'text-sage-700',
      dot: 'bg-sage-500',
    };
  }
  return {
    bg: 'bg-amber-50',
    text: 'text-amber-600',
    dot: 'bg-amber-400',
  };
};

const getStatusLabel = (
  agentId: string,
  completed: string[],
  failed: string[]
): string => {
  if (failed.includes(agentId)) return 'Failed';
  if (completed.includes(agentId)) return 'Completed';
  return 'Running';
};

export const ExecutionTimeline: React.FC<ExecutionTimelineProps> = ({ status }) => {
  if (!status || status.agents_triggered.length === 0) {
    return null;
  }

  const { agents_triggered, agents_completed, agents_failed, agent_details } = status;
  const totalAgents = agents_triggered.length;
  const completedCount = agents_completed.length + agents_failed.length;

  return (
    <CalmCard className="mb-8 border border-warm-divider">
      {/* Header */}
      <div className="mb-6 pb-4 border-b border-warm-divider">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-warm-text font-inter uppercase tracking-wide">
              Execution Progress
            </h3>
            <p className="text-xs text-warm-text-light mt-1 font-inter">
              {completedCount} of {totalAgents} agents processing
            </p>
          </div>
          <div className="text-right">
            <div className="text-xs text-warm-text-subtle font-inter">
              {status.execution_time_ms ? (
                <span>{(status.execution_time_ms / 1000).toFixed(1)}s elapsed</span>
              ) : null}
            </div>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="space-y-3">
        {agents_triggered.map((agentId, index) => {
          const detail = agent_details.find((d) => d.agent_id === agentId);
          const { bg, text, dot } = getStatusBadgeClass(agentId, agents_completed, agents_failed);
          const statusLabel = getStatusLabel(agentId, agents_completed, agents_failed);

          return (
            <div key={agentId} className="flex items-start gap-4">
              {/* Timeline connector */}
              <div className="flex flex-col items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${dot}`} />
                {index < agents_triggered.length - 1 && (
                  <div className="w-0.5 h-6 bg-warm-divider" />
                )}
              </div>

              {/* Agent row */}
              <div className={`flex-1 rounded-lg px-3 py-2 ${bg}`}>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className={`text-sm font-semibold ${text} font-inter`}>
                      {getAgentLabel(agentId)}
                    </p>
                    {detail && detail.result_count !== null && (
                      <p className="text-xs text-warm-text-light mt-0.5 font-inter">
                        {detail.result_count} result{detail.result_count !== 1 ? 's' : ''}
                        {detail.duration_ms ? ` • ${detail.duration_ms}ms` : ''}
                      </p>
                    )}
                  </div>
                  <div className="flex-shrink-0">
                    <span className={`inline-block px-2 py-1 text-xs font-semibold rounded font-inter ${text}`}>
                      {statusLabel}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </CalmCard>
  );
};
