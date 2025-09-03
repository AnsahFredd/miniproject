import re
from typing import List

def chunk_text(text: str, max_tokens: int = 400) -> List[str]:
    """
    Split long text into manageable chunks based on sentence length.
    """
    if not text or not text.strip():
        return []
    
    text = text.strip()
    sentences = re.split(r'(?<=[.!?])\s+', text.replace('\n', ' '))
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
        estimated_tokens = len(potential_chunk) // 4
        
        if estimated_tokens < max_tokens:
            current_chunk = potential_chunk
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    if not chunks and text:
        words = text.split()
        words_per_chunk = max_tokens
        
        for i in range(0, len(words), words_per_chunk):
            chunk_words = words[i:i + words_per_chunk]
            chunk = " ".join(chunk_words)
            if chunk.strip():
                chunks.append(chunk.strip())
    
    return chunks


def validate_embedding(embedding: List[float], expected_dim: int) -> bool:
    if not embedding:
        return False
    if len(embedding) != expected_dim:
        return False
    if all(x == 0 for x in embedding):
        return False
    return True
