import os
import logging
from typing import List

from app.utils.hf_cache import load_pipeline_with_cache
from app.core.runtime import setup_runtime

# Ensure runtime env (cache, threads) is configured
setup_runtime()

logger = logging.getLogger(__name__)

# Prefer env var, then settings (if present), then a sane default
try:
    from core.config import settings  # matches repo layout
except Exception:
    settings = None  # optional fallback

def resolve_model_id() -> str:
    # Allow overriding via env
    env_id = os.getenv("SUMMARIZATION_MODEL")
    if env_id:
        return env_id
    # From settings (could be a repo id string)
    if settings and getattr(settings, "SUMMARIZATION_MODEL", None):
        return str(getattr(settings, "SUMMARIZATION_MODEL"))
    # Default to a smaller model for memory-constrained environments
    return "sshleifer/distilbart-cnn-12-6"  # smaller than bart-large-cnn

FALLBACKS: List[str] = [
    "facebook/bart-large-cnn",
    "philschmid/bart-large-cnn-samsum",
]

class SummarizationService:
    def __init__(self):
        self.model_id = resolve_model_id()
        self.summarizer = None
        logger.info(f"SummarizationService initialized. Model candidate: {self.model_id}")

    def _ensure_loaded(self):
        if self.summarizer is not None:
            return
        self.summarizer, used = load_pipeline_with_cache(
            "summarization",
            self.model_id,
            fallbacks=FALLBACKS,
            device=-1,
        )
        if self.summarizer is None:
            raise RuntimeError("No summarization model available (all candidates failed to load).")
        if used and used != self.model_id:
            logger.warning(f"SummarizationService fell back to {used}")

    def _chunk_text(self, text: str, max_tokens: int = 900) -> list:
        # Rough token proxy = words; safe for CPU summarization
        words = text.split()
        chunks, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= max_tokens:
                chunks.append(" ".join(cur))
                cur = []
        if cur:
            chunks.append(" ".join(cur))
        return chunks

    def summarize_text(self, text: str, max_length: int = 130, min_length: int = 30) -> str:
        if not text or not text.strip():
            return "No content to summarize."
        self._ensure_loaded()

        words = text.split()
        if len(words) < min_length:
            return text

        # For long text, chunk to respect memory constraints
        if len(words) > 900:
            pieces = self._chunk_text(text, 900)
            partials: List[str] = []
            for i, piece in enumerate(pieces, 1):
                try:
                    out = self.summarizer(
                        piece,
                        max_length=min(max_length, max(56, len(piece.split()) // 2)),
                        min_length=min(min_length, max(24, len(piece.split()) // 4)),
                        do_sample=False,
                        truncation=True,
                    )[0]["summary_text"]
                    partials.append(out)
                except Exception as e:
                    logger.warning(f"Chunk {i} summarization failed: {e}")
            if not partials:
                return "Error: Could not summarize the text."
            combined = " ".join(partials)
            if len(combined.split()) > max_length:
                # Summarize the summaries
                final = self.summarizer(
                    combined,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False,
                    truncation=True,
                )[0]["summary_text"]
                return final
            return combined

        # Short text single pass
        result = self.summarizer(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False,
            truncation=True,
        )
        return result[0]["summary_text"]

    def get_model_info(self) -> dict:
        return {
            "model_id": self.model_id,
            "loaded": self.summarizer is not None,
            "task": "summarization",
            "cache_dir": os.getenv("TRANSFORMERS_CACHE"),
        }

# Backward compatible helpers
def summarize_text(text: str, max_length: int = 130, min_length: int = 30) -> str:
    service = SummarizationService()
    return service.summarize_text(text, max_length, min_length)

def get_model_info() -> dict:
    service = SummarizationService()
    return service.get_model_info()

summarization_service = SummarizationService()
