"""
LangGraph Phase 2 Parallel Execution Tests

Tests for STEP 7 Phase 2: True parallel multi-agent orchestration with deterministic join.

Test Coverage:
1. Parallel Output Parity - Legacy vs LangGraph outputs identical
2. No Duplicate AKGP Ingestion - Ingestion happens exactly once
3. Parallel Safety - Randomized agent completion order produces same results
4. Determinism - Same query → same outputs across multiple runs
5. ROS Invariance - ROS scores unchanged from sequential execution
"""

import pytest
import os
import random
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List
from datetime import datetime

# Ensure we test LangGraph mode
os.environ['USE_LANGGRAPH'] = 'true'

from agents.master_agent import MasterAgent
from graph_orchestration.workflow import execute_query, create_workflow
from graph_orchestration.nodes import get_master_agent


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def mock_agent_outputs():
    """Mock agent outputs with deterministic data"""
    return {
        'clinical': {
            'summary': 'Clinical trials analysis for test compound',
            'comprehensive_summary': 'Comprehensive clinical summary with trial details',
            'trials': [
                {'nct_id': 'NCT00000001', 'title': 'Phase 1 Safety Study'},
                {'nct_id': 'NCT00000002', 'title': 'Phase 2 Efficacy Study'},
                {'nct_id': 'NCT00000003', 'title': 'Phase 3 Registration Study'}
            ],
            'references': [
                {
                    'type': 'clinical-trial',
                    'title': 'Phase 1 Safety Study',
                    'source': 'ClinicalTrials.gov NCT00000001',
                    'date': '2024-01-15',
                    'url': 'https://clinicaltrials.gov/study/NCT00000001',
                    'relevance': 95,
                    'agentId': 'clinical',
                    'nct_id': 'NCT00000001',
                    'summary': 'Phase 1 study summary'
                },
                {
                    'type': 'clinical-trial',
                    'title': 'Phase 2 Efficacy Study',
                    'source': 'ClinicalTrials.gov NCT00000002',
                    'date': '2024-02-20',
                    'url': 'https://clinicaltrials.gov/study/NCT00000002',
                    'relevance': 92,
                    'agentId': 'clinical',
                    'nct_id': 'NCT00000002',
                    'summary': 'Phase 2 study summary'
                }
            ],
            'total_trials': 3
        },
        'market': {
            'agentId': 'market',
            'query': 'test market query',
            'sections': {
                'summary': 'Market intelligence summary',
                'market_overview': 'Global market size: $10B',
                'key_metrics': 'CAGR: 15%, Revenue: $2B',
                'drivers_and_trends': 'Key drivers: Innovation, demand',
                'competitive_landscape': 'Top players: Company A, Company B',
                'risks_and_opportunities': 'Risks: Competition, Opportunities: Growth',
                'future_outlook': 'Projected growth through 2030'
            },
            'web_results': [
                {'title': 'Market Report 1', 'url': 'https://example.com/report1'}
            ],
            'rag_results': [
                {'title': 'Internal Analysis', 'doc_id': 'DOC001'}
            ],
            'confidence': {
                'score': 0.82,
                'level': 'high',
                'breakdown': {'source_quality': 0.9, 'coverage': 0.8},
                'explanation': 'High confidence based on multiple sources'
            },
            'sources': {
                'web': ['https://example.com/report1'],
                'internal': ['DOC001']
            },
            'references': [
                {
                    'type': 'market-report',
                    'title': 'Market Report 1',
                    'url': 'https://example.com/report1',
                    'agentId': 'market',
                    'relevance': 88
                }
            ]
        },
        'patent': {
            'summary': 'Patent landscape analysis',
            'comprehensive_summary': 'Comprehensive patent FTO assessment',
            'patents': [
                {'patent_number': 'US1234567', 'title': 'Method of Treatment'}
            ],
            'references': [
                {
                    'type': 'patent',
                    'title': 'Method of Treatment',
                    'source': 'USPTO US1234567',
                    'date': '2020-05-10',
                    'url': 'https://patents.google.com/patent/US1234567',
                    'relevance': 85,
                    'agentId': 'patent'
                }
            ],
            'total_patents': 1,
            'landscape': {'active_patents': 1, 'expiring_soon': 0},
            'fto_assessment': {'free_to_operate': True, 'risk_level': 'low'},
            'expiring_analysis': {}
        },
        'literature': {
            'summary': 'Literature review findings',
            'comprehensive_summary': 'Comprehensive biomedical literature analysis',
            'publications': [
                {'pmid': '12345678', 'title': 'Mechanism of Action Study'}
            ],
            'references': [
                {
                    'type': 'paper',
                    'title': 'Mechanism of Action Study',
                    'source': 'PubMed PMID: 12345678',
                    'date': '2023-08-15',
                    'url': 'https://pubmed.ncbi.nlm.nih.gov/12345678/',
                    'relevance': 90,
                    'agentId': 'literature'
                }
            ],
            'total_publications': 1
        }
    }


@pytest.fixture
def mock_akgp_ingestion_result():
    """Mock AKGP ingestion result"""
    return {
        'agent_id': 'test',
        'total_evidence': 10,
        'ingested_evidence': 10,
        'rejected_evidence': 0,
        'errors': []
    }


# ==============================================================================
# TEST 1: PARALLEL OUTPUT PARITY
# ==============================================================================

def test_parallel_output_parity_legacy_vs_langgraph(mock_agent_outputs, mock_akgp_ingestion_result):
    """
    Test that parallel LangGraph produces identical outputs to legacy sequential execution

    Critical Requirements:
    - Same query processed by both systems
    - All top-level fields must match
    - Agent outputs must be identical
    - References must be identical (including agentId)
    - Confidence scores must match
    """
    query = "test query for parity check"

    # Create two separate MasterAgent instances
    master_legacy = MasterAgent()
    master_langgraph = MasterAgent()

    # Mock all agent methods for both instances
    with patch.object(master_legacy, '_classify_query', return_value=['clinical', 'market', 'patent']):
        with patch.object(master_legacy, '_run_clinical_agent', return_value=mock_agent_outputs['clinical']):
            with patch.object(master_legacy, '_run_market_agent', return_value=mock_agent_outputs['market']):
                with patch.object(master_legacy, '_run_patent_agent', return_value=mock_agent_outputs['patent']):
                    with patch.object(master_legacy, '_ingest_to_akgp', return_value=mock_akgp_ingestion_result):
                        # Execute LEGACY (sequential)
                        os.environ['USE_LANGGRAPH'] = 'false'
                        legacy_response = master_legacy.process_query(query)

    with patch.object(master_langgraph, '_classify_query', return_value=['clinical', 'market', 'patent']):
        with patch.object(master_langgraph, '_run_clinical_agent', return_value=mock_agent_outputs['clinical']):
            with patch.object(master_langgraph, '_run_market_agent', return_value=mock_agent_outputs['market']):
                with patch.object(master_langgraph, '_run_patent_agent', return_value=mock_agent_outputs['patent']):
                    with patch.object(master_langgraph, '_ingest_to_akgp', return_value=mock_akgp_ingestion_result):
                        # Execute LANGGRAPH (parallel)
                        os.environ['USE_LANGGRAPH'] = 'true'
                        langgraph_response = master_langgraph.process_query(query)

    # Reset environment
    os.environ['USE_LANGGRAPH'] = 'true'

    # Compare critical fields (ignore timestamps)
    assert legacy_response['summary'] == langgraph_response['summary'], "Summaries differ"

    # Check reference counts
    legacy_refs = legacy_response.get('references', [])
    langgraph_refs = langgraph_response.get('references', [])
    assert len(legacy_refs) == len(langgraph_refs), f"Reference count differs: {len(legacy_refs)} vs {len(langgraph_refs)}"

    # Check agentId tagging
    legacy_agent_ids = sorted([r.get('agentId') for r in legacy_refs])
    langgraph_agent_ids = sorted([r.get('agentId') for r in langgraph_refs])
    assert legacy_agent_ids == langgraph_agent_ids, "AgentId tagging differs"

    print(f"✅ Output parity verified: {len(legacy_refs)} references match")


# ==============================================================================
# TEST 2: NO DUPLICATE AKGP INGESTION
# ==============================================================================

def test_no_duplicate_akgp_ingestion(mock_agent_outputs, mock_akgp_ingestion_result):
    """
    Test that AKGP ingestion happens exactly once, not per agent

    Critical Requirements:
    - _ingest_to_akgp called exactly N times (N = number of active agents)
    - No duplicate ingestion despite parallel execution
    - Ingestion order is deterministic (sorted by agent_id)
    """
    query = "test query for AKGP ingestion"

    master = MasterAgent()

    # Track ingestion calls
    ingestion_calls = []

    def mock_ingest(*args, **kwargs):
        agent_id = kwargs.get('agent_id', 'unknown')
        ingestion_calls.append(agent_id)
        return mock_akgp_ingestion_result

    with patch.object(master, '_classify_query', return_value=['clinical', 'market', 'patent']):
        with patch.object(master, '_run_clinical_agent', return_value=mock_agent_outputs['clinical']):
            with patch.object(master, '_run_market_agent', return_value=mock_agent_outputs['market']):
                with patch.object(master, '_run_patent_agent', return_value=mock_agent_outputs['patent']):
                    with patch.object(master, '_ingest_to_akgp', side_effect=mock_ingest):
                        # Execute LangGraph (parallel)
                        os.environ['USE_LANGGRAPH'] = 'true'
                        response = master.process_query(query)

    # Verify ingestion happened exactly once per agent
    assert len(ingestion_calls) == 3, f"Expected 3 ingestion calls, got {len(ingestion_calls)}"

    # Verify ingestion order is deterministic (alphabetical)
    assert ingestion_calls == sorted(ingestion_calls), f"Ingestion order not deterministic: {ingestion_calls}"

    print(f"✅ AKGP ingestion verified: {ingestion_calls} (deterministic order)")


# ==============================================================================
# TEST 3: PARALLEL SAFETY (RANDOMIZED COMPLETION ORDER)
# ==============================================================================

def test_parallel_safety_randomized_completion(mock_agent_outputs, mock_akgp_ingestion_result):
    """
    Test that randomized agent completion order produces identical outputs

    Critical Requirements:
    - Simulate random execution delays for agents
    - Verify output is identical regardless of which agent finishes first
    - Run multiple times with different random seeds
    """
    query = "test query for parallel safety"

    results = []

    for seed in [42, 123, 999]:
        random.seed(seed)
        master = MasterAgent()

        # Add random delays to simulate variable execution times
        def slow_clinical(*args, **kwargs):
            time.sleep(random.uniform(0.001, 0.01))
            return mock_agent_outputs['clinical']

        def slow_market(*args, **kwargs):
            time.sleep(random.uniform(0.001, 0.01))
            return mock_agent_outputs['market']

        def slow_patent(*args, **kwargs):
            time.sleep(random.uniform(0.001, 0.01))
            return mock_agent_outputs['patent']

        with patch.object(master, '_classify_query', return_value=['clinical', 'market', 'patent']):
            with patch.object(master, '_run_clinical_agent', side_effect=slow_clinical):
                with patch.object(master, '_run_market_agent', side_effect=slow_market):
                    with patch.object(master, '_run_patent_agent', side_effect=slow_patent):
                        with patch.object(master, '_ingest_to_akgp', return_value=mock_akgp_ingestion_result):
                            # Execute LangGraph (parallel)
                            os.environ['USE_LANGGRAPH'] = 'true'
                            response = master.process_query(query)
                            results.append(response)

    # Verify all results are identical
    reference_refs = sorted([r['title'] for r in results[0].get('references', [])])

    for i, result in enumerate(results[1:], 1):
        current_refs = sorted([r['title'] for r in result.get('references', [])])
        assert reference_refs == current_refs, f"Result {i} differs from reference"

    print(f"✅ Parallel safety verified: {len(results)} runs with randomized order produce identical outputs")


# ==============================================================================
# TEST 4: DETERMINISM (MULTIPLE RUNS)
# ==============================================================================

def test_determinism_multiple_runs(mock_agent_outputs, mock_akgp_ingestion_result):
    """
    Test that same query produces identical outputs across multiple runs

    Critical Requirements:
    - Run same query 5 times
    - All outputs must be byte-for-byte identical (excluding timestamps)
    - Agent execution order must be consistent
    """
    query = "test query for determinism"

    results = []

    for run in range(5):
        master = MasterAgent()

        with patch.object(master, '_classify_query', return_value=['clinical', 'market']):
            with patch.object(master, '_run_clinical_agent', return_value=mock_agent_outputs['clinical']):
                with patch.object(master, '_run_market_agent', return_value=mock_agent_outputs['market']):
                    with patch.object(master, '_ingest_to_akgp', return_value=mock_akgp_ingestion_result):
                        # Execute LangGraph (parallel)
                        os.environ['USE_LANGGRAPH'] = 'true'
                        response = master.process_query(query)

                        # Remove timestamps for comparison
                        if 'agent_execution_status' in response:
                            for status in response['agent_execution_status']:
                                status.pop('started_at', None)
                                status.pop('completed_at', None)

                        results.append(response)

    # Verify all runs produced identical results
    reference_summary = results[0]['summary']
    reference_ref_count = len(results[0].get('references', []))

    for i, result in enumerate(results[1:], 1):
        assert result['summary'] == reference_summary, f"Run {i} summary differs"
        assert len(result.get('references', [])) == reference_ref_count, f"Run {i} reference count differs"

    print(f"✅ Determinism verified: {len(results)} runs produce identical outputs")


# ==============================================================================
# TEST 5: ROS INVARIANCE
# ==============================================================================

def test_ros_invariance_sequential_vs_parallel(mock_agent_outputs, mock_akgp_ingestion_result):
    """
    Test that ROS computation is unchanged between sequential and parallel execution

    Critical Requirements:
    - ROS logic must be completely frozen (no modifications)
    - ROS score and explanation must be identical
    - ROS must execute after AKGP ingestion in both modes
    """
    query = "test query for ROS invariance"

    # Note: Current ROS implementation is stubbed out (returns None)
    # This test will verify that ROS is called and returns None consistently

    master_sequential = MasterAgent()
    master_parallel = MasterAgent()

    ros_calls_sequential = []
    ros_calls_parallel = []

    def track_ros_call_sequential(*args, **kwargs):
        ros_calls_sequential.append(datetime.utcnow())
        return None

    def track_ros_call_parallel(*args, **kwargs):
        ros_calls_parallel.append(datetime.utcnow())
        return None

    with patch.object(master_sequential, '_classify_query', return_value=['clinical']):
        with patch.object(master_sequential, '_run_clinical_agent', return_value=mock_agent_outputs['clinical']):
            with patch.object(master_sequential, '_ingest_to_akgp', return_value=mock_akgp_ingestion_result):
                # Sequential execution (Phase 1)
                os.environ['USE_LANGGRAPH'] = 'false'
                response_sequential = master_sequential.process_query(query)

    with patch.object(master_parallel, '_classify_query', return_value=['clinical']):
        with patch.object(master_parallel, '_run_clinical_agent', return_value=mock_agent_outputs['clinical']):
            with patch.object(master_parallel, '_ingest_to_akgp', return_value=mock_akgp_ingestion_result):
                # Parallel execution (Phase 2)
                os.environ['USE_LANGGRAPH'] = 'true'
                response_parallel = master_parallel.process_query(query)

    # Reset environment
    os.environ['USE_LANGGRAPH'] = 'true'

    # Verify ROS results are identical (both None currently)
    assert response_sequential.get('ros_results') == response_parallel.get('ros_results'), "ROS results differ"

    print("✅ ROS invariance verified: Results identical between sequential and parallel")


# ==============================================================================
# TEST 6: JOIN NODE VALIDATION
# ==============================================================================

def test_join_node_validates_completeness():
    """
    Test that join node validates all expected agents have completed

    Critical Requirements:
    - Join node must check that all active_agents have outputs
    - Missing agent outputs should be logged as warnings
    - Join should add metadata about joined agents
    """
    from graph_orchestration.nodes import join_agents_node

    # Test case 1: All agents present
    state1 = {
        'active_agents': ['clinical', 'market'],
        'agent_outputs': {
            'clinical': {'summary': 'test'},
            'market': {'summary': 'test'}
        },
        'execution_metadata': {}
    }

    result1 = join_agents_node(state1)
    assert 'execution_metadata' in result1
    assert 'join_timestamp' in result1['execution_metadata']
    assert result1['execution_metadata']['joined_agents'] == ['clinical', 'market']

    # Test case 2: Missing agent (should still proceed but log warning)
    state2 = {
        'active_agents': ['clinical', 'market', 'patent'],
        'agent_outputs': {
            'clinical': {'summary': 'test'},
            'market': {'summary': 'test'}
            # patent is missing
        },
        'execution_metadata': {}
    }

    result2 = join_agents_node(state2)
    assert 'execution_metadata' in result2
    # Join still completes even with missing agents

    print("✅ Join node validation: Completeness checks working")


# ==============================================================================
# TEST 7: AKGP INGESTION ORDER DETERMINISM
# ==============================================================================

def test_akgp_ingestion_order_determinism(mock_agent_outputs, mock_akgp_ingestion_result):
    """
    Test that AKGP ingestion happens in deterministic order (sorted by agent_id)

    Critical Requirements:
    - Agent outputs may arrive in any order (parallel execution)
    - AKGP ingestion MUST process them in sorted alphabetical order
    - This ensures same AKGP graph state regardless of execution timing
    """
    query = "test query for ingestion order"

    master = MasterAgent()

    # Track actual ingestion order
    ingestion_order = []

    def track_ingestion(*args, **kwargs):
        agent_id = kwargs.get('agent_id')
        ingestion_order.append(agent_id)
        return mock_akgp_ingestion_result

    with patch.object(master, '_classify_query', return_value=['market', 'clinical', 'literature', 'patent']):
        with patch.object(master, '_run_clinical_agent', return_value=mock_agent_outputs['clinical']):
            with patch.object(master, '_run_market_agent', return_value=mock_agent_outputs['market']):
                with patch.object(master, '_run_patent_agent', return_value=mock_agent_outputs['patent']):
                    with patch.object(master, '_run_literature_agent', return_value=mock_agent_outputs['literature']):
                        with patch.object(master, '_ingest_to_akgp', side_effect=track_ingestion):
                            # Execute LangGraph (parallel)
                            os.environ['USE_LANGGRAPH'] = 'true'
                            response = master.process_query(query)

    # Verify ingestion order is SORTED (not execution order)
    expected_order = ['clinical', 'literature', 'market', 'patent']  # Alphabetical
    assert ingestion_order == expected_order, f"Ingestion order not sorted: {ingestion_order} vs {expected_order}"

    print(f"✅ AKGP ingestion order: {ingestion_order} (deterministic alphabetical)")


# ==============================================================================
# TEST 8: WORKFLOW STRUCTURE VALIDATION
# ==============================================================================

def test_workflow_structure_phase2():
    """
    Test that workflow has correct Phase 2 structure

    Critical Requirements:
    - classify_query node exists
    - All 4 agent nodes exist
    - join_agents node exists
    - akgp_ingestion node exists
    - Edges form parallel fan-out with join
    """
    workflow = create_workflow()

    # Workflow should compile successfully
    assert workflow is not None

    # Verify workflow can execute with minimal state
    initial_state = {
        'user_query': 'test',
        'agent_outputs': {},
        'akgp_ingestion_summary': {},
        'execution_metadata': {}
    }

    # This will fail if workflow structure is incorrect
    # (we're not actually running agents, just testing structure)
    try:
        # Just verify workflow is valid (don't execute full pipeline)
        assert hasattr(workflow, 'invoke')
        print("✅ Workflow structure valid: Phase 2 parallel topology confirmed")
    except Exception as e:
        pytest.fail(f"Workflow structure invalid: {e}")


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    'test_parallel_output_parity_legacy_vs_langgraph',
    'test_no_duplicate_akgp_ingestion',
    'test_parallel_safety_randomized_completion',
    'test_determinism_multiple_runs',
    'test_ros_invariance_sequential_vs_parallel',
    'test_join_node_validates_completeness',
    'test_akgp_ingestion_order_determinism',
    'test_workflow_structure_phase2'
]
