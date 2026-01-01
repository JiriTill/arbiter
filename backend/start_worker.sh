#!/bin/bash
# Start RQ Worker for The Arbiter
# Usage: ./start_worker.sh

set -e

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "=============================================="
echo "The Arbiter - Starting RQ Worker"
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

# Start the worker
python -m app.jobs.worker
