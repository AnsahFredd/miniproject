import os
import logging
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List

from sentence_transformers import SentenceTransformer
import torch
from app.models.document import AcceptedDocument
from app.utils.model_loader import load_embedding_model_smart

logger = logging.getLogger(__name__)

# === Base Path for Embedding Model ===
MODEL_DIR = Path(__file__).resolve().parent.parent / "ai/models/InLegalBERT"
MODEL_DIR = MODEL_DIR.as_posix()

# === Load Embedding Model Using Smart Loader ===
sentence_model = None

try:
    sentence_model = load_embedding_model_smart(MODEL_DIR, "law-ai/InLegalBERT")
    logger.info("✅ Embedding model loaded successfully")
    
    # Handle case where smart loader returns tuple (model, tokenizer)
    if isinstance(sentence_model, tuple):
        logger.warning("⚠️ Loaded as regular transformers model, not SentenceTransformer")
        # This means it fell back to regular transformers
        # For consistency, try to load as SentenceTransformer directly
        try:
            sentence_model = SentenceTransformer("law-ai/InLegalBERT")
            logger.info("✅ Successfully converted to SentenceTransformer")
        except Exception as convert_error:
            logger.error(f"❌ Could not convert to SentenceTransformer: {convert_error}")
            # Keep the tuple for now, we'll handle it in the functions
            raw_model, raw_tokenizer = sentence_model
            logger.warning("⚠️ Using raw transformers model - some functionality may be limited")
        
except Exception as e:
    logger.error(f"❌ Failed to load embedding model: {e}")
    # Fallback to direct HuggingFace loading
    try:
        logger.info("🔄 Attempting fallback to direct HuggingFace loading...")
        sentence_model = SentenceTransformer("law-ai/InLegalBERT")
        logger.info("✅ Fallback embedding model loaded successfully")
    except Exception as fallback_error:
        logger.error(f"❌ Complete failure to load embedding model: {fallback_error}")
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
        
        # Handle both SentenceTransformer and tuple cases
        if isinstance(sentence_model, tuple):
            # This is the fallback case where we have raw transformers
            logger.warning("Using raw transformers for embedding - this may not be optimal")
            model, tokenizer = sentence_model
            
            # Simple mean pooling implementation
            inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
            with torch.no_grad():
                outputs = model(**inputs)
                # Mean pooling
                embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            
            embedding = embeddings.tolist()
        else:
            # Standard SentenceTransformer case
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
                
                # Generate embeddings for chunks
                if isinstance(sentence_model, tuple):
                    # Handle raw transformers case
                    model, tokenizer = sentence_model
                    embeddings = []
                    
                    for chunk in chunks:
                        inputs = tokenizer(chunk, return_tensors="pt", truncation=True, padding=True, max_length=512)
                        with torch.no_grad():
                            outputs = model(**inputs)
                            chunk_embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy().tolist()
                        embeddings.append(chunk_embedding)
                else:
                    # Standard SentenceTransformer case
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
        is_sentence_transformer = isinstance(sentence_model, SentenceTransformer)
        is_tuple = isinstance(sentence_model, tuple)
        
        model_info = {
            "model_type": "law-ai/InLegalBERT",
            "local_path": MODEL_DIR,
            "model_loaded": sentence_model is not None,
            "is_sentence_transformer": is_sentence_transformer,
            "is_raw_transformers": is_tuple,
        }
        
        if is_sentence_transformer:
            try:
                test_embedding = sentence_model.encode("test")
                model_info["embedding_dimension"] = len(test_embedding)
            except Exception as e:
                model_info["embedding_dimension_error"] = str(e)
        elif is_tuple:
            model_info["embedding_dimension"] = "unknown (raw transformers)"
        
        return model_info
        
    except Exception as e:
        return {
            "error": str(e),
            "model_loaded": False
        }