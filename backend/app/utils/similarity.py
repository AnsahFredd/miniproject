import numpy as np
from typing import Union, List
import logging

logger = logging.getLogger(__name__)

def cosine_similarity(vec1: Union[List[float], np.ndarray], vec2: Union[List[float], np.ndarray]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector (list or numpy array)
        vec2: Second vector (list or numpy array)
        
    Returns:
        float: Cosine similarity score between -1 and 1
        
    Raises:
        ValueError: If vectors have different dimensions or are scalars
    """
    # Convert to numpy arrays if needed
    if isinstance(vec1, list):
        a = np.array(vec1)
    elif isinstance(vec1, np.ndarray):
        a = vec1
    else:
        raise ValueError(f"Invalid type for vec1: {type(vec1)}")
    
    if isinstance(vec2, list):
        b = np.array(vec2)
    elif isinstance(vec2, np.ndarray):
        b = vec2
    else:
        raise ValueError(f"Invalid type for vec2: {type(vec2)}")
    
    # Check for scalar inputs (this was your main issue)
    if a.shape == () or b.shape == ():
        logger.error(f"Scalar embedding detected - vec1.shape: {a.shape}, vec2.shape: {b.shape}")
        raise ValueError(f"Embedding dimension mismatch: {a.shape} != {b.shape}")
    
    # Ensure both vectors have the same dimensionality
    if a.shape != b.shape:
        logger.error(f"Shape mismatch - vec1.shape: {a.shape}, vec2.shape: {b.shape}")
        raise ValueError(f"Embedding dimension mismatch: {a.shape} != {b.shape}")

    # Calculate norms
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    # Avoid division by zero
    if norm_a == 0 or norm_b == 0:
        logger.warning("Zero vector detected in similarity calculation")
        return 0.0

    # Calculate cosine similarity
    similarity = np.dot(a, b) / (norm_a * norm_b)
    
    # Ensure result is within valid range [-1, 1] (handles floating point errors)
    similarity = np.clip(similarity, -1.0, 1.0)
    
    return float(similarity)


# Alternative: More explicit version with better error messages
def cosine_similarity_verbose(vec1: Union[List[float], np.ndarray], vec2: Union[List[float], np.ndarray]) -> float:
    """
    Calculate cosine similarity with verbose error reporting for debugging.
    """
    try:
        # Convert inputs
        if isinstance(vec1, list):
            a = np.array(vec1)
            logger.debug(f"Converted vec1 from list to array: shape {a.shape}")
        elif isinstance(vec1, np.ndarray):
            a = vec1
            logger.debug(f"Vec1 is already numpy array: shape {a.shape}")
        else:
            raise ValueError(f"vec1 must be list or numpy array, got {type(vec1)}")
        
        if isinstance(vec2, list):
            b = np.array(vec2)
            logger.debug(f"Converted vec2 from list to array: shape {b.shape}")
        elif isinstance(vec2, np.ndarray):
            b = vec2
            logger.debug(f"Vec2 is already numpy array: shape {b.shape}")
        else:
            raise ValueError(f"vec2 must be list or numpy array, got {type(vec2)}")
        
        # Detailed shape validation
        if a.shape == ():
            logger.error("vec1 is a scalar (empty shape)")
            raise ValueError("vec1 cannot be a scalar - must be a vector")
        
        if b.shape == ():
            logger.error("vec2 is a scalar (empty shape)")
            raise ValueError("vec2 cannot be a scalar - must be a vector")
        
        if len(a.shape) != 1:
            logger.error(f"vec1 has {len(a.shape)} dimensions, expected 1")
            raise ValueError(f"vec1 must be 1-dimensional, got shape {a.shape}")
        
        if len(b.shape) != 1:
            logger.error(f"vec2 has {len(b.shape)} dimensions, expected 1")
            raise ValueError(f"vec2 must be 1-dimensional, got shape {b.shape}")
        
        if a.shape != b.shape:
            logger.error(f"Dimension mismatch: {a.shape} vs {b.shape}")
            raise ValueError(f"Vector dimensions must match: {a.shape} != {b.shape}")
        
        # Calculate similarity
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0:
            logger.warning("vec1 is a zero vector")
            return 0.0
        
        if norm_b == 0:
            logger.warning("vec2 is a zero vector")
            return 0.0
        
        similarity = np.dot(a, b) / (norm_a * norm_b)
        similarity = np.clip(similarity, -1.0, 1.0)
        
        logger.debug(f"Calculated similarity: {similarity}")
        return float(similarity)
        
    except Exception as e:
        logger.error(f"Cosine similarity calculation failed: {e}")
        logger.error(f"vec1 type: {type(vec1)}, shape: {getattr(vec1, 'shape', 'no shape')}")
        logger.error(f"vec2 type: {type(vec2)}, shape: {getattr(vec2, 'shape', 'no shape')}")
        raise