"""
Rate limiting middleware and FastAPI dependencies.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.rate_limit import (
    rate_limit,
    check_concurrent_limit,
    get_rate_limit_key,
    RateLimitResult,
)


logger = logging.getLogger(__name__)


# Rate limit configurations
RATE_LIMITS = {
    "ask": {
        "ip": {"max_requests": 10, "window_seconds": 60},       # 10/min per IP
        "session": {"max_requests": 100, "window_seconds": 3600},  # 100/hour per session
    },
    "ingest": {
        "ip": {"max_requests": 3, "window_seconds": 3600},      # 3/hour per IP
        "concurrent": {"max_concurrent": 50},                    # 50 concurrent max
    },
}


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request.
    
    Handles X-Forwarded-For header for proxied requests.
    """
    # Check for forwarded header (reverse proxy)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Take the first IP in the chain
        return forwarded.split(",")[0].strip()
    
    # Check X-Real-IP (nginx)
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    # Fall back to direct connection
    if request.client:
        return request.client.host
    
    return "unknown"


def get_session_id(request: Request) -> Optional[str]:
    """
    Extract session ID from request.
    
    Uses cookie or Authorization header.
    """
    # Check for session cookie
    session_id = request.cookies.get("session_id")
    if session_id:
        return session_id
    
    # Check Authorization header
    auth = request.headers.get("authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:][:32]  # Use first 32 chars as identifier
    
    return None


async def log_rate_limit_violation(
    request: Request,
    endpoint: str,
    client_ip: str,
    limit_type: str,
    limit_config: dict,
) -> None:
    """Log rate limit violation for analysis."""
    logger.warning(
        f"Rate limit violation: endpoint={endpoint}, ip={client_ip}, "
        f"type={limit_type}, limit={limit_config}"
    )
    
    # TODO: Store in rate_limit_violations table
    # This would require database access in hot path
    # Consider async logging or queue-based approach


def create_rate_limit_response(
    result: RateLimitResult,
    limit_description: str,
) -> JSONResponse:
    """Create a 429 Too Many Requests response."""
    retry_after = max(1, result.reset_at - int(time.time()))
    
    response = JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "retry_after": retry_after,
            "limit": limit_description,
            "message": f"Too many requests. Please wait {retry_after} seconds.",
        },
    )
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(result.limit)
    response.headers["X-RateLimit-Remaining"] = str(result.remaining)
    response.headers["X-RateLimit-Reset"] = str(result.reset_at)
    response.headers["Retry-After"] = str(retry_after)
    
    return response


def add_rate_limit_headers(
    response: JSONResponse,
    result: RateLimitResult,
) -> None:
    """Add rate limit headers to a response."""
    response.headers["X-RateLimit-Limit"] = str(result.limit)
    response.headers["X-RateLimit-Remaining"] = str(result.remaining)
    response.headers["X-RateLimit-Reset"] = str(result.reset_at)


# ============================================================================
# FastAPI Dependencies
# ============================================================================

async def check_ask_rate_limit(request: Request) -> RateLimitResult:
    """
    Dependency to check /ask endpoint rate limits.
    
    Raises HTTPException 429 if rate limit exceeded.
    """
    client_ip = get_client_ip(request)
    session_id = get_session_id(request)
    
    # Check IP rate limit (10/min)
    ip_key = get_rate_limit_key("ask", client_ip, "ip")
    ip_config = RATE_LIMITS["ask"]["ip"]
    ip_result = rate_limit(ip_key, ip_config["max_requests"], ip_config["window_seconds"])
    
    if not ip_result.allowed:
        await log_rate_limit_violation(request, "ask", client_ip, "ip", ip_config)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "retry_after": max(1, ip_result.reset_at - int(time.time())),
                "limit": f"{ip_config['max_requests']} requests per minute",
            },
            headers={
                "X-RateLimit-Limit": str(ip_result.limit),
                "X-RateLimit-Remaining": str(ip_result.remaining),
                "X-RateLimit-Reset": str(ip_result.reset_at),
                "Retry-After": str(max(1, ip_result.reset_at - int(time.time()))),
            },
        )
    
    # Check session rate limit if session exists (100/hour)
    if session_id:
        session_key = get_rate_limit_key("ask", session_id, "session")
        session_config = RATE_LIMITS["ask"]["session"]
        session_result = rate_limit(
            session_key,
            session_config["max_requests"],
            session_config["window_seconds"],
        )
        
        if not session_result.allowed:
            await log_rate_limit_violation(request, "ask", client_ip, "session", session_config)
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": max(1, session_result.reset_at - int(time.time())),
                    "limit": f"{session_config['max_requests']} requests per hour",
                },
                headers={
                    "X-RateLimit-Limit": str(session_result.limit),
                    "X-RateLimit-Remaining": str(session_result.remaining),
                    "X-RateLimit-Reset": str(session_result.reset_at),
                    "Retry-After": str(max(1, session_result.reset_at - int(time.time()))),
                },
            )
    
    return ip_result


async def check_ingest_rate_limit(request: Request) -> RateLimitResult:
    """
    Dependency to check /ingest endpoint rate limits.
    
    Raises HTTPException 429 if rate limit exceeded.
    """
    client_ip = get_client_ip(request)
    
    # Check IP rate limit (3/hour)
    ip_key = get_rate_limit_key("ingest", client_ip, "ip")
    ip_config = RATE_LIMITS["ingest"]["ip"]
    ip_result = rate_limit(ip_key, ip_config["max_requests"], ip_config["window_seconds"])
    
    if not ip_result.allowed:
        await log_rate_limit_violation(request, "ingest", client_ip, "ip", ip_config)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "retry_after": max(1, ip_result.reset_at - int(time.time())),
                "limit": f"{ip_config['max_requests']} requests per hour",
            },
            headers={
                "X-RateLimit-Limit": str(ip_result.limit),
                "X-RateLimit-Remaining": str(ip_result.remaining),
                "X-RateLimit-Reset": str(ip_result.reset_at),
                "Retry-After": str(max(1, ip_result.reset_at - int(time.time()))),
            },
        )
    
    # Check concurrent limit (50 max)
    concurrent_config = RATE_LIMITS["ingest"]["concurrent"]
    allowed, current = check_concurrent_limit("ingest", concurrent_config["max_concurrent"])
    
    if not allowed:
        await log_rate_limit_violation(request, "ingest", client_ip, "concurrent", concurrent_config)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Too many concurrent ingestions",
                "error_code": "CONCURRENT_LIMIT_EXCEEDED",
                "retry_after": 60,
                "limit": f"{concurrent_config['max_concurrent']} concurrent operations",
                "current": current,
            },
            headers={
                "Retry-After": "60",
            },
        )
    
    return ip_result


# ============================================================================
# Middleware (Alternative Approach)
# ============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting.
    
    Alternative to dependency injection for global rate limiting.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Only apply to specific paths
        path = request.url.path
        
        # Skip non-rate-limited endpoints
        if not any(path.startswith(p) for p in ["/ask", "/ingest"]):
            return await call_next(request)
        
        client_ip = get_client_ip(request)
        
        # Determine rate limit based on path
        if path == "/ask" and request.method == "POST":
            key = get_rate_limit_key("ask", client_ip, "ip")
            config = RATE_LIMITS["ask"]["ip"]
            result = rate_limit(key, config["max_requests"], config["window_seconds"])
            limit_desc = f"{config['max_requests']} requests per minute"
            
        elif path == "/ingest" and request.method == "POST":
            key = get_rate_limit_key("ingest", client_ip, "ip")
            config = RATE_LIMITS["ingest"]["ip"]
            result = rate_limit(key, config["max_requests"], config["window_seconds"])
            limit_desc = f"{config['max_requests']} requests per hour"
            
        else:
            return await call_next(request)
        
        if not result.allowed:
            return create_rate_limit_response(result, limit_desc)
        
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(result.reset_at)
        
        return response
