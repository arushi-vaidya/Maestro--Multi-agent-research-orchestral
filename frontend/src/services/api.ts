/**
 * MAESTRO API Client
 *
 * Type-safe API client for backend façade endpoints.
 * Uses ONLY the READ-ONLY API façade (no backend modifications).
 */

import axios, { AxiosInstance } from 'axios';
import type {
  QueryRequest,
  QueryResponse,
  ROSViewResponse,
  GraphSummaryResponse,
  EvidenceTimelineResponse,
  ConflictExplanationResponse,
  ExecutionStatusResponse,
} from '../types/api';

// API base URL - configurable via environment variable
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class MaestroAPIClient {
  private client: AxiosInstance;

  constructor(baseURL: string = API_BASE_URL) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
      },
      // Increase timeout to tolerate slower multi-agent runs and external APIs
      timeout: 300000, // 5 minutes
    });
  }

  // ==========================================================================
  // CORE QUERY ENDPOINT
  // ==========================================================================

  /**
   * Submit pharmaceutical research query
   * Triggers full agent orchestration (Clinical, Patent, Market, Literature)
   * @param query The research query
   * @param rosMethod ROS calculation method: 'deterministic' (fast) or 'gemini_honest' (honest assessment)
   */
  async submitQuery(query: string, rosMethod: 'deterministic' | 'gemini_honest' = 'gemini_honest'): Promise<QueryResponse> {
    const response = await this.client.post<QueryResponse>('/query', {
      query,
      ros_method: rosMethod,
    } as QueryRequest);
    return response.data;
  }

  // ==========================================================================
  // API FAÇADE ENDPOINTS (READ-ONLY)
  // ==========================================================================

  /**
   * Get ROS score for last queried drug-disease pair
   * READ-ONLY: Does NOT trigger agents or recompute ROS
   */
  async getROSLatest(queryId?: string): Promise<ROSViewResponse> {
    const response = await this.client.get<ROSViewResponse>('/ros/latest', {
      params: {
        query_id: queryId,
      },
    });
    return response.data;
  }

  /**
   * Get knowledge graph summary for visualization
   * READ-ONLY: Does NOT modify graph
   *
   * @param nodeLimit Maximum nodes to return (default: 100)
   * @param includeEvidence Include evidence nodes (default: false)
   */
  async getGraphSummary(
    nodeLimit: number = 100,
    includeEvidence: boolean = false,
    queryId?: string
  ): Promise<GraphSummaryResponse> {
    const response = await this.client.get<GraphSummaryResponse>('/graph/summary', {
      params: {
        node_limit: nodeLimit,
        include_evidence: includeEvidence,
        query_id: queryId,
      },
    });
    return response.data;
  }

  /**
   * Get evidence timeline (chronologically sorted)
   * READ-ONLY: Does NOT trigger agents
   *
   * @param limit Maximum events to return (default: 100)
   * @param agentFilter Filter by agent (optional)
   * @param qualityFilter Filter by quality (optional)
   */
  async getEvidenceTimeline(
    limit: number = 100,
    agentFilter?: string,
    qualityFilter?: 'LOW' | 'MEDIUM' | 'HIGH',
    queryId?: string
  ): Promise<EvidenceTimelineResponse> {
    const response = await this.client.get<EvidenceTimelineResponse>('/evidence/timeline', {
      params: {
        limit,
        agent_filter: agentFilter,
        quality_filter: qualityFilter,
        query_id: queryId,
      },
    });
    return response.data;
  }

  /**
   * Get conflict explanation for last query
   * READ-ONLY: Does NOT recompute conflicts
   */
  async getConflictExplanation(queryId?: string): Promise<ConflictExplanationResponse> {
    const response = await this.client.get<ConflictExplanationResponse>('/conflicts/explanation', {
      params: {
        query_id: queryId,
      },
    });
    return response.data;
  }

  /**
   * Get execution status for last query
   * READ-ONLY: Does NOT trigger execution
   */
  async getExecutionStatus(queryId?: string): Promise<ExecutionStatusResponse> {
    const response = await this.client.get<ExecutionStatusResponse>('/execution/status', {
      params: {
        query_id: queryId,
      },
    });
    return response.data;
  }
}

// Export singleton instance
export const api = new MaestroAPIClient();

// Export class for testing
export { MaestroAPIClient };
