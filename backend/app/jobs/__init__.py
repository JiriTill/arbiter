"""Background jobs for The Arbiter."""

from app.jobs.queue import (
    get_redis_connection,
    close_redis_connection,
    get_queue,
    enqueue_ingestion,
    enqueue_batch_ingestion,
    get_job_status,
    set_job_status,
    get_queue_stats,
)
from app.jobs.ingestion_jobs import (
    ingest_source_job,
)
from app.jobs.cleanup_jobs import (
    cleanup_expired_chunks,
    cleanup_old_history,
    cleanup_rate_limit_violations,
    run_all_cleanup_jobs,
)
from app.jobs.health_jobs import (
    check_source_health,
    check_all_sources,
    get_health_summary,
)

__all__ = [
    # Queue management
    "get_redis_connection",
    "close_redis_connection",
    "get_queue",
    "get_queue_stats",
    
    # Job status
    "get_job_status",
    "set_job_status",
    
    # Ingestion jobs
    "enqueue_ingestion",
    "enqueue_batch_ingestion",
    "ingest_source_job",
    
    # Cleanup jobs
    "cleanup_expired_chunks",
    "cleanup_old_history",
    "cleanup_rate_limit_violations",
    "run_all_cleanup_jobs",
    
    # Health jobs
    "check_source_health",
    "check_all_sources",
    "get_health_summary",
]


