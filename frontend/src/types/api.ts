/**
 * TypeScript API Types for MAESTRO Backend Façade
 *
 * These types match EXACTLY the backend API response schemas.
 * Source: backend/api/API_FACADE_README.md
 */

// ==============================================================================
// ROS TYPES
// ==============================================================================

export interface ROSViewResponse {
  drug: string;
  disease: string;
  ros_score: number;
  confidence_level: 'LOW' | 'MEDIUM' | 'HIGH';
  breakdown: {
    evidence_strength: number;
    evidence_diversity: number;
    conflict_penalty: number;
    recency_boost: number;
    patent_risk_penalty: number;
  };
  conflict_penalty: number;
  explanation: string;
  metadata: {
    computation_timestamp: string;
    num_supporting_evidence: number;
    num_contradicting_evidence: number;
    num_suggesting_evidence?: number;
    distinct_agents: string[];
    drug_name?: string;
    disease_name?: string;
  };
}

// ==============================================================================
// GRAPH TYPES
// ==============================================================================

export interface GraphNodeView {
  id: string;
  label: string;
  type: 'drug' | 'disease' | 'evidence' | 'trial' | 'patent' | 'market_signal';
  metadata?: Record<string, any>;
}

export interface GraphEdgeView {
  source: string;
  target: string;
  relationship: string;
  weight: number;
  metadata?: Record<string, any>;
}

export interface GraphSummaryResponse {
  nodes: GraphNodeView[];
  edges: GraphEdgeView[];
  statistics: {
    total_nodes: number;
    total_edges: number;
    node_counts: Record<string, number>;
    graph_mode?: string;
    full_graph_stats?: Record<string, any>;
  };
}

// ==============================================================================
// EVIDENCE TIMELINE TYPES
// ==============================================================================

export interface EvidenceTimelineEvent {
  timestamp: string;
  source: string;
  polarity: 'SUPPORTS' | 'SUGGESTS' | 'CONTRADICTS';
  confidence: number;
  quality: 'LOW' | 'MEDIUM' | 'HIGH';
  reference_id: string;
  summary: string;
  agent_id: string;
  recency_weight?: number;
}

export interface EvidenceTimelineResponse {
  events: EvidenceTimelineEvent[];
  total_count: number;
  date_range: {
    earliest: string | null;
    latest: string | null;
  };
  agent_distribution: Record<string, number>;
  polarity_distribution: Record<string, number>;
}

// ==============================================================================
// CONFLICT TYPES
// ==============================================================================

export interface EvidenceSummary {
  evidence_id: string;
  source: string;
  agent_id: string;
  quality: string;
  confidence: number;
  reference: string;
}

export interface ConflictExplanationResponse {
  has_conflict: boolean;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'NONE';
  dominant_evidence_id: string | null;
  explanation: string;
  supporting_evidence: EvidenceSummary[];
  contradicting_evidence: EvidenceSummary[];
  temporal_reasoning: string | null;
  evidence_counts: {
    supports: number;
    contradicts: number;
    suggests: number;
  };
}

// ==============================================================================
// EXECUTION STATUS TYPES
// ==============================================================================

export interface AgentExecutionDetail {
  agent_id: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  result_count: number | null;
  error: string | null;
}

export interface ExecutionStatusResponse {
  agents_triggered: string[];
  agents_completed: string[];
  agents_failed: string[];
  agent_details: AgentExecutionDetail[];
  ingestion_summary: Record<string, number>;
  execution_time_ms: number;
  query_timestamp: string;
  metadata: Record<string, any>;
}

// ==============================================================================
// QUERY REQUEST/RESPONSE TYPES (from existing /api/query)
// ==============================================================================

export interface QueryRequest {
  query: string;
}

export interface QueryResponse {
  summary: string;
  insights: Array<{
    agent: string;
    finding: string;
    confidence: number;
    confidence_level?: string;
    total_trials?: number;
    sources_used?: Record<string, number>;
  }>;
  recommendation: string;
  timelineSaved: string;
  references: Array<{
    type: string;
    title: string;
    source: string;
    date: string;
    url: string;
    relevance: number;
    agentId: string;
  }>;
  confidence_score?: number;
  active_agents?: string[];
  agent_execution_status?: Array<{
    agent_id: string;
    status: string;
    started_at?: string;
    completed_at?: string;
    result_count?: number;
  }>;
  market_intelligence?: any;
  total_trials?: number;
  ros_results?: any;
  execution_metadata?: any;
}
