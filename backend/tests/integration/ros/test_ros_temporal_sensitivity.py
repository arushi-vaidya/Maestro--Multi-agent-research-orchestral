"""
ROS Temporal Sensitivity Tests

Tests for recency weighting in ROS.

Requirements:
- Newer evidence → higher recency boost
- Older evidence → lower recency boost
- Uses AKGP temporal decay logic
- Temporal weights must come from TemporalReasoner (STEP 1)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from ros.ros_engine import ROSEngine
from akgp.graph_manager import GraphManager
from akgp.conflict_reasoning import ConflictReasoner
from akgp.temporal import TemporalReasoner


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
def mock_temporal_reasoner():
    """Mock TemporalReasoner with controllable weights"""
    mock = Mock(spec=TemporalReasoner)
    return mock


@pytest.fixture
def recent_evidence():
    """Evidence from last month"""
    return [
        {
            'evidence_id': 'ev_recent',
            'quality': 'HIGH',
            'confidence_score': 0.9,
            'agent_id': 'clinical',
            'source_type': 'clinical',
            'extraction_timestamp': (datetime.utcnow() - timedelta(days=30)).isoformat()
        }
    ]


@pytest.fixture
def old_evidence():
    """Evidence from 5 years ago"""
    return [
        {
            'evidence_id': 'ev_old',
            'quality': 'HIGH',
            'confidence_score': 0.9,
            'agent_id': 'clinical',
            'source_type': 'clinical',
            'extraction_timestamp': (datetime.utcnow() - timedelta(days=1825)).isoformat()
        }
    ]


# ==============================================================================
# RECENCY BOOST TESTS
# ==============================================================================

def test_recent_evidence_higher_boost_than_old(
    mock_graph_manager,
    mock_conflict_reasoner,
    mock_temporal_reasoner,
    recent_evidence,
    old_evidence
):
    """Test recent evidence yields higher recency boost than old evidence"""
    # Mock temporal weights
    # Recent evidence: high weight (0.9)
    # Old evidence: low weight (0.2)

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner,
        temporal_reasoner=mock_temporal_reasoner
    )

    # Test with recent evidence
    recent_conflict_result = {
        'has_conflict': False,
        'severity': None,
        'supporting_evidence': recent_evidence,
        'contradicting_evidence': [],
        'evidence_count': {'supports': 1, 'contradicts': 0, 'suggests': 0},
        'provenance_summary': []
    }

    # High temporal weight for recent evidence
    mock_temporal_reasoner.compute_recency_weight = Mock(return_value=0.9)
    mock_conflict_reasoner.explain_conflict = Mock(return_value=recent_conflict_result)
    result_recent = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    # Test with old evidence
    old_conflict_result = {
        'has_conflict': False,
        'severity': None,
        'supporting_evidence': old_evidence,
        'contradicting_evidence': [],
        'evidence_count': {'supports': 1, 'contradicts': 0, 'suggests': 0},
        'provenance_summary': []
    }

    # Low temporal weight for old evidence
    mock_temporal_reasoner.compute_recency_weight = Mock(return_value=0.2)
    mock_conflict_reasoner.explain_conflict = Mock(return_value=old_conflict_result)
    result_old = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    # Recent evidence should have higher recency boost
    recent_boost = result_recent['feature_breakdown']['recency_boost']
    old_boost = result_old['feature_breakdown']['recency_boost']

    assert recent_boost > old_boost
    assert result_recent['ros_score'] > result_old['ros_score']


def test_recency_boost_bounded(
    mock_graph_manager,
    mock_conflict_reasoner,
    mock_temporal_reasoner,
    recent_evidence
):
    """Test recency boost is bounded to [0, MAX_RECENCY_BOOST]"""
    from ros.scoring_rules import ScoringWeights

    conflict_result = {
        'has_conflict': False,
        'severity': None,
        'supporting_evidence': recent_evidence,
        'contradicting_evidence': [],
        'evidence_count': {'supports': 1, 'contradicts': 0, 'suggests': 0},
        'provenance_summary': []
    }

    # Mock maximum temporal weight
    mock_temporal_reasoner.compute_recency_weight = Mock(return_value=1.0)

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner,
        temporal_reasoner=mock_temporal_reasoner
    )

    mock_conflict_reasoner.explain_conflict = Mock(return_value=conflict_result)
    result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    recency_boost = result['feature_breakdown']['recency_boost']

    # Should not exceed MAX_RECENCY_BOOST
    assert 0.0 <= recency_boost <= ScoringWeights.MAX_RECENCY_BOOST


def test_very_old_evidence_gets_minimum_boost(
    mock_graph_manager,
    mock_conflict_reasoner,
    mock_temporal_reasoner,
    old_evidence
):
    """Test very old evidence gets minimum recency boost (not zero)"""
    conflict_result = {
        'has_conflict': False,
        'severity': None,
        'supporting_evidence': old_evidence,
        'contradicting_evidence': [],
        'evidence_count': {'supports': 1, 'contradicts': 0, 'suggests': 0},
        'provenance_summary': []
    }

    # Mock minimum temporal weight (very old evidence)
    mock_temporal_reasoner.compute_recency_weight = Mock(return_value=0.1)

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner,
        temporal_reasoner=mock_temporal_reasoner
    )

    mock_conflict_reasoner.explain_conflict = Mock(return_value=conflict_result)
    result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    recency_boost = result['feature_breakdown']['recency_boost']

    # Should get some boost (not zero) even for very old evidence
    assert recency_boost > 0.0


def test_no_timestamp_evidence_gets_minimum_boost(
    mock_graph_manager,
    mock_conflict_reasoner,
    mock_temporal_reasoner
):
    """Test evidence without timestamp gets minimum recency boost"""
    # Evidence with no timestamp
    no_timestamp_evidence = [
        {
            'evidence_id': 'ev_no_timestamp',
            'quality': 'HIGH',
            'confidence_score': 0.9,
            'agent_id': 'clinical',
            'source_type': 'clinical',
            # No extraction_timestamp field
        }
    ]

    conflict_result = {
        'has_conflict': False,
        'severity': None,
        'supporting_evidence': no_timestamp_evidence,
        'contradicting_evidence': [],
        'evidence_count': {'supports': 1, 'contradicts': 0, 'suggests': 0},
        'provenance_summary': []
    }

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner,
        temporal_reasoner=mock_temporal_reasoner
    )

    mock_conflict_reasoner.explain_conflict = Mock(return_value=conflict_result)
    result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    recency_boost = result['feature_breakdown']['recency_boost']

    # Should get minimum boost
    assert recency_boost >= 0.0
    assert recency_boost <= 0.5  # Should be low for missing timestamp


# ==============================================================================
# TEMPORAL MONOTONICITY TESTS
# ==============================================================================

def test_temporal_monotonicity(
    mock_graph_manager,
    mock_conflict_reasoner,
    mock_temporal_reasoner
):
    """Test temporal monotonicity: newer → higher score (all else equal)"""
    # Create evidence at different time points
    times = [
        datetime.utcnow() - timedelta(days=30),   # Very recent
        datetime.utcnow() - timedelta(days=365),  # 1 year old
        datetime.utcnow() - timedelta(days=730),  # 2 years old
    ]

    scores = []

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner,
        temporal_reasoner=mock_temporal_reasoner
    )

    for i, time in enumerate(times):
        evidence = [
            {
                'evidence_id': f'ev_{i}',
                'quality': 'HIGH',
                'confidence_score': 0.9,
                'agent_id': 'clinical',
                'source_type': 'clinical',
                'extraction_timestamp': time.isoformat()
            }
        ]

        conflict_result = {
            'has_conflict': False,
            'severity': None,
            'supporting_evidence': evidence,
            'contradicting_evidence': [],
            'evidence_count': {'supports': 1, 'contradicts': 0, 'suggests': 0},
            'provenance_summary': []
        }

        # Mock temporal weight (decreases with age)
        temporal_weight = 1.0 / (i + 1)  # 1.0, 0.5, 0.33
        mock_temporal_reasoner.compute_recency_weight = Mock(return_value=temporal_weight)

        mock_conflict_reasoner.explain_conflict = Mock(return_value=conflict_result)
        result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

        scores.append(result['ros_score'])

    # Scores should be monotonically decreasing (newer → higher)
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1], f"Temporal monotonicity violated: scores[{i}]={scores[i]} < scores[{i+1}]={scores[i+1]}"


# ==============================================================================
# USES AKGP TEMPORAL REASONER TESTS
# ==============================================================================

def test_uses_akgp_temporal_decay_logic(
    mock_graph_manager,
    mock_conflict_reasoner,
    mock_temporal_reasoner,
    recent_evidence
):
    """Test ROS uses AKGP temporal decay logic (half-life based)"""
    conflict_result = {
        'has_conflict': False,
        'severity': None,
        'supporting_evidence': recent_evidence,
        'contradicting_evidence': [],
        'evidence_count': {'supports': 1, 'contradicts': 0, 'suggests': 0},
        'provenance_summary': []
    }

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner,
        temporal_reasoner=mock_temporal_reasoner
    )

    mock_conflict_reasoner.explain_conflict = Mock(return_value=conflict_result)
    result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    # Verify recency boost was calculated (should be > 0 for recent evidence)
    assert result['feature_breakdown']['recency_boost'] > 0.0
    # Verify it uses exponential decay (recent evidence should have high boost)
    assert result['feature_breakdown']['recency_boost'] > 1.0  # Recent evidence should be near max (2.0)
