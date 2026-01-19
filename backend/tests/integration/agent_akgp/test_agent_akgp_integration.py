"""
Integration Tests: Agent → Normalization → AKGP

Tests the complete flow from agent output through normalization layer into AKGP.

REQUIREMENTS (from STEP 4 spec):
- Each agent → parser → AKGP.ingest_evidence() flow
- Provenance correctness (agent_id, raw_reference, timestamp)
- Conflict detection (SUPPORTS vs CONTRADICTS)
- Temporal weighting (newer > older)
- Rejection handling (malformed outputs don't enter graph)
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

# Agent imports
from agents.clinical_agent import ClinicalAgent
from agents.patent_agent import PatentAgent
from agents.market_agent_hybrid import MarketAgentHybrid
from agents.literature_agent import LiteratureAgent

# Normalization imports
from normalization import (
    parse_clinical_evidence,
    parse_patent_evidence,
    parse_market_evidence,
    parse_literature_evidence,
    ParsingRejection
)

# AKGP imports
from akgp.graph_manager import GraphManager
from akgp.ingestion import IngestionEngine
from akgp.schema import EvidenceNode, SourceType


class TestClinicalAgentIntegration:
    """Test Clinical Agent → Normalization → AKGP flow"""

    def setup_method(self):
        """Setup fresh AKGP for each test"""
        self.graph = GraphManager()
        self.ingestion_engine = IngestionEngine(self.graph)

    def test_clinical_agent_to_akgp_flow(self):
        """Test Clinical Agent output flows through normalization into AKGP"""
        # Mock clinical agent output
        clinical_output = {
            "query": "GLP-1 for type 2 diabetes",
            "summary": "Clinical trials show GLP-1 agonists are effective for type 2 diabetes.",
            "comprehensive_summary": "Phase 3 trials demonstrate efficacy.",
            "trials": [
                {
                    "nct_id": "NCT12345678",
                    "title": "GLP-1 Trial for Type 2 Diabetes",
                    "phase": "Phase 3",
                    "status": "Completed",
                    "conditions": ["Type 2 Diabetes"],
                    "interventions": ["GLP-1"],
                    "summary": "Trial summary"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT12345678",
                                "briefTitle": "GLP-1 Trial for Type 2 Diabetes"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "GLP-1"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Type 2 Diabetes"]
                            },
                            "designModule": {
                                "phases": ["PHASE3"]
                            },
                            "statusModule": {
                                "overallStatus": "COMPLETED"
                            }
                        }
                    }
                ],
                "totalCount": 1
            },
            "total_trials": 1,
            "confidence_score": 0.9,
            "agent_id": "clinical"
        }

        # Step 1: Parse agent output
        normalized_evidence_list = parse_clinical_evidence(clinical_output)
        assert len(normalized_evidence_list) > 0, "Should parse at least one evidence"

        # Step 2: Ingest into AKGP
        for evidence in normalized_evidence_list:
            result = self.ingestion_engine.ingest_evidence(evidence)

            # Verify ingestion success
            assert result["success"] is True
            assert "evidence_id" in result
            assert "drug_id" in result
            assert "disease_id" in result

            # Verify provenance tracking
            assert evidence.evidence_node.agent_id == "clinical"
            assert evidence.evidence_node.source_type == SourceType.CLINICAL
            assert evidence.evidence_node.raw_reference == "NCT12345678"

    def test_clinical_agent_provenance_correctness(self):
        """Test provenance metadata is preserved in AKGP"""
        clinical_output = {
            "query": "semaglutide diabetes",
            "summary": "Test summary",
            "comprehensive_summary": "Test comprehensive summary",
            "trials": [
                {
                    "nct_id": "NCT99999999",
                    "title": "Semaglutide for Diabetes",
                    "phase": "Phase 2",
                    "status": "Recruiting",
                    "conditions": ["Diabetes"],
                    "interventions": ["semaglutide"],
                    "summary": "Test trial"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT99999999",
                                "briefTitle": "Semaglutide for Diabetes"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "semaglutide"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Diabetes"]
                            },
                            "designModule": {
                                "phases": ["PHASE2"]
                            },
                            "statusModule": {
                                "overallStatus": "RECRUITING"
                            }
                        }
                    }
                ],
                "totalCount": 1
            },
            "total_trials": 1,
            "confidence_score": 0.8,
            "agent_id": "clinical"
        }

        normalized_evidence_list = parse_clinical_evidence(clinical_output)
        evidence = normalized_evidence_list[0]

        # Ingest into AKGP
        result = self.ingestion_engine.ingest_evidence(evidence)

        # Verify provenance details
        assert evidence.evidence_node.agent_id == "clinical"
        assert evidence.evidence_node.agent_name == "Clinical Agent"
        assert evidence.evidence_node.api_source == "ClinicalTrials.gov v2 API"
        assert "NCT99999999" in evidence.evidence_node.raw_reference
        assert evidence.evidence_node.extraction_timestamp is not None


class TestPatentAgentIntegration:
    """Test Patent Agent → Normalization → AKGP flow"""

    def setup_method(self):
        """Setup fresh AKGP for each test"""
        self.graph = GraphManager()
        self.ingestion_engine = IngestionEngine(self.graph)

    def test_patent_agent_to_akgp_flow(self):
        """Test Patent Agent output flows through normalization into AKGP"""
        patent_output = {
            "query": "GLP-1 patents",
            "summary": "Patent landscape for GLP-1 agonists.",
            "comprehensive_summary": "Multiple patents cover GLP-1 therapeutics.",
            "patents": [
                {
                    "patent_number": "US10000000",
                    "patent_title": "GLP-1 Receptor Agonist for Diabetes Treatment",
                    "patent_abstract": "Novel GLP-1 compounds for treating type 2 diabetes",
                    "patent_date": "2020-01-01",
                    "assignees": [{"assignee_organization": "Pharma Corp"}],
                    "claims": "Claim 1: GLP-1 for diabetes treatment",
                    "status": "Granted"
                }
            ],
            "total_patents": 1,
            "confidence_score": 0.7,
            "agent_id": "patent"
        }

        # Step 1: Parse agent output
        normalized_evidence_list = parse_patent_evidence(patent_output)
        assert len(normalized_evidence_list) > 0

        # Step 2: Ingest into AKGP
        for evidence in normalized_evidence_list:
            result = self.ingestion_engine.ingest_evidence(evidence)

            assert result["success"] is True
            assert evidence.evidence_node.agent_id == "patent"
            assert evidence.evidence_node.source_type == SourceType.PATENT


class TestMarketAgentIntegration:
    """Test Market Agent → Normalization → AKGP flow"""

    def setup_method(self):
        """Setup fresh AKGP for each test"""
        self.graph = GraphManager()
        self.ingestion_engine = IngestionEngine(self.graph)

    def test_market_agent_to_akgp_flow(self):
        """Test Market Agent output flows through normalization into AKGP"""
        market_output = {
            "agentId": "market",
            "query": "GLP-1 market size",
            "sections": {
                "summary": "GLP-1 market for type 2 diabetes is growing rapidly.",
                "market_overview": "Strong growth in diabetes therapeutics market.",
                "key_metrics": "Market size: $10B, CAGR: 15%"
            },
            "confidence": {
                "score": 0.75,
                "level": "high"
            },
            "confidence_score": 0.75,
            "web_results": [{"url": "https://example.com/market-report", "title": "GLP-1 Market Report"}],
            "rag_results": []
        }

        # Step 1: Parse agent output
        normalized_evidence_list = parse_market_evidence(market_output)
        assert len(normalized_evidence_list) == 1  # Market creates one aggregate evidence

        # Step 2: Ingest into AKGP
        evidence = normalized_evidence_list[0]
        result = self.ingestion_engine.ingest_evidence(evidence)

        assert result["success"] is True
        assert evidence.evidence_node.agent_id == "market"
        assert evidence.evidence_node.source_type == SourceType.MARKET
        assert evidence.polarity == "SUGGESTS"  # Market evidence is always SUGGESTS


class TestLiteratureAgentIntegration:
    """Test Literature Agent → Normalization → AKGP flow"""

    def setup_method(self):
        """Setup fresh AKGP for each test"""
        self.graph = GraphManager()
        self.ingestion_engine = IngestionEngine(self.graph)

    def test_literature_agent_to_akgp_flow(self):
        """Test Literature Agent output flows through normalization into AKGP"""
        literature_output = {
            "query": "GLP-1 meta-analysis",
            "summary": "Meta-analysis shows GLP-1 efficacy for diabetes.",
            "comprehensive_summary": "Systematic review of GLP-1 trials.",
            "publications": [
                {
                    "pmid": "12345678",
                    "title": "Meta-analysis of GLP-1 for Type 2 Diabetes",
                    "abstract": "This meta-analysis evaluates GLP-1 agonists for type 2 diabetes treatment.",
                    "authors": ["Smith J", "Doe A"],
                    "journal": "Diabetes Care",
                    "year": "2023",
                    "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"
                }
            ],
            "total_publications": 1,
            "confidence_score": 0.9,
            "agent_id": "literature"
        }

        # Step 1: Parse agent output
        normalized_evidence_list = parse_literature_evidence(literature_output)
        assert len(normalized_evidence_list) > 0

        # Step 2: Ingest into AKGP
        evidence = normalized_evidence_list[0]
        result = self.ingestion_engine.ingest_evidence(evidence)

        assert result["success"] is True
        assert evidence.evidence_node.agent_id == "literature"
        assert evidence.evidence_node.source_type == SourceType.LITERATURE
        assert "PMID:12345678" in evidence.evidence_node.raw_reference


class TestPolarityAndConflictDetection:
    """Test polarity mapping and conflict detection"""

    def setup_method(self):
        """Setup fresh AKGP for each test"""
        self.graph = GraphManager()
        self.ingestion_engine = IngestionEngine(self.graph)

    def test_supports_polarity_creates_treats_relationship(self):
        """Test SUPPORTS polarity creates TREATS relationship"""
        clinical_output = {
            "query": "GLP-1 phase 3 success",
            "summary": "Phase 3 trial successful",
            "comprehensive_summary": "Phase 3 trial demonstrates efficacy",
            "trials": [
                {
                    "nct_id": "NCT11111111",
                    "title": "Phase 3 GLP-1 Success",
                    "phase": "Phase 3",
                    "status": "Completed",
                    "conditions": ["Diabetes"],
                    "interventions": ["GLP-1"],
                    "summary": "Successful trial"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT11111111",
                                "briefTitle": "Phase 3 GLP-1 Success"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "GLP-1"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Diabetes"]
                            },
                            "designModule": {
                                "phases": ["PHASE3"]
                            },
                            "statusModule": {
                                "overallStatus": "COMPLETED"
                            }
                        }
                    }
                ],
                "totalCount": 1
            },
            "total_trials": 1,
            "confidence_score": 0.95,
            "agent_id": "clinical"
        }

        normalized_evidence_list = parse_clinical_evidence(clinical_output)
        evidence = normalized_evidence_list[0]

        # Phase 3 successful → SUPPORTS
        assert evidence.polarity == "SUPPORTS"

        # Ingest and verify relationship type
        result = self.ingestion_engine.ingest_evidence(evidence)
        assert result["relationship_type"] == "TREATS"

    def test_suggests_polarity_for_market_evidence(self):
        """Test market evidence always gets SUGGESTS polarity"""
        market_output = {
            "agentId": "market",
            "query": "GLP-1 forecast for type 2 diabetes",
            "sections": {
                "summary": "Strong market forecast for GLP-1 in type 2 diabetes treatment",
                "market_overview": "Growth expected in diabetes therapeutics market",
                "key_metrics": "CAGR: 20%"
            },
            "confidence": {"score": 0.8, "level": "high"},
            "confidence_score": 0.8,
            "web_results": [],
            "rag_results": []
        }

        normalized_evidence_list = parse_market_evidence(market_output)
        evidence = normalized_evidence_list[0]

        # Market evidence always SUGGESTS
        assert evidence.polarity == "SUGGESTS"

        result = self.ingestion_engine.ingest_evidence(evidence)
        assert result["relationship_type"] == "SUGGESTS"


class TestRejectionHandling:
    """Test that malformed outputs are rejected gracefully"""

    def setup_method(self):
        """Setup fresh AKGP for each test"""
        self.graph = GraphManager()
        self.ingestion_engine = IngestionEngine(self.graph)

    def test_malformed_clinical_output_raises_parsing_rejection(self):
        """Test that missing required fields raises ParsingRejection"""
        malformed_output = {
            "query": "test",
            # Missing 'trials' field
            "summary": "test summary"
        }

        with pytest.raises(ParsingRejection):
            parse_clinical_evidence(malformed_output)

    def test_clinical_output_without_drug_is_rejected(self):
        """Test that trials without drug mentions are rejected during normalization"""
        clinical_output = {
            "query": "test query",
            "summary": "test",
            "comprehensive_summary": "test comprehensive",
            "trials": [
                {
                    "nct_id": "NCT00000000",
                    "title": "Trial without drug or disease mentions",
                    "phase": "Phase 1",
                    "status": "Recruiting",
                    "conditions": [],  # No disease
                    "interventions": [],  # No drug
                    "summary": "Empty trial"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT00000000",
                                "briefTitle": "Trial without drug or disease mentions"
                            },
                            "armsInterventionsModule": {
                                "interventions": []  # No drug
                            },
                            "conditionsModule": {
                                "conditions": []  # No disease
                            },
                            "designModule": {
                                "phases": ["PHASE1"]
                            },
                            "statusModule": {
                                "overallStatus": "RECRUITING"
                            }
                        }
                    }
                ],
                "totalCount": 1
            },
            "total_trials": 1,
            "confidence_score": 0.5,
            "agent_id": "clinical"
        }

        # Should parse but return empty list (trials rejected)
        normalized_evidence_list = parse_clinical_evidence(clinical_output)
        assert len(normalized_evidence_list) == 0, "Trial without drug/disease should be rejected"

    def test_market_output_without_drug_is_rejected(self):
        """Test market evidence without drug mentions is rejected"""
        market_output = {
            "agentId": "market",
            "query": "generic market data",
            "sections": {
                "summary": "Generic market data without drug or disease mentions",
                "market_overview": "Some market overview",
                "key_metrics": "Growth: 10%"
            },
            "confidence_score": 0.6,
            "web_results": [],
            "rag_results": []
        }

        # Should raise ParsingRejection (no drug/disease extracted)
        with pytest.raises(ParsingRejection, match="No drug mentions found"):
            parse_market_evidence(market_output)


class TestTemporalWeighting:
    """Test that temporal weighting is preserved"""

    def setup_method(self):
        """Setup fresh AKGP for each test"""
        self.graph = GraphManager()
        self.ingestion_engine = IngestionEngine(self.graph)

    def test_evidence_has_extraction_timestamp(self):
        """Test that all evidence has extraction timestamps"""
        clinical_output = {
            "query": "GLP-1 diabetes",
            "summary": "test",
            "comprehensive_summary": "test comprehensive",
            "trials": [
                {
                    "nct_id": "NCT12345678",
                    "title": "GLP-1 Trial",
                    "phase": "Phase 2",
                    "status": "Recruiting",
                    "conditions": ["Diabetes"],
                    "interventions": ["GLP-1"],
                    "summary": "Trial"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT12345678",
                                "briefTitle": "GLP-1 Trial"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "GLP-1"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Diabetes"]
                            },
                            "designModule": {
                                "phases": ["PHASE2"]
                            },
                            "statusModule": {
                                "overallStatus": "RECRUITING"
                            }
                        }
                    }
                ],
                "totalCount": 1
            },
            "total_trials": 1,
            "confidence_score": 0.8,
            "agent_id": "clinical"
        }

        normalized_evidence_list = parse_clinical_evidence(clinical_output)
        evidence = normalized_evidence_list[0]

        # Verify timestamp exists and is recent
        assert evidence.evidence_node.extraction_timestamp is not None
        assert isinstance(evidence.evidence_node.extraction_timestamp, datetime)

        # Timestamp should be within last minute (just created)
        time_diff = datetime.utcnow() - evidence.evidence_node.extraction_timestamp
        assert time_diff.total_seconds() < 60, "Timestamp should be recent"


class TestEndToEndFlow:
    """Test complete end-to-end integration"""

    def setup_method(self):
        """Setup fresh AKGP for each test"""
        self.graph = GraphManager()
        self.ingestion_engine = IngestionEngine(self.graph)

    def test_multiple_agents_ingest_to_same_graph(self):
        """Test that multiple agents can ingest into the same graph without conflicts"""
        # Clinical evidence
        clinical_output = {
            "query": "GLP-1 diabetes",
            "summary": "Clinical trials",
            "comprehensive_summary": "Comprehensive clinical trials",
            "trials": [
                {
                    "nct_id": "NCT11111111",
                    "title": "GLP-1 Clinical Trial",
                    "phase": "Phase 3",
                    "status": "Completed",
                    "conditions": ["Type 2 Diabetes"],
                    "interventions": ["GLP-1"],
                    "summary": "Trial"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT11111111",
                                "briefTitle": "GLP-1 Clinical Trial"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "GLP-1"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Type 2 Diabetes"]
                            },
                            "designModule": {
                                "phases": ["PHASE3"]
                            },
                            "statusModule": {
                                "overallStatus": "COMPLETED"
                            }
                        }
                    }
                ],
                "totalCount": 1
            },
            "total_trials": 1,
            "confidence_score": 0.9,
            "agent_id": "clinical"
        }

        # Market evidence
        market_output = {
            "agentId": "market",
            "query": "GLP-1 market size for type 2 diabetes",
            "sections": {
                "summary": "GLP-1 market for type 2 diabetes shows strong growth",
                "market_overview": "Type 2 diabetes therapeutics market overview",
                "key_metrics": "Market size: $5B"
            },
            "confidence": {"score": 0.7, "level": "medium"},
            "confidence_score": 0.7,
            "web_results": [],
            "rag_results": []
        }

        # Ingest both
        clinical_evidence_list = parse_clinical_evidence(clinical_output)
        market_evidence_list = parse_market_evidence(market_output)

        results = []
        for evidence in clinical_evidence_list:
            result = self.ingestion_engine.ingest_evidence(evidence)
            results.append(result)

        for evidence in market_evidence_list:
            result = self.ingestion_engine.ingest_evidence(evidence)
            results.append(result)

        # Verify both ingested successfully
        assert all(r["success"] for r in results), "All evidence should ingest successfully"
        assert len(results) >= 2, "Should have at least clinical + market evidence"

    def test_canonical_ids_are_stable_across_agents(self):
        """Test that same drug/disease from different agents get same canonical IDs"""
        # Clinical evidence with "GLP-1" and "type 2 diabetes"
        clinical_output = {
            "query": "GLP-1 diabetes",
            "summary": "test",
            "comprehensive_summary": "test",
            "trials": [
                {
                    "nct_id": "NCT11111111",
                    "title": "GLP-1 for Type 2 Diabetes",
                    "phase": "Phase 2",
                    "status": "Recruiting",
                    "conditions": ["Type 2 Diabetes"],
                    "interventions": ["GLP-1"],
                    "summary": "Trial"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT11111111",
                                "briefTitle": "GLP-1 for Type 2 Diabetes"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "GLP-1"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Type 2 Diabetes"]
                            },
                            "designModule": {
                                "phases": ["PHASE2"]
                            },
                            "statusModule": {
                                "overallStatus": "RECRUITING"
                            }
                        }
                    }
                ],
                "totalCount": 1
            },
            "total_trials": 1,
            "confidence_score": 0.8,
            "agent_id": "clinical"
        }

        # Market evidence with "glp-1" and "type 2 diabetes" (different case)
        market_output = {
            "agentId": "market",
            "query": "glp-1 type 2 diabetes market",
            "sections": {
                "summary": "glp-1 market for type 2 diabetes shows growth",
                "market_overview": "Type 2 diabetes market overview",
                "key_metrics": "Metrics"
            },
            "confidence": {"score": 0.7, "level": "medium"},
            "confidence_score": 0.7,
            "web_results": [],
            "rag_results": []
        }

        clinical_evidence_list = parse_clinical_evidence(clinical_output)
        market_evidence_list = parse_market_evidence(market_output)

        clinical_evidence = clinical_evidence_list[0]
        market_evidence = market_evidence_list[0]

        # Canonical IDs should be identical despite case differences
        assert clinical_evidence.drug_id == market_evidence.drug_id, \
            "Same drug from different agents should have same canonical ID"
        assert clinical_evidence.disease_id == market_evidence.disease_id, \
            "Same disease from different agents should have same canonical ID"
