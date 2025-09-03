import torch
import logging
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class ModelHandler:
    def __init__(self):
        # Use the settings from your main app
        if hasattr(settings, 'AI_MODELS') and hasattr(settings.AI_MODELS, 'CLASSIFICATION_MODEL'):
            self.model_name = settings.AI_MODELS.CLASSIFICATION_MODEL
            self.model_path = settings.AI_MODELS.CLASSIFICATION_MODEL
        else:
            # Fallback paths
            self.model_name = "law-ai/InLegalBERT"
            self.model_path = "app/ai/models/classification"
        
        self.device = -1  # Use CPU
        self.max_length = 512

        # Model components
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.use_hf_api = False
        self.initialized = False

    async def initialize(self):
        """Async initialization of the model (local only)."""
        if self.initialized:
            return
            
        self.use_hf_api = False
        logger.info("Initializing local classification model")
        try:
            self._load_local_model()
            self.initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize classification model: {e}")
            # Don't raise exception, just log it

    def _load_local_model(self):
        """Load the local classification model."""
        try:
            logger.info(f"Loading local model from: {self.model_path}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                local_files_only=True
            )
            self.model = AutoModelForSequenceClassification.from_pretrained(
                str(self.model_path),
                local_files_only=True
            )

            # Keep model on CPU for stability
            self.model.eval()

            self.pipeline = pipeline(
                "text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1,  # CPU
                return_all_scores=True
            )

            logger.info("Local classification model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            self.pipeline = None
            # Don't raise exception, let it fall back to rule-based

    async def classify_text(self, content: str) -> Dict[str, Any]:
        """Classify text using local model - ASYNC VERSION."""
        try:
            if len(content) > 2000:
                content = content[:2000] + "..."
            
            # Ensure model is initialized
            if not self.initialized:
                await self.initialize()

            if self.pipeline is None:
                logger.warning("Model pipeline not available, returning fallback classification")
                return {"document_type": "general", "confidence": 0.0, "model_source": "fallback"}

            # Run the pipeline
            results = self.pipeline(content)

            if not results:
                return {"document_type": "unknown", "confidence": 0.0, "model_source": "local"}

            if isinstance(results, list) and len(results) > 0 and isinstance(results[0], list):
                predictions = results[0]
            elif isinstance(results, list):
                predictions = results
            else:
                logger.error(f"Unexpected results format: {type(results)}")
                return {"document_type": "unknown", "confidence": 0.0, "model_source": "local"}

            valid_predictions = [
                pred for pred in predictions
                if isinstance(pred, dict) and 'label' in pred and 'score' in pred
            ]

            if not valid_predictions:
                return {"document_type": "unknown", "confidence": 0.0, "model_source": "local"}

            best_prediction = max(valid_predictions, key=lambda x: float(x['score']))

            logger.debug("Classification performed using local model")
            return {
                "document_type": self._map_label(best_prediction['label']),
                "confidence": float(best_prediction['score']),
                "raw_predictions": valid_predictions[:3],  # Limit to avoid too much data
                "model_source": "local"
            }

        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {"document_type": "general", "confidence": 0.0, "error": str(e), "model_source": "error"}

    def classify_text_sync(self, content: str) -> Dict[str, Any]:
        """Synchronous version for backward compatibility"""
        try:
            if self.pipeline is None:
                self._load_local_model()
                
            if self.pipeline is None:
                return {"document_type": "general", "confidence": 0.0, "model_source": "fallback"}
                
            if len(content) > 2000:
                content = content[:2000] + "..."
                
            results = self.pipeline(content)
            
            if not results:
                return {"document_type": "unknown", "confidence": 0.0, "model_source": "local"}

            if isinstance(results, list) and len(results) > 0 and isinstance(results[0], list):
                predictions = results[0]
            elif isinstance(results, list):
                predictions = results
            else:
                return {"document_type": "unknown", "confidence": 0.0, "model_source": "local"}

            valid_predictions = [
                pred for pred in predictions
                if isinstance(pred, dict) and 'label' in pred and 'score' in pred
            ]

            if not valid_predictions:
                return {"document_type": "unknown", "confidence": 0.0, "model_source": "local"}

            best_prediction = max(valid_predictions, key=lambda x: float(x['score']))

            return {
                "document_type": self._map_label(best_prediction['label']),
                "confidence": float(best_prediction['score']),
                "model_source": "local"
            }
            
        except Exception as e:
            logger.error(f"Sync classification error: {e}")
            return {"document_type": "general", "confidence": 0.0, "error": str(e), "model_source": "error"}

    def _map_label(self, label: str) -> str:
        """Map model labels to our document types"""
        mapping = {
            "contract": "contract",
            "agreement": "contract",
            "lease": "lease",
            "brief": "legal_brief",
            "policy": "policy",
            "regulation": "regulation",
            "financial": "financial",
            "correspondence": "correspondence",
            "report": "report"
        }
        label_lower = label.lower()
        for key, value in mapping.items():
            if key in label_lower:
                return value
        return "general"

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_path": str(self.model_path),
            "use_hf_api": self.use_hf_api,
            "device": str(self.device),
            "max_length": self.max_length,
            "local_model_loaded": self.model is not None,
            "tokenizer_loaded": self.tokenizer is not None,
            "pipeline_loaded": self.pipeline is not None,
            "initialized": self.initialized,
            "local_only": True
        }

    async def health_check(self) -> Dict[str, Any]:
        try:
            test_text = "This is a test legal contract document for classification purposes."
            result = await self.classify_text(test_text)
            is_healthy = result.get("document_type") != "unknown" and "error" not in result
            return {
                "healthy": is_healthy,
                "use_hf_api": self.use_hf_api,
                "local_model_loaded": self.model is not None,
                "test_result": {
                    "document_type": result.get("document_type"),
                    "confidence": result.get("confidence", 0.0)
                },
                "model_info": self.get_model_info()
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "use_hf_api": self.use_hf_api,
                "local_model_loaded": self.model is not None
            }