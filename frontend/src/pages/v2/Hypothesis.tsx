/**
 * Hypothesis & ROS Page - PRIMARY PAGE
 * POST /api/query → GET /api/ros/latest
 */

import React, { useState } from 'react';
import { PageContainer, CalmButton, CalmInput, CalmCard } from '../../components/calm';
import { api } from '../../services/api';
import type { QueryResponse, ROSViewResponse } from '../../types/api';

export const Hypothesis: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [rosData, setRosData] = useState<ROSViewResponse | null>(null);

  const handleSubmit = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      await api.submitQuery(query);
      const ros = await api.getROSLatest();
      setRosData(ros);
    } catch (error) {
      console.error('Query error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageContainer maxWidth="lg">
      <div className="mb-12">
        <h1 className="text-3xl font-bold text-warm-text mb-2 font-inter">
          Research Hypothesis Analysis
        </h1>
        <p className="text-warm-text-light font-inter">
          Submit a drug-disease hypothesis for systematic evaluation.
        </p>
      </div>

      <CalmCard className="mb-8">
        <CalmInput
          value={query}
          onChange={setQuery}
          placeholder="e.g., Semaglutide for Alzheimer's disease"
          label="Hypothesis"
          multiline
          rows={3}
          className="mb-4"
        />
        <CalmButton onClick={handleSubmit} disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze Opportunity'}
        </CalmButton>
      </CalmCard>

      {rosData && (
        <CalmCard>
          <h2 className="text-2xl font-bold text-warm-text mb-4 font-inter">
            ROS Score: {rosData.ros_score.toFixed(1)}/10
          </h2>
          <p className="text-warm-text-light mb-4 font-inter">
            {rosData.explanation}
          </p>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
            <div>
              <div className="text-warm-text-subtle font-inter">Evidence Strength</div>
              <div className="text-lg font-semibold text-warm-text font-inter">
                {rosData.breakdown.evidence_strength.toFixed(1)}
              </div>
            </div>
            <div>
              <div className="text-warm-text-subtle font-inter">Diversity</div>
              <div className="text-lg font-semibold text-warm-text font-inter">
                {rosData.breakdown.evidence_diversity.toFixed(1)}
              </div>
            </div>
            <div>
              <div className="text-warm-text-subtle font-inter">Conflict Penalty</div>
              <div className="text-lg font-semibold text-warm-text font-inter">
                {rosData.breakdown.conflict_penalty.toFixed(1)}
              </div>
            </div>
            <div>
              <div className="text-warm-text-subtle font-inter">Recency</div>
              <div className="text-lg font-semibold text-warm-text font-inter">
                {rosData.breakdown.recency_boost.toFixed(1)}
              </div>
            </div>
            <div>
              <div className="text-warm-text-subtle font-inter">Patent Risk</div>
              <div className="text-lg font-semibold text-warm-text font-inter">
                {rosData.breakdown.patent_risk_penalty.toFixed(1)}
              </div>
            </div>
          </div>
        </CalmCard>
      )}
    </PageContainer>
  );
};
