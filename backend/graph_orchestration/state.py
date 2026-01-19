"""
Graph State Definition for LangGraph Orchestration

Pure data structure with no logic.

Design:
- TypedDict for compile-time type safety
- All fields optional to allow progressive state building
- Immutable updates (state merging)
- No methods or logic (pure data)
"""

from typing import TypedDict, List, Dict, Any, Optional


class GraphState(TypedDict, total=False):
    """
    State object for LangGraph orchestration workflow

    All fields are optional to allow progressive state building.
    LangGraph merges updates into state automatically.

    Fields:
        user_query: Original user query string
        active_agents: List of agent IDs to execute (from classification)
        agent_outputs: Dict mapping agent_id -> raw agent output
        akgp_ingestion_summary: Dict mapping agent_id -> AKGP ingestion result
        ros_results: ROS computation results (if applicable)
        execution_metadata: Execution tracking data
        final_response: Complete response to return to user
    """

    # Input
    user_query: str

    # Classification result
    active_agents: List[str]

    # Agent execution results
    agent_outputs: Dict[str, Dict[str, Any]]

    # AKGP ingestion results (after normalization)
    akgp_ingestion_summary: Dict[str, Dict[str, Any]]

    # ROS results (if drug-disease pair detected)
    ros_results: Optional[Dict[str, Any]]

    # Execution tracking
    execution_metadata: Dict[str, Any]

    # Final assembled response
    final_response: Dict[str, Any]


# Type aliases for clarity
AgentID = str  # 'clinical', 'patent', 'market', 'literature'
AgentOutput = Dict[str, Any]
IngestionSummary = Dict[str, Any]
ROSResult = Dict[str, Any]
ExecutionMetadata = Dict[str, Any]


__all__ = ['GraphState', 'AgentID', 'AgentOutput', 'IngestionSummary', 'ROSResult', 'ExecutionMetadata']
