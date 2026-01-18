"""
AKGP Conflict Resolution
Deterministic conflict detection and resolution for evidence

This module provides:
- Conflict detection between evidence nodes
- Conflict recording (not overwriting)
- Weight-based resolution recommendations
- Explainable conflict analysis

Design Philosophy:
- Record all conflicts, never overwrite
- Newer, higher-quality evidence gets higher weight
- Conflicts are queryable
- Deterministic rules (no ML)
- Provide explanations for all conflicts
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

from akgp.schema import EvidenceNode, Relationship, Conflict, SourceType, EvidenceQuality
from akgp.temporal import TemporalReasoner

logger = logging.getLogger(__name__)


# ==============================================================================
# CONFLICT TYPES
# ==============================================================================

class ConflictType:
    """Enumeration of conflict types"""
    EFFICACY_CONTRADICTION = "efficacy_contradiction"  # One says works, other says doesn't
    SAFETY_CONTRADICTION = "safety_contradiction"  # Conflicting safety signals
    DOSAGE_DISCREPANCY = "dosage_discrepancy"  # Different dosing recommendations
    POPULATION_MISMATCH = "population_mismatch"  # Different target populations
    TEMPORAL_INVALIDATION = "temporal_invalidation"  # Newer evidence invalidates older
    SOURCE_DISAGREEMENT = "source_disagreement"  # Different sources, different conclusions


# ==============================================================================
# CONFLICT DETECTOR
# ==============================================================================

class ConflictDetector:
    """
    Detects conflicts between evidence nodes using deterministic rules
    """

    def __init__(self, temporal_reasoner: Optional[TemporalReasoner] = None):
        """
        Initialize conflict detector

        Args:
            temporal_reasoner: Optional temporal reasoner (creates new if not provided)
        """
        self.temporal_reasoner = temporal_reasoner or TemporalReasoner()
        self._detected_conflicts: List[Conflict] = []

    def detect_conflicts(
        self,
        evidence_list: List[EvidenceNode],
        drug_name: Optional[str] = None,
        disease_name: Optional[str] = None
    ) -> List[Conflict]:
        """
        Detect conflicts within a list of evidence

        Args:
            evidence_list: List of evidence nodes to check
            drug_name: Optional drug name to filter context
            disease_name: Optional disease name to filter context

        Returns:
            List of detected conflicts
        """
        conflicts = []

        # Compare each pair of evidence
        for i in range(len(evidence_list)):
            for j in range(i + 1, len(evidence_list)):
                evidence1 = evidence_list[i]
                evidence2 = evidence_list[j]

                # Check for conflicts
                conflict = self._check_pair_for_conflict(evidence1, evidence2)
                if conflict:
                    conflicts.append(conflict)
                    self._detected_conflicts.append(conflict)

        logger.info(f"Detected {len(conflicts)} conflicts in {len(evidence_list)} evidence nodes")
        return conflicts

    def _check_pair_for_conflict(
        self,
        evidence1: EvidenceNode,
        evidence2: EvidenceNode
    ) -> Optional[Conflict]:
        """
        Check if two evidence nodes conflict

        Args:
            evidence1: First evidence node
            evidence2: Second evidence node

        Returns:
            Conflict object if conflict detected, None otherwise
        """
        # Rule 1: Check for efficacy contradictions in summary text
        conflict = self._check_efficacy_contradiction(evidence1, evidence2)
        if conflict:
            return conflict

        # Rule 2: Check for temporal invalidation
        conflict = self._check_temporal_invalidation(evidence1, evidence2)
        if conflict:
            return conflict

        # Rule 3: Check for source-level disagreements
        conflict = self._check_source_disagreement(evidence1, evidence2)
        if conflict:
            return conflict

        return None

    def _check_efficacy_contradiction(
        self,
        evidence1: EvidenceNode,
        evidence2: EvidenceNode
    ) -> Optional[Conflict]:
        """Check for efficacy contradictions (positive vs. negative results)"""
        # Keywords indicating positive results
        positive_keywords = ["effective", "improved", "successful", "benefit", "positive", "treats"]

        # Keywords indicating negative results
        negative_keywords = ["ineffective", "failed", "unsuccessful", "no benefit", "negative", "terminated"]

        summary1_lower = evidence1.summary.lower()
        summary2_lower = evidence2.summary.lower()

        # Check if one is positive and the other is negative
        is_positive1 = any(kw in summary1_lower for kw in positive_keywords)
        is_negative1 = any(kw in summary1_lower for kw in negative_keywords)

        is_positive2 = any(kw in summary2_lower for kw in positive_keywords)
        is_negative2 = any(kw in summary2_lower for kw in negative_keywords)

        if (is_positive1 and is_negative2) or (is_negative1 and is_positive2):
            # Determine severity based on confidence scores
            severity = self._assess_conflict_severity(evidence1, evidence2)

            return Conflict(
                entity1_id=evidence1.id,
                entity2_id=evidence2.id,
                entity_type="evidence",
                conflict_type=ConflictType.EFFICACY_CONTRADICTION,
                severity=severity,
                explanation=f"Efficacy contradiction detected: Evidence {evidence1.id} suggests positive results while {evidence2.id} suggests negative results."
            )

        return None

    def _check_temporal_invalidation(
        self,
        evidence1: EvidenceNode,
        evidence2: EvidenceNode
    ) -> Optional[Conflict]:
        """Check if newer evidence invalidates older evidence"""
        # If both are from clinical trials and one is significantly newer
        if evidence1.source_type == SourceType.CLINICAL and evidence2.source_type == SourceType.CLINICAL:
            time_diff_days = abs((evidence1.extraction_timestamp - evidence2.extraction_timestamp).days)

            # If more than 2 years apart, check for phase progression
            if time_diff_days > 730:
                # Newer evidence from later phase might invalidate earlier phase
                newer = evidence1 if evidence1.extraction_timestamp > evidence2.extraction_timestamp else evidence2
                older = evidence2 if newer == evidence1 else evidence1

                # Check metadata for phase information
                newer_phase = newer.metadata.get("phase", "")
                older_phase = older.metadata.get("phase", "")

                if "phase 3" in newer_phase.lower() and "phase 1" in older_phase.lower():
                    return Conflict(
                        entity1_id=older.id,
                        entity2_id=newer.id,
                        entity_type="evidence",
                        conflict_type=ConflictType.TEMPORAL_INVALIDATION,
                        severity="medium",
                        explanation=f"Phase 3 trial ({newer.id}) may supersede earlier Phase 1 results ({older.id})."
                    )

        return None

    def _check_source_disagreement(
        self,
        evidence1: EvidenceNode,
        evidence2: EvidenceNode
    ) -> Optional[Conflict]:
        """Check for disagreements between different source types"""
        # If clinical trial shows failure but patent suggests use
        if (evidence1.source_type == SourceType.CLINICAL and evidence2.source_type == SourceType.PATENT) or \
           (evidence1.source_type == SourceType.PATENT and evidence2.source_type == SourceType.CLINICAL):

            clinical = evidence1 if evidence1.source_type == SourceType.CLINICAL else evidence2
            patent = evidence2 if clinical == evidence1 else evidence1

            # Check for negative clinical results
            if any(kw in clinical.summary.lower() for kw in ["failed", "ineffective", "terminated"]):
                return Conflict(
                    entity1_id=clinical.id,
                    entity2_id=patent.id,
                    entity_type="evidence",
                    conflict_type=ConflictType.SOURCE_DISAGREEMENT,
                    severity="high",
                    explanation=f"Clinical trial ({clinical.id}) shows negative results despite patent filing ({patent.id})."
                )

        return None

    def _assess_conflict_severity(
        self,
        evidence1: EvidenceNode,
        evidence2: EvidenceNode
    ) -> str:
        """
        Assess severity of conflict based on evidence confidence and quality

        Returns:
            "low", "medium", or "high"
        """
        # High severity if both have high confidence
        if evidence1.confidence_score > 0.7 and evidence2.confidence_score > 0.7:
            return "high"

        # Medium severity if at least one has medium confidence
        if evidence1.confidence_score > 0.5 or evidence2.confidence_score > 0.5:
            return "medium"

        return "low"

    def resolve_conflict(
        self,
        conflict: Conflict,
        evidence1: EvidenceNode,
        evidence2: EvidenceNode
    ) -> Dict[str, Any]:
        """
        Provide resolution recommendation for a conflict

        Args:
            conflict: Conflict to resolve
            evidence1: First evidence node
            evidence2: Second evidence node

        Returns:
            Resolution recommendation dictionary
        """
        # Compute combined weights
        weight1 = self.temporal_reasoner.compute_combined_weight(evidence1)
        weight2 = self.temporal_reasoner.compute_combined_weight(evidence2)

        # Determine recommended evidence based on weight
        if weight1 > weight2:
            recommended = evidence1
            recommended_weight = weight1
            alternative = evidence2
            alternative_weight = weight2
        else:
            recommended = evidence2
            recommended_weight = weight2
            alternative = evidence1
            alternative_weight = weight1

        # Generate explanation
        quality_names = {
            EvidenceQuality.HIGH: "high",
            EvidenceQuality.MEDIUM: "medium",
            EvidenceQuality.LOW: "low"
        }

        explanation_parts = [
            f"Recommendation: Prefer evidence {recommended.id}",
            f"Reason: Higher combined weight ({recommended_weight:.3f} vs {alternative_weight:.3f})",
            f"Quality: {quality_names.get(recommended.quality, 'unknown')} (vs {quality_names.get(alternative.quality, 'unknown')})",
            f"Recency: {(datetime.utcnow() - recommended.extraction_timestamp).days} days old (vs {(datetime.utcnow() - alternative.extraction_timestamp).days} days)",
            f"Confidence: {recommended.confidence_score:.2f} (vs {alternative.confidence_score:.2f})"
        ]

        return {
            "conflict_id": conflict.id,
            "recommended_evidence_id": recommended.id,
            "recommended_weight": recommended_weight,
            "alternative_evidence_id": alternative.id,
            "alternative_weight": alternative_weight,
            "explanation": " | ".join(explanation_parts),
            "weight_difference": abs(weight1 - weight2)
        }

    def get_all_conflicts(self) -> List[Conflict]:
        """Get all detected conflicts"""
        return self._detected_conflicts.copy()

    def get_unresolved_conflicts(self) -> List[Conflict]:
        """Get all unresolved conflicts"""
        return [c for c in self._detected_conflicts if not c.resolved]


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def analyze_conflict_patterns(conflicts: List[Conflict]) -> Dict[str, Any]:
    """
    Analyze patterns in detected conflicts

    Args:
        conflicts: List of conflicts

    Returns:
        Dictionary with conflict pattern analysis
    """
    if not conflicts:
        return {
            "total_conflicts": 0,
            "by_type": {},
            "by_severity": {},
            "resolution_rate": 0.0
        }

    # Count by type
    by_type = {}
    for conflict in conflicts:
        ct = conflict.conflict_type
        by_type[ct] = by_type.get(ct, 0) + 1

    # Count by severity
    by_severity = {}
    for conflict in conflicts:
        sev = conflict.severity
        by_severity[sev] = by_severity.get(sev, 0) + 1

    # Calculate resolution rate
    resolved_count = sum(1 for c in conflicts if c.resolved)
    resolution_rate = resolved_count / len(conflicts) if conflicts else 0.0

    return {
        "total_conflicts": len(conflicts),
        "by_type": by_type,
        "by_severity": by_severity,
        "resolved_count": resolved_count,
        "unresolved_count": len(conflicts) - resolved_count,
        "resolution_rate": resolution_rate
    }


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    'ConflictType',
    'ConflictDetector',
    'analyze_conflict_patterns',
]
