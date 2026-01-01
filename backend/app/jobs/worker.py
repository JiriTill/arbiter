#!/usr/bin/env python3
"""
RQ Worker for The Arbiter background jobs.

Run with:
    python -m app.jobs.worker

Or use the start_worker script:
    ./start_worker.sh (Linux/Mac)
    start_worker.bat (Windows)
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from redis import Redis
from rq import Worker, Queue, Connection

from app.config import get_settings
from app.jobs.queue import get_redis_connection


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# Queues to listen to
QUEUES = ["default"]

# Worker configuration
WORKER_CONFIG = {
    "name": "arbiter-worker",
    "default_worker_ttl": 420,  # 7 minutes
    "job_monitoring_interval": 5,
}


def run_worker():
    """Run the RQ worker."""
    settings = get_settings()
    
    logger.info("=" * 50)
    logger.info("The Arbiter - RQ Worker")
    logger.info("=" * 50)
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Redis URL: {settings.redis_url}")
    logger.info(f"Queues: {', '.join(QUEUES)}")
    logger.info("")
    
    conn = get_redis_connection()
    
    # Test Redis connection
    try:
        conn.ping()
        logger.info("✓ Redis connection successful")
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        sys.exit(1)
    
    # Create queues
    queues = [Queue(name, connection=conn) for name in QUEUES]
    
    # Start worker
    logger.info("")
    logger.info("Starting worker, listening on queues...")
    logger.info("Press Ctrl+C to exit")
    logger.info("")
    
    with Connection(conn):
        worker = Worker(
            queues,
            name=WORKER_CONFIG["name"],
            default_worker_ttl=WORKER_CONFIG["default_worker_ttl"],
            job_monitoring_interval=WORKER_CONFIG["job_monitoring_interval"],
        )
        worker.work(with_scheduler=True)


if __name__ == "__main__":
    run_worker()
