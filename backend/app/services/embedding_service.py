import os
import logging
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List

from sentence_transformers import SentenceTransformer
import torch
from app.models.document import AcceptedDocument
from app.utils.hf_cache import cache_manager

logger = logging.getLogger(__name__)

# === Load model name from environment variable ===
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "AnsahFredd/embedding_model")
logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")

# === Load Embedding Model with cache management ===
sentence_model = None

try:
    logger.info(f"🔄 Loading embedding model from Hugging Face: {EMBEDDING_MODEL}")
    
    sentence_model = cache_manager.load_model_with_retry(
        EMBEDDING_MODEL, 
        model_type="embedding"
    )
    
    if sentence_model:
        logger.info("✅ Embedding model loaded successfully from Hugging Face")
    else:
        raise RuntimeError("Cache manager returned None")
        
except Exception as e:
    logger.error(f"❌ Failed to load embedding model from Hugging Face: {e}")
    # Fallback to alternative model if your repo fails
    try:
        logger.info("🔄 Attempting fallback to sentence-transformers/all-MiniLM-L6-v2...")
        sentence_model = cache_manager.load_model_with_retry(
            "sentence-transformers/all-MiniLM-L6-v2", 
            model_type="embedding"
        )
        
        if sentence_model:
            logger.warning("⚠️ Using fallback embedding model")
        else:
            raise RuntimeError("Cache manager returned None")
    except Exception as fallback_error:
        logger.error(f"❌ Complete failure to load any embedding model: {fallback_error}")
        raise fallback_error

if sentence_model is None:
    raise RuntimeError("❌ No embedding model could be loaded!")

# === Helper: Chunk Text for Embedding ===
def chunk_text(text: str, max_length: int = 512) -> List[str]:
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

# === Public: Generate Embedding Vector for Text ===
def generate_embedding(text: str):
    """Generate a dense vector embedding for the provided text."""
    try:
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for embedding generation")
            return []
        
        # Standard SentenceTransformer case (simplified since we're loading directly)
        embedding = sentence_model.encode(text).tolist()
        
        logger.debug(f"Generated embedding of dimension: {len(embedding)}")
        return embedding
    
    except Exception as e:
        logger.error(f"Error during embedding generation: {e}")
        return []

# === Public: Generate and Store Embeddings for User's Documents ===
async def generate_and_store_embeddings(user_id: str):
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

        for doc in documents:
            if not doc.content:
                logger.warning(f"Document {doc.id} has no content, skipping")
                skipped += 1
                continue

            try:
                chunks = chunk_text(doc.content)
                
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

def get_model_info() -> dict:
    """Return information about the loaded embedding model."""
    try:
        model_info = {
            "model_type": EMBEDDING_MODEL,
            "model_loaded": sentence_model is not None,
            "is_sentence_transformer": isinstance(sentence_model, SentenceTransformer),
            "source": "hugging_face_hub"
        }
        
        if isinstance(sentence_model, SentenceTransformer):
            try:
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
