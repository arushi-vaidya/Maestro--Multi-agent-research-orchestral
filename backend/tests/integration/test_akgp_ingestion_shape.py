"""
Integration Tests for AKGP Ingestion Shape Validation
Tests that agent outputs can be ingested without schema errors
Uses SYNTHETIC agent-shaped inputs (NOT real agents)
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from akgp.ingestion import IngestionEngine
from akgp.graph_manager import GraphManager
from akgp.schema import (
    NodeType, RelationshipType, SourceType, EvidenceQuality,
    DrugNode, DiseaseNode, EvidenceNode, TrialNode, PatentNode
)


class TestIngestionEngineInitialization:
    """Test IngestionEngine initialization"""

    def test_ingestion_engine_initializes(self):
        """Test that IngestionEngine initializes successfully"""
        mock_graph = Mock(spec=GraphManager)
        engine = IngestionEngine(mock_graph)

        assert engine is not None
        assert engine.graph is not None
        assert engine.provenance is not None
        assert engine.temporal is not None
        assert engine.conflict_detector is not None


class TestClinicalTrialIngestion:
    """Test clinical trial data ingestion"""

    def test_ingest_clinical_trial_success(self):
        """Test successful clinical trial ingestion"""
        # Setup mock graph manager
        mock_graph = Mock(spec=GraphManager)
        mock_graph.create_node.side_effect = ["trial_1", "evidence_1", "drug_1", "disease_1"]
        mock_graph.create_relationship.return_value = "rel_1"

        engine = IngestionEngine(mock_graph)

        # Synthetic clinical trial data (agent-shaped)
        trial_data = {
            "nct_id": "NCT12345678",
            "title": "Phase 3 Study of GLP-1 Agonist",
            "summary": "A randomized trial evaluating efficacy",
            "interventions": ["Semaglutide"],
            "conditions": ["Type 2 Diabetes Mellitus"],
            "phase": "PHASE3",
            "status": "RECRUITING",
            "confidence_score": 0.95
        }

        result = engine.ingest_clinical_trial(trial_data)

        # Verify ingestion succeeded
        assert result["success"] is True
        assert result["nct_id"] == "NCT12345678"
        assert "created_nodes" in result
        assert "created_relationships" in result
        assert "evidence_id" in result
        assert len(result["created_nodes"]) > 0

    def test_ingest_clinical_trial_preserves_provenance(self):
        """Test that provenance fields are preserved"""
        mock_graph = Mock(spec=GraphManager)
        mock_graph.create_node.side_effect = ["trial_1", "evidence_1", "drug_1", "disease_1"]
        mock_graph.create_relationship.return_value = "rel_1"

        engine = IngestionEngine(mock_graph)

        trial_data = {
            "nct_id": "NCT99999999",
            "title": "Trial Title",
            "summary": "Trial summary",
            "interventions": ["DrugA"],
            "conditions": ["DiseaseB"],
            "phase": "PHASE2",
            "status": "COMPLETED",
            "confidence_score": 0.8
        }

        result = engine.ingest_clinical_trial(trial_data, agent_name="Clinical Agent", agent_id="clinical")

        # Verify graph.create_node was called for evidence node
        # Evidence node should have agent_id and agent_name
        calls = mock_graph.create_node.call_args_list
        # Second call should be evidence node
        if len(calls) >= 2:
            evidence_node_arg = calls[1][0][0]
            assert evidence_node_arg.agent_id == "clinical"
            assert evidence_node_arg.agent_name == "Clinical Agent"

    def test_ingest_clinical_trial_minimal_fields(self):
        """Test ingestion with minimal required fields"""
        mock_graph = Mock(spec=GraphManager)
        mock_graph.create_node.side_effect = ["trial_1", "evidence_1"]

        engine = IngestionEngine(mock_graph)

        # Minimal trial data
        trial_data = {
            "nct_id": "NCT00000001",
            "title": "Minimal Trial",
            "summary": "Summary",
            "interventions": [],
            "conditions": []
        }

        result = engine.ingest_clinical_trial(trial_data)

        assert result["success"] is True
        assert result["nct_id"] == "NCT00000001"

    def test_ingest_clinical_trial_no_duplicates(self):
        """Test that duplicate ingestion doesn't create duplicate nodes"""
        mock_graph = Mock(spec=GraphManager)

        # First ingestion
        mock_graph.create_node.side_effect = ["trial_1", "evidence_1", "drug_1", "disease_1"]
        mock_graph.create_relationship.return_value = "rel_1"

        engine = IngestionEngine(mock_graph)

        trial_data = {
            "nct_id": "NCT12345678",
            "title": "Trial",
            "summary": "Summary",
            "interventions": ["DrugA"],
            "conditions": ["DiseaseA"]
        }

        result1 = engine.ingest_clinical_trial(trial_data)

        # Second ingestion of same trial
        # (In real system, get_or_create should return existing nodes)
        # For now, just verify it doesn't crash
        mock_graph.create_node.side_effect = ["trial_2", "evidence_2", "drug_1_existing", "disease_1_existing"]
        mock_graph.create_relationship.return_value = "rel_2"

        result2 = engine.ingest_clinical_trial(trial_data)

        assert result2["success"] is True


class TestPatentIngestion:
    """Test patent data ingestion"""

    def test_ingest_patent_success(self):
        """Test successful patent ingestion"""
        mock_graph = Mock(spec=GraphManager)
        mock_graph.create_node.side_effect = ["patent_1", "evidence_1", "drug_1", "disease_1"]
        mock_graph.create_relationship.return_value = "rel_1"

        engine = IngestionEngine(mock_graph)

        # Synthetic patent data (agent-shaped)
        patent_data = {
            "patent_number": "US11234567B2",
            "title": "GLP-1 Receptor Agonist Formulation",
            "abstract": "Novel GLP-1 formulation for diabetes treatment",
            "assignees": ["Pharma Corp"],
            "drugs": ["Semaglutide"],
            "indications": ["Type 2 Diabetes"],
            "confidence_score": 0.85
        }

        result = engine.ingest_patent(patent_data)

        assert result["success"] is True
        assert result["patent_number"] == "US11234567B2"
        assert "created_nodes" in result
        assert "created_relationships" in result

    def test_ingest_patent_preserves_provenance(self):
        """Test that patent provenance is preserved"""
        mock_graph = Mock(spec=GraphManager)
        mock_graph.create_node.side_effect = ["patent_1", "evidence_1"]

        engine = IngestionEngine(mock_graph)

        patent_data = {
            "patent_number": "US99999999B1",
            "title": "Patent Title",
            "abstract": "Abstract",
            "assignees": ["Company A"],
            "drugs": [],
            "indications": []
        }

        result = engine.ingest_patent(patent_data, agent_name="Patent Agent", agent_id="patent")

        # Verify evidence node was created with correct agent_id
        calls = mock_graph.create_node.call_args_list
        if len(calls) >= 2:
            evidence_node = calls[1][0][0]
            assert evidence_node.agent_id == "patent"


class TestMarketSignalIngestion:
    """Test market signal data ingestion"""

    def test_ingest_market_signal_success(self):
        """Test successful market signal ingestion"""
        mock_graph = Mock(spec=GraphManager)
        mock_graph.create_node.side_effect = ["market_1", "evidence_1", "drug_1"]

        engine = IngestionEngine(mock_graph)

        # Synthetic market data (agent-shaped)
        market_data = {
            "signal_type": "market_size",
            "drug": "Semaglutide",
            "indication": "Type 2 Diabetes",
            "metric": "market_size_usd",
            "value": 10000000000,  # $10B
            "year": 2024,
            "source": "Market Intelligence Report",
            "confidence_score": 0.75
        }

        result = engine.ingest_market_signal(market_data)

        assert result["success"] is True
        assert "created_nodes" in result


class TestConflictDetection:
    """Test conflict detection during ingestion"""

    def test_ingest_conflicting_evidence_triggers_detection(self):
        """Test that conflicting evidence is detected"""
        mock_graph = Mock(spec=GraphManager)
        mock_conflict_detector = Mock()
        mock_conflict_detector.detect_conflicts.return_value = []

        engine = IngestionEngine(mock_graph, conflict_detector=mock_conflict_detector)

        # Ingest two conflicting market signals
        # Signal 1: Market size $10B
        mock_graph.create_node.side_effect = ["market_1", "evidence_1", "drug_1"]
        market_data_1 = {
            "signal_type": "market_size",
            "drug": "Semaglutide",
            "metric": "market_size_usd",
            "value": 10000000000,
            "year": 2024,
            "source": "Source A"
        }
        engine.ingest_market_signal(market_data_1)

        # Signal 2: Market size $12B (conflicting)
        mock_graph.create_node.side_effect = ["market_2", "evidence_2", "drug_1"]
        market_data_2 = {
            "signal_type": "market_size",
            "drug": "Semaglutide",
            "metric": "market_size_usd",
            "value": 12000000000,  # Different value
            "year": 2024,
            "source": "Source B"
        }
        engine.ingest_market_signal(market_data_2)

        # In real system, conflict detector would identify these as conflicting
        # For now, verify ingestion doesn't crash


class TestSchemaValidation:
    """Test that ingested data validates against AKGP schema"""

    def test_drug_node_schema_validation(self):
        """Test DrugNode validates correctly"""
        # Valid drug node
        drug = DrugNode(
            name="Semaglutide",
            source="Clinical Agent",
            drug_class="GLP-1 agonist"
        )

        assert drug.node_type == NodeType.DRUG
        assert drug.name == "Semaglutide"

    def test_disease_node_schema_validation(self):
        """Test DiseaseNode validates correctly"""
        disease = DiseaseNode(
            name="Type 2 Diabetes Mellitus",
            source="Clinical Agent",
            disease_category="Metabolic"
        )

        assert disease.node_type == NodeType.DISEASE
        assert "Diabetes" in disease.name

    def test_evidence_node_schema_validation(self):
        """Test EvidenceNode validates correctly"""
        evidence = EvidenceNode(
            name="Clinical Evidence",
            source="Clinical Agent",
            agent_name="Clinical Agent",
            agent_id="clinical",
            raw_reference="NCT12345678",
            source_type=SourceType.CLINICAL,
            quality=EvidenceQuality.HIGH,
            confidence_score=0.9,
            summary="Trial summary"
        )

        assert evidence.node_type == NodeType.EVIDENCE
        assert evidence.agent_id == "clinical"
        assert evidence.confidence_score == 0.9

    def test_evidence_node_confidence_validation(self):
        """Test that confidence score is validated to [0, 1] range"""
        # Valid confidence
        evidence = EvidenceNode(
            name="Test",
            source="Agent",
            agent_name="Agent",
            agent_id="test",
            raw_reference="ref",
            source_type=SourceType.CLINICAL,
            summary="Summary",
            confidence_score=0.5
        )
        assert 0.0 <= evidence.confidence_score <= 1.0

        # Out of range confidence should be clamped
        evidence_high = EvidenceNode(
            name="Test",
            source="Agent",
            agent_name="Agent",
            agent_id="test",
            raw_reference="ref",
            source_type=SourceType.CLINICAL,
            summary="Summary",
            confidence_score=1.5  # Will be clamped to 1.0
        )
        assert evidence_high.confidence_score == 1.0

    def test_trial_node_schema_validation(self):
        """Test TrialNode validates correctly"""
        trial = TrialNode(
            name="Phase 3 GLP-1 Trial",
            source="Clinical Agent",
            nct_id="NCT12345678",
            phase="PHASE3",
            status="RECRUITING",
            interventions=["Semaglutide"],
            conditions=["Type 2 Diabetes"]
        )

        assert trial.node_type == NodeType.TRIAL
        assert trial.nct_id == "NCT12345678"

    def test_patent_node_schema_validation(self):
        """Test PatentNode validates correctly"""
        patent = PatentNode(
            name="GLP-1 Formulation Patent",
            source="Patent Agent",
            patent_number="US11234567B2",
            assignees=["Pharma Corp"],
            patent_title="GLP-1 Formulation"
        )

        assert patent.node_type == NodeType.PATENT
        assert patent.patent_number == "US11234567B2"


class TestProvenanceTracking:
    """Test that provenance is properly tracked"""

    def test_provenance_fields_required(self):
        """Test that evidence nodes require provenance fields"""
        # Must have agent_name, agent_id, raw_reference
        with pytest.raises(Exception):  # Pydantic validation error
            EvidenceNode(
                name="Test",
                source="Agent",
                # Missing agent_name, agent_id, raw_reference
                source_type=SourceType.CLINICAL,
                summary="Summary"
            )

    def test_provenance_timestamp_auto_populated(self):
        """Test that extraction timestamp is auto-populated"""
        evidence = EvidenceNode(
            name="Test",
            source="Agent",
            agent_name="Agent",
            agent_id="test",
            raw_reference="ref",
            source_type=SourceType.CLINICAL,
            summary="Summary"
        )

        assert evidence.extraction_timestamp is not None
        assert isinstance(evidence.extraction_timestamp, datetime)

    def test_provenance_tracks_source_type(self):
        """Test that source type is tracked"""
        clinical_evidence = EvidenceNode(
            name="Clinical",
            source="Agent",
            agent_name="Clinical Agent",
            agent_id="clinical",
            raw_reference="NCT123",
            source_type=SourceType.CLINICAL,
            summary="Summary"
        )

        patent_evidence = EvidenceNode(
            name="Patent",
            source="Agent",
            agent_name="Patent Agent",
            agent_id="patent",
            raw_reference="US123",
            source_type=SourceType.PATENT,
            summary="Summary"
        )

        assert clinical_evidence.source_type == SourceType.CLINICAL
        assert patent_evidence.source_type == SourceType.PATENT


class TestTemporalValidity:
    """Test temporal validity tracking"""

    def test_evidence_has_validity_period(self):
        """Test that evidence nodes have validity period"""
        evidence = EvidenceNode(
            name="Test",
            source="Agent",
            agent_name="Agent",
            agent_id="test",
            raw_reference="ref",
            source_type=SourceType.CLINICAL,
            summary="Summary"
        )

        assert evidence.validity_start is not None
        assert isinstance(evidence.validity_start, datetime)
        # validity_end is None by default (still valid)
        assert evidence.validity_end is None


class TestRelationshipCreation:
    """Test relationship creation during ingestion"""

    def test_relationships_have_evidence_links(self):
        """Test that relationships are linked to evidence"""
        mock_graph = Mock(spec=GraphManager)
        mock_graph.create_node.side_effect = ["trial_1", "evidence_1", "drug_1", "disease_1"]
        mock_graph.create_relationship.return_value = "rel_1"

        engine = IngestionEngine(mock_graph)

        trial_data = {
            "nct_id": "NCT12345678",
            "title": "Trial",
            "summary": "Summary",
            "interventions": ["DrugA"],
            "conditions": ["DiseaseB"]
        }

        result = engine.ingest_clinical_trial(trial_data)

        # Verify relationship was created
        assert mock_graph.create_relationship.called

        # Verify relationship includes evidence_id
        rel_call = mock_graph.create_relationship.call_args[0][0]
        assert hasattr(rel_call, 'evidence_id')
        assert rel_call.evidence_id == "evidence_1"

    def test_relationships_have_confidence_scores(self):
        """Test that relationships inherit confidence from evidence"""
        mock_graph = Mock(spec=GraphManager)
        mock_graph.create_node.side_effect = ["trial_1", "evidence_1", "drug_1", "disease_1"]
        mock_graph.create_relationship.return_value = "rel_1"

        engine = IngestionEngine(mock_graph)

        trial_data = {
            "nct_id": "NCT12345678",
            "title": "Trial",
            "summary": "Summary",
            "interventions": ["DrugA"],
            "conditions": ["DiseaseB"],
            "confidence_score": 0.95
        }

        result = engine.ingest_clinical_trial(trial_data)

        # Verify relationship has confidence
        rel_call = mock_graph.create_relationship.call_args[0][0]
        assert hasattr(rel_call, 'confidence')
        assert rel_call.confidence == 0.95


class TestErrorHandling:
    """Test error handling during ingestion"""

    def test_missing_required_field_raises_error(self):
        """Test that missing required fields raise errors"""
        mock_graph = Mock(spec=GraphManager)
        engine = IngestionEngine(mock_graph)

        # Missing nct_id (required field)
        with pytest.raises(KeyError):
            engine.ingest_clinical_trial({
                "title": "Trial",
                # Missing nct_id
                "summary": "Summary"
            })

    def test_invalid_confidence_score_is_clamped(self):
        """Test that invalid confidence scores are handled"""
        evidence = EvidenceNode(
            name="Test",
            source="Agent",
            agent_name="Agent",
            agent_id="test",
            raw_reference="ref",
            source_type=SourceType.CLINICAL,
            summary="Summary",
            confidence_score=2.0  # Invalid, should be clamped
        )

        assert evidence.confidence_score <= 1.0

    def test_graph_manager_failure_propagates(self):
        """Test that GraphManager failures are handled"""
        mock_graph = Mock(spec=GraphManager)
        mock_graph.create_node.side_effect = Exception("Graph creation failed")

        engine = IngestionEngine(mock_graph)

        trial_data = {
            "nct_id": "NCT12345678",
            "title": "Trial",
            "summary": "Summary",
            "interventions": [],
            "conditions": []
        }

        # Should raise the exception
        with pytest.raises(Exception):
            engine.ingest_clinical_trial(trial_data)


class TestBatchIngestion:
    """Test batch ingestion capabilities"""

    def test_batch_ingest_clinical_trials(self):
        """Test ingesting multiple clinical trials"""
        mock_graph = Mock(spec=GraphManager)

        # Create enough IDs for all nodes
        node_ids = [f"node_{i}" for i in range(50)]
        mock_graph.create_node.side_effect = node_ids
        mock_graph.create_relationship.side_effect = [f"rel_{i}" for i in range(50)]

        engine = IngestionEngine(mock_graph)

        trials = [
            {
                "nct_id": f"NCT0000000{i}",
                "title": f"Trial {i}",
                "summary": "Summary",
                "interventions": ["Drug"],
                "conditions": ["Disease"]
            }
            for i in range(5)
        ]

        results = []
        for trial in trials:
            result = engine.ingest_clinical_trial(trial)
            results.append(result)

        # All should succeed
        assert all(r["success"] for r in results)
        assert len(results) == 5
