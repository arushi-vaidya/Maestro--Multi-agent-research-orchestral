"""Cache management for MAESTRO."""
import redis
import json
from typing import Any, Optional
import hashlib

class CacheManager:
    """Manages caching for agent responses."""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
    
    def _generate_key(self, agent_name: str, query: str) -> str:
        """Generate cache key from agent and query."""
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        return f"maestro:{agent_name}:{query_hash}"
    
    def get(self, agent_name: str, query: str) -> Optional[dict]:
        """Get cached response."""
        key = self._generate_key(agent_name, query)
        cached = self.redis_client.get(key)
        return json.loads(cached) if cached else None
    
    def set(self, agent_name: str, query: str, response: dict, ttl: int = 3600):
        """Cache response with TTL."""
        key = self._generate_key(agent_name, query)
        self.redis_client.setex(
            key,
            ttl,
            json.dumps(response)
        )
    
    def invalidate(self, agent_name: str, query: str):
        """Invalidate cached response."""
        key = self._generate_key(agent_name, query)
        self.redis_client.delete(key)
