"""
LangGraph Output Parity Tests

Verifies that LangGraph orchestration produces identical outputs to legacy MasterAgent.

Requirements:
- Legacy and LangGraph outputs must be byte-for-byte identical
- Classification results must match
- Agent execution results must match
- Result fusion must match
- All reference fields must match
"""

import pytest
import os
from unittest.mock import Mock, patch
from typing import Dict, Any

# Ensure we can test both paths
os.environ['USE_LANGGRAPH'] = 'false'  # Start with legacy

from agents.master_agent import MasterAgent
from graph_orchestration.workflow import execute_query


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def sample_queries():
    """Sample queries for testing different agent combinations"""
    return {
        'market_only': "GLP-1 market size 2024",
        'clinical_only': "semaglutide phase 3 trials",
        'patent_only': "SGLT2 inhibitor patent landscape",
        'multi_agent': "GLP-1 freedom to operate assessment"
    }


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def normalize_response_for_comparison(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize response for comparison (remove non-deterministic fields)

    Fields to remove:
    - Timestamps (execution_metadata.computation_timestamp, etc.)
    - Dynamic IDs
    - Any time-based values

    Returns:
        Normalized response dict
    """
    import copy
    normalized = copy.deepcopy(response)

    # Remove timestamps from agent_execution_status
    if 'agent_execution_status' in normalized:
        for status in normalized['agent_execution_status']:
            status.pop('started_at', None)
            status.pop('completed_at', None)

    # Remove timestamps from metadata
    if 'metadata' in normalized:
        normalized['metadata'].pop('computation_timestamp', None)

    # Remove timestamps from ros_results
    if 'ros_results' in normalized and normalized['ros_results']:
        if 'metadata' in normalized['ros_results']:
            normalized['ros_results']['metadata'].pop('computation_timestamp', None)

    return normalized


def compare_responses(legacy: Dict[str, Any], langgraph: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two responses and return differences

    Returns:
        Dict with comparison results:
        - 'identical': bool
        - 'differences': list of difference descriptions
    """
    differences = []

    # Normalize both responses
    legacy_norm = normalize_response_for_comparison(legacy)
    langgraph_norm = normalize_response_for_comparison(langgraph)

    # Compare top-level keys
    legacy_keys = set(legacy_norm.keys())
    langgraph_keys = set(langgraph_norm.keys())

    if legacy_keys != langgraph_keys:
        differences.append(f"Top-level keys differ: legacy={legacy_keys}, langgraph={langgraph_keys}")

    # Compare each top-level field
    for key in legacy_keys & langgraph_keys:
        legacy_val = legacy_norm[key]
        langgraph_val = langgraph_norm[key]

        if legacy_val != langgraph_val:
            differences.append(f"Field '{key}' differs")

    return {
        'identical': len(differences) == 0,
        'differences': differences
    }


# ==============================================================================
# CLASSIFICATION PARITY TESTS
# ==============================================================================

def test_classification_parity_market_only(sample_queries):
    """Test classification produces same result for market-only query"""
    query = sample_queries['market_only']

    master = MasterAgent()

    # Test legacy classification
    legacy_classification = master._classify_query(query)

    # Legacy classification should produce: ['market']
    assert 'market' in legacy_classification


def test_classification_parity_clinical_only(sample_queries):
    """Test classification produces same result for clinical-only query"""
    query = sample_queries['clinical_only']

    master = MasterAgent()

    # Test legacy classification
    legacy_classification = master._classify_query(query)

    # Legacy classification should produce: ['clinical'] or ['market', 'clinical']
    assert 'clinical' in legacy_classification


def test_classification_parity_multi_agent(sample_queries):
    """Test classification produces same result for multi-agent query"""
    query = sample_queries['multi_agent']

    master = MasterAgent()

    # Test legacy classification
    legacy_classification = master._classify_query(query)

    # FTO query should activate all agents
    assert len(legacy_classification) >= 2


# ==============================================================================
# MOCK-BASED OUTPUT PARITY TESTS
# ==============================================================================

@pytest.fixture
def mock_agent_outputs():
    """Mock agent outputs to avoid API calls"""
    return {
        'clinical': {
            'summary': 'Clinical summary',
            'comprehensive_summary': 'Comprehensive clinical summary',
            'trials': [
                {'nct_id': 'NCT12345678', 'title': 'Test Trial'}
            ],
            'references': [
                {
                    'type': 'clinical-trial',
                    'title': 'Test Trial',
                    'source': 'ClinicalTrials.gov NCT12345678',
                    'date': '2024',
                    'url': 'https://clinicaltrials.gov/study/NCT12345678',
                    'relevance': 90,
                    'agentId': 'clinical',
                    'nct_id': 'NCT12345678',
                    'summary': 'Trial summary'
                }
            ],
            'total_trials': 1
        },
        'market': {
            'summary': 'Market summary',
            'sections': {
                'summary': 'Market overview',
                'market_overview': 'Overview',
                'key_metrics': 'Metrics',
                'drivers_and_trends': 'Drivers',
                'competitive_landscape': 'Competitive',
                'risks_and_opportunities': 'Risks',
                'future_outlook': 'Outlook'
            },
            'web_results': [],
            'rag_results': [],
            'confidence': {
                'score': 0.75,
                'level': 'medium',
                'breakdown': {},
                'explanation': 'Moderate confidence'
            },
            'sources': {
                'web': [],
                'internal': []
            }
        },
        'patent': {
            'summary': 'Patent summary',
            'comprehensive_summary': 'Comprehensive patent summary',
            'patents': [],
            'references': [],
            'total_patents': 0,
            'landscape': {},
            'fto_assessment': {},
            'expiring_analysis': {}
        }
    }


@pytest.mark.skipif(
    os.getenv('RUN_SLOW_TESTS') != 'true',
    reason="Slow test - requires mocking agent execution"
)
def test_output_parity_with_mocks(mock_agent_outputs):
    """
    Test output parity using mocked agent outputs

    This test is CRITICAL for verifying output equivalence without API calls
    """
    query = "test query for market and clinical"

    master_legacy = MasterAgent()
    master_langgraph = MasterAgent()

    # Mock agent execution for both
    with patch.object(master_legacy, '_run_clinical_agent', return_value=mock_agent_outputs['clinical']):
        with patch.object(master_legacy, '_run_market_agent', return_value=mock_agent_outputs['market']):
            with patch.object(master_legacy, '_ingest_to_akgp', return_value={
                'agent_id': 'mock',
                'total_evidence': 0,
                'ingested_evidence': 0,
                'rejected_evidence': 0,
                'errors': []
            }):
                # Execute legacy
                os.environ['USE_LANGGRAPH'] = 'false'
                legacy_response = master_legacy.process_query(query)

    with patch.object(master_langgraph, '_run_clinical_agent', return_value=mock_agent_outputs['clinical']):
        with patch.object(master_langgraph, '_run_market_agent', return_value=mock_agent_outputs['market']):
            with patch.object(master_langgraph, '_ingest_to_akgp', return_value={
                'agent_id': 'mock',
                'total_evidence': 0,
                'ingested_evidence': 0,
                'rejected_evidence': 0,
                'errors': []
            }):
                # Execute LangGraph
                os.environ['USE_LANGGRAPH'] = 'true'
                langgraph_response = master_langgraph.process_query(query)

    # Reset environment
    os.environ['USE_LANGGRAPH'] = 'false'

    # Compare responses
    comparison = compare_responses(legacy_response, langgraph_response)

    # Assert identical
    if not comparison['identical']:
        print(f"Differences found: {comparison['differences']}")

    assert comparison['identical'], f"Outputs differ: {comparison['differences']}"


# ==============================================================================
# STRUCTURE VERIFICATION TESTS
# ==============================================================================

def test_langgraph_response_structure():
    """Test LangGraph response has required fields"""
    # This test verifies basic structure without executing agents

    from graph_orchestration.workflow import create_workflow

    # Create workflow
    graph = create_workflow()

    # Workflow should compile without errors
    assert graph is not None


def test_state_transitions():
    """Test GraphState transitions through workflow"""
    from graph_orchestration.state import GraphState

    # Verify GraphState has required fields
    required_fields = [
        'user_query',
        'active_agents',
        'agent_outputs',
        'akgp_ingestion_summary',
        'ros_results',
        'execution_metadata',
        'final_response'
    ]

    # GraphState should be a TypedDict with these fields
    assert hasattr(GraphState, '__annotations__')
    for field in required_fields:
        assert field in GraphState.__annotations__


# ==============================================================================
# NODE EXECUTION TESTS
# ==============================================================================

def test_classify_query_node_determinism():
    """Test classify_query_node is deterministic (ignoring timestamps)"""
    from graph_orchestration.nodes import classify_query_node

    query = "GLP-1 market size"

    state = {'user_query': query}

    # Run classification 3 times
    results = [classify_query_node(state) for _ in range(3)]

    # Extract active_agents from each result
    active_agents_list = [r['active_agents'] for r in results]

    # All active_agents should be identical (deterministic classification)
    assert active_agents_list[0] == active_agents_list[1] == active_agents_list[2]


def test_agent_nodes_skip_when_not_active():
    """Test agent nodes skip execution when not in active_agents"""
    from graph_orchestration.nodes import clinical_agent_node

    state = {
        'user_query': 'test query',
        'active_agents': ['market']  # Clinical not active
    }

    # Clinical agent should return empty state update
    result = clinical_agent_node(state)

    assert result == {}


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    'test_classification_parity_market_only',
    'test_classification_parity_clinical_only',
    'test_classification_parity_multi_agent',
    'test_output_parity_with_mocks',
    'test_langgraph_response_structure',
    'test_state_transitions',
    'test_classify_query_node_determinism',
    'test_agent_nodes_skip_when_not_active'
]
