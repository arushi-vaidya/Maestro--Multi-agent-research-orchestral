"""
Integration Tests: Conflict Explanations

Tests the ConflictReasoner's ability to generate human-readable explanations
for conflicting evidence in AKGP.

REQUIREMENTS:
- Create synthetic conflicting evidence
- Ingest via AKGP (DO NOT bypass)
- Call ConflictReasoner.explain_conflict()
- Assert: Correct explanations, Deterministic text, Provenance preserved
"""

import pytest
from datetime import datetime, timedelta

from akgp.graph_manager import GraphManager
from akgp.ingestion import IngestionEngine
from akgp.conflict_reasoning import ConflictReasoner
from normalization import parse_clinical_evidence


class TestConflictExplanations:
    """Test conflict explanation generation"""

    def setup_method(self):
        """Setup fresh AKGP for each test"""
        self.graph = GraphManager()
        self.ingestion_engine = IngestionEngine(self.graph)
        self.conflict_reasoner = ConflictReasoner(self.graph)

    def test_explain_conflict_with_opposing_evidence(self):
        """Test conflict explanation when evidence directly opposes"""
        # Create conflicting clinical evidence:
        # Trial 1: Phase 3 completed (SUPPORTS)
        # Trial 2: Phase 3 terminated due to inefficacy (CONTRADICTS)

        clinical_output_supports = {
            "query": "Drug X for Disease Y",
            "summary": "Phase 3 trial completed successfully",
            "comprehensive_summary": "Trial demonstrates efficacy",
            "trials": [
                {
                    "nct_id": "NCT10000001",
                    "title": "Phase 3 Trial - Success",
                    "phase": "Phase 3",
                    "status": "Completed",
                    "conditions": ["Disease Y"],
                    "interventions": ["Drug X"],
                    "summary": "Successful trial"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT10000001",
                                "briefTitle": "Phase 3 Trial - Success"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug X"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease Y"]
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

        clinical_output_contradicts = {
            "query": "Drug X for Disease Y",
            "summary": "Phase 3 trial terminated",
            "comprehensive_summary": "Trial terminated due to lack of efficacy",
            "trials": [
                {
                    "nct_id": "NCT10000002",
                    "title": "Phase 3 Trial - Terminated",
                    "phase": "Phase 3",
                    "status": "Terminated",
                    "conditions": ["Disease Y"],
                    "interventions": ["Drug X"],
                    "summary": "Trial failed"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT10000002",
                                "briefTitle": "Phase 3 Trial - Terminated"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug X"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease Y"]
                            },
                            "designModule": {
                                "phases": ["PHASE3"]
                            },
                            "statusModule": {
                                "overallStatus": "TERMINATED"
                            }
                        }
                    }
                ],
                "totalCount": 1
            },
            "total_trials": 1,
            "confidence_score": 0.90,
            "agent_id": "clinical"
        }

        # Ingest both into AKGP
        supports_evidence = parse_clinical_evidence(clinical_output_supports)
        contradicts_evidence = parse_clinical_evidence(clinical_output_contradicts)

        for evidence in supports_evidence:
            self.ingestion_engine.ingest_evidence(evidence)

        for evidence in contradicts_evidence:
            self.ingestion_engine.ingest_evidence(evidence)

        # Get canonical IDs
        drug_id = supports_evidence[0].drug_id
        disease_id = supports_evidence[0].disease_id

        # Explain conflict
        explanation = self.conflict_reasoner.explain_conflict(drug_id, disease_id)

        # Assertions
        assert explanation["has_conflict"] is True, "Should detect conflict"
        assert explanation["severity"] is not None, "Should have severity classification"
        assert len(explanation["summary"]) > 0, "Should have summary"
        assert "Conflict detected" in explanation["summary"], "Summary should mention conflict"
        assert explanation["dominant_evidence"] is not None, "Should have dominant evidence"
        assert len(explanation["supporting_evidence"]) > 0, "Should have supporting evidence"
        assert len(explanation["contradicting_evidence"]) > 0, "Should have contradicting evidence"
        assert explanation["evidence_count"]["supports"] == 1
        assert explanation["evidence_count"]["contradicts"] == 1

    def test_explain_no_conflict_all_supporting(self):
        """Test explanation when all evidence supports (no conflict)"""
        clinical_output = {
            "query": "Aspirin for heart disease",
            "summary": "Multiple trials support efficacy",
            "comprehensive_summary": "Comprehensive evidence supports efficacy",
            "trials": [
                {
                    "nct_id": "NCT20000001",
                    "title": "Aspirin Trial 1",
                    "phase": "Phase 3",
                    "status": "Completed",
                    "conditions": ["Heart Disease"],
                    "interventions": ["Aspirin"],
                    "summary": "Trial 1"
                },
                {
                    "nct_id": "NCT20000002",
                    "title": "Aspirin Trial 2",
                    "phase": "Phase 4",
                    "status": "Completed",
                    "conditions": ["Heart Disease"],
                    "interventions": ["Aspirin"],
                    "summary": "Trial 2"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT20000001",
                                "briefTitle": "Aspirin Trial 1"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Aspirin"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Heart Disease"]
                            },
                            "designModule": {
                                "phases": ["PHASE3"]
                            },
                            "statusModule": {
                                "overallStatus": "COMPLETED"
                            }
                        }
                    },
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT20000002",
                                "briefTitle": "Aspirin Trial 2"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Aspirin"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Heart Disease"]
                            },
                            "designModule": {
                                "phases": ["PHASE4"]
                            },
                            "statusModule": {
                                "overallStatus": "COMPLETED"
                            }
                        }
                    }
                ],
                "totalCount": 2
            },
            "total_trials": 2,
            "confidence_score": 0.95,
            "agent_id": "clinical"
        }

        # Ingest
        evidence_list = parse_clinical_evidence(clinical_output)
        for evidence in evidence_list:
            self.ingestion_engine.ingest_evidence(evidence)

        drug_id = evidence_list[0].drug_id
        disease_id = evidence_list[0].disease_id

        # Explain
        explanation = self.conflict_reasoner.explain_conflict(drug_id, disease_id)

        # Assertions
        assert explanation["has_conflict"] is False, "Should not detect conflict"
        assert explanation["severity"] is None, "No severity when no conflict"
        assert "No conflict" in explanation["summary"], "Summary should say no conflict"
        assert len(explanation["supporting_evidence"]) == 2, "Should have 2 supporting evidence"
        assert len(explanation["contradicting_evidence"]) == 0, "Should have 0 contradicting evidence"

    def test_temporal_explanation_newer_dominates(self):
        """Test that temporal explanation explains newer evidence dominating"""
        # Create older contradicting evidence and newer supporting evidence

        # Older evidence (2020)
        old_trial = {
            "query": "Drug Z for Disease W",
            "summary": "Old trial failed",
            "comprehensive_summary": "2020 trial failed",
            "trials": [
                {
                    "nct_id": "NCT30000001",
                    "title": "Drug Z Trial 2020",
                    "phase": "Phase 2",
                    "status": "Terminated",
                    "conditions": ["Disease W"],
                    "interventions": ["Drug Z"],
                    "summary": "Failed"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT30000001",
                                "briefTitle": "Drug Z Trial 2020"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug Z"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease W"]
                            },
                            "designModule": {
                                "phases": ["PHASE2"]
                            },
                            "statusModule": {
                                "overallStatus": "TERMINATED"
                            }
                        }
                    }
                ],
                "totalCount": 1
            },
            "total_trials": 1,
            "confidence_score": 0.70,
            "agent_id": "clinical"
        }

        # Newer evidence (2024)
        new_trial = {
            "query": "Drug Z for Disease W",
            "summary": "New trial succeeded",
            "comprehensive_summary": "2024 trial succeeded",
            "trials": [
                {
                    "nct_id": "NCT30000002",
                    "title": "Drug Z Trial 2024",
                    "phase": "Phase 3",
                    "status": "Completed",
                    "conditions": ["Disease W"],
                    "interventions": ["Drug Z"],
                    "summary": "Success"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT30000002",
                                "briefTitle": "Drug Z Trial 2024"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug Z"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease W"]
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

        # Ingest both
        old_evidence = parse_clinical_evidence(old_trial)
        new_evidence = parse_clinical_evidence(new_trial)

        for evidence in old_evidence:
            self.ingestion_engine.ingest_evidence(evidence)

        for evidence in new_evidence:
            self.ingestion_engine.ingest_evidence(evidence)

        drug_id = new_evidence[0].drug_id
        disease_id = new_evidence[0].disease_id

        # Explain
        explanation = self.conflict_reasoner.explain_conflict(drug_id, disease_id)

        # Assertions
        assert explanation["has_conflict"] is True
        # Temporal explanation should exist and discuss time periods
        assert len(explanation["temporal_explanation"]) > 0, "Should have temporal explanation"
        assert "time" in explanation["temporal_explanation"].lower() or "period" in explanation["temporal_explanation"].lower(), \
            "Temporal explanation should mention time periods"
        assert len(explanation["provenance_summary"]) == 2, "Should have provenance for both evidence"

    def test_provenance_summary_includes_all_sources(self):
        """Test that provenance summary includes all evidence sources"""
        clinical_output = {
            "query": "Drug A for Disease B",
            "summary": "Multiple trials",
            "comprehensive_summary": "Multiple trials",
            "trials": [
                {
                    "nct_id": "NCT40000001",
                    "title": "Trial 1",
                    "phase": "Phase 3",
                    "status": "Completed",
                    "conditions": ["Disease B"],
                    "interventions": ["Drug A"],
                    "summary": "Trial 1"
                },
                {
                    "nct_id": "NCT40000002",
                    "title": "Trial 2",
                    "phase": "Phase 2",
                    "status": "Terminated",
                    "conditions": ["Disease B"],
                    "interventions": ["Drug A"],
                    "summary": "Trial 2"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT40000001",
                                "briefTitle": "Trial 1"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug A"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease B"]
                            },
                            "designModule": {
                                "phases": ["PHASE3"]
                            },
                            "statusModule": {
                                "overallStatus": "COMPLETED"
                            }
                        }
                    },
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT40000002",
                                "briefTitle": "Trial 2"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug A"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease B"]
                            },
                            "designModule": {
                                "phases": ["PHASE2"]
                            },
                            "statusModule": {
                                "overallStatus": "TERMINATED"
                            }
                        }
                    }
                ],
                "totalCount": 2
            },
            "total_trials": 2,
            "confidence_score": 0.85,
            "agent_id": "clinical"
        }

        # Ingest
        evidence_list = parse_clinical_evidence(clinical_output)
        for evidence in evidence_list:
            self.ingestion_engine.ingest_evidence(evidence)

        drug_id = evidence_list[0].drug_id
        disease_id = evidence_list[0].disease_id

        # Explain
        explanation = self.conflict_reasoner.explain_conflict(drug_id, disease_id)

        # Assertions
        assert len(explanation["provenance_summary"]) == 2, "Should have provenance for both trials"

        # Check provenance structure
        for prov in explanation["provenance_summary"]:
            assert "agent_id" in prov
            assert "agent_name" in prov
            assert "api_source" in prov
            assert "raw_reference" in prov
            assert "extraction_timestamp" in prov
            assert "quality" in prov
            assert "confidence" in prov

        # Check that NCT IDs are present
        references = [p["raw_reference"] for p in explanation["provenance_summary"]]
        assert "NCT40000001" in references
        assert "NCT40000002" in references
