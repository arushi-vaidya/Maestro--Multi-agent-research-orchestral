"""
AKGP Conflict Reasoning Engine

Provides explainable, deterministic conflict analysis for drug-disease relationships.

DESIGN PRINCIPLES:
- Deterministic: Same inputs → same outputs
- Auditable: Every decision is traceable
- Explainable: Human-readable justifications
- Reviewer-proof: Evidence-based reasoning

STEP 5: Multi-Agent Conflict Reasoning
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import logging

from akgp.schema import EvidenceNode, RelationshipType, EvidenceQuality, SourceType, NodeType
from akgp.graph_manager import GraphManager
from akgp.provenance import ProvenanceTracker

logger = logging.getLogger(__name__)


# ==============================================================================
# ENUMS
# ==============================================================================

class ConflictSeverity(str, Enum):
    """
    Conflict severity classification

    LOW: Weak vs weak evidence (both LOW quality or low confidence)
    MEDIUM: Weak vs strong evidence (one HIGH quality, one LOW)
    HIGH: Strong vs strong evidence (both HIGH quality, true scientific disagreement)
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ==============================================================================
# CONFLICT REASONER
# ==============================================================================

class ConflictReasoner:
    """
    Explains, ranks, and justifies conflicting evidence in AKGP

    Transforms "we detect conflicts" into "we can explain why evidence conflicts
    and which evidence should be trusted more"
    """

    def __init__(
        self,
        graph_manager: GraphManager,
        provenance_tracker: Optional[ProvenanceTracker] = None
    ):
        """
        Initialize conflict reasoner

        Args:
            graph_manager: Graph manager for querying evidence
            provenance_tracker: Provenance tracker for evidence metadata
        """
        self.graph = graph_manager
        self.provenance = provenance_tracker or ProvenanceTracker()

    def explain_conflict(
        self,
        drug_id: str,
        disease_id: str
    ) -> Dict[str, Any]:
        """
        Explain conflict for a drug-disease pair

        This is the PRIMARY API for conflict reasoning. Returns:
        - Has conflict?
        - Conflict severity
        - Dominant evidence (which evidence should be trusted more)
        - Human-readable explanations
        - Provenance summary

        Args:
            drug_id: Canonical drug identifier
            disease_id: Canonical disease identifier

        Returns:
            Conflict explanation dictionary with structure:
            {
                "has_conflict": bool,
                "severity": "HIGH" | "MEDIUM" | "LOW" | None,
                "summary": str,
                "dominant_evidence": {
                    "evidence_id": str,
                    "reason": str,
                    "polarity": str
                },
                "supporting_evidence": List[Dict],
                "contradicting_evidence": List[Dict],
                "temporal_explanation": str,
                "provenance_summary": List[Dict],
                "evidence_count": {
                    "supports": int,
                    "contradicts": int,
                    "suggests": int
                }
            }
        """
        logger.info(f"Explaining conflict for drug={drug_id[:20]}..., disease={disease_id[:20]}...")

        # 1. Find all evidence for this drug-disease pair
        evidence_list = self._find_evidence_for_pair(drug_id, disease_id)

        if not evidence_list:
            return {
                "has_conflict": False,
                "severity": None,
                "summary": "No evidence found for this drug-disease pair.",
                "dominant_evidence": None,
                "supporting_evidence": [],
                "contradicting_evidence": [],
                "temporal_explanation": "No temporal data available.",
                "provenance_summary": [],
                "evidence_count": {"supports": 0, "contradicts": 0, "suggests": 0}
            }

        # 2. Classify evidence by polarity
        supports, contradicts, suggests = self._classify_by_polarity(evidence_list)

        evidence_count = {
            "supports": len(supports),
            "contradicts": len(contradicts),
            "suggests": len(suggests)
        }

        # 3. Check if conflict exists
        # SUGGESTS counts as weak support for conflict detection
        has_conflict = (len(supports) > 0 or len(suggests) > 0) and len(contradicts) > 0

        if not has_conflict:
            # No conflict - generate simple explanation
            dominant = self._get_dominant_evidence(supports + contradicts + suggests)
            return {
                "has_conflict": False,
                "severity": None,
                "summary": self._generate_no_conflict_summary(supports, contradicts, suggests),
                "dominant_evidence": self._format_evidence_summary(dominant) if dominant else None,
                "supporting_evidence": [self._format_evidence_summary(e) for e in supports],
                "contradicting_evidence": [self._format_evidence_summary(e) for e in contradicts],
                "temporal_explanation": "No conflict detected.",
                "provenance_summary": self._generate_provenance_summary(evidence_list),
                "evidence_count": evidence_count
            }

        # 4. Determine conflict severity
        severity = self._determine_severity(supports, contradicts, suggests)

        # 5. Determine dominant evidence
        dominant_evidence = self._determine_dominant_evidence(supports, contradicts, suggests)

        # 6. Generate human-readable explanations
        summary = self._generate_conflict_summary(supports, contradicts, suggests, dominant_evidence, severity)
        temporal_explanation = self._generate_temporal_explanation(supports, contradicts, suggests)

        # 7. Format provenance summary
        provenance_summary = self._generate_provenance_summary(evidence_list)

        return {
            "has_conflict": True,
            "severity": severity.value,
            "summary": summary,
            "dominant_evidence": {
                "evidence_id": dominant_evidence.id if hasattr(dominant_evidence, 'id') else "unknown",
                "reason": self._explain_dominance(dominant_evidence, supports, contradicts, suggests),
                "polarity": self._get_evidence_polarity(dominant_evidence, supports, contradicts, suggests)
            },
            "supporting_evidence": [self._format_evidence_summary(e) for e in supports + suggests],
            "contradicting_evidence": [self._format_evidence_summary(e) for e in contradicts],
            "temporal_explanation": temporal_explanation,
            "provenance_summary": provenance_summary,
            "evidence_count": evidence_count
        }

    # ==========================================================================
    # EVIDENCE RETRIEVAL
    # ==========================================================================

    def _find_evidence_for_pair(
        self,
        drug_id: str,
        disease_id: str
    ) -> List[Dict[str, Any]]:
        """
        Find all evidence nodes related to drug-disease pair

        This queries the graph for:
        - All Drug nodes with matching canonical_id
        - All Disease nodes with matching canonical_id
        - All relationships between them
        - Evidence nodes linked to those relationships

        Returns:
            List of evidence dictionaries with metadata
        """
        evidence_list = []

        # Find Drug nodes with this canonical ID
        drug_nodes = self.graph.find_nodes_by_type(NodeType.DRUG)
        matching_drugs = [n for n in drug_nodes if n.get('metadata', {}).get('canonical_id') == drug_id]

        # Find Disease nodes with this canonical ID
        disease_nodes = self.graph.find_nodes_by_type(NodeType.DISEASE)
        matching_diseases = [n for n in disease_nodes if n.get('metadata', {}).get('canonical_id') == disease_id]

        if not matching_drugs or not matching_diseases:
            logger.debug("No matching drug or disease nodes found")
            return []

        # Get relationships for each drug node
        for drug_node in matching_drugs:
            drug_node_id = drug_node.get('id')
            if not drug_node_id:
                continue

            # Get outgoing relationships from drug
            relationships = self.graph.get_relationships_for_node(drug_node_id, direction="outgoing")

            for rel in relationships:
                # Check if relationship targets one of our disease nodes
                target_id = rel.get('target_id')
                if not any(d.get('id') == target_id for d in matching_diseases):
                    continue

                # Get evidence node for this relationship
                evidence_id = rel.get('evidence_id')
                if not evidence_id:
                    continue

                # Get evidence node
                evidence_node = self.graph.get_node(evidence_id)
                if evidence_node:
                    # Add relationship type for polarity determination
                    evidence_node['relationship_type'] = rel.get('relationship_type')
                    evidence_list.append(evidence_node)

        logger.debug(f"Found {len(evidence_list)} evidence nodes for drug-disease pair")
        return evidence_list

    # ==========================================================================
    # EVIDENCE CLASSIFICATION
    # ==========================================================================

    def _classify_by_polarity(
        self,
        evidence_list: List[Dict[str, Any]]
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Classify evidence by relationship polarity

        Returns:
            (supports, contradicts, suggests) tuple of evidence lists
        """
        supports = []
        contradicts = []
        suggests = []

        for evidence in evidence_list:
            rel_type = evidence.get('relationship_type', '')

            if rel_type == RelationshipType.TREATS.value:
                supports.append(evidence)
            elif rel_type == RelationshipType.INVESTIGATED_FOR.value:
                # INVESTIGATED_FOR can be negative evidence (failed trials)
                # Check metadata for actual polarity
                metadata = evidence.get('metadata', {})
                if metadata.get('polarity') == 'CONTRADICTS':
                    contradicts.append(evidence)
                else:
                    suggests.append(evidence)
            elif rel_type == RelationshipType.SUGGESTS.value:
                suggests.append(evidence)
            else:
                # Unknown - treat as suggests
                suggests.append(evidence)

        logger.debug(f"Classified: {len(supports)} SUPPORTS, {len(contradicts)} CONTRADICTS, {len(suggests)} SUGGESTS")
        return supports, contradicts, suggests

    # ==========================================================================
    # DOMINANT EVIDENCE DETERMINATION
    # ==========================================================================

    def _determine_dominant_evidence(
        self,
        supports: List[Dict],
        contradicts: List[Dict],
        suggests: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Determine which evidence dominates

        Ranking criteria (in order):
        1. Quality: HIGH > MEDIUM > LOW
        2. Confidence: Higher confidence wins
        3. Temporal: Newer evidence wins

        Note: SUGGESTS is treated as weak supporting evidence

        Returns:
            Dominant evidence dictionary
        """
        if suggests is None:
            suggests = []

        all_evidence = supports + contradicts + suggests

        if not all_evidence:
            return None

        # Sort by quality, confidence, and timestamp
        sorted_evidence = sorted(
            all_evidence,
            key=lambda e: (
                self._quality_to_rank(e.get('quality', 'MEDIUM')),
                e.get('confidence_score', 0.0),
                self._parse_timestamp(e.get('extraction_timestamp'))
            ),
            reverse=True
        )

        return sorted_evidence[0]

    def _get_dominant_evidence(self, evidence_list: List[Dict]) -> Optional[Dict]:
        """Get dominant evidence from any list"""
        if not evidence_list:
            return None

        sorted_evidence = sorted(
            evidence_list,
            key=lambda e: (
                self._quality_to_rank(e.get('quality', 'MEDIUM')),
                e.get('confidence_score', 0.0),
                self._parse_timestamp(e.get('extraction_timestamp'))
            ),
            reverse=True
        )

        return sorted_evidence[0]

    def _quality_to_rank(self, quality: str) -> int:
        """Convert quality enum to numeric rank for sorting"""
        rank_map = {
            EvidenceQuality.HIGH.value: 3,
            EvidenceQuality.MEDIUM.value: 2,
            EvidenceQuality.LOW.value: 1,
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1
        }
        return rank_map.get(quality, 2)  # Default to MEDIUM

    def _parse_timestamp(self, timestamp) -> datetime:
        """Parse timestamp for comparison"""
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp)
            except:
                return datetime.min
        else:
            return datetime.min

    # ==========================================================================
    # CONFLICT SEVERITY
    # ==========================================================================

    def _determine_severity(
        self,
        supports: List[Dict],
        contradicts: List[Dict],
        suggests: List[Dict] = None
    ) -> ConflictSeverity:
        """
        Determine conflict severity based on evidence quality

        Rules:
        - HIGH: Both sides have HIGH quality evidence
        - MEDIUM: One side has HIGH, other has MEDIUM/LOW
        - LOW: Both sides have MEDIUM or LOW quality evidence

        Note: SUGGESTS is treated as weak supporting evidence
        """
        if suggests is None:
            suggests = []

        # Get max quality for each side (includes SUGGESTS as weak support)
        all_supporting = supports + suggests
        supports_quality = max(
            [self._quality_to_rank(e.get('quality', 'MEDIUM')) for e in all_supporting],
            default=0
        )
        contradicts_quality = max(
            [self._quality_to_rank(e.get('quality', 'MEDIUM')) for e in contradicts],
            default=0
        )

        # HIGH severity: both sides have HIGH quality (rank 3)
        if supports_quality == 3 and contradicts_quality == 3:
            return ConflictSeverity.HIGH

        # MEDIUM severity: one side has HIGH quality, other has less
        if (supports_quality == 3 and contradicts_quality < 3) or \
           (supports_quality < 3 and contradicts_quality == 3):
            return ConflictSeverity.MEDIUM

        # LOW severity: both sides have MEDIUM or LOW quality
        return ConflictSeverity.LOW

    # ==========================================================================
    # EXPLANATION GENERATION
    # ==========================================================================

    def _generate_conflict_summary(
        self,
        supports: List[Dict],
        contradicts: List[Dict],
        suggests: List[Dict],
        dominant: Dict[str, Any],
        severity: ConflictSeverity
    ) -> str:
        """
        Generate human-readable conflict summary

        Example: "Early Phase-2 trials (2018) failed, but multiple Phase-4 trials
                  (2023-2024) demonstrate efficacy. Newer, higher-quality clinical
                  evidence dominates."

        Note: SUGGESTS is treated as weak supporting evidence
        """
        if suggests is None:
            suggests = []

        supports_count = len(supports) + len(suggests)  # SUGGESTS counts as weak support
        contradicts_count = len(contradicts)

        # Get temporal info
        supports_years = self._extract_years(supports)
        contradicts_years = self._extract_years(contradicts)

        # Get quality info
        dominant_quality = dominant.get('quality', 'MEDIUM')
        dominant_year = self._extract_years([dominant])[0] if dominant else "unknown"

        # Build summary
        summary_parts = []

        # Conflict description
        summary_parts.append(
            f"Conflict detected: {supports_count} evidence source(s) support treatment, "
            f"{contradicts_count} evidence source(s) contradict."
        )

        # Temporal description
        if contradicts_years and supports_years:
            if min(contradicts_years) < min(supports_years):
                summary_parts.append(
                    f"Earlier evidence ({min(contradicts_years)}) suggested failure, "
                    f"but more recent evidence ({max(supports_years)}) demonstrates efficacy."
                )
            else:
                summary_parts.append(
                    f"Recent evidence conflicts with earlier findings."
                )

        # Dominant evidence explanation
        dominant_polarity = self._get_evidence_polarity(dominant, supports, contradicts, suggests)
        summary_parts.append(
            f"{dominant_quality}-quality {dominant_polarity.lower()} evidence "
            f"from {dominant_year} dominates due to superior quality and recency."
        )

        return " ".join(summary_parts)

    def _generate_no_conflict_summary(
        self,
        supports: List[Dict],
        contradicts: List[Dict],
        suggests: List[Dict]
    ) -> str:
        """Generate summary when no conflict exists"""
        total = len(supports) + len(contradicts) + len(suggests)

        if len(supports) > 0 and len(contradicts) == 0:
            return f"No conflict: All {len(supports)} evidence source(s) support treatment efficacy."
        elif len(contradicts) > 0 and len(supports) == 0:
            return f"No conflict: All {len(contradicts)} evidence source(s) suggest treatment inefficacy."
        elif len(suggests) > 0 and len(supports) == 0 and len(contradicts) == 0:
            return f"No conflict: {len(suggests)} speculative evidence source(s) found, no definitive findings."
        else:
            return f"No conflict detected among {total} evidence source(s)."

    def _generate_temporal_explanation(
        self,
        supports: List[Dict],
        contradicts: List[Dict],
        suggests: List[Dict] = None
    ) -> str:
        """
        Generate temporal explanation

        Example: "Contradicting evidence from 2018 (Phase 2 trial) is older than
                  supporting evidence from 2023-2024 (Phase 4 trials). Newer evidence
                  carries more weight in conflict resolution."

        Note: SUGGESTS is treated as weak supporting evidence
        """
        if suggests is None:
            suggests = []

        all_supporting = supports + suggests
        supports_years = self._extract_years(all_supporting)
        contradicts_years = self._extract_years(contradicts)

        if not supports_years or not contradicts_years:
            return "Insufficient temporal data for comparison."

        supports_range = f"{min(supports_years)}-{max(supports_years)}" if len(supports_years) > 1 else str(supports_years[0])
        contradicts_range = f"{min(contradicts_years)}-{max(contradicts_years)}" if len(contradicts_years) > 1 else str(contradicts_years[0])

        if min(supports_years) > max(contradicts_years):
            return (
                f"Supporting evidence ({supports_range}) is newer than contradicting evidence ({contradicts_range}). "
                f"Temporal recency favors supporting evidence."
            )
        elif min(contradicts_years) > max(supports_years):
            return (
                f"Contradicting evidence ({contradicts_range}) is newer than supporting evidence ({supports_range}). "
                f"Temporal recency favors contradicting evidence."
            )
        else:
            return (
                f"Evidence spans overlapping time periods (supports: {supports_range}, contradicts: {contradicts_range}). "
                f"Quality and confidence are primary discriminators."
            )

    def _explain_dominance(
        self,
        dominant: Dict[str, Any],
        supports: List[Dict],
        contradicts: List[Dict],
        suggests: List[Dict] = None
    ) -> str:
        """
        Explain why dominant evidence dominates

        Returns human-readable explanation of ranking decision

        Note: SUGGESTS is treated as weak supporting evidence
        """
        if suggests is None:
            suggests = []

        quality = dominant.get('quality', 'MEDIUM')
        confidence = dominant.get('confidence_score', 0.0)
        year = self._extract_years([dominant])[0] if dominant else "unknown"

        reasons = []

        # Quality reason
        other_evidence = [e for e in supports + contradicts + suggests if e != dominant]
        other_qualities = [self._quality_to_rank(e.get('quality', 'MEDIUM')) for e in other_evidence]
        dominant_quality_rank = self._quality_to_rank(quality)

        if other_qualities and dominant_quality_rank > max(other_qualities):
            reasons.append(f"highest quality ({quality})")
        else:
            reasons.append(f"{quality} quality")

        # Confidence reason
        other_confidences = [e.get('confidence_score', 0.0) for e in other_evidence]
        if other_confidences and confidence > max(other_confidences):
            reasons.append(f"highest confidence ({confidence:.2f})")

        # Temporal reason
        other_years = self._extract_years(other_evidence)
        if other_years and year > max(other_years):
            reasons.append(f"most recent ({year})")

        reason_text = ", ".join(reasons) if reasons else "default selection"
        return f"This evidence dominates due to: {reason_text}."

    def _get_evidence_polarity(
        self,
        evidence: Dict[str, Any],
        supports: List[Dict],
        contradicts: List[Dict],
        suggests: List[Dict] = None
    ) -> str:
        """Determine if evidence is SUPPORTS, CONTRADICTS, or SUGGESTS"""
        if suggests is None:
            suggests = []

        if evidence in supports:
            return "SUPPORTS"
        elif evidence in contradicts:
            return "CONTRADICTS"
        else:
            return "SUGGESTS"

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================

    def _extract_years(self, evidence_list: List[Dict]) -> List[int]:
        """Extract years from evidence timestamps"""
        years = []
        for evidence in evidence_list:
            timestamp = evidence.get('extraction_timestamp')
            if timestamp:
                dt = self._parse_timestamp(timestamp)
                if dt != datetime.min:
                    years.append(dt.year)
        return sorted(years)

    def _format_evidence_summary(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Format evidence for output"""
        return {
            "evidence_id": evidence.get('id', 'unknown'),
            "name": evidence.get('name', 'Unknown Evidence'),
            "source": evidence.get('source', 'Unknown'),
            "agent_id": evidence.get('agent_id', 'unknown'),
            "quality": evidence.get('quality', 'MEDIUM'),
            "confidence_score": evidence.get('confidence_score', 0.0),
            "source_type": evidence.get('source_type', 'unknown'),
            "extraction_timestamp": str(evidence.get('extraction_timestamp', '')),
            "raw_reference": evidence.get('raw_reference', '')
        }

    def _generate_provenance_summary(self, evidence_list: List[Dict]) -> List[Dict[str, Any]]:
        """
        Generate provenance summary

        Returns list of provenance entries showing:
        - Agent that produced evidence
        - Source (API, database, etc.)
        - Timestamp
        - Reference (NCT ID, patent number, etc.)
        """
        provenance = []
        for evidence in evidence_list:
            provenance.append({
                "agent_id": evidence.get('agent_id', 'unknown'),
                "agent_name": evidence.get('agent_name', 'Unknown Agent'),
                "api_source": evidence.get('api_source', 'Unknown'),
                "raw_reference": evidence.get('raw_reference', ''),
                "extraction_timestamp": str(evidence.get('extraction_timestamp', '')),
                "quality": evidence.get('quality', 'MEDIUM'),
                "confidence": evidence.get('confidence_score', 0.0)
            })
        return provenance


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = ['ConflictReasoner', 'ConflictSeverity']
