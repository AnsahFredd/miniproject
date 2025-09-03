import torch
import logging
import asyncio
import os
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from typing import Dict, Any, List
from app.core.config import settings

model = settings.AI_MODELS.SUMMARIZATION_MODEL

logger = logging.getLogger(__name__)

# Configuration Constants
DEVICE = os.getenv("DEVICE", "cpu")
MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "1024"))
MAX_OUTPUT_LENGTH = int(os.getenv("MAX_OUTPUT_LENGTH", "512"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))

# Generation Parameters
DEFAULT_GENERATION_PARAMS = {
    "max_length": 130,
    "min_length": 30,
    "do_sample": False,
    "num_beams": 4,
    "length_penalty": 2.0,
    "early_stopping": True,
    "no_repeat_ngram_size": 3
}

ADVANCED_GENERATION_PARAMS = {
    "temperature": 1.0,
    "top_p": 1.0,
    "top_k": 50,
    "repetition_penalty": 1.0
}


class TextProcessor:
    """Text processing utilities for summarization."""
    
    def __init__(self, model_handler):
        self.model_handler = model_handler

    def chunk_text(self, text: str, max_length: int = 900) -> List[str]:
        """Split text into manageable chunks."""
        tokens = self.model_handler.get_token_count(text)
        
        if tokens <= max_length:
            return [text]
        
        # Split by sentences for better coherence
        sentences = text.split('. ')
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self.model_handler.get_token_count(sentence)
            
            if current_tokens + sentence_tokens > max_length and current_chunk:
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')
        
        return chunks

    def preprocess_text(self, text: str) -> str:
        """Clean and prepare text for summarization."""
        if not text:
            return ""
        
        # Basic cleaning
        text = text.strip()
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        return text

    def validate_text(self, text: str, min_length: int = 30) -> bool:
        """Validate if text is suitable for summarization."""
        if not text or not text.strip():
            return False
        
        word_count = len(text.split())
        return word_count >= min_length


class ModelHandler:
    """Handles the local summarization model operations."""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.device = DEVICE
        self.max_input_length = MAX_INPUT_LENGTH

        # Model components
        self.tokenizer = None
        self.model = None
        self.pipeline = None

        logger.info(f"ModelHandler created - Local model path: {self.model_path}")

    async def initialize(self):
        """Initialize the local model."""
        try:
            logger.info(f"Starting model initialization from: {self.model_path}")

            if not self.model_path.exists():
                raise FileNotFoundError(f"Model directory not found: {self.model_path}")
            
            # List available files for debugging
            available_files = [f.name for f in self.model_path.iterdir() if f.is_file()]
            logger.info(f"Available files in model directory: {available_files}")

            self._load_local_model()
            logger.info("✅ Model initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize model: {e}")
            logger.error(f"Model path: {self.model_path}")
            logger.error(f"Path exists: {self.model_path.exists()}")
            raise

    def _load_local_model(self):
        """Load the local summarization model."""
        try:
            torch.set_num_threads(1)
            os.environ["CUDA_VISIBLE_DEVICES"]


            logger.info(f"Loading local model from: {self.model_path}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                local_files_only=True
            )
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                str(self.model_path),
                local_files_only=True,
                torch_dtype=torch.float32,
                device_map=None
            )

            self.device = "cpu"
            self.model.to(self.device)
            self.model.eval()

            # Create pipeline
            self.pipeline = pipeline(
                "summarization",
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1 
            )
            
            logger.info(f"Local model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            raise RuntimeError(f"Local model initialization failed: {e}")

    def generate_summary(self, text: str, **kwargs) -> str:
        """Generate summary using local model."""
        try:
            if not self.pipeline:
                raise RuntimeError("Model pipeline not initialized. Call initialize() first.")

            # Merge with default parameters
            generation_params = {**DEFAULT_GENERATION_PARAMS, **kwargs}

            # Validate input length
            input_tokens = self.get_token_count(text)
            if input_tokens > self.max_input_length:
                logger.warning(f"Input text too long ({input_tokens} tokens), truncating to {self.max_input_length-50}")
                tokens = self.tokenizer.encode(text, max_length=self.max_input_length-50, truncation=True)
                text = self.tokenizer.decode(tokens, skip_special_tokens=True)
                logger.info(f"Text truncated to {len(text)} characters")
            
            result = self.pipeline(text, **generation_params)
            
            if isinstance(result, list) and len(result) > 0:
                summary = result[0]['summary_text'].strip()
                logger.debug("Summary generated successfully")
                return summary
            
            return "Error: Could not generate summary"
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return f"Error generating summary: {str(e)}"

    def get_token_count(self, text: str) -> int:
        """Get token count for text."""
        if self.tokenizer:
            try:
                tokens = self.tokenizer.encode(text, add_special_tokens=True)
                return len(tokens)
            except Exception as e:
                logger.warning(f"Token counting failed: {e}")
                return int(len(text.split()) * 1.3)  # Fallback estimate
        return int(len(text.split()) * 1.3)  # Rough estimate

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "model_path": str(self.model_path),
            "device": str(self.device),
            "max_input_length": self.max_input_length,
            "local_model_loaded": self.model is not None,
            "tokenizer_loaded": self.tokenizer is not None,
            "pipeline_loaded": self.pipeline is not None,
            "model_exists": self.model_path.exists(),
            "config_exists": (self.model_path / "config.json").exists(),
            "local_only": True
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the model."""
        try:
            test_text = "This is a test document for checking summarization service functionality. It contains multiple sentences to ensure the model can process and summarize content properly."
            result = self.generate_summary(test_text, max_length=50)
            is_healthy = result and not result.startswith("Error")
            
            return {
                "healthy": is_healthy,
                "local_model_loaded": self.model is not None,
                "test_result": result[:100] + "..." if len(result) > 100 else result,
                "model_info": self.get_model_info()
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "local_model_loaded": self.model is not None,
                "model_info": self.get_model_info()
            }


class LocalSummarizationService:
    """Complete local summarization service."""
    
    def __init__(self, model_path: str):
        """Initialize the summarization service."""
        self.model_handler = None
        self.text_processor = None
        self.model_path = model_path
        self._initialized = False
        
        logger.info("LocalSummarizationService created")

    async def initialize(self):
        """Initialize the service with local models."""
        try:
            # Initialize model handler
            self.model_handler = ModelHandler(self.model_path)
            await self.model_handler.initialize()
            
            # Initialize text processor
            self.text_processor = TextProcessor(self.model_handler)
            
            self._initialized = True
            logger.info("✅ Summarization service fully initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize summarization service: {e}")
            raise RuntimeError(f"Service initialization failed: {e}")

    def _ensure_initialized(self):
        """Ensure the service is initialized before use."""
        if not self._initialized:
            raise RuntimeError("Summarization service not initialized. Call initialize() first.")

    async def summarize_text(self, text: str, max_length: int = 130, min_length: int = 30) -> str:
        """Basic text summarization."""
        self._ensure_initialized()
        
        if not text or not text.strip():
            return "No content to summarize."

        # Validate and preprocess text
        if not self.text_processor.validate_text(text, min_length=10):
            return "Text too short to summarize."

        text = self.text_processor.preprocess_text(text)
        token_count = self.model_handler.get_token_count(text)
        
        # Handle long texts with chunking
        if token_count > self.model_handler.max_input_length:
            return await self._summarize_long_text(text, max_length, min_length)
        
        # Generate summary
        try:
            summary = self.model_handler.generate_summary(
                text, 
                max_length=max_length, 
                min_length=min_length
            )
            return summary
            
        except Exception as e:
            logger.error(f"Failed to summarize text: {e}")
            return f"Error: Failed to generate summary - {str(e)}"

    async def _summarize_long_text(self, text: str, max_length: int, min_length: int) -> str:
        """Handle long text by chunking."""
        chunks = self.text_processor.chunk_text(text)
        summaries = []

        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            
            # Adjust parameters for chunks
            chunk_max = min(max_length, max(50, len(chunk.split()) // 3))
            chunk_min = min(min_length, max(10, len(chunk.split()) // 8))
            
            try:
                chunk_summary = self.model_handler.generate_summary(
                    chunk, 
                    max_length=chunk_max, 
                    min_length=chunk_min
                )
                
                if not chunk_summary.startswith("Error"):
                    summaries.append(chunk_summary)
                else:
                    logger.warning(f"Failed to summarize chunk {i+1}: {chunk_summary}")
                    
            except Exception as e:
                logger.warning(f"Error processing chunk {i+1}: {e}")
                continue

        if not summaries:
            return "Error: Could not generate summary from any text chunk"

        combined_summary = " ".join(summaries)
        
        # If combined summary is still too long, summarize it again
        if len(combined_summary.split()) > max_length * 2:
            try:
                final_summary = self.model_handler.generate_summary(
                    combined_summary, 
                    max_length=max_length, 
                    min_length=min_length
                )
                return final_summary
            except Exception as e:
                logger.warning(f"Failed to create final summary: {e}")
                return combined_summary

        return combined_summary

    async def summarize_advanced(self, text: str, **kwargs) -> str:
        """Advanced summarization with custom parameters."""
        self._ensure_initialized()
        
        if not text or not text.strip():
            return "No content to summarize."

        text = self.text_processor.preprocess_text(text)
        token_count = self.model_handler.get_token_count(text)
        
        # Merge advanced parameters
        generation_params = {**ADVANCED_GENERATION_PARAMS, **kwargs}
        
        # Handle long texts
        if token_count > self.model_handler.max_input_length:
            return await self._summarize_long_text_advanced(text, **generation_params)
        
        try:
            return self.model_handler.generate_summary(text, **generation_params)
        except Exception as e:
            logger.error(f"Advanced summarization failed: {e}")
            return f"Error: Advanced summarization failed - {str(e)}"

    async def _summarize_long_text_advanced(self, text: str, **kwargs) -> str:
        """Handle long text with advanced parameters."""
        chunks = self.text_processor.chunk_text(text)
        summaries = []

        max_length = kwargs.get('max_length', 130)
        min_length = kwargs.get('min_length', 30)

        for i, chunk in enumerate(chunks):
            logger.info(f"Processing advanced chunk {i+1}/{len(chunks)}")
            
            chunk_max = min(max_length, len(chunk.split()) // 2)
            chunk_min = min(min_length, max(10, len(chunk.split()) // 8))
            
            chunk_params = kwargs.copy()
            chunk_params.update({"max_length": chunk_max, "min_length": chunk_min})
            
            try:
                chunk_summary = self.model_handler.generate_summary(chunk, **chunk_params)
                if not chunk_summary.startswith("Error"):
                    summaries.append(chunk_summary)
            except Exception as e:
                logger.warning(f"Error in advanced processing of chunk {i+1}: {e}")
                continue

        if not summaries:
            return "Error: Could not generate summary from any chunk"

        return " ".join(summaries)

    async def get_key_points(self, text: str, num_points: int = 5) -> List[str]:
        """Extract key points from text."""
        self._ensure_initialized()
        
        try:
            summary = await self.summarize_text(text, max_length=200, min_length=50)
            
            if summary.startswith("Error"):
                return [summary]
            
            # Split into sentences and return top N
            sentences = [s.strip() + '.' for s in summary.split('.') if s.strip()]
            return sentences[:num_points]
            
        except Exception as e:
            logger.error(f"Key points extraction failed: {e}")
            return [f"Error extracting key points: {str(e)}"]

    async def batch_summarize(self, texts: List[str], max_length: int = 130, min_length: int = 30) -> List[str]:
        """Summarize multiple texts."""
        self._ensure_initialized()
        
        summaries = []
        
        for i, text in enumerate(texts):
            logger.info(f"Processing text {i+1}/{len(texts)}")
            try:
                summary = await self.summarize_text(text, max_length=max_length, min_length=min_length)
                summaries.append(summary)
            except Exception as e:
                logger.error(f"Failed to summarize text {i+1}: {e}")
                summaries.append(f"Error: Failed to summarize text {i+1}")
        
        return summaries

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        try:
            if not self._initialized:
                return {
                    "healthy": False,
                    "error": "Service not initialized",
                    "initialized": False
                }

            # Test model handler health
            model_health = self.model_handler.health_check()
            
            # Test with a simple summarization
            test_text = "This is a comprehensive test document for the summarization service. It contains multiple sentences to verify that the local model can process and generate appropriate summaries. The service should be able to handle this text without any issues."
            
            test_result = await self.summarize_text(test_text, max_length=50)
            test_passed = test_result and not test_result.startswith("Error")
            
            return {
                "healthy": model_health.get("healthy", False) and test_passed,
                "initialized": self._initialized,
                "model_health": model_health,
                "test_passed": test_passed,
                "test_result": test_result[:100] + "..." if len(test_result) > 100 else test_result
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "initialized": self._initialized
            }

    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information."""
        if not self._initialized:
            return {"error": "Service not initialized"}
        
        info = self.model_handler.get_model_info()
        info.update({
            "service_initialized": self._initialized,
            "local_only": True,
            "uses_external_api": False
        })
        
        return info


# Global service instance and management
_service_instance: LocalSummarizationService = None
_initialization_lock = asyncio.Lock()
_initialized = False


async def get_service() -> LocalSummarizationService:
    """Get the initialized summarization service instance."""
    global _service_instance, _initialized
    
    if not _initialized:
        async with _initialization_lock:
            if not _initialized:  # Double-check pattern
                try:
                    logger.info(f"🚀 Initializing summarization service with model at: {model}")
                    _service_instance = LocalSummarizationService(model)
                    await _service_instance.initialize()
                    _initialized = True
                    logger.info("✅ Global summarization service initialized successfully")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize summarization service: {e}")
                    raise RuntimeError(f"Summarization service initialization failed: {e}")
    
    return _service_instance


# Convenience functions for easy usage
async def summarize_text(text: str, max_length: int = 130, min_length: int = 30) -> str:
    """Summarize text using the service."""
    service = await get_service()
    return await service.summarize_text(text, max_length, min_length)


async def summarize_advanced(text: str, **kwargs) -> str:
    """Advanced text summarization."""
    service = await get_service()
    return await service.summarize_advanced(text, **kwargs)


async def get_key_points(text: str, num_points: int = 5) -> List[str]:
    """Extract key points from text."""
    service = await get_service()
    return await service.get_key_points(text, num_points)


async def batch_summarize(texts: List[str], max_length: int = 130, min_length: int = 30) -> List[str]:
    """Batch summarize multiple texts."""
    service = await get_service()
    return await service.batch_summarize(texts, max_length, min_length)


async def health_check() -> Dict[str, Any]:
    """Perform health check on the service."""
    try:
        service = await get_service()
        return await service.health_check()
    except Exception as e:
        return {"healthy": False, "error": str(e), "initialized": False}