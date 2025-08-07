# Celery taskt definitions


from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "lawlens_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BACKEND_URL,
)
celery_app.conf.task_routes = {
    "app.workers.processor.process_document_task": {"queue": "documents"},
}

