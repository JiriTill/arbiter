"""
Cleanup jobs for maintaining data hygiene.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from app.db.connection import get_sync_connection


logger = logging.getLogger(__name__)


def cleanup_expired_chunks() -> dict[str, Any]:
    """
    Delete expired chunks and mark affected sources for re-ingestion.
    
    This job:
    1. Finds all chunks where expires_at < now()
    2. Gets the unique source IDs for those chunks
    3. Deletes the expired chunks
    4. Marks affected sources as needs_reingest = true
    
    Returns:
        Stats dict with deleted_chunks and affected_sources counts
    """
    start_time = datetime.now(timezone.utc)
    logger.info("Starting expired chunks cleanup...")
    
    result = {
        "deleted_chunks": 0,
        "affected_sources": 0,
        "source_ids": [],
        "started_at": start_time.isoformat(),
        "completed_at": None,
        "duration_ms": 0,
    }
    
    try:
        with get_sync_connection() as conn:
            with conn.cursor() as cur:
                # Step 1: Find affected source IDs before deleting
                cur.execute("""
                    SELECT DISTINCT source_id 
                    FROM rule_chunks 
                    WHERE expires_at IS NOT NULL 
                      AND expires_at < NOW()
                """)
                affected_sources = [row["source_id"] for row in cur.fetchall()]
                result["source_ids"] = affected_sources
                result["affected_sources"] = len(affected_sources)
                
                if not affected_sources:
                    logger.info("No expired chunks found")
                    result["completed_at"] = datetime.now(timezone.utc).isoformat()
                    return result
                
                logger.info(f"Found {len(affected_sources)} sources with expired chunks")
                
                # Step 2: Delete expired chunks
                cur.execute("""
                    DELETE FROM rule_chunks 
                    WHERE expires_at IS NOT NULL 
                      AND expires_at < NOW()
                    RETURNING id
                """)
                deleted_ids = cur.fetchall()
                result["deleted_chunks"] = len(deleted_ids)
                
                logger.info(f"Deleted {len(deleted_ids)} expired chunks")
                
                # Step 3: Mark affected sources for re-ingestion
                if affected_sources:
                    placeholders = ", ".join(["%s"] * len(affected_sources))
                    cur.execute(f"""
                        UPDATE game_sources 
                        SET needs_reingest = TRUE,
                            last_ingested_at = NULL,
                            updated_at = NOW()
                        WHERE id IN ({placeholders})
                    """, tuple(affected_sources))
                    
                    logger.info(f"Marked {len(affected_sources)} sources for re-ingestion")
                
                conn.commit()
        
        end_time = datetime.now(timezone.utc)
        result["completed_at"] = end_time.isoformat()
        result["duration_ms"] = int((end_time - start_time).total_seconds() * 1000)
        
        logger.info(
            f"Cleanup completed: {result['deleted_chunks']} chunks deleted, "
            f"{result['affected_sources']} sources marked for re-ingestion"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        result["error"] = str(e)
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        return result


def cleanup_old_history(days_to_keep: int = 90) -> dict[str, Any]:
    """
    Delete old ask_history entries.
    
    Args:
        days_to_keep: Number of days of history to retain
        
    Returns:
        Stats dict with deleted_entries count
    """
    logger.info(f"Cleaning up history older than {days_to_keep} days...")
    
    result = {
        "deleted_entries": 0,
        "days_retained": days_to_keep,
    }
    
    try:
        with get_sync_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM ask_history 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                    RETURNING id
                """, (days_to_keep,))
                deleted = cur.fetchall()
                result["deleted_entries"] = len(deleted)
                conn.commit()
        
        logger.info(f"Deleted {result['deleted_entries']} old history entries")
        return result
        
    except Exception as e:
        logger.error(f"History cleanup failed: {e}")
        result["error"] = str(e)
        return result


def cleanup_rate_limit_violations(days_to_keep: int = 30) -> dict[str, Any]:
    """
    Delete old rate limit violation records.
    
    Args:
        days_to_keep: Number of days of violations to retain
        
    Returns:
        Stats dict with deleted_entries count
    """
    logger.info(f"Cleaning up rate limit violations older than {days_to_keep} days...")
    
    result = {
        "deleted_entries": 0,
        "days_retained": days_to_keep,
    }
    
    try:
        with get_sync_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM rate_limit_violations 
                    WHERE violated_at < NOW() - INTERVAL '%s days'
                    RETURNING id
                """, (days_to_keep,))
                deleted = cur.fetchall()
                result["deleted_entries"] = len(deleted)
                conn.commit()
        
        logger.info(f"Deleted {result['deleted_entries']} old violation records")
        return result
        
    except Exception as e:
        logger.error(f"Violations cleanup failed: {e}")
        result["error"] = str(e)
        return result


def run_all_cleanup_jobs() -> dict[str, Any]:
    """
    Run all cleanup jobs.
    
    Returns:
        Combined stats from all cleanup jobs
    """
    logger.info("Running all cleanup jobs...")
    
    results = {
        "chunks": cleanup_expired_chunks(),
        "history": cleanup_old_history(days_to_keep=90),
    }
    
    # Only run if table exists (migration may not have run)
    try:
        results["violations"] = cleanup_rate_limit_violations(days_to_keep=30)
    except Exception as e:
        logger.warning(f"Violations cleanup skipped: {e}")
        results["violations"] = {"skipped": True, "reason": str(e)}
    
    logger.info("All cleanup jobs completed")
    return results
