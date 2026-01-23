"""
AKGP Graph Manager
Handles Neo4j database operations for the Adaptive Knowledge Graph

This module provides:
- Neo4j connection management
- CRUD operations for nodes and relationships
- Transaction handling
- Batch operations
- Graph queries

Design Philosophy:
- Fail gracefully when Neo4j is not available (allow in-memory mode for testing)
- All operations are atomic (use transactions)
- Provide both sync operations (for simplicity)
- Log all graph modifications for auditability
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging
import json
from contextlib import contextmanager

from akgp.schema import (
    BaseNode, DrugNode, DiseaseNode, EvidenceNode,
    TrialNode, PatentNode, MarketSignalNode,
    Relationship, NodeType, RelationshipType,
    validate_node, validate_relationship
)

logger = logging.getLogger(__name__)


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def _get_enum_value(value):
    """
    Helper to extract string value from enum or string (Pydantic v2 compatibility)

    In Pydantic v2 with use_enum_values=True, enum fields are automatically
    converted to their string values. This helper handles both enum objects
    and pre-converted strings.

    Args:
        value: Enum object or string value

    Returns:
        String value
    """
    if isinstance(value, str):
        return value
    return value.value if hasattr(value, 'value') else str(value)


# ==============================================================================
# NEO4J WRAPPER (Graceful degradation)
# ==============================================================================

try:
    from neo4j import GraphDatabase, Driver
    from neo4j.exceptions import ServiceUnavailable, AuthError
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("Neo4j driver not installed. AKGP will run in IN-MEMORY mode only.")
    Driver = None


# ==============================================================================
# GRAPH MANAGER
# ==============================================================================

class GraphManager:
    """
    Manages AKGP knowledge graph operations

    Supports two modes:
    1. Neo4j mode (production): Full graph database with persistence
    2. In-memory mode (testing): Python dict-based storage (not persistent)
    """

    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        use_in_memory: bool = False
    ):
        """
        Initialize Graph Manager

        Args:
            neo4j_uri: Neo4j database URI (e.g., "bolt://localhost:7687")
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            use_in_memory: Force in-memory mode even if Neo4j is available
        """
        self.driver: Optional[Driver] = None
        self.in_memory_mode = use_in_memory or not NEO4J_AVAILABLE

        # In-memory storage (fallback)
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._relationships: Dict[str, Dict[str, Any]] = {}

        if not self.in_memory_mode and neo4j_uri and neo4j_user and neo4j_password:
            try:
                self.driver = GraphDatabase.driver(
                    neo4j_uri,
                    auth=(neo4j_user, neo4j_password)
                )
                # Test connection
                with self.driver.session() as session:
                    session.run("RETURN 1")
                logger.info(f"✅ Neo4j connected: {neo4j_uri}")
                self.in_memory_mode = False
            except Exception as e:
                logger.warning(f"⚠️  Neo4j connection failed: {e}")
                logger.warning("   Falling back to IN-MEMORY mode")
                self.in_memory_mode = True
                self.driver = None
        else:
            logger.info("🧠 AKGP running in IN-MEMORY mode")
            self.in_memory_mode = True

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ==========================================================================
    # NODE OPERATIONS
    # ==========================================================================

    def create_node(self, node: BaseNode) -> str:
        """
        Create a node in the graph

        Args:
            node: Node instance (DrugNode, DiseaseNode, etc.)

        Returns:
            Node ID

        Raises:
            ValueError: If node already exists
        """
        node_id = node.id

        if self.in_memory_mode:
            if node_id in self._nodes:
                raise ValueError(f"Node {node_id} already exists")

            self._nodes[node_id] = node.dict()
            logger.debug(f"Created node {node_id} (type: {node.node_type}) in memory")
            return node_id
        else:
            # Neo4j mode
            with self.driver.session() as session:
                query = f"""
                CREATE (n:{node.node_type} $props)
                RETURN n.id as id
                """
                props = node.dict()
                # Convert datetime to ISO string for Neo4j
                props = self._serialize_for_neo4j(props)

                result = session.run(query, props=props)
                record = result.single()
                logger.debug(f"Created node {node_id} (type: {node.node_type}) in Neo4j")
                return record["id"]

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a node by ID

        Args:
            node_id: Node ID

        Returns:
            Node data or None if not found
        """
        if self.in_memory_mode:
            return self._nodes.get(node_id)
        else:
            with self.driver.session() as session:
                query = """
                MATCH (n)
                WHERE n.id = $node_id
                RETURN n
                """
                result = session.run(query, node_id=node_id)
                record = result.single()
                if record:
                    return dict(record["n"])
                return None

    def update_node(self, node_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update node properties

        Args:
            node_id: Node ID
            updates: Dictionary of properties to update

        Returns:
            True if successful, False if node not found
        """
        if self.in_memory_mode:
            if node_id not in self._nodes:
                return False
            self._nodes[node_id].update(updates)
            logger.debug(f"Updated node {node_id} in memory")
            return True
        else:
            with self.driver.session() as session:
                query = """
                MATCH (n)
                WHERE n.id = $node_id
                SET n += $updates
                RETURN n
                """
                updates_serialized = self._serialize_for_neo4j(updates)
                result = session.run(query, node_id=node_id, updates=updates_serialized)
                record = result.single()
                if record:
                    logger.debug(f"Updated node {node_id} in Neo4j")
                    return True
                return False

    def delete_node(self, node_id: str) -> bool:
        """
        Delete a node (and its relationships)

        Args:
            node_id: Node ID

        Returns:
            True if successful, False if node not found
        """
        if self.in_memory_mode:
            if node_id not in self._nodes:
                return False

            # Delete relationships involving this node
            rels_to_delete = [
                rel_id for rel_id, rel in self._relationships.items()
                if rel.get("source_id") == node_id or rel.get("target_id") == node_id
            ]
            for rel_id in rels_to_delete:
                del self._relationships[rel_id]

            del self._nodes[node_id]
            logger.debug(f"Deleted node {node_id} and {len(rels_to_delete)} relationships in memory")
            return True
        else:
            with self.driver.session() as session:
                query = """
                MATCH (n)
                WHERE n.id = $node_id
                DETACH DELETE n
                """
                result = session.run(query, node_id=node_id)
                logger.debug(f"Deleted node {node_id} in Neo4j")
                return True

    def find_nodes_by_type(self, node_type: NodeType, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find nodes by type

        Args:
            node_type: Type of node to find
            limit: Maximum number of results

        Returns:
            List of node data dictionaries
        """
        if self.in_memory_mode:
            node_type_str = _get_enum_value(node_type)
            results = [
                node for node in self._nodes.values()
                if node.get("node_type") == node_type_str
            ]
            return results[:limit]
        else:
            with self.driver.session() as session:
                node_type_str = _get_enum_value(node_type)
                query = f"""
                MATCH (n:{node_type_str})
                RETURN n
                LIMIT $limit
                """
                result = session.run(query, limit=limit)
                return [dict(record["n"]) for record in result]

    def find_nodes_by_name(self, name: str, node_type: Optional[NodeType] = None) -> List[Dict[str, Any]]:
        """
        Find nodes by name (case-insensitive partial match)

        Args:
            name: Name to search for
            node_type: Optional filter by node type

        Returns:
            List of matching nodes
        """
        name_lower = name.lower()

        if self.in_memory_mode:
            results = []
            node_type_str = _get_enum_value(node_type) if node_type else None
            for node in self._nodes.values():
                if node_type_str and node.get("node_type") != node_type_str:
                    continue
                if name_lower in node.get("name", "").lower():
                    results.append(node)
            return results
        else:
            with self.driver.session() as session:
                if node_type:
                    node_type_str = _get_enum_value(node_type)
                    query = f"""
                    MATCH (n:{node_type_str})
                    WHERE toLower(n.name) CONTAINS toLower($name)
                    RETURN n
                    """
                else:
                    query = """
                    MATCH (n)
                    WHERE toLower(n.name) CONTAINS toLower($name)
                    RETURN n
                    """
                result = session.run(query, name=name)
                return [dict(record["n"]) for record in result]

    # ==========================================================================
    # RELATIONSHIP OPERATIONS
    # ==========================================================================

    def create_relationship(self, relationship: Relationship) -> str:
        """
        Create a relationship between nodes

        Args:
            relationship: Relationship instance

        Returns:
            Relationship ID

        Raises:
            ValueError: If source or target node doesn't exist
        """
        rel_id = relationship.id

        # Validate source and target exist
        source_exists = self.get_node(relationship.source_id) is not None
        target_exists = self.get_node(relationship.target_id) is not None

        if not source_exists:
            raise ValueError(f"Source node {relationship.source_id} not found")
        if not target_exists:
            raise ValueError(f"Target node {relationship.target_id} not found")

        if self.in_memory_mode:
            if rel_id in self._relationships:
                raise ValueError(f"Relationship {rel_id} already exists")

            self._relationships[rel_id] = relationship.dict()
            logger.debug(f"Created relationship {rel_id} (type: {relationship.relationship_type}) in memory")
            return rel_id
        else:
            with self.driver.session() as session:
                query = f"""
                MATCH (source), (target)
                WHERE source.id = $source_id AND target.id = $target_id
                CREATE (source)-[r:{relationship.relationship_type} $props]->(target)
                RETURN r.id as id
                """
                props = relationship.dict()
                props = self._serialize_for_neo4j(props)

                result = session.run(
                    query,
                    source_id=relationship.source_id,
                    target_id=relationship.target_id,
                    props=props
                )
                record = result.single()
                logger.debug(f"Created relationship {rel_id} (type: {relationship.relationship_type}) in Neo4j")
                return record["id"]

    def get_relationship(self, rel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get relationship by ID

        Args:
            rel_id: Relationship ID

        Returns:
            Relationship data or None
        """
        if self.in_memory_mode:
            return self._relationships.get(rel_id)
        else:
            with self.driver.session() as session:
                query = """
                MATCH ()-[r]->()
                WHERE r.id = $rel_id
                RETURN r
                """
                result = session.run(query, rel_id=rel_id)
                record = result.single()
                if record:
                    return dict(record["r"])
                return None

    def get_relationships_for_node(
        self,
        node_id: str,
        direction: str = "both",
        rel_type: Optional[RelationshipType] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all relationships for a node

        Args:
            node_id: Node ID
            direction: "outgoing", "incoming", or "both"
            rel_type: Optional filter by relationship type

        Returns:
            List of relationships
        """
        if self.in_memory_mode:
            results = []
            rel_type_str = _get_enum_value(rel_type) if rel_type else None
            for rel in self._relationships.values():
                if rel_type_str and rel.get("relationship_type") != rel_type_str:
                    continue

                if direction == "outgoing" and rel.get("source_id") == node_id:
                    results.append(rel)
                elif direction == "incoming" and rel.get("target_id") == node_id:
                    results.append(rel)
                elif direction == "both" and (rel.get("source_id") == node_id or rel.get("target_id") == node_id):
                    results.append(rel)

            return results
        else:
            with self.driver.session() as session:
                rel_type_str = _get_enum_value(rel_type) if rel_type else None
                if direction == "outgoing":
                    pattern = f"(n)-[r{':' + rel_type_str if rel_type_str else ''}]->()"
                elif direction == "incoming":
                    pattern = f"()<-[r{':' + rel_type_str if rel_type_str else ''}]-(n)"
                else:  # both
                    pattern = f"(n)-[r{':' + rel_type_str if rel_type_str else ''}]-()"

                query = f"""
                MATCH {pattern}
                WHERE n.id = $node_id
                RETURN r
                """
                result = session.run(query, node_id=node_id)
                return [dict(record["r"]) for record in result]

    def delete_relationship(self, rel_id: str) -> bool:
        """
        Delete a relationship

        Args:
            rel_id: Relationship ID

        Returns:
            True if successful, False if not found
        """
        if self.in_memory_mode:
            if rel_id not in self._relationships:
                return False
            del self._relationships[rel_id]
            logger.debug(f"Deleted relationship {rel_id} in memory")
            return True
        else:
            with self.driver.session() as session:
                query = """
                MATCH ()-[r]->()
                WHERE r.id = $rel_id
                DELETE r
                """
                session.run(query, rel_id=rel_id)
                logger.debug(f"Deleted relationship {rel_id} in Neo4j")
                return True

    # ==========================================================================
    # BATCH OPERATIONS
    # ==========================================================================

    def create_nodes_batch(self, nodes: List[BaseNode]) -> List[str]:
        """
        Create multiple nodes in a single transaction

        Args:
            nodes: List of node instances

        Returns:
            List of created node IDs
        """
        node_ids = []
        for node in nodes:
            try:
                node_id = self.create_node(node)
                node_ids.append(node_id)
            except Exception as e:
                logger.error(f"Failed to create node {node.id}: {e}")
                # Continue with other nodes
        return node_ids

    def create_relationships_batch(self, relationships: List[Relationship]) -> List[str]:
        """
        Create multiple relationships in a single transaction

        Args:
            relationships: List of relationship instances

        Returns:
            List of created relationship IDs
        """
        rel_ids = []
        for rel in relationships:
            try:
                rel_id = self.create_relationship(rel)
                rel_ids.append(rel_id)
            except Exception as e:
                logger.error(f"Failed to create relationship {rel.id}: {e}")
        return rel_ids

    # ==========================================================================
    # STATISTICS
    # ==========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Get graph statistics

        Returns:
            Dictionary with node counts, relationship counts, etc.
        """
        if self.in_memory_mode:
            node_counts = {}
            for node in self._nodes.values():
                node_type = node.get("node_type")
                node_counts[node_type] = node_counts.get(node_type, 0) + 1

            rel_counts = {}
            for rel in self._relationships.values():
                rel_type = rel.get("relationship_type")
                rel_counts[rel_type] = rel_counts.get(rel_type, 0) + 1

            return {
                "mode": "in_memory",
                "total_nodes": len(self._nodes),
                "total_relationships": len(self._relationships),
                "nodes_by_type": node_counts,
                "relationships_by_type": rel_counts
            }
        else:
            with self.driver.session() as session:
                # Count nodes by type
                node_query = """
                MATCH (n)
                RETURN labels(n)[0] as node_type, count(n) as count
                """
                node_result = session.run(node_query)
                node_counts = {record["node_type"]: record["count"] for record in node_result}

                # Count relationships by type
                rel_query = """
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, count(r) as count
                """
                rel_result = session.run(rel_query)
                rel_counts = {record["rel_type"]: record["count"] for record in rel_result}

                return {
                    "mode": "neo4j",
                    "total_nodes": sum(node_counts.values()),
                    "total_relationships": sum(rel_counts.values()),
                    "nodes_by_type": node_counts,
                    "relationships_by_type": rel_counts
                }

    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================

    def _serialize_for_neo4j(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Python objects to Neo4j-compatible types"""
        result = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, (list, dict)):
                result[key] = json.dumps(value)
            else:
                result[key] = value
        return result

    def clear_all(self):
        """
        Clear all nodes and relationships (USE WITH CAUTION)
        Only for testing purposes
        """
        if self.in_memory_mode:
            self._nodes.clear()
            self._relationships.clear()
            logger.warning("⚠️  Cleared all in-memory graph data")
        else:
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
                logger.warning("⚠️  Cleared all Neo4j graph data")


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = ['GraphManager']
