import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Activity, Database, FileText, TrendingUp, Loader, CheckCircle, X, ExternalLink, Calendar, Award, BookOpen, Download, ChevronLeft, ChevronRight, Terminal, Sparkles } from 'lucide-react';

interface Insight {
  agent: string;
  finding: string;
  confidence: number;
}

interface Reference {
  type?: 'patent' | 'paper' | 'clinical-trial' | 'market-report';
  title: string;
  source?: string;
  date?: string;
  url?: string;
  relevance?: number;
  agentId?: string;
  nct_id?: string;
  summary?: string;
}

interface AgentExecutionStatus {
  agent_id: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  result_count?: number;
}

interface AnalysisResults {
  summary: string;
  comprehensive_summary?: string;
  insights: Insight[];
  recommendation: string;
  timelineSaved: string;
  references: Reference[];

  // NEW FIELDS from backend
  confidence_score?: number;
  active_agents?: string[];
  agent_execution_status?: AgentExecutionStatus[];
  market_intelligence?: {
    agentId: string;
    query: string;
    sections: {
      summary: string;
      market_overview: string;
      key_metrics: string;
      drivers_and_trends: string;
      competitive_landscape: string;
      risks_and_opportunities: string;
      future_outlook: string;
    };
    confidence: {
      score: number;
      breakdown: any;
      explanation: string;
      level: string;
    };
    sources: {
      web: string[];
      internal: string[];
    };
  };
  total_trials?: number;
}

interface Agent {
  id: string;
  name: string;
  icon: any;
  color: string;
  status: 'idle' | 'running' | 'complete';
  logs?: string[];
}

const ResearchPage: React.FC = () => {
  const [query, setQuery] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [activeAgents, setActiveAgents] = useState<string[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [agentLogs, setAgentLogs] = useState<Record<string, string[]>>({});
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'overall' | 'clinical' | 'market' | 'other'>('overall');

  const agents: Agent[] = [
    { id: 'market', name: 'Market Intelligence', icon: TrendingUp, color: 'from-blue-500 to-cyan-500', status: 'idle' },
    { id: 'clinical', name: 'Clinical Trials', icon: Activity, color: 'from-green-500 to-emerald-500', status: 'idle' },
    { id: 'patent', name: 'Patent & IP', icon: FileText, color: 'from-purple-500 to-violet-500', status: 'idle' },
    { id: 'trade', name: 'Trade Data', icon: Database, color: 'from-orange-500 to-amber-500', status: 'idle' }
  ];

  const sampleQueries: string[] = [
    "Analyze GLP-1 agonist market opportunity in diabetes",
    "Freedom to operate analysis for CRISPR gene therapy",
    "Clinical trial landscape for Alzheimer's disease",
    "Import dependency analysis for oncology APIs"
  ];

  const simulateAnalysis = async (userQuery: string) => {
    setIsProcessing(true);
    setResults(null);
    setSelectedAgent(null);
    setActiveTab('overall');
    setAgentLogs({});
    setActiveAgents([]);  // Start with no agents, will be updated from backend

    const addLog = (agentId: string, message: string) => {
      setAgentLogs(prev => ({
        ...prev,
        [agentId]: [...(prev[agentId] || []), `${new Date().toLocaleTimeString()}: ${message}`]
      }));
    };

    const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const endpoint = `${apiUrl}/api/query`;

    try {
      // Initial log - we don't know which agents yet
      console.log('📊 Processing query:', userQuery);

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        },
        cache: 'no-store',
        body: JSON.stringify({ query: userQuery }),
      });

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`);
      }

      const data = await response.json();

      // Extract active agents from backend response
      const backendActiveAgents = data.active_agents || [];
      setActiveAgents(backendActiveAgents);

      // Add logs based on execution status
      if (data.agent_execution_status) {
        data.agent_execution_status.forEach((status: AgentExecutionStatus) => {
          const agentName = status.agent_id === 'clinical' ? 'Clinical Trials' :
                           status.agent_id === 'market' ? 'Market Intelligence' : status.agent_id;

          if (status.status === 'completed') {
            addLog(status.agent_id, `✅ ${agentName} Agent completed`);
            addLog(status.agent_id, `Found ${status.result_count || 0} results`);
          } else if (status.status === 'failed') {
            addLog(status.agent_id, `❌ ${agentName} Agent failed`);
          }
        });
      }

      setResults(data);
    } catch (error) {
      console.error('❌ Error calling backend:', error);
      alert(
        'Failed to connect to backend.\n\n' +
        'Make sure:\n' +
        '1. Backend is running: python main.py\n' +
        '2. Backend is on: ' + apiUrl + '\n' +
        '3. Check browser console for details\n\n' +
        'Error: ' + error
      );
      setActiveAgents([]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSearch = () => {
    if (query.trim()) {
      setActiveAgents([]);
      simulateAnalysis(query);
    }
  };

  const handleSampleQuery = (sampleQuery: string) => {
    setQuery(sampleQuery);
    setActiveAgents([]);
    simulateAnalysis(sampleQuery);
  };

  const getAgentStatus = (agentId: string): 'idle' | 'running' | 'complete' => {
    // Check if agent executed and completed
    if (results?.agent_execution_status) {
      const status = results.agent_execution_status.find(s => s.agent_id === agentId);
      if (status) {
        if (status.status === 'completed') return 'complete';
        if (status.status === 'failed') return 'complete';  // Show as complete even if failed
      }
    }

    // Check if agent is currently in the active list
    if (activeAgents.includes(agentId)) {
      if (isProcessing) return 'running';
      return 'complete';
    }

    return 'idle';
  };

  const getTabGlowClass = (tabId: string): string => {
    // CRITICAL FIX: Use backend execution_status to determine if agent is actively running
    // Check if ANY agent matching this tab is in 'running' state
    
    if (!results?.agent_execution_status) {
      return ''; // No execution status available yet
    }

    const relevantAgents = tabId === 'clinical' ? ['clinical'] :
                           tabId === 'market' ? ['market'] :
                           [];

    // Check if any relevant agent is actively RUNNING (not just active)
    const isRunning = results.agent_execution_status.some(status =>
      relevantAgents.includes(status.agent_id) && status.status === 'running'
    );

    if (isRunning) {
      return 'animate-pulse ring-2 ring-purple-500/50 shadow-lg shadow-purple-500/50';
    }

    return '';
  };

  const getAgentReferences = (agentId: string): Reference[] => {
    if (!results) return [];
    return results.references.filter(ref => ref.agentId === agentId);
  };

  const renderTextWithNCTLinks = (text: string) => {
    if (!text) return null;
    const nctPattern = /NCT\d{8}/g;
    const parts = text.split(nctPattern);
    const matches = text.match(nctPattern) || [];
    
    return (
      <>
        {parts.map((part, index) => (
          <React.Fragment key={index}>
            {part}
            {matches[index] && (
              <a
                href={`https://clinicaltrials.gov/study/${matches[index]}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-neon-blue hover:text-neon-cyan underline font-medium inline-flex items-center gap-1 transition-colors"
              >
                {matches[index]}
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </React.Fragment>
        ))}
      </>
    );
  };

  const getTypeIcon = (type: Reference['type']) => {
    switch (type) {
      case 'patent': return <Award className="w-4 h-4" />;
      case 'paper': return <FileText className="w-4 h-4" />;
      case 'clinical-trial': return <Activity className="w-4 h-4" />;
      case 'market-report': return <TrendingUp className="w-4 h-4" />;
    }
  };

  const getTabContent = (): string => {
    if (!results) return '';
    
    switch (activeTab) {
      case 'clinical':
        // FIXED: Return clinical-specific summary, NOT overview
        return results.comprehensive_summary || results.summary;
        
      case 'market':
        // FIXED: Return full market intelligence sections with more lenient check
        if (!results.market_intelligence) {
          return 'No market intelligence data available. Check SERPAPI_KEY configuration.';
        }
        
        const sections = results.market_intelligence.sections;
        
        // FIXED: More lenient check - just verify summary exists and isn't an error message
        const hasValidContent = sections.summary && 
                                sections.summary.length > 20 &&  // More lenient: 20 chars instead of 50
                                !sections.summary.includes('No market intelligence') &&
                                !sections.summary.includes('Check SERPAPI_KEY');
        
        if (!hasValidContent) {
          return `Market intelligence data retrieved but synthesis incomplete. 

Found ${results.market_intelligence.sources?.web?.length || 0} web sources and ${results.market_intelligence.sources?.internal?.length || 0} internal documents.

Raw summary: ${sections.summary}

Check backend logs for detailed synthesis status.`;
        }
        
        // Return formatted market intelligence with all 7 sections
        return `${sections.summary}

## Market Overview
${sections.market_overview}

## Key Metrics
${sections.key_metrics}

## Drivers and Trends
${sections.drivers_and_trends}

## Competitive Landscape
${sections.competitive_landscape}

## Risks and Opportunities
${sections.risks_and_opportunities}

## Future Outlook
${sections.future_outlook}`.trim();
        
      case 'other':
        return 'Other agents data will appear here when implemented.';
        
      default:
        // FIXED: Overview tab returns synthesized overview (NOT clinical summary)
        // This is the multi-agent synthesis from master agent
        return results.summary;
    }
  };

  const getTabReferences = (): Reference[] => {
    if (!results) return [];

    // Defensive filtering with strict agentId enforcement
    switch (activeTab) {
      case 'clinical':
        // Only show references explicitly tagged as clinical
        return results.references.filter(ref =>
          ref.agentId && ref.agentId === 'clinical'
        );
      case 'market':
        // Only show references explicitly tagged as market
        return results.references.filter(ref =>
          ref.agentId && ref.agentId === 'market'
        );
      case 'other':
        // Show references not tagged as clinical or market
        return results.references.filter(ref =>
          ref.agentId && ref.agentId !== 'clinical' && ref.agentId !== 'market'
        );
      default:
        // Overview: show all references
        return results.references;
    }
  };

  const handleExportPDF = () => {
    if (!results) return;
    const pdfContent = `
MAESTRO Analysis Report
========================

Query: ${query}
Generated: ${new Date().toLocaleString()}
Time Saved: ${results.timelineSaved}

SUMMARY
-------
${results.summary}

INSIGHTS
--------
${results.insights.map((insight, idx) => `
${idx + 1}. ${insight.agent}
   Finding: ${insight.finding}
   Confidence: ${insight.confidence}%
`).join('\n')}

RECOMMENDATION
--------------
${results.recommendation}

REFERENCES
----------
${results.references.map((ref, idx) => `
${idx + 1}. [${ref.nct_id ? 'CLINICAL TRIAL' : (ref.type?.toUpperCase() || 'REFERENCE')}] ${ref.title}
   ${ref.nct_id ? `NCT ID: ${ref.nct_id}` : `Source: ${ref.source || 'N/A'}`}
   ${ref.date ? `Date: ${ref.date}` : ''}
   ${ref.url ? `URL: ${ref.url}` : ref.nct_id ? `URL: https://clinicaltrials.gov/study/${ref.nct_id}` : ''}
   ${ref.relevance ? `Relevance: ${ref.relevance}%` : ''}
   ${ref.summary ? `Summary: ${ref.summary}` : ''}
`).join('\n')}
    `.trim();

    const blob = new Blob([pdfContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `maestro-analysis-${Date.now()}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-deep-black text-white flex flex-col overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-deep-black via-charcoal to-dark-gray opacity-50" />
      
      <header className="relative z-20 border-b border-purple-500/20 bg-charcoal/50 backdrop-blur-xl">
        <div className="px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Sparkles className="w-8 h-8 text-neon-purple animate-pulse" />
              <div className="absolute inset-0 bg-neon-purple rounded-full blur-lg opacity-50" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-neon-purple via-neon-blue to-neon-cyan bg-clip-text text-transparent">
                MAESTRO Research Console
              </h1>
              <p className="text-xs text-gray-500">Multi-Agent Therapeutic Intelligence</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {isProcessing && (
              <div className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-500/20 to-blue-500/20 border border-purple-500/30 flex items-center gap-2">
                <Loader className="w-4 h-4 animate-spin text-neon-purple" />
                <span className="text-sm text-gray-300">Processing...</span>
              </div>
            )}
            {results && (
              <div className="px-4 py-2 rounded-lg bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-sm text-gray-300">Analysis Complete</span>
              </div>
            )}
            <button
              onClick={() => {
                setResults(null);
                setQuery('');
                setActiveAgents([]);
                setAgentLogs({});
                setSelectedAgent(null);
              }}
              className="px-4 py-2 rounded-lg bg-purple-500/20 border border-purple-500/50 hover:border-purple-500/70 text-sm font-medium text-purple-300 hover:text-purple-200 transition-all flex items-center gap-2"
            >
              <X className="w-4 h-4" />
              New Query
            </button>
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden relative z-10">
          {!sidebarCollapsed && (
            <motion.aside
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="w-80 border-r border-purple-500/20 bg-charcoal/80 backdrop-blur-xl overflow-y-auto"
            >
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-bold text-gray-300 flex items-center gap-2">
                    <Terminal className="w-5 h-5 text-neon-purple" />
                    AI Agents
                  </h2>
                  <button
                    onClick={() => setSidebarCollapsed(true)}
                    className="p-2 hover:bg-purple-500/10 rounded-lg transition-colors"
                  >
                    <ChevronLeft className="w-5 h-5 text-gray-400" />
                  </button>
                </div>

                <div className="space-y-3">
                  {agents.map((agent) => {
                    const status = getAgentStatus(agent.id);
                    const Icon = agent.icon;
                    const refs = getAgentReferences(agent.id);

                    return (
                      <motion.div
                        key={agent.id}
                        whileHover={{ scale: status !== 'idle' ? 1.02 : 1 }}
                        onClick={() => status === 'complete' && setSelectedAgent(agent.id)}
                        className={`relative p-4 rounded-xl border transition-all cursor-pointer ${
                          status === 'idle' 
                            ? 'border-gray-700 bg-dark-gray/50 hover:border-gray-600'
                            : status === 'running'
                            ? `border-purple-500/50 bg-gradient-to-br ${agent.color} bg-opacity-10 animate-pulse-glow`
                            : `border-green-500/50 bg-gradient-to-br ${agent.color} bg-opacity-10`
                        }`}
                      >
                        {status === 'running' && (
                          <div className="absolute inset-0 bg-gradient-to-r from-purple-600/20 to-blue-600/20 rounded-xl animate-pulse-glow" />
                        )}
                        {status === 'complete' && (
                          <div className="absolute inset-0 bg-gradient-to-r from-green-600/10 to-emerald-600/10 rounded-xl" />
                        )}
                        
                        <div className="relative flex items-start gap-3">
                          <div className={`p-2 rounded-lg ${
                            status === 'idle'
                              ? 'bg-gray-700/50'
                              : `bg-gradient-to-br ${agent.color}`
                          } transition-all`}>
                            <Icon className={`w-5 h-5 ${status === 'idle' ? 'text-gray-400' : 'text-white'}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="font-semibold text-sm text-white mb-1">{agent.name}</h3>
                            <p className="text-xs text-gray-400">
                              {status === 'idle' && 'Standby'}
                              {status === 'running' && (
                                <span className="flex items-center gap-1">
                                  <Loader className="w-3 h-3 animate-spin" />
                                  Processing...
                                </span>
                              )}
                              {status === 'complete' && (
                                <span className="flex items-center gap-1 text-green-400">
                                  <CheckCircle className="w-3 h-3" />
                                  {refs.length} results
                                </span>
                              )}
                            </p>
                            {status === 'running' && agentLogs[agent.id] && agentLogs[agent.id].length > 0 && (
                              <div className="mt-2 space-y-1">
                                {agentLogs[agent.id].slice(-3).map((log, idx) => (
                                  <div key={idx} className="text-xs text-gray-500 flex items-start gap-1">
                                    <span className="text-green-500">›</span>
                                    <span className="flex-1">{log}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            </motion.aside>
          )}

        {sidebarCollapsed && (
          <button
            onClick={() => setSidebarCollapsed(false)}
            className="absolute left-0 top-1/2 -translate-y-1/2 p-3 bg-charcoal/80 backdrop-blur-xl border-r border-purple-500/20 rounded-r-lg hover:bg-charcoal transition-colors z-20"
          >
            <ChevronRight className="w-5 h-5 text-gray-400" />
          </button>
        )}

        <main className="flex-1 overflow-y-auto">
          <div className="max-w-6xl mx-auto p-8">
            {!results ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-8"
              >
                <div className="text-center mb-12">
                  <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-neon-purple via-neon-blue to-neon-cyan bg-clip-text text-transparent">
                    Enter Research Query
                  </h2>
                  <p className="text-gray-400">Deploy AI agents to analyze therapeutic intelligence</p>
                </div>

                <div className="relative">
                  <div className="absolute -inset-1 bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl blur opacity-25" />
                  <div className="relative bg-charcoal/50 backdrop-blur-xl border border-purple-500/30 rounded-2xl p-6">
                    <div className="flex gap-3">
                      <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                        placeholder="e.g., Analyze GLP-1 agonist market opportunity..."
                        className="flex-1 px-6 py-4 bg-dark-gray/50 border border-purple-500/30 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                        disabled={isProcessing}
                      />
                      <button
                        onClick={handleSearch}
                        disabled={isProcessing || !query.trim()}
                        className="px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-all flex items-center gap-2 shadow-lg shadow-purple-500/30"
                      >
                        {isProcessing ? <Loader className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
                        {isProcessing ? 'Analyzing' : 'Analyze'}
                      </button>
                    </div>

                    <div className="mt-6">
                      <p className="text-sm text-gray-400 mb-3 flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-amber-400" />
                        Sample queries
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {sampleQueries.map((sq, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSampleQuery(sq)}
                            disabled={isProcessing}
                            className="text-xs px-4 py-2 bg-dark-gray/50 border border-purple-500/20 hover:border-purple-500/50 rounded-full text-gray-300 hover:text-white transition-all disabled:opacity-50"
                          >
                            {sq}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-6">
                  {[
                    { value: '70%', label: 'Faster Research', color: 'from-blue-500 to-cyan-500' },
                    { value: '4', label: 'AI Agents', color: 'from-purple-500 to-violet-500' },
                    { value: '100K+', label: 'Data Sources', color: 'from-orange-500 to-amber-500' },
                  ].map((stat, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      className="relative group"
                    >
                      <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl blur opacity-25 group-hover:opacity-75 transition-opacity" />
                      <div className="relative bg-charcoal/50 backdrop-blur-xl border border-purple-500/20 rounded-xl p-6 text-center">
                        <div className={`text-3xl font-bold bg-gradient-to-r ${stat.color} bg-clip-text text-transparent mb-2`}>
                          {stat.value}
                        </div>
                        <p className="text-sm text-gray-400">{stat.label}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-6"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-2">Analysis Results</h2>
                    <p className="text-sm text-gray-400">Query: {query}</p>
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={handleExportPDF}
                      className="px-4 py-2 bg-dark-gray/50 border border-purple-500/30 hover:border-purple-500/50 rounded-lg text-white flex items-center gap-2 transition-all"
                    >
                      <Download className="w-4 h-4" />
                      Export
                    </button>
                    <button
                      onClick={() => {
                        setResults(null);
                        setQuery('');
                        setActiveAgents([]);
                      }}
                      className="px-4 py-2 bg-dark-gray/50 border border-purple-500/30 hover:border-purple-500/50 rounded-lg text-white flex items-center gap-2 transition-all"
                    >
                      <X className="w-4 h-4" />
                      New Query
                    </button>
                  </div>
                </div>

                <div className="flex gap-3 border-b border-purple-500/20 pb-3">
                  <button
                    onClick={() => setActiveTab('overall')}
                    className={`px-4 py-2 rounded-lg transition-all ${
                      activeTab === 'overall'
                        ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white'
                        : 'bg-dark-gray/50 text-gray-400 hover:text-white'
                    }`}
                  >
                    Overview
                  </button>
                  <button
                    onClick={() => setActiveTab('clinical')}
                    className={`px-4 py-2 rounded-lg transition-all ${getTabGlowClass('clinical')} ${
                      activeTab === 'clinical'
                        ? 'bg-gradient-to-r from-green-600 to-emerald-600 text-white'
                        : 'bg-dark-gray/50 text-gray-400 hover:text-white'
                    }`}
                  >
                    Clinical Trials ({results.references.filter(r => r.agentId === 'clinical').length})
                  </button>
                  <button
                    onClick={() => setActiveTab('market')}
                    className={`px-4 py-2 rounded-lg transition-all ${getTabGlowClass('market')} ${
                      activeTab === 'market'
                        ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white'
                        : 'bg-dark-gray/50 text-gray-400 hover:text-white'
                    }`}
                  >
                    Market Intelligence ({results.references.filter(r => r.agentId === 'market').length})
                  </button>
                  <button
                    onClick={() => setActiveTab('other')}
                    className={`px-4 py-2 rounded-lg transition-all ${
                      activeTab === 'other'
                        ? 'bg-gradient-to-r from-orange-600 to-amber-600 text-white'
                        : 'bg-dark-gray/50 text-gray-400 hover:text-white'
                    }`}
                  >
                    Other Agents
                  </button>
                </div>

                <div className="relative">
                  <div className="absolute -inset-1 bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl blur opacity-20" />
                  <div className="relative bg-charcoal/50 backdrop-blur-xl border border-purple-500/30 rounded-2xl p-8">
                    <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                      <BookOpen className="w-5 h-5 text-neon-purple" />
                      Summary
                    </h3>
                    <div className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                      {renderTextWithNCTLinks(getTabContent())}
                    </div>
                  </div>
                </div>

                {getTabReferences().length > 0 && (
                  <div>
                    <h3 className="text-xl font-bold text-white mb-4">References ({getTabReferences().length})</h3>
                    <div className="space-y-3">
                      {getTabReferences().map((ref, idx) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: idx * 0.05 }}
                          className="relative group"
                        >
                          <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl blur opacity-0 group-hover:opacity-50 transition-opacity" />
                          <div className="relative bg-charcoal/50 backdrop-blur-xl border border-purple-500/20 hover:border-purple-500/40 rounded-xl p-5 transition-all">
                            <div className="flex items-start gap-4">
                              <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg">
                                {getTypeIcon(ref.type)}
                              </div>
                              <div className="flex-1 min-w-0">
                                <h4 className="font-semibold text-white mb-1">{ref.title}</h4>
                                {ref.nct_id && (
                                  <p className="text-sm text-gray-400 mb-1 font-mono">NCT ID: {ref.nct_id}</p>
                                )}
                                {ref.summary && (
                                  <p className="text-sm text-gray-400 mb-2">{ref.summary}</p>
                                )}
                                <div className="flex items-center gap-4">
                                  {ref.date && (
                                    <span className="text-xs text-gray-500 flex items-center gap-1">
                                      <Calendar className="w-3 h-3" />
                                      {ref.date}
                                    </span>
                                  )}
                                  {(ref.url || ref.nct_id) && (
                                    <a
                                      href={ref.nct_id ? `https://clinicaltrials.gov/study/${ref.nct_id}` : ref.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-sm text-neon-blue hover:text-neon-cyan flex items-center gap-1 transition-colors"
                                    >
                                      View Source <ExternalLink className="w-3 h-3" />
                                    </a>
                                  )}
                                  {!ref.url && !ref.nct_id && (
                                    <span className="text-sm text-gray-500">No URL available</span>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </div>
        </main>

          {selectedAgent && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              onClick={() => setSelectedAgent(null)}
              className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-6"
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                onClick={(e) => e.stopPropagation()}
                className="bg-charcoal border border-purple-500/30 rounded-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden"
              >
                <div className="p-6 border-b border-purple-500/20 flex items-center justify-between">
                  <h2 className="text-xl font-bold text-white">
                    {agents.find(a => a.id === selectedAgent)?.name} Results
                  </h2>
                  <button
                    onClick={() => setSelectedAgent(null)}
                    className="p-2 hover:bg-purple-500/10 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5 text-gray-400" />
                  </button>
                </div>
                <div className="p-6 overflow-y-auto max-h-[calc(80vh-100px)] space-y-3">
                  {getAgentReferences(selectedAgent).map((ref, idx) => (
                    <div key={idx} className="bg-dark-gray/50 border border-purple-500/20 rounded-xl p-4">
                      <h4 className="font-semibold text-white mb-2">{ref.title}</h4>
                      {ref.summary && <p className="text-sm text-gray-400 mb-2">{ref.summary}</p>}
                      <a
                        href={ref.nct_id ? `https://clinicaltrials.gov/study/${ref.nct_id}` : ref.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-neon-blue hover:text-neon-cyan flex items-center gap-1 transition-colors"
                      >
                        View Source <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  ))}
                </div>
              </motion.div>
            </motion.div>
          )}
      </div>
    </div>
  );
};

export default ResearchPage;
