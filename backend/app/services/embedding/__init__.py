from typing import List

import numpy as np
from .service import LocalEmbeddingService

embedding_service = LocalEmbeddingService()

async def generate_embedding(text: str) -> np.ndarray:
    embedding_result = await embedding_service.generate_embedding(text)

    # Convert to numpy array if it's a list
    if isinstance(embedding_result, list):
        return np.array(embedding_result)
    elif isinstance(embedding_result, np.ndarray):
        return embedding_result
    else:
        raise ValueError(f"Invalid embedding type returned: {type(embedding_result)}")

def generate_embedding_batch(texts: List[str]):
    return embedding_service.generate_embedding_batch(texts)



async def generate_and_store_embeddings(user_id: str):
    return await embedding_service.generate_and_store_embeddings(user_id)

def get_model_info() -> dict:
    return embedding_service.get_model_info()

def health_check() -> dict:
    return embedding_service.health_check()

