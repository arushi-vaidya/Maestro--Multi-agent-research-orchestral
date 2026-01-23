"""
ROS Feature Extractors

Each function extracts ONE feature from AKGP data.

Design Principles:
- One function per feature (single responsibility)
- No shared mutable state
- Deterministic math only (same inputs → same outputs)
- Fully documented rationale
- Type hints for all functions

All extractors consume ONLY:
- AKGP query engine outputs
- Conflict reasoning outputs
- Never raw agent data
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from akgp.temporal import TemporalReasoner
from ros.scoring_rules import (
    ScoringWeights,
    get_quality_weight,
    get_diversity_score,
    get_patent_risk_penalty
)

logger = logging.getLogger(__name__)


# ==============================================================================
# FEATURE 1: EVIDENCE STRENGTH
# ==============================================================================

def extract_evidence_strength(
    supporting_evidence: List[Dict[str, Any]],
    suggesting_evidence: List[Dict[str, Any]]
) -> float:
    """
    Extract evidence strength score from supporting/suggesting evidence

    FORMULA:
        strength = Σ(quality_weight × confidence_score) for all SUPPORTS/SUGGESTS evidence
        normalized to [0, MAX_EVIDENCE_STRENGTH]

    RATIONALE:
    - SUPPORTS evidence: Strong positive signal
    - SUGGESTS evidence: Weak positive signal (treated equally in sum)
    - Quality weight: HIGH (1.0) > MEDIUM (0.6) > LOW (0.3)
    - Confidence score: Agent's confidence in this evidence

    Args:
        supporting_evidence: List of SUPPORTS evidence dicts from conflict reasoning
        suggesting_evidence: List of SUGGESTS evidence dicts from conflict reasoning

    Returns:
        Evidence strength score (0.0 to MAX_EVIDENCE_STRENGTH)
    """
    all_positive_evidence = supporting_evidence + suggesting_evidence

    if not all_positive_evidence:
        return 0.0

    # Sum weighted evidence scores
    total_weighted_score = 0.0
    for evidence in all_positive_evidence:
        quality = evidence.get('quality', 'MEDIUM')
        confidence = evidence.get('confidence_score', 0.5)

        quality_weight = get_quality_weight(quality)
        weighted_score = quality_weight * confidence

        total_weighted_score += weighted_score

    # Normalize to [0, MAX_EVIDENCE_STRENGTH]
    # Use logarithmic scaling to avoid unbounded growth
    # log(1 + x) grows slowly, scaled to MAX range
    import math
    normalized_score = ScoringWeights.MAX_EVIDENCE_STRENGTH * math.log(1 + total_weighted_score) / math.log(1 + 10)

    # Clamp to max
    return min(normalized_score, ScoringWeights.MAX_EVIDENCE_STRENGTH)


# ==============================================================================
# FEATURE 2: EVIDENCE DIVERSITY
# ==============================================================================

def extract_evidence_diversity(
    all_evidence: List[Dict[str, Any]]
) -> float:
    """
    Extract evidence diversity score from agent sources

    FORMULA:
        diversity = score(num_distinct_agents)
        1 agent = 0.5, 2 agents = 1.0, 3 agents = 1.5, 4+ agents = 2.0

    RATIONALE:
    - Single-source evidence is less reliable (one perspective)
    - Multi-source evidence provides corroboration
    - Different agents have complementary strengths:
        - Clinical: Efficacy/safety data
        - Patent: IP landscape
        - Market: Commercial viability
        - Literature: Scientific foundation

    Args:
        all_evidence: Combined list of all evidence (supports + contradicts + suggests)

    Returns:
        Diversity score (0.0 to MAX_DIVERSITY)
    """
    if not all_evidence:
        return 0.0

    # Extract distinct agent IDs
    agent_ids = set()
    for evidence in all_evidence:
        agent_id = evidence.get('agent_id')
        if agent_id:
            agent_ids.add(agent_id)

    num_distinct_agents = len(agent_ids)

    # Get diversity score from rules
    return get_diversity_score(num_distinct_agents)


# ==============================================================================
# FEATURE 3: CONFLICT PENALTY
# ==============================================================================

def extract_conflict_penalty(
    conflict_summary: Dict[str, Any]
) -> float:
    """
    Extract conflict penalty from conflict reasoning output

    FORMULA:
        penalty = conflict_severity_penalty
        HIGH = -3.0, MEDIUM = -1.5, LOW = -0.5, NONE = 0.0

    RATIONALE:
    - HIGH conflict: Strong evidence on BOTH sides → major uncertainty
        Example: Phase 3 trial shows efficacy, but another Phase 3 shows failure
    - MEDIUM conflict: Asymmetric evidence quality → moderate uncertainty
        Example: Phase 3 shows efficacy, but Phase 1 shows toxicity
    - LOW conflict: Weak evidence on both sides → minor noise
        Example: Preclinical data conflicts, but not definitive
    - Penalties are intentionally harsh to reflect research risk

    Args:
        conflict_summary: Conflict explanation from ConflictReasoner.explain_conflict()

    Returns:
        Conflict penalty (negative or zero)
    """
    from ros.scoring_rules import get_conflict_penalty

    has_conflict = conflict_summary.get('has_conflict', False)

    if not has_conflict:
        return 0.0

    severity = conflict_summary.get('severity')
    penalty = get_conflict_penalty(severity)

    logger.debug(f"Conflict detected: severity={severity}, penalty={penalty}")

    return penalty


# ==============================================================================
# FEATURE 4: RECENCY BOOST
# ==============================================================================

def extract_recency_boost(
    supporting_evidence: List[Dict[str, Any]],
    suggesting_evidence: List[Dict[str, Any]],
    temporal_reasoner: TemporalReasoner
) -> float:
    """
    Extract recency boost from temporal weighting

    FORMULA:
        recency_boost = avg(temporal_weight) × MAX_RECENCY_BOOST
        Uses AKGP temporal decay logic (half-life based)

    RATIONALE:
    - Recent evidence indicates active research area
    - Newer findings may supersede older ones
    - But old evidence still valid (min weight = 0.1)
    - Uses AKGP half-life decay:
        - Clinical: 2 years
        - Patent: 3 years
        - Literature: 1 year
        - Market: 6 months

    Args:
        supporting_evidence: SUPPORTS evidence list
        suggesting_evidence: SUGGESTS evidence list
        temporal_reasoner: AKGP TemporalReasoner instance (for config)

    Returns:
        Recency boost (0.0 to MAX_RECENCY_BOOST)
    """
    all_positive_evidence = supporting_evidence + suggesting_evidence

    if not all_positive_evidence:
        return 0.0

    # Import math for exponential decay
    import math

    # Get half-life config from temporal reasoner
    from akgp.temporal import TemporalConfig
    config = temporal_reasoner.config if hasattr(temporal_reasoner, 'config') else TemporalConfig()

    # Calculate temporal weight for each evidence
    temporal_weights = []
    reference_time = datetime.utcnow()

    for evidence in all_positive_evidence:
        # Get timestamp
        timestamp_str = evidence.get('extraction_timestamp')
        if not timestamp_str:
            # No timestamp, use minimum weight
            temporal_weights.append(0.1)
            continue

        # Parse timestamp
        if isinstance(timestamp_str, str):
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except:
                timestamp = None
        elif isinstance(timestamp_str, datetime):
            timestamp = timestamp_str
        else:
            timestamp = None

        if not timestamp:
            temporal_weights.append(0.1)
            continue

        # Get source type for half-life
        source_type_str = evidence.get('source_type', 'clinical')

        # Get half-life (use string keys for SourceType enum)
        half_life_map = {
            'clinical': 730,
            'patent': 1095,
            'literature': 365,
            'market': 180
        }
        half_life = half_life_map.get(source_type_str, 365)

        # Calculate age in days
        age_seconds = (reference_time - timestamp).total_seconds()
        age_days = age_seconds / 86400

        # Exponential decay: weight = 2^(-age / half_life)
        decay_factor = math.pow(2, -age_days / half_life)

        # Clamp to min/max bounds
        weight = max(0.1, min(2.0, decay_factor))

        temporal_weights.append(weight)

    # Average temporal weight
    avg_temporal_weight = sum(temporal_weights) / len(temporal_weights)

    # Scale to recency boost range
    recency_boost = avg_temporal_weight * ScoringWeights.MAX_RECENCY_BOOST

    return min(recency_boost, ScoringWeights.MAX_RECENCY_BOOST)


# ==============================================================================
# FEATURE 5: PATENT RISK PENALTY
# ==============================================================================

def extract_patent_risk_penalty(
    all_evidence: List[Dict[str, Any]]
) -> float:
    """
    Extract patent risk penalty from patent evidence

    FORMULA:
        penalty = patent_count_penalty
        Many (>10) = -2.0, Some (3-10) = -1.0, Few (1-2) = -0.3, None = 0.0

    RATIONALE:
    - Many active patents: High FTO (freedom-to-operate) risk
        - Costly licensing or litigation
        - Development may be blocked
    - Some active patents: Moderate FTO risk
        - Possible workarounds or licenses
    - Few/expired patents: Low FTO risk
        - Clear or navigable IP landscape
    - No patents: No IP barriers
        - But also indicates less commercial validation

    IMPORTANT:
    - Only count ACTIVE (unexpired) patents
    - Expired patents contribute zero penalty
    - Patent quality matters less than existence

    Args:
        all_evidence: Combined evidence list (to extract patent evidence)

    Returns:
        Patent risk penalty (negative or zero)
    """
    # Filter to patent evidence only
    patent_evidence = [
        e for e in all_evidence
        if e.get('source_type') == 'patent'
    ]

    if not patent_evidence:
        return 0.0  # No patents = no penalty

    # Count active (unexpired) patents
    active_patent_count = 0
    now = datetime.utcnow()

    for evidence in patent_evidence:
        # Check if patent is still active
        # Evidence metadata should have expiration info
        metadata = evidence.get('metadata', {})

        # Check validity_end from evidence node
        validity_end_str = evidence.get('validity_end')
        if validity_end_str:
            # Parse validity_end
            if isinstance(validity_end_str, str):
                try:
                    validity_end = datetime.fromisoformat(validity_end_str)
                except:
                    validity_end = None
            elif isinstance(validity_end_str, datetime):
                validity_end = validity_end_str
            else:
                validity_end = None

            # If expired, skip
            if validity_end and validity_end < now:
                continue

        # Patent is active
        active_patent_count += 1

    # Get penalty from rules
    penalty = get_patent_risk_penalty(active_patent_count)

    logger.debug(f"Patent risk: {active_patent_count} active patents, penalty={penalty}")

    return penalty


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    'extract_evidence_strength',
    'extract_evidence_diversity',
    'extract_conflict_penalty',
    'extract_recency_boost',
    'extract_patent_risk_penalty'
]
