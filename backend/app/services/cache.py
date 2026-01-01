"""
Simple in-memory cache for query embeddings.
"""

import time
import logging
import hashlib
import json
from typing import Any
from functools import lru_cache

import redis.asyncio as redis
from app.config import get_settings
from app.services.normalizer import normalize_question


logger = logging.getLogger(__name__)


class TTLCache:
    """Simple TTL cache for embeddings."""
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds
        self._max_size = max_size
    
    def get(self, key: str) -> Any | None:
        """Get value if exists and not expired."""
        if key not in self._cache:
            return None
        
        value, timestamp = self._cache[key]
        if time.time() - timestamp > self._ttl:
            # Expired
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set value with current timestamp."""
        # Evict if at max size
        if len(self._cache) >= self._max_size:
            self._evict_oldest()
        
        self._cache[key] = (value, time.time())
    
    def _evict_oldest(self) -> None:
        """Remove oldest entries."""
        if not self._cache:
            return
        
        # Sort by timestamp and remove oldest 10%
        sorted_keys = sorted(
            self._cache.keys(),
            key=lambda k: self._cache[k][1]
        )
        
        to_remove = max(1, len(sorted_keys) // 10)
        for key in sorted_keys[:to_remove]:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
    
    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "ttl_seconds": self._ttl,
        }


# Global embedding cache instance (5 minute TTL)
_embedding_cache = TTLCache(ttl_seconds=300, max_size=1000)


def get_cached_embedding(query: str) -> list[float] | None:
    """Get cached embedding for a query."""
    return _embedding_cache.get(query)


def cache_embedding(query: str, embedding: list[float]) -> None:
    """Cache an embedding for a query."""
    _embedding_cache.set(query, embedding)


def get_or_create_embedding(query: str) -> list[float]:
    """
    Get embedding from cache or create new one.
    
    Args:
        query: The text to embed
        
    Returns:
        The embedding vector
    """
    from app.services.embeddings import create_embedding
    
    # Check cache first
    cached = get_cached_embedding(query)
    if cached is not None:
        logger.debug(f"Cache hit for query embedding")
        return cached
    
    # Create new embedding
    logger.debug(f"Cache miss, creating embedding for query")
    embedding = create_embedding(query)
    
    # Cache it
    cache_embedding(query, embedding)
    
    return embedding


def clear_embedding_cache() -> None:
    """Clear the embedding cache."""
    _embedding_cache.clear()


def get_cache_stats() -> dict:
    """Get embedding cache statistics."""
    return _embedding_cache.stats()


# ============================================================================
# Redis Answer Cache
# ============================================================================

def generate_cache_key(game_id: int, edition: str | None, expansion_ids: list[int], question: str) -> str:
    """Generate a consistent cache key using normalized question."""
    # Sort expansion IDs
    exp_hash = hashlib.md5(json.dumps(sorted(expansion_ids or [])).encode()).hexdigest()[:8]
    
    # Normalize question
    norm_q = normalize_question(question)
    q_hash = hashlib.md5(norm_q.encode()).hexdigest()[:12]
    
    edition_str = edition or "base"
    
    return f"answer:{game_id}:{edition_str}:{exp_hash}:{q_hash}"


async def get_cached_answer(key: str) -> dict[str, Any] | None:
    """Get answer from Redis cache."""
    settings = get_settings()
    try:
        # Note: In production, use a shared connection pool
        client = redis.from_url(settings.redis_url, decode_responses=True)
        async with client:
            data = await client.get(key)
            if data:
                return json.loads(data)
    except Exception as e:
        logger.warning(f"Redis cache get failed: {e}")
    return None


async def cache_answer(key: str, answer: dict[str, Any], ttl: int = 86400) -> None:
    """Cache answer in Redis."""
    settings = get_settings()
    try:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        async with client:
            await client.set(key, json.dumps(answer), ex=ttl)
    except Exception as e:
        logger.warning(f"Redis cache set failed: {e}")

