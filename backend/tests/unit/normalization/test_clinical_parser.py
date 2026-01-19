"""
Tests for Clinical Evidence Parser

Tests parsing of ClinicalAgent output into normalized AKGP Evidence.
"""

import pytest
from normalization.clinical_parser import parse_clinical_evidence, _parse_single_trial
from normalization.common import ParsingRejection, Polarity
from akgp.schema import SourceType, EvidenceQuality


class TestClinicalEvidenceParsing:
    """Test parsing of complete ClinicalAgent output"""

    def test_parse_clinical_evidence_success(self, mock_clinical_trials_response):
        """Test successful parsing of clinical agent output"""
        agent_output = {
            "summary": "Found 2 trials for GLP-1 diabetes",
            "comprehensive_summary": "Analysis of trials...",
            "trials": [
                {"nct_id": "NCT12345678", "title": "Phase 3 GLP-1 Trial"},
                {"nct_id": "NCT87654321", "title": "Phase 2 GLP-1 Trial"}
            ],
            "raw": mock_clinical_trials_response
        }

        result = parse_clinical_evidence(agent_output)

        # Should return list of NormalizedEvidence
        assert isinstance(result, list)
        assert len(result) > 0

        # Check first evidence
        first_evidence = result[0]
        assert first_evidence.evidence_node.agent_id == "clinical"
        assert first_evidence.evidence_node.source_type == SourceType.CLINICAL
        assert first_evidence.drug_id.startswith("drug_")
        assert first_evidence.disease_id.startswith("disease_")
        assert first_evidence.polarity in [Polarity.SUPPORTS, Polarity.SUGGESTS, Polarity.CONTRADICTS]

    def test_parse_clinical_evidence_missing_fields(self):
        """Test that missing required fields raises ParsingRejection"""
        agent_output = {
            "summary": "Found trials"
            # Missing 'trials' and 'raw'
        }

        with pytest.raises(ParsingRejection, match="Required field"):
            parse_clinical_evidence(agent_output)

    def test_parse_clinical_evidence_no_trials(self):
        """Test that no trials returns empty list"""
        agent_output = {
            "summary": "No trials found",
            "trials": [],
            "raw": {"studies": [], "totalCount": 0}
        }

        result = parse_clinical_evidence(agent_output)
        assert result == []

    def test_parse_clinical_evidence_filters_invalid_trials(self):
        """Test that invalid trials are filtered out"""
        agent_output = {
            "summary": "Found 2 trials",
            "trials": [{"nct_id": "NCT123", "title": "Trial"}],
            "raw": {
                "studies": [
                    # Valid trial
                    {
                        "protocolSection": {
                            "identificationModule": {"nctId": "NCT12345678", "briefTitle": "GLP-1 Trial"},
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "GLP-1"}]
                            },
                            "conditionsModule": {"conditions": ["Type 2 Diabetes"]},
                            "designModule": {"phases": ["PHASE3"]},
                            "statusModule": {"overallStatus": "COMPLETED"}
                        }
                    },
                    # Invalid trial (no drug)
                    {
                        "protocolSection": {
                            "identificationModule": {"nctId": "NCT99999999", "briefTitle": "Trial"},
                            "armsInterventionsModule": {"interventions": []},  # No drug
                            "conditionsModule": {"conditions": ["Diabetes"]},
                            "designModule": {"phases": ["PHASE2"]},
                            "statusModule": {"overallStatus": "RECRUITING"}
                        }
                    }
                ],
                "totalCount": 2
            }
        }

        result = parse_clinical_evidence(agent_output)

        # Should only return valid trial
        assert len(result) == 1
        assert result[0].evidence_node.raw_reference == "NCT12345678"


class TestSingleTrialParsing:
    """Test parsing of individual trials"""

    def test_parse_single_trial_phase3_completed(self):
        """Test Phase 3 completed trial → SUPPORTS polarity"""
        trial = {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT12345678", "briefTitle": "GLP-1 Phase 3 Trial"},
                "armsInterventionsModule": {
                    "interventions": [{"type": "DRUG", "name": "Semaglutide"}]
                },
                "conditionsModule": {"conditions": ["Type 2 Diabetes Mellitus"]},
                "designModule": {"phases": ["PHASE3"]},
                "statusModule": {"overallStatus": "COMPLETED"},
                "descriptionModule": {"briefSummary": "Efficacy study of GLP-1"}
            }
        }

        evidence = _parse_single_trial(trial)

        assert evidence.polarity == Polarity.SUPPORTS  # Completed Phase 3 = strong evidence
        assert evidence.evidence_node.quality == EvidenceQuality.HIGH
        assert evidence.evidence_node.confidence_score == 0.9

    def test_parse_single_trial_phase2_recruiting(self):
        """Test Phase 2 recruiting trial → SUGGESTS polarity"""
        trial = {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT87654321", "briefTitle": "GLP-1 Phase 2"},
                "armsInterventionsModule": {
                    "interventions": [{"type": "DRUG", "name": "GLP-1 analog"}]
                },
                "conditionsModule": {"conditions": ["Diabetes"]},
                "designModule": {"phases": ["PHASE2"]},
                "statusModule": {"overallStatus": "RECRUITING"},
                "descriptionModule": {"briefSummary": "Phase 2 trial"}
            }
        }

        evidence = _parse_single_trial(trial)

        assert evidence.polarity == Polarity.SUGGESTS  # Recruiting Phase 2 = promising but not proven
        assert evidence.evidence_node.quality == EvidenceQuality.MEDIUM
        assert 0.6 <= evidence.evidence_node.confidence_score <= 0.7

    def test_parse_single_trial_terminated(self):
        """Test terminated trial → CONTRADICTS polarity"""
        trial = {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT11111111", "briefTitle": "Failed Trial"},
                "armsInterventionsModule": {
                    "interventions": [{"type": "DRUG", "name": "Test Drug"}]
                },
                "conditionsModule": {"conditions": ["Cancer"]},
                "designModule": {"phases": ["PHASE2"]},
                "statusModule": {"overallStatus": "TERMINATED"},
                "descriptionModule": {"briefSummary": "Trial was terminated early"}
            }
        }

        evidence = _parse_single_trial(trial)

        assert evidence.polarity == Polarity.CONTRADICTS  # Terminated = negative evidence
        assert evidence.evidence_node.confidence_score == 0.3

    def test_parse_single_trial_missing_nct_id(self):
        """Test that missing NCT ID raises ParsingRejection"""
        trial = {
            "protocolSection": {
                "identificationModule": {},  # No nctId
                "armsInterventionsModule": {"interventions": [{"type": "DRUG", "name": "Drug"}]},
                "conditionsModule": {"conditions": ["Disease"]}
            }
        }

        with pytest.raises(ParsingRejection, match="Missing NCT ID"):
            _parse_single_trial(trial)

    def test_parse_single_trial_no_drug(self):
        """Test that trial with no drug intervention is rejected"""
        trial = {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT12345678", "briefTitle": "Trial"},
                "armsInterventionsModule": {
                    "interventions": [{"type": "OTHER", "name": "Placebo"}]  # No DRUG type
                },
                "conditionsModule": {"conditions": ["Diabetes"]},
                "designModule": {"phases": ["PHASE2"]},
                "statusModule": {"overallStatus": "RECRUITING"}
            }
        }

        with pytest.raises(ParsingRejection, match="No drug interventions found"):
            _parse_single_trial(trial)

    def test_parse_single_trial_no_disease(self):
        """Test that trial with no conditions is rejected"""
        trial = {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT12345678", "briefTitle": "Trial"},
                "armsInterventionsModule": {
                    "interventions": [{"type": "DRUG", "name": "GLP-1"}]
                },
                "conditionsModule": {"conditions": []},  # No conditions
                "designModule": {"phases": ["PHASE2"]},
                "statusModule": {"overallStatus": "RECRUITING"}
            }
        }

        with pytest.raises(ParsingRejection, match="No conditions found"):
            _parse_single_trial(trial)

    def test_parse_single_trial_deterministic(self):
        """Test that parsing same trial twice produces identical results"""
        trial = {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT12345678", "briefTitle": "GLP-1 Trial"},
                "armsInterventionsModule": {
                    "interventions": [{"type": "DRUG", "name": "GLP-1"}]
                },
                "conditionsModule": {"conditions": ["Type 2 Diabetes"]},
                "designModule": {"phases": ["PHASE3"]},
                "statusModule": {"overallStatus": "COMPLETED"},
                "descriptionModule": {"briefSummary": "Efficacy study"}
            }
        }

        evidence1 = _parse_single_trial(trial)
        evidence2 = _parse_single_trial(trial)

        # IDs should be identical (deterministic)
        assert evidence1.drug_id == evidence2.drug_id
        assert evidence1.disease_id == evidence2.disease_id
        assert evidence1.polarity == evidence2.polarity
        assert evidence1.evidence_node.quality == evidence2.evidence_node.quality
        assert evidence1.evidence_node.confidence_score == evidence2.evidence_node.confidence_score


class TestClinicalEvidenceNodeStructure:
    """Test that generated EvidenceNode has correct structure"""

    def test_evidence_node_has_required_fields(self):
        """Test that EvidenceNode contains all required AKGP fields"""
        agent_output = {
            "summary": "Found 1 trial",
            "trials": [{"nct_id": "NCT12345678", "title": "Trial"}],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {"nctId": "NCT12345678", "briefTitle": "GLP-1 Trial"},
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "GLP-1"}]
                            },
                            "conditionsModule": {"conditions": ["Diabetes"]},
                            "designModule": {"phases": ["PHASE2"]},
                            "statusModule": {"overallStatus": "RECRUITING"},
                            "descriptionModule": {"briefSummary": "Trial summary"}
                        }
                    }
                ],
                "totalCount": 1
            }
        }

        result = parse_clinical_evidence(agent_output)
        evidence_node = result[0].evidence_node

        # Required AKGP fields
        assert evidence_node.name
        assert evidence_node.source == "ClinicalTrials.gov"
        assert evidence_node.agent_name == "Clinical Agent"
        assert evidence_node.agent_id == "clinical"
        assert evidence_node.api_source == "ClinicalTrials.gov v2 API"
        assert evidence_node.raw_reference == "NCT12345678"
        assert evidence_node.extraction_timestamp is not None
        assert evidence_node.source_type == SourceType.CLINICAL
        assert evidence_node.quality in [EvidenceQuality.LOW, EvidenceQuality.MEDIUM, EvidenceQuality.HIGH]
        assert 0.0 <= evidence_node.confidence_score <= 1.0
        assert evidence_node.summary
        assert isinstance(evidence_node.metadata, dict)

    def test_evidence_node_confidence_clamped(self):
        """Test that confidence is always in [0, 1] range"""
        agent_output = {
            "summary": "Found 1 trial",
            "trials": [{"nct_id": "NCT12345678", "title": "Trial"}],
            "raw": {
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {"nctId": "NCT12345678", "briefTitle": "Trial"},
                            "armsInterventionsModule": {
                                "interventions": [{"type": "DRUG", "name": "Drug"}]
                            },
                            "conditionsModule": {"conditions": ["Disease"]},
                            "designModule": {"phases": ["UNKNOWN"]},
                            "statusModule": {"overallStatus": "UNKNOWN"},
                            "descriptionModule": {"briefSummary": "Summary"}
                        }
                    }
                ],
                "totalCount": 1
            }
        }

        result = parse_clinical_evidence(agent_output)
        confidence = result[0].evidence_node.confidence_score

        assert 0.0 <= confidence <= 1.0
