"""
Rate limiting utilities using Redis with sliding window algorithm.
"""

import logging
import time
from typing import NamedTuple

from app.jobs.queue import get_redis_connection


logger = logging.getLogger(__name__)


class RateLimitResult(NamedTuple):
    """Result of a rate limit check."""
    allowed: bool
    remaining: int
    reset_at: int  # Unix timestamp
    limit: int
    window_seconds: int


def rate_limit(
    key: str,
    max_requests: int,
    window_seconds: int,
) -> RateLimitResult:
    """
    Check and apply rate limit using sliding window algorithm.
    
    Uses a Redis sorted set to track request timestamps, allowing
    for a true sliding window implementation.
    
    Args:
        key: Unique rate limit key (e.g., "ask:ip:192.168.1.1")
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
        
    Returns:
        RateLimitResult with allowed status and metadata
    """
    try:
        redis = get_redis_connection()
    except Exception as e:
        logger.error(f"Redis connection failed for rate limiting: {e}")
        # If Redis is down, allow the request (fail open)
        return RateLimitResult(
            allowed=True,
            remaining=max_requests,
            reset_at=int(time.time()) + window_seconds,
            limit=max_requests,
            window_seconds=window_seconds,
        )
    
    now = time.time()
    window_start = now - window_seconds
    
    # Redis key for the sorted set
    redis_key = f"ratelimit:{key}"
    
    try:
        # Use pipeline for atomic operations
        pipe = redis.pipeline()
        
        # Remove old entries outside the window
        pipe.zremrangebyscore(redis_key, 0, window_start)
        
        # Count requests in current window
        pipe.zcard(redis_key)
        
        # Execute pipeline
        results = pipe.execute()
        current_count = results[1]
        
        if current_count >= max_requests:
            # Rate limit exceeded
            # Get the oldest entry to calculate when window resets
            oldest = redis.zrange(redis_key, 0, 0, withscores=True)
            if oldest:
                reset_at = int(oldest[0][1]) + window_seconds
            else:
                reset_at = int(now) + window_seconds
            
            logger.warning(
                f"Rate limit exceeded: key={key}, "
                f"current={current_count}, max={max_requests}"
            )
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=reset_at,
                limit=max_requests,
                window_seconds=window_seconds,
            )
        
        # Add current request
        pipe = redis.pipeline()
        pipe.zadd(redis_key, {str(now): now})
        pipe.expire(redis_key, window_seconds + 1)
        pipe.execute()
        
        remaining = max_requests - current_count - 1
        reset_at = int(now) + window_seconds
        
        return RateLimitResult(
            allowed=True,
            remaining=max(0, remaining),
            reset_at=reset_at,
            limit=max_requests,
            window_seconds=window_seconds,
        )
        
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        # Fail open on error
        return RateLimitResult(
            allowed=True,
            remaining=max_requests,
            reset_at=int(time.time()) + window_seconds,
            limit=max_requests,
            window_seconds=window_seconds,
        )


def check_concurrent_limit(
    key: str,
    max_concurrent: int,
    ttl_seconds: int = 600,
) -> tuple[bool, int]:
    """
    Check concurrent operation limit using Redis counter.
    
    Args:
        key: Unique key for the limit (e.g., "concurrent:ingest")
        max_concurrent: Maximum concurrent operations
        ttl_seconds: TTL for stuck counters (safety net)
        
    Returns:
        Tuple of (allowed, current_count)
    """
    try:
        redis = get_redis_connection()
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return (True, 0)
    
    redis_key = f"concurrent:{key}"
    
    try:
        current = redis.get(redis_key)
        current_count = int(current) if current else 0
        
        if current_count >= max_concurrent:
            logger.warning(f"Concurrent limit exceeded: key={key}, current={current_count}")
            return (False, current_count)
        
        # Increment with TTL
        pipe = redis.pipeline()
        pipe.incr(redis_key)
        pipe.expire(redis_key, ttl_seconds)
        pipe.execute()
        
        return (True, current_count + 1)
        
    except Exception as e:
        logger.error(f"Concurrent limit check failed: {e}")
        return (True, 0)


def release_concurrent(key: str) -> None:
    """Release a concurrent operation slot."""
    try:
        redis = get_redis_connection()
        redis_key = f"concurrent:{key}"
        redis.decr(redis_key)
    except Exception as e:
        logger.error(f"Failed to release concurrent slot: {e}")


def get_rate_limit_key(
    endpoint: str,
    identifier: str,
    identifier_type: str = "ip",
) -> str:
    """
    Generate a rate limit key.
    
    Args:
        endpoint: API endpoint name (e.g., "ask", "ingest")
        identifier: The identifier value (e.g., IP address, session ID)
        identifier_type: Type of identifier ("ip" or "session")
        
    Returns:
        Rate limit key string
    """
    return f"{endpoint}:{identifier_type}:{identifier}"
