"""
AKGP Provenance Tracking
Handles provenance tracking for evidence in the knowledge graph

This module provides:
- Provenance chain construction
- Audit trail generation
- Source quality assessment
- Evidence lineage tracking

Design Philosophy:
- Every piece of evidence must be traceable to its source
- Provenance is immutable once recorded
- Support multiple levels of provenance (agent -> API -> raw data)
- Enable auditability for regulatory compliance
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from dataclasses import dataclass

from akgp.schema import EvidenceNode, SourceType, EvidenceQuality

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
# PROVENANCE DATA STRUCTURES
# ==============================================================================

@dataclass
class ProvenanceChain:
    """Represents a complete provenance chain for a piece of evidence"""

    # Original evidence
    evidence_id: str
    evidence_node: Dict[str, Any]

    # Agent information
    agent_name: str
    agent_id: str

    # Source information
    api_source: Optional[str]
    raw_reference: str  # NCT ID, patent number, URL, etc.

    # Timestamps
    extraction_timestamp: datetime
    ingestion_timestamp: datetime

    # Quality metadata
    source_type: SourceType
    quality: EvidenceQuality
    confidence_score: float

    # Additional metadata
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "evidence_id": self.evidence_id,
            "evidence_node": self.evidence_node,
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "api_source": self.api_source,
            "raw_reference": self.raw_reference,
            "extraction_timestamp": self.extraction_timestamp.isoformat(),
            "ingestion_timestamp": self.ingestion_timestamp.isoformat(),
            "source_type": self.source_type,
            "quality": self.quality,
            "confidence_score": self.confidence_score,
            "metadata": self.metadata
        }


# ==============================================================================
# PROVENANCE TRACKER
# ==============================================================================

class ProvenanceTracker:
    """
    Tracks and validates provenance for evidence nodes

    This class ensures that all evidence in AKGP has complete, auditable provenance.
    """

    def __init__(self):
        """Initialize provenance tracker"""
        self._provenance_chains: Dict[str, ProvenanceChain] = {}
        self._audit_log: List[Dict[str, Any]] = []

    def record_provenance(
        self,
        evidence_node: EvidenceNode,
        ingestion_timestamp: Optional[datetime] = None
    ) -> ProvenanceChain:
        """
        Record provenance for an evidence node

        Args:
            evidence_node: Evidence node to track
            ingestion_timestamp: When the evidence was ingested (default: now)

        Returns:
            ProvenanceChain instance

        Raises:
            ValueError: If evidence node is missing required provenance fields
        """
        # Validate required provenance fields
        self._validate_provenance(evidence_node)

        # Create provenance chain
        chain = ProvenanceChain(
            evidence_id=evidence_node.id,
            evidence_node=evidence_node.dict(),
            agent_name=evidence_node.agent_name,
            agent_id=evidence_node.agent_id,
            api_source=evidence_node.api_source,
            raw_reference=evidence_node.raw_reference,
            extraction_timestamp=evidence_node.extraction_timestamp,
            ingestion_timestamp=ingestion_timestamp or datetime.utcnow(),
            source_type=evidence_node.source_type,
            quality=evidence_node.quality,
            confidence_score=evidence_node.confidence_score,
            metadata=evidence_node.metadata
        )

        # Store provenance chain
        self._provenance_chains[evidence_node.id] = chain

        # Log to audit trail
        self._log_audit_event(
            event_type="provenance_recorded",
            evidence_id=evidence_node.id,
            agent_name=evidence_node.agent_name,
            source_type=evidence_node.source_type,
            raw_reference=evidence_node.raw_reference
        )

        logger.info(f"Recorded provenance for evidence {evidence_node.id} from {evidence_node.agent_name}")
        return chain

    def get_provenance(self, evidence_id: str) -> Optional[ProvenanceChain]:
        """
        Retrieve provenance chain for an evidence node

        Args:
            evidence_id: Evidence node ID

        Returns:
            ProvenanceChain or None if not found
        """
        return self._provenance_chains.get(evidence_id)

    def get_all_provenance(self) -> Dict[str, ProvenanceChain]:
        """Get all recorded provenance chains"""
        return self._provenance_chains.copy()

    def verify_provenance(self, evidence_id: str) -> bool:
        """
        Verify that provenance exists and is complete for an evidence node

        Args:
            evidence_id: Evidence node ID

        Returns:
            True if provenance is complete and valid
        """
        chain = self.get_provenance(evidence_id)
        if not chain:
            logger.warning(f"No provenance found for evidence {evidence_id}")
            return False

        # Check required fields are present and non-empty
        required_fields = [
            chain.agent_name,
            chain.agent_id,
            chain.raw_reference,
            chain.source_type,
            chain.quality
        ]

        if not all(required_fields):
            logger.warning(f"Incomplete provenance for evidence {evidence_id}")
            return False

        return True

    def get_evidence_by_agent(self, agent_id: str) -> List[ProvenanceChain]:
        """
        Get all evidence from a specific agent

        Args:
            agent_id: Agent ID (e.g., "clinical", "patent", "market")

        Returns:
            List of provenance chains from this agent
        """
        return [
            chain for chain in self._provenance_chains.values()
            if chain.agent_id == agent_id
        ]

    def get_evidence_by_source_type(self, source_type: SourceType) -> List[ProvenanceChain]:
        """
        Get all evidence from a specific source type

        Args:
            source_type: Source type (clinical, patent, literature, market)

        Returns:
            List of provenance chains of this type
        """
        return [
            chain for chain in self._provenance_chains.values()
            if chain.source_type == source_type
        ]

    def get_evidence_by_quality(self, quality: EvidenceQuality) -> List[ProvenanceChain]:
        """
        Get all evidence of a specific quality level

        Args:
            quality: Quality level (high, medium, low)

        Returns:
            List of provenance chains with this quality
        """
        return [
            chain for chain in self._provenance_chains.values()
            if chain.quality == quality
        ]

    def generate_audit_report(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate an audit report for provenance

        Args:
            start_time: Filter events after this time
            end_time: Filter events before this time

        Returns:
            Audit report dictionary
        """
        # Filter audit log by time
        filtered_events = self._audit_log
        if start_time:
            filtered_events = [e for e in filtered_events if e["timestamp"] >= start_time]
        if end_time:
            filtered_events = [e for e in filtered_events if e["timestamp"] <= end_time]

        # Count by agent
        agent_counts = {}
        for chain in self._provenance_chains.values():
            agent_counts[chain.agent_name] = agent_counts.get(chain.agent_name, 0) + 1

        # Count by source type
        source_type_counts = {}
        for chain in self._provenance_chains.values():
            st = _get_enum_value(chain.source_type)
            source_type_counts[st] = source_type_counts.get(st, 0) + 1

        # Count by quality
        quality_counts = {}
        for chain in self._provenance_chains.values():
            q = _get_enum_value(chain.quality)
            quality_counts[q] = quality_counts.get(q, 0) + 1

        # Average confidence by agent
        agent_confidence = {}
        agent_confidence_counts = {}
        for chain in self._provenance_chains.values():
            if chain.agent_name not in agent_confidence:
                agent_confidence[chain.agent_name] = 0
                agent_confidence_counts[chain.agent_name] = 0
            agent_confidence[chain.agent_name] += chain.confidence_score
            agent_confidence_counts[chain.agent_name] += 1

        for agent in agent_confidence:
            agent_confidence[agent] /= agent_confidence_counts[agent]

        return {
            "total_evidence": len(self._provenance_chains),
            "total_audit_events": len(filtered_events),
            "evidence_by_agent": agent_counts,
            "evidence_by_source_type": source_type_counts,
            "evidence_by_quality": quality_counts,
            "average_confidence_by_agent": agent_confidence,
            "audit_events": filtered_events[-100:]  # Last 100 events
        }

    # ==========================================================================
    # PRIVATE METHODS
    # ==========================================================================

    def _validate_provenance(self, evidence_node: EvidenceNode):
        """
        Validate that evidence node has all required provenance fields

        Args:
            evidence_node: Evidence node to validate

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = {
            "agent_name": evidence_node.agent_name,
            "agent_id": evidence_node.agent_id,
            "raw_reference": evidence_node.raw_reference,
            "source_type": evidence_node.source_type,
            "extraction_timestamp": evidence_node.extraction_timestamp
        }

        missing_fields = [name for name, value in required_fields.items() if not value]

        if missing_fields:
            raise ValueError(
                f"Evidence node {evidence_node.id} is missing required provenance fields: {missing_fields}"
            )

    def _log_audit_event(
        self,
        event_type: str,
        evidence_id: str,
        agent_name: str,
        source_type: SourceType,
        raw_reference: str
    ):
        """Log an audit event"""
        event = {
            "timestamp": datetime.utcnow(),
            "event_type": event_type,
            "evidence_id": evidence_id,
            "agent_name": agent_name,
            "source_type": _get_enum_value(source_type),
            "raw_reference": raw_reference
        }
        self._audit_log.append(event)

    def get_audit_trail(self, evidence_id: str) -> List[Dict[str, Any]]:
        """
        Get audit trail for a specific piece of evidence

        Args:
            evidence_id: Evidence ID

        Returns:
            List of audit events for this evidence
        """
        return [
            event for event in self._audit_log
            if event["evidence_id"] == evidence_id
        ]


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def assess_source_quality(
    source_type: SourceType,
    raw_reference: str,
    metadata: Optional[Dict[str, Any]] = None
) -> EvidenceQuality:
    """
    Deterministically assess evidence quality based on source type and metadata

    Args:
        source_type: Type of source (clinical, patent, literature, market)
        raw_reference: Raw reference string
        metadata: Optional metadata for more nuanced assessment

    Returns:
        EvidenceQuality (HIGH, MEDIUM, LOW)

    Rules:
    - Clinical trials:
        - HIGH: Phase 3/4, completed trials
        - MEDIUM: Phase 2, recruiting trials
        - LOW: Phase 1, early stage
    - Patents:
        - HIGH: Granted patents
        - MEDIUM: Published applications
        - LOW: Patent searches
    - Literature:
        - HIGH: Peer-reviewed journals
        - MEDIUM: Preprints, conference papers
        - LOW: Abstracts only
    - Market:
        - HIGH: Tier 1 sources (IQVIA, EvaluatePharma)
        - MEDIUM: Industry reports
        - LOW: Web sources, news articles
    """
    metadata = metadata or {}

    if source_type == SourceType.CLINICAL:
        phase = metadata.get("phase", "").lower()
        status = metadata.get("status", "").lower()

        if "phase 3" in phase or "phase 4" in phase:
            if "completed" in status:
                return EvidenceQuality.HIGH
            else:
                return EvidenceQuality.MEDIUM
        elif "phase 2" in phase:
            return EvidenceQuality.MEDIUM
        else:
            return EvidenceQuality.LOW

    elif source_type == SourceType.PATENT:
        # Check if granted (has patent number starting with US followed by digits)
        if raw_reference.startswith("US") and any(char.isdigit() for char in raw_reference):
            return EvidenceQuality.HIGH
        else:
            return EvidenceQuality.MEDIUM

    elif source_type == SourceType.LITERATURE:
        source_name = metadata.get("source", "").lower()
        if any(journal in source_name for journal in ["nature", "science", "lancet", "nejm"]):
            return EvidenceQuality.HIGH
        elif "arxiv" in source_name or "biorxiv" in source_name:
            return EvidenceQuality.MEDIUM
        else:
            return EvidenceQuality.LOW

    elif source_type == SourceType.MARKET:
        source_name = metadata.get("data_provider", "").lower()
        if any(provider in source_name for provider in ["iqvia", "evaluatepharma", "globaldata"]):
            return EvidenceQuality.HIGH
        elif "report" in source_name:
            return EvidenceQuality.MEDIUM
        else:
            return EvidenceQuality.LOW

    # Default to MEDIUM if unable to determine
    return EvidenceQuality.MEDIUM


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    'ProvenanceChain',
    'ProvenanceTracker',
    'assess_source_quality',
]
