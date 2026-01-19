"""
Integration Tests: Dominant Evidence Determination

Tests the ConflictReasoner's ability to correctly identify dominant evidence
based on Quality > Confidence > Temporal ordering.

REQUIREMENTS:
- Create synthetic evidence with different quality/confidence/timestamps
- Ingest via AKGP (DO NOT bypass)
- Call ConflictReasoner.explain_conflict()
- Assert: Correct dominant evidence selected, Deterministic ranking
"""

import pytest
from datetime import datetime, timedelta

from akgp.graph_manager import GraphManager
from akgp.ingestion import IngestionEngine
from akgp.conflict_reasoning import ConflictReasoner
from normalization import parse_clinical_evidence


class TestDominantEvidenceDetermination:
    """Test dominant evidence determination logic"""

    def setup_method(self):
        """Setup fresh AKGP for each test"""
        self.graph = GraphManager()
        self.ingestion_engine = IngestionEngine(self.graph)
        self.conflict_reasoner = ConflictReasoner(self.graph)

    def test_high_quality_dominates_over_low_quality(self):
        """Test that HIGH quality evidence dominates over LOW quality"""
        # High quality evidence (Phase 3 completed)
        high_quality = {
            "query": "Drug M for Disease N",
            "summary": "Phase 3 completed",
            "comprehensive_summary": "Phase 3 trial completed successfully",
            "trials": [
                {
                    "nct_id": "NCT50000001",
                    "title": "Phase 3 Trial",
                    "phase": "Phase 3",
                    "status": "Completed",
                    "conditions": ["Disease N"],
                    "interventions": ["Drug M"],
                    "summary": "Success"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT50000001",
                                "briefTitle": "Phase 3 Trial"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug M"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease N"]
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
            "confidence_score": 0.85,
            "agent_id": "clinical"
        }

        # Low quality evidence (Phase 1 terminated)
        low_quality = {
            "query": "Drug M for Disease N",
            "summary": "Phase 1 terminated",
            "comprehensive_summary": "Phase 1 trial terminated",
            "trials": [
                {
                    "nct_id": "NCT50000002",
                    "title": "Phase 1 Trial",
                    "phase": "Phase 1",
                    "status": "Terminated",
                    "conditions": ["Disease N"],
                    "interventions": ["Drug M"],
                    "summary": "Failed"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT50000002",
                                "briefTitle": "Phase 1 Trial"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug M"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease N"]
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
            "confidence_score": 0.95,  # Even higher confidence
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
        # High quality should dominate despite lower confidence
        assert explanation["has_conflict"] is True
        assert "quality" in explanation["dominant_evidence"]["reason"].lower(), \
            "Dominance reason should mention quality"
        # The dominant evidence should be the Phase 3 trial (high quality)
        assert "NCT50000001" in explanation["dominant_evidence"]["reason"] or \
               "high" in explanation["dominant_evidence"]["reason"].lower()

    def test_higher_confidence_dominates_when_quality_equal(self):
        """Test that higher confidence wins when quality is equal"""
        # Both Phase 2 (MEDIUM quality), different confidence

        # Higher confidence
        high_conf = {
            "query": "Drug P for Disease Q",
            "summary": "Phase 2 high confidence",
            "comprehensive_summary": "Phase 2 trial with high confidence",
            "trials": [
                {
                    "nct_id": "NCT60000001",
                    "title": "Phase 2 Trial - High Confidence",
                    "phase": "Phase 2",
                    "status": "Completed",
                    "conditions": ["Disease Q"],
                    "interventions": ["Drug P"],
                    "summary": "High confidence"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT60000001",
                                "briefTitle": "Phase 2 Trial - High Confidence"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug P"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease Q"]
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
            "confidence_score": 0.95,
            "agent_id": "clinical"
        }

        # Lower confidence
        low_conf = {
            "query": "Drug P for Disease Q",
            "summary": "Phase 2 low confidence",
            "comprehensive_summary": "Phase 2 trial with low confidence",
            "trials": [
                {
                    "nct_id": "NCT60000002",
                    "title": "Phase 2 Trial - Low Confidence",
                    "phase": "Phase 2",
                    "status": "Terminated",
                    "conditions": ["Disease Q"],
                    "interventions": ["Drug P"],
                    "summary": "Low confidence"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT60000002",
                                "briefTitle": "Phase 2 Trial - Low Confidence"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug P"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease Q"]
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
            "confidence_score": 0.60,
            "agent_id": "clinical"
        }

        # Ingest both
        high_evidence = parse_clinical_evidence(high_conf)
        low_evidence = parse_clinical_evidence(low_conf)

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
        # Higher confidence should dominate
        assert "confidence" in explanation["dominant_evidence"]["reason"].lower() or \
               "0.95" in explanation["dominant_evidence"]["reason"]

    def test_quality_dominates_over_confidence(self):
        """Test that quality trumps confidence in dominance determination"""
        # High quality, low confidence (Phase 3, confidence 0.70)
        high_qual_low_conf = {
            "query": "Drug R for Disease S",
            "summary": "Phase 3 low confidence",
            "comprehensive_summary": "Phase 3 trial with lower confidence",
            "trials": [
                {
                    "nct_id": "NCT70000001",
                    "title": "Phase 3 Trial",
                    "phase": "Phase 3",
                    "status": "Completed",
                    "conditions": ["Disease S"],
                    "interventions": ["Drug R"],
                    "summary": "Phase 3"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT70000001",
                                "briefTitle": "Phase 3 Trial"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug R"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease S"]
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
            "confidence_score": 0.70,
            "agent_id": "clinical"
        }

        # Low quality, high confidence (Phase 1, confidence 0.95)
        low_qual_high_conf = {
            "query": "Drug R for Disease S",
            "summary": "Phase 1 high confidence",
            "comprehensive_summary": "Phase 1 trial with high confidence",
            "trials": [
                {
                    "nct_id": "NCT70000002",
                    "title": "Phase 1 Trial",
                    "phase": "Phase 1",
                    "status": "Terminated",
                    "conditions": ["Disease S"],
                    "interventions": ["Drug R"],
                    "summary": "Phase 1"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT70000002",
                                "briefTitle": "Phase 1 Trial"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug R"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease S"]
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
            "confidence_score": 0.95,
            "agent_id": "clinical"
        }

        # Ingest both
        high_qual = parse_clinical_evidence(high_qual_low_conf)
        low_qual = parse_clinical_evidence(low_qual_high_conf)

        for evidence in high_qual:
            self.ingestion_engine.ingest_evidence(evidence)

        for evidence in low_qual:
            self.ingestion_engine.ingest_evidence(evidence)

        drug_id = high_qual[0].drug_id
        disease_id = high_qual[0].disease_id

        # Explain
        explanation = self.conflict_reasoner.explain_conflict(drug_id, disease_id)

        # Assertions
        assert explanation["has_conflict"] is True
        # Quality should dominate (Phase 3 should win despite lower confidence)
        assert "quality" in explanation["dominant_evidence"]["reason"].lower() or \
               "HIGH" in explanation["dominant_evidence"]["reason"]

    def test_deterministic_ranking_same_inputs_same_output(self):
        """Test that ranking is deterministic - same inputs produce same output"""
        clinical_output = {
            "query": "Drug T for Disease U",
            "summary": "Multiple trials",
            "comprehensive_summary": "Multiple trials",
            "trials": [
                {
                    "nct_id": "NCT80000001",
                    "title": "Trial 1",
                    "phase": "Phase 3",
                    "status": "Completed",
                    "conditions": ["Disease U"],
                    "interventions": ["Drug T"],
                    "summary": "Trial 1"
                },
                {
                    "nct_id": "NCT80000002",
                    "title": "Trial 2",
                    "phase": "Phase 2",
                    "status": "Terminated",
                    "conditions": ["Disease U"],
                    "interventions": ["Drug T"],
                    "summary": "Trial 2"
                }
            ],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT80000001",
                                "briefTitle": "Trial 1"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug T"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease U"]
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
                                "nctId": "NCT80000002",
                                "briefTitle": "Trial 2"
                            },
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug T"}]
                            },
                            "conditionsModule": {
                                "conditions": ["Disease U"]
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

        # Call explain_conflict multiple times
        explanation1 = self.conflict_reasoner.explain_conflict(drug_id, disease_id)
        explanation2 = self.conflict_reasoner.explain_conflict(drug_id, disease_id)
        explanation3 = self.conflict_reasoner.explain_conflict(drug_id, disease_id)

        # Assertions - should be identical
        assert explanation1["dominant_evidence"]["evidence_id"] == explanation2["dominant_evidence"]["evidence_id"]
        assert explanation2["dominant_evidence"]["evidence_id"] == explanation3["dominant_evidence"]["evidence_id"]
        assert explanation1["severity"] == explanation2["severity"] == explanation3["severity"]
        assert explanation1["summary"] == explanation2["summary"] == explanation3["summary"]
