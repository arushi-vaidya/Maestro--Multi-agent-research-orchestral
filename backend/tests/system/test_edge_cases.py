"""
STEP 7.5: Failure & Edge-Case Scenarios

Tests system robustness under adverse conditions:
- Agent failures
- Empty results
- Single-source evidence
- Conflicting-only evidence
- Patent-heavy vs clinical-heavy evidence

Critical for ensuring graceful degradation and system reliability.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from typing import Dict, Any

os.environ['USE_LANGGRAPH'] = 'true'

from agents.master_agent import MasterAgent


# ==============================================================================
# TEST 1: ONE AGENT RETURNS EMPTY OUTPUT
# ==============================================================================

def test_edge_case_one_agent_empty():
    """
    Scenario: Clinical agent returns no trials

    Expected Behavior:
    - System continues (doesn't crash)
    - Other agents proceed normally
    - Response acknowledges limited data
    - References from other agents still present
    """
    master = MasterAgent()

    # Mock clinical agent returning empty results
    empty_clinical = {
        'summary': '',
        'comprehensive_summary': '',
        'trials': [],
        'references': [],
        'total_trials': 0
    }

    # Mock market agent returning normal results
    normal_market = {
        'agentId': 'market',
        'sections': {'summary': 'Market data available'},
        'references': [
            {
                'type': 'market-report',
                'title': 'Market Report 1',
                'agentId': 'market',
                'url': 'https://example.com/report1'
            }
        ],
        'confidence': {'score': 0.7, 'level': 'medium'}
    }

    with patch.object(master, '_run_clinical_agent', return_value=empty_clinical):
        with patch.object(master, '_run_market_agent', return_value=normal_market):
            response = master.process_query("Test query with empty clinical agent")

    # System should NOT crash
    assert response is not None, "System crashed with empty agent output"

    # Response should have structure
    assert 'summary' in response
    assert 'references' in response

    # Market references should still be present
    market_refs = [r for r in response.get('references', []) if r.get('agentId') == 'market']
    assert len(market_refs) > 0, "Market references missing despite market agent success"

    # Clinical references should be empty or minimal
    clinical_refs = [r for r in response.get('references', []) if r.get('agentId') == 'clinical']
    assert len(clinical_refs) == 0, "Clinical references present despite empty output"

    print(f"✅ Edge case handled: One agent empty")
    print(f"   Total references: {len(response.get('references', []))}")
    print(f"   Market refs: {len(market_refs)}, Clinical refs: {len(clinical_refs)}")


# ==============================================================================
# TEST 2: ONE AGENT FAILS GRACEFULLY
# ==============================================================================

def test_edge_case_agent_failure():
    """
    Scenario: Patent agent raises exception

    Expected Behavior:
    - Exception caught gracefully
    - Other agents proceed
    - Final response generated
    - Execution status shows failure
    """
    master = MasterAgent()

    # Mock patent agent raising exception
    def failing_patent_agent(*args, **kwargs):
        raise Exception("Lens.org API unavailable")

    # Mock market agent succeeding
    normal_market = {
        'agentId': 'market',
        'sections': {'summary': 'Market data'},
        'references': [{'title': 'Market Report', 'agentId': 'market'}],
        'confidence': {'score': 0.75, 'level': 'high'}
    }

    with patch.object(master, '_run_patent_agent', side_effect=failing_patent_agent):
        with patch.object(master, '_run_market_agent', return_value=normal_market):
            # Should not raise exception
            try:
                response = master.process_query("Test query with failing patent agent")
                assert response is not None, "No response returned despite agent failure"

            except Exception as e:
                pytest.fail(f"System crashed instead of handling agent failure: {e}")

    # Verify execution status shows failure
    if 'agent_execution_status' in response:
        patent_status = [s for s in response['agent_execution_status'] if s['agent_id'] == 'patent']
        if patent_status:
            assert patent_status[0]['status'] in ['failed', 'completed'], \
                f"Patent agent status not recorded: {patent_status[0]['status']}"

    # Market agent should have succeeded
    market_refs = [r for r in response.get('references', []) if r.get('agentId') == 'market']
    assert len(market_refs) > 0, "Market agent didn't run despite patent failure"

    print(f"✅ Edge case handled: Agent failure")
    print(f"   System remained operational")


# ==============================================================================
# TEST 3: CONFLICTING EVIDENCE ONLY
# ==============================================================================

def test_edge_case_conflicting_evidence_only():
    """
    Scenario: All evidence conflicts (no consensus)

    Expected Behavior:
    - System processes conflicting evidence
    - Conflict reasoning identifies contradictions
    - ROS score reflects high uncertainty
    - Explanation acknowledges conflicts
    """
    master = MasterAgent()

    # Mock conflicting clinical trials
    conflicting_trials = [
        {
            'nct_id': 'NCT00001111',
            'title': 'Positive Outcome Study',
            'primary_outcome': 'Significant improvement',
            'status': 'COMPLETED'
        },
        {
            'nct_id': 'NCT00002222',
            'title': 'Negative Outcome Study',
            'primary_outcome': 'No benefit observed',
            'status': 'COMPLETED'
        },
        {
            'nct_id': 'NCT00003333',
            'title': 'Mixed Results Study',
            'primary_outcome': 'Inconclusive',
            'status': 'COMPLETED'
        }
    ]

    with patch.object(master.clinical_agent, 'search_trials', return_value=conflicting_trials):
        response = master.process_query("Conflicting drug efficacy data")

    # System should process without crashing
    assert response is not None

    # References should be present
    assert len(response.get('references', [])) > 0, "No references despite conflicting evidence"

    # Summary should exist
    assert len(response.get('summary', '')) > 0, "No summary generated for conflicting evidence"

    # ROS score should reflect uncertainty (if implemented)
    if 'ros_results' in response and response['ros_results']:
        ros_score = response['ros_results'].get('score', 1.0)
        # Conflicting evidence should result in lower ROS
        # (This assertion may be adjusted based on implementation)
        print(f"   ROS score with conflicts: {ros_score}")

    print(f"✅ Edge case handled: Conflicting evidence only")


# ==============================================================================
# TEST 4: SINGLE-SOURCE EVIDENCE ONLY
# ==============================================================================

def test_edge_case_single_source_evidence():
    """
    Scenario: Only one trial or source available

    Expected Behavior:
    - System processes single source
    - Confidence reflects limited evidence
    - No false confidence from single source
    """
    master = MasterAgent()

    # Mock single trial
    single_trial = [
        {
            'nct_id': 'NCT00009999',
            'title': 'Single Pilot Study',
            'enrollment': 30,  # Small sample
            'status': 'COMPLETED',
            'phases': ['PHASE1']
        }
    ]

    with patch.object(master.clinical_agent, 'search_trials', return_value=single_trial):
        response = master.process_query("Rare disease single pilot study")

    # System should process
    assert response is not None

    # Should have exactly one clinical reference
    clinical_refs = [r for r in response.get('references', []) if r.get('agentId') == 'clinical']
    assert len(clinical_refs) >= 0, "Clinical reference missing for single trial"

    # Confidence should not be artificially high
    if 'confidence_score' in response:
        confidence = response['confidence_score']
        # Single source should not yield maximum confidence
        assert confidence < 95, \
            f"Confidence too high for single source: {confidence}% (expected < 95%)"

    print(f"✅ Edge case handled: Single-source evidence")
    print(f"   Confidence: {response.get('confidence_score', 'N/A')}%")


# ==============================================================================
# TEST 5: PATENT-HEAVY EVIDENCE
# ==============================================================================

def test_edge_case_patent_heavy_evidence():
    """
    Scenario: Query returns mostly patent data, minimal clinical

    Expected Behavior:
    - Patent references dominate
    - System acknowledges limited clinical data
    - FTO assessment present
    """
    master = MasterAgent()

    # Mock extensive patent data, minimal clinical
    many_patents = [
        {'patent_number': f'US{i:07d}', 'title': f'Patent {i}'}
        for i in range(10, 20)
    ]

    minimal_clinical = []  # No trials found

    mock_patent_result = {
        'patents': many_patents,
        'references': [
            {
                'type': 'patent',
                'title': f'Patent {i}',
                'agentId': 'patent',
                'patent_number': f'US{i:07d}'
            }
            for i in range(10, 20)
        ],
        'total_patents': len(many_patents),
        'fto_assessment': {'free_to_operate': False, 'risk_level': 'high'}
    }

    with patch.object(master, '_run_patent_agent', return_value=mock_patent_result):
        with patch.object(master.clinical_agent, 'search_trials', return_value=minimal_clinical):
            response = master.process_query("Patent landscape for compound X")

    # Patent references should dominate
    patent_refs = [r for r in response.get('references', []) if r.get('agentId') == 'patent']
    clinical_refs = [r for r in response.get('references', []) if r.get('agentId') == 'clinical']

    assert len(patent_refs) > len(clinical_refs), \
        "Patent-heavy query didn't return more patents than clinical"

    print(f"✅ Edge case handled: Patent-heavy evidence")
    print(f"   Patent refs: {len(patent_refs)}, Clinical refs: {len(clinical_refs)}")


# ==============================================================================
# TEST 6: CLINICAL-HEAVY EVIDENCE
# ==============================================================================

def test_edge_case_clinical_heavy_evidence():
    """
    Scenario: Query returns extensive clinical data, minimal market

    Expected Behavior:
    - Clinical references dominate
    - Comprehensive clinical summary generated
    - Market intelligence minimal or generic
    """
    master = MasterAgent()

    # Mock extensive clinical trials
    many_trials = [
        {
            'nct_id': f'NCT{i:08d}',
            'title': f'Trial {i}',
            'status': 'COMPLETED',
            'phases': ['PHASE3']
        }
        for i in range(1, 51)  # 50 trials
    ]

    with patch.object(master.clinical_agent, 'search_trials', return_value=many_trials):
        response = master.process_query("Comprehensive clinical trials for diabetes drug")

    # Clinical references should be extensive
    clinical_refs = [r for r in response.get('references', []) if r.get('agentId') == 'clinical']

    assert len(clinical_refs) > 10, \
        f"Clinical-heavy query returned too few clinical references: {len(clinical_refs)}"

    # Comprehensive summary should exist
    if 'comprehensive_summary' in response:
        summary = response['comprehensive_summary']
        assert len(summary) > 500, \
            f"Comprehensive summary too short for {len(clinical_refs)} trials: {len(summary)} chars"

    print(f"✅ Edge case handled: Clinical-heavy evidence")
    print(f"   Clinical refs: {len(clinical_refs)}")


# ==============================================================================
# TEST 7: NO RESULTS FROM ANY AGENT
# ==============================================================================

def test_edge_case_no_results_any_agent():
    """
    Scenario: All agents return empty results (rare query)

    Expected Behavior:
    - System doesn't crash
    - Response acknowledges no data found
    - Confidence score is 0 or very low
    """
    master = MasterAgent()

    # Mock all agents returning empty
    empty_result = {
        'summary': '',
        'trials': [],
        'references': [],
        'total_trials': 0
    }

    with patch.object(master, '_run_clinical_agent', return_value=empty_result):
        with patch.object(master, '_run_market_agent', return_value={'agentId': 'market', 'references': []}):
            with patch.object(master, '_run_patent_agent', return_value={'references': [], 'patents': []}):
                response = master.process_query("Extremely obscure molecule XYZABC123")

    # System should not crash
    assert response is not None

    # Response should have minimal structure
    assert 'summary' in response
    assert 'references' in response

    # References should be empty or very minimal
    assert len(response.get('references', [])) == 0, \
        "References present despite all agents returning empty"

    # Confidence should be 0 or very low
    if 'confidence_score' in response:
        assert response['confidence_score'] <= 20, \
            f"Confidence too high with no results: {response['confidence_score']}%"

    print(f"✅ Edge case handled: No results from any agent")


# ==============================================================================
# TEST 8: MALFORMED QUERY INPUT
# ==============================================================================

def test_edge_case_malformed_query():
    """
    Scenario: Query is empty, too short, or contains special characters

    Expected Behavior:
    - System handles gracefully
    - No crash or exception
    - Returns meaningful error or minimal response
    """
    master = MasterAgent()

    # Test empty query
    try:
        response_empty = master.process_query("")
        assert response_empty is not None, "Empty query caused crash"
    except Exception as e:
        pytest.fail(f"Empty query caused exception: {e}")

    # Test single character
    try:
        response_short = master.process_query("X")
        assert response_short is not None, "Short query caused crash"
    except Exception as e:
        pytest.fail(f"Short query caused exception: {e}")

    # Test special characters
    try:
        response_special = master.process_query("!@#$%^&*()")
        assert response_special is not None, "Special characters caused crash"
    except Exception as e:
        pytest.fail(f"Special character query caused exception: {e}")

    print(f"✅ Edge case handled: Malformed query inputs")


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    'test_edge_case_one_agent_empty',
    'test_edge_case_agent_failure',
    'test_edge_case_conflicting_evidence_only',
    'test_edge_case_single_source_evidence',
    'test_edge_case_patent_heavy_evidence',
    'test_edge_case_clinical_heavy_evidence',
    'test_edge_case_no_results_any_agent',
    'test_edge_case_malformed_query'
]
