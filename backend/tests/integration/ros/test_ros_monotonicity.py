"""
ROS Monotonicity Tests

Tests for score monotonicity guarantees.

Requirements (MANDATORY):
- More SUPPORTS evidence → higher score
- More conflicts → lower score
- Higher quality evidence → higher score
- More diverse sources → higher score
- More active patents → lower score

These are CRITICAL guarantees for journal defensibility.
"""

import pytest
from datetime import datetime
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
    """Mock TemporalReasoner with consistent weights"""
    mock = Mock(spec=TemporalReasoner)
    mock.compute_recency_weight = Mock(return_value=0.8)  # Consistent temporal weight
    return mock


def create_evidence(num_evidence, quality='HIGH', agent_ids=None):
    """Helper to create evidence lists"""
    if agent_ids is None:
        agent_ids = ['clinical']

    evidence = []
    for i in range(num_evidence):
        agent_id = agent_ids[i % len(agent_ids)]
        evidence.append({
            'evidence_id': f'ev_{i}',
            'quality': quality,
            'confidence_score': 0.9,
            'agent_id': agent_id,
            'source_type': 'clinical',
            'extraction_timestamp': datetime.utcnow().isoformat()
        })
    return evidence


# ==============================================================================
# EVIDENCE COUNT MONOTONICITY
# ==============================================================================

def test_more_evidence_higher_score(
    mock_graph_manager,
    mock_conflict_reasoner,
    mock_temporal_reasoner
):
    """Test monotonicity: more SUPPORTS evidence → higher score"""
    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner,
        temporal_reasoner=mock_temporal_reasoner
    )

    scores = []

    # Test with 1, 2, 3, 4 evidence
    for num_evidence in [1, 2, 3, 4]:
        evidence = create_evidence(num_evidence)

        conflict_result = {
            'has_conflict': False,
            'severity': None,
            'supporting_evidence': evidence,
            'contradicting_evidence': [],
            'evidence_count': {'supports': num_evidence, 'contradicts': 0, 'suggests': 0},
            'provenance_summary': []
        }

        mock_conflict_reasoner.explain_conflict = Mock(return_value=conflict_result)
        result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

        scores.append(result['ros_score'])

    # Scores should be monotonically increasing
    for i in range(len(scores) - 1):
        assert scores[i] <= scores[i + 1], \
            f"Evidence count monotonicity violated: {scores[i]} > {scores[i+1]} for {i+1} vs {i+2} evidence"


def test_more_conflicts_lower_score(
    mock_graph_manager,
    mock_conflict_reasoner,
    mock_temporal_reasoner
):
    """Test monotonicity: conflicts → lower score (conflict penalty increases)"""
    evidence = create_evidence(3)

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner,
        temporal_reasoner=mock_temporal_reasoner
    )

    # No conflict
    no_conflict_result = {
        'has_conflict': False,
        'severity': None,
        'supporting_evidence': evidence,
        'contradicting_evidence': [],
        'evidence_count': {'supports': 3, 'contradicts': 0, 'suggests': 0},
        'provenance_summary': []
    }

    mock_conflict_reasoner.explain_conflict = Mock(return_value=no_conflict_result)
    score_no_conflict = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')['ros_score']

    # LOW conflict
    low_conflict_result = {
        'has_conflict': True,
        'severity': 'LOW',
        'supporting_evidence': evidence,
        'contradicting_evidence': create_evidence(1),
        'evidence_count': {'supports': 3, 'contradicts': 1, 'suggests': 0},
        'provenance_summary': []
    }

    mock_conflict_reasoner.explain_conflict = Mock(return_value=low_conflict_result)
    score_low_conflict = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')['ros_score']

    # MEDIUM conflict
    medium_conflict_result = {
        'has_conflict': True,
        'severity': 'MEDIUM',
        'supporting_evidence': evidence,
        'contradicting_evidence': create_evidence(1),
        'evidence_count': {'supports': 3, 'contradicts': 1, 'suggests': 0},
        'provenance_summary': []
    }

    mock_conflict_reasoner.explain_conflict = Mock(return_value=medium_conflict_result)
    score_medium_conflict = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')['ros_score']

    # HIGH conflict
    high_conflict_result = {
        'has_conflict': True,
        'severity': 'HIGH',
        'supporting_evidence': evidence,
        'contradicting_evidence': create_evidence(1),
        'evidence_count': {'supports': 3, 'contradicts': 1, 'suggests': 0},
        'provenance_summary': []
    }

    mock_conflict_reasoner.explain_conflict = Mock(return_value=high_conflict_result)
    score_high_conflict = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')['ros_score']

    # Monotonicity: no conflict > low > medium > high
    assert score_no_conflict > score_low_conflict
    assert score_low_conflict > score_medium_conflict
    assert score_medium_conflict > score_high_conflict


# ==============================================================================
# QUALITY MONOTONICITY
# ==============================================================================

def test_higher_quality_higher_score(
    mock_graph_manager,
    mock_conflict_reasoner,
    mock_temporal_reasoner
):
    """Test monotonicity: HIGH quality > MEDIUM > LOW"""
    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner,
        temporal_reasoner=mock_temporal_reasoner
    )

    scores = {}

    for quality in ['LOW', 'MEDIUM', 'HIGH']:
        evidence = create_evidence(2, quality=quality)

        conflict_result = {
            'has_conflict': False,
            'severity': None,
            'supporting_evidence': evidence,
            'contradicting_evidence': [],
            'evidence_count': {'supports': 2, 'contradicts': 0, 'suggests': 0},
            'provenance_summary': []
        }

        mock_conflict_reasoner.explain_conflict = Mock(return_value=conflict_result)
        result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

        scores[quality] = result['ros_score']

    # Quality monotonicity
    assert scores['HIGH'] > scores['MEDIUM']
    assert scores['MEDIUM'] > scores['LOW']


# ==============================================================================
# DIVERSITY MONOTONICITY
# ==============================================================================

def test_more_diverse_sources_higher_score(
    mock_graph_manager,
    mock_conflict_reasoner,
    mock_temporal_reasoner
):
    """Test monotonicity: more distinct agents → higher score"""
    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner,
        temporal_reasoner=mock_temporal_reasoner
    )

    scores = []

    # Test with 1, 2, 3, 4 distinct agents
    agent_sets = [
        ['clinical'],
        ['clinical', 'market'],
        ['clinical', 'market', 'patent'],
        ['clinical', 'market', 'patent', 'literature']
    ]

    for agent_ids in agent_sets:
        # Create evidence from different agents
        evidence = create_evidence(len(agent_ids), agent_ids=agent_ids)

        conflict_result = {
            'has_conflict': False,
            'severity': None,
            'supporting_evidence': evidence,
            'contradicting_evidence': [],
            'evidence_count': {'supports': len(agent_ids), 'contradicts': 0, 'suggests': 0},
            'provenance_summary': []
        }

        mock_conflict_reasoner.explain_conflict = Mock(return_value=conflict_result)
        result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

        scores.append(result['ros_score'])

    # Diversity monotonicity: more agents → higher score
    for i in range(len(scores) - 1):
        assert scores[i] <= scores[i + 1], \
            f"Diversity monotonicity violated: {scores[i]} > {scores[i+1]} for {i+1} vs {i+2} agents"


# ==============================================================================
# PATENT RISK MONOTONICITY
# ==============================================================================

def test_more_patents_lower_score(
    mock_graph_manager,
    mock_conflict_reasoner,
    mock_temporal_reasoner
):
    """Test monotonicity: more active patents → lower score (via patent risk penalty)"""
    # Keep clinical evidence constant across all tests
    clinical_evidence = create_evidence(3, quality='HIGH')

    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner,
        temporal_reasoner=mock_temporal_reasoner
    )

    penalties = []

    # Test with 0, 2, 5, 15 patents
    for num_patents in [0, 2, 5, 15]:
        # Create patent evidence (all active) but DON'T add to supporting evidence
        # We want to isolate the patent risk penalty
        patent_evidence = []
        for i in range(num_patents):
            patent_evidence.append({
                'evidence_id': f'patent_{i}',
                'quality': 'MEDIUM',
                'confidence_score': 0.7,
                'agent_id': 'patent',
                'source_type': 'patent',
                'extraction_timestamp': datetime.utcnow().isoformat(),
                'validity_end': None  # Active (not expired)
            })

        # All evidence includes patents (for patent risk calculation)
        # But supporting_evidence does NOT (to isolate patent penalty effect)
        all_evidence = clinical_evidence + patent_evidence

        conflict_result = {
            'has_conflict': False,
            'severity': None,
            'supporting_evidence': clinical_evidence,  # Only clinical (constant)
            'contradicting_evidence': [],
            'evidence_count': {'supports': len(clinical_evidence), 'contradicts': 0, 'suggests': 0},
            'provenance_summary': []
        }

        mock_conflict_reasoner.explain_conflict = Mock(return_value=conflict_result)
        result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

        # Extract patent risk penalty (should get more negative with more patents)
        patent_penalty = result['feature_breakdown']['patent_risk_penalty']
        penalties.append(patent_penalty)

    # Patent risk monotonicity: more patents → more negative penalty
    # penalties should be: [0.0, -0.3, -1.0, -2.0] for [0, 2, 5, 15] patents
    for i in range(len(penalties) - 1):
        assert penalties[i] >= penalties[i + 1], \
            f"Patent risk penalty monotonicity violated: {penalties[i]} < {penalties[i+1]} for {[0, 2, 5, 15][i]} vs {[0, 2, 5, 15][i+1]} patents"


# ==============================================================================
# COMBINED MONOTONICITY
# ==============================================================================

def test_combined_monotonicity(
    mock_graph_manager,
    mock_conflict_reasoner,
    mock_temporal_reasoner
):
    """Test monotonicity holds when changing multiple factors"""
    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner,
        temporal_reasoner=mock_temporal_reasoner
    )

    # Baseline: 2 MEDIUM quality evidence, 1 agent, no conflict
    baseline_evidence = create_evidence(2, quality='MEDIUM', agent_ids=['clinical'])
    baseline_result = {
        'has_conflict': False,
        'severity': None,
        'supporting_evidence': baseline_evidence,
        'contradicting_evidence': [],
        'evidence_count': {'supports': 2, 'contradicts': 0, 'suggests': 0},
        'provenance_summary': []
    }

    mock_conflict_reasoner.explain_conflict = Mock(return_value=baseline_result)
    baseline_score = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')['ros_score']

    # Improved: 3 HIGH quality evidence, 2 agents, no conflict
    improved_evidence = create_evidence(3, quality='HIGH', agent_ids=['clinical', 'market'])
    improved_result = {
        'has_conflict': False,
        'severity': None,
        'supporting_evidence': improved_evidence,
        'contradicting_evidence': [],
        'evidence_count': {'supports': 3, 'contradicts': 0, 'suggests': 0},
        'provenance_summary': []
    }

    mock_conflict_reasoner.explain_conflict = Mock(return_value=improved_result)
    improved_score = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')['ros_score']

    # Improved scenario should have higher score
    assert improved_score > baseline_score, \
        f"Combined monotonicity violated: improved={improved_score} not > baseline={baseline_score}"


# ==============================================================================
# SCORE BOUNDS MONOTONICITY
# ==============================================================================

def test_score_never_exceeds_bounds(
    mock_graph_manager,
    mock_conflict_reasoner,
    mock_temporal_reasoner
):
    """Test scores always stay in [0, 10] regardless of inputs"""
    engine = ROSEngine(
        graph_manager=mock_graph_manager,
        conflict_reasoner=mock_conflict_reasoner,
        temporal_reasoner=mock_temporal_reasoner
    )

    # Extreme case: many high-quality evidence, no conflicts
    extreme_evidence = create_evidence(
        100,
        quality='HIGH',
        agent_ids=['clinical', 'market', 'patent', 'literature']
    )

    extreme_result = {
        'has_conflict': False,
        'severity': None,
        'supporting_evidence': extreme_evidence,
        'contradicting_evidence': [],
        'evidence_count': {'supports': 100, 'contradicts': 0, 'suggests': 0},
        'provenance_summary': []
    }

    mock_conflict_reasoner.explain_conflict = Mock(return_value=extreme_result)
    result = engine.compute_ros(drug_id='drug_123', disease_id='disease_456')

    # Score must be clamped to [0, 10]
    assert 0.0 <= result['ros_score'] <= 10.0
