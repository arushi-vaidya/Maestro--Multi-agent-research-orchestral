"""
Tests for Common Normalization Utilities

Tests determinism, validation, entity extraction, and ID generation.
"""

import pytest
from normalization.common import (
    normalize_entity_name,
    generate_canonical_id,
    extract_drug_mentions,
    extract_disease_mentions,
    validate_confidence,
    validate_required_fields,
    determine_quality_from_phase,
    determine_quality_from_patent_status,
    determine_quality_from_publication_type,
    ParsingRejection,
    NormalizedEvidence
)
from akgp.schema import EvidenceNode, SourceType, EvidenceQuality


class TestEntityNormalization:
    """Test entity name normalization"""

    def test_normalize_entity_name_lowercase(self):
        """Test lowercase conversion"""
        assert normalize_entity_name("GLP-1") == "glp-1"
        assert normalize_entity_name("Type 2 Diabetes") == "type 2 diabetes"

    def test_normalize_entity_name_strips_whitespace(self):
        """Test whitespace stripping"""
        assert normalize_entity_name("  GLP-1  ") == "glp-1"
        assert normalize_entity_name("Type  2   Diabetes") == "type 2 diabetes"

    def test_normalize_entity_name_removes_special_chars(self):
        """Test special character removal (except hyphens)"""
        assert normalize_entity_name("GLP-1 (Receptor Agonist)") == "glp-1 receptor agonist"
        assert normalize_entity_name("Type-2 Diabetes!") == "type-2 diabetes"

    def test_normalize_entity_name_deterministic(self):
        """Test that normalization is deterministic"""
        # Same input should always produce same output
        name1 = normalize_entity_name("GLP-1")
        name2 = normalize_entity_name("GLP-1")
        assert name1 == name2

    def test_normalize_entity_name_empty_raises(self):
        """Test that empty name raises ValueError"""
        with pytest.raises(ValueError, match="Entity name cannot be empty"):
            normalize_entity_name("")


class TestCanonicalIDGeneration:
    """Test canonical ID generation"""

    def test_generate_canonical_id_deterministic(self):
        """Test that same entity always generates same ID"""
        id1 = generate_canonical_id("GLP-1", "drug")
        id2 = generate_canonical_id("GLP-1", "drug")
        assert id1 == id2

    def test_generate_canonical_id_case_insensitive(self):
        """Test that case variations produce same ID"""
        id1 = generate_canonical_id("GLP-1", "drug")
        id2 = generate_canonical_id("glp-1", "drug")
        assert id1 == id2

    def test_generate_canonical_id_whitespace_insensitive(self):
        """Test that whitespace variations produce same ID"""
        id1 = generate_canonical_id("Type 2 Diabetes", "disease")
        id2 = generate_canonical_id("  Type  2  Diabetes  ", "disease")
        assert id1 == id2

    def test_generate_canonical_id_format(self):
        """Test ID format (prefix + hash)"""
        drug_id = generate_canonical_id("GLP-1", "drug")
        disease_id = generate_canonical_id("Diabetes", "disease")

        assert drug_id.startswith("drug_")
        assert disease_id.startswith("disease_")
        assert len(drug_id.split("_")[1]) == 16  # 16-char hash

    def test_generate_canonical_id_different_entities_different_ids(self):
        """Test that different entities produce different IDs"""
        id1 = generate_canonical_id("GLP-1", "drug")
        id2 = generate_canonical_id("GLP-2", "drug")
        assert id1 != id2

    def test_generate_canonical_id_invalid_type_raises(self):
        """Test that invalid entity type raises ValueError"""
        with pytest.raises(ValueError, match="Invalid entity_type"):
            generate_canonical_id("GLP-1", "invalid_type")


class TestEntityExtraction:
    """Test drug/disease extraction from text"""

    def test_extract_drug_mentions_glp1(self):
        """Test extraction of GLP-1 drug pattern"""
        text = "This study evaluates GLP-1 receptor agonists"
        drugs = extract_drug_mentions(text)
        assert "glp-1" in drugs

    def test_extract_drug_mentions_antibody(self):
        """Test extraction of -mab antibodies"""
        text = "Treatment with pembrolizumab showed efficacy"
        drugs = extract_drug_mentions(text)
        assert "pembrolizumab" in drugs

    def test_extract_drug_mentions_common_names(self):
        """Test extraction of common drug names"""
        text = "Patients received metformin or insulin"
        drugs = extract_drug_mentions(text)
        assert "metformin" in drugs or "insulin" in drugs

    def test_extract_drug_mentions_empty_text(self):
        """Test extraction from empty text"""
        assert extract_drug_mentions("") == []
        assert extract_drug_mentions(None) == []

    def test_extract_disease_mentions_diabetes(self):
        """Test extraction of diabetes patterns"""
        text = "Study in type 2 diabetes patients"
        diseases = extract_disease_mentions(text)
        assert "type 2 diabetes" in diseases

    def test_extract_disease_mentions_cancer(self):
        """Test extraction of cancer patterns"""
        text = "Lung cancer treatment options"
        diseases = extract_disease_mentions(text)
        assert "cancer" in diseases

    def test_extract_disease_mentions_empty_text(self):
        """Test extraction from empty text"""
        assert extract_disease_mentions("") == []
        assert extract_disease_mentions(None) == []


class TestValidation:
    """Test validation utilities"""

    def test_validate_confidence_clamps_high(self):
        """Test that confidence > 1.0 is clamped to 1.0"""
        assert validate_confidence(1.5) == 1.0
        assert validate_confidence(100.0) == 1.0

    def test_validate_confidence_clamps_low(self):
        """Test that confidence < 0.0 is clamped to 0.0"""
        assert validate_confidence(-0.5) == 0.0
        assert validate_confidence(-100.0) == 0.0

    def test_validate_confidence_valid_range(self):
        """Test that valid confidence is unchanged"""
        assert validate_confidence(0.5) == 0.5
        assert validate_confidence(0.0) == 0.0
        assert validate_confidence(1.0) == 1.0

    def test_validate_confidence_none_raises(self):
        """Test that None raises ParsingRejection"""
        with pytest.raises(ParsingRejection, match="Confidence score is required"):
            validate_confidence(None)

    def test_validate_required_fields_success(self):
        """Test successful validation"""
        data = {"field1": "value1", "field2": "value2"}
        # Should not raise
        validate_required_fields(data, ["field1", "field2"])

    def test_validate_required_fields_missing_field(self):
        """Test that missing field raises ParsingRejection"""
        data = {"field1": "value1"}
        with pytest.raises(ParsingRejection, match="Required field 'field2' missing"):
            validate_required_fields(data, ["field1", "field2"])

    def test_validate_required_fields_none_value(self):
        """Test that None value raises ParsingRejection"""
        data = {"field1": None}
        with pytest.raises(ParsingRejection, match="Required field 'field1' is None"):
            validate_required_fields(data, ["field1"])

    def test_validate_required_fields_empty_string(self):
        """Test that empty string raises ParsingRejection"""
        data = {"field1": ""}
        with pytest.raises(ParsingRejection, match="Required field 'field1' is empty"):
            validate_required_fields(data, ["field1"])


class TestQualityDetermination:
    """Test quality determination functions"""

    def test_determine_quality_from_phase_high(self):
        """Test Phase 3/4 → HIGH quality"""
        assert determine_quality_from_phase("PHASE3") == EvidenceQuality.HIGH
        assert determine_quality_from_phase("Phase 3") == EvidenceQuality.HIGH
        assert determine_quality_from_phase("PHASE4") == EvidenceQuality.HIGH

    def test_determine_quality_from_phase_medium(self):
        """Test Phase 2 → MEDIUM quality"""
        assert determine_quality_from_phase("PHASE2") == EvidenceQuality.MEDIUM
        assert determine_quality_from_phase("Phase 2") == EvidenceQuality.MEDIUM

    def test_determine_quality_from_phase_low(self):
        """Test Phase 1 → LOW quality"""
        assert determine_quality_from_phase("PHASE1") == EvidenceQuality.LOW
        assert determine_quality_from_phase("Phase 1") == EvidenceQuality.LOW
        assert determine_quality_from_phase("Early Phase 1") == EvidenceQuality.LOW

    def test_determine_quality_from_phase_unknown(self):
        """Test unknown phase → MEDIUM (conservative)"""
        assert determine_quality_from_phase("UNKNOWN") == EvidenceQuality.MEDIUM
        assert determine_quality_from_phase("") == EvidenceQuality.MEDIUM

    def test_determine_quality_from_patent_status_granted(self):
        """Test granted patent → MEDIUM quality"""
        assert determine_quality_from_patent_status("Granted") == EvidenceQuality.MEDIUM
        assert determine_quality_from_patent_status("Issued") == EvidenceQuality.MEDIUM

    def test_determine_quality_from_patent_status_pending(self):
        """Test pending patent → LOW quality"""
        assert determine_quality_from_patent_status("Pending") == EvidenceQuality.LOW
        assert determine_quality_from_patent_status("Filed") == EvidenceQuality.LOW

    def test_determine_quality_from_publication_type_high(self):
        """Test meta-analysis → HIGH quality"""
        assert determine_quality_from_publication_type("meta-analysis") == EvidenceQuality.HIGH
        assert determine_quality_from_publication_type("systematic review") == EvidenceQuality.HIGH

    def test_determine_quality_from_publication_type_medium(self):
        """Test RCT → MEDIUM quality"""
        assert determine_quality_from_publication_type("rct") == EvidenceQuality.MEDIUM
        assert determine_quality_from_publication_type("clinical trial") == EvidenceQuality.MEDIUM

    def test_determine_quality_from_publication_type_low(self):
        """Test case study → LOW quality"""
        assert determine_quality_from_publication_type("case study") == EvidenceQuality.LOW
        assert determine_quality_from_publication_type("review") == EvidenceQuality.LOW


class TestDeterminism:
    """Test that all functions are deterministic (same input → same output)"""

    def test_normalization_deterministic_multiple_calls(self):
        """Test 100 calls produce identical output"""
        results = [normalize_entity_name("GLP-1 Receptor Agonist") for _ in range(100)]
        assert len(set(results)) == 1  # All results identical

    def test_id_generation_deterministic_multiple_calls(self):
        """Test 100 calls produce identical ID"""
        results = [generate_canonical_id("GLP-1", "drug") for _ in range(100)]
        assert len(set(results)) == 1  # All IDs identical

    def test_extraction_deterministic(self):
        """Test extraction is deterministic"""
        text = "GLP-1 for type 2 diabetes"
        drugs1 = extract_drug_mentions(text)
        drugs2 = extract_drug_mentions(text)
        diseases1 = extract_disease_mentions(text)
        diseases2 = extract_disease_mentions(text)

        assert drugs1 == drugs2
        assert diseases1 == diseases2
