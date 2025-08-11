import threading
import logging
from typing import Optional, Dict, Any, Callable
from functools import wraps
from app.utils.hf_cache import cache_manager

logger = logging.getLogger(__name__)

class LazyModelLoader:
    """Thread-safe lazy model loader for AI services."""
    
    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._loading_locks: Dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()
    
    def get_or_load_model(self, 
                         model_key: str, 
                         model_name: str, 
                         model_type: str, 
                         fallback_models: Optional[list] = None) -> Optional[Any]:
        """
        Thread-safe lazy loading of models.
        
        Args:
            model_key: Unique key for caching (e.g., 'summarization_primary')
            model_name: Hugging Face model name
            model_type: Type of model (summarization, embedding, classification, etc.)
            fallback_models: List of fallback model names to try if primary fails
            
        Returns:
            Loaded model or None if all attempts fail
        """
        # Check if model is already loaded
        if model_key in self._models:
            return self._models[model_key]
        
        # Get or create lock for this model
        with self._global_lock:
            if model_key not in self._loading_locks:
                self._loading_locks[model_key] = threading.Lock()
            model_lock = self._loading_locks[model_key]
        
        # Load model with thread safety
        with model_lock:
            # Double-check pattern - model might have been loaded while waiting for lock
            if model_key in self._models:
                return self._models[model_key]
            
            logger.info(f"🔄 Lazy loading {model_type} model: {model_name}")
            
            # Try primary model
            model = self._load_single_model(model_name, model_type)
            if model is not None:
                self._models[model_key] = model
                logger.info(f"✅ Successfully loaded {model_type} model: {model_name}")
                return model
            
            # Try fallback models if provided
            if fallback_models:
                for fallback_name in fallback_models:
                    logger.warning(f"🔄 Trying fallback {model_type} model: {fallback_name}")
                    model = self._load_single_model(fallback_name, model_type)
                    if model is not None:
                        self._models[model_key] = model
                        logger.info(f"✅ Successfully loaded fallback {model_type} model: {fallback_name}")
                        return model
            
            # All attempts failed
            logger.error(f"❌ Failed to load any {model_type} model for key: {model_key}")
            self._models[model_key] = None  # Cache the failure to avoid repeated attempts
            return None
    
    def _load_single_model(self, model_name: str, model_type: str) -> Optional[Any]:
        """Load a single model using the cache manager."""
        try:
            return cache_manager.load_model_with_retry(model_name, model_type)
        except Exception as e:
            logger.error(f"Failed to load {model_type} model {model_name}: {e}")
            return None
    
    def is_model_loaded(self, model_key: str) -> bool:
        """Check if a model is loaded without triggering loading."""
        return model_key in self._models and self._models[model_key] is not None
    
    def get_loaded_models(self) -> Dict[str, bool]:
        """Get status of all models."""
        return {key: (model is not None) for key, model in self._models.items()}
    
    def clear_model(self, model_key: str) -> bool:
        """Clear a specific model from memory."""
        with self._global_lock:
            if model_key in self._models:
                del self._models[model_key]
                logger.info(f"Cleared model from memory: {model_key}")
                return True
            return False
    
    def clear_all_models(self):
        """Clear all models from memory."""
        with self._global_lock:
            self._models.clear()
            logger.info("Cleared all models from memory")

# Global lazy loader instance
lazy_loader = LazyModelLoader()

def require_model(model_key: str, model_name: str, model_type: str, fallback_models: Optional[list] = None):
    """
    Decorator to ensure a model is loaded before executing a method.
    
    Usage:
        @require_model('summarization_primary', 'facebook/bart-large-cnn', 'summarization')
        def summarize_text(self, text: str):
            # self.model will be available here
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Load model if not already loaded
            model = lazy_loader.get_or_load_model(model_key, model_name, model_type, fallback_models)
            if model is None:
                raise RuntimeError(f"Failed to load required model: {model_key}")
            
            # Set model on the service instance for use in the method
            setattr(self, '_current_model', model)
            
            try:
                return func(self, *args, **kwargs)
            finally:
                # Clean up the temporary model reference
                if hasattr(self, '_current_model'):
                    delattr(self, '_current_model')
        
        return wrapper
    return decorator
