"""
LangGraph Orchestration - STEP 7

Parallel, graph-based orchestration of MAESTRO agents.

This module provides:
- Parallel agent execution (replaces sequential MasterAgent)
- Deterministic routing
- Identical outputs to legacy orchestration
- No duplicate AKGP ingestion

Design Philosophy:
- Same brain, better nervous system
- Zero behavior changes (output parity guaranteed)
- Toggle-able (can fall back to legacy)
- Fully tested (output equivalence verified)
"""

from graph_orchestration.state import GraphState
from graph_orchestration.workflow import create_workflow, execute_query
from graph_orchestration.nodes import (
    classify_query_node,
    clinical_agent_node,
    patent_agent_node,
    market_agent_node,
    literature_agent_node,
    akgp_ingestion_node,
    ros_node,
    finalize_response_node
)

__all__ = [
    'GraphState',
    'create_workflow',
    'execute_query',
    'classify_query_node',
    'clinical_agent_node',
    'patent_agent_node',
    'market_agent_node',
    'literature_agent_node',
    'akgp_ingestion_node',
    'ros_node',
    'finalize_response_node'
]

__version__ = '1.0.0-step7'
