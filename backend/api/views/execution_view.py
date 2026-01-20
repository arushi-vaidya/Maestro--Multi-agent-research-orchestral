"""
Execution View - Execution Status Façade

Provides frontend-safe access to execution metadata and timing information.

CRITICAL CONSTRAINTS:
- READ-ONLY: Does NOT trigger execution
- Does NOT call agents
- Does NOT modify graph
- ONLY exposes execution metadata from last query

Endpoints:
- GET /api/execution/status: Get execution status and timing for last query
"""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from api.views.cache import get_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/execution", tags=["Execution"])


# ==============================================================================
# RESPONSE MODELS
# ==============================================================================

class AgentExecutionDetail(BaseModel):
    """
    Detailed execution info for a single agent
    """
    agent_id: str
    status: str  # completed, running, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    result_count: Optional[int] = None  # trials, patents, sources
    error: Optional[str] = None


class ExecutionStatusResponse(BaseModel):
    """
    Frontend-safe execution status

    Provides execution metadata, timing, and agent status.
    """
    agents_triggered: List[str]  # List of agent IDs that were executed
    agents_completed: List[str]  # List of agent IDs that completed
    agents_failed: List[str]  # List of agent IDs that failed
    agent_details: List[AgentExecutionDetail]  # Detailed execution info
    ingestion_summary: Dict[str, int]  # AKGP ingestion counts
    execution_time_ms: int  # Total execution time
    query_timestamp: str  # When query was executed
    metadata: Dict[str, Any]  # Additional execution metadata

    class Config:
        json_schema_extra = {
            "example": {
                "agents_triggered": ["clinical", "market", "patent", "literature"],
                "agents_completed": ["clinical", "market", "patent", "literature"],
                "agents_failed": [],
                "agent_details": [
                    {
                        "agent_id": "clinical",
                        "status": "completed",
                        "started_at": "2024-01-19T10:00:00Z",
                        "completed_at": "2024-01-19T10:00:05Z",
                        "duration_ms": 5000,
                        "result_count": 45,
                        "error": None
                    }
                ],
                "ingestion_summary": {
                    "total_evidence": 120,
                    "ingested_evidence": 115,
                    "rejected_evidence": 5
                },
                "execution_time_ms": 12500,
                "query_timestamp": "2024-01-19T10:00:00Z",
                "metadata": {
                    "orchestration_mode": "langgraph_parallel",
                    "graph_nodes_executed": 8
                }
            }
        }


# ==============================================================================
# ENDPOINTS
# ==============================================================================

@router.get("/status", response_model=ExecutionStatusResponse)
def get_execution_status(response: Response):
    """
    Get execution status for last query

    This endpoint:
    - Reads execution metadata from last /api/query execution
    - Provides agent timing and status information
    - Shows AKGP ingestion statistics
    - Does NOT trigger new execution

    Returns:
        ExecutionStatusResponse with execution details

    Raises:
        404: No execution data available (no query executed yet)
        500: Error reading cached results
    """
    try:
        # Prevent caching
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        cache = get_cache()

        # If no execution yet, return an empty-but-valid payload so UI doesn't spam 404s
        if cache.is_empty():
          logger.debug(
              "Execution status requested but cache is empty (no query executed yet)"
          )
          raise HTTPException(
              status_code=404,
              detail={
                  "error": "No execution data available",
                  "message": "No query has been executed yet. Please submit a query via POST /api/query first.",
                  "suggestion": "This is normal on initial page load or before the first query."
              }
          )


        # Get execution metadata from cache
        execution_metadata = cache.get_last_execution_metadata()
        last_response = cache.get_last_response()

        if not execution_metadata and not last_response:
            raise HTTPException(
                status_code=404,
                detail="Execution metadata not available."
            )

        # Extract agent execution status from response
        agent_execution_status = []
        if last_response and 'agent_execution_status' in last_response:
            agent_execution_status = last_response['agent_execution_status']

        # Extract active agents
        active_agents = []
        if last_response and 'active_agents' in last_response:
            active_agents = last_response['active_agents']

        # Build agent details list
        agent_details = []
        agents_completed = []
        agents_failed = []

        for agent_status in agent_execution_status:
            agent_id = agent_status.get('agent_id', 'unknown')
            status = agent_status.get('status', 'unknown')

            # Calculate duration if timestamps available
            duration_ms = None
            started_at = agent_status.get('started_at')
            completed_at = agent_status.get('completed_at')

            if started_at and completed_at:
                try:
                    start = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    duration_ms = int((end - start).total_seconds() * 1000)
                except Exception:
                    pass

            # Track status
            if status == 'completed':
                agents_completed.append(agent_id)
            elif status == 'failed':
                agents_failed.append(agent_id)

            detail = AgentExecutionDetail(
                agent_id=agent_id,
                status=status,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                result_count=agent_status.get('result_count'),
                error=agent_status.get('error')
            )
            agent_details.append(detail)

        # Extract ingestion summary from execution metadata or agent status
        ingestion_summary = {}
        if execution_metadata and 'akgp_ingestion_summary' in execution_metadata:
            akgp_summary = execution_metadata['akgp_ingestion_summary']
            ingestion_summary = {
                "total_evidence": akgp_summary.get('total_evidence', 0),
                "ingested_evidence": akgp_summary.get('ingested_evidence', 0),
                "rejected_evidence": akgp_summary.get('rejected_evidence', 0)
            }
        else:
            # Fallback: aggregate from individual agent AKGP ingestion summaries
            total_evidence = 0
            ingested_evidence = 0
            rejected_evidence = 0
            for agent_status in agent_execution_status:
                if 'akgp_ingestion' in agent_status:
                    total_evidence += agent_status['akgp_ingestion'].get('total_evidence', 0)
                    ingested_evidence += agent_status['akgp_ingestion'].get('ingested_evidence', 0)
                    rejected_evidence += agent_status['akgp_ingestion'].get('rejected_evidence', 0)
            
            if total_evidence > 0:
                ingestion_summary = {
                    "total_evidence": total_evidence,
                    "ingested_evidence": ingested_evidence,
                    "rejected_evidence": rejected_evidence
                }

        # Calculate total execution time
        execution_time_ms = 0
        if agent_details:
            execution_time_ms = sum(d.duration_ms for d in agent_details if d.duration_ms is not None)

        # Get query timestamp
        query_timestamp = cache.get_cache_timestamp()
        if query_timestamp:
            query_timestamp_str = query_timestamp.isoformat()
        else:
            query_timestamp_str = datetime.utcnow().isoformat()

        # Extract additional metadata
        metadata = {}
        if execution_metadata:
            metadata = {
                "orchestration_mode": "langgraph_parallel" if execution_metadata.get('join_timestamp') else "sequential",
                "classification_timestamp": execution_metadata.get('classification_timestamp'),
                "join_timestamp": execution_metadata.get('join_timestamp'),
                "joined_agents": execution_metadata.get('joined_agents', [])
            }

        logger.info(f"✅ Execution status: {len(agents_completed)} completed, {len(agents_failed)} failed")

        return ExecutionStatusResponse(
            agents_triggered=active_agents,
            agents_completed=agents_completed,
            agents_failed=agents_failed,
            agent_details=agent_details,
            ingestion_summary=ingestion_summary,
            execution_time_ms=execution_time_ms,
            query_timestamp=query_timestamp_str,
            metadata=metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving execution status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving execution status: {str(e)}"
        )
