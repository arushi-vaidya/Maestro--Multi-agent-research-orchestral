"""
STEP 7.5: Cross-Run Determinism Validation

Verifies that the MAESTRO system produces identical outputs across multiple runs
of the same query, ensuring reproducibility for scientific validation.

Requirements:
- Same query run ≥5 times
- Identical ROS scores
- Identical dominant evidence
- Identical conflict severity
- Identical explanation text (excluding timestamps)

This is CRITICAL for:
- Scientific reproducibility
- Journal publication requirements
- System

 reliability validation
"""

import pytest
import os
from unittest.mock import patch
from typing import Dict, Any, List
import copy

os.environ['USE_LANGGRAPH'] = 'true'

from agents.master_agent import MasterAgent


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def normalize_for_determinism(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove non-deterministic fields for comparison

    Fields to remove:
    - Timestamps (started_at, completed_at, computation_timestamp)
    - Dynamic IDs (if any)
    - Non-deterministic random values
    """
    normalized = copy.deepcopy(response)

    # Remove timestamps from agent_execution_status
    if 'agent_execution_status' in normalized:
        for status in normalized['agent_execution_status']:
            status.pop('started_at', None)
            status.pop('completed_at', None)

    # Remove timestamps from execution_metadata
    if 'execution_metadata' in normalized:
        normalized['execution_metadata'].pop('computation_timestamp', None)
        if 'classification_timestamp' in normalized.get('execution_metadata', {}):
            normalized['execution_metadata'].pop('classification_timestamp', None)
        if 'join_timestamp' in normalized.get('execution_metadata', {}):
            normalized['execution_metadata'].pop('join_timestamp', None)

    # Remove timestamps from ROS results
    if 'ros_results' in normalized and normalized['ros_results']:
        if 'metadata' in normalized['ros_results']:
            normalized['ros_results']['metadata'].pop('computation_timestamp', None)

    return normalized


def compare_responses(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compare multiple responses for determinism

    Returns:
        Dict with:
        - 'deterministic': bool
        - 'differences': List of difference descriptions
        - 'common_fields': Dict of fields that were identical
    """
    if len(responses) < 2:
        return {'deterministic': True, 'differences': [], 'common_fields': {}}

    # Normalize all responses
    normalized = [normalize_for_determinism(r) for r in responses]

    # Compare first response against all others
    reference = normalized[0]
    differences = []

    for i, response in enumerate(normalized[1:], 1):
        # Compare top-level keys
        ref_keys = set(reference.keys())
        resp_keys = set(response.keys())

        if ref_keys != resp_keys:
            differences.append(f"Run {i}: Top-level keys differ")

        # Compare each field
        for key in ref_keys & resp_keys:
            if reference[key] != response[key]:
                differences.append(f"Run {i}: Field '{key}' differs")

    return {
        'deterministic': len(differences) == 0,
        'differences': differences,
        'common_fields': {k: v for k, v in reference.items() if k not in ['agent_execution_status', 'execution_metadata']}
    }


# ==============================================================================
# TEST 1: DETERMINISM - SAME QUERY 5 TIMES
# ==============================================================================

def test_determinism_same_query_5_runs():
    """
    Run same query 5 times and verify identical outputs

    Critical Assertions:
    - Summaries identical
    - Reference counts identical
    - Reference titles identical
    - Confidence scores identical
    - AgentId tagging identical
    - Active agents identical
    """
    query = "GLP-1 agonists for type 2 diabetes - clinical trials and market analysis"

    # Mock data for consistency across runs
    mock_trials = [
        {
            'nct_id': 'NCT12345678',
            'title': 'Semaglutide Efficacy Study',
            'status': 'COMPLETED',
            'phases': ['PHASE3'],
            'enrollment': 1200
        }
    ]

    responses = []

    for run in range(5):
        master = MasterAgent()

        with patch.object(master.clinical_agent, 'search_trials', return_value=mock_trials):
            response = master.process_query(query)
            responses.append(response)

    # ========================================
    # ASSERTION 1: All Runs Complete
    # ========================================
    assert len(responses) == 5, f"Expected 5 responses, got {len(responses)}"

    # ========================================
    # ASSERTION 2: Summaries Identical
    # ========================================
    summaries = [r.get('summary', '') for r in responses]
    reference_summary = summaries[0]

    for i, summary in enumerate(summaries[1:], 1):
        assert summary == reference_summary, \
            f"Run {i} summary differs from reference:\nRef: {reference_summary[:100]}...\nRun: {summary[:100]}..."

    # ========================================
    # ASSERTION 3: Reference Counts Identical
    # ========================================
    ref_counts = [len(r.get('references', [])) for r in responses]
    reference_count = ref_counts[0]

    for i, count in enumerate(ref_counts[1:], 1):
        assert count == reference_count, \
            f"Run {i} reference count differs: {count} vs {reference_count}"

    # ========================================
    # ASSERTION 4: Reference Titles Identical (Order-Independent)
    # ========================================
    ref_titles_sets = [
        set(ref.get('title', 'NO_TITLE') for ref in r.get('references', []))
        for r in responses
    ]
    reference_titles = ref_titles_sets[0]

    for i, titles in enumerate(ref_titles_sets[1:], 1):
        assert titles == reference_titles, \
            f"Run {i} reference titles differ"

    # ========================================
    # ASSERTION 5: Confidence Scores Identical
    # ========================================
    confidences = [r.get('confidence_score', 0) for r in responses]
    reference_confidence = confidences[0]

    for i, confidence in enumerate(confidences[1:], 1):
        assert confidence == reference_confidence, \
            f"Run {i} confidence differs: {confidence} vs {reference_confidence}"

    # ========================================
    # ASSERTION 6: Active Agents Identical
    # ========================================
    active_agents_list = [sorted(r.get('active_agents', [])) for r in responses]
    reference_agents = active_agents_list[0]

    for i, agents in enumerate(active_agents_list[1:], 1):
        assert agents == reference_agents, \
            f"Run {i} active agents differ: {agents} vs {reference_agents}"

    # ========================================
    # ASSERTION 7: AgentId Tagging Consistent
    # ========================================
    for i, response in enumerate(responses):
        references = response.get('references', [])
        for ref in references:
            assert 'agentId' in ref, f"Run {i}: Reference missing agentId: {ref.get('title', 'NO_TITLE')}"

    # ========================================
    # COMPREHENSIVE COMPARISON
    # ========================================
    comparison = compare_responses(responses)

    if not comparison['deterministic']:
        print(f"❌ Determinism violated:")
        for diff in comparison['differences']:
            print(f"   - {diff}")

    assert comparison['deterministic'], \
        f"System not deterministic: {comparison['differences']}"

    print(f"✅ Determinism verified: 5 runs produced identical outputs")
    print(f"   Summary length: {len(reference_summary)} chars")
    print(f"   References: {reference_count}")
    print(f"   Confidence: {reference_confidence}%")
    print(f"   Active agents: {reference_agents}")


# ==============================================================================
# TEST 2: DETERMINISM - ROS SCORE STABILITY
# ==============================================================================

def test_determinism_ros_score_stability():
    """
    Verify ROS scores are identical across multiple runs

    Note: Current implementation may return None (ROS not fully implemented)
    This test verifies consistency of behavior
    """
    query = "Semaglutide for cardiovascular outcomes"

    ros_results_list = []

    for run in range(5):
        master = MasterAgent()

        mock_trials = [{'nct_id': 'NCT01234567', 'title': 'CV Outcomes Trial'}]

        with patch.object(master.clinical_agent, 'search_trials', return_value=mock_trials):
            response = master.process_query(query)
            ros_results_list.append(response.get('ros_results'))

    # All ROS results should be identical
    reference_ros = ros_results_list[0]

    for i, ros_result in enumerate(ros_results_list[1:], 1):
        assert ros_result == reference_ros, \
            f"Run {i} ROS result differs from reference"

    print(f"✅ ROS determinism verified: 5 runs produced identical ROS results")
    print(f"   ROS result: {reference_ros}")


# ==============================================================================
# TEST 3: DETERMINISM - PARALLEL VS SEQUENTIAL PARITY
# ==============================================================================

def test_determinism_parallel_vs_sequential_parity():
    """
    Verify parallel LangGraph produces identical results to sequential legacy

    This tests output parity at the system level (not just unit level)
    """
    query = "Clinical trials for metformin in oncology"

    mock_trials = [
        {
            'nct_id': 'NCT98765432',
            'title': 'Metformin Breast Cancer Trial',
            'status': 'ACTIVE',
            'phases': ['PHASE2']
        }
    ]

    # Run with LangGraph (parallel)
    master_parallel = MasterAgent()
    os.environ['USE_LANGGRAPH'] = 'true'

    with patch.object(master_parallel.clinical_agent, 'search_trials', return_value=mock_trials):
        response_parallel = master_parallel.process_query(query)

    # Run with legacy (sequential)
    master_sequential = MasterAgent()
    os.environ['USE_LANGGRAPH'] = 'false'

    with patch.object(master_sequential.clinical_agent, 'search_trials', return_value=mock_trials):
        response_sequential = master_sequential.process_query(query)

    # Reset to parallel mode
    os.environ['USE_LANGGRAPH'] = 'true'

    # Normalize both responses
    normalized_parallel = normalize_for_determinism(response_parallel)
    normalized_sequential = normalize_for_determinism(response_sequential)

    # Compare key fields
    assert normalized_parallel.get('summary') == normalized_sequential.get('summary'), \
        "Parallel vs sequential: summaries differ"

    parallel_ref_count = len(normalized_parallel.get('references', []))
    sequential_ref_count = len(normalized_sequential.get('references', []))
    assert parallel_ref_count == sequential_ref_count, \
        f"Parallel vs sequential: reference counts differ ({parallel_ref_count} vs {sequential_ref_count})"

    print(f"✅ Parallel-sequential parity verified")
    print(f"   References: {parallel_ref_count}")


# ==============================================================================
# TEST 4: DETERMINISM - AGENT CLASSIFICATION
# ==============================================================================

def test_determinism_agent_classification():
    """
    Verify query classification is deterministic

    Same query should always produce same active_agents list
    """
    queries_and_expected = [
        ("GLP-1 market size", ['market']),  # Market-only query
        ("semaglutide phase 3 trials", ['clinical', 'market']),  # Clinical query (may include market)
        ("patent landscape for SGLT2 inhibitors", ['patent', 'market']),  # Patent query
    ]

    for query, expected_agents in queries_and_expected:
        classifications = []

        for run in range(5):
            master = MasterAgent()
            classification = master._classify_query(query)
            classifications.append(sorted(classification))

        # All classifications should be identical
        reference = classifications[0]

        for i, classification in enumerate(classifications[1:], 1):
            assert classification == reference, \
                f"Query '{query}' classification inconsistent at run {i}: {classification} vs {reference}"

        # Verify expected agents are present
        for expected_agent in expected_agents:
            assert expected_agent in reference, \
                f"Query '{query}' missing expected agent '{expected_agent}': got {reference}"

        print(f"✅ Classification deterministic for: {query}")
        print(f"   Result: {reference}")


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    'test_determinism_same_query_5_runs',
    'test_determinism_ros_score_stability',
    'test_determinism_parallel_vs_sequential_parity',
    'test_determinism_agent_classification'
]
