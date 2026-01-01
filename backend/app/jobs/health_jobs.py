"""
Health check jobs for monitoring source URLs.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.db.connection import get_sync_connection


logger = logging.getLogger(__name__)


# Request configuration
REQUEST_TIMEOUT = 10.0  # seconds
USER_AGENT = "The-Arbiter-HealthCheck/1.0"


def compute_content_hash(content: bytes) -> str:
    """Compute SHA-256 hash of content."""
    return hashlib.sha256(content).hexdigest()


def check_source_health(source_id: int) -> dict[str, Any]:
    """
    Check health of a single source URL.
    
    Performs:
    1. HEAD request to check availability
    2. If accessible, compare hash to detect changes
    3. Update health status in database
    4. Set needs_reingest if content changed
    
    Args:
        source_id: ID of the game_source to check
        
    Returns:
        Dict with check results
    """
    result = {
        "source_id": source_id,
        "status": "error",
        "http_code": None,
        "file_hash": None,
        "content_length": None,
        "etag": None,
        "last_modified": None,
        "error": None,
        "hash_match": None,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    
    try:
        with get_sync_connection() as conn:
            with conn.cursor() as cur:
                # Get source info
                cur.execute("""
                    SELECT id, source_url, file_hash
                    FROM game_sources
                    WHERE id = %s
                """, (source_id,))
                
                source = cur.fetchone()
                if not source:
                    result["error"] = f"Source {source_id} not found"
                    return result
                
                source_url = source["source_url"]
                stored_hash = source["file_hash"]
                
                if not source_url:
                    result["status"] = "error"
                    result["error"] = "No source URL configured"
                    _save_health_result(cur, source_id, result)
                    conn.commit()
                    return result
                
                # Perform HEAD request
                try:
                    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                        head_response = client.head(
                            source_url,
                            headers={"User-Agent": USER_AGENT},
                            follow_redirects=True,
                        )
                        
                        result["http_code"] = head_response.status_code
                        result["content_length"] = int(head_response.headers.get("content-length", 0))
                        result["etag"] = head_response.headers.get("etag")
                        result["last_modified"] = head_response.headers.get("last-modified")
                        
                        if head_response.status_code == 200:
                            # Source is accessible
                            # Do a full GET to compute hash for comparison
                            if stored_hash:
                                get_response = client.get(
                                    source_url,
                                    headers={"User-Agent": USER_AGENT},
                                    follow_redirects=True,
                                )
                                
                                if get_response.status_code == 200:
                                    new_hash = compute_content_hash(get_response.content)
                                    result["file_hash"] = new_hash
                                    
                                    if new_hash != stored_hash:
                                        # Content has changed!
                                        result["status"] = "changed"
                                        result["hash_match"] = False
                                        
                                        # Mark for re-ingestion
                                        cur.execute("""
                                            UPDATE game_sources
                                            SET needs_reingest = TRUE,
                                                last_health_check = NOW(),
                                                updated_at = NOW()
                                            WHERE id = %s
                                        """, (source_id,))
                                        
                                        logger.warning(
                                            f"Source {source_id} content changed: "
                                            f"old_hash={stored_hash[:8]}..., new_hash={new_hash[:8]}..."
                                        )
                                    else:
                                        # Content unchanged
                                        result["status"] = "ok"
                                        result["hash_match"] = True
                                        
                                        cur.execute("""
                                            UPDATE game_sources
                                            SET last_health_check = NOW()
                                            WHERE id = %s
                                        """, (source_id,))
                            else:
                                # No stored hash, just check accessibility
                                result["status"] = "ok"
                                
                                cur.execute("""
                                    UPDATE game_sources
                                    SET last_health_check = NOW()
                                    WHERE id = %s
                                """, (source_id,))
                        
                        elif head_response.status_code in (301, 302, 303, 307, 308):
                            # Redirect (shouldn't happen with follow_redirects)
                            result["status"] = "ok"
                        
                        elif head_response.status_code in (403, 404, 410):
                            # Client errors - URL no longer accessible
                            result["status"] = "unreachable"
                            result["error"] = f"HTTP {head_response.status_code}"
                        
                        elif head_response.status_code >= 500:
                            # Server errors
                            result["status"] = "error"
                            result["error"] = f"Server error: HTTP {head_response.status_code}"
                        
                        else:
                            result["status"] = "error"
                            result["error"] = f"Unexpected status: HTTP {head_response.status_code}"
                
                except httpx.TimeoutException:
                    result["status"] = "error"
                    result["error"] = "Request timed out"
                
                except httpx.ConnectError as e:
                    result["status"] = "unreachable"
                    result["error"] = f"Connection failed: {str(e)[:100]}"
                
                except httpx.HTTPError as e:
                    result["status"] = "error"
                    result["error"] = f"HTTP error: {str(e)[:100]}"
                
                # Save health check result
                _save_health_result(cur, source_id, result)
                conn.commit()
    
    except Exception as e:
        logger.error(f"Health check failed for source {source_id}: {e}")
        result["status"] = "error"
        result["error"] = str(e)[:200]
    
    return result


def _save_health_result(cur, source_id: int, result: dict) -> None:
    """Save health check result to database."""
    cur.execute("""
        INSERT INTO source_health (
            source_id, last_checked_at, status, http_code,
            file_hash, content_length, etag, last_modified, error
        ) VALUES (
            %s, NOW(), %s, %s, %s, %s, %s, %s, %s
        )
    """, (
        source_id,
        result["status"],
        result["http_code"],
        result["file_hash"],
        result["content_length"],
        result["etag"],
        result["last_modified"],
        result["error"],
    ))


def check_all_sources() -> dict[str, Any]:
    """
    Check health of all game sources.
    
    Returns:
        Summary statistics
    """
    start_time = datetime.now(timezone.utc)
    logger.info("Starting health check for all sources...")
    
    result = {
        "total": 0,
        "ok": 0,
        "changed": 0,
        "unreachable": 0,
        "error": 0,
        "source_results": [],
        "started_at": start_time.isoformat(),
        "completed_at": None,
        "duration_ms": 0,
    }
    
    try:
        with get_sync_connection() as conn:
            with conn.cursor() as cur:
                # Get all sources with URLs
                cur.execute("""
                    SELECT id, source_url
                    FROM game_sources
                    WHERE source_url IS NOT NULL
                    ORDER BY id
                """)
                
                sources = cur.fetchall()
                result["total"] = len(sources)
                
                logger.info(f"Checking {len(sources)} sources...")
                
                for source in sources:
                    source_id = source["id"]
                    check_result = check_source_health(source_id)
                    
                    status = check_result["status"]
                    result[status] = result.get(status, 0) + 1
                    
                    result["source_results"].append({
                        "source_id": source_id,
                        "status": status,
                        "http_code": check_result["http_code"],
                    })
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        result["error_message"] = str(e)
    
    end_time = datetime.now(timezone.utc)
    result["completed_at"] = end_time.isoformat()
    result["duration_ms"] = int((end_time - start_time).total_seconds() * 1000)
    result["problems"] = result["changed"] + result["unreachable"] + result["error"]
    
    logger.info(
        f"Health check completed: {result['total']} sources, "
        f"{result['ok']} ok, {result['problems']} problems"
    )
    
    return result


def get_health_summary() -> dict[str, Any]:
    """
    Get summary of latest health status for all sources.
    
    Returns:
        Summary with source statuses
    """
    try:
        with get_sync_connection() as conn:
            with conn.cursor() as cur:
                # Get latest status per source from view
                cur.execute("""
                    SELECT 
                        source_id,
                        game_name,
                        edition,
                        source_url,
                        status,
                        http_code,
                        last_checked_at,
                        needs_reingest,
                        error
                    FROM source_health_latest
                    ORDER BY 
                        CASE status 
                            WHEN 'changed' THEN 1 
                            WHEN 'unreachable' THEN 2 
                            WHEN 'error' THEN 3 
                            ELSE 4 
                        END,
                        game_name
                """)
                
                rows = cur.fetchall()
                
                # Count by status
                status_counts = {
                    "ok": 0,
                    "changed": 0,
                    "unreachable": 0,
                    "error": 0,
                }
                
                sources = []
                for row in rows:
                    status = row["status"]
                    status_counts[status] = status_counts.get(status, 0) + 1
                    sources.append(dict(row))
                
                return {
                    "total": len(sources),
                    "status_counts": status_counts,
                    "sources": sources,
                }
    
    except Exception as e:
        logger.error(f"Failed to get health summary: {e}")
        return {
            "error": str(e),
            "total": 0,
            "sources": [],
        }
