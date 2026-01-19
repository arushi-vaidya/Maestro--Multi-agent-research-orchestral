/**
 * Knowledge Graph Explorer
 * GET /api/graph/summary
 */

import React, { useEffect, useState } from 'react';
import { PageContainer, CalmCard } from '../../components/calm';
import { api } from '../../services/api';
import type { GraphSummaryResponse } from '../../types/api';

export const GraphExplorer: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphSummaryResponse | null>(null);

  useEffect(() => {
    api.getGraphSummary().then(setGraphData).catch(console.error);
  }, []);

  return (
    <PageContainer maxWidth="full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-warm-text mb-2 font-inter">
          Knowledge Graph Explorer
        </h1>
        <p className="text-warm-text-light font-inter">
          Structural view of drug-disease relationships and evidence.
        </p>
      </div>

      {graphData && (
        <CalmCard>
          <div className="grid grid-cols-3 gap-4 mb-8 text-sm">
            <div>
              <div className="text-warm-text-subtle font-inter">Total Nodes</div>
              <div className="text-2xl font-semibold text-warm-text font-inter">
                {graphData.statistics.total_nodes}
              </div>
            </div>
            <div>
              <div className="text-warm-text-subtle font-inter">Total Edges</div>
              <div className="text-2xl font-semibold text-warm-text font-inter">
                {graphData.statistics.total_edges}
              </div>
            </div>
            <div>
              <div className="text-warm-text-subtle font-inter">Graph Mode</div>
              <div className="text-lg font-semibold text-warm-text font-inter">
                {graphData.statistics.graph_mode || 'N/A'}
              </div>
            </div>
          </div>

          <div className="bg-warm-surface-alt rounded p-8 text-center">
            <p className="text-warm-text-light font-inter">
              Graph visualization would render here
              <br />
              <span className="text-sm text-warm-text-subtle">
                (SVG/Three.js implementation)
              </span>
            </p>
          </div>
        </CalmCard>
      )}
    </PageContainer>
  );
};
