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
  const [currentQueryId, setCurrentQueryId] = useState<string | null>(null);
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
      const queryId = response.query_id || 'latest';
      setCurrentQueryId(response.query_id || null);

      // Once POST returns, we assume completion
      await handleCompletion(queryId, query);
      
    } catch (err: any) {
      console.error('Analysis failed:', err);
      setError(err?.response?.data?.detail || 'System failed to execute analysis. Please try again.');
      setConsoleState('IDLE'); // Reset on error
      setExecutionData(null);
      setRosData(null);
    }
  };

  const handleCompletion = async (queryId: string, queryText: string) => {
    try {
      // Fetch final states
      const [finalExecution, finalRos] = await Promise.all([
        api.getExecutionStatus(queryId),
        api.getROSLatest(queryId)
      ]);

      setExecutionData(finalExecution);
      setRosData(finalRos);
      setConsoleState('COMPLETED');
      
      // Notify all pages that a new query has been completed
      console.log('[Hypothesis] Query completed, notifying pages...');
      notifyQuerySubmitted(queryId, queryText);
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
          const status = await api.getExecutionStatus(currentQueryId || undefined);
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
  }, [consoleState, currentQueryId]);

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
    // During SUBMITTING or start of EXECUTING, show pending
    if (!executionData || executionData.agents_triggered.length === 0) return 'pending';
    
    if (executionData.agents_completed.includes(agentId)) return 'completed';
    if (executionData.agents_failed.includes(agentId)) return 'failed';
    if (executionData.agents_triggered.includes(agentId)) return 'running';
    
    // If we are COMPLETED but agent not in triggered, it was skipped
    if (consoleState === 'COMPLETED') return 'skipped';
    return 'pending'; // Default during execution
  };

  const getAgentProgress = () => {
    if (!executionData) return 0;
    const total = executionData.agents_triggered.length || AGENTS.length;
    const completed = executionData.agents_completed.length;
    return Math.round((completed / total) * 100);
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
      <CalmCard className={`mb-8 transition-opacity duration-500 border-2 border-orange-100 bg-orange-50/20 ${consoleState === 'COMPLETED' ? 'opacity-75' : 'opacity-100'}`}>
        <div className="mb-4">
           <div className="flex items-center gap-2 mb-2">
             <div className="w-2 h-2 rounded-full bg-orange-500" />
             <label className="block text-xs font-semibold text-orange-900 uppercase tracking-wider font-inter">
               Research Hypothesis
             </label>
           </div>
           <CalmInput 
             value={query}
             onChange={(val) => {
               // When user starts typing a new query, clear old results immediately
               if (consoleState === 'COMPLETED') {
                 setExecutionData(null);
                 setRosData(null);
                 setConsoleState('IDLE');
               }
                setCurrentQueryId(null);
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
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wider font-inter">
              System Orchestration
            </h3>
            {consoleState === 'EXECUTING' && (
              <div className="flex items-center gap-2">
                <div className="w-32 h-1.5 bg-warm-divider rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-emerald-500 to-emerald-600 transition-all duration-300"
                    style={{ width: `${getAgentProgress()}%` }}
                  />
                </div>
                <span className="text-xs font-semibold text-emerald-600 font-inter min-w-[40px]">
                  {getAgentProgress()}%
                </span>
              </div>
            )}
          </div>
          
          <CalmCard className="p-0 overflow-hidden border border-warm-border">
             {AGENTS.map((agent, idx) => {
               const status = getAgentStatus(agent.id);
               const detail = executionData?.agent_details?.find(d => d.agent_id === agent.id);
               const isLast = idx === AGENTS.length - 1;

               let statusColor = "text-warm-text-light";
               let statusIcon = <div className="w-2 h-2 rounded-full bg-warm-divider" />;
               let statusBg = "bg-white";
               let accentColor = "bg-slate-50";
               let progressPercent = 0;

               if (status === 'running') {
                 statusColor = "text-amber-600";
                 statusIcon = <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />;
                 statusBg = "bg-amber-50/30";
                 accentColor = "bg-amber-50";
                 progressPercent = 50; // In-progress
               } else if (status === 'completed') {
                 statusColor = "text-emerald-700";
                 statusIcon = <CheckCircle2 className="w-4 h-4 text-emerald-600" />;
                 statusBg = "bg-emerald-50/30";
                 accentColor = "bg-emerald-50";
                 progressPercent = 100; // Complete
               } else if (status === 'failed') {
                 statusColor = "text-rose-700";
                 statusIcon = <AlertCircle className="w-4 h-4 text-rose-600" />;
                 statusBg = "bg-rose-50/30";
                 accentColor = "bg-rose-50";
               }

               return (
                 <div key={agent.id} className={`flex flex-col p-4 ${statusBg} ${!isLast ? 'border-b border-warm-divider' : ''}`}>
                   <div className="flex items-center justify-between mb-3">
                     <div className="flex items-center gap-4 flex-1">
                       <div className={`p-2 rounded-lg border border-warm-divider ${accentColor}`}>
                         <agent.icon className="w-4 h-4 text-warm-text-subtle" />
                       </div>
                       <div>
                         <p className="text-sm font-semibold text-warm-text font-inter">{agent.label}</p>
                         <p className={`text-xs font-medium font-inter capitalize ${statusColor}`}>
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
                   
                   {/* Progress bar */}
                   {status !== 'pending' && (
                     <div className="ml-12 h-1 bg-warm-divider rounded-full overflow-hidden">
                       <div
                         className={`h-full transition-all duration-300 ${
                           status === 'completed'
                             ? 'bg-gradient-to-r from-emerald-500 to-emerald-600'
                             : status === 'running'
                             ? 'bg-gradient-to-r from-amber-400 to-amber-500'
                             : 'bg-gradient-to-r from-rose-500 to-rose-600'
                         }`}
                         style={{ width: `${progressPercent}%` }}
                       />
                     </div>
                   )}
                 </div>
               );
             })}
             
             {/* Total System Time Footer */}
             {executionData?.execution_time_ms && (
               <div className="px-4 py-3 bg-emerald-50/40 border-t border-emerald-200 flex justify-between items-center">
                 <div className="flex items-center gap-2">
                   <div className="w-2 h-2 rounded-full bg-emerald-500" />
                   <span className="text-xs font-semibold text-emerald-700 font-inter">{executionData.agents_completed.length}/{executionData.agents_triggered.length} Agents Complete</span>
                 </div>
                 <p className="text-xs text-emerald-700 font-inter flex items-center gap-2 font-semibold">
                   <Clock className="w-3 h-3" />
                   {(executionData.execution_time_ms / 1000).toFixed(1)}s
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
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-orange-500" />
              <h3 className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wider font-inter">
                Research Opportunity Score
              </h3>
            </div>
            <span className="text-xs text-warm-text-light font-inter">Generated {new Date().toLocaleTimeString()}</span>
          </div>

          <ROSResultCard rosData={rosData} />

          {/* 5b. DETAILED AGENT INSIGHTS SECTION */}
          {queryData?.insights && queryData.insights.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-indigo-500" />
                <h3 className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wider font-inter">
                  Agent Findings
                </h3>
              </div>
              <div className="grid gap-4">
                {queryData.insights.map((insight: any, idx: number) => {
                  const bgColor = idx % 4 === 0 ? 'bg-blue-50/30 border-blue-100' : 
                                 idx % 4 === 1 ? 'bg-emerald-50/30 border-emerald-100' :
                                 idx % 4 === 2 ? 'bg-purple-50/30 border-purple-100' :
                                 'bg-orange-50/30 border-orange-100';
                  
                  // Format the finding text into readable sections with markdown support
                  const formatFinding = (text: string) => {
                    // Split by numbered sections (e.g., "**1. OVERVIEW:**")
                    const sections = text.split(/(?=\*\*\d+\.\s+[A-Z][A-Z\s]+:\*\*)/g);
                    
                    if (sections.length > 1) {
                      // Has numbered sections
                      return sections.map((section, i) => {
                        const match = section.match(/^\*\*(\d+\.\s+[A-Z][A-Z\s]+:)\*\*(.*)/s);
                        if (match) {
                          // Process content for inline bold/italic
                          const processInlineFormatting = (content: string) => {
                            const parts: (string | React.ReactElement)[] = [];
                            let currentText = content;
                            let key = 0;
                            
                            // Replace **text** with bold
                            const boldRegex = /\*\*([^*]+)\*\*/g;
                            let lastIndex = 0;
                            let boldMatch;
                            
                            while ((boldMatch = boldRegex.exec(currentText)) !== null) {
                              // Add text before match
                              if (boldMatch.index > lastIndex) {
                                parts.push(currentText.slice(lastIndex, boldMatch.index));
                              }
                              // Add bold text
                              parts.push(<strong key={key++} className="font-bold text-warm-text">{boldMatch[1]}</strong>);
                              lastIndex = boldMatch.index + boldMatch[0].length;
                            }
                            
                            // Add remaining text
                            if (lastIndex < currentText.length) {
                              parts.push(currentText.slice(lastIndex));
                            }
                            
                            return parts.length > 0 ? parts : currentText;
                          };
                          
                          return (
                            <div key={i} className="mb-4 last:mb-0">
                              <h5 className="text-sm font-bold text-warm-text uppercase tracking-wide mb-2 font-inter border-b border-warm-divider/20 pb-1">
                                {match[1].trim()}
                              </h5>
                              <div className="text-sm text-warm-text-light leading-relaxed font-inter pl-2">
                                {processInlineFormatting(match[2].trim())}
                              </div>
                            </div>
                          );
                        }
                        return null;
                      }).filter(Boolean);
                    } else {
                      // No clear sections - process as paragraph with inline formatting
                      const processInlineFormatting = (content: string) => {
                        const parts: (string | React.ReactElement)[] = [];
                        let currentText = content;
                        let key = 0;
                        
                        // Replace **text** with bold
                        const boldRegex = /\*\*([^*]+)\*\*/g;
                        let lastIndex = 0;
                        let boldMatch;
                        
                        while ((boldMatch = boldRegex.exec(currentText)) !== null) {
                          if (boldMatch.index > lastIndex) {
                            parts.push(currentText.slice(lastIndex, boldMatch.index));
                          }
                          parts.push(<strong key={key++} className="font-bold text-warm-text">{boldMatch[1]}</strong>);
                          lastIndex = boldMatch.index + boldMatch[0].length;
                        }
                        
                        if (lastIndex < currentText.length) {
                          parts.push(currentText.slice(lastIndex));
                        }
                        
                        return parts.length > 0 ? parts : currentText;
                      };
                      
                      // Split into paragraphs by double newline
                      const paragraphs = text.split('\n\n').filter(p => p.trim());
                      
                      return paragraphs.map((para, i) => (
                        <p key={i} className="text-sm text-warm-text-light leading-relaxed font-inter mb-3 last:mb-0">
                          {processInlineFormatting(para.trim())}
                        </p>
                      ));
                    }
                  };
                  
                  return (
                    <CalmCard key={idx} className={`border ${bgColor}`}>
                      <div className="space-y-3">
                        {/* Header */}
                        <div className="flex items-center justify-between pb-2 border-b border-warm-divider/30">
                          <h4 className="text-base font-bold text-warm-text font-inter">{insight.agent}</h4>
                          <span className="text-xs bg-warm-surface-alt text-warm-text-subtle px-3 py-1.5 rounded-full font-semibold font-inter">
                            {insight.confidence}% confidence
                          </span>
                        </div>
                        
                        {/* Metadata badges */}
                        <div className="flex gap-2 text-xs font-inter flex-wrap">
                          {insight.total_trials !== undefined && insight.total_trials > 0 && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-md font-medium">
                              📋 {insight.total_trials} trials
                            </span>
                          )}
                          {insight.sources_used && (
                            <span className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded-md font-medium">
                              📚 {(insight.sources_used as any).web || 0} web + {(insight.sources_used as any).internal || 0} internal
                            </span>
                          )}
                          {insight.total_patents !== undefined && insight.total_patents > 0 && (
                            <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-md font-medium">
                              📄 {insight.total_patents} patents
                            </span>
                          )}
                          {insight.total_publications !== undefined && insight.total_publications > 0 && (
                            <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded-md font-medium">
                              📖 {insight.total_publications} publications
                            </span>
                          )}
                        </div>
                        
                        {/* Finding content with smart formatting */}
                        <div className="pt-2">
                          {formatFinding(insight.finding)}
                        </div>
                      </div>
                    </CalmCard>
                  );
                })}
              </div>
            </div>
          )}

          {/* 5c. RECOMMENDATION SECTION */}
          {queryData?.recommendation && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-sage-500" />
                <h3 className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wider font-inter">
                  Recommendation
                </h3>
              </div>
              <CalmCard className="bg-sage-50/30 border border-sage-100">
                <p className="text-sm text-warm-text leading-relaxed font-inter">{queryData.recommendation}</p>
              </CalmCard>
            </div>
          )}

          {/* 5. ENHANCED EXECUTIVE SUMMARY PANEL */}
          <div className="grid md:grid-cols-3 gap-6">
            <div className="md:col-span-2">
               <div className="flex items-center gap-2 mb-3">
                 <div className="w-2 h-2 rounded-full bg-blue-500" />
                 <h3 className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wider font-inter">
                   Executive Summary
                 </h3>
               </div>
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
                       <div className="flex items-center gap-2 mb-2">
                         <div className="w-2 h-2 rounded-full bg-emerald-500" />
                         <p className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wide font-inter">Agent Analysis Breakdown</p>
                       </div>
                       <div className="space-y-2">
                         {executionData.agent_details.map((detail) => {
                           const agentLabel = AGENTS.find(a => a.id === detail.agent_id)?.label || detail.agent_id;
                           const isCompleted = detail.status === 'completed';
                           return (
                             <div key={detail.agent_id} className={`flex items-start gap-3 p-2 rounded border transition-colors ${
                               isCompleted
                                 ? 'bg-emerald-50/50 border-emerald-200'
                                 : 'bg-warm-bg-alt border-warm-divider'
                             }`}>
                               <div className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${
                                 isCompleted ? 'bg-emerald-500' : 'bg-warm-divider'
                               }`} />
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
                       <div className="flex items-center gap-2 mb-2">
                         <div className="w-2 h-2 rounded-full bg-orange-500" />
                         <p className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wide font-inter">Evidence Quality Metrics</p>
                       </div>
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
               <div className="flex items-center gap-2 mb-3">
                 <div className="w-2 h-2 rounded-full bg-indigo-500" />
                 <h3 className="text-xs font-semibold text-warm-text-subtle uppercase tracking-wider font-inter">
                   Deep Dive
                 </h3>
               </div>
               <div className="space-y-3">
                 <button
                   className="w-full flex items-center justify-between px-4 py-3 rounded-lg font-medium text-sm transition-all font-inter bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-md hover:shadow-lg"
                   onClick={() => navigate('/timeline')}
                 >
                   <span>Evidence Timeline</span>
                   <ArrowRight className="w-4 h-4" />
                 </button>
                 <button
                   className="w-full flex items-center justify-between px-4 py-3 rounded-lg font-medium text-sm transition-all font-inter bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white shadow-md hover:shadow-lg"
                   onClick={() => navigate('/graph')}
                 >
                   <span>Knowledge Graph</span>
                   <Database className="w-4 h-4" />
                 </button>
                 <button
                   className="w-full flex items-center justify-between px-4 py-3 rounded-lg font-medium text-sm transition-all font-inter bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white shadow-md hover:shadow-lg"
                   onClick={() => navigate('/conflicts')}
                 >
                   <span>Conflict Analysis</span>
                   <AlertCircle className="w-4 h-4" />
                 </button>
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