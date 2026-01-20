/**
 * Research Console - Primary Interaction Surface
 * 
 * STRICT STATE MACHINE IMPLEMENTATION
 * 0. IDLE: Input ready
 * 1. SUBMITTING: Query sent
 * 2. EXECUTING: Polling progress (Live)
 * 3. COMPLETED: ROS & Data available
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  PageContainer,
  CalmCard,
  CalmInput,
  CalmButton,
  CalmBadge,
  ROSResultCard,
  ReferencesPanel
} from '../../components/calm';
import { api } from '../../services/api';
import { useQueryRefresh } from '../../context/QueryContext';
import type { ROSViewResponse, ExecutionStatusResponse, QueryResponse } from '../../types/api';
import { 
  Sparkles, 
  Activity, 
  CheckCircle2, 
  Clock, 
  AlertCircle,
  ArrowRight,
  Database,
  FileText,
  Search,
  Scale
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

// STRICT PAGE STATES
type ConsoleState = 'IDLE' | 'SUBMITTING' | 'EXECUTING' | 'COMPLETED';

// Agent configuration for consistent display order
const AGENTS = [
  { id: 'clinical', label: 'Clinical Trials', icon: Activity },
  { id: 'market', label: 'Market Intelligence', icon: Search },
  { id: 'patent', label: 'Patent Landscape', icon: Scale },
  { id: 'literature', label: 'Scientific Literature', icon: FileText },
];

export const Hypothesis: React.FC = () => {
  const navigate = useNavigate();
  const { notifyQuerySubmitted } = useQueryRefresh();

  // --- STATE ---
  const [consoleState, setConsoleState] = useState<ConsoleState>('IDLE');
  const [query, setQuery] = useState('');
  const [executionData, setExecutionData] = useState<ExecutionStatusResponse | null>(null);
  const [rosData, setRosData] = useState<ROSViewResponse | null>(null);
  const [queryData, setQueryData] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Polling ref to stop polling when complete
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // --- ACTIONS ---

  const handleAnalyze = async () => {
    if (!query.trim()) return;

    // Transition: IDLE -> SUBMITTING
    // Clear ALL previous query data first
    setConsoleState('SUBMITTING');
    setError(null);
    setExecutionData(null);
    setRosData(null);
    setQueryData(null);

    try {
      // Start the heavy job
      // Note: We transition to EXECUTING immediately to show the UI
      setConsoleState('EXECUTING');
      
      // Fire the POST request (Blocking)
      // We start polling in parallel in useEffect
      const response = await api.submitQuery(query);
      setQueryData(response);

      // Once POST returns, we assume completion
      await handleCompletion();
      
    } catch (err: any) {
      console.error('Analysis failed:', err);
      setError(err?.response?.data?.detail || 'System failed to execute analysis. Please try again.');
      setConsoleState('IDLE'); // Reset on error
      setExecutionData(null);
      setRosData(null);
    }
  };

  const handleCompletion = async () => {
    try {
      // Fetch final states
      const [finalExecution, finalRos] = await Promise.all([
        api.getExecutionStatus(),
        api.getROSLatest()
      ]);

      setExecutionData(finalExecution);
      setRosData(finalRos);
      setConsoleState('COMPLETED');
      
      // Notify all pages that a new query has been completed
      console.log('[Hypothesis] Query completed, notifying pages...');
      notifyQuerySubmitted();
    } catch (err) {
      console.error('Failed to fetch results:', err);
      // Fallback: stay in executing or show partial error? 
      // We'll show error but keep state reachable
      setError('Analysis finished but results could not be loaded.');
    }
  };

  // --- EFFECTS ---

  // Polling Logic: Active only in EXECUTING state
  useEffect(() => {
    if (consoleState === 'EXECUTING') {
      const poll = async () => {
        try {
          const status = await api.getExecutionStatus();
          // Verify this status belongs to CURRENT query (by checking timestamp or active agents)
          // Since we can't easily check ID, we just display what we get.
          // If the backend is blocking, this might timeout or return old data.
          // We update state if we get a valid response.
          setExecutionData(status);
        } catch (e) {
          // Ignore polling errors (backend busy)
          console.debug('Polling skipped/failed:', e);
        }
      };

      // Poll every 1s
      pollIntervalRef.current = setInterval(poll, 1000);
      poll(); // Immediate poll
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [consoleState]);

  // --- RENDER HELPERS ---

  const getStatusBadge = (state: ConsoleState) => {
    switch (state) {
      case 'IDLE': return <CalmBadge variant="neutral">System Ready</CalmBadge>;
      case 'SUBMITTING': return <CalmBadge variant="info">Initiating...</CalmBadge>;
      case 'EXECUTING': return <CalmBadge variant="warning">Processing</CalmBadge>;
      case 'COMPLETED': return <CalmBadge variant="positive">Analysis Complete</CalmBadge>;
    }
  };

  const getAgentStatus = (agentId: string) => {
    if (!executionData) return 'pending';
    if (executionData.agents_completed.includes(agentId)) return 'completed';
    if (executionData.agents_failed.includes(agentId)) return 'failed';
    if (executionData.agents_triggered.includes(agentId)) return 'running';
    // If we are COMPLETED but agent not in triggered, it was skipped
    if (consoleState === 'COMPLETED') return 'skipped';
    return 'pending'; // Default during execution
  };

  // --- UI SECTIONS ---

  return (
    <PageContainer maxWidth="lg">
      
      {/* 1. CONSOLE HEADER */}
      <div className="flex items-center justify-between mb-8 pt-4">
        <div>
          <h1 className="text-3xl font-bold text-warm-text font-inter tracking-tight mb-1">
            Research Console
          </h1>
          <p className="text-warm-text-light font-inter text-sm">
            MAESTRO Pharmaceutical Intelligence Grid
          </p>
        </div>
        <div className="flex items-center gap-3">
           {getStatusBadge(consoleState)}
        </div>
      </div>

      {/* 2. INPUT PANEL */}
      <CalmCard className={`mb-8 transition-opacity duration-500 ${consoleState === 'COMPLETED' ? 'opacity-75' : 'opacity-100'}`}>
        <div className="mb-4">
           <label className="block text-xs font-semibold text-warm-text-subtle uppercase tracking-wider mb-2 font-inter">
             Research Hypothesis
           </label>
           <CalmInput 
             value={query}
             onChange={(val) => {
               // When user starts typing a new query, clear old results
               if (consoleState === 'COMPLETED') {
                 setExecutionData(null);
                 setRosData(null);
               }
               setQuery(val);
             }}
             placeholder="e.g. Semaglutide for Alzheimer's disease"
             multiline
             rows={3}
             disabled={consoleState !== 'IDLE' && consoleState !== 'COMPLETED'}
             className="text-lg font-inter"
           />
        </div>

        {(consoleState === 'IDLE' || consoleState === 'COMPLETED') && (
          <div className="flex justify-end">
            <CalmButton 
              onClick={handleAnalyze}
              disabled={!query.trim()}
              className="flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              Analyze Research Opportunity
            </CalmButton>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-rose-50 border border-rose-100 rounded-md flex items-start gap-3">
             <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
             <p className="text-sm text-rose-700 font-inter">{error}</p>
          </div>
        )}
      </CalmCard>

      {/* 3. AGENT EXECUTION PANEL (Visible during & after execution) */}
      {(consoleState === 'EXECUTING' || consoleState === 'COMPLETED') && (
        <div className="mb-8 animate-calm-fade-in">
          <h3 className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wider mb-4 font-inter">
            System Orchestration
          </h3>
          
          <CalmCard className="p-0 overflow-hidden border border-warm-border">
             {AGENTS.map((agent, idx) => {
               const status = getAgentStatus(agent.id);
               const detail = executionData?.agent_details?.find(d => d.agent_id === agent.id);
               const isLast = idx === AGENTS.length - 1;

               let statusColor = "text-warm-text-light";
               let statusIcon = <div className="w-2 h-2 rounded-full bg-warm-divider" />;
               let statusBg = "bg-white";

               if (status === 'running') {
                 statusColor = "text-amber-600";
                 statusIcon = <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />;
                 statusBg = "bg-amber-50/30";
               } else if (status === 'completed') {
                 statusColor = "text-sage-700";
                 statusIcon = <CheckCircle2 className="w-4 h-4 text-sage-600" />;
                 statusBg = "bg-sage-50/30";
               } else if (status === 'failed') {
                 statusColor = "text-rose-700";
                 statusIcon = <AlertCircle className="w-4 h-4 text-rose-600" />;
                 statusBg = "bg-rose-50/30";
               }

               return (
                 <div key={agent.id} className={`flex items-center justify-between p-4 ${statusBg} ${!isLast ? 'border-b border-warm-divider' : ''}`}>
                   <div className="flex items-center gap-4">
                     <div className={`p-2 rounded-lg bg-white border border-warm-divider text-warm-text-subtle`}>
                       <agent.icon className="w-4 h-4" />
                     </div>
                     <div>
                       <p className="text-sm font-semibold text-warm-text font-inter">{agent.label}</p>
                       <p className="text-xs text-warm-text-light font-inter capitalize">
                         {status === 'pending' ? 'Waiting...' : status}
                       </p>
                     </div>
                   </div>
                   
                   <div className="flex items-center gap-6 text-right">
                     {status === 'completed' && detail && (
                       <>
                         <div className="hidden sm:block">
                           <p className="text-xs text-warm-text-subtle font-inter">Duration</p>
                           <p className="text-sm font-medium text-warm-text font-inter">
                             {detail.duration_ms ? `${(detail.duration_ms / 1000).toFixed(1)}s` : '-'}
                           </p>
                         </div>
                         <div className="min-w-[80px]">
                           <p className="text-xs text-warm-text-subtle font-inter">Results</p>
                           <p className="text-sm font-medium text-warm-text font-inter">
                             {detail.result_count ?? 0}
                           </p>
                         </div>
                       </>
                     )}
                     <div className="w-6 flex justify-center">
                       {statusIcon}
                     </div>
                   </div>
                 </div>
               );
             })}
             
             {/* Total System Time Footer */}
             {executionData?.execution_time_ms && (
               <div className="px-4 py-2 bg-warm-bg-alt border-t border-warm-divider flex justify-end">
                 <p className="text-xs text-warm-text-subtle font-inter flex items-center gap-2">
                   <Clock className="w-3 h-3" />
                   Total Execution Time: {(executionData.execution_time_ms / 1000).toFixed(1)}s
                 </p>
               </div>
             )}
          </CalmCard>
        </div>
      )}

      {/* 4. ROS RESULT PANEL (State 3) */}
      {consoleState === 'COMPLETED' && rosData && (
        <div className="animate-calm-fade-in space-y-8">
          
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wider font-inter">
              Research Opportunity Score
            </h3>
            <span className="text-xs text-warm-text-light font-inter">Generated {new Date().toLocaleTimeString()}</span>
          </div>

          <ROSResultCard rosData={rosData} />

          {/* 5. ENHANCED EXECUTIVE SUMMARY PANEL */}
          <div className="grid md:grid-cols-3 gap-6">
            <div className="md:col-span-2">
               <h3 className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wider mb-3 font-inter">
                 Executive Summary
               </h3>
               <CalmCard className="h-full">
                 <div className="space-y-4">
                   {/* Main Finding - COMPREHENSIVE SUMMARY */}
                   <div>
                     <p className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wide mb-2 font-inter">Comprehensive Analysis Report</p>
                     <div className="text-sm text-warm-text leading-relaxed font-inter max-w-none space-y-3 max-h-96 overflow-y-auto pr-2">
                       {queryData?.summary ? (
                         <div 
                           className="prose prose-sm max-w-none prose-headings:text-warm-text prose-headings:font-semibold prose-p:text-warm-text prose-li:text-warm-text prose-strong:text-warm-text"
                           dangerouslySetInnerHTML={{ 
                             __html: queryData.summary
                               .replace(/### (.*)/g, '<h3 class="text-base font-semibold mt-4 mb-2">$1</h3>')
                               .replace(/## (.*)/g, '<h2 class="text-lg font-bold mt-5 mb-3">$1</h2>')
                               .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                               .replace(/\n- /g, '<br/>• ')
                               .replace(/\n\n/g, '<br/><br/>')
                               .replace(/\n/g, '<br/>')
                           }} 
                         />
                       ) : (
                         <p>{rosData.explanation || "No summary available."}</p>
                       )}
                     </div>
                   </div>

                   {/* Agent Contributions */}
                   {executionData && executionData.agent_details && executionData.agent_details.length > 0 && (
                     <div>
                       <p className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wide mb-2 font-inter">Agent Analysis Breakdown</p>
                       <div className="space-y-2">
                         {executionData.agent_details.map((detail) => {
                           const agentLabel = AGENTS.find(a => a.id === detail.agent_id)?.label || detail.agent_id;
                           return (
                             <div key={detail.agent_id} className="flex items-start gap-3 p-2 bg-warm-bg-alt rounded border border-warm-divider">
                               <div className="flex-1">
                                 <p className="text-xs font-medium text-warm-text font-inter capitalize">{agentLabel}</p>
                                 <p className="text-xs text-warm-text-light font-inter mt-0.5">
                                   {detail.status === 'completed' 
                                     ? `${detail.result_count || 0} results • ${detail.duration_ms ? (detail.duration_ms / 1000).toFixed(1) + 's' : 'N/A'}`
                                     : detail.status === 'failed'
                                     ? `Failed: ${detail.error || 'Unknown error'}`
                                     : 'Pending'}
                                 </p>
                               </div>
                             </div>
                           );
                         })}
                       </div>
                     </div>
                   )}

                   {/* Evidence Summary */}
                   {rosData.metadata && (
                     <div>
                       <p className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wide mb-2 font-inter">Evidence Summary</p>
                       <div className="grid grid-cols-3 gap-2 text-xs">
                         <div className="p-2 bg-sage-50 border border-sage-100 rounded">
                           <p className="text-sage-700 font-semibold">{rosData.metadata.num_supporting_evidence || 0}</p>
                           <p className="text-sage-600 text-xs">Supporting</p>
                         </div>
                         <div className="p-2 bg-amber-50 border border-amber-100 rounded">
                           <p className="text-amber-700 font-semibold">{rosData.metadata.num_suggesting_evidence || 0}</p>
                           <p className="text-amber-600 text-xs">Suggesting</p>
                         </div>
                         <div className="p-2 bg-rose-50 border border-rose-100 rounded">
                           <p className="text-rose-700 font-semibold">{rosData.metadata.num_contradicting_evidence || 0}</p>
                           <p className="text-rose-600 text-xs">Contradicting</p>
                         </div>
                       </div>
                     </div>
                   )}

                   {/* Distinct Sources */}
                   {rosData.metadata?.distinct_agents && rosData.metadata.distinct_agents.length > 0 && (
                     <div>
                       <p className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wide mb-2 font-inter">Data Sources</p>
                       <div className="flex flex-wrap gap-1">
                         {rosData.metadata.distinct_agents.map((agent) => (
                           <span key={agent} className="px-2 py-1 bg-warm-bg-alt border border-warm-divider rounded text-xs text-warm-text font-inter capitalize">
                             {agent}
                           </span>
                         ))}
                       </div>
                     </div>
                   )}
                 </div>
               </CalmCard>
            </div>
            
            {/* 6. NAVIGATION AFFORDANCES */}
            <div>
               <h3 className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wider mb-3 font-inter">
                 Deep Dive
               </h3>
               <div className="space-y-3">
                 <CalmButton 
                   variant="secondary" 
                   className="w-full justify-between group"
                   onClick={() => navigate('/timeline')}
                 >
                   <span>Evidence Timeline</span>
                   <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                 </CalmButton>
                 <CalmButton 
                   variant="secondary" 
                   className="w-full justify-between group"
                   onClick={() => navigate('/graph')}
                 >
                   <span>Knowledge Graph</span>
                   <Database className="w-4 h-4 opacity-50" />
                 </CalmButton>
                 <CalmButton 
                   variant="secondary" 
                   className="w-full justify-between group"
                   onClick={() => navigate('/conflicts')}
                 >
                   <span>Conflict Analysis</span>
                   <AlertCircle className="w-4 h-4 opacity-50" />
                 </CalmButton>
               </div>
            </div>
          </div>

          {/* 7. REFERENCES SECTION */}
          {queryData?.references && queryData.references.length > 0 && (
            <div className="animate-calm-fade-in">
              <h3 className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wider mb-4 font-inter">
                Supporting Research
              </h3>
              <ReferencesPanel 
                references={queryData.references}
                rosMetadata={rosData?.metadata}
              />
            </div>
          )}
          
          {/* Final Status Banner */}
          <div className="flex justify-center pt-8 pb-12">
            <p className="text-warm-text-subtle text-sm font-inter">
              Analysis stable. System idle.
            </p>
          </div>
        </div>
      )}
    </PageContainer>
  );
};