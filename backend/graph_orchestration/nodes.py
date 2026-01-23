"""
LangGraph Node Definitions

Each node is a pure function: GraphState → Partial GraphState Update

Design:
- Nodes MUST NOT have side effects beyond state updates
- Nodes MUST NOT duplicate AKGP ingestion (use shared instance)
- Nodes SHOULD reuse MasterAgent methods where possible
- Nodes MUST be deterministic (same input → same output)

Implementation:
- All nodes receive full GraphState
- All nodes return partial state updates (dict)
- LangGraph merges updates into state automatically
"""

from typing import Dict, Any
from datetime import datetime
import logging

from graph_orchestration.state import GraphState
from agents.master_agent import MasterAgent
from normalization import (
    parse_clinical_evidence,
    parse_patent_evidence,
    parse_market_evidence,
    parse_literature_evidence
)

logger = logging.getLogger(__name__)


# ==============================================================================
# SHARED MASTER AGENT INSTANCE
# ==============================================================================

# Create single MasterAgent instance to avoid duplicate AKGP graphs
# This is CRITICAL: nodes must share same graph_manager to prevent duplicate ingestion
_master_agent_instance = None


def get_master_agent() -> MasterAgent:
    """
    Get shared MasterAgent instance

    CRITICAL: All nodes must use same instance to prevent duplicate AKGP ingestion
    """
    global _master_agent_instance
    if _master_agent_instance is None:
        logger.info("🎼 Initializing shared MasterAgent instance for LangGraph nodes")
        _master_agent_instance = MasterAgent()
    return _master_agent_instance


# ==============================================================================
# NODE 1: QUERY CLASSIFICATION
# ==============================================================================

def classify_query_node(state: GraphState) -> Dict[str, Any]:
    """
    Classify user query to determine which agents to activate

    Reuses MasterAgent._classify_query() for deterministic routing

    Input State:
        - user_query: str

    Output State:
        - active_agents: List[str]
        - execution_metadata: Dict with classification timestamp
    """
    logger.info("🎯 LangGraph Node: classify_query_node")

    user_query = state['user_query']
    master = get_master_agent()

    # Reuse existing classification logic
    active_agents = master._classify_query(user_query)

    logger.info(f"📋 Classification result: {active_agents}")

    return {
        'active_agents': active_agents,
        'execution_metadata': {
            'classification_timestamp': datetime.utcnow().isoformat(),
            'active_agents': active_agents
        }
    }


# ==============================================================================
# NODE 2: CLINICAL AGENT
# ==============================================================================

def clinical_agent_node(state: GraphState) -> Dict[str, Any]:
    """
    Execute Clinical Agent

    Reuses MasterAgent._run_clinical_agent() for consistency

    Input State:
        - user_query: str
        - active_agents: List[str]

    Output State:
        - agent_outputs: {'clinical': Dict}
    """
    logger.info("🏥 LangGraph Node: clinical_agent_node")

    # Check if agent should run
    active_agents = state.get('active_agents', [])
    if 'clinical' not in active_agents:
        logger.info("⏭️ Clinical agent not in active_agents, skipping")
        return {}  # No state update

    user_query = state['user_query']
    master = get_master_agent()

    start_time = datetime.utcnow()

    try:
        # Execute clinical agent (includes trial summary fetching)
        clinical_result = master._run_clinical_agent(user_query)

        trial_count = clinical_result.get('total_trials', 0)
        ref_count = len(clinical_result.get('references', []))
        logger.info(f"✅ Clinical Agent completed: {trial_count} trials, {ref_count} references")

        # Update agent_outputs
        agent_outputs = state.get('agent_outputs', {})
        agent_outputs['clinical'] = clinical_result

        return {'agent_outputs': agent_outputs}

    except Exception as e:
        logger.error(f"❌ Clinical Agent FAILED: {e}", exc_info=True)
        # Return empty result on failure (graceful degradation)
        agent_outputs = state.get('agent_outputs', {})
        agent_outputs['clinical'] = {
            'summary': '',
            'comprehensive_summary': '',
            'trials': [],
            'references': [],
            'total_trials': 0,
            'error': str(e)
        }
        return {'agent_outputs': agent_outputs}


# ==============================================================================
# NODE 3: PATENT AGENT
# ==============================================================================

def patent_agent_node(state: GraphState) -> Dict[str, Any]:
    """
    Execute Patent Agent

    Reuses MasterAgent._run_patent_agent() for consistency

    Input State:
        - user_query: str
        - active_agents: List[str]

    Output State:
        - agent_outputs: {'patent': Dict}
    """
    logger.info("⚖️ LangGraph Node: patent_agent_node")

    # Check if agent should run
    active_agents = state.get('active_agents', [])
    if 'patent' not in active_agents:
        logger.info("⏭️ Patent agent not in active_agents, skipping")
        return {}  # No state update

    user_query = state['user_query']
    master = get_master_agent()

    start_time = datetime.utcnow()

    try:
        # Execute patent agent
        patent_result = master._run_patent_agent(user_query)

        patent_count = len(patent_result.get('references', []))
        logger.info(f"✅ Patent Agent completed: {patent_count} patents")

        # Update agent_outputs
        agent_outputs = state.get('agent_outputs', {})
        agent_outputs['patent'] = patent_result

        return {'agent_outputs': agent_outputs}

    except Exception as e:
        logger.error(f"❌ Patent Agent FAILED: {e}", exc_info=True)
        # Return empty result on failure
        agent_outputs = state.get('agent_outputs', {})
        agent_outputs['patent'] = {
            'summary': '',
            'comprehensive_summary': '',
            'patents': [],
            'references': [],
            'total_patents': 0,
            'error': str(e)
        }
        return {'agent_outputs': agent_outputs}


# ==============================================================================
# NODE 4: MARKET AGENT
# ==============================================================================

def market_agent_node(state: GraphState) -> Dict[str, Any]:
    """
    Execute Market Agent

    Reuses MasterAgent._run_market_agent() for consistency

    Input State:
        - user_query: str
        - active_agents: List[str]

    Output State:
        - agent_outputs: {'market': Dict}
    """
    logger.info("💼 LangGraph Node: market_agent_node")

    # Check if agent should run
    active_agents = state.get('active_agents', [])
    if 'market' not in active_agents:
        logger.info("⏭️ Market agent not in active_agents, skipping")
        return {}  # No state update

    user_query = state['user_query']
    master = get_master_agent()

    start_time = datetime.utcnow()

    try:
        # Execute market agent (top_k_rag=15, top_k_web=80)
        market_result = master._run_market_agent(user_query)

        web_count = len(market_result.get('web_results', []))
        rag_count = len(market_result.get('rag_results', []))
        confidence = market_result.get('confidence', {}).get('score', 0.0)
        logger.info(f"✅ Market Agent completed: {web_count} web sources, {rag_count} RAG docs, confidence {confidence:.2%}")

        # Update agent_outputs
        agent_outputs = state.get('agent_outputs', {})
        agent_outputs['market'] = market_result

        return {'agent_outputs': agent_outputs}

    except Exception as e:
        logger.error(f"❌ Market Agent FAILED: {e}", exc_info=True)
        # Return empty result on failure
        agent_outputs = state.get('agent_outputs', {})
        agent_outputs['market'] = {
            'summary': '',
            'sections': {},
            'web_results': [],
            'rag_results': [],
            'confidence': {'score': 0.0, 'level': 'low'},
            'error': str(e)
        }
        return {'agent_outputs': agent_outputs}


# ==============================================================================
# NODE 5: LITERATURE AGENT
# ==============================================================================

def literature_agent_node(state: GraphState) -> Dict[str, Any]:
    """
    Execute Literature Agent

    Reuses MasterAgent._run_literature_agent() for consistency

    Input State:
        - user_query: str
        - active_agents: List[str]

    Output State:
        - agent_outputs: {'literature': Dict}
    """
    logger.info("📚 LangGraph Node: literature_agent_node")

    # Check if agent should run
    active_agents = state.get('active_agents', [])
    if 'literature' not in active_agents:
        logger.info("⏭️ Literature agent not in active_agents, skipping")
        return {}  # No state update

    user_query = state['user_query']
    master = get_master_agent()

    start_time = datetime.utcnow()

    try:
        # Execute literature agent
        literature_result = master._run_literature_agent(user_query)

        pub_count = len(literature_result.get('references', []))
        logger.info(f"✅ Literature Agent completed: {pub_count} publications")

        # Update agent_outputs
        agent_outputs = state.get('agent_outputs', {})
        agent_outputs['literature'] = literature_result

        return {'agent_outputs': agent_outputs}

    except Exception as e:
        logger.error(f"❌ Literature Agent FAILED: {e}", exc_info=True)
        # Return empty result on failure
        agent_outputs = state.get('agent_outputs', {})
        agent_outputs['literature'] = {
            'summary': '',
            'comprehensive_summary': '',
            'publications': [],
            'references': [],
            'total_publications': 0,
            'error': str(e)
        }
        return {'agent_outputs': agent_outputs}


# ==============================================================================
# NODE 6: JOIN NODE (PHASE 2 - PARALLEL EXECUTION)
# ==============================================================================

def join_agents_node(state: GraphState) -> Dict[str, Any]:
    """
    Join node for parallel agent execution (STEP 7 Phase 2)

    Purpose:
    - Wait for all active agents to complete (implicit in LangGraph)
    - Validate all expected agents have outputs
    - Produce deterministic merged state
    - No actual merging needed (LangGraph already merged agent_outputs)

    This node acts as a synchronization barrier ensuring:
    1. All parallel agents have completed
    2. agent_outputs dict is complete and stable
    3. State is ready for AKGP ingestion

    Input State:
        - active_agents: List[str] (expected agents)
        - agent_outputs: Dict[str, Dict] (merged from parallel execution)

    Output State:
        - execution_metadata: Dict with join completion timestamp

    Note: LangGraph's parallel execution automatically merges agent_outputs
    updates from all branches. This node validates completeness and adds
    a synchronization point before AKGP ingestion.
    """
    logger.info("🔀 LangGraph Node: join_agents_node (Phase 2 Parallel Join)")

    active_agents = state.get('active_agents', [])
    agent_outputs = state.get('agent_outputs', {})

    # Validate all active agents have outputs (even if empty/error)
    expected_agents = set(active_agents)
    actual_agents = set(agent_outputs.keys())

    if expected_agents != actual_agents:
        missing = expected_agents - actual_agents
        extra = actual_agents - expected_agents
        logger.warning(f"⚠️ Agent output mismatch - Missing: {missing}, Extra: {extra}")

    # Sort agent_outputs keys for deterministic iteration order
    # This ensures stable AKGP ingestion order
    sorted_agent_ids = sorted(agent_outputs.keys())

    logger.info(f"✅ Join complete: {len(agent_outputs)} agents → {sorted_agent_ids}")

    # Add join metadata
    execution_metadata = state.get('execution_metadata', {})
    execution_metadata['join_timestamp'] = datetime.utcnow().isoformat()
    execution_metadata['joined_agents'] = sorted_agent_ids

    return {'execution_metadata': execution_metadata}


# ==============================================================================
# NODE 7: AKGP INGESTION
# ==============================================================================

def akgp_ingestion_node(state: GraphState) -> Dict[str, Any]:
    """
    Ingest all agent outputs into AKGP (normalization + graph ingestion)

    This node runs AFTER all agents complete to normalize and ingest evidence

    CRITICAL: Uses shared MasterAgent instance to prevent duplicate ingestion

    Input State:
        - agent_outputs: Dict[str, Dict]

    Output State:
        - akgp_ingestion_summary: Dict[str, Dict]
    """
    logger.info("🔗 LangGraph Node: akgp_ingestion_node")

    agent_outputs = state.get('agent_outputs', {})
    master = get_master_agent()

    ingestion_summary = {}

    # CRITICAL: Sort agent IDs for deterministic ingestion order
    # This ensures same query → same AKGP state regardless of parallel execution order
    sorted_agent_ids = sorted(agent_outputs.keys())

    logger.info(f"📥 AKGP ingestion order: {sorted_agent_ids}")

    # Ingest each agent's output in sorted order
    for agent_id in sorted_agent_ids:
        agent_output = agent_outputs[agent_id]
        if agent_output.get('error'):
            logger.warning(f"⚠️ Skipping AKGP ingestion for {agent_id} (agent failed)")
            continue

        # Map agent_id to parser function
        parser_map = {
            'clinical': parse_clinical_evidence,
            'patent': parse_patent_evidence,
            'market': parse_market_evidence,
            'literature': parse_literature_evidence
        }

        parser_func = parser_map.get(agent_id)
        if not parser_func:
            logger.warning(f"⚠️ No parser function for agent: {agent_id}")
            continue

        try:
            # Reuse MasterAgent._ingest_to_akgp for consistency
            summary = master._ingest_to_akgp(
                agent_output=agent_output,
                agent_id=agent_id,
                parser_func=parser_func
            )
            ingestion_summary[agent_id] = summary
            logger.info(f"✅ AKGP ingestion for {agent_id}: {summary['ingested_evidence']} evidence ingested")

        except Exception as e:
            logger.error(f"❌ AKGP ingestion FAILED for {agent_id}: {e}", exc_info=True)
            ingestion_summary[agent_id] = {
                'agent_id': agent_id,
                'total_evidence': 0,
                'ingested_evidence': 0,
                'rejected_evidence': 0,
                'errors': [str(e)]
            }

    return {'akgp_ingestion_summary': ingestion_summary}


# ==============================================================================
# NODE 8: ROS COMPUTATION
# ==============================================================================

def ros_node(state: GraphState) -> Dict[str, Any]:
    """
    Compute Research Opportunity Score (ROS) if applicable

    Only runs if drug-disease pair can be detected from query

    Input State:
        - user_query: str
        - akgp_ingestion_summary: Dict

    Output State:
        - ros_results: Dict or None
    """
    logger.info("🎯 LangGraph Node: ros_node")

    # TODO: Implement drug-disease pair detection
    # For now, skip ROS computation (will add in future iteration)

    logger.info("⏭️ ROS computation skipped (drug-disease pair detection not implemented)")

    return {'ros_results': None}


# ==============================================================================
# NODE 9: FINALIZE RESPONSE
# ==============================================================================

def finalize_response_node(state: GraphState) -> Dict[str, Any]:
    """
    Finalize response by fusing agent outputs

    Reuses MasterAgent._fuse_results() for consistency

    Input State:
        - user_query: str
        - active_agents: List[str]
        - agent_outputs: Dict
        - akgp_ingestion_summary: Dict
        - ros_results: Dict or None

    Output State:
        - final_response: Dict
    """
    logger.info("🎼 LangGraph Node: finalize_response_node")

    user_query = state['user_query']
    active_agents = state.get('active_agents', [])
    agent_outputs = state.get('agent_outputs', {})
    akgp_ingestion_summary = state.get('akgp_ingestion_summary', {})
    ros_results = state.get('ros_results')

    master = get_master_agent()

    # Build execution_status from agent_outputs
    execution_status = []
    for agent_id in active_agents:
        agent_output = agent_outputs.get(agent_id, {})
        execution_status.append({
            'agent_id': agent_id,
            'status': 'completed' if not agent_output.get('error') else 'failed',
            'started_at': None,  # Not tracked in parallel execution
            'completed_at': datetime.utcnow().isoformat(),
            'result_count': len(agent_output.get('references', [])),
            'akgp_ingestion': akgp_ingestion_summary.get(agent_id, {})
        })

    # Reuse MasterAgent._fuse_results for consistency
    try:
        # Build results dict matching MasterAgent format
        results = {}
        for agent_id, agent_output in agent_outputs.items():
            results[agent_id] = agent_output
            results[f'{agent_id}_akgp_ingestion'] = akgp_ingestion_summary.get(agent_id, {})

        final_response = master._fuse_results(
            query=user_query,
            results=results,
            execution_status=execution_status
        )

        # Add ROS results if available
        if ros_results:
            final_response['ros_results'] = ros_results

        logger.info("✅ Response finalization completed")

        return {'final_response': final_response}

    except Exception as e:
        logger.error(f"❌ Response finalization FAILED: {e}", exc_info=True)
        # Return minimal response on failure
        return {
            'final_response': {
                'summary': 'An error occurred while processing your query.',
                'insights': [],
                'references': [],
                'confidence_score': 0,
                'agent_execution_status': execution_status,
                'error': str(e)
            }
        }


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    'classify_query_node',
    'clinical_agent_node',
    'patent_agent_node',
    'market_agent_node',
    'literature_agent_node',
    'join_agents_node',
    'akgp_ingestion_node',
    'ros_node',
    'finalize_response_node'
]
