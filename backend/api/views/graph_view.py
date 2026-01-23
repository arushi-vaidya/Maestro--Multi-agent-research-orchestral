"""
Graph View - Knowledge Graph Visualization Façade

Provides frontend-safe access to AKGP knowledge graph for visualization.

CRITICAL CONSTRAINTS:
- READ-ONLY: Does NOT modify graph
- Does NOT trigger ingestion
- Does NOT call agents
- ONLY queries existing graph state

Endpoints:
- GET /api/graph/summary: Get nodes and edges for visualization
"""

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel
from typing import List, Literal, Optional, Dict, Any
import logging

from akgp.schema import NodeType, RelationshipType
from api.views.cache import get_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


# ==============================================================================
# RESPONSE MODELS
# ==============================================================================

class GraphNodeView(BaseModel):
    """
    Frontend-safe node representation for graph visualization

    Simplified node format suitable for D3.js, Three.js, or Neo4j-style visualizations.
    """
    id: str
    label: str
    type: Literal["drug", "disease", "evidence", "trial", "patent", "market_signal"]
    metadata: Optional[Dict[str, Any]] = None  # Additional data for tooltips/details

    class Config:
        json_schema_extra = {
            "example": {
                "id": "drug_12345",
                "label": "Semaglutide",
                "type": "drug",
                "metadata": {
                    "drug_class": "GLP-1 agonist",
                    "synonyms": ["Ozempic", "Wegovy"]
                }
            }
        }


class GraphEdgeView(BaseModel):
    """
    Frontend-safe edge representation for graph visualization

    Simplified relationship format with source, target, and relationship type.
    """
    source: str  # Source node ID
    target: str  # Target node ID
    relationship: str  # TREATS, INVESTIGATED_FOR, SUGGESTS, CONTRADICTS, SUPPORTS
    weight: float  # Confidence/strength (0.0-1.0)
    metadata: Optional[Dict[str, Any]] = None  # Evidence ID, agent, timestamp

    class Config:
        json_schema_extra = {
            "example": {
                "source": "drug_12345",
                "target": "disease_67890",
                "relationship": "INVESTIGATED_FOR",
                "weight": 0.85,
                "metadata": {
                    "evidence_id": "ev_abc123",
                    "agent": "clinical",
                    "confidence": 0.85
                }
            }
        }


class GraphSummaryResponse(BaseModel):
    """
    Complete graph summary for visualization

    Contains nodes and edges ready for frontend graph libraries.
    """
    nodes: List[GraphNodeView]
    edges: List[GraphEdgeView]
    statistics: Dict[str, Any]  # Node counts, edge counts, graph metadata

    class Config:
        json_schema_extra = {
            "example": {
                "nodes": [
                    {"id": "drug_1", "label": "Semaglutide", "type": "drug"},
                    {"id": "disease_1", "label": "Type 2 Diabetes", "type": "disease"}
                ],
                "edges": [
                    {
                        "source": "drug_1",
                        "target": "disease_1",
                        "relationship": "TREATS",
                        "weight": 0.9
                    }
                ],
                "statistics": {
                    "total_nodes": 2,
                    "total_edges": 1,
                    "node_counts": {"drug": 1, "disease": 1}
                }
            }
        }


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def _normalize_node_type(node_type: str) -> str:
    """
    Normalize AKGP node type to frontend format

    AKGP uses: Drug, Disease, Evidence, Trial, Patent, MarketSignal
    Frontend uses: drug, disease, evidence, trial, patent, market_signal
    """
    mapping = {
        "Drug": "drug",
        "Disease": "disease",
        "Evidence": "evidence",
        "Trial": "trial",
        "Patent": "patent",
        "MarketSignal": "market_signal"
    }
    return mapping.get(node_type, node_type.lower())


def _extract_node_label(node: Dict[str, Any]) -> str:
    """Extract display label from node"""
    # Try common label fields
    return node.get('name') or node.get('title') or node.get('id', 'Unknown')


def _build_node_metadata(node: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant metadata for frontend tooltips

    Include useful fields but exclude internal system fields.
    """
    metadata = {}

    # Include common useful fields
    useful_fields = [
        'synonyms', 'drug_class', 'disease_category',
        'nct_id', 'phase', 'status',
        'patent_number', 'filing_date',
        'source', 'agent_name', 'confidence_score', 'quality'
    ]

    for field in useful_fields:
        if field in node and node[field] is not None:
            metadata[field] = node[field]

    return metadata if metadata else None


# ==============================================================================
# ENDPOINTS
# ==============================================================================

@router.get("/summary", response_model=GraphSummaryResponse)
def get_graph_summary(
    response: Response,
    node_limit: int = Query(100, description="Maximum nodes to return", ge=1, le=1000),
    include_evidence: bool = Query(False, description="Include evidence nodes (can be large)")
):
    """
    Get knowledge graph summary for visualization

    This endpoint:
    - Reads current AKGP graph state (READ-ONLY)
    - Returns nodes and edges in visualization-friendly format
    - Does NOT modify graph
    - Does NOT trigger ingestion

    Query Parameters:
        node_limit: Maximum number of nodes to return (default: 100, max: 1000)
        include_evidence: Include evidence nodes (default: False - they can be numerous)

    Returns:
        GraphSummaryResponse with nodes, edges, and statistics

    Raises:
        500: Error reading graph
    """
    try:
        # Prevent caching
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        # Import here to avoid circular dependencies
        from api.routes import get_master_agent

        # Get graph manager from master agent
        master = get_master_agent()
        graph_manager = master.graph_manager

        # Get graph statistics first
        stats = graph_manager.get_stats()
        logger.info(f"📊 Graph stats: {stats}")

        nodes_list = []
        edges_list = []
        
        # Check cache for current query context
        cache = get_cache()
        drug_id, disease_id = cache.get_last_drug_disease_ids()
        
        # Priority Strategy: If we have specific drug/disease from query, focus graph on them
        priority_nodes_found = False
        
        if drug_id and disease_id:
            logger.info(f"🎯 Focusing graph on query entities: {drug_id}, {disease_id}")
            
            # Fetch focal nodes
            focal_ids = [did for did in [drug_id, disease_id] if did]
            focal_nodes = []
            
            for fid in focal_ids:
                node = graph_manager.get_node(fid)
                if node:
                    focal_nodes.append(node)
                    
            if focal_nodes:
                priority_nodes_found = True
                # Fetch 1-hop neighbors for focal nodes
                neighbor_ids = set()
                neighbor_nodes = []
                
                for fnode in focal_nodes:
                    try:
                        rels = graph_manager.get_relationships_for_node(fnode['id'], direction="both")
                        for rel in rels:
                            neighbor_id = rel['target_id'] if rel['source_id'] == fnode['id'] else rel['source_id']
                            if neighbor_id not in neighbor_ids and neighbor_id not in focal_ids:
                                neighbor_ids.add(neighbor_id)
                                n_node = graph_manager.get_node(neighbor_id)
                                if n_node:
                                    neighbor_nodes.append(n_node)
                    except Exception as e:
                        logger.warning(f"Error fetching neighbors for {fnode['id']}: {e}")

                # Combine nodes (focal + neighbors)
                target_nodes = focal_nodes + neighbor_nodes
                logger.info(f"   Found {len(focal_nodes)} focal nodes + {len(neighbor_nodes)} neighbors")
                
                # Add to response list
                for node in target_nodes[:node_limit]:
                    node_view = GraphNodeView(
                        id=node['id'],
                        label=_extract_node_label(node),
                        type=_normalize_node_type(node.get('node_type', '')),
                        metadata=_build_node_metadata(node)
                    )
                    nodes_list.append(node_view)
            else:
                logger.warning(f"⚠️ Query entities {drug_id}, {disease_id} found in cache but MISSING from graph manager. Falling back.")

        # Fallback Strategy: If priority strategy failed or yielded no nodes, fetch global top nodes
        if not priority_nodes_found:
            logger.info("🌍 No specific query context (or entities missing) - fetching global top nodes")
            
            # Determine which node types to fetch
            node_types_to_fetch = [NodeType.DRUG, NodeType.DISEASE]

            if include_evidence:
                node_types_to_fetch.extend([
                    NodeType.EVIDENCE,
                    NodeType.TRIAL,
                    NodeType.PATENT,
                    NodeType.MARKET_SIGNAL
                ])

            # Fetch nodes by type
            for node_type in node_types_to_fetch:
                try:
                    nodes = graph_manager.find_nodes_by_type(node_type, limit=node_limit)
                    logger.info(f"Found {len(nodes)} {node_type.value} nodes")

                    for node in nodes:
                        node_view = GraphNodeView(
                            id=node['id'],
                            label=_extract_node_label(node),
                            type=_normalize_node_type(node.get('node_type', '')),
                            metadata=_build_node_metadata(node)
                        )
                        nodes_list.append(node_view)

                except Exception as e:
                    logger.warning(f"Error fetching {node_type.value} nodes: {e}")
                    continue

        # Fetch relationships for collected nodes
        node_ids = {node.id for node in nodes_list}

        for node_id in list(node_ids)[:node_limit]:  # Limit relationship queries
            try:
                relationships = graph_manager.get_relationships_for_node(
                    node_id,
                    direction="outgoing"
                )

                for rel in relationships:
                    # Only include edge if target is in our node set
                    if rel.get('target_id') in node_ids:
                        edge_view = GraphEdgeView(
                            source=rel['source_id'],
                            target=rel['target_id'],
                            relationship=rel.get('relationship_type', 'UNKNOWN'),
                            weight=rel.get('confidence', 0.5),
                            metadata={
                                'evidence_id': rel.get('evidence_id'),
                                'agent_id': rel.get('agent_id'),
                                'timestamp': rel.get('timestamp')
                            }
                        )
                        edges_list.append(edge_view)

            except Exception as e:
                logger.warning(f"Error fetching relationships for {node_id}: {e}")
                continue

        # Build statistics
        node_counts = {}
        for node in nodes_list:
            node_counts[node.type] = node_counts.get(node.type, 0) + 1

        statistics = {
            "total_nodes": len(nodes_list),
            "total_edges": len(edges_list),
            "node_counts": node_counts,
            "graph_mode": stats.get('mode', 'unknown'),
            "full_graph_stats": stats  # Include full graph stats for reference
        }

        logger.info(f"✅ Graph summary: {len(nodes_list)} nodes, {len(edges_list)} edges")

        return GraphSummaryResponse(
            nodes=nodes_list,
            edges=edges_list,
            statistics=statistics
        )

    except Exception as e:
        logger.error(f"Error retrieving graph summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving graph summary: {str(e)}"
        )
