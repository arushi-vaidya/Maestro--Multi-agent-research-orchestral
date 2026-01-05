import React, { useState } from 'react';
import { Search, Database, FileText, Activity, TrendingUp, AlertCircle, CheckCircle, Loader, Download, BookOpen, ExternalLink, Calendar, Award, X, Sparkles } from 'lucide-react';
import './App.css';

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

interface AnalysisResults {
  summary: string;
  comprehensive_summary?: string;
  insights: Insight[];
  recommendation: string;
  timelineSaved: string;
  references: Reference[];
}

interface Agent {
  id: string;
  name: string;
  icon: any;
  color: string;
  status: string;
  logs?: string[];
}

interface SavedResearch {
  id: number;
  query: string;
  timestamp: string;
  results: AnalysisResults;
}

type TabType = 'overall' | 'clinical' | 'other';

const App = () => {
  const [query, setQuery] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [activeAgents, setActiveAgents] = useState<string[]>([]);
  const [showKnowledgeBase, setShowKnowledgeBase] = useState<boolean>(false);
  const [showReferences, setShowReferences] = useState<boolean>(false);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [agentLogs, setAgentLogs] = useState<Record<string, string[]>>({});
  const [activeTab, setActiveTab] = useState<TabType>('overall');
  const [showResultsPage, setShowResultsPage] = useState<boolean>(false);

  const agents: Agent[] = [
    { id: 'market', name: 'Market Intelligence Agent', icon: TrendingUp, color: 'blue', status: 'idle' },
    { id: 'clinical', name: 'Clinical Trials Agent', icon: Activity, color: 'green', status: 'idle' },
    { id: 'patent', name: 'Patent & IP Agent', icon: FileText, color: 'purple', status: 'idle' },
    { id: 'trade', name: 'Trade Data Agent', icon: Database, color: 'orange', status: 'idle' }
  ];

  const sampleQueries: string[] = [
    "Analyze GLP-1 agonist market opportunity in diabetes",
    "Freedom to operate analysis for CRISPR gene therapy",
    "Clinical trial landscape for Alzheimer's disease",
    "Import dependency analysis for oncology APIs"
  ];

  // Mock references data with agent assignments
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const generateMockReferences = (): Reference[] => [
    // Market Intelligence Agent References
    {
      type: 'market-report',
      title: 'Global GLP-1 Agonist Market Analysis 2024-2030',
      source: 'IQVIA Market Intelligence',
      date: '2024-02-01',
      url: 'https://www.iqvia.com/insights/market-reports',
      relevance: 95,
      agentId: 'market'
    },
    {
      type: 'market-report',
      title: 'Diabetes Drug Market Size and Forecast',
      source: 'Grand View Research',
      date: '2024-01-15',
      url: 'https://www.grandviewresearch.com',
      relevance: 90,
      agentId: 'market'
    },
    {
      type: 'paper',
      title: 'Economic Impact of GLP-1 Therapies in Healthcare Systems',
      source: 'Health Economics Journal',
      date: '2023-11-20',
      url: 'https://onlinelibrary.wiley.com/journal/health-economics',
      relevance: 85,
      agentId: 'market'
    },

    // Clinical Trials Agent References
    {
      type: 'clinical-trial',
      title: 'Phase III Trial: Semaglutide vs Placebo in T2DM',
      source: 'ClinicalTrials.gov NCT04567890',
      date: '2024-01-10',
      url: 'https://clinicaltrials.gov/ct2/show/NCT04567890',
      relevance: 98,
      agentId: 'clinical'
    },
    {
      type: 'clinical-trial',
      title: 'Long-term Safety Study of GLP-1 Agonists',
      source: 'ClinicalTrials.gov NCT04123456',
      date: '2023-12-05',
      url: 'https://clinicaltrials.gov/ct2/show/NCT04123456',
      relevance: 92,
      agentId: 'clinical'
    },
    {
      type: 'paper',
      title: 'Efficacy of GLP-1 agonists in Type 2 Diabetes: A Meta-Analysis',
      source: 'Nature Medicine',
      date: '2024-03-20',
      url: 'https://www.nature.com/nm/',
      relevance: 96,
      agentId: 'clinical'
    },
    {
      type: 'clinical-trial',
      title: 'Cardiovascular Outcomes Trial - GLP-1 Therapy',
      source: 'ClinicalTrials.gov NCT05234567',
      date: '2024-02-28',
      url: 'https://clinicaltrials.gov/ct2/show/NCT05234567',
      relevance: 89,
      agentId: 'clinical'
    },

    // Patent & IP Agent References
    {
      type: 'patent',
      title: 'Methods for GLP-1 receptor agonist synthesis',
      source: 'US Patent 11,234,567',
      date: '2023-08-15',
      url: 'https://patents.google.com/patent/US11234567',
      relevance: 95,
      agentId: 'patent'
    },
    {
      type: 'patent',
      title: 'Novel formulation of long-acting GLP-1 analogs',
      source: 'EP Patent 3,456,789',
      date: '2023-11-22',
      url: 'https://patents.google.com/patent/EP3456789',
      relevance: 88,
      agentId: 'patent'
    },
    {
      type: 'patent',
      title: 'Oral delivery system for peptide therapeutics',
      source: 'US Patent 10,987,654',
      date: '2023-09-10',
      url: 'https://patents.google.com/patent/US10987654',
      relevance: 82,
      agentId: 'patent'
    },
    {
      type: 'patent',
      title: 'GLP-1/GIP dual agonist compounds',
      source: 'WO Patent 2023/123456',
      date: '2023-12-01',
      url: 'https://patents.google.com/patent/WO2023123456',
      relevance: 91,
      agentId: 'patent'
    },

    // Trade Data Agent References
    {
      type: 'market-report',
      title: 'API Import-Export Analysis: Diabetes Therapeutics',
      source: 'Global Trade Analytics',
      date: '2024-01-20',
      url: 'https://www.trade.gov/data-visualization',
      relevance: 93,
      agentId: 'trade'
    },
    {
      type: 'market-report',
      title: 'China-India Pharmaceutical Supply Chain Report',
      source: 'Trade Data Monitor',
      date: '2023-11-30',
      url: 'https://www.worldbank.org/en/topic/trade',
      relevance: 87,
      agentId: 'trade'
    },
    {
      type: 'paper',
      title: 'Global Supply Chain Resilience in Pharmaceutical Manufacturing',
      source: 'Journal of Supply Chain Management',
      date: '2024-02-15',
      url: 'https://onlinelibrary.wiley.com/journal/supply-chain',
      relevance: 84,
      agentId: 'trade'
    }
  ];

  const simulateAnalysis = async (userQuery: string) => {
    setIsProcessing(true);
    setResults(null);
    setSelectedAgent(null);
    setShowResultsPage(false);
    setActiveTab('overall');
    setAgentLogs({ clinical: [] });

    // Show clinical agent as active (Feature 1 only uses Clinical Agent)
    setActiveAgents(['clinical']);

    // Simulate agent logging
    const addLog = (agentId: string, message: string) => {
      setAgentLogs(prev => ({
        ...prev,
        [agentId]: [...(prev[agentId] || []), `${new Date().toLocaleTimeString()}: ${message}`]
      }));
    };

    addLog('clinical', 'Initializing Clinical Trials Agent...');
    addLog('clinical', 'Extracting medical keywords from query...');

    // Get API URL from environment variable or fallback to localhost
    const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const endpoint = `${apiUrl}/api/query`;
    
    console.log('🚀 Starting analysis...');
    console.log('📍 API Endpoint:', endpoint);
    console.log('🔍 Query:', userQuery);

    try {
      addLog('clinical', 'Connecting to ClinicalTrials.gov API...');
      
      // Call backend API
      console.log('📡 Sending request to backend...');
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: userQuery }),
      });

      console.log('📥 Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`);
      }

      addLog('clinical', 'Retrieving clinical trials data...');
      const data = await response.json();
      console.log('📦 Response data:', data);

      addLog('clinical', `Found ${data.references?.length || 0} clinical trials`);
      addLog('clinical', 'Generating comprehensive analysis with AI...');
      addLog('clinical', 'Analysis complete! Preparing results...');

      // Backend returns the correct format already
      setResults(data);
      setShowResultsPage(true);

      console.log('✅ Analysis complete:', data);

    } catch (error) {
      console.error('❌ Error calling backend:', error);
      addLog('clinical', '❌ Error: Failed to complete analysis');
      alert(
        'Failed to connect to backend.\n\n' +
        'Make sure:\n' +
        '1. Backend is running: python main.py\n' +
        '2. Backend is on: ' + apiUrl + '\n' +
        '3. Check browser console for details\n\n' +
        'Error: ' + error
      );

      // Reset states on error
      setActiveAgents([]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSearch = () => {
    if (query.trim()) {
      setActiveAgents([]);
      setShowReferences(false);
      simulateAnalysis(query);
    }
  };

  const handleSampleQuery = (sampleQuery: string) => {
    setQuery(sampleQuery);
    setActiveAgents([]);
    setShowReferences(false);
    simulateAnalysis(sampleQuery);
  };

  const getSavedResearch = (): SavedResearch[] => {
    const existingKB = localStorage.getItem('maestro_knowledge_base');
    return existingKB ? JSON.parse(existingKB) : [];
  };

  const loadSavedResearch = (research: SavedResearch) => {
    setQuery(research.query);
    setResults(research.results);
    setShowKnowledgeBase(false);
    setActiveAgents(['market', 'clinical', 'patent', 'trade']);
  };

  const deleteSavedResearch = (id: number) => {
    const knowledgeBase = getSavedResearch().filter(item => item.id !== id);
    localStorage.setItem('maestro_knowledge_base', JSON.stringify(knowledgeBase));
    setShowKnowledgeBase(false);
    setTimeout(() => setShowKnowledgeBase(true), 0);
  };

  const getAgentReferences = (agentId: string): Reference[] => {
    if (!results) return [];
    return results.references.filter(ref => ref.agentId === agentId);
  };

  const handleAgentClick = (agentId: string) => {
    if (activeAgents.includes(agentId) && !isProcessing) {
      setSelectedAgent(agentId);
    }
  };

  const getTypeIcon = (type: Reference['type']) => {
    switch (type) {
      case 'patent': return <Award className="w-4 h-4" />;
      case 'paper': return <FileText className="w-4 h-4" />;
      case 'clinical-trial': return <Activity className="w-4 h-4" />;
      case 'market-report': return <TrendingUp className="w-4 h-4" />;
    }
  };

  const getTypeColor = (type: Reference['type']) => {
    switch (type) {
      case 'patent': return 'purple';
      case 'paper': return 'blue';
      case 'clinical-trial': return 'green';
      case 'market-report': return 'orange';
    }
  };

  // Convert NCT IDs in text to clickable links
  const renderTextWithNCTLinks = (text: string) => {
    if (!text) return null;
    
    // Match NCT IDs (e.g., NCT05037669, NCT06321289)
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
                className="text-blue-600 hover:text-blue-800 underline font-medium inline-flex items-center gap-1"
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

  const getTabReferences = (tab: TabType): Reference[] => {
    if (!results) return [];
    
    switch (tab) {
      case 'clinical':
        return results.references.filter(ref => ref.agentId === 'clinical');
      case 'other':
        return results.references.filter(ref => ref.agentId !== 'clinical');
      default:
        return results.references;
    }
  };

  const getTabContent = (tab: TabType): string => {
    if (!results) return '';
    
    switch (tab) {
      case 'clinical':
        return results.comprehensive_summary || results.summary;
      case 'other':
        return 'Other agents data will appear here when implemented.';
      default:
        return results.summary;
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
   ${ref.agentId ? `Agent: ${ref.agentId}` : ''}
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

  const handleExportExcel = () => {
    if (!results) return;

    const csvContent = [
      ['MAESTRO Analysis Report'],
      [''],
      ['Query', query],
      ['Generated', new Date().toLocaleString()],
      ['Time Saved', results.timelineSaved],
      [''],
      ['SUMMARY'],
      [results.summary],
      [''],
      ['INSIGHTS'],
      ['Agent', 'Finding', 'Confidence'],
      ...results.insights.map(insight => [
        insight.agent,
        insight.finding,
        `${insight.confidence}%`
      ]),
      [''],
      ['RECOMMENDATION'],
      [results.recommendation],
      [''],
      ['REFERENCES'],
      ['Agent', 'Type', 'Title', 'Source', 'Date', 'URL', 'Relevance'],
      ...results.references.map(ref => [
        ref.agentId,
        ref.type,
        ref.title,
        ref.source,
        ref.date,
        ref.url,
        `${ref.relevance}%`
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `maestro-analysis-${Date.now()}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleSaveToKnowledgeBase = () => {
    if (!results) return;

    const knowledgeEntry = {
      id: Date.now(),
      query: query,
      timestamp: new Date().toISOString(),
      results: results
    };

    const existingKB = localStorage.getItem('maestro_knowledge_base');
    const knowledgeBase = existingKB ? JSON.parse(existingKB) : [];

    knowledgeBase.push(knowledgeEntry);

    localStorage.setItem('maestro_knowledge_base', JSON.stringify(knowledgeBase));

    alert(`Analysis saved to Knowledge Base!\n\nTotal entries: ${knowledgeBase.length}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-purple-200 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
        <div className="absolute top-40 right-10 w-72 h-72 bg-yellow-200 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-pink-200 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-gray-200 shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <Sparkles className="w-8 h-8 text-indigo-600 animate-pulse" />
                <div className="absolute inset-0 w-8 h-8 bg-indigo-400 rounded-full blur-md opacity-50"></div>
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  MAESTRO
                </h1>
                <p className="text-sm text-gray-600 mt-1">Multi-Agent Ensemble for Strategic Therapeutic Research Orchestration</p>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowKnowledgeBase(!showKnowledgeBase);
                  setShowReferences(false);
                }}
                className="px-4 py-2 bg-gradient-to-r from-purple-500 to-indigo-500 text-white rounded-xl hover:from-purple-600 hover:to-indigo-600 transition-all duration-300 flex items-center gap-2 shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                <Database className="w-4 h-4" />
                Knowledge Base ({getSavedResearch().length})
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 relative z-10">
        {/* Knowledge Base Panel */}
        {showKnowledgeBase && (
          <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-2xl p-8 mb-8 border border-gray-100 animate-fadeIn">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">Saved Research</h2>
              <button
                onClick={() => setShowKnowledgeBase(false)}
                className="text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-100 transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {getSavedResearch().length === 0 ? (
              <div className="text-center py-12 text-gray-500 animate-fadeIn">
                <Database className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No saved research yet. Complete an analysis and save it to build your knowledge base.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {getSavedResearch().map((research, idx) => (
                  <div
                    key={research.id}
                    className="border border-gray-200 rounded-xl p-4 hover:border-purple-300 hover:shadow-lg transition-all duration-300 bg-white/50 backdrop-blur-sm transform hover:scale-[1.02] animate-slideUp"
                    style={{ animationDelay: `${idx * 100}ms` }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900 mb-2">{research.query}</h3>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {new Date(research.timestamp).toLocaleDateString()}
                          </span>
                          <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                            Time Saved: {research.results.timelineSaved}
                          </span>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => loadSavedResearch(research)}
                          className="px-3 py-1 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-lg hover:from-blue-600 hover:to-cyan-600 text-sm transform hover:scale-105 transition-all shadow-md"
                        >
                          Load
                        </button>
                        <button
                          onClick={() => deleteSavedResearch(research.id)}
                          className="px-3 py-1 bg-gradient-to-r from-red-500 to-pink-500 text-white rounded-lg hover:from-red-600 hover:to-pink-600 text-sm transform hover:scale-105 transition-all shadow-md"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Main Content - Search Interface or Results Page */}
        {!showResultsPage ? (
          <>
            {/* Search Interface */}
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8 mb-8 border border-gray-100 animate-fadeIn">
              <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <Search className="w-5 h-5 text-indigo-600" />
                Research Query
              </h2>
          <div className="flex gap-3">
            <div className="flex-1 relative group">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Enter your pharmaceutical research query..."
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all duration-300 bg-white/50 backdrop-blur-sm group-hover:border-gray-300"
                disabled={isProcessing}
              />
              <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl blur opacity-0 group-hover:opacity-20 transition-opacity -z-10"></div>
            </div>
            <button
              onClick={handleSearch}
              disabled={isProcessing || !query.trim()}
              className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed flex items-center gap-2 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105 disabled:transform-none"
            >
              {isProcessing ? <Loader className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
              {isProcessing ? 'Analyzing...' : 'Analyze'}
            </button>
          </div>

          {/* Sample Queries */}
          <div className="mt-4">
            <p className="text-sm text-gray-600 mb-2 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              Try these sample queries:
            </p>
            <div className="flex flex-wrap gap-2">
              {sampleQueries.map((sq, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSampleQuery(sq)}
                  disabled={isProcessing}
                  className="text-xs px-3 py-2 bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700 rounded-full hover:from-indigo-100 hover:to-purple-100 hover:text-indigo-700 disabled:opacity-50 transition-all duration-300 transform hover:scale-105 shadow-sm hover:shadow-md"
                >
                  {sq}
                </button>
              ))}
            </div>
          </div>
        </div>

            {/* Agent Status Panel */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {agents.map((agent, idx) => {
            const Icon = agent.icon;
            const isActive = activeAgents.includes(agent.id);
            const isCompleted = isActive && !isProcessing;
            const agentRefs = getAgentReferences(agent.id);

            const colorClasses = {
              blue: 'from-blue-500 to-cyan-500',
              green: 'from-green-500 to-emerald-500',
              purple: 'from-purple-500 to-pink-500',
              orange: 'from-orange-500 to-amber-500'
            };

            return (
              <div
                key={agent.id}
                onClick={() => handleAgentClick(agent.id)}
                className={`bg-white/90 backdrop-blur-sm rounded-2xl p-6 border-2 transition-all duration-500 transform hover:scale-105 ${isActive
                    ? `border-${agent.color}-400 shadow-2xl ${isCompleted ? 'cursor-pointer animate-bounce-once' : 'animate-pulse-slow'}`
                    : 'border-gray-200 hover:border-gray-300 shadow-md hover:shadow-lg'
                  } animate-slideUp`}
                style={{ animationDelay: `${idx * 100}ms` }}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className={`p-3 rounded-xl ${isActive ? `bg-gradient-to-br ${colorClasses[agent.color as keyof typeof colorClasses]} shadow-lg` : 'bg-gray-100'} transition-all duration-300`}>
                    <Icon className={`w-6 h-6 ${isActive ? 'text-white' : 'text-gray-400'}`} />
                  </div>
                  {isActive && (
                    isProcessing ? (
                      <Loader className="w-5 h-5 text-indigo-600 animate-spin" />
                    ) : (
                      <CheckCircle className="w-5 h-5 text-green-600 animate-checkmark" />
                    )
                  )}
                </div>
                <h3 className="font-semibold text-gray-800 text-sm mb-1">{agent.name}</h3>
                <p className="text-xs text-gray-500">
                  {isActive ? (isProcessing ? 'Processing...' : '✓ Complete') : 'Standby'}
                </p>
                {isCompleted && agentRefs.length > 0 && (
                  <div className="mt-3 px-3 py-1 bg-gradient-to-r from-blue-100 to-cyan-100 text-blue-700 rounded-full text-xs font-medium inline-block animate-fadeIn">
                    {agentRefs.length} references • Click to view
                  </div>
                )}
                
                {/* Agent Logs - Show during processing */}
                {isActive && isProcessing && agentLogs[agent.id]?.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-gray-200">
                    <p className="text-xs font-semibold text-gray-600 mb-2">Activity Log:</p>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {agentLogs[agent.id].slice(-5).map((log, logIdx) => (
                        <div key={logIdx} className="text-xs text-gray-500 animate-fadeIn flex items-start gap-1">
                          <span className="text-green-500">•</span>
                          <span className="flex-1">{log}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Agent-Specific References Modal */}
        {selectedAgent && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fadeIn">
            <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden animate-scaleIn">
              <div className="p-6 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-indigo-50 to-purple-50">
                <div>
                  <h2 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                    {agents.find(a => a.id === selectedAgent)?.name}
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    References & Citations ({getAgentReferences(selectedAgent).length})
                  </p>
                </div>
                <button
                  onClick={() => setSelectedAgent(null)}
                  className="p-2 hover:bg-white rounded-xl transition-all transform hover:scale-110"
                >
                  <X className="w-6 h-6 text-gray-500" />
                </button>
              </div>

              <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
                <div className="space-y-3">
                  {getAgentReferences(selectedAgent).map((ref, idx) => {
                    const color = getTypeColor(ref.type);
                    const colorClasses = {
                      purple: 'from-purple-500 to-pink-500',
                      blue: 'from-blue-500 to-cyan-500',
                      green: 'from-green-500 to-emerald-500',
                      orange: 'from-orange-500 to-amber-500'
                    };

                    return (
                      <div
                        key={idx}
                        className="border border-gray-200 rounded-xl p-4 hover:border-gray-300 hover:shadow-lg transition-all duration-300 bg-white/50 backdrop-blur-sm transform hover:scale-[1.02] animate-slideUp"
                        style={{ animationDelay: `${idx * 50}ms` }}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`p-2 bg-gradient-to-br ${colorClasses[color as keyof typeof colorClasses]} rounded-xl flex-shrink-0 shadow-md`}>
                            <div className="text-white">
                              {getTypeIcon(ref.type)}
                            </div>
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between mb-2 gap-3">
                              <div className="flex-1 min-w-0">
                                <span className={`text-xs font-semibold bg-gradient-to-r ${colorClasses[color as keyof typeof colorClasses]} bg-clip-text text-transparent uppercase tracking-wide`}>
                                  {ref.type?.replace('-', ' ') || 'Reference'}
                                </span>
                                <h4 className="font-semibold text-gray-900 mt-1 break-words">{ref.title}</h4>
                              </div>
                              <div className="text-sm text-gray-500 flex-shrink-0 px-2 py-1 bg-gray-100 rounded-lg">
                                {ref.relevance}% match
                              </div>
                            </div>
                            <p className="text-sm text-gray-600 mb-2 break-words">{ref.source}</p>
                            <div className="flex items-center justify-between gap-3">
                              <span className="text-xs text-gray-500 flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {ref.date}
                              </span>
                              <a
                                href={ref.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent hover:from-blue-700 hover:to-cyan-700 flex items-center gap-1 flex-shrink-0 font-medium"
                              >
                                View Source <ExternalLink className="w-3 h-3" />
                              </a>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}
          </>
        ) : null}

        {/* Results Panel - New Tabbed Interface */}
        {results && showResultsPage && (
          <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-2xl border border-gray-100 animate-fadeIn overflow-hidden">
            {/* Header */}
            <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-indigo-50 to-purple-50">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent flex items-center gap-2">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                    Analysis Results
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">Query: {query}</p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl text-sm font-semibold shadow-lg">
                    ⚡ Time Saved: {results.timelineSaved}
                  </div>
                  <button
                    onClick={() => setShowResultsPage(false)}
                    className="p-2 hover:bg-white rounded-xl transition-all"
                  >
                    <X className="w-5 h-5 text-gray-500" />
                  </button>
                </div>
              </div>
            </div>

            <div className="flex h-[calc(100vh-300px)]">
              {/* Main Content Area */}
              <div className="flex-1 overflow-y-auto p-6">
                {/* Tab Content */}
                <div className="prose max-w-none">
                  <div className="bg-gradient-to-r from-blue-50 to-cyan-50 border-l-4 border-blue-500 p-6 rounded-r-xl mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      {activeTab === 'overall' && 'Overall Summary'}
                      {activeTab === 'clinical' && 'Clinical Trials Analysis'}
                      {activeTab === 'other' && 'Other Agents Summary'}
                    </h3>
                    <div className="text-gray-800 whitespace-pre-wrap leading-relaxed">
                      {renderTextWithNCTLinks(getTabContent(activeTab))}
                    </div>
                  </div>

                  {/* References for Current Tab */}
                  {getTabReferences(activeTab).length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                        <BookOpen className="w-5 h-5 text-indigo-600" />
                        References & Citations ({getTabReferences(activeTab).length})
                      </h3>
                      <div className="space-y-3">
                        {getTabReferences(activeTab).map((ref, idx) => {
                          const color = getTypeColor(ref.type);
                          const colorClasses = {
                            purple: 'from-purple-500 to-pink-500',
                            blue: 'from-blue-500 to-cyan-500',
                            green: 'from-green-500 to-emerald-500',
                            orange: 'from-orange-500 to-amber-500'
                          };

                          return (
                            <div
                              key={idx}
                              className="border border-gray-200 rounded-xl p-4 hover:border-gray-300 hover:shadow-lg transition-all duration-300 bg-white/50 backdrop-blur-sm"
                            >
                              <div className="flex items-start gap-3">
                                <div className={`p-2 bg-gradient-to-br ${colorClasses[color as keyof typeof colorClasses]} rounded-xl flex-shrink-0 shadow-md`}>
                                  <div className="text-white">
                                    {getTypeIcon(ref.type)}
                                  </div>
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-start justify-between mb-2 gap-3">
                                    <div className="flex-1 min-w-0">
                                      <span className={`text-xs font-semibold bg-gradient-to-r ${colorClasses[color as keyof typeof colorClasses]} bg-clip-text text-transparent uppercase tracking-wide`}>
                                        {ref.nct_id ? 'Clinical Trial' : (ref.type?.replace('-', ' ') || 'Reference')}
                                      </span>
                                      <h4 className="font-semibold text-gray-900 mt-1 break-words">{ref.title}</h4>
                                    </div>
                                    {ref.relevance && (
                                      <div className="text-sm text-gray-500 flex-shrink-0 px-2 py-1 bg-gray-100 rounded-lg">
                                        {ref.relevance}% match
                                      </div>
                                    )}
                                  </div>
                                  {ref.nct_id && (
                                    <p className="text-sm text-gray-600 mb-2 font-mono">NCT ID: {ref.nct_id}</p>
                                  )}
                                  {ref.summary && (
                                    <p className="text-sm text-gray-600 mb-2">{ref.summary}</p>
                                  )}
                                  <div className="flex items-center justify-between gap-3 flex-wrap">
                                    {ref.date && (
                                      <span className="text-xs text-gray-500 flex items-center gap-1">
                                        <Calendar className="w-3 h-3" />
                                        {ref.date}
                                      </span>
                                    )}
                                    <a
                                      href={ref.nct_id ? `https://clinicaltrials.gov/study/${ref.nct_id}` : ref.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-sm bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent hover:from-blue-700 hover:to-cyan-700 flex items-center gap-1 flex-shrink-0 font-medium"
                                    >
                                      View Source <ExternalLink className="w-3 h-3" />
                                    </a>
                                  </div>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Right Navigation Panel */}
              <div className="w-80 border-l border-gray-200 bg-gradient-to-b from-gray-50 to-white p-6">
                <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-4">Navigation</h3>
                <div className="space-y-2">
                  <button
                    onClick={() => setActiveTab('overall')}
                    className={`w-full text-left px-4 py-3 rounded-xl transition-all duration-300 flex items-center gap-3 ${
                      activeTab === 'overall'
                        ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg scale-105'
                        : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
                    }`}
                  >
                    <FileText className="w-5 h-5" />
                    <div>
                      <div className="font-semibold">Overall Summary</div>
                      <div className="text-xs opacity-80">Main findings</div>
                    </div>
                  </button>

                  <button
                    onClick={() => setActiveTab('clinical')}
                    className={`w-full text-left px-4 py-3 rounded-xl transition-all duration-300 flex items-center gap-3 ${
                      activeTab === 'clinical'
                        ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg scale-105'
                        : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
                    }`}
                  >
                    <Activity className="w-5 h-5" />
                    <div>
                      <div className="font-semibold">Clinical Trials</div>
                      <div className="text-xs opacity-80">{results.references.filter(r => r.agentId === 'clinical').length} trials</div>
                    </div>
                  </button>

                  <button
                    onClick={() => setActiveTab('other')}
                    className={`w-full text-left px-4 py-3 rounded-xl transition-all duration-300 flex items-center gap-3 ${
                      activeTab === 'other'
                        ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg scale-105'
                        : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
                    }`}
                  >
                    <Database className="w-5 h-5" />
                    <div>
                      <div className="font-semibold">Other Agents</div>
                      <div className="text-xs opacity-80">Additional data</div>
                    </div>
                  </button>
                </div>

                {/* Action Buttons */}
                <div className="mt-8 pt-6 border-t border-gray-200 space-y-3">
                  <button
                    onClick={handleSaveToKnowledgeBase}
                    className="w-full px-4 py-2 bg-gradient-to-r from-purple-500 to-indigo-500 text-white rounded-xl hover:from-purple-600 hover:to-indigo-600 transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
                  >
                    <Database className="w-4 h-4" />
                    Save to KB
                  </button>
                  
                  <button
                    onClick={handleExportPDF}
                    className="w-full px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition-all flex items-center justify-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    Export TXT
                  </button>

                  <button
                    onClick={handleExportExcel}
                    className="w-full px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition-all flex items-center justify-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    Export CSV
                  </button>
                </div>

                {/* Insights Summary */}
                {results.insights.length > 0 && (
                  <div className="mt-6 pt-6 border-t border-gray-200">
                    <h4 className="text-sm font-semibold text-gray-600 mb-3">Key Insights</h4>
                    <div className="space-y-2">
                      {results.insights.slice(0, 3).map((insight, idx) => (
                        <div key={idx} className="bg-white rounded-lg p-3 border border-gray-200">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-600">{insight.agent}</span>
                            <span className="text-xs text-green-600 font-semibold">{insight.confidence}%</span>
                          </div>
                          <p className="text-xs text-gray-700 line-clamp-2">{insight.finding}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* System Stats */}
        {!results && !isProcessing && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fadeIn">
            {[
              { value: '70%', label: 'Faster Research Cycles', color: 'from-blue-500 to-cyan-500' },
              { value: '7+', label: 'Integrated Data Sources', color: 'from-green-500 to-emerald-500' },
              { value: '4', label: 'Specialized AI Agents', color: 'from-purple-500 to-pink-500' }
            ].map((stat, idx) => (
              <div
                key={idx}
                className="bg-white/90 backdrop-blur-sm rounded-2xl p-6 shadow-xl border border-gray-100 transform hover:scale-105 transition-all duration-300 hover:shadow-2xl animate-slideUp"
                style={{ animationDelay: `${idx * 100}ms` }}
              >
                <div className={`text-4xl font-bold bg-gradient-to-r ${stat.color} bg-clip-text text-transparent mb-2`}>
                  {stat.value}
                </div>
                <p className="text-gray-600 text-sm">{stat.label}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;