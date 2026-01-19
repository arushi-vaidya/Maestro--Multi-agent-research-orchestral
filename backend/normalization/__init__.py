"""
Evidence Normalization Layer for MAESTRO / PharmaGraph

This module provides deterministic parsers that convert agent outputs
into strict AKGP EvidenceNode objects.

This is the ONLY bridge between agents and AKGP.

DESIGN PRINCIPLES:
- 100% deterministic (same input → same output)
- No ML models, no LLMs
- Reject malformed data (fail-fast)
- No hallucination (only extract what exists)
- Canonical entity IDs (stable across runs)

EXPORTS:
- Parsers: parse_clinical_evidence, parse_patent_evidence, parse_market_evidence, parse_literature_evidence
- Common utilities: NormalizedEvidence, ParsingRejection, generate_canonical_id
- Quality/polarity determination functions
"""

# Common utilities
from .common import (
    NormalizedEvidence,
    ParsingRejection,
    Polarity,
    generate_canonical_id,
    normalize_entity_name,
    extract_drug_mentions,
    extract_disease_mentions,
    validate_confidence,
    validate_required_fields,
    determine_quality_from_phase,
    determine_quality_from_patent_status,
    determine_quality_from_publication_type,
    get_utc_timestamp
)

# Parsers
from .clinical_parser import parse_clinical_evidence
from .patent_parser import parse_patent_evidence
from .market_parser import parse_market_evidence
from .literature_parser import parse_literature_evidence


__all__ = [
    # Common utilities
    "NormalizedEvidence",
    "ParsingRejection",
    "Polarity",
    "generate_canonical_id",
    "normalize_entity_name",
    "extract_drug_mentions",
    "extract_disease_mentions",
    "validate_confidence",
    "validate_required_fields",
    "determine_quality_from_phase",
    "determine_quality_from_patent_status",
    "determine_quality_from_publication_type",
    "get_utc_timestamp",
    # Parsers
    "parse_clinical_evidence",
    "parse_patent_evidence",
    "parse_market_evidence",
    "parse_literature_evidence",
]
