"""
LangGraph Workflow Definition

Defines the graph structure and execution flow for MAESTRO agents.

Design:
- Parallel agent execution where possible
- Conditional routing based on query classification
- Deterministic execution (same input → same output)
- Compatible with legacy MasterAgent outputs

Flow:
1. classify_query_node → Determine active agents
2. Agent nodes (parallel execution for activated agents)
3. akgp_ingestion_node → Normalize and ingest evidence
4. ros_node → Compute ROS (if applicable)
5. finalize_response_node → Fuse results

"""

from typing import Literal
import logging

from langgraph.graph import StateGraph, END
from graph_orchestration.state import GraphState
from graph_orchestration.nodes import (
    classify_query_node,
    clinical_agent_node,
    patent_agent_node,
    market_agent_node,
    literature_agent_node,
    join_agents_node,
    akgp_ingestion_node,
    ros_node,
    finalize_response_node
)

logger = logging.getLogger(__name__)


# ==============================================================================
# CONDITIONAL EXECUTION HELPERS
# ==============================================================================

def should_run_agent(state: GraphState, agent_id: str) -> bool:
    """
    Check if agent should run based on active_agents in state

    Args:
        state: Current graph state
        agent_id: Agent identifier (clinical, patent, market, literature)

    Returns:
        True if agent should execute, False otherwise
    """
    active_agents = state.get('active_agents', [])
    return agent_id in active_agents


# ==============================================================================
# WORKFLOW BUILDER
# ==============================================================================

def create_workflow() -> StateGraph:
    """
    Create LangGraph workflow for MAESTRO orchestration (STEP 7 Phase 2: Parallel)

    Returns:
        Compiled StateGraph ready for execution

    Graph Structure (Phase 2 - Parallel):
        START
        → classify_query
        → [FAN-OUT: parallel execution of active agents]
           ├─→ clinical_agent ──┐
           ├─→ patent_agent ────┤
           ├─→ market_agent ────┤
           └─→ literature_agent ─┤
        → [JOIN: wait for all agents] ←┘
        → akgp_ingestion (single execution after join)
        → ros
        → finalize_response
        → END

    Key Design:
    - True parallel fan-out after classification
    - All active agents run concurrently
    - Deterministic join ensures stable merge order
    - AKGP ingestion happens exactly once after join
    - Output parity with sequential Phase 1 maintained
    """
    logger.info("🎼 Creating LangGraph workflow (Phase 2: Parallel Execution)")

    # Initialize StateGraph
    workflow = StateGraph(GraphState)

    # ==============================================================================
    # ADD NODES
    # ==============================================================================

    # Node 1: Query classification
    workflow.add_node("classify_query", classify_query_node)

    # Nodes 2-5: Agent execution (parallel)
    workflow.add_node("clinical_agent", clinical_agent_node)
    workflow.add_node("patent_agent", patent_agent_node)
    workflow.add_node("market_agent", market_agent_node)
    workflow.add_node("literature_agent", literature_agent_node)

    # Node 6: Join node (synchronization barrier)
    workflow.add_node("join_agents", join_agents_node)

    # Node 7: AKGP ingestion (after join)
    workflow.add_node("akgp_ingestion", akgp_ingestion_node)

    # Node 8: ROS computation
    workflow.add_node("ros", ros_node)

    # Node 9: Finalize response
    workflow.add_node("finalize_response", finalize_response_node)

    # ==============================================================================
    # DEFINE EDGES (PHASE 2: Parallel Fan-Out with Join)
    # ==============================================================================

    # START → classify_query
    workflow.set_entry_point("classify_query")

    # PARALLEL FAN-OUT: classify_query → all agent nodes (unconditional)
    # Agents will check active_agents internally and skip if not needed
    # LangGraph executes these in parallel automatically
    workflow.add_edge("classify_query", "clinical_agent")
    workflow.add_edge("classify_query", "patent_agent")
    workflow.add_edge("classify_query", "market_agent")
    workflow.add_edge("classify_query", "literature_agent")

    # PARALLEL JOIN: All agents → join_agents
    # LangGraph waits for all parallel branches before continuing
    workflow.add_edge("clinical_agent", "join_agents")
    workflow.add_edge("patent_agent", "join_agents")
    workflow.add_edge("market_agent", "join_agents")
    workflow.add_edge("literature_agent", "join_agents")

    # SEQUENTIAL AFTER JOIN: join_agents → akgp_ingestion
    workflow.add_edge("join_agents", "akgp_ingestion")

    # akgp_ingestion → ros
    workflow.add_edge("akgp_ingestion", "ros")

    # ros → finalize_response
    workflow.add_edge("ros", "finalize_response")

    # finalize_response → END
    workflow.add_edge("finalize_response", END)

    # ==============================================================================
    # COMPILE GRAPH
    # ==============================================================================

    compiled_graph = workflow.compile()

    logger.info("✅ LangGraph workflow compiled (Phase 2: Parallel)")

    return compiled_graph


# ==============================================================================
# CONVENIENCE FUNCTION
# ==============================================================================

def execute_query(query: str) -> dict:
    """
    Execute query using LangGraph orchestration

    This is the PRIMARY API for LangGraph-based execution

    Args:
        query: User query string

    Returns:
        Final response dict (compatible with legacy MasterAgent output)
    """
    logger.info(f"🎼 Executing query via LangGraph: {query[:100]}...")

    # Create workflow
    graph = create_workflow()

    # Initialize state
    initial_state = {
        'user_query': query,
        'agent_outputs': {},
        'akgp_ingestion_summary': {},
        'execution_metadata': {}
    }

    # Execute graph
    final_state = graph.invoke(initial_state)

    # Extract final response
    final_response = final_state.get('final_response', {})

    logger.info("✅ LangGraph execution completed")

    return final_response


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = ['create_workflow', 'execute_query']
