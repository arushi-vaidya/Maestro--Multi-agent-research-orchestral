"""
ROS Basic Scoring Tests

Tests for core ROS scoring functionality.

Requirements:
- ROS must compute scores in [0, 10] range
- ROS must use ONLY AKGP data (not raw agents)
- ROS must be deterministic
- ROS must provide feature breakdown
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from ros.ros_engine import ROSEngine, compute_ros
from akgp.graph_manager import GraphManager
from akgp.conflict_reasoning import ConflictReasoner
from akgp.temporal import TemporalReasoner


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def mock_graph_manager():
    """Mock GraphManager for testing"""
    mock = Mock(spec=GraphManager)
    return mock


@pytest.fixture
def mock_conflict_reasoner():
    """Mock ConflictReasoner for testing"""
    mock = Mock(spec=ConflictReasoner)
    return mock


@pytest.fixture
def mock_temporal_reasoner():
    """Mock TemporalReasoner for testing"""
    mock = Mock(spec=TemporalReasoner)
    # Default temporal weight
    mock.compute_recency_weight = Mock(return_value=0.8)
    return mock


@pytest.fixture
def sample_conflict_result_no_conflict():
    """Sample conflict result with no conflicts"""
    return {
        'has_conflict': False,
        'severity': None,
        'summary': 'No conflict detected.',
        'dominant_evidence': None,
        'supporting_evidence': [
            {
                'evidence_id': 'ev1',
                'name': 'Clinical Trial NCT12345',
                'quality': 'HIGH',
                'confidence_score': 0.9,
                'agent_id': 'clinical',
                'source_type': 'clinical',
                'extraction_timestamp': datetime.utcnow().isoformat()
            },
            {
                'evidence_id': 'ev2',
                'name': 'Market Report',
                'quality': 'MEDIUM',
                'confidence_score': 0.7,
                'agent_id': 'market',
                'source_type': 'market',
                'extraction_timestamp': datetime.utcnow().isoformat()
            }
        ],
        'contradicting_evidence': [],
        'evidence_count': {
            'supports': 2,
            'contradicts': 0,
            'suggests': 0
        },
        'provenance_summary': [],
        'temporal_explanation': 'No temporal data available.'
    }


@pytest.fixture
def sample_conflict_result_with_conflict():
    """Sample conflict result with HIGH severity conflict"""
    return {
        'has_conflict': True,
        'severity': 'HIGH',
        'summary': 'Conflict detected.',
        'dominant_evidence': {
            'evidence_id': 'ev1',
            'reason': 'Highest quality',
            'polarity': 'SUPPORTS'
        },
        'supporting_evidence': [
            {
                'evidence_id': 'ev1',
                'name': 'Clinical Trial NCT12345',
                'quality': 'HIGH',
                'confidence_score': 0.9,
                'agent_id': 'clinical',
                'source_type': 'clinical',
                'extraction_timestamp': datetime.utcnow().isoformat()
            }
        ],
        'contradicting_evidence': [
            {
                'evidence_id': 'ev3',
                'name': 'Failed Clinical Trial NCT67890',
                'quality': 'HIGH',
                'confidence_score': 0.8,
                'agent_id': 'clinical',
                'source_type': 'clinical',
                'extraction_timestamp': (datetime.utcnow() - timedelta(days=365)).isoformat()
            }
        ],
        'evidence_count': {
            'supports': 1,
            'contradicts': 1,
            'suggests': 0
        },
        'provenance_summary': [],
        'temporal_explanation': 'Newer evidence contradicts older findings.'
    }


# ==============================================================================
# BASIC FUNCTIONALITY TESTS
# ==============================================================================

def test_ros_engine_initialization(mock_graph_manager, mock_conflict_reasoner):
    """Test ROSEngine can be initialized"""
    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner
    )

    assert engine is not None
    assert engine.graph == mock_graph_manager
    assert engine.conflict_reasoner == mock_conflict_reasoner
    assert engine.temporal is not None  # Should create default


def test_ros_score_in_valid_range(
    mock_graph_manager,
    mock_conflict_reasoner,
    sample_conflict_result_no_conflict
):
    """Test ROS score is always in [0, 10] range"""
    mock_conflict_reasoner.explain_conflict = Mock(return_value=sample_conflict_result_no_conflict)

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner
    )

    result = engine.compute_ros(
        drug_id='drug_123',
        disease_id='disease_456'
    )

    assert 'ros_score' in result
    assert 0.0 <= result['ros_score'] <= 10.0


def test_ros_returns_required_fields(
    mock_graph_manager,
    mock_conflict_reasoner,
    sample_conflict_result_no_conflict
):
    """Test ROS result contains all required fields"""
    mock_conflict_reasoner.explain_conflict = Mock(return_value=sample_conflict_result_no_conflict)

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner
    )

    result = engine.compute_ros(
        drug_id='drug_123',
        disease_id='disease_456'
    )

    # Required top-level fields
    assert 'drug_id' in result
    assert 'disease_id' in result
    assert 'ros_score' in result
    assert 'feature_breakdown' in result
    assert 'conflict_summary' in result
    assert 'explanation' in result
    assert 'metadata' in result

    # Required feature breakdown fields
    assert 'evidence_strength' in result['feature_breakdown']
    assert 'evidence_diversity' in result['feature_breakdown']
    assert 'conflict_penalty' in result['feature_breakdown']
    assert 'recency_boost' in result['feature_breakdown']
    assert 'patent_risk_penalty' in result['feature_breakdown']

    # Required conflict summary fields
    assert 'has_conflict' in result['conflict_summary']
    assert 'severity' in result['conflict_summary']
    assert 'dominant_evidence' in result['conflict_summary']


def test_ros_determinism(
    mock_graph_manager,
    mock_conflict_reasoner,
    mock_temporal_reasoner,
    sample_conflict_result_no_conflict
):
    """Test ROS is deterministic (same inputs → same outputs)"""
    mock_conflict_reasoner.explain_conflict = Mock(return_value=sample_conflict_result_no_conflict)

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner,
        temporal_reasoner=mock_temporal_reasoner
    )

    # Compute twice with same inputs
    result1 = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')
    result2 = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    # Scores must be identical
    assert result1['ros_score'] == result2['ros_score']
    assert result1['feature_breakdown'] == result2['feature_breakdown']


def test_no_evidence_yields_zero_score(
    mock_graph_manager,
    mock_conflict_reasoner
):
    """Test drug-disease pair with no evidence yields zero score"""
    # Mock no evidence
    mock_conflict_reasoner.explain_conflict = Mock(return_value={
        'has_conflict': False,
        'severity': None,
        'supporting_evidence': [],
        'contradicting_evidence': [],
        'evidence_count': {'supports': 0, 'contradicts': 0, 'suggests': 0},
        'provenance_summary': []
    })

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner
    )

    result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    # No evidence should yield low/zero score
    assert result['ros_score'] <= 1.0
    assert result['feature_breakdown']['evidence_strength'] == 0.0


def test_high_quality_evidence_increases_score(
    mock_graph_manager,
    mock_conflict_reasoner
):
    """Test high-quality evidence yields higher score than low-quality"""
    # High quality evidence
    high_quality_result = {
        'has_conflict': False,
        'severity': None,
        'supporting_evidence': [
            {
                'evidence_id': 'ev1',
                'quality': 'HIGH',
                'confidence_score': 0.9,
                'agent_id': 'clinical',
                'source_type': 'clinical',
                'extraction_timestamp': datetime.utcnow().isoformat()
            }
        ],
        'contradicting_evidence': [],
        'evidence_count': {'supports': 1, 'contradicts': 0, 'suggests': 0},
        'provenance_summary': []
    }

    # Low quality evidence
    low_quality_result = {
        'has_conflict': False,
        'severity': None,
        'supporting_evidence': [
            {
                'evidence_id': 'ev2',
                'quality': 'LOW',
                'confidence_score': 0.5,
                'agent_id': 'clinical',
                'source_type': 'clinical',
                'extraction_timestamp': datetime.utcnow().isoformat()
            }
        ],
        'contradicting_evidence': [],
        'evidence_count': {'supports': 1, 'contradicts': 0, 'suggests': 0},
        'provenance_summary': []
    }

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner
    )

    # Test high quality
    mock_conflict_reasoner.explain_conflict = Mock(return_value=high_quality_result)
    result_high = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    # Test low quality
    mock_conflict_reasoner.explain_conflict = Mock(return_value=low_quality_result)
    result_low = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    # High quality should yield higher score
    assert result_high['ros_score'] > result_low['ros_score']
    assert result_high['feature_breakdown']['evidence_strength'] > result_low['feature_breakdown']['evidence_strength']


def test_convenience_function(
    mock_graph_manager,
    mock_conflict_reasoner,
    sample_conflict_result_no_conflict
):
    """Test compute_ros convenience function works"""
    mock_conflict_reasoner.explain_conflict = Mock(return_value=sample_conflict_result_no_conflict)

    result = compute_ros(
        drug_id='drug_123',
        disease_id='disease_456',
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner
    )

    assert 'ros_score' in result
    assert 0.0 <= result['ros_score'] <= 10.0


# ==============================================================================
# EXPLANATION TESTS
# ==============================================================================

def test_explanation_is_non_empty(
    mock_graph_manager,
    mock_conflict_reasoner,
    sample_conflict_result_no_conflict
):
    """Test ROS generates non-empty explanation"""
    mock_conflict_reasoner.explain_conflict = Mock(return_value=sample_conflict_result_no_conflict)

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner
    )

    result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    assert result['explanation']
    assert len(result['explanation']) > 0
    assert 'Research Opportunity Score' in result['explanation']


def test_explanation_mentions_score_components(
    mock_graph_manager,
    mock_conflict_reasoner,
    sample_conflict_result_no_conflict
):
    """Test explanation mentions all score components"""
    mock_conflict_reasoner.explain_conflict = Mock(return_value=sample_conflict_result_no_conflict)

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner
    )

    result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    explanation = result['explanation']

    # Should mention all features
    assert 'Evidence Strength' in explanation
    assert 'Evidence Diversity' in explanation
    assert 'Conflict Penalty' in explanation
    assert 'Recency Boost' in explanation
    assert 'Patent Risk Penalty' in explanation


# ==============================================================================
# METADATA TESTS
# ==============================================================================

def test_metadata_includes_evidence_counts(
    mock_graph_manager,
    mock_conflict_reasoner,
    sample_conflict_result_no_conflict
):
    """Test metadata includes evidence counts"""
    mock_conflict_reasoner.explain_conflict = Mock(return_value=sample_conflict_result_no_conflict)

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner
    )

    result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    metadata = result['metadata']

    assert 'num_supporting_evidence' in metadata
    assert 'num_contradicting_evidence' in metadata
    assert 'num_suggesting_evidence' in metadata
    assert 'distinct_agents' in metadata
    assert 'computation_timestamp' in metadata

    # Verify counts match conflict result
    assert metadata['num_supporting_evidence'] == 2
    assert metadata['num_contradicting_evidence'] == 0
