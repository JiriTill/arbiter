"""
RQ Scheduler for periodic background jobs.
"""

import logging
from datetime import datetime, timedelta, timezone

from rq_scheduler import Scheduler

from app.jobs.queue import get_redis_connection


logger = logging.getLogger(__name__)


def get_scheduler() -> Scheduler:
    """Get RQ Scheduler instance."""
    conn = get_redis_connection()
    return Scheduler(connection=conn)


def schedule_cleanup_jobs():
    """
    Schedule all periodic cleanup jobs.
    
    Jobs scheduled:
    - cleanup_expired_chunks: Daily at 3 AM UTC
    - run_all_cleanup_jobs: Weekly on Sunday at 4 AM UTC
    """
    scheduler = get_scheduler()
    
    # Clear existing scheduled jobs (to avoid duplicates on restart)
    for job in scheduler.get_jobs():
        if job.meta.get("scheduled_by") == "arbiter":
            scheduler.cancel(job)
            logger.info(f"Cancelled existing job: {job.id}")
    
    # Schedule daily chunk cleanup at 3 AM UTC
    from app.jobs.cleanup_jobs import cleanup_expired_chunks
    
    scheduler.cron(
        "0 3 * * *",  # 3:00 AM UTC daily
        func=cleanup_expired_chunks,
        id="cleanup_expired_chunks_daily",
        timeout=600,  # 10 minute timeout
        meta={"scheduled_by": "arbiter"},
    )
    logger.info("Scheduled cleanup_expired_chunks: daily at 3 AM UTC")
    
    # Schedule weekly full cleanup on Sunday at 4 AM UTC
    from app.jobs.cleanup_jobs import run_all_cleanup_jobs
    
    scheduler.cron(
        "0 4 * * 0",  # 4:00 AM UTC on Sunday
        func=run_all_cleanup_jobs,
        id="run_all_cleanup_weekly",
        timeout=1800,  # 30 minute timeout
        meta={"scheduled_by": "arbiter"},
    )
    logger.info("Scheduled run_all_cleanup_jobs: weekly on Sunday at 4 AM UTC")
    
    # Schedule daily source health check at 2 AM UTC
    from app.jobs.health_jobs import check_all_sources
    
    scheduler.cron(
        "0 2 * * *",  # 2:00 AM UTC daily
        func=check_all_sources,
        id="check_all_sources_daily",
        timeout=1800,  # 30 minute timeout (many sources)
        meta={"scheduled_by": "arbiter"},
    )
    logger.info("Scheduled check_all_sources: daily at 2 AM UTC")
    
    return scheduler


def list_scheduled_jobs() -> list[dict]:
    """List all scheduled jobs."""
    scheduler = get_scheduler()
    jobs = []
    
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "func": job.func_name,
            "timeout": job.timeout,
            "meta": job.meta,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        })
    
    return jobs


def run_scheduler():
    """Run the RQ Scheduler."""
    logger.info("=" * 50)
    logger.info("The Arbiter - RQ Scheduler")
    logger.info("=" * 50)
    
    # Schedule jobs
    scheduler = schedule_cleanup_jobs()
    
    # List scheduled jobs
    jobs = list_scheduled_jobs()
    logger.info(f"Scheduled {len(jobs)} jobs:")
    for job in jobs:
        logger.info(f"  - {job['id']}: {job['func']}")
    
    logger.info("")
    logger.info("Scheduler running. Press Ctrl+C to exit.")
    logger.info("")
    
    # Run scheduler
    scheduler.run()


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add parent to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    run_scheduler()
