"""
AKGP Schema Definition
Adaptive Knowledge Graph Protocol for PharmaGraph

This module defines the core schema for the AKGP knowledge graph:
- Node types (Drug, Disease, Evidence, Trial, Patent, MarketSignal)
- Relationship types (TREATS, INVESTIGATED_FOR, SUGGESTS, CONTRADICTS, SUPPORTS)
- Validation rules
- Type definitions

Design Philosophy:
- Explicit provenance for all evidence
- Temporal validity tracking
- Conflict-aware (record, don't overwrite)
- Deterministic and explainable
"""

from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field, validator
from enum import Enum


# ==============================================================================
# ENUMS - Controlled Vocabularies
# ==============================================================================

class NodeType(str, Enum):
    """Valid node types in AKGP"""
    DRUG = "Drug"
    DISEASE = "Disease"
    EVIDENCE = "Evidence"
    TRIAL = "Trial"
    PATENT = "Patent"
    MARKET_SIGNAL = "MarketSignal"


class RelationshipType(str, Enum):
    """Valid relationship types in AKGP"""
    TREATS = "TREATS"  # Drug -> Disease (established treatment)
    INVESTIGATED_FOR = "INVESTIGATED_FOR"  # Drug -> Disease (under investigation)
    SUGGESTS = "SUGGESTS"  # Evidence -> relationship (supporting signal)
    CONTRADICTS = "CONTRADICTS"  # Evidence -> Evidence (conflicting evidence)
    SUPPORTS = "SUPPORTS"  # Evidence -> Evidence (corroborating evidence)


class SourceType(str, Enum):
    """Source type for evidence"""
    CLINICAL = "clinical"  # Clinical trials
    PATENT = "patent"  # Patent filings
    LITERATURE = "literature"  # Published papers
    MARKET = "market"  # Market intelligence


class EvidenceQuality(str, Enum):
    """Evidence quality tier (for deterministic weighting)"""
    HIGH = "high"  # Phase 3 trials, granted patents, peer-reviewed papers
    MEDIUM = "medium"  # Phase 2 trials, patent applications, market reports
    LOW = "low"  # Phase 1 trials, patent searches, web sources


# ==============================================================================
# BASE NODE MODEL
# ==============================================================================

class BaseNode(BaseModel):
    """Base model for all AKGP nodes"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    node_type: NodeType
    name: str = Field(..., min_length=1)
    source: str = Field(..., description="Origin of this node (agent name or data source)")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Optional metadata (extensible)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


# ==============================================================================
# SPECIFIC NODE TYPES
# ==============================================================================

class DrugNode(BaseNode):
    """Drug/Compound node"""
    node_type: Literal[NodeType.DRUG] = NodeType.DRUG

    # Drug-specific fields
    umls_id: Optional[str] = None  # UMLS concept ID
    drugbank_id: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)
    drug_class: Optional[str] = None  # e.g., "GLP-1 agonist"

    @validator('name')
    def normalize_drug_name(cls, v):
        """Normalize drug names to title case"""
        return v.strip().title()


class DiseaseNode(BaseNode):
    """Disease/Indication node"""
    node_type: Literal[NodeType.DISEASE] = NodeType.DISEASE

    # Disease-specific fields
    umls_id: Optional[str] = None  # UMLS concept ID
    icd10_code: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)
    disease_category: Optional[str] = None  # e.g., "Metabolic", "Oncology"

    @validator('name')
    def normalize_disease_name(cls, v):
        """Normalize disease names to title case"""
        return v.strip().title()


class EvidenceNode(BaseNode):
    """Evidence node - represents a piece of evidence from an agent"""
    node_type: Literal[NodeType.EVIDENCE] = NodeType.EVIDENCE

    # Evidence-specific fields (PROVENANCE)
    agent_name: str = Field(..., description="Name of agent that generated this evidence")
    agent_id: str = Field(..., description="ID of agent (clinical/patent/market)")
    api_source: Optional[str] = None  # e.g., "ClinicalTrials.gov", "USPTO PatentsView"
    raw_reference: str = Field(..., description="Raw reference (NCT ID, patent number, URL)")
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Evidence quality and type
    source_type: SourceType
    quality: EvidenceQuality = EvidenceQuality.MEDIUM
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)

    # Content
    summary: str = Field(..., min_length=1)
    full_text: Optional[str] = None

    # Temporal validity
    validity_start: datetime = Field(default_factory=datetime.utcnow)
    validity_end: Optional[datetime] = None  # None = still valid

    @validator('confidence_score')
    def validate_confidence(cls, v):
        """Ensure confidence is in valid range"""
        return max(0.0, min(1.0, v))


class TrialNode(BaseNode):
    """Clinical Trial node"""
    node_type: Literal[NodeType.TRIAL] = NodeType.TRIAL

    # Trial-specific fields
    nct_id: str = Field(..., description="ClinicalTrials.gov NCT ID")
    phase: Optional[str] = None  # "Phase 1", "Phase 2", "Phase 3", "Phase 4"
    status: Optional[str] = None  # "Recruiting", "Completed", "Terminated"
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    sponsor: Optional[str] = None

    # Link to interventions and conditions
    interventions: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)


class PatentNode(BaseNode):
    """Patent node"""
    node_type: Literal[NodeType.PATENT] = NodeType.PATENT

    # Patent-specific fields
    patent_number: str = Field(..., description="USPTO patent number")
    filing_date: Optional[datetime] = None
    grant_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    assignees: List[str] = Field(default_factory=list)
    patent_title: str = ""
    abstract: Optional[str] = None
    claims_count: Optional[int] = None


class MarketSignalNode(BaseNode):
    """Market intelligence signal node"""
    node_type: Literal[NodeType.MARKET_SIGNAL] = NodeType.MARKET_SIGNAL

    # Market-specific fields
    signal_type: str = Field(..., description="Type of market signal (forecast, sales, etc.)")
    market_size: Optional[float] = None  # in USD
    growth_rate: Optional[float] = None  # CAGR
    forecast_year: Optional[int] = None
    geographic_region: Optional[str] = None
    data_provider: Optional[str] = None  # "IQVIA", "EvaluatePharma", etc.


# ==============================================================================
# RELATIONSHIP MODEL
# ==============================================================================

class Relationship(BaseModel):
    """Relationship between nodes in AKGP"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    relationship_type: RelationshipType

    # Source and target nodes
    source_id: str = Field(..., description="ID of source node")
    target_id: str = Field(..., description="ID of target node")

    # Provenance (which evidence supports this relationship)
    evidence_id: str = Field(..., description="ID of evidence node that created this relationship")
    agent_id: str = Field(..., description="Agent that inferred this relationship")

    # Confidence and type
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_type: SourceType

    # Temporal validity
    validity_start: datetime = Field(default_factory=datetime.utcnow)
    validity_end: Optional[datetime] = None

    # Optional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True

    @validator('confidence')
    def validate_confidence(cls, v):
        """Ensure confidence is in valid range"""
        return max(0.0, min(1.0, v))


# ==============================================================================
# CONFLICT MODEL
# ==============================================================================

class Conflict(BaseModel):
    """Represents a detected conflict between evidence or relationships"""
    id: str = Field(default_factory=lambda: str(uuid4()))

    # Conflicting entities
    entity1_id: str = Field(..., description="ID of first conflicting entity")
    entity2_id: str = Field(..., description="ID of second conflicting entity")
    entity_type: Literal["evidence", "relationship"] = "evidence"

    # Conflict details
    conflict_type: str = Field(..., description="Type of conflict (e.g., 'efficacy_contradiction')")
    severity: Literal["low", "medium", "high"] = "medium"
    detected_at: datetime = Field(default_factory=datetime.utcnow)

    # Resolution status
    resolved: bool = False
    resolution_note: Optional[str] = None
    resolved_at: Optional[datetime] = None

    # Explanation
    explanation: str = Field(..., description="Human-readable explanation of the conflict")


# ==============================================================================
# VALIDATION UTILITIES
# ==============================================================================

def validate_node(node_data: Dict[str, Any]) -> BaseNode:
    """
    Validate and construct appropriate node type from raw data

    Args:
        node_data: Dictionary containing node data

    Returns:
        Validated node instance

    Raises:
        ValueError: If node_type is invalid or data doesn't validate
    """
    node_type = node_data.get('node_type')

    if node_type == NodeType.DRUG:
        return DrugNode(**node_data)
    elif node_type == NodeType.DISEASE:
        return DiseaseNode(**node_data)
    elif node_type == NodeType.EVIDENCE:
        return EvidenceNode(**node_data)
    elif node_type == NodeType.TRIAL:
        return TrialNode(**node_data)
    elif node_type == NodeType.PATENT:
        return PatentNode(**node_data)
    elif node_type == NodeType.MARKET_SIGNAL:
        return MarketSignalNode(**node_data)
    else:
        raise ValueError(f"Invalid node_type: {node_type}")


def validate_relationship(rel_data: Dict[str, Any]) -> Relationship:
    """
    Validate and construct relationship from raw data

    Args:
        rel_data: Dictionary containing relationship data

    Returns:
        Validated relationship instance

    Raises:
        ValueError: If data doesn't validate
    """
    return Relationship(**rel_data)


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    'NodeType',
    'RelationshipType',
    'SourceType',
    'EvidenceQuality',
    'BaseNode',
    'DrugNode',
    'DiseaseNode',
    'EvidenceNode',
    'TrialNode',
    'PatentNode',
    'MarketSignalNode',
    'Relationship',
    'Conflict',
    'validate_node',
    'validate_relationship',
]
