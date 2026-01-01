"""
Integration tests for the caching system.

Tests cover:
- Cache hit behavior
- Cache miss behavior
- Question normalization consistency
- Cache key generation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestCacheKeyGeneration:
    """Tests for cache key generation."""
    
    def test_same_question_generates_same_key(self):
        """Identical questions generate identical cache keys."""
        from app.services.cache import generate_cache_key
        
        key1 = generate_cache_key(
            game_id=1,
            edition="1st",
            expansion_ids=[],
            question="Can I move twice?"
        )
        
        key2 = generate_cache_key(
            game_id=1,
            edition="1st",
            expansion_ids=[],
            question="Can I move twice?"
        )
        
        assert key1 == key2
        
    def test_different_games_generate_different_keys(self):
        """Different game IDs generate different keys."""
        from app.services.cache import generate_cache_key
        
        key1 = generate_cache_key(1, "1st", [], "Can I move twice?")
        key2 = generate_cache_key(2, "1st", [], "Can I move twice?")
        
        assert key1 != key2
        
    def test_different_editions_generate_different_keys(self):
        """Different editions generate different keys."""
        from app.services.cache import generate_cache_key
        
        key1 = generate_cache_key(1, "1st", [], "Can I move twice?")
        key2 = generate_cache_key(1, "2nd", [], "Can I move twice?")
        
        assert key1 != key2
        
    def test_expansion_order_doesnt_matter(self):
        """Expansion IDs are sorted, so order doesn't affect key."""
        from app.services.cache import generate_cache_key
        
        key1 = generate_cache_key(1, "1st", [1, 2, 3], "Test?")
        key2 = generate_cache_key(1, "1st", [3, 1, 2], "Test?")
        
        assert key1 == key2


class TestQuestionNormalization:
    """Tests for question normalization affecting cache keys."""
    
    def test_normalized_questions_same_key(self):
        """Questions that normalize to same form get same key."""
        from app.services.cache import generate_cache_key
        
        # These should normalize to the same question
        key1 = generate_cache_key(1, "1st", [], "Can I move twice?")
        key2 = generate_cache_key(1, "1st", [], "can i move twice")  # lowercase, no punctuation
        key3 = generate_cache_key(1, "1st", [], "CAN I MOVE TWICE?")  # uppercase
        
        # After normalization, these should be the same
        assert key1 == key2
        assert key2 == key3
        
    def test_different_questions_different_keys(self):
        """Semantically different questions get different keys."""
        from app.services.cache import generate_cache_key
        
        key1 = generate_cache_key(1, "1st", [], "Can I move twice?")
        key2 = generate_cache_key(1, "1st", [], "Can I attack twice?")
        
        assert key1 != key2


class TestInMemoryCache:
    """Tests for TTL cache."""
    
    def test_cache_stores_and_retrieves(self):
        """Basic cache store and retrieve."""
        from app.services.cache import TTLCache
        
        cache = TTLCache(ttl_seconds=60)
        cache.set("test_key", [1.0, 2.0, 3.0])
        
        result = cache.get("test_key")
        assert result == [1.0, 2.0, 3.0]
        
    def test_cache_returns_none_for_missing(self):
        """Missing keys return None."""
        from app.services.cache import TTLCache
        
        cache = TTLCache(ttl_seconds=60)
        
        result = cache.get("nonexistent")
        assert result is None
        
    def test_cache_respects_max_size(self):
        """Cache evicts old entries when full."""
        from app.services.cache import TTLCache
        
        cache = TTLCache(ttl_seconds=60, max_size=5)
        
        for i in range(10):
            cache.set(f"key_{i}", i)
        
        # Should have evicted some entries
        stats = cache.stats()
        assert stats["size"] <= 5


class TestRedisCache:
    """Tests for Redis cache operations."""
    
    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_data(self):
        """Cache hit returns stored data."""
        with patch("app.services.cache.redis") as redis_mock:
            from app.services.cache import get_cached_answer
            
            # Setup mock
            client_mock = AsyncMock()
            client_mock.get = AsyncMock(return_value='{"verdict": "Yes", "confidence": "high"}')
            redis_mock.from_url.return_value = client_mock
            client_mock.__aenter__ = AsyncMock(return_value=client_mock)
            client_mock.__aexit__ = AsyncMock()
            
            result = await get_cached_answer("test:key")
            
            assert result is not None
            assert result["verdict"] == "Yes"
            
    @pytest.mark.asyncio
    async def test_cache_miss_returns_none(self):
        """Cache miss returns None."""
        with patch("app.services.cache.redis") as redis_mock:
            from app.services.cache import get_cached_answer
            
            client_mock = AsyncMock()
            client_mock.get = AsyncMock(return_value=None)
            redis_mock.from_url.return_value = client_mock
            client_mock.__aenter__ = AsyncMock(return_value=client_mock)
            client_mock.__aexit__ = AsyncMock()
            
            result = await get_cached_answer("test:key")
            
            assert result is None
            
    @pytest.mark.asyncio
    async def test_cache_error_returns_none(self):
        """Redis errors return None gracefully."""
        with patch("app.services.cache.redis") as redis_mock:
            from app.services.cache import get_cached_answer
            
            redis_mock.from_url.side_effect = Exception("Connection failed")
            
            result = await get_cached_answer("test:key")
            
            assert result is None
