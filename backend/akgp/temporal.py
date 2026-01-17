"""
AKGP Temporal Logic
Handles temporal reasoning and recency weighting for evidence

This module provides:
- Temporal validity checking
- Recency-based weighting
- Time-series evidence analysis
- Evidence expiration handling

Design Philosophy:
- Newer evidence is weighted higher (but not automatically better)
- Evidence can have validity periods
- Expired evidence is retained but flagged
- Deterministic, rule-based temporal logic (no ML)
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import math

from akgp.schema import EvidenceNode, EvidenceQuality, SourceType

logger = logging.getLogger(__name__)


# ==============================================================================
# TEMPORAL CONFIGURATION
# ==============================================================================

class TemporalConfig:
    """Configuration for temporal logic"""

    # Recency decay half-life (how quickly evidence loses relevance)
    # After this period, evidence weight is reduced by 50%
    RECENCY_HALF_LIFE_DAYS = {
        SourceType.CLINICAL: 730,  # 2 years (clinical trials evolve slowly)
        SourceType.PATENT: 1095,  # 3 years (patents have long validity)
        SourceType.LITERATURE: 365,  # 1 year (literature evolves faster)
        SourceType.MARKET: 180,  # 6 months (market data changes quickly)
    }

    # Evidence validity periods (default if not explicitly set)
    DEFAULT_VALIDITY_DAYS = {
        SourceType.CLINICAL: None,  # Clinical trials are valid indefinitely (unless contradicted)
        SourceType.PATENT: 7300,  # ~20 years (patent lifetime)
        SourceType.LITERATURE: None,  # Literature is valid indefinitely
        SourceType.MARKET: 730,  # 2 years (market forecasts expire)
    }

    # Minimum recency weight (even very old evidence has some weight)
    MIN_RECENCY_WEIGHT = 0.1

    # Maximum recency boost for recent evidence
    MAX_RECENCY_BOOST = 2.0


# ==============================================================================
# TEMPORAL REASONING ENGINE
# ==============================================================================

class TemporalReasoner:
    """
    Handles temporal logic for AKGP knowledge graph

    Provides methods for:
    - Checking evidence validity
    - Computing recency weights
    - Filtering evidence by time
    - Temporal aggregation
    """

    def __init__(self, config: Optional[TemporalConfig] = None):
        """
        Initialize temporal reasoner

        Args:
            config: Optional custom configuration (uses defaults if not provided)
        """
        self.config = config or TemporalConfig()

    def is_valid(
        self,
        evidence: EvidenceNode,
        reference_time: Optional[datetime] = None
    ) -> bool:
        """
        Check if evidence is temporally valid

        Args:
            evidence: Evidence node to check
            reference_time: Time to check validity against (default: now)

        Returns:
            True if evidence is currently valid
        """
        reference_time = reference_time or datetime.utcnow()

        # Check validity_start
        if evidence.validity_start and evidence.validity_start > reference_time:
            return False  # Not yet valid

        # Check validity_end
        if evidence.validity_end and evidence.validity_end < reference_time:
            return False  # Expired

        return True

    def compute_recency_weight(
        self,
        evidence: EvidenceNode,
        reference_time: Optional[datetime] = None
    ) -> float:
        """
        Compute recency weight for evidence using exponential decay

        Args:
            evidence: Evidence node
            reference_time: Time to compute weight against (default: now)

        Returns:
            Recency weight (0.0 to MAX_RECENCY_BOOST)

        Formula:
            weight = exp(-ln(2) * age / half_life)

        Where:
            - age = time since extraction
            - half_life = configured half-life for this source type
        """
        reference_time = reference_time or datetime.utcnow()

        # Calculate age in days
        age_seconds = (reference_time - evidence.extraction_timestamp).total_seconds()
        age_days = age_seconds / 86400  # Convert to days

        # Get half-life for this source type
        half_life = self.config.RECENCY_HALF_LIFE_DAYS.get(
            evidence.source_type,
            365  # Default: 1 year
        )

        # Exponential decay: weight = 2^(-age / half_life)
        decay_factor = math.pow(2, -age_days / half_life)

        # Clamp to min/max bounds
        weight = max(
            self.config.MIN_RECENCY_WEIGHT,
            min(self.config.MAX_RECENCY_BOOST, decay_factor)
        )

        logger.debug(
            f"Recency weight for evidence {evidence.id}: "
            f"{weight:.3f} (age: {age_days:.1f} days, half-life: {half_life} days)"
        )

        return weight

    def compute_combined_weight(
        self,
        evidence: EvidenceNode,
        reference_time: Optional[datetime] = None
    ) -> float:
        """
        Compute combined weight considering quality, confidence, and recency

        Args:
            evidence: Evidence node
            reference_time: Time to compute weight against (default: now)

        Returns:
            Combined weight (0.0 to 1.0)

        Formula:
            combined_weight = base_quality * confidence * recency_weight

        Where:
            - base_quality: 0.9 (HIGH), 0.7 (MEDIUM), 0.5 (LOW)
            - confidence: evidence confidence score
            - recency_weight: computed recency weight
        """
        # Base quality weights
        quality_weights = {
            EvidenceQuality.HIGH: 0.9,
            EvidenceQuality.MEDIUM: 0.7,
            EvidenceQuality.LOW: 0.5,
        }

        base_quality = quality_weights.get(evidence.quality, 0.7)
        recency_weight = self.compute_recency_weight(evidence, reference_time)

        # Combined weight (normalized to 0-1 range)
        combined = base_quality * evidence.confidence_score * recency_weight

        # Normalize by MAX_RECENCY_BOOST to keep in 0-1 range
        combined = combined / self.config.MAX_RECENCY_BOOST

        return min(1.0, combined)

    def filter_valid_evidence(
        self,
        evidence_list: List[EvidenceNode],
        reference_time: Optional[datetime] = None
    ) -> List[EvidenceNode]:
        """
        Filter evidence list to only valid evidence

        Args:
            evidence_list: List of evidence nodes
            reference_time: Time to check validity against (default: now)

        Returns:
            Filtered list of valid evidence
        """
        return [
            evidence for evidence in evidence_list
            if self.is_valid(evidence, reference_time)
        ]

    def sort_by_recency(
        self,
        evidence_list: List[EvidenceNode],
        reference_time: Optional[datetime] = None
    ) -> List[Tuple[EvidenceNode, float]]:
        """
        Sort evidence by recency weight (highest first)

        Args:
            evidence_list: List of evidence nodes
            reference_time: Time to compute weights against (default: now)

        Returns:
            List of (evidence, weight) tuples, sorted by weight descending
        """
        weighted_evidence = [
            (evidence, self.compute_recency_weight(evidence, reference_time))
            for evidence in evidence_list
        ]

        # Sort by weight (descending)
        weighted_evidence.sort(key=lambda x: x[1], reverse=True)

        return weighted_evidence

    def sort_by_combined_weight(
        self,
        evidence_list: List[EvidenceNode],
        reference_time: Optional[datetime] = None
    ) -> List[Tuple[EvidenceNode, float]]:
        """
        Sort evidence by combined weight (quality + confidence + recency)

        Args:
            evidence_list: List of evidence nodes
            reference_time: Time to compute weights against (default: now)

        Returns:
            List of (evidence, combined_weight) tuples, sorted by weight descending
        """
        weighted_evidence = [
            (evidence, self.compute_combined_weight(evidence, reference_time))
            for evidence in evidence_list
        ]

        # Sort by combined weight (descending)
        weighted_evidence.sort(key=lambda x: x[1], reverse=True)

        return weighted_evidence

    def get_most_recent_evidence(
        self,
        evidence_list: List[EvidenceNode],
        reference_time: Optional[datetime] = None,
        top_k: int = 1
    ) -> List[EvidenceNode]:
        """
        Get the most recent valid evidence

        Args:
            evidence_list: List of evidence nodes
            reference_time: Time to check validity against (default: now)
            top_k: Number of most recent items to return

        Returns:
            List of most recent evidence (up to top_k items)
        """
        # Filter to valid evidence
        valid_evidence = self.filter_valid_evidence(evidence_list, reference_time)

        if not valid_evidence:
            return []

        # Sort by extraction timestamp (descending)
        valid_evidence.sort(key=lambda e: e.extraction_timestamp, reverse=True)

        return valid_evidence[:top_k]

    def get_strongest_evidence(
        self,
        evidence_list: List[EvidenceNode],
        reference_time: Optional[datetime] = None,
        top_k: int = 1
    ) -> List[Tuple[EvidenceNode, float]]:
        """
        Get the strongest evidence based on combined weight

        Args:
            evidence_list: List of evidence nodes
            reference_time: Time to compute weights against (default: now)
            top_k: Number of strongest items to return

        Returns:
            List of (evidence, weight) tuples for strongest evidence
        """
        # Filter to valid evidence
        valid_evidence = self.filter_valid_evidence(evidence_list, reference_time)

        if not valid_evidence:
            return []

        # Sort by combined weight
        sorted_evidence = self.sort_by_combined_weight(valid_evidence, reference_time)

        return sorted_evidence[:top_k]

    def analyze_temporal_distribution(
        self,
        evidence_list: List[EvidenceNode]
    ) -> Dict[str, Any]:
        """
        Analyze temporal distribution of evidence

        Args:
            evidence_list: List of evidence nodes

        Returns:
            Dictionary with temporal statistics
        """
        if not evidence_list:
            return {
                "total_evidence": 0,
                "earliest_timestamp": None,
                "latest_timestamp": None,
                "time_span_days": 0,
                "valid_evidence_count": 0,
                "expired_evidence_count": 0
            }

        timestamps = [e.extraction_timestamp for e in evidence_list]
        earliest = min(timestamps)
        latest = max(timestamps)
        time_span = (latest - earliest).days

        valid_count = len(self.filter_valid_evidence(evidence_list))
        expired_count = len(evidence_list) - valid_count

        # Count evidence by source type and year
        by_year = {}
        for evidence in evidence_list:
            year = evidence.extraction_timestamp.year
            if year not in by_year:
                by_year[year] = {}

            source_type = evidence.source_type.value
            if source_type not in by_year[year]:
                by_year[year][source_type] = 0
            by_year[year][source_type] += 1

        return {
            "total_evidence": len(evidence_list),
            "earliest_timestamp": earliest.isoformat(),
            "latest_timestamp": latest.isoformat(),
            "time_span_days": time_span,
            "valid_evidence_count": valid_count,
            "expired_evidence_count": expired_count,
            "evidence_by_year": by_year
        }

    def set_validity_period(
        self,
        evidence: EvidenceNode,
        validity_days: Optional[int] = None
    ) -> EvidenceNode:
        """
        Set validity period for evidence

        Args:
            evidence: Evidence node
            validity_days: Number of days evidence is valid (None = indefinite)

        Returns:
            Updated evidence node
        """
        if validity_days is None:
            # Use default for this source type
            validity_days = self.config.DEFAULT_VALIDITY_DAYS.get(evidence.source_type)

        if validity_days:
            evidence.validity_end = evidence.validity_start + timedelta(days=validity_days)
            logger.debug(f"Set validity period for evidence {evidence.id}: {validity_days} days")
        else:
            evidence.validity_end = None
            logger.debug(f"Set indefinite validity for evidence {evidence.id}")

        return evidence


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def is_evidence_recent(
    evidence: EvidenceNode,
    days_threshold: int = 365,
    reference_time: Optional[datetime] = None
) -> bool:
    """
    Check if evidence is recent (within threshold)

    Args:
        evidence: Evidence node
        days_threshold: Number of days to consider "recent"
        reference_time: Time to check against (default: now)

    Returns:
        True if evidence is within threshold days
    """
    reference_time = reference_time or datetime.utcnow()
    age_days = (reference_time - evidence.extraction_timestamp).days
    return age_days <= days_threshold


def get_evidence_age_days(
    evidence: EvidenceNode,
    reference_time: Optional[datetime] = None
) -> float:
    """
    Get age of evidence in days

    Args:
        evidence: Evidence node
        reference_time: Time to measure age from (default: now)

    Returns:
        Age in days (float)
    """
    reference_time = reference_time or datetime.utcnow()
    age_seconds = (reference_time - evidence.extraction_timestamp).total_seconds()
    return age_seconds / 86400


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    'TemporalConfig',
    'TemporalReasoner',
    'is_evidence_recent',
    'get_evidence_age_days',
]
