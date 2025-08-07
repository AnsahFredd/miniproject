import numpy as np
from typing import List

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    a = np.array(vec1)
    b = np.array(vec2)

    # Ensure both vectors have the same dimensionality
    if a.shape != b.shape:
        raise ValueError(f"Embedding dimension mismatch: {a.shape} != {b.shape}")

    # Avoid division by zero
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0

    similarity = np.dot(a, b) / (norm_a * norm_b)
    return float(similarity)


