from celery import Celery
import os

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://red-d2cegfmr433s73aku840:6379/0")
CELERY_BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://red-d2cegfmr433s73aku840:6379/1")

celery_app = Celery(
    "lawlens_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BACKEND_URL,
)

celery_app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_BACKEND_URL,
    task_queues={
        "document": {"exchange": "document", "routing_key": "document"},
    },
)

# Autodiscover tasks in the `app.tasks` package
celery_app.autodiscover_tasks(["app.tasks"])
