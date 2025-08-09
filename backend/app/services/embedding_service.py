import os
import logging
import numpy as np
from datetime import datetime
from typing import List, Optional

from sentence_transformers import SentenceTransformer
from app.core.runtime import setup_runtime, get_cache_dir
from app.models.document import AcceptedDocument  # keep original import path used in your app

setup_runtime()
logger = logging.getLogger(__name__)

def resolve_embedding_model_id() -> str:
    # First prefer env override
    env_id = os.getenv("EMBEDDING_MODEL")
    if env_id:
        return env_id
    # Try settings if present
    try:
        from core.config import settings
        if getattr(settings, "EMBEDDING_MODEL", None):
            return str(settings.EMBEDDING_MODEL)
    except Exception:
        pass
    # Lightweight default that runs on CPU easily
    return "sentence-transformers/all-MiniLM-L6-v2"

FALLBACKS = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "sentence-transformers/all-MiniLM-L12-v2",
]

class EmbeddingService:
    def __init__(self):
        self.model_id = resolve_embedding_model_id()
        self._model: Optional[SentenceTransformer] = None
        logger.info(f"EmbeddingService initialized. Model candidate: {self.model_id}")

    def _ensure_loaded(self):
        if self._model is not None:
            return
        last_err: Optional[Exception] = None
        tried = [self.model_id] + [m for m in FALLBACKS if m != self.model_id]
        for mid in tried:
            try:
                logger.info(f"Loading SentenceTransformer {mid} with cache_folder={get_cache_dir()}")
                self._model = SentenceTransformer(mid, cache_folder=get_cache_dir())
                logger.info(f"Loaded embedding model: {mid}")
                if mid != self.model_id:
                    logger.warning(f"EmbeddingService fell back to {mid}")
                return
            except Exception as e:
                last_err = e
                logger.warning(f"Failed to load embedding model {mid}: {e}")
        raise RuntimeError(f"No embedding model available. Last error: {last_err}")

    def generate_embedding(self, text: str) -> List[float]:
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation")
            return []
        self._ensure_loaded()
        vec = self._model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def chunk_text(self, text: str, max_length: int = 512) -> List[str]:
        # Simple sentence split to constrain memory during batch encoding
        sentences = [s.strip() for s in text.split(". ") if s.strip()]
        chunks, cur = [], ""
        for s in sentences:
            if len(cur) + len(s) + 2 <= max_length:
                cur = (cur + " " + s).strip()
            else:
                if cur:
                    chunks.append(cur)
                cur = s
        if cur:
            chunks.append(cur)
        return chunks

    async def generate_and_store_embeddings(self, user_id: str):
        """
        Generate embeddings for all accepted docs of user:
        - Chunks content to reduce memory.
        - Stores chunk embeddings and an averaged document embedding.
        """
        self._ensure_loaded()
        docs = await AcceptedDocument.find({"user_id": user_id}).to_list()
        if not docs:
            return {"message": "No documents found for user."}
        updated = 0
        skipped = 0
        for doc in docs:
            try:
                if not getattr(doc, "content", None):
                    skipped += 1
                    continue
                chunks = self.chunk_text(doc.content, 512)
                # Encode in small batches to keep RAM low
                embeddings = self._model.encode(chunks, batch_size=8, normalize_embeddings=True)
                full_embedding = np.mean(embeddings, axis=0).tolist()
                await AcceptedDocument.find_one(AcceptedDocument.id == doc.id).update(
                    {
                        "$set": {
                            "chunks": chunks,
                            "embedding_chunks": [e.tolist() for e in embeddings],
                            "embedding": full_embedding,
                            "embedding_generated_at": datetime.utcnow(),
                        }
                    }
                )
                updated += 1
            except Exception as e:
                logger.error(f"Failed to embed document {getattr(doc, 'id', '?')}: {e}")
                skipped += 1
        return {"message": f"Processed {updated} documents. Skipped {skipped}."}

    def get_model_info(self) -> dict:
        return {
            "model_id": self.model_id,
            "loaded": self._model is not None,
            "cache_dir": os.getenv("TRANSFORMERS_CACHE"),
            "dim": (len(self._model.encode("x")) if self._model else None),
        }

embedding_service = EmbeddingService()

# Backwards-compatible functions
def generate_embedding(text: str) -> List[float]:
    return embedding_service.generate_embedding(text)

async def generate_and_store_embeddings(user_id: str):
    return await embedding_service.generate_and_store_embeddings(user_id)

def get_model_info() -> dict:
    return embedding_service.get_model_info()
