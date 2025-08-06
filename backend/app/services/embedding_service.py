from pathlib import Path
from datetime import datetime
from typing import List
import numpy as np

from sentence_transformers import SentenceTransformer
from app.models.document import AcceptedDocument

# === Load Sentence Transformer Model ===
MODEL_DIR = Path(__file__).resolve().parent.parent / "ai/models/InLegalBERT"
MODEL_DIR = MODEL_DIR.as_posix()

if not Path(MODEL_DIR).exists():
    raise FileNotFoundError(f"Embedding model not found at {MODEL_DIR}")

sentence_model = SentenceTransformer(MODEL_DIR)

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
    return sentence_model.encode(text).tolist()

# === Public: Generate and Store Embeddings for User's Documents ===
async def generate_and_store_embeddings(user_id: str):
    """
    Generate and store embeddings for all accepted documents for a given user.
    - Splits document into chunks
    - Stores `chunks`, `embedding_chunks`, and `embedding_generated_at`
    """
    documents = await AcceptedDocument.find({"user_id": user_id}).to_list()
    updated = 0
    skipped = 0

    if not documents:
        return {"message": "No documents found for user."}

    for doc in documents:
        if not doc.content:
            skipped += 1
            continue

        chunks = chunk_text(doc.content)
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

    return {
        "message": f"Processed {updated} documents. Skipped {skipped} (no content)."
    }