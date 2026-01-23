/**
 * Execution Transparency Page
 * GET /api/execution/status
 */

import React, { useEffect, useState } from 'react';
import { PageContainer, CalmCard, CalmBadge } from '../../components/calm';
import { api } from '../../services/api';
import { useQueryRefresh } from '../../context/QueryContext';
import type { ExecutionStatusResponse } from '../../types/api';

export const Execution: React.FC = () => {
  // Query refresh hook
  const { queryCount } = useQueryRefresh();

  const [execution, setExecution] = useState<ExecutionStatusResponse | null>(null);

  useEffect(() => {
    console.log('[Execution] Fetching execution data (queryCount:', queryCount, ')');
    setExecution(null); // Clear old data
    api.getExecutionStatus()
      .then((data) => {
        console.log('[Execution] Execution data loaded:', data);
        setExecution(data);
      })
      .catch(console.error);
  }, [queryCount]);

  const statusVariant = (status: string) => {
    if (status === 'completed') return 'positive';
    if (status === 'failed') return 'warning';
    return 'info';
  };

  return (
    <PageContainer maxWidth="lg">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-warm-text mb-2 font-inter">
          Execution Transparency
        </h1>
        <p className="text-warm-text-light font-inter">
          System credibility through complete execution visibility.
        </p>
      </div>

      {execution && (
        <>
          <CalmCard className="mb-8">
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-warm-text-subtle font-inter">Agents Triggered</div>
                <div className="text-2xl font-semibold text-warm-text font-inter">
                  {execution.agents_triggered.length}
                </div>
              </div>
              <div>
                <div className="text-warm-text-subtle font-inter">Completed</div>
                <div className="text-2xl font-semibold text-sage-600 font-inter">
                  {execution.agents_completed.length}
                </div>
              </div>
              <div>
                <div className="text-warm-text-subtle font-inter">Failed</div>
                <div className="text-2xl font-semibold text-terracotta-600 font-inter">
                  {execution.agents_failed.length}
                </div>
              </div>
              <div>
                <div className="text-warm-text-subtle font-inter">Duration</div>
                <div className="text-2xl font-semibold text-warm-text font-inter">
                  {(execution.execution_time_ms / 1000).toFixed(1)}s
                </div>
              </div>
            </div>
          </CalmCard>

          <h3 className="font-semibold text-warm-text mb-4 font-inter">Agent Timeline</h3>
          <div className="space-y-3 mb-8">
            {execution.agent_details.map((agent, idx) => (
              <CalmCard key={idx}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-warm-text font-inter">
                        {agent.agent_id}
                      </span>
                      <CalmBadge variant={statusVariant(agent.status) as any}>
                        {agent.status}
                      </CalmBadge>
                    </div>
                    <p className="text-xs text-warm-text-subtle font-inter">
                      {agent.started_at && new Date(agent.started_at).toLocaleTimeString()}
                      {' → '}
                      {agent.completed_at && new Date(agent.completed_at).toLocaleTimeString()}
                    </p>
                  </div>
                  <div className="text-right">
                    {agent.duration_ms !== null && (
                      <div className="text-sm font-semibold text-warm-text font-inter">
                        {(agent.duration_ms / 1000).toFixed(2)}s
                      </div>
                    )}
                    {agent.result_count !== null && (
                      <div className="text-xs text-warm-text-subtle font-inter">
                        {agent.result_count} results
                      </div>
                    )}
                  </div>
                </div>
              </CalmCard>
            ))}
          </div>

          <h3 className="font-semibold text-warm-text mb-4 font-inter">AKGP Ingestion Summary</h3>
          <CalmCard>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-warm-text-subtle font-inter">Total Evidence</div>
                <div className="text-xl font-semibold text-warm-text font-inter">
                  {execution.ingestion_summary.total_evidence || 0}
                </div>
              </div>
              <div>
                <div className="text-warm-text-subtle font-inter">Ingested</div>
                <div className="text-xl font-semibold text-sage-600 font-inter">
                  {execution.ingestion_summary.ingested_evidence || 0}
                </div>
              </div>
              <div>
                <div className="text-warm-text-subtle font-inter">Rejected</div>
                <div className="text-xl font-semibold text-terracotta-600 font-inter">
                  {execution.ingestion_summary.rejected_evidence || 0}
                </div>
              </div>
            </div>
          </CalmCard>
        </>
      )}
    </PageContainer>
  );
};
