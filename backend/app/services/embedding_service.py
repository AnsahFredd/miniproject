import os
import logging
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List

from sentence_transformers import SentenceTransformer
import torch
from app.models.document import AcceptedDocument
from app.utils.lazy_model_loader import lazy_loader, require_model

logger = logging.getLogger(__name__)

# === Load model name from environment variable ===
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "AnsahFredd/embedding_model")
logger.info(f"Embedding model configured: {EMBEDDING_MODEL}")

class EmbeddingService:
    def __init__(self):
        self.model_name = EMBEDDING_MODEL
        self.fallback_models = ["sentence-transformers/all-MiniLM-L6-v2"]
        
        logger.info("Embedding service initialized with lazy loading")
    
    @require_model('embedding_primary', EMBEDDING_MODEL, 'embedding', 
                   ["sentence-transformers/all-MiniLM-L6-v2"])
    def _get_sentence_model(self):
        """Get the loaded sentence transformer model."""
        return self._current_model
    
    def generate_embedding(self, text: str):
        """Generate a dense vector embedding for the provided text."""
        try:
            if not text or len(text.strip()) == 0:
                logger.warning("Empty text provided for embedding generation")
                return []
            
            sentence_model = self._get_sentence_model()
            
            # Standard SentenceTransformer case (simplified since we're loading directly)
            embedding = sentence_model.encode(text).tolist()
            
            logger.debug(f"Generated embedding of dimension: {len(embedding)}")
            return embedding
        
        except Exception as e:
            logger.error(f"Error during embedding generation: {e}")
            return []
    
    async def generate_and_store_embeddings(self, user_id: str):
        """
        Generate and store embeddings for all accepted documents for a given user.
        - Splits document into chunks
        - Stores `chunks`, `embedding_chunks`, and `embedding_generated_at`
        """
        try:
            documents = await AcceptedDocument.find({"user_id": user_id}).to_list()
            updated = 0
            skipped = 0

            if not documents:
                return {"message": "No documents found for user."}

            sentence_model = self._get_sentence_model()

            for doc in documents:
                if not doc.content:
                    logger.warning(f"Document {doc.id} has no content, skipping")
                    skipped += 1
                    continue

                try:
                    chunks = self._chunk_text(doc.content)
                    
                    # Generate embeddings for chunks (simplified)
                    embeddings = sentence_model.encode(chunks).tolist()

                    # Compute average embedding for full document
                    full_embedding = np.mean(embeddings, axis=0).tolist()

                    # Update the document
                    await AcceptedDocument.find_one(AcceptedDocument.id == doc.id).update(
                        {
                            "$set": {
                                "chunks": chunks,
                                "embedding_chunks": embeddings,
                                "embedding": full_embedding,
                                "embedding_generated_at": datetime.utcnow(),
                            }
                        }
                    )
                    updated += 1
                    logger.debug(f"Updated embeddings for document {doc.id}")
                    
                except Exception as e:
                    logger.error(f"Failed to process document {doc.id}: {e}")
                    skipped += 1

            logger.info(f"Embedding generation completed: {updated} updated, {skipped} skipped")
            return {
                "message": f"Processed {updated} documents. Skipped {skipped} (no content or errors)."
            }
            
        except Exception as e:
            logger.error(f"Error in generate_and_store_embeddings: {e}")
            return {
                "error": f"Failed to process embeddings: {str(e)}"
            }
    
    def _chunk_text(self, text: str, max_length: int = 512) -> List[str]:
        """
        Split long text into manageable chunks based on sentence length.
        """
        sentences = text.split(". ")
        chunks, current = [], ""
        for sentence in sentences:
            if len(current) + len(sentence) < max_length:
                current += sentence + ". "
            else:
                chunks.append(current.strip())
                current = sentence + ". "
        if current:
            chunks.append(current.strip())
        return chunks
    
    def get_model_info(self) -> dict:
        """Return information about the loaded embedding model."""
        try:
            model_info = {
                "model_type": self.model_name,
                "model_loaded": lazy_loader.is_model_loaded('embedding_primary'),
                "fallback_models": self.fallback_models,
                "source": "hugging_face_hub"
            }
            
            if lazy_loader.is_model_loaded('embedding_primary'):
                try:
                    sentence_model = self._get_sentence_model()
                    test_embedding = sentence_model.encode("test")
                    model_info["embedding_dimension"] = len(test_embedding)
                except Exception as e:
                    model_info["embedding_dimension_error"] = str(e)
            
            return model_info
            
        except Exception as e:
            return {
                "error": str(e),
                "model_loaded": False
            }

embedding_service = EmbeddingService()

def generate_embedding(text: str):
    """Generate a dense vector embedding for the provided text."""
    return embedding_service.generate_embedding(text)

async def generate_and_store_embeddings(user_id: str):
    """
    Generate and store embeddings for all accepted documents for a given user.
    """
    return await embedding_service.generate_and_store_embeddings(user_id)

def get_model_info() -> dict:
    """Return information about the loaded embedding model."""
    return embedding_service.get_model_info()
