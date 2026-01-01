# Background Jobs Directory

This directory contains RQ (Redis Queue) background job workers for The Arbiter.

## Planned Jobs

| Job | Description |
|-----|-------------|
| `ingest.py` | PDF ingestion and chunking |
| `embed.py` | Batch embedding generation |
| `health_check.py` | Source URL health monitoring |
| `cleanup.py` | Expired chunk cleanup |

## Running Workers

```bash
# Start a worker
rq worker arbiter-jobs

# Start with specific queues
rq worker high default low

# Monitor jobs
rq info
```

## Job Pattern

```python
# jobs/example.py

from rq import Queue
from redis import Redis
from app.config import get_settings

settings = get_settings()
redis_conn = Redis.from_url(settings.redis_url)
queue = Queue("arbiter-jobs", connection=redis_conn)

def example_job(param1: str, param2: int) -> dict:
    """Job function - must be importable."""
    # Do work...
    return {"status": "complete"}

# Enqueue from routes
def enqueue_example(param1: str, param2: int):
    job = queue.enqueue(example_job, param1, param2)
    return job.id
```

## Queue Priority

- `high`: User-facing operations (immediate feedback needed)
- `default`: Standard background processing
- `low`: Batch operations, cleanup, etc.
