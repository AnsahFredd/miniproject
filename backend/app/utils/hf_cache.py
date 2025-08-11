import os
import shutil
import logging
from pathlib import Path
from typing import Optional, List
import tempfile
from huggingface_hub import snapshot_download, login
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = logging.getLogger(__name__)

class HuggingFaceCacheManager:
    """Manages Hugging Face model cache and handles stale commit issues."""
    
    def __init__(self):
        self.cache_dir = Path(settings.HUGGINGFACE_CACHE_DIR)
        self.hf_token = settings.HUGGINGFACE_API_KEY
        
        # Authenticate with Hugging Face if token is provided
        if self.hf_token:
            try:
                login(token=self.hf_token, add_to_git_credential=True)
                logger.info("Authenticated to Hugging Face Hub with provided token")
            except Exception as e:
                logger.warning(f"Failed to authenticate with HF Hub: {e}")
    
    def clear_model_cache(self, model_name: str) -> bool:
        """Clear cache for a specific model."""
        try:
            # Clear transformers cache
            transformers_cache = Path.home() / ".cache" / "huggingface" / "transformers"
            if transformers_cache.exists():
                for item in transformers_cache.iterdir():
                    if model_name.replace("/", "--") in item.name:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                        logger.info(f"Cleared transformers cache for {model_name}: {item}")
            
            # Clear hub cache
            hub_cache = Path.home() / ".cache" / "huggingface" / "hub"
            if hub_cache.exists():
                for item in hub_cache.iterdir():
                    if model_name.replace("/", "--") in item.name:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                        logger.info(f"Cleared hub cache for {model_name}: {item}")
            
            # Clear local cache directory
            if self.cache_dir.exists():
                for item in self.cache_dir.iterdir():
                    if model_name.replace("/", "--") in item.name:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                        logger.info(f"Cleared local cache for {model_name}: {item}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache for {model_name}: {e}")
            return False
    
    def clear_all_cache(self) -> bool:
        """Clear all Hugging Face caches."""
        try:
            cache_dirs = [
                Path.home() / ".cache" / "huggingface",
                self.cache_dir
            ]
            
            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    logger.info(f"Cleared cache directory: {cache_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear all caches: {e}")
            return False
    
    def prewarm_model_snapshot(self, model_name: str, revision: str = "main") -> bool:
        """Pre-download model snapshot to avoid commit hash issues."""
        try:
            logger.info(f"Pre-warming snapshot for {model_name} at revision {revision}")
            
            snapshot_path = snapshot_download(
                repo_id=model_name,
                revision=revision,
                cache_dir=str(self.cache_dir),
                force_download=True,  # Force fresh download
                resume_download=False,  # Don't resume partial downloads
                token=self.hf_token
            )
            
            logger.info(f"Successfully pre-warmed {model_name} to {snapshot_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pre-warm snapshot for {model_name}: {e}")
            return False
    
    def load_model_with_retry(self, model_name: str, model_type: str = "summarization", max_retries: int = 2):
        """Load model with automatic cache clearing and retry on commit hash errors."""
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Loading {model_type} model {model_name} (attempt {attempt + 1}/{max_retries})")
                
                if model_type == "summarization":
                    pipeline_obj = pipeline(
                        "summarization",
                        model=model_name,
                        tokenizer=model_name,
                        cache_dir=str(self.cache_dir)
                    )
                    return pipeline_obj
                    
                elif model_type == "embedding":
                    model = SentenceTransformer(model_name, cache_folder=str(self.cache_dir))
                    return model
                    
                elif model_type == "classification":
                    pipeline_obj = pipeline(
                        "text-classification",
                        model=model_name,
                        tokenizer=model_name,
                        cache_dir=str(self.cache_dir)
                    )
                    return pipeline_obj
                    
                else:
                    raise ValueError(f"Unsupported model type: {model_type}")
                    
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if it's a commit hash error
                if "404" in error_msg and ("resolve" in error_msg or "commit" in error_msg):
                    logger.warning(f"Detected stale commit hash error for {model_name}: {e}")
                    
                    if attempt < max_retries - 1:
                        logger.info(f"Clearing cache and retrying for {model_name}")
                        self.clear_model_cache(model_name)
                        
                        # Try to pre-warm with latest revision
                        self.prewarm_model_snapshot(model_name, "main")
                        continue
                    else:
                        logger.error(f"Failed to load {model_name} after {max_retries} attempts")
                        raise
                else:
                    # Different error, don't retry
                    logger.error(f"Non-cache error loading {model_name}: {e}")
                    raise
        
        return None

# Global cache manager instance
cache_manager = HuggingFaceCacheManager()

def clear_model_cache(model_name: str) -> bool:
    """Convenience function to clear cache for a specific model."""
    return cache_manager.clear_model_cache(model_name)

def clear_all_cache() -> bool:
    """Convenience function to clear all caches."""
    return cache_manager.clear_all_cache()

def load_model_safe(model_name: str, model_type: str = "summarization"):
    """Safely load a model with automatic cache management."""
    return cache_manager.load_model_with_retry(model_name, model_type)
