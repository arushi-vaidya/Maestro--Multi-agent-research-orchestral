"""
Integration Tests: Conflict Severity Classification

Tests the ConflictReasoner's ability to correctly classify conflict severity
as LOW, MEDIUM, or HIGH based on evidence quality.

REQUIREMENTS:
- Create synthetic evidence with different quality combinations
- Ingest via AKGP (DO NOT bypass)
- Call ConflictReasoner.explain_conflict()
- Assert: Correct severity classification, Deterministic
"""

import pytest

from akgp.graph_manager import GraphManager
from akgp.ingestion import IngestionEngine
from akgp.conflict_reasoning import ConflictReasoner, ConflictSeverity
from normalization import parse_clinical_evidence


class TestConflictSeverityClassification:
    """Test conflict severity classification"""

    def setup_method(self):
        """Setup fresh AKGP for each test"""
        self.graph = GraphManager()
        self.ingestion_engine = IngestionEngine(self.graph)
        self.conflict_reasoner = ConflictReasoner(self.graph)

    def test_high_severity_both_high_quality(self):
        """Test HIGH severity when both sides have HIGH quality evidence"""
        # Phase 3 completed (HIGH quality, SUPPORTS)
        supports_high = {
            "query": "Drug V for Disease W",
            "summary": "Phase 3 completed",
            "comprehensive_summary": "Phase 3 trial completed successfully",
            "trials": [
                {
                    "nct_id": "NCT90000001",
                    "title": "Phase 3 Success",
                    "phase": "Phase 3",
                    "status": "Completed",
                    "conditions": ["Disease W"],
                    "interventions": ["Drug V"],
                    "summary": "Success"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT90000001",
                                "briefTitle": "Phase 3 Success"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug V"}]
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

        # Phase 4 terminated (HIGH quality, CONTRADICTS)
        contradicts_high = {
            "query": "Drug V for Disease W",
            "summary": "Phase 4 terminated",
            "comprehensive_summary": "Phase 4 trial terminated due to adverse events",
            "trials": [
                {
                    "nct_id": "NCT90000002",
                    "title": "Phase 4 Terminated",
                    "phase": "Phase 4",
                    "status": "Terminated",
                    "conditions": ["Disease W"],
                    "interventions": ["Drug V"],
                    "summary": "Terminated"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT90000002",
                                "briefTitle": "Phase 4 Terminated"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug V"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease W"]
                            },
                            "designModule": {
                                "phases": ["PHASE4"]
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

        # Ingest both
        supports = parse_clinical_evidence(supports_high)
        contradicts = parse_clinical_evidence(contradicts_high)

        for evidence in supports:
            self.ingestion_engine.ingest_evidence(evidence)

        for evidence in contradicts:
            self.ingestion_engine.ingest_evidence(evidence)

        drug_id = supports[0].drug_id
        disease_id = supports[0].disease_id

        # Explain
        explanation = self.conflict_reasoner.explain_conflict(drug_id, disease_id)

        # Assertions
        assert explanation["has_conflict"] is True
        assert explanation["severity"] == ConflictSeverity.HIGH.value, \
            "Should be HIGH severity when both sides have HIGH quality evidence"

    def test_medium_severity_one_high_one_low(self):
        """Test MEDIUM severity when one side has HIGH quality, other has LOW"""
        # Phase 3 completed (HIGH quality)
        high_quality = {
            "query": "Drug X for Disease Y",
            "summary": "Phase 3 completed",
            "comprehensive_summary": "Phase 3 trial completed",
            "trials": [
                {
                    "nct_id": "NCTA0000001",
                    "title": "Phase 3 Trial",
                    "phase": "Phase 3",
                    "status": "Completed",
                    "conditions": ["Disease Y"],
                    "interventions": ["Drug X"],
                    "summary": "Phase 3"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCTA0000001",
                                "briefTitle": "Phase 3 Trial"
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
            "confidence_score": 0.90,
            "agent_id": "clinical"
        }

        # Phase 1 terminated (LOW quality)
        low_quality = {
            "query": "Drug X for Disease Y",
            "summary": "Phase 1 terminated",
            "comprehensive_summary": "Phase 1 trial terminated",
            "trials": [
                {
                    "nct_id": "NCTA0000002",
                    "title": "Phase 1 Trial",
                    "phase": "Phase 1",
                    "status": "Terminated",
                    "conditions": ["Disease Y"],
                    "interventions": ["Drug X"],
                    "summary": "Phase 1"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCTA0000002",
                                "briefTitle": "Phase 1 Trial"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug X"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease Y"]
                            },
                            "designModule": {
                                "phases": ["PHASE1"]
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

        # Ingest both
        high_evidence = parse_clinical_evidence(high_quality)
        low_evidence = parse_clinical_evidence(low_quality)

        for evidence in high_evidence:
            self.ingestion_engine.ingest_evidence(evidence)

        for evidence in low_evidence:
            self.ingestion_engine.ingest_evidence(evidence)

        drug_id = high_evidence[0].drug_id
        disease_id = high_evidence[0].disease_id

        # Explain
        explanation = self.conflict_reasoner.explain_conflict(drug_id, disease_id)

        # Assertions
        assert explanation["has_conflict"] is True
        assert explanation["severity"] == ConflictSeverity.MEDIUM.value, \
            "Should be MEDIUM severity when one side has HIGH quality, other has LOW"

    def test_low_severity_both_low_quality(self):
        """Test LOW severity when both sides have LOW or MEDIUM quality"""
        # Phase 2 completed (MEDIUM quality, SUPPORTS)
        low_quality_1 = {
            "query": "Drug Z for Disease A",
            "summary": "Phase 2 completed",
            "comprehensive_summary": "Phase 2 trial completed",
            "trials": [
                {
                    "nct_id": "NCTB0000001",
                    "title": "Phase 2 Trial",
                    "phase": "Phase 2",
                    "status": "Completed",
                    "conditions": ["Disease A"],
                    "interventions": ["Drug Z"],
                    "summary": "Phase 2"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCTB0000001",
                                "briefTitle": "Phase 2 Trial"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug Z"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease A"]
                            },
                            "designModule": {
                                "phases": ["PHASE2"]
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
            "confidence_score": 0.70,
            "agent_id": "clinical"
        }

        # Phase 2 terminated (MEDIUM quality)
        medium_quality = {
            "query": "Drug Z for Disease A",
            "summary": "Phase 2 terminated",
            "comprehensive_summary": "Phase 2 trial terminated",
            "trials": [
                {
                    "nct_id": "NCTB0000002",
                    "title": "Phase 2 Trial",
                    "phase": "Phase 2",
                    "status": "Terminated",
                    "conditions": ["Disease A"],
                    "interventions": ["Drug Z"],
                    "summary": "Phase 2"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCTB0000002",
                                "briefTitle": "Phase 2 Trial"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug Z"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease A"]
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
            "confidence_score": 0.75,
            "agent_id": "clinical"
        }

        # Ingest both
        low_evidence = parse_clinical_evidence(low_quality_1)
        medium_evidence = parse_clinical_evidence(medium_quality)

        for evidence in low_evidence:
            self.ingestion_engine.ingest_evidence(evidence)

        for evidence in medium_evidence:
            self.ingestion_engine.ingest_evidence(evidence)

        drug_id = low_evidence[0].drug_id
        disease_id = low_evidence[0].disease_id

        # Explain
        explanation = self.conflict_reasoner.explain_conflict(drug_id, disease_id)

        # Assertions
        assert explanation["has_conflict"] is True
        assert explanation["severity"] == ConflictSeverity.LOW.value, \
            "Should be LOW severity when both sides have LOW/MEDIUM quality"

    def test_severity_is_deterministic(self):
        """Test that severity classification is deterministic"""
        clinical_output = {
            "query": "Drug B for Disease C",
            "summary": "Conflicting trials",
            "comprehensive_summary": "Conflicting trials",
            "trials": [
                {
                    "nct_id": "NCTC0000001",
                    "title": "Phase 3 Success",
                    "phase": "Phase 3",
                    "status": "Completed",
                    "conditions": ["Disease C"],
                    "interventions": ["Drug B"],
                    "summary": "Success"
                },
                {
                    "nct_id": "NCTC0000002",
                    "title": "Phase 3 Terminated",
                    "phase": "Phase 3",
                    "status": "Terminated",
                    "conditions": ["Disease C"],
                    "interventions": ["Drug B"],
                    "summary": "Terminated"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCTC0000001",
                                "briefTitle": "Phase 3 Success"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug B"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease C"]
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
                                "nctId": "NCTC0000002",
                                "briefTitle": "Phase 3 Terminated"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug B"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease C"]
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

        # Call multiple times
        explanation1 = self.conflict_reasoner.explain_conflict(drug_id, disease_id)
        explanation2 = self.conflict_reasoner.explain_conflict(drug_id, disease_id)
        explanation3 = self.conflict_reasoner.explain_conflict(drug_id, disease_id)

        # Assertions - severity should be identical across calls
        assert explanation1["severity"] == explanation2["severity"]
        assert explanation2["severity"] == explanation3["severity"]
        # Should be HIGH (both Phase 3)
        assert explanation1["severity"] == ConflictSeverity.HIGH.value

    def test_no_conflict_has_no_severity(self):
        """Test that when no conflict exists, severity is None"""
        clinical_output = {
            "query": "Drug D for Disease E",
            "summary": "All trials support",
            "comprehensive_summary": "All trials support efficacy",
            "trials": [
                {
                    "nct_id": "NCTD0000001",
                    "title": "Phase 3 Success",
                    "phase": "Phase 3",
                    "status": "Completed",
                    "conditions": ["Disease E"],
                    "interventions": ["Drug D"],
                    "summary": "Success"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCTD0000001",
                                "briefTitle": "Phase 3 Success"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug D"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease E"]
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

        # Ingest
        evidence_list = parse_clinical_evidence(clinical_output)
        for evidence in evidence_list:
            self.ingestion_engine.ingest_evidence(evidence)

        drug_id = evidence_list[0].drug_id
        disease_id = evidence_list[0].disease_id

        # Explain
        explanation = self.conflict_reasoner.explain_conflict(drug_id, disease_id)

        # Assertions
        assert explanation["has_conflict"] is False
        assert explanation["severity"] is None, "Should have no severity when no conflict exists"
