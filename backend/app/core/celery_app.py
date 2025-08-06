from celery import Celery
import os

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://localhost:6379/1")

celery_app = Celery(
    "lawlens_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BACKEND_URL,
)

# Autodiscover tasks in the `app.tasks` package
celery_app.autodiscover_tasks(["app.tasks"])
