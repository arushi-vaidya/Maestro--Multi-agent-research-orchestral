"""
ROS Conflict Penalty Tests

Tests for conflict-aware scoring.

Requirements:
- HIGH conflict → larger penalty than MEDIUM
- MEDIUM conflict → larger penalty than LOW
- LOW conflict → larger penalty than NO conflict
- Conflict penalty must come from STEP 5 conflict reasoning
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from ros.ros_engine import ROSEngine
from akgp.graph_manager import GraphManager
from akgp.conflict_reasoning import ConflictReasoner


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def mock_graph_manager():
    """Mock GraphManager"""
    return Mock(spec=GraphManager)


@pytest.fixture
def mock_conflict_reasoner():
    """Mock ConflictReasoner"""
    return Mock(spec=ConflictReasoner)


@pytest.fixture
def base_evidence():
    """Base evidence for conflict tests"""
    return [
        {
            'evidence_id': 'ev1',
            'quality': 'HIGH',
            'confidence_score': 0.9,
            'agent_id': 'clinical',
            'source_type': 'clinical',
            'extraction_timestamp': datetime.utcnow().isoformat()
        }
    ]


# ==============================================================================
# CONFLICT SEVERITY TESTS
# ==============================================================================

def test_high_conflict_penalty_greater_than_medium(
    mock_graph_manager,
    mock_conflict_reasoner,
    base_evidence
):
    """Test HIGH conflict penalty > MEDIUM conflict penalty"""
    # HIGH conflict
    high_conflict_result = {
        'has_conflict': True,
        'severity': 'HIGH',
        'supporting_evidence': base_evidence,
        'contradicting_evidence': base_evidence,
        'evidence_count': {'supports': 1, 'contradicts': 1, 'suggests': 0},
        'provenance_summary': []
    }

    # MEDIUM conflict
    medium_conflict_result = {
        'has_conflict': True,
        'severity': 'MEDIUM',
        'supporting_evidence': base_evidence,
        'contradicting_evidence': base_evidence,
        'evidence_count': {'supports': 1, 'contradicts': 1, 'suggests': 0},
        'provenance_summary': []
    }

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner
    )

    # Test HIGH conflict
    mock_conflict_reasoner.explain_conflict = Mock(return_value=high_conflict_result)
    result_high = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    # Test MEDIUM conflict
    mock_conflict_reasoner.explain_conflict = Mock(return_value=medium_conflict_result)
    result_medium = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    # HIGH conflict should have MORE NEGATIVE penalty
    high_penalty = result_high['feature_breakdown']['conflict_penalty']
    medium_penalty = result_medium['feature_breakdown']['conflict_penalty']

    assert high_penalty < medium_penalty  # More negative
    assert high_penalty < 0  # Should be negative
    assert result_high['ros_score'] < result_medium['ros_score']  # Lower overall score


def test_medium_conflict_penalty_greater_than_low(
    mock_graph_manager,
    mock_conflict_reasoner,
    base_evidence
):
    """Test MEDIUM conflict penalty > LOW conflict penalty"""
    # MEDIUM conflict
    medium_conflict_result = {
        'has_conflict': True,
        'severity': 'MEDIUM',
        'supporting_evidence': base_evidence,
        'contradicting_evidence': base_evidence,
        'evidence_count': {'supports': 1, 'contradicts': 1, 'suggests': 0},
        'provenance_summary': []
    }

    # LOW conflict
    low_conflict_result = {
        'has_conflict': True,
        'severity': 'LOW',
        'supporting_evidence': base_evidence,
        'contradicting_evidence': base_evidence,
        'evidence_count': {'supports': 1, 'contradicts': 1, 'suggests': 0},
        'provenance_summary': []
    }

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner
    )

    # Test MEDIUM conflict
    mock_conflict_reasoner.explain_conflict = Mock(return_value=medium_conflict_result)
    result_medium = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    # Test LOW conflict
    mock_conflict_reasoner.explain_conflict = Mock(return_value=low_conflict_result)
    result_low = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    # MEDIUM conflict should have MORE NEGATIVE penalty
    medium_penalty = result_medium['feature_breakdown']['conflict_penalty']
    low_penalty = result_low['feature_breakdown']['conflict_penalty']

    assert medium_penalty < low_penalty  # More negative
    assert medium_penalty < 0
    assert result_medium['ros_score'] < result_low['ros_score']


def test_low_conflict_penalty_greater_than_no_conflict(
    mock_graph_manager,
    mock_conflict_reasoner,
    base_evidence
):
    """Test LOW conflict penalty > NO conflict (zero penalty)"""
    # LOW conflict
    low_conflict_result = {
        'has_conflict': True,
        'severity': 'LOW',
        'supporting_evidence': base_evidence,
        'contradicting_evidence': base_evidence,
        'evidence_count': {'supports': 1, 'contradicts': 1, 'suggests': 0},
        'provenance_summary': []
    }

    # NO conflict
    no_conflict_result = {
        'has_conflict': False,
        'severity': None,
        'supporting_evidence': base_evidence,
        'contradicting_evidence': [],
        'evidence_count': {'supports': 1, 'contradicts': 0, 'suggests': 0},
        'provenance_summary': []
    }

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner
    )

    # Test LOW conflict
    mock_conflict_reasoner.explain_conflict = Mock(return_value=low_conflict_result)
    result_low = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    # Test NO conflict
    mock_conflict_reasoner.explain_conflict = Mock(return_value=no_conflict_result)
    result_none = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    # LOW conflict should have NEGATIVE penalty, no conflict should have ZERO
    low_penalty = result_low['feature_breakdown']['conflict_penalty']
    none_penalty = result_none['feature_breakdown']['conflict_penalty']

    assert low_penalty < 0
    assert none_penalty == 0.0
    assert result_low['ros_score'] < result_none['ros_score']


def test_no_conflict_yields_zero_penalty(
    mock_graph_manager,
    mock_conflict_reasoner,
    base_evidence
):
    """Test no conflict yields exactly zero penalty"""
    no_conflict_result = {
        'has_conflict': False,
        'severity': None,
        'supporting_evidence': base_evidence,
        'contradicting_evidence': [],
        'evidence_count': {'supports': 1, 'contradicts': 0, 'suggests': 0},
        'provenance_summary': []
    }

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner
    )

    mock_conflict_reasoner.explain_conflict = Mock(return_value=no_conflict_result)
    result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    assert result['feature_breakdown']['conflict_penalty'] == 0.0
    assert result['conflict_summary']['has_conflict'] is False


# ==============================================================================
# CONFLICT SUMMARY TESTS
# ==============================================================================

def test_conflict_summary_reflects_conflict_state(
    mock_graph_manager,
    mock_conflict_reasoner,
    base_evidence
):
    """Test conflict_summary correctly reflects conflict reasoning output"""
    conflict_result = {
        'has_conflict': True,
        'severity': 'HIGH',
        'dominant_evidence': {
            'evidence_id': 'ev1',
            'reason': 'Highest quality',
            'polarity': 'SUPPORTS'
        },
        'supporting_evidence': base_evidence,
        'contradicting_evidence': base_evidence,
        'evidence_count': {'supports': 1, 'contradicts': 1, 'suggests': 0},
        'provenance_summary': []
    }

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner
    )

    mock_conflict_reasoner.explain_conflict = Mock(return_value=conflict_result)
    result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    conflict_summary = result['conflict_summary']

    assert conflict_summary['has_conflict'] is True
    assert conflict_summary['severity'] == 'HIGH'
    assert conflict_summary['dominant_evidence'] == 'SUPPORTS'


def test_conflict_explanation_mentions_severity(
    mock_graph_manager,
    mock_conflict_reasoner,
    base_evidence
):
    """Test explanation mentions conflict severity when conflict exists"""
    conflict_result = {
        'has_conflict': True,
        'severity': 'MEDIUM',
        'supporting_evidence': base_evidence,
        'contradicting_evidence': base_evidence,
        'evidence_count': {'supports': 1, 'contradicts': 1, 'suggests': 0},
        'provenance_summary': []
    }

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner
    )

    mock_conflict_reasoner.explain_conflict = Mock(return_value=conflict_result)
    result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    explanation = result['explanation']

    assert 'MEDIUM' in explanation or 'Medium' in explanation
    assert 'conflict' in explanation.lower()


# ==============================================================================
# MONOTONICITY TESTS (CONFLICT-SPECIFIC)
# ==============================================================================

def test_more_conflicts_lower_score(
    mock_graph_manager,
    mock_conflict_reasoner,
    base_evidence
):
    """Test that conflicts consistently lower the score"""
    # No conflict baseline
    no_conflict = {
        'has_conflict': False,
        'severity': None,
        'supporting_evidence': base_evidence * 3,  # 3 supporting evidence
        'contradicting_evidence': [],
        'evidence_count': {'supports': 3, 'contradicts': 0, 'suggests': 0},
        'provenance_summary': []
    }

    # With conflict
    with_conflict = {
        'has_conflict': True,
        'severity': 'MEDIUM',
        'supporting_evidence': base_evidence * 3,  # Same supporting evidence
        'contradicting_evidence': base_evidence,   # But 1 contradicting
        'evidence_count': {'supports': 3, 'contradicts': 1, 'suggests': 0},
        'provenance_summary': []
    }

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner
    )

    # No conflict
    mock_conflict_reasoner.explain_conflict = Mock(return_value=no_conflict)
    result_no_conflict = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    # With conflict
    mock_conflict_reasoner.explain_conflict = Mock(return_value=with_conflict)
    result_with_conflict = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    # Score should be lower with conflict (monotonicity)
    assert result_with_conflict['ros_score'] < result_no_conflict['ros_score']
