/**
 * Hypothesis & ROS Page - PRIMARY PAGE
 * 
 * Architecture: Three-zone research console
 * Zone A: Hypothesis input (top)
 * Zone B: Real-time execution timeline (middle)
 * Zone C: Progressive result disclosure (bottom)
 */

import React, { useState, useEffect } from 'react';
import {
  PageContainer,
  CalmButton,
  CalmInput,
  CalmCard,
  ExecutionTimeline,
  ROSResultCard,
  ConflictSummary,
  EvidenceTimelinePreview,
} from '../../components/calm';
import { useExecutionStatusPoller } from '../../hooks/useExecutionStatusPoller';
import { api } from '../../services/api';
import type {
  ROSViewResponse,
  ExecutionStatusResponse,
  ConflictExplanationResponse,
  EvidenceTimelineResponse,
  QueryResponse,
} from '../../types/api';
import { Sparkles, TrendingUp, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';

export const Hypothesis: React.FC = () => {
  // Input state
  const [query, setQuery] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Execution state
  const [executionStarted, setExecutionStarted] = useState(false);
  const [executionStatus, setExecutionStatus] = useState<ExecutionStatusResponse | null>(null);
  const { status, isPolling, error: pollingError } = useExecutionStatusPoller(executionStarted);

  // Result state (progressive disclosure)
  const [rosData, setRosData] = useState<ROSViewResponse | null>(null);
  const [conflictData, setConflictData] = useState<ConflictExplanationResponse | null>(null);
  const [evidenceData, setEvidenceData] = useState<EvidenceTimelineResponse | null>(null);
  const [resultsLoaded, setResultsLoaded] = useState(false);
  const [initialQueryResponse, setInitialQueryResponse] = useState<QueryResponse | null>(null);

  // Update execution status when polling returns data
  useEffect(() => {
    if (status) {
      console.log('[Hypothesis] Execution status update:', status);
      setExecutionStatus(status);
    }
  }, [status]);

  // Fetch results after execution completes
  useEffect(() => {
    if (!executionStatus) return;

    // Check if all agents are done
    const totalTriggered = Array.isArray(executionStatus.agents_triggered) 
      ? executionStatus.agents_triggered.length 
      : 0;
    const totalCompleted = (Array.isArray(executionStatus.agents_completed) ? executionStatus.agents_completed.length : 0) + 
                          (Array.isArray(executionStatus.agents_failed) ? executionStatus.agents_failed.length : 0);
    const allAgentsDone = totalTriggered > 0 && totalCompleted >= totalTriggered;

    console.log('[Hypothesis] Execution check:', {
      agents_triggered: executionStatus.agents_triggered,
      agents_completed: executionStatus.agents_completed,
      agents_failed: executionStatus.agents_failed,
      totalTriggered,
      totalCompleted,
      allAgentsDone,
      resultsLoaded,
    });

    // Removed !isPolling condition - fetch results immediately when agents complete
    if (allAgentsDone && !resultsLoaded) {
      console.log('[Hypothesis] All agents done, fetching results...');
      fetchResults();
    }
  }, [executionStatus, resultsLoaded]);

  const fetchResults = async () => {
    try {
      console.log('[Hypothesis] Fetching results from API facade...');
      
      // Fetch all results in parallel
      const [ros, conflict, evidence] = await Promise.all([
        api.getROSLatest().catch((err) => {
          console.error('[Hypothesis] Failed to fetch ROS:', err);
          return null;
        }),
        api.getConflictExplanation().catch((err) => {
          console.error('[Hypothesis] Failed to fetch conflicts:', err);
          return null;
        }),
        api.getEvidenceTimeline().catch((err) => {
          console.error('[Hypothesis] Failed to fetch evidence:', err);
          return null;
        }),
      ]);

      console.log('[Hypothesis] API responses:', { ros, conflict, evidence });

      if (ros) {
        console.log('[Hypothesis] Setting ROS data:', ros);
        setRosData(ros);
      }
      if (conflict) setConflictData(conflict);
      if (evidence) setEvidenceData(evidence);
      setResultsLoaded(true);
      console.log('[Hypothesis] Results loaded successfully');
    } catch (error) {
      console.error('[Hypothesis] Failed to fetch results:', error);
    }
  };

  const handleSubmit = async () => {
    if (!query.trim()) return;

    setIsSubmitting(true);
    setSubmitError(null);
    setExecutionStarted(false);
    setExecutionStatus(null);
    setRosData(null);
    setConflictData(null);
    setEvidenceData(null);
    setResultsLoaded(false);
    setInitialQueryResponse(null);

    try {
      // Submit query and capture initial response (may include insights)
      console.log('[Hypothesis] Submitting query:', query);
      const resp = await api.submitQuery(query);
      console.log('[Hypothesis] Query submitted successfully, response:', resp);
      setInitialQueryResponse(resp);

      // Start execution polling
      setExecutionStarted(true);
    } catch (error: any) {
      console.error('[Hypothesis] Query submission error:', error);
      setSubmitError(
        error?.response?.data?.detail || 'Failed to submit hypothesis. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // Determine if input should be disabled
  const isExecuting = isSubmitting || executionStarted;

  return (
    <PageContainer maxWidth="lg">
      <div className="mb-12 animate-calm-fade-in">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 bg-gradient-to-br from-terracotta-500 to-terracotta-600 rounded-xl flex items-center justify-center shadow-md">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-warm-text font-inter tracking-tight">
            Research Hypothesis Analysis
          </h1>
        </div>
        <p className="text-lg text-warm-text-light font-inter ml-13">
          Submit a drug-disease hypothesis for systematic evaluation powered by multi-agent orchestration.
        </p>
      </div>

      {/* ZONE A: Input Section - Minimal, Always Visible */}
      <CalmCard className="mb-8 shadow-lg">
        <div className="flex items-start gap-3 mb-4">
          <TrendingUp className="w-5 h-5 text-terracotta-500 mt-1 flex-shrink-0" />
          <div className="flex-1">
            <label className="block text-sm font-semibold text-warm-text mb-2 font-inter">
              Research Hypothesis
            </label>
            <p className="text-xs text-warm-text-light mb-3 font-inter">
              Example: "Semaglutide for Alzheimer's disease" or "Repurpose metformin for cancer treatment"
            </p>
          </div>
        </div>
        <CalmInput
          value={query}
          onChange={setQuery}
          placeholder="Enter drug-disease hypothesis..."
          multiline
          rows={4}
          className="mb-6"
          disabled={isExecuting}
        />
        <div className="flex items-center gap-3">
          <CalmButton
            onClick={handleSubmit}
            disabled={isExecuting || !query.trim()}
            className="flex items-center gap-2 shadow-md hover:shadow-lg transition-shadow"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Analyze Hypothesis
              </>
            )}
          </CalmButton>
          {query.trim() && !isExecuting && (
            <span className="text-xs text-warm-text-subtle font-inter">
              {query.trim().length} characters
            </span>
          )}
        </div>
      </CalmCard>

      {/* Submission Error */}
      {submitError && (
        <CalmCard className="mb-8 border-2 border-red-200 bg-red-50">
          <div className="flex items-start gap-3 text-red-700">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold font-inter mb-1">Submission Failed</p>
              <p className="text-sm font-inter">{submitError}</p>
            </div>
          </div>
        </CalmCard>
      )}

      {/* ZONE B: Execution Timeline - Appears After Submission */}
      {executionStarted && executionStatus && (
        <div className="mb-8 animate-calm-fade-in">
          <ExecutionTimeline status={executionStatus} />
        </div>
      )}

      {/* Agent Summaries - progressively reveal as agents complete */}
      {executionStarted && executionStatus && initialQueryResponse?.insights && (
        <div className="space-y-4 mb-8 animate-calm-fade-in">
          <h2 className="text-2xl font-bold text-warm-text font-inter">Agent Summaries</h2>
          {executionStatus.agent_details
            .filter((d) => d.status === 'completed' || d.status === 'failed')
            .map((detail) => {
              const insight = initialQueryResponse!.insights.find(
                (i) => i.agent.toLowerCase() === detail.agent_id.toLowerCase()
              );
              return (
                <CalmCard key={detail.agent_id} className="border border-warm-border">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm uppercase tracking-wide text-warm-text-subtle font-inter">
                          {detail.agent_id}
                        </span>
                        <span className="text-xs px-2 py-0.5 rounded bg-terracotta-50 text-terracotta-700 border border-terracotta-200">
                          {detail.status}
                        </span>
                      </div>
                      {insight ? (
                        <>
                          <p className="text-warm-text font-inter mb-2">{insight.finding}</p>
                          <div className="text-sm text-warm-text-subtle font-inter">
                            <span>Confidence: {Math.round(insight.confidence * 100)}%</span>
                            {insight.total_trials !== undefined && (
                              <span className="ml-4">Trials: {insight.total_trials}</span>
                            )}
                          </div>
                        </>
                      ) : (
                        <p className="text-warm-text-subtle font-inter">No summary available for this agent.</p>
                      )}
                    </div>
                  </div>
                </CalmCard>
              );
            })}
        </div>
      )}

      {/* Polling Error */}
      {pollingError && executionStarted && (
        <CalmCard className="mb-8 border-2 border-amber-200 bg-amber-50">
          <div className="flex items-start gap-3 text-amber-700">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold font-inter mb-1">Status Update Timeout</p>
              <p className="text-sm font-inter">
                Still monitoring execution. This can take a few minutes for complex analyses.
              </p>
            </div>
          </div>
        </CalmCard>
      )}

      {/* ZONE C: Results - Progressive Disclosure */}
      {resultsLoaded && (
        <div className="space-y-6 animate-calm-fade-in">
          {/* ROS Score Card */}
          {rosData && <ROSResultCard rosData={rosData} />}

          {/* Conflict Analysis */}
          {conflictData && <ConflictSummary conflict={conflictData} />}

          {/* Evidence Timeline Preview */}
          {evidenceData && <EvidenceTimelinePreview timeline={evidenceData} limit={5} />}


          {/* Completion Message */}
          {isPolling === false && (
            <CalmCard className="border-2 border-emerald-200 bg-emerald-50">
              <div className="flex items-center gap-3 text-emerald-700">
                <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                <div>
                  <p className="font-semibold font-inter">Analysis Complete</p>
                  <p className="text-sm font-inter">
                    All agents have finished processing. Results are ready for review.
                  </p>
                </div>
              </div>
            </CalmCard>
          )}
        </div>
      )}
    </PageContainer>
  );
};
