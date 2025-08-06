#!/bin/bash
set -e

# Activate virtual environment
if [ -f ".venv/Scripts/activate" ]; then
  source .venv/Scripts/activate    # Windows Git Bash
elif [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate        # Linux/Mac
else
  echo "Virtual environment not found."
  exit 1
fi

# Ensure Celery is installed
if ! command -v celery &> /dev/null; then
  echo "Installing dependencies..."
  pip install --upgrade pip
  pip install -r requirements.txt
fi

# Start Celery worker with `document` queue
exec celery -A app.core.tasks.celery_app worker \
  --loglevel=info \
  --concurrency="${CELERY_CONCURRENCY:-4}" \
  -Q document
