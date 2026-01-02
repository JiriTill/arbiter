#!/bin/bash
set -e

echo "Starting The Arbiter..."

# Activate venv if it exists (for local testing)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start RQ Worker in background
echo "Starting RQ Worker..."
python -m rq.cli worker --url $REDIS_URL &
WORKER_PID=$!

# Start API in foreground
echo "Starting FastAP API..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT

# Cleanup worker on exit
kill $WORKER_PID
