#!/bin/bash

# worker_startup.sh - Optimized Celery worker startup for Redis Cloud
# Usage: ./worker_startup.sh [development|production]

set -e

# Load environment variables safely from .env if it exists
if [ -f .env ]; then
  set -o allexport
  source .env
  set +o allexport
fi

ENVIRONMENT=${1:-development}
LOG_LEVEL=${2:-info}

echo "=================================="
echo "CELERY WORKER STARTUP - REDIS CLOUD"
echo "Environment: $ENVIRONMENT"
echo "Log Level: $LOG_LEVEL"
echo "=================================="

# Get the Python path from virtual environment (works in Git Bash / WSL / Linux / Mac)
VENV_PYTHON="./.venv/Scripts/python.exe"
if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON="./.venv/bin/python"
fi

if [ ! -x "$VENV_PYTHON" ]; then
    echo "ERROR: Could not find Python in .venv. Did you activate the virtual environment?"
    exit 1
fi

echo "Using Python interpreter: $VENV_PYTHON"

# Check if Redis URL is set
if [ -z "$REDIS_URL" ]; then
    echo "ERROR: REDIS_URL environment variable is not set"
    echo "Please set REDIS_URL to your Redis Cloud connection string"
    echo "Example: export REDIS_URL='redis://username:password@hostname:port'"
    exit 1
fi

echo "Redis URL configured: ${REDIS_URL:0:20}..."

# Test Redis connection before starting worker
echo "Testing Redis Cloud connection..."
$VENV_PYTHON -c "
import redis, sys, os
try:
    r = redis.from_url(os.getenv('REDIS_URL'), socket_timeout=10, socket_connect_timeout=10)
    r.ping()
    print('Redis Cloud connection successful')
except Exception as e:
    print(f'Redis Cloud connection failed: {e}')
    sys.exit(1)
"
if [ $? -ne 0 ]; then
    echo "Redis connection failed. Please check your REDIS_URL and Redis Cloud status."
    exit 1
fi

# Clear old Redis keys (optional but recommended)
echo "Clearing old Celery keys from Redis..."
$VENV_PYTHON -c "
import redis, os
try:
    r = redis.from_url(os.getenv('REDIS_URL'))
    keys = []
    for key in r.scan_iter(match='celery-task-meta-*'):
        keys.append(key)
    for key in r.scan_iter(match='_kombu.binding.*'):
        keys.append(key)
    if keys:
        r.delete(*keys)
        print(f'Cleared {len(keys)} old Celery keys')
    else:
        print('No old keys to clear')
except Exception as e:
    print(f'Failed to clear keys: {e}')
"

# Set optimized environment variables for Redis Cloud
export C_FORCE_ROOT=1
export CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True
export CELERY_BROKER_CONNECTION_RETRY=True
export CELERY_TASK_SOFT_TIME_LIMIT=600
export CELERY_TASK_TIME_LIMIT=900
export CELERY_WORKER_PREFETCH_MULTIPLIER=1

# Memory optimization
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export TRANSFORMERS_OFFLINE=1

echo "Starting AI model preload test..."
$VENV_PYTHON -c "
try:
    from app.core.celery_app import get_preloaded_models
    models = get_preloaded_models()
    if 'error' in models:
        print(f'Model preload failed: {models[\"error\"]}')
    else:
        loaded = [k for k in models.keys() if not k.endswith('_error')]
        errors = [k for k in models.keys() if k.endswith('_error')]
        print(f'Preloaded {len(loaded)} models: {loaded}')
        if errors:
            print(f'Model errors: {errors}')
except Exception as e:
    print(f'Model preload test failed: {e}')
"

# Worker configuration
if [ "$ENVIRONMENT" = "production" ]; then
    WORKER_ARGS="--loglevel=$LOG_LEVEL --concurrency=2 --max-tasks-per-child=50 --time-limit=900"
    echo "Production mode: Limited concurrency and task recycling enabled"
else
    WORKER_ARGS="--loglevel=$LOG_LEVEL --concurrency=1 --max-tasks-per-child=20"
    echo "Development mode: Single worker process"
fi

# Redis Cloud optimizations
WORKER_ARGS="$WORKER_ARGS --without-gossip --without-mingle --without-heartbeat"

echo "Starting Celery worker with args: $WORKER_ARGS"
echo "Press Ctrl+C to stop the worker"
echo "=================================="

exec $VENV_PYTHON -m celery -A app.core.celery_app worker \
    $WORKER_ARGS \
    --queues=ai_processing,default \
    --pool=prefork \
    --optimization=fair
