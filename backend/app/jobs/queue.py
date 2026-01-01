"""
Queue management for background jobs using Redis and RQ.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

import redis
from rq import Queue
from rq.job import Job

from app.config import get_settings


logger = logging.getLogger(__name__)

# Connection pool for Redis
_redis_pool: redis.ConnectionPool | None = None
_redis_client: redis.Redis | None = None


def get_redis_url() -> str:
    """Get Redis URL from settings."""
    settings = get_settings()
    return settings.redis_url


def get_redis_connection() -> redis.Redis:
    """Get Redis connection from pool."""
    global _redis_pool, _redis_client
    
    if _redis_client is None:
        redis_url = get_redis_url()
        _redis_pool = redis.ConnectionPool.from_url(redis_url)
        _redis_client = redis.Redis(connection_pool=_redis_pool)
        logger.info(f"Connected to Redis at {redis_url}")
    
    return _redis_client


def close_redis_connection():
    """Close Redis connection pool."""
    global _redis_pool, _redis_client
    
    if _redis_client:
        _redis_client.close()
        _redis_client = None
    if _redis_pool:
        _redis_pool.disconnect()
        _redis_pool = None
    logger.info("Redis connection closed")


def get_queue(name: str = "default") -> Queue:
    """Get RQ queue."""
    conn = get_redis_connection()
    return Queue(name, connection=conn)


# ============================================================================
# Job Status Management
# ============================================================================

JOB_STATUS_TTL = 3600  # 1 hour TTL for job status in Redis


def get_job_status_key(job_id: str) -> str:
    """Get Redis key for job status."""
    return f"job_status:{job_id}"


def set_job_status(
    job_id: str,
    state: str,
    pct: int = 0,
    message: str = "",
    result: dict[str, Any] | None = None,
    error: str | None = None,
):
    """
    Set job status in Redis.
    
    Args:
        job_id: The job ID
        state: Current state (queued, downloading, extracting, etc.)
        pct: Progress percentage (0-100)
        message: Human-readable status message
        result: Job result data (when complete)
        error: Error message (if failed)
    """
    conn = get_redis_connection()
    key = get_job_status_key(job_id)
    
    status = {
        "job_id": job_id,
        "state": state,
        "pct": pct,
        "message": message,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    if result:
        status["result"] = result
    if error:
        status["error"] = error
    
    conn.setex(key, JOB_STATUS_TTL, json.dumps(status))
    logger.debug(f"Job {job_id}: {state} ({pct}%) - {message}")


def get_job_status(job_id: str) -> dict[str, Any]:
    """
    Get job status from Redis.
    
    Args:
        job_id: The job ID
        
    Returns:
        Status dict with state, pct, message, result, error
    """
    conn = get_redis_connection()
    key = get_job_status_key(job_id)
    
    data = conn.get(key)
    if data:
        return json.loads(data)
    
    # Try to get status from RQ job itself
    try:
        job = Job.fetch(job_id, connection=conn)
        if job.is_finished:
            return {
                "job_id": job_id,
                "state": "ready",
                "pct": 100,
                "message": "Job completed",
                "result": job.result,
            }
        elif job.is_failed:
            return {
                "job_id": job_id,
                "state": "failed",
                "pct": 0,
                "message": "Job failed",
                "error": str(job.exc_info),
            }
        elif job.is_queued:
            return {
                "job_id": job_id,
                "state": "queued",
                "pct": 0,
                "message": "Job waiting in queue",
            }
        elif job.is_started:
            return {
                "job_id": job_id,
                "state": "processing",
                "pct": 10,
                "message": "Job in progress",
            }
    except Exception as e:
        logger.warning(f"Failed to fetch job {job_id}: {e}")
    
    return {
        "job_id": job_id,
        "state": "unknown",
        "pct": 0,
        "message": "Job not found",
    }


# ============================================================================
# Ingestion Queue
# ============================================================================

def enqueue_ingestion(source_id: int, force: bool = False) -> str:
    """
    Enqueue a source ingestion job.
    
    Args:
        source_id: ID of the source to ingest
        force: If True, re-ingest even if already done
        
    Returns:
        Job ID string
    """
    from app.jobs.ingestion_jobs import ingest_source_job
    
    queue = get_queue("default")
    
    job = queue.enqueue(
        ingest_source_job,
        source_id,
        force,
        job_timeout=300,  # 5 minute timeout
        result_ttl=JOB_STATUS_TTL,
    )
    
    # Set initial status
    set_job_status(
        job.id,
        state="queued",
        pct=0,
        message=f"Ingestion queued for source {source_id}",
    )
    
    logger.info(f"Enqueued ingestion job {job.id} for source {source_id}")
    return job.id


def enqueue_batch_ingestion(source_ids: list[int], force: bool = False) -> list[str]:
    """
    Enqueue multiple source ingestion jobs.
    
    Args:
        source_ids: List of source IDs to ingest
        force: If True, re-ingest even if already done
        
    Returns:
        List of job IDs
    """
    job_ids = []
    for source_id in source_ids:
        job_id = enqueue_ingestion(source_id, force)
        job_ids.append(job_id)
    return job_ids


def get_queue_stats() -> dict[str, Any]:
    """Get queue statistics."""
    queue = get_queue("default")
    
    return {
        "name": queue.name,
        "count": len(queue),
        "failed_count": queue.failed_job_registry.count,
        "scheduled_count": queue.scheduled_job_registry.count,
        "started_count": queue.started_job_registry.count,
        "finished_count": queue.finished_job_registry.count,
    }
