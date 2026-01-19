"""
AKGP Ingestion API
Ingests agent outputs into the knowledge graph

This module provides:
- Clean ingestion APIs for Clinical, Patent, and Market agents
- Automatic node and relationship creation
- Provenance tracking integration
- Conflict detection during ingestion
- Batch ingestion support

Design Philosophy:
- Accept structured agent outputs (don't parse raw text)
- Automatically create Drug/Disease nodes if they don't exist
- Link evidence to entities via relationships
- Run conflict detection after ingestion
- Return ingestion summary with statistics
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from uuid import uuid4

from akgp.schema import (
    DrugNode, DiseaseNode, EvidenceNode, TrialNode, PatentNode, MarketSignalNode,
    Relationship, NodeType, RelationshipType, SourceType, EvidenceQuality
)
from akgp.graph_manager import GraphManager
from akgp.provenance import ProvenanceTracker, assess_source_quality
from akgp.temporal import TemporalReasoner
from akgp.conflict_resolution import ConflictDetector
from normalization.common import NormalizedEvidence, Polarity

logger = logging.getLogger(__name__)


# ==============================================================================
# INGESTION ENGINE
# ==============================================================================

class IngestionEngine:
    """
    Handles ingestion of agent outputs into AKGP knowledge graph
    """

    def __init__(
        self,
        graph_manager: GraphManager,
        provenance_tracker: Optional[ProvenanceTracker] = None,
        temporal_reasoner: Optional[TemporalReasoner] = None,
        conflict_detector: Optional[ConflictDetector] = None
    ):
        """
        Initialize ingestion engine

        Args:
            graph_manager: Graph manager instance
            provenance_tracker: Optional provenance tracker (creates new if not provided)
            temporal_reasoner: Optional temporal reasoner (creates new if not provided)
            conflict_detector: Optional conflict detector (creates new if not provided)
        """
        self.graph = graph_manager
        self.provenance = provenance_tracker or ProvenanceTracker()
        self.temporal = temporal_reasoner or TemporalReasoner()
        self.conflict_detector = conflict_detector or ConflictDetector(self.temporal)

    def ingest_clinical_trial(
        self,
        trial_data: Dict[str, Any],
        agent_name: str = "Clinical Trials Agent",
        agent_id: str = "clinical"
    ) -> Dict[str, Any]:
        """
        Ingest clinical trial data from Clinical Agent

        Args:
            trial_data: Clinical trial data from agent
                Expected fields:
                - nct_id: NCT ID
                - title: Trial title
                - summary: Trial summary
                - interventions: List of drug names
                - conditions: List of disease names
                - phase: Trial phase
                - status: Trial status
                - confidence_score: (optional) Confidence score

        Returns:
            Ingestion summary with created node IDs
        """
        logger.info(f"Ingesting clinical trial: {trial_data.get('nct_id', 'Unknown')}")

        created_nodes = []
        created_relationships = []

        # 1. Create Trial node
        trial_node = TrialNode(
            name=trial_data.get('title', f"Trial {trial_data['nct_id']}"),
            source=agent_name,
            nct_id=trial_data['nct_id'],
            phase=trial_data.get('phase'),
            status=trial_data.get('status'),
            interventions=trial_data.get('interventions', []),
            conditions=trial_data.get('conditions', [])
        )
        trial_id = self.graph.create_node(trial_node)
        created_nodes.append(trial_id)

        # 2. Create Evidence node
        evidence_node = EvidenceNode(
            name=f"Clinical Evidence: {trial_data['nct_id']}",
            source=agent_name,
            agent_name=agent_name,
            agent_id=agent_id,
            api_source="ClinicalTrials.gov",
            raw_reference=trial_data['nct_id'],
            source_type=SourceType.CLINICAL,
            quality=assess_source_quality(SourceType.CLINICAL, trial_data['nct_id'], trial_data),
            confidence_score=trial_data.get('confidence_score', 0.7),
            summary=trial_data.get('summary', ''),
            metadata=trial_data
        )

        # Set temporal validity
        evidence_node = self.temporal.set_validity_period(evidence_node)

        evidence_id = self.graph.create_node(evidence_node)
        created_nodes.append(evidence_id)

        # Track provenance
        self.provenance.record_provenance(evidence_node)

        # 3. Create Drug nodes and relationships
        for drug_name in trial_data.get('interventions', []):
            drug_node, drug_id = self._get_or_create_drug(drug_name, agent_name)
            created_nodes.append(drug_id)

            # Create INVESTIGATED_FOR relationships to diseases
            for disease_name in trial_data.get('conditions', []):
                disease_node, disease_id = self._get_or_create_disease(disease_name, agent_name)
                created_nodes.append(disease_id)

                # Drug -> Disease relationship
                rel = Relationship(
                    relationship_type=RelationshipType.INVESTIGATED_FOR,
                    source_id=drug_id,
                    target_id=disease_id,
                    evidence_id=evidence_id,
                    agent_id=agent_id,
                    confidence=evidence_node.confidence_score,
                    source_type=SourceType.CLINICAL
                )
                rel_id = self.graph.create_relationship(rel)
                created_relationships.append(rel_id)

        logger.info(f"Ingested clinical trial {trial_data['nct_id']}: {len(created_nodes)} nodes, {len(created_relationships)} relationships")

        return {
            "success": True,
            "nct_id": trial_data['nct_id'],
            "created_nodes": created_nodes,
            "created_relationships": created_relationships,
            "evidence_id": evidence_id
        }

    def ingest_patent(
        self,
        patent_data: Dict[str, Any],
        agent_name: str = "Patent Intelligence Agent",
        agent_id: str = "patent"
    ) -> Dict[str, Any]:
        """
        Ingest patent data from Patent Agent

        Args:
            patent_data: Patent data from agent
                Expected fields:
                - patent_number: Patent number
                - title: Patent title
                - abstract: Patent abstract
                - assignees: List of assignee organizations
                - drugs: List of drug names (extracted from claims)
                - indications: List of disease names (extracted from claims)
                - confidence_score: (optional) Confidence score

        Returns:
            Ingestion summary with created node IDs
        """
        logger.info(f"Ingesting patent: {patent_data.get('patent_number', 'Unknown')}")

        created_nodes = []
        created_relationships = []

        # 1. Create Patent node
        patent_node = PatentNode(
            name=patent_data.get('title', f"Patent {patent_data['patent_number']}"),
            source=agent_name,
            patent_number=patent_data['patent_number'],
            assignees=patent_data.get('assignees', []),
            patent_title=patent_data.get('title', ''),
            abstract=patent_data.get('abstract')
        )
        patent_id = self.graph.create_node(patent_node)
        created_nodes.append(patent_id)

        # 2. Create Evidence node
        evidence_node = EvidenceNode(
            name=f"Patent Evidence: {patent_data['patent_number']}",
            source=agent_name,
            agent_name=agent_name,
            agent_id=agent_id,
            api_source="USPTO PatentsView",
            raw_reference=patent_data['patent_number'],
            source_type=SourceType.PATENT,
            quality=assess_source_quality(SourceType.PATENT, patent_data['patent_number'], patent_data),
            confidence_score=patent_data.get('confidence_score', 0.6),
            summary=patent_data.get('abstract', '')[:500],
            metadata=patent_data
        )

        # Set temporal validity
        evidence_node = self.temporal.set_validity_period(evidence_node)

        evidence_id = self.graph.create_node(evidence_node)
        created_nodes.append(evidence_id)

        # Track provenance
        self.provenance.record_provenance(evidence_node)

        # 3. Create Drug-Disease relationships from patent claims
        for drug_name in patent_data.get('drugs', []):
            drug_node, drug_id = self._get_or_create_drug(drug_name, agent_name)
            created_nodes.append(drug_id)

            for disease_name in patent_data.get('indications', []):
                disease_node, disease_id = self._get_or_create_disease(disease_name, agent_name)
                created_nodes.append(disease_id)

                # Drug -> Disease relationship (SUGGESTS, not TREATS)
                rel = Relationship(
                    relationship_type=RelationshipType.SUGGESTS,
                    source_id=drug_id,
                    target_id=disease_id,
                    evidence_id=evidence_id,
                    agent_id=agent_id,
                    confidence=evidence_node.confidence_score,
                    source_type=SourceType.PATENT
                )
                rel_id = self.graph.create_relationship(rel)
                created_relationships.append(rel_id)

        logger.info(f"Ingested patent {patent_data['patent_number']}: {len(created_nodes)} nodes, {len(created_relationships)} relationships")

        return {
            "success": True,
            "patent_number": patent_data['patent_number'],
            "created_nodes": created_nodes,
            "created_relationships": created_relationships,
            "evidence_id": evidence_id
        }

    def ingest_market_signal(
        self,
        market_data: Dict[str, Any],
        agent_name: str = "Market Intelligence Agent",
        agent_id: str = "market"
    ) -> Dict[str, Any]:
        """
        Ingest market intelligence from Market Agent

        Args:
            market_data: Market data from agent
                Expected fields:
                - drug_name: Drug name
                - indication: Disease/indication
                - market_size: Market size in USD
                - forecast: Market forecast data
                - source_url: Source URL
                - confidence_score: (optional) Confidence score

        Returns:
            Ingestion summary with created node IDs
        """
        logger.info(f"Ingesting market signal for: {market_data.get('drug_name', 'Unknown')}")

        created_nodes = []
        created_relationships = []

        # 1. Create MarketSignal node
        market_node = MarketSignalNode(
            name=f"Market Signal: {market_data.get('drug_name', 'Unknown')}",
            source=agent_name,
            signal_type=market_data.get('signal_type', 'forecast'),
            market_size=market_data.get('market_size'),
            growth_rate=market_data.get('growth_rate'),
            data_provider=market_data.get('data_provider')
        )
        market_id = self.graph.create_node(market_node)
        created_nodes.append(market_id)

        # 2. Create Evidence node
        # Ensure summary and raw_reference are not empty (Pydantic v2 and provenance validation require non-empty strings)
        summary = market_data.get('summary', '') or f"Market signal for {market_data.get('drug_name', 'drug')}: {market_data.get('signal_type', 'data')}"
        raw_reference = market_data.get('source_url', '') or market_data.get('source', '') or f"Market data from {agent_name}"

        evidence_node = EvidenceNode(
            name=f"Market Evidence: {market_data.get('drug_name', 'Unknown')}",
            source=agent_name,
            agent_name=agent_name,
            agent_id=agent_id,
            api_source=market_data.get('data_provider', 'Web Search'),
            raw_reference=raw_reference,
            source_type=SourceType.MARKET,
            quality=assess_source_quality(SourceType.MARKET, raw_reference, market_data),
            confidence_score=market_data.get('confidence_score', 0.5),
            summary=summary,
            metadata=market_data
        )

        # Set temporal validity (market data expires faster)
        evidence_node = self.temporal.set_validity_period(evidence_node, validity_days=730)  # 2 years

        evidence_id = self.graph.create_node(evidence_node)
        created_nodes.append(evidence_id)

        # Track provenance
        self.provenance.record_provenance(evidence_node)

        # 3. Create Drug-Disease relationship
        if market_data.get('drug_name') and market_data.get('indication'):
            drug_node, drug_id = self._get_or_create_drug(market_data['drug_name'], agent_name)
            disease_node, disease_id = self._get_or_create_disease(market_data['indication'], agent_name)

            created_nodes.extend([drug_id, disease_id])

            # Drug -> Disease relationship (SUGGESTS commercial viability)
            rel = Relationship(
                relationship_type=RelationshipType.SUGGESTS,
                source_id=drug_id,
                target_id=disease_id,
                evidence_id=evidence_id,
                agent_id=agent_id,
                confidence=evidence_node.confidence_score,
                source_type=SourceType.MARKET
            )
            rel_id = self.graph.create_relationship(rel)
            created_relationships.append(rel_id)

        logger.info(f"Ingested market signal: {len(created_nodes)} nodes, {len(created_relationships)} relationships")

        return {
            "success": True,
            "created_nodes": created_nodes,
            "created_relationships": created_relationships,
            "evidence_id": evidence_id
        }

    def ingest_evidence(
        self,
        normalized_evidence: NormalizedEvidence
    ) -> Dict[str, Any]:
        """
        Ingest normalized evidence from normalization layer

        THIS IS THE SINGLE INGESTION GATE - ALL agent outputs flow through here.

        Args:
            normalized_evidence: NormalizedEvidence from parser (parse_clinical_evidence, etc.)
                Contains:
                - evidence_node: Complete EvidenceNode with provenance
                - drug_id: Canonical drug identifier
                - disease_id: Canonical disease identifier
                - polarity: SUPPORTS/CONTRADICTS/SUGGESTS

        Returns:
            Ingestion summary with created node IDs

        Note:
            The evidence_node is already complete with:
            - Temporal validity set by normalization layer
            - Quality determined by parser
            - Confidence score calculated
            - Provenance metadata (agent_id, agent_name, raw_reference)
        """
        evidence_node = normalized_evidence.evidence_node
        drug_id = normalized_evidence.drug_id
        disease_id = normalized_evidence.disease_id
        polarity = normalized_evidence.polarity

        logger.info(
            f"Ingesting normalized evidence: {evidence_node.name} "
            f"(drug={drug_id[:20]}..., disease={disease_id[:20]}..., polarity={polarity})"
        )

        created_nodes = []
        created_relationships = []

        # 1. Store polarity in evidence metadata for conflict reasoning
        if not hasattr(evidence_node, 'metadata') or evidence_node.metadata is None:
            evidence_node.metadata = {}
        evidence_node.metadata['polarity'] = polarity

        # 2. Create Evidence node in graph
        evidence_graph_id = self.graph.create_node(evidence_node)
        created_nodes.append(evidence_graph_id)

        # 3. Track provenance
        self.provenance.record_provenance(evidence_node)

        # 4. Extract drug/disease names from metadata
        # Clinical parser uses "interventions" and "conditions"
        # Other parsers may use "drug_mentions" and "disease_mentions"
        drug_mentions = (
            evidence_node.metadata.get("drug_mentions") or
            evidence_node.metadata.get("interventions") or
            evidence_node.metadata.get("drugs") or
            []
        )
        disease_mentions = (
            evidence_node.metadata.get("disease_mentions") or
            evidence_node.metadata.get("conditions") or
            evidence_node.metadata.get("indications") or
            []
        )

        if not drug_mentions or not disease_mentions:
            logger.warning(
                f"Evidence {evidence_node.name} missing drug/disease mentions in metadata. "
                f"Cannot create relationships."
            )
            return {
                "success": True,
                "evidence_id": evidence_graph_id,
                "created_nodes": created_nodes,
                "created_relationships": [],
                "warning": "No drug/disease mentions found - evidence stored but not linked"
            }

        # Take primary drug and disease (first mention)
        primary_drug = drug_mentions[0]
        primary_disease = disease_mentions[0]

        # 5. Create or find Drug node
        drug_node, drug_graph_id = self._get_or_create_drug(
            primary_drug,
            source=evidence_node.source
        )
        created_nodes.append(drug_graph_id)

        # Store canonical ID in drug node metadata for future reference
        # Always update metadata to include canonical_id
        if not hasattr(drug_node, 'metadata') or drug_node.metadata is None:
            drug_node.metadata = {}
        if 'canonical_id' not in drug_node.metadata:
            drug_node.metadata['canonical_id'] = drug_id
            # Update the node in the graph
            self.graph.update_node(drug_graph_id, {'metadata': drug_node.metadata})

        # 6. Create or find Disease node
        disease_node, disease_graph_id = self._get_or_create_disease(
            primary_disease,
            source=evidence_node.source
        )
        created_nodes.append(disease_graph_id)

        # Store canonical ID in disease node metadata for future reference
        # Always update metadata to include canonical_id
        if not hasattr(disease_node, 'metadata') or disease_node.metadata is None:
            disease_node.metadata = {}
        if 'canonical_id' not in disease_node.metadata:
            disease_node.metadata['canonical_id'] = disease_id
            # Update the node in the graph
            self.graph.update_node(disease_graph_id, {'metadata': disease_node.metadata})

        # 7. Map polarity to RelationshipType
        # Note: CONTRADICTS polarity doesn't create drug-disease relationship
        # (CONTRADICTS is for evidence-to-evidence relationships)
        relationship_type_map = {
            Polarity.SUPPORTS: RelationshipType.TREATS,  # Strong positive evidence
            Polarity.CONTRADICTS: RelationshipType.INVESTIGATED_FOR,  # Negative trial results (still investigated)
            Polarity.SUGGESTS: RelationshipType.SUGGESTS  # Weak/speculative evidence
        }

        relationship_type = relationship_type_map.get(polarity, RelationshipType.SUGGESTS)

        # 8. Create Drug → Disease relationship
        rel = Relationship(
            relationship_type=relationship_type,
            source_id=drug_graph_id,
            target_id=disease_graph_id,
            evidence_id=evidence_graph_id,
            agent_id=evidence_node.agent_id,
            confidence=evidence_node.confidence_score,
            source_type=evidence_node.source_type
        )
        rel_id = self.graph.create_relationship(rel)
        created_relationships.append(rel_id)

        logger.info(
            f"Successfully ingested evidence: {evidence_node.name} "
            f"({relationship_type.value}: {primary_drug} → {primary_disease})"
        )

        return {
            "success": True,
            "evidence_id": evidence_graph_id,
            "created_nodes": created_nodes,
            "created_relationships": created_relationships,
            "drug_id": drug_id,
            "disease_id": disease_id,
            "polarity": polarity,
            "relationship_type": relationship_type.value
        }

    def ingest_batch(
        self,
        items: List[Tuple[str, Dict[str, Any]]],
        detect_conflicts: bool = True
    ) -> Dict[str, Any]:
        """
        Batch ingest multiple items

        Args:
            items: List of (item_type, item_data) tuples
                   item_type: "clinical", "patent", or "market"
            detect_conflicts: Whether to run conflict detection after ingestion

        Returns:
            Batch ingestion summary
        """
        results = {
            "clinical": [],
            "patent": [],
            "market": [],
            "total_nodes": 0,
            "total_relationships": 0,
            "conflicts": []
        }

        for item_type, item_data in items:
            try:
                if item_type == "clinical":
                    result = self.ingest_clinical_trial(item_data)
                    results["clinical"].append(result)
                elif item_type == "patent":
                    result = self.ingest_patent(item_data)
                    results["patent"].append(result)
                elif item_type == "market":
                    result = self.ingest_market_signal(item_data)
                    results["market"].append(result)
                else:
                    logger.warning(f"Unknown item type: {item_type}")
                    continue

                results["total_nodes"] += len(result.get("created_nodes", []))
                results["total_relationships"] += len(result.get("created_relationships", []))

            except Exception as e:
                logger.error(f"Failed to ingest {item_type} item: {e}")

        # Run conflict detection if requested
        if detect_conflicts:
            # Get all evidence nodes
            all_evidence = self.provenance.get_all_provenance()
            evidence_nodes = [
                EvidenceNode(**chain.evidence_node)
                for chain in all_evidence.values()
            ]

            conflicts = self.conflict_detector.detect_conflicts(evidence_nodes)
            results["conflicts"] = [c.dict() for c in conflicts]

        logger.info(f"Batch ingestion complete: {results['total_nodes']} nodes, {results['total_relationships']} relationships, {len(results['conflicts'])} conflicts")

        return results

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================

    def _get_or_create_drug(self, drug_name: str, source: str) -> Tuple[DrugNode, str]:
        """Get existing drug node or create new one"""
        # Search for existing drug
        existing = self.graph.find_nodes_by_name(drug_name, NodeType.DRUG)

        if existing:
            drug_id = existing[0]['id']
            drug_node = DrugNode(**existing[0])
            logger.debug(f"Found existing drug: {drug_name} ({drug_id})")
        else:
            # Create new drug node
            drug_node = DrugNode(
                name=drug_name,
                source=source
            )
            drug_id = self.graph.create_node(drug_node)
            logger.debug(f"Created new drug: {drug_name} ({drug_id})")

        return drug_node, drug_id

    def _get_or_create_disease(self, disease_name: str, source: str) -> Tuple[DiseaseNode, str]:
        """Get existing disease node or create new one"""
        # Search for existing disease
        existing = self.graph.find_nodes_by_name(disease_name, NodeType.DISEASE)

        if existing:
            disease_id = existing[0]['id']
            disease_node = DiseaseNode(**existing[0])
            logger.debug(f"Found existing disease: {disease_name} ({disease_id})")
        else:
            # Create new disease node
            disease_node = DiseaseNode(
                name=disease_name,
                source=source
            )
            disease_id = self.graph.create_node(disease_node)
            logger.debug(f"Created new disease: {disease_name} ({disease_id})")

        return disease_node, disease_id


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = ['IngestionEngine']
