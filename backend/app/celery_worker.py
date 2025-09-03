# celery_worker.py - Unified worker entrypoint with Upstash Redis

import logging
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

# Import tasks explicitly so Celery registers them
import app.tasks.document_tasks  # noqa: F401

if __name__ == "__main__":
    logger.info("Starting Celery worker with Upstash Redis...")
    celery_app.start()
