"""
Common utilities for Evidence Normalization Layer

This module provides shared functionality for all parsers:
- Canonical ID generation (deterministic)
- Entity normalization (drug/disease)
- Validation logic
- Output data models

DESIGN PRINCIPLES:
- 100% deterministic (same input → same output)
- No ML models, no LLMs
- Reject malformed data (fail-fast)
- No hallucination (only extract what exists)
"""

import re
import hashlib
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, validator
from akgp.schema import EvidenceNode, SourceType, EvidenceQuality


# ==============================================================================
# ENUMS
# ==============================================================================

class Polarity(str):
    """
    Polarity of evidence (determines relationship type in AKGP)

    - SUPPORTS: Strong positive evidence (e.g., Phase 3 success, granted patent)
    - CONTRADICTS: Negative evidence (e.g., trial failure, patent rejection)
    - SUGGESTS: Weak/speculative evidence (e.g., Phase 1 trial, market forecast)
    """
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    SUGGESTS = "SUGGESTS"


# ==============================================================================
# OUTPUT MODEL
# ==============================================================================

class NormalizedEvidence(BaseModel):
    """
    Normalized evidence output from parser

    This is what parsers return - it includes:
    1. The EvidenceNode (for AKGP storage)
    2. Extracted entities (drug_id, disease_id)
    3. Relationship type (polarity)

    This structure bridges agent output → AKGP ingestion
    """
    evidence_node: EvidenceNode
    drug_id: str = Field(..., min_length=1, description="Canonical drug identifier")
    disease_id: str = Field(..., min_length=1, description="Canonical disease identifier")
    polarity: Literal["SUPPORTS", "CONTRADICTS", "SUGGESTS"]

    @validator('drug_id', 'disease_id')
    def validate_ids(cls, v):
        """Ensure IDs are non-empty and trimmed"""
        if not v or not v.strip():
            raise ValueError("Entity IDs must be non-empty")
        return v.strip()


class ParsingRejection(Exception):
    """
    Raised when agent output cannot be parsed into valid evidence

    This is expected behavior - not all agent outputs are valid evidence.
    Examples:
    - No drug/disease mentioned
    - Ambiguous polarity
    - Missing required fields
    """
    pass


# ==============================================================================
# ENTITY NORMALIZATION (DETERMINISTIC)
# ==============================================================================

def normalize_entity_name(name: str) -> str:
    """
    Normalize entity name to canonical form

    Rules:
    - Lowercase
    - Strip whitespace
    - Remove special characters (except hyphens)
    - Collapse multiple spaces

    Args:
        name: Raw entity name (e.g., "GLP-1", "Type 2 Diabetes")

    Returns:
        Normalized name (e.g., "glp-1", "type 2 diabetes")

    Examples:
        >>> normalize_entity_name("  GLP-1  ")
        'glp-1'
        >>> normalize_entity_name("Type 2 Diabetes")
        'type 2 diabetes'
    """
    if not name:
        raise ValueError("Entity name cannot be empty")

    # Lowercase
    name = name.lower().strip()

    # Remove special characters (keep alphanumeric, spaces, hyphens)
    name = re.sub(r'[^a-z0-9\s\-]', '', name)

    # Collapse multiple spaces/hyphens
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'\-+', '-', name)

    return name.strip()


def generate_canonical_id(entity_name: str, entity_type: str) -> str:
    """
    Generate deterministic canonical ID for an entity

    Uses SHA256 hash of normalized name to ensure:
    - Same entity → same ID (deterministic)
    - Different entities → different IDs (collision-resistant)
    - ID is stable across runs

    Args:
        entity_name: Raw entity name
        entity_type: "drug" or "disease"

    Returns:
        Canonical ID (e.g., "drug_a3f2b1c...")

    Examples:
        >>> generate_canonical_id("GLP-1", "drug")
        'drug_6e8f9a2b...'
        >>> generate_canonical_id("Type 2 Diabetes", "disease")
        'disease_4c7d3e1f...'
    """
    if entity_type not in ["drug", "disease"]:
        raise ValueError(f"Invalid entity_type: {entity_type}")

    # Normalize name first
    normalized = normalize_entity_name(entity_name)

    if not normalized:
        raise ValueError(f"Entity name '{entity_name}' normalizes to empty string")

    # Generate stable hash
    hash_input = f"{entity_type}:{normalized}"
    hash_digest = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:16]

    return f"{entity_type}_{hash_digest}"


# ==============================================================================
# DRUG/DISEASE EXTRACTION (DETERMINISTIC PATTERNS)
# ==============================================================================

# Common drug name patterns (simplified - not exhaustive)
DRUG_PATTERNS = [
    r'\b([A-Z][a-z]+-\d+)\b',  # GLP-1, IL-2, etc.
    r'\b([A-Z][a-z]+mab)\b',   # Antibodies ending in -mab
    r'\b([A-Z][a-z]+nib)\b',   # Kinase inhibitors ending in -nib
    r'\b(semaglutide|metformin|insulin|ozempic|wegovy|mounjaro)\b',  # Common drugs (lowercase patterns)
]

# Common disease patterns
DISEASE_PATTERNS = [
    r'\b(type\s+\d+\s+diabetes)\b',
    r'\b(diabetes\s+mellitus)\b',
    r'\b(cancer|carcinoma|lymphoma|leukemia|sarcoma)\b',
    r'\b(alzheimer\'?s?|parkinson\'?s?)\b',
    r'\b(hypertension|obesity|asthma|copd)\b',
]


def extract_drug_mentions(text: str) -> List[str]:
    """
    Extract potential drug mentions from text using patterns

    This is a simple heuristic-based extraction (no ML).
    Returns all potential matches - caller must validate.

    Args:
        text: Text to search (case-insensitive)

    Returns:
        List of potential drug names (deduplicated, normalized)
    """
    if not text:
        return []

    text_lower = text.lower()
    mentions = set()

    for pattern in DRUG_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        mentions.update(matches)

    # Normalize all mentions
    return [normalize_entity_name(m) for m in mentions if m]


def extract_disease_mentions(text: str) -> List[str]:
    """
    Extract potential disease mentions from text using patterns

    This is a simple heuristic-based extraction (no ML).
    Returns all potential matches - caller must validate.

    Args:
        text: Text to search (case-insensitive)

    Returns:
        List of potential disease names (deduplicated, normalized)
    """
    if not text:
        return []

    text_lower = text.lower()
    mentions = set()

    for pattern in DISEASE_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        mentions.update(matches)

    # Normalize all mentions
    return [normalize_entity_name(m) for m in mentions if m]


# ==============================================================================
# VALIDATION UTILITIES
# ==============================================================================

def validate_confidence(confidence: Optional[float]) -> float:
    """
    Validate and clamp confidence score

    Args:
        confidence: Raw confidence score (may be None or out of range)

    Returns:
        Clamped confidence in [0.0, 1.0]

    Raises:
        ParsingRejection: If confidence is None or invalid type
    """
    if confidence is None:
        raise ParsingRejection("Confidence score is required but was None")

    if not isinstance(confidence, (int, float)):
        raise ParsingRejection(f"Confidence must be numeric, got {type(confidence)}")

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, float(confidence)))


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that required fields exist and are non-empty

    Args:
        data: Data dictionary
        required_fields: List of required field names

    Raises:
        ParsingRejection: If any required field is missing or empty
    """
    for field in required_fields:
        if field not in data:
            raise ParsingRejection(f"Required field '{field}' missing from agent output")

        value = data[field]

        # Check for None
        if value is None:
            raise ParsingRejection(f"Required field '{field}' is None")

        # Check for empty strings
        if isinstance(value, str) and not value.strip():
            raise ParsingRejection(f"Required field '{field}' is empty string")


# ==============================================================================
# QUALITY DETERMINATION (DETERMINISTIC)
# ==============================================================================

def determine_quality_from_phase(phase: str) -> EvidenceQuality:
    """
    Determine evidence quality from clinical trial phase

    Rules:
    - Phase 3, Phase 4, "Completed" → HIGH
    - Phase 2 → MEDIUM
    - Phase 1, Early Phase 1 → LOW
    - Unknown → MEDIUM (conservative default)

    Args:
        phase: Trial phase string (e.g., "Phase 3", "PHASE_2")

    Returns:
        EvidenceQuality enum value
    """
    if not phase:
        return EvidenceQuality.MEDIUM

    phase_lower = phase.lower()

    if any(p in phase_lower for p in ['phase 3', 'phase 4', 'phase3', 'phase4']):
        return EvidenceQuality.HIGH
    elif any(p in phase_lower for p in ['phase 2', 'phase2']):
        return EvidenceQuality.MEDIUM
    elif any(p in phase_lower for p in ['phase 1', 'phase1', 'early']):
        return EvidenceQuality.LOW
    else:
        # Default to MEDIUM for unknown phases
        return EvidenceQuality.MEDIUM


def determine_quality_from_patent_status(status: str) -> EvidenceQuality:
    """
    Determine evidence quality from patent status

    Rules:
    - Granted, Issued → MEDIUM (patents are speculative IP)
    - Pending, Filed → LOW
    - Unknown → LOW

    Args:
        status: Patent status string

    Returns:
        EvidenceQuality enum value
    """
    if not status:
        return EvidenceQuality.LOW

    status_lower = status.lower()

    if any(s in status_lower for s in ['granted', 'issued', 'active']):
        return EvidenceQuality.MEDIUM
    else:
        # Pending, filed, or unknown → LOW
        return EvidenceQuality.LOW


def determine_quality_from_publication_type(pub_type: str) -> EvidenceQuality:
    """
    Determine evidence quality from publication type

    Rules:
    - Meta-analysis, Systematic review → HIGH
    - RCT, Clinical trial → MEDIUM
    - Case study, Review → LOW
    - Unknown → MEDIUM

    Args:
        pub_type: Publication type string

    Returns:
        EvidenceQuality enum value
    """
    if not pub_type:
        return EvidenceQuality.MEDIUM

    pub_lower = pub_type.lower()

    if any(t in pub_lower for t in ['meta-analysis', 'systematic review']):
        return EvidenceQuality.HIGH
    elif any(t in pub_lower for t in ['rct', 'randomized', 'clinical trial']):
        return EvidenceQuality.MEDIUM
    else:
        # Case studies, reviews, other → LOW
        return EvidenceQuality.LOW


# ==============================================================================
# TIMESTAMP UTILITIES
# ==============================================================================

def get_utc_timestamp() -> datetime:
    """Get current UTC timestamp"""
    return datetime.utcnow()
