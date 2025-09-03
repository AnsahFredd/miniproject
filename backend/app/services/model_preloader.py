import os
import logging
import httpx
import numpy as np
from typing import Optional, Dict, Any, List

from app.services.summarization_service import get_service as get_summarization_service
from app.services.embedding import LocalEmbeddingService, health_check as embedding_health_check, embedding_service
from app.services.classification import classify_document, model_handler
from app.services.classification.service import DocumentClassificationService

logger = logging.getLogger(__name__)

# Environment flag to detect Celery worker
IS_CELERY_WORKER = os.environ.get("IS_CELERY_WORKER", "0") == "1"
FASTAPI_URL = os.environ.get("FASTAPI_URL", "http://localhost:8000")

# Singleton embedding service
embedding_service = LocalEmbeddingService()

async def generate_embedding(text: str) -> np.ndarray:
    result = await embedding_service.generate_embedding(text)
    if isinstance(result, list):
        return np.array(result)
    elif isinstance(result, np.ndarray):
        return result
    else:
        raise ValueError(f"Invalid embedding type returned: {type(result)}")


def generate_embedding_batch(texts: List[str]):
    return embedding_service.generate_embedding_batch(texts)


async def generate_and_store_embeddings(user_id: str):
    return await embedding_service.generate_and_store_embeddings(user_id)


def get_embedding_model_info() -> dict:
    return embedding_service.get_model_info()


def embedding_health_check_wrapper() -> dict:
    return embedding_health_check()


class ModelPreloader:
    def __init__(self):
        self.summarization_service = None
        self.classification_service = None
        self.embedding_service = embedding_service
        self.models_loaded = False
        self.http_client: Optional[httpx.AsyncClient] = None

        if IS_CELERY_WORKER:
            # HTTP client for Celery worker mode
            self.http_client = httpx.AsyncClient(base_url=FASTAPI_URL, timeout=60)

    async def initialize_models(self):
        """Initialize local models (skip if running as Celery worker)"""
        if IS_CELERY_WORKER:
            logger.info("[Preloader] Running in Celery worker mode. Skipping local model loading.")
            self.models_loaded = True
            return
        
        try:
            logger.info("[Preloader] Starting local model initialization...")

            # Summarization
            logger.info("[Preloader] Loading summarization model locally...")
            self.summarization_service = await get_summarization_service()
            logger.info("[Preloader] Summarization model loaded successfully.")

            # Classification
            logger.info("[Preloader] Loading classification model locally...")
            if not model_handler.initialized:
                await model_handler.initialize()
            self.classification_service = DocumentClassificationService()

            # Test classification
            test_result = await self.classification_service.classify_document_async(
                "This is a test legal contract for initialization.",
                "test_document.pdf"
            )
            if test_result.get("document_type"):
                logger.info(f"[Preloader] Classification test successful: {test_result['document_type']} "
                            f"(method: {test_result['classification_method']})")
            else:
                logger.warning("[Preloader] Classification test returned no document type")

            logger.info("[Preloader] Classification model loaded.")

            # Embedding service
            logger.info("[Preloader] Initializing embedding model...")
            if not embedding_service.initialize:
                await embedding_service.initialize()

            test_embedding = await generate_embedding("test text for initialization")
            logger.info(f"[Preloader] Embedding model loaded. Vector dimension: {test_embedding.shape[0]}")

            self.models_loaded = True
            logger.info("[Preloader] All models initialized successfully.")

        except Exception as e:
            logger.error(f"[Preloader] Model preloading failed: {e}")
            raise

    async def get_summarization_service(self):
        if IS_CELERY_WORKER:
            return self._http_proxy_service("summarization")
        return self.summarization_service

    async def get_classification_service(self):
        if IS_CELERY_WORKER:
            return self._http_proxy_service("classification")
        return self.classification_service

    async def get_embedding_service(self):
        if IS_CELERY_WORKER:
            return self._http_proxy_service("embedding")
        return self.embedding_service

    async def health_check(self) -> Dict[str, Any]:
        status = {
            "models_loaded": self.models_loaded,
            "summarization_healthy": False,
            "classification_healthy": False,
            "embedding_healthy": False,
            "overall_healthy": False,
        }
        try:
            if IS_CELERY_WORKER:
                resp = await self.http_client.get("/api/v1/health")
                data = resp.json()
                status.update(data)
                return status

            # Local health checks
            if self.summarization_service:
                sum_health = await self.summarization_service.health_check()
                status["summarization_healthy"] = sum_health.get("healthy", False)

            class_health = await self.classification_service.classify_document_async(
                "health check", "dummy.pdf"
            )
            status["classification_healthy"] = class_health.get("document_type") is not None

            embed_health = embedding_health_check_wrapper()
            status["embedding_healthy"] = embed_health.get("healthy", False)

            status["overall_healthy"] = all([
                status["models_loaded"],
                status["summarization_healthy"],
                status["classification_healthy"],
                status["embedding_healthy"]
            ])

            return status

        except Exception as e:
            logger.error(f"[Preloader] Health check failed: {e}")
            return {"overall_healthy": False, "error": str(e)}

    def _http_proxy_service(self, service_type: str, params: dict = None):
        class HTTPServiceProxy:
            def __init__(self, client: httpx.AsyncClient, service_type: str, params: dict = None):
                self.client = client
                self.service_type = service_type
                self.params = params or {}

            async def __getattr__(self, name):
                async def caller(*args, **kwargs):
                    endpoint = f"/api/v1/{self.service_type}/{name}"
                    payload = {"args": args, "kwargs": kwargs, **self.params}
                    resp = await self.client.post(endpoint, json=payload)
                    resp.raise_for_status()
                    return resp.json()
                return caller

        return HTTPServiceProxy(self.http_client, service_type, params)


# Singleton instance
model_preloader = ModelPreloader()
