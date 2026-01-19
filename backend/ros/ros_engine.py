"""
ROS Engine - Research Opportunity Scoring

Main entry point for computing ROS scores for drug-disease pairs.

This is the PRIMARY API for Phase 6A ROS.

Usage:
    from ros import compute_ros

    score_result = compute_ros(
        drug_id="canonical_drug_id",
        disease_id="canonical_disease_id",
        graph_manager=graph,
        conflict_reasoner=conflict_reasoner
    )

Design:
- Calls AKGP query engine
- Calls conflict reasoning
- Extracts features
- Assembles final score
- Generates explanation
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from akgp.graph_manager import GraphManager
from akgp.conflict_reasoning import ConflictReasoner
from akgp.temporal import TemporalReasoner
from akgp.schema import NodeType

from ros.feature_extractors import (
    extract_evidence_strength,
    extract_evidence_diversity,
    extract_conflict_penalty,
    extract_recency_boost,
    extract_patent_risk_penalty
)
from ros.scoring_rules import ScoringWeights

logger = logging.getLogger(__name__)


# ==============================================================================
# ROS ENGINE
# ==============================================================================

class ROSEngine:
    """
    Research Opportunity Scoring Engine

    Computes deterministic, explainable opportunity scores for drug-disease pairs.

    Phase 6A: Heuristic scoring (no ML)
    Phase 6B: ML-enhanced scoring (future)
    """

    def __init__(
        self,
        graph_manager: GraphManager,
        conflict_reasoner: ConflictReasoner,
        temporal_reasoner: Optional[TemporalReasoner] = None
    ):
        """
        Initialize ROS engine

        Args:
            graph_manager: AKGP graph manager for evidence retrieval
            conflict_reasoner: Conflict reasoner from STEP 5
            temporal_reasoner: Optional temporal reasoner (uses default if None)
        """
        self.graph = graph_manager
        self.conflict_reasoner = conflict_reasoner
        self.temporal = temporal_reasoner or TemporalReasoner()

        logger.info("ROSEngine initialized (Phase 6A - Heuristic)")

    def compute_ros(
        self,
        drug_id: str,
        disease_id: str
    ) -> Dict[str, Any]:
        """
        Compute Research Opportunity Score for drug-disease pair

        This is the PRIMARY API for ROS.

        Args:
            drug_id: Canonical drug identifier (from AKGP graph)
            disease_id: Canonical disease identifier (from AKGP graph)

        Returns:
            ROS result dictionary:
            {
                "drug_id": str,
                "disease_id": str,
                "ros_score": float (0.0-10.0),
                "feature_breakdown": {
                    "evidence_strength": float,
                    "evidence_diversity": float,
                    "conflict_penalty": float,
                    "recency_boost": float,
                    "patent_risk_penalty": float
                },
                "conflict_summary": {
                    "has_conflict": bool,
                    "severity": str,
                    "dominant_evidence": str
                },
                "explanation": str,
                "metadata": {
                    "num_supporting_evidence": int,
                    "num_contradicting_evidence": int,
                    "num_suggesting_evidence": int,
                    "distinct_agents": list,
                    "computation_timestamp": str
                }
            }
        """
        logger.info(f"Computing ROS for drug={drug_id[:20]}..., disease={disease_id[:20]}...")

        # STEP 1: Get conflict analysis from STEP 5
        conflict_result = self.conflict_reasoner.explain_conflict(drug_id, disease_id)

        # STEP 2: Extract evidence lists
        supporting_evidence = conflict_result.get('supporting_evidence', [])
        contradicting_evidence = conflict_result.get('contradicting_evidence', [])
        # Note: supporting_evidence includes both SUPPORTS and SUGGESTS from conflict reasoning

        # Separate SUGGESTS from SUPPORTS if needed
        # For now, conflict_reasoner returns supporting_evidence = SUPPORTS + SUGGESTS combined
        # We'll use this combined list as "all positive evidence"

        # Get evidence counts
        evidence_count = conflict_result.get('evidence_count', {})
        num_supports = evidence_count.get('supports', 0)
        num_suggests = evidence_count.get('suggests', 0)
        num_contradicts = evidence_count.get('contradicts', 0)

        # Split supporting_evidence back into SUPPORTS and SUGGESTS based on counts
        # supporting_evidence list = SUPPORTS + SUGGESTS (in that order from conflict_reasoner)
        pure_supports = supporting_evidence[:num_supports]
        pure_suggests = supporting_evidence[num_supports:num_supports + num_suggests]

        # All evidence (for diversity calculation)
        all_evidence = supporting_evidence + contradicting_evidence

        # STEP 3: Extract features
        logger.debug("Extracting ROS features...")

        # Feature 1: Evidence Strength
        evidence_strength = extract_evidence_strength(
            supporting_evidence=pure_supports,
            suggesting_evidence=pure_suggests
        )

        # Feature 2: Evidence Diversity
        evidence_diversity = extract_evidence_diversity(all_evidence)

        # Feature 3: Conflict Penalty
        conflict_penalty = extract_conflict_penalty(conflict_result)

        # Feature 4: Recency Boost
        recency_boost = extract_recency_boost(
            supporting_evidence=pure_supports,
            suggesting_evidence=pure_suggests,
            temporal_reasoner=self.temporal
        )

        # Feature 5: Patent Risk Penalty
        patent_risk_penalty = extract_patent_risk_penalty(all_evidence)

        # STEP 4: Compute final score
        raw_score = (
            evidence_strength +
            evidence_diversity +
            conflict_penalty +  # This is negative or zero
            recency_boost +
            patent_risk_penalty  # This is negative or zero
        )

        # Clamp to [0, 10]
        final_score = max(ScoringWeights.MIN_SCORE, min(raw_score, ScoringWeights.MAX_SCORE))

        logger.info(f"ROS computed: {final_score:.2f}/10.0")

        # STEP 5: Generate explanation
        explanation = self._generate_explanation(
            evidence_strength=evidence_strength,
            evidence_diversity=evidence_diversity,
            conflict_penalty=conflict_penalty,
            recency_boost=recency_boost,
            patent_risk_penalty=patent_risk_penalty,
            final_score=final_score,
            conflict_result=conflict_result,
            all_evidence=all_evidence
        )

        # STEP 6: Assemble result
        # Extract distinct agents
        distinct_agents = list(set(e.get('agent_id', 'unknown') for e in all_evidence))

        # Conflict summary
        dominant_ev = conflict_result.get('dominant_evidence')
        conflict_summary = {
            "has_conflict": conflict_result.get('has_conflict', False),
            "severity": conflict_result.get('severity'),
            "dominant_evidence": dominant_ev.get('polarity', 'UNKNOWN') if dominant_ev else 'UNKNOWN'
        }

        result = {
            "drug_id": drug_id,
            "disease_id": disease_id,
            "ros_score": round(final_score, 2),
            "feature_breakdown": {
                "evidence_strength": round(evidence_strength, 2),
                "evidence_diversity": round(evidence_diversity, 2),
                "conflict_penalty": round(conflict_penalty, 2),
                "recency_boost": round(recency_boost, 2),
                "patent_risk_penalty": round(patent_risk_penalty, 2)
            },
            "conflict_summary": conflict_summary,
            "explanation": explanation,
            "metadata": {
                "num_supporting_evidence": num_supports,
                "num_contradicting_evidence": num_contradicts,
                "num_suggesting_evidence": num_suggests,
                "distinct_agents": distinct_agents,
                "computation_timestamp": datetime.utcnow().isoformat()
            }
        }

        return result

    def _generate_explanation(
        self,
        evidence_strength: float,
        evidence_diversity: float,
        conflict_penalty: float,
        recency_boost: float,
        patent_risk_penalty: float,
        final_score: float,
        conflict_result: Dict[str, Any],
        all_evidence: List[Dict[str, Any]]
    ) -> str:
        """
        Generate human-readable explanation for ROS score

        REQUIREMENT: Explanation must match numbers exactly (no hallucinations)

        Args:
            evidence_strength: Evidence strength score
            evidence_diversity: Diversity score
            conflict_penalty: Conflict penalty
            recency_boost: Recency boost
            patent_risk_penalty: Patent risk penalty
            final_score: Final ROS score
            conflict_result: Conflict reasoning result
            all_evidence: All evidence list

        Returns:
            Human-readable explanation string
        """
        parts = []

        # Overall score
        parts.append(f"Research Opportunity Score: {final_score:.1f}/10.0")

        # Evidence strength
        num_supports = conflict_result.get('evidence_count', {}).get('supports', 0)
        num_suggests = conflict_result.get('evidence_count', {}).get('suggests', 0)
        parts.append(
            f"Evidence Strength ({evidence_strength:.1f}/4.0): "
            f"{num_supports} supporting + {num_suggests} suggesting evidence sources."
        )

        # Diversity
        num_agents = len(set(e.get('agent_id') for e in all_evidence if e.get('agent_id')))
        parts.append(
            f"Evidence Diversity ({evidence_diversity:.1f}/2.0): "
            f"Evidence from {num_agents} distinct agent source(s)."
        )

        # Conflict
        if conflict_penalty < 0:
            severity = conflict_result.get('severity', 'UNKNOWN')
            parts.append(
                f"Conflict Penalty ({conflict_penalty:.1f}): "
                f"{severity} severity conflict detected between evidence sources."
            )
        else:
            parts.append("Conflict Penalty (0.0): No conflicts detected.")

        # Recency
        parts.append(
            f"Recency Boost ({recency_boost:.1f}/2.0): "
            f"Recent evidence indicates active research area."
        )

        # Patent risk
        if patent_risk_penalty < 0:
            num_patents = len([e for e in all_evidence if e.get('source_type') == 'patent'])
            parts.append(
                f"Patent Risk Penalty ({patent_risk_penalty:.1f}): "
                f"{num_patents} patent(s) detected, indicating IP complexity."
            )
        else:
            parts.append("Patent Risk Penalty (0.0): No active patents detected.")

        return " ".join(parts)


# ==============================================================================
# CONVENIENCE FUNCTION
# ==============================================================================

def compute_ros(
    drug_id: str,
    disease_id: str,
    graph_manager: GraphManager,
    conflict_reasoner: ConflictReasoner,
    temporal_reasoner: Optional[TemporalReasoner] = None
) -> Dict[str, Any]:
    """
    Convenience function to compute ROS without instantiating engine

    Args:
        drug_id: Canonical drug identifier
        disease_id: Canonical disease identifier
        graph_manager: AKGP graph manager
        conflict_reasoner: Conflict reasoner
        temporal_reasoner: Optional temporal reasoner

    Returns:
        ROS result dictionary
    """
    engine = ROSEngine(
        graph_manager=graph_manager,
        conflict_reasoner=conflict_reasoner,
        temporal_reasoner=temporal_reasoner
    )
    return engine.compute_ros(drug_id, disease_id)


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = ['ROSEngine', 'compute_ros']
