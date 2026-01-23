"""
AKGP Query Engine
High-level query interface for the knowledge graph

This module provides:
- Natural query interface for evidence retrieval
- Conflict-aware queries
- Temporal filtering
- Explainable results
- Query optimization

Design Philosophy:
- Return structured, explainable results
- Always include confidence and provenance
- Flag conflicts in results
- Rank by combined weight (quality + confidence + recency)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from akgp.schema import NodeType, SourceType, EvidenceNode
from akgp.graph_manager import GraphManager
from akgp.provenance import ProvenanceTracker
from akgp.temporal import TemporalReasoner
from akgp.conflict_resolution import ConflictDetector

logger = logging.getLogger(__name__)


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def _get_enum_value(value):
    """
    Helper to extract string value from enum or string (Pydantic v2 compatibility)

    In Pydantic v2 with use_enum_values=True, enum fields are automatically
    converted to their string values. This helper handles both enum objects
    and pre-converted strings.

    Args:
        value: Enum object or string value

    Returns:
        String value
    """
    if isinstance(value, str):
        return value
    return value.value if hasattr(value, 'value') else str(value)


# ==============================================================================
# QUERY ENGINE
# ==============================================================================

class QueryEngine:
    """
    High-level query engine for AKGP knowledge graph

    Provides natural query interface with automatic:
    - Evidence retrieval
    - Conflict detection
    - Temporal filtering
    - Ranking by combined weight
    - Explanation generation
    """

    def __init__(
        self,
        graph_manager: GraphManager,
        provenance_tracker: Optional[ProvenanceTracker] = None,
        temporal_reasoner: Optional[TemporalReasoner] = None,
        conflict_detector: Optional[ConflictDetector] = None
    ):
        """
        Initialize query engine

        Args:
            graph_manager: Graph manager instance
            provenance_tracker: Optional provenance tracker
            temporal_reasoner: Optional temporal reasoner
            conflict_detector: Optional conflict detector
        """
        self.graph = graph_manager
        self.provenance = provenance_tracker or ProvenanceTracker()
        self.temporal = temporal_reasoner or TemporalReasoner()
        self.conflict_detector = conflict_detector or ConflictDetector(self.temporal)

    def query_drug_disease_evidence(
        self,
        drug_name: str,
        disease_name: str,
        include_conflicts: bool = True,
        only_valid: bool = True
    ) -> Dict[str, Any]:
        """
        Query: "What evidence supports Drug X for Disease Y?"

        Args:
            drug_name: Drug name
            disease_name: Disease name
            include_conflicts: Whether to detect and include conflicts
            only_valid: Whether to filter to only temporally valid evidence

        Returns:
            Structured query result with evidence, conflicts, and explanations
        """
        logger.info(f"Querying evidence for {drug_name} → {disease_name}")

        # 1. Find Drug and Disease nodes
        drug_nodes = self.graph.find_nodes_by_name(drug_name, NodeType.DRUG)
        disease_nodes = self.graph.find_nodes_by_name(disease_name, NodeType.DISEASE)

        if not drug_nodes:
            return {
                "success": False,
                "error": f"Drug not found: {drug_name}",
                "drug_name": drug_name,
                "disease_name": disease_name
            }

        if not disease_nodes:
            return {
                "success": False,
                "error": f"Disease not found: {disease_name}",
                "drug_name": drug_name,
                "disease_name": disease_name
            }

        drug_id = drug_nodes[0]['id']
        disease_id = disease_nodes[0]['id']

        # 2. Find relationships between drug and disease
        drug_relationships = self.graph.get_relationships_for_node(drug_id, direction="outgoing")

        # Filter to relationships targeting this disease
        relevant_relationships = [
            rel for rel in drug_relationships
            if rel.get('target_id') == disease_id
        ]

        logger.info(f"Found {len(relevant_relationships)} relationships between {drug_name} and {disease_name}")

        # 3. Collect evidence from relationships
        evidence_list = []
        for rel in relevant_relationships:
            evidence_id = rel.get('evidence_id')
            if evidence_id:
                evidence_data = self.graph.get_node(evidence_id)
                if evidence_data and evidence_data.get('node_type') == 'Evidence':
                    try:
                        evidence_node = EvidenceNode(**evidence_data)
                        evidence_list.append(evidence_node)
                    except Exception as e:
                        logger.warning(f"Failed to parse evidence {evidence_id}: {e}")

        logger.info(f"Collected {len(evidence_list)} evidence nodes")

        # 4. Filter to valid evidence if requested
        if only_valid:
            evidence_list = self.temporal.filter_valid_evidence(evidence_list)
            logger.info(f"Filtered to {len(evidence_list)} valid evidence nodes")

        # 5. Detect conflicts if requested
        conflicts = []
        if include_conflicts and len(evidence_list) > 1:
            conflicts = self.conflict_detector.detect_conflicts(evidence_list, drug_name, disease_name)
            logger.info(f"Detected {len(conflicts)} conflicts")

        # 6. Rank evidence by combined weight
        ranked_evidence = self.temporal.sort_by_combined_weight(evidence_list)

        # 7. Build structured result
        evidence_summary = []
        for evidence, weight in ranked_evidence:
            provenance_chain = self.provenance.get_provenance(evidence.id)

            evidence_summary.append({
                "evidence_id": evidence.id,
                "summary": evidence.summary[:300],
                "source_type": _get_enum_value(evidence.source_type),
                "quality": _get_enum_value(evidence.quality),
                "confidence": evidence.confidence_score,
                "recency_weight": self.temporal.compute_recency_weight(evidence),
                "combined_weight": weight,
                "agent_name": evidence.agent_name,
                "raw_reference": evidence.raw_reference,
                "extraction_date": evidence.extraction_timestamp.isoformat(),
                "is_valid": self.temporal.is_valid(evidence)
            })

        # 8. Generate explanation
        explanation = self._generate_explanation(
            drug_name,
            disease_name,
            evidence_list,
            conflicts,
            ranked_evidence
        )

        return {
            "success": True,
            "drug_name": drug_name,
            "disease_name": disease_name,
            "total_evidence": len(evidence_list),
            "valid_evidence": len([e for e in evidence_list if self.temporal.is_valid(e)]),
            "evidence": evidence_summary,
            "conflicts": [c.dict() for c in conflicts],
            "has_conflicts": len(conflicts) > 0,
            "strongest_evidence": evidence_summary[0] if evidence_summary else None,
            "explanation": explanation
        }

    def query_conflicts(
        self,
        drug_name: Optional[str] = None,
        disease_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query: "Are there conflicting signals for Drug X and Disease Y?"

        Args:
            drug_name: Optional drug name filter
            disease_name: Optional disease name filter

        Returns:
            Conflict report with resolution recommendations
        """
        logger.info(f"Querying conflicts for {drug_name} → {disease_name}")

        # Get all evidence (filtered by drug/disease if specified)
        all_evidence = []

        if drug_name or disease_name:
            # Get filtered evidence via drug-disease query
            if drug_name and disease_name:
                result = self.query_drug_disease_evidence(drug_name, disease_name, include_conflicts=False)
                if result.get('success'):
                    # Reconstruct evidence nodes from summary
                    for ev_data in result.get('evidence', []):
                        evidence_data = self.graph.get_node(ev_data['evidence_id'])
                        if evidence_data:
                            all_evidence.append(EvidenceNode(**evidence_data))
        else:
            # Get all evidence from provenance tracker
            all_prov_chains = self.provenance.get_all_provenance()
            for chain in all_prov_chains.values():
                all_evidence.append(EvidenceNode(**chain.evidence_node))

        # Detect conflicts
        conflicts = self.conflict_detector.detect_conflicts(all_evidence, drug_name, disease_name)

        # Generate resolution recommendations for each conflict
        conflict_details = []
        for conflict in conflicts:
            # Get the two conflicting evidence nodes
            evidence1_data = self.graph.get_node(conflict.entity1_id)
            evidence2_data = self.graph.get_node(conflict.entity2_id)

            if evidence1_data and evidence2_data:
                evidence1 = EvidenceNode(**evidence1_data)
                evidence2 = EvidenceNode(**evidence2_data)

                resolution = self.conflict_detector.resolve_conflict(conflict, evidence1, evidence2)

                conflict_details.append({
                    "conflict": conflict.dict(),
                    "resolution": resolution
                })

        return {
            "success": True,
            "total_conflicts": len(conflicts),
            "conflicts": conflict_details,
            "summary": f"Found {len(conflicts)} conflicts" + (f" for {drug_name} → {disease_name}" if drug_name and disease_name else "")
        }

    def query_strongest_evidence(
        self,
        drug_name: str,
        disease_name: str,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Query: "What is the strongest evidence for Drug X treating Disease Y and why?"

        Args:
            drug_name: Drug name
            disease_name: Disease name
            top_k: Number of top evidence to return

        Returns:
            Top evidence with detailed explanations
        """
        logger.info(f"Querying strongest evidence for {drug_name} → {disease_name}")

        # Get all evidence
        result = self.query_drug_disease_evidence(drug_name, disease_name, include_conflicts=False)

        if not result.get('success'):
            return result

        # Get top K evidence
        top_evidence = result.get('evidence', [])[:top_k]

        # Generate detailed explanation for each
        detailed_evidence = []
        for ev in top_evidence:
            # Fetch full evidence node
            evidence_data = self.graph.get_node(ev['evidence_id'])
            if evidence_data:
                evidence_node = EvidenceNode(**evidence_data)

                # Calculate components
                quality_weight = {
                    'high': 0.9,
                    'medium': 0.7,
                    'low': 0.5
                }.get(_get_enum_value(evidence_node.quality), 0.7)

                recency_weight = self.temporal.compute_recency_weight(evidence_node)
                combined_weight = self.temporal.compute_combined_weight(evidence_node)

                # Generate explanation
                age_days = (datetime.utcnow() - evidence_node.extraction_timestamp).days

                explanation_parts = [
                    f"Source: {_get_enum_value(evidence_node.source_type).upper()} ({evidence_node.agent_name})",
                    f"Quality: {_get_enum_value(evidence_node.quality).upper()} (weight: {quality_weight:.2f})",
                    f"Confidence: {evidence_node.confidence_score:.2f}",
                    f"Recency: {age_days} days old (weight: {recency_weight:.2f})",
                    f"Combined weight: {combined_weight:.3f}",
                    f"Reference: {evidence_node.raw_reference}"
                ]

                detailed_evidence.append({
                    **ev,
                    "full_summary": evidence_node.summary,
                    "explanation_breakdown": explanation_parts,
                    "why_strong": f"This evidence ranks highly because: {_get_enum_value(evidence_node.quality)} quality ({quality_weight:.2f}), {evidence_node.confidence_score:.0%} confidence, and relatively recent ({age_days} days old, recency weight: {recency_weight:.2f})."
                })

        return {
            "success": True,
            "drug_name": drug_name,
            "disease_name": disease_name,
            "top_evidence": detailed_evidence,
            "total_evidence_available": len(result.get('evidence', []))
        }

    def query_by_source_type(
        self,
        source_type: SourceType,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Query all evidence from a specific source type

        Args:
            source_type: Source type (clinical, patent, literature, market)
            limit: Maximum number of results

        Returns:
            Evidence from this source type
        """
        logger.info(f"Querying evidence by source type: {source_type.value}")

        # Get evidence from provenance tracker
        evidence_chains = self.provenance.get_evidence_by_source_type(source_type)

        # Convert to evidence nodes
        evidence_list = [
            EvidenceNode(**chain.evidence_node)
            for chain in evidence_chains
        ]

        # Rank by combined weight
        ranked = self.temporal.sort_by_combined_weight(evidence_list)

        # Format results
        results = []
        for evidence, weight in ranked[:limit]:
            results.append({
                "evidence_id": evidence.id,
                "name": evidence.name,
                "summary": evidence.summary[:200],
                "agent_name": evidence.agent_name,
                "raw_reference": evidence.raw_reference,
                "quality": _get_enum_value(evidence.quality),
                "confidence": evidence.confidence_score,
                "combined_weight": weight,
                "extraction_date": evidence.extraction_timestamp.isoformat()
            })

        return {
            "success": True,
            "source_type": _get_enum_value(source_type),
            "total_evidence": len(evidence_list),
            "returned": len(results),
            "evidence": results
        }

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================

    def _generate_explanation(
        self,
        drug_name: str,
        disease_name: str,
        evidence_list: List[EvidenceNode],
        conflicts: List,
        ranked_evidence: List
    ) -> str:
        """Generate human-readable explanation of query results"""
        if not evidence_list:
            return f"No evidence found for {drug_name} treating {disease_name}."

        # Count by source type
        by_source = {}
        for evidence in evidence_list:
            st = _get_enum_value(evidence.source_type)
            by_source[st] = by_source.get(st, 0) + 1

        # Get strongest evidence
        strongest = ranked_evidence[0] if ranked_evidence else (None, 0)

        explanation_parts = [
            f"Found {len(evidence_list)} pieces of evidence for {drug_name} treating {disease_name}.",
            f"Sources: {', '.join(f'{count} {source}' for source, count in by_source.items())}."
        ]

        if strongest[0]:
            explanation_parts.append(
                f"Strongest evidence: {strongest[0]_get_enum_value(evidence_node.source_type)} from {strongest[0].agent_name} "
                f"(weight: {strongest[1]:.3f}, confidence: {strongest[0].confidence_score:.0%})."
            )

        if conflicts:
            explanation_parts.append(
                f"⚠️  Warning: {len(conflicts)} conflict(s) detected. Review conflicting evidence carefully."
            )

        return " ".join(explanation_parts)


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = ['QueryEngine']
