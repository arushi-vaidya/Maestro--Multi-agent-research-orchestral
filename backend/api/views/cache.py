"""
Query Result Cache

Thread-safe singleton cache for storing last query results.
Used by API façade views to access already-computed data.

CRITICAL: This is a PRESENTATION CACHE ONLY
- Does NOT trigger computation
- Does NOT modify graph
- Does NOT call agents
- ONLY stores results from /api/query endpoint
"""

from typing import Dict, Any, Optional
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)


class QueryResultCache:
    """
    Thread-safe singleton cache for query results

    Stores:
    - Last QueryResponse from /api/query
    - Last ROS computation results
    - Last AKGP query results
    - Last execution metadata
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize cache storage"""
        self._last_query: Optional[str] = None
        self._last_response: Optional[Dict[str, Any]] = None
        self._last_ros_result: Optional[Dict[str, Any]] = None
        self._last_akgp_result: Optional[Dict[str, Any]] = None
        self._last_execution_metadata: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[datetime] = None

        # Store drug/disease IDs for ROS/conflict queries
        self._last_drug_id: Optional[str] = None
        self._last_disease_id: Optional[str] = None

        logger.info("QueryResultCache initialized")

    def store_query_result(
        self,
        query: str,
        response: Dict[str, Any],
        ros_result: Optional[Dict[str, Any]] = None,
        akgp_result: Optional[Dict[str, Any]] = None,
        execution_metadata: Optional[Dict[str, Any]] = None,
        drug_id: Optional[str] = None,
        disease_id: Optional[str] = None
    ):
        """
        Store query results in cache

        Args:
            query: User query string
            response: Full QueryResponse dictionary
            ros_result: ROS computation result (if available)
            akgp_result: AKGP query result (if available)
            execution_metadata: Execution metadata from graph orchestration
            drug_id: Canonical drug ID (if detected)
            disease_id: Canonical disease ID (if detected)
        """
        with self._lock:
            self._last_query = query
            self._last_response = response
            self._last_ros_result = ros_result
            self._last_akgp_result = akgp_result
            self._last_execution_metadata = execution_metadata
            self._last_drug_id = drug_id
            self._last_disease_id = disease_id
            self._cache_timestamp = datetime.utcnow()

            logger.info(f"✅ Cache updated: query='{query[:50]}...', timestamp={self._cache_timestamp.isoformat()}")

    def get_last_query(self) -> Optional[str]:
        """Get last query string"""
        return self._last_query

    def get_last_response(self) -> Optional[Dict[str, Any]]:
        """Get last full QueryResponse"""
        return self._last_response

    def get_last_ros_result(self) -> Optional[Dict[str, Any]]:
        """Get last ROS computation result"""
        return self._last_ros_result

    def get_last_akgp_result(self) -> Optional[Dict[str, Any]]:
        """Get last AKGP query result"""
        return self._last_akgp_result

    def get_last_execution_metadata(self) -> Optional[Dict[str, Any]]:
        """Get last execution metadata"""
        return self._last_execution_metadata

    def get_last_drug_disease_ids(self) -> tuple[Optional[str], Optional[str]]:
        """Get last drug/disease canonical IDs"""
        return self._last_drug_id, self._last_disease_id

    def get_cache_timestamp(self) -> Optional[datetime]:
        """Get timestamp of last cache update"""
        return self._cache_timestamp

    def is_empty(self) -> bool:
        """Check if cache is empty"""
        return self._last_response is None

    def clear(self):
        """Clear all cached data"""
        with self._lock:
            self._last_query = None
            self._last_response = None
            self._last_ros_result = None
            self._last_akgp_result = None
            self._last_execution_metadata = None
            self._last_drug_id = None
            self._last_disease_id = None
            self._cache_timestamp = None
            logger.info("Cache cleared")


# Singleton instance
_cache = QueryResultCache()


def get_cache() -> QueryResultCache:
    """Get singleton cache instance"""
    return _cache
