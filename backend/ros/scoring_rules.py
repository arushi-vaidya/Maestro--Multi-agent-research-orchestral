"""
ROS Scoring Rules - Explicit Numeric Constants

All scoring weights and thresholds are defined here.
No magic numbers allowed in the main code.

Design Rationale:
- Explicit constants make scoring auditable
- Easy to tune without code changes
- Journal papers can cite these exact values
- Ablation studies can modify these systematically
"""

from typing import Dict


# ==============================================================================
# FEATURE WEIGHTS (sum to reasonable total)
# ==============================================================================

class ScoringWeights:
    """
    Feature contribution weights to final ROS score (0-10 scale)

    RATIONALE:
    - Evidence strength is primary signal (40% of max score)
    - Diversity ensures multi-source validation (20% of max score)
    - Conflicts are strong negative signal (up to -30% penalty)
    - Recency matters for evolving fields (20% of max score)
    - Patent risk is strategic consideration (up to -20% penalty)
    """

    # Maximum contribution per feature (positive features)
    MAX_EVIDENCE_STRENGTH = 4.0   # 0-4 points
    MAX_DIVERSITY = 2.0            # 0-2 points
    MAX_RECENCY_BOOST = 2.0        # 0-2 points

    # Maximum penalty per feature (negative features)
    MAX_CONFLICT_PENALTY = 3.0     # 0 to -3 points
    MAX_PATENT_RISK_PENALTY = 2.0  # 0 to -2 points

    # Final score bounds
    MIN_SCORE = 0.0
    MAX_SCORE = 10.0


# ==============================================================================
# EVIDENCE QUALITY WEIGHTS
# ==============================================================================

class QualityWeights:
    """
    Evidence quality tier weights for scoring

    RATIONALE:
    - HIGH quality (Phase 3 trials, granted patents): Full weight
    - MEDIUM quality (Phase 2, applications): Moderate weight
    - LOW quality (Phase 1, searches): Low weight

    Based on pharmaceutical industry standards for evidence hierarchy.
    """

    HIGH = 1.0     # Phase 3 trials, granted patents, peer-reviewed papers
    MEDIUM = 0.6   # Phase 2 trials, patent applications, market reports
    LOW = 0.3      # Phase 1 trials, patent searches, web sources


# ==============================================================================
# CONFLICT PENALTY WEIGHTS
# ==============================================================================

class ConflictPenalty:
    """
    Conflict severity penalty weights

    RATIONALE:
    - HIGH conflict: Strong evidence on both sides → major uncertainty
    - MEDIUM conflict: Asymmetric evidence quality → moderate uncertainty
    - LOW conflict: Weak evidence conflict → minor uncertainty

    Penalties are harsh because conflicts indicate high research risk.
    """

    HIGH = -3.0    # Both sides have high-quality evidence (major disagreement)
    MEDIUM = -1.5  # One side has high-quality, other doesn't (moderate risk)
    LOW = -0.5     # Both sides have low-quality evidence (minor noise)
    NONE = 0.0     # No conflicts detected


# ==============================================================================
# DIVERSITY SCORING
# ==============================================================================

class DiversityScoring:
    """
    Agent diversity scoring thresholds

    RATIONALE:
    - Single agent: Limited perspective
    - Two agents: Corroboration from independent sources
    - Three agents: Strong multi-modal evidence
    - Four+ agents: Comprehensive cross-validation

    Diversity reduces single-source bias.
    """

    # Points awarded for N distinct agent sources
    ONE_AGENT = 0.5
    TWO_AGENTS = 1.0
    THREE_AGENTS = 1.5
    FOUR_PLUS_AGENTS = 2.0


# ==============================================================================
# PATENT RISK WEIGHTS
# ==============================================================================

class PatentRisk:
    """
    Patent-based risk penalties

    RATIONALE:
    - Many active patents: High FTO risk, costly licensing
    - Some active patents: Moderate FTO risk
    - Few/expired patents: Low FTO risk
    - No patents: No IP barriers

    Patent risk is strategic (not scientific) but critical for ROI.
    """

    # Thresholds for patent count classification
    MANY_PATENTS_THRESHOLD = 10
    SOME_PATENTS_THRESHOLD = 3

    # Penalties
    MANY_ACTIVE_PATENTS = -2.0   # >10 active patents
    SOME_ACTIVE_PATENTS = -1.0   # 3-10 active patents
    FEW_ACTIVE_PATENTS = -0.3    # 1-2 active patents
    NO_PATENTS = 0.0             # 0 active patents or all expired


# ==============================================================================
# RECENCY SCORING
# ==============================================================================

class RecencyScoring:
    """
    Temporal recency boost parameters

    RATIONALE:
    - Use AKGP temporal decay (already implemented)
    - Recent evidence indicates active research area
    - Very old evidence may be outdated

    Recency is a boost, not a requirement (old evidence still valid).
    """

    # Minimum recency weight (even very old evidence has value)
    MIN_RECENCY_WEIGHT = 0.1

    # Maximum recency boost multiplier
    MAX_RECENCY_BOOST = 2.0


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_quality_weight(quality: str) -> float:
    """
    Get numeric weight for evidence quality tier

    Args:
        quality: "HIGH", "MEDIUM", or "LOW"

    Returns:
        Numeric weight (0.3-1.0)
    """
    quality_map = {
        "HIGH": QualityWeights.HIGH,
        "MEDIUM": QualityWeights.MEDIUM,
        "LOW": QualityWeights.LOW,
        "high": QualityWeights.HIGH,
        "medium": QualityWeights.MEDIUM,
        "low": QualityWeights.LOW
    }
    return quality_map.get(quality, QualityWeights.MEDIUM)


def get_conflict_penalty(severity: str) -> float:
    """
    Get penalty for conflict severity

    Args:
        severity: "HIGH", "MEDIUM", "LOW", or None

    Returns:
        Penalty value (negative or zero)
    """
    if severity is None:
        return ConflictPenalty.NONE

    severity_map = {
        "HIGH": ConflictPenalty.HIGH,
        "MEDIUM": ConflictPenalty.MEDIUM,
        "LOW": ConflictPenalty.LOW
    }
    return severity_map.get(severity, ConflictPenalty.NONE)


def get_diversity_score(num_agents: int) -> float:
    """
    Get diversity score for number of distinct agents

    Args:
        num_agents: Number of distinct agent sources

    Returns:
        Diversity score (0.5-2.0)
    """
    if num_agents >= 4:
        return DiversityScoring.FOUR_PLUS_AGENTS
    elif num_agents == 3:
        return DiversityScoring.THREE_AGENTS
    elif num_agents == 2:
        return DiversityScoring.TWO_AGENTS
    elif num_agents == 1:
        return DiversityScoring.ONE_AGENT
    else:
        return 0.0


def get_patent_risk_penalty(active_patent_count: int) -> float:
    """
    Get penalty for patent risk based on active patent count

    Args:
        active_patent_count: Number of active (unexpired) patents

    Returns:
        Penalty value (negative or zero)
    """
    if active_patent_count >= PatentRisk.MANY_PATENTS_THRESHOLD:
        return PatentRisk.MANY_ACTIVE_PATENTS
    elif active_patent_count >= PatentRisk.SOME_PATENTS_THRESHOLD:
        return PatentRisk.SOME_ACTIVE_PATENTS
    elif active_patent_count > 0:
        return PatentRisk.FEW_ACTIVE_PATENTS
    else:
        return PatentRisk.NO_PATENTS


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    'ScoringWeights',
    'QualityWeights',
    'ConflictPenalty',
    'DiversityScoring',
    'PatentRisk',
    'RecencyScoring',
    'get_quality_weight',
    'get_conflict_penalty',
    'get_diversity_score',
    'get_patent_risk_penalty'
]
