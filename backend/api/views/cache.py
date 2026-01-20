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

from typing import Dict, Any, Optional, OrderedDict as OrderedDictType
from datetime import datetime
import threading
import logging
from collections import OrderedDict

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
        # Store multiple queries keyed by query_id
        # OrderedDict keeps insertion order so we can evict oldest entries
        self._queries: OrderedDictType[str, Dict[str, Any]] = OrderedDict()
        self._latest_query_id: Optional[str] = None
        self._cache_timestamp: Optional[datetime] = None

        # Limit how many queries we retain to avoid unbounded growth
        self._max_entries: int = 20

        logger.info("QueryResultCache initialized")

    def store_query_result(
        self,
        query_id: str,
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
            # Remove existing entry if same id to refresh ordering
            if query_id in self._queries:
                self._queries.pop(query_id, None)

            self._queries[query_id] = {
                "query": query,
                "response": response,
                "ros_result": ros_result,
                "akgp_result": akgp_result,
                "execution_metadata": execution_metadata,
                "drug_id": drug_id,
                "disease_id": disease_id,
                "timestamp": datetime.utcnow(),
            }

            # Evict oldest if exceeding max entries
            while len(self._queries) > self._max_entries:
                evicted_id, _ = self._queries.popitem(last=False)
                logger.info(f"Cache evicted query_id={evicted_id} due to max_entries={self._max_entries}")

            # Track latest for convenience
            self._latest_query_id = query_id
            self._cache_timestamp = datetime.utcnow()

            logger.info(
                f"✅ Cache updated: query_id={query_id}, query='{query[:50]}...', timestamp={self._cache_timestamp.isoformat()}"
            )

    def get_last_query(self) -> Optional[str]:
        """Get last query string"""
        if not self._latest_query_id:
            return None
        return self._queries.get(self._latest_query_id, {}).get("query")

    def get_latest_query_id(self) -> Optional[str]:
        """Get the most recent query id"""
        return self._latest_query_id

    def _get_entry(self, query_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Return cached entry for query_id or latest if not provided"""
        if query_id is None:
            if not self._latest_query_id:
                return None
            query_id = self._latest_query_id
        return self._queries.get(query_id)

    def get_last_response(self) -> Optional[Dict[str, Any]]:
        """Get last full QueryResponse"""
        entry = self._get_entry(None)
        return entry.get("response") if entry else None

    def get_last_response_by_id(self, query_id: Optional[str]) -> Optional[Dict[str, Any]]:
        entry = self._get_entry(query_id)
        return entry.get("response") if entry else None

    def get_last_ros_result(self, query_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get ROS computation result for specific or latest query"""
        entry = self._get_entry(query_id)
        return entry.get("ros_result") if entry else None

    def get_last_akgp_result(self, query_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get AKGP query result for specific or latest query"""
        entry = self._get_entry(query_id)
        return entry.get("akgp_result") if entry else None

    def get_last_execution_metadata(self, query_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get execution metadata for specific or latest query"""
        entry = self._get_entry(query_id)
        return entry.get("execution_metadata") if entry else None

    def get_last_drug_disease_ids(self, query_id: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
        """Get drug/disease canonical IDs for specific or latest query"""
        entry = self._get_entry(query_id)
        if not entry:
            return None, None
        return entry.get("drug_id"), entry.get("disease_id")

    def get_cache_timestamp(self) -> Optional[datetime]:
        """Get timestamp of last cache update"""
        return self._cache_timestamp

    def is_empty(self) -> bool:
        """Check if cache is empty"""
        return len(self._queries) == 0

    def clear(self):
        """Clear all cached data"""
        with self._lock:
            self._queries.clear()
            self._latest_query_id = None
            self._cache_timestamp = None
            logger.info("Cache cleared")


# Singleton instance
_cache = QueryResultCache()


def get_cache() -> QueryResultCache:
    """Get singleton cache instance"""
    return _cache
