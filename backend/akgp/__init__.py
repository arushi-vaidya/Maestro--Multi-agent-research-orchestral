"""
AKGP - Adaptive Knowledge Graph Protocol
Multi-Agent Pharmaceutical Knowledge Graph with Provenance and Temporal Reasoning

This module implements the core scientific contribution of PharmaGraph:
an adaptive knowledge graph that:
- Stores drug-disease-evidence relationships
- Tracks provenance from multiple agents
- Supports temporal reasoning
- Detects and records conflicts
- Provides explainable queries

Modules:
- schema: Core data models and validation
- graph_manager: Neo4j graph database operations
- provenance: Provenance tracking and auditability
- temporal: Temporal logic and recency weighting
- conflict_resolution: Deterministic conflict detection
- ingestion: APIs for ingesting agent outputs
- query_engine: High-level query interface

Author: MAESTRO Team
Version: 1.0.0
"""

from akgp.schema import (
    NodeType,
    RelationshipType,
    SourceType,
    EvidenceQuality,
    DrugNode,
    DiseaseNode,
    EvidenceNode,
    TrialNode,
    PatentNode,
    MarketSignalNode,
    Relationship,
    Conflict,
)

__version__ = "1.0.0"
__all__ = [
    'NodeType',
    'RelationshipType',
    'SourceType',
    'EvidenceQuality',
    'DrugNode',
    'DiseaseNode',
    'EvidenceNode',
    'TrialNode',
    'PatentNode',
    'MarketSignalNode',
    'Relationship',
    'Conflict',
]
