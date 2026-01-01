#!/bin/bash
# Start RQ Scheduler for The Arbiter
# Usage: ./start_scheduler.sh

set -e

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "=============================================="
echo "The Arbiter - Starting RQ Scheduler"
echo "=============================================="
echo ""

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠ Redis is not running. Please start Redis first:"
    echo "  redis-server"
    echo ""
    exit 1
fi

echo "✓ Redis is running"
echo ""

# Install rq-scheduler if not present
pip show rq-scheduler > /dev/null 2>&1 || pip install rq-scheduler

# Start the scheduler
python -m app.jobs.scheduler
