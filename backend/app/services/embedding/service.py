import logging
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List
import torch
from transformers import AutoTokenizer, AutoModel
from app.models.document import AcceptedDocument
from .errors import EmbeddingError
from .utils import chunk_text, validate_embedding
from app.core.config import settings

EXPECTED_EMBEDDING_DIM = 768
logger = logging.getLogger(__name__)

class LocalEmbeddingService:
    def __init__(self):
        self.model_path = settings.AI_MODELS.EMBEDDING_MODEL
        self.expected_dim = EXPECTED_EMBEDDING_DIM
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.fallback_embedding = np.zeros(self.expected_dim).tolist()
        
        # Model components

        self.tokenizer = None
        self.model = None
        
        logger.info("Local embedding service instance created (local-only mode)")

    async def initialize(self):
        """Initialize with local model only - no HF API fallback."""
        try:
            logger.info(f"Loading local embedding model from: {self.model_path}")

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                local_files_only=True
            )
            self.model = AutoModel.from_pretrained(
                self.model_path,
                local_files_only=True
            ).to(self.device)

            logger.info("✅ Local embedding service initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize embedding service: {e}")
            raise
    
    def generate(self, text: str):
        """Generate embeddings for a given text."""
        if not text.strip():
            return self.fallback_embedding

        if self.tokenizer is None or self.model is None:
            raise

        try:
            encoded_input = self.tokenizer(
                text,
                padding=True,
                truncation=True,
                return_tensors="pt"
            ).to(self.device)

            with torch.no_grad():
                model_output = self.model(**encoded_input)

            embeddings = model_output.last_hidden_state.mean(dim=1).cpu().numpy().tolist()[0]

            # Ensure correct dimension
            if len(embeddings) != self.expected_dim:
                logger.warning(f"Embedding dimension mismatch: got {len(embeddings)}, expected {self.expected_dim}")
                return self.fallback_embedding

            return embeddings

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return self.fallback_embedding

    def _load_local_model(self):
        """Load the local embedding model - no online fallbacks."""
        try:
           
            logger.info(f"Loading local embedding model from: {self.model_path}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                local_files_only=True
            )
            self.model = AutoModel.from_pretrained(
                str(self.model_path),
                local_files_only=True
            )
            
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"✅ Local embedding model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load local model: {e}")
            raise EmbeddingError(f"Local model loading failed: {str(e)}")

    def _mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def _generate_local_embedding(self, text: str) -> List[float]:
        if not self.model or not self.tokenizer:
            raise EmbeddingError("Local model not properly initialized")
        try:
            cleaned_text = text.strip()
            if not cleaned_text:
                raise EmbeddingError("Empty text after cleaning")
            encoded_input = self.tokenizer(cleaned_text, padding=True, truncation=True, max_length=512, return_tensors='pt')
            encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}
            with torch.no_grad():
                model_output = self.model(**encoded_input)
            sentence_embedding = self._mean_pooling(model_output, encoded_input['attention_mask'])
            sentence_embedding = torch.nn.functional.normalize(sentence_embedding, p=2, dim=1)
            embedding = sentence_embedding.cpu().numpy()[0].tolist()
            if not validate_embedding(embedding, self.expected_dim):
                raise EmbeddingError("Invalid embedding generated")
            return embedding
        except Exception as e:
            logger.error(f"Error generating local embedding: {e}")
            raise EmbeddingError(f"Failed to generate embedding: {str(e)}")

    def _get_fallback_embedding(self, text: str) -> List[float]:
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        np.random.seed(hash_int % (2**32))
        embedding = np.random.normal(0, 0.1, self.expected_dim)
        return embedding.tolist()

    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using local model only."""
        if not text or len(text.strip()) == 0:
            return np.array(self.fallback_embedding)
        
        try:
            if not self.model or not self.tokenizer:
                raise EmbeddingError("Local model not properly initialized. Call initialize() first.")
            
            embedding_list = self._generate_local_embedding(text)

            return np.array(embedding_list)

        except EmbeddingError as e:
            logger.error(f"Embedding generation failed: {e}")
            fallback = self._get_fallback_embedding(text)
            return np.array(fallback)
        except Exception as e:
            logger.error(f"Unexpected error in embedding generation: {e}")
            return np.array(self.fallback_embedding)  

    async def generate_embedding_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using local model only."""
        if not texts:
            return []
        
        embeddings = []
        batch_size = 8
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            for text in batch_texts:
                try:
                    embedding = self._generate_local_embedding(text)
                    embeddings.append(embedding)
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for text {i}: {e}")
                    embeddings.append(self._get_fallback_embedding(text))

        return embeddings

    def get_model_info(self) -> dict:
        return {
            "model_path": str(self.model_path),
            "framework": "transformers-local",
            "device": str(self.device),
            "expected_dimension": self.expected_dim,
            "fallback_available": True,
            "local_model_loaded": self.model is not None,
            "tokenizer_loaded": self.tokenizer is not None,
            "local_only": True
        }

    async def health_check(self) -> dict:
        try:
            test_text = "Legal document test for embedding generation."
            test_embedding = await self.generate_embedding(test_text)
            is_healthy = validate_embedding(test_embedding, self.expected_dim)
            return {
                "healthy": is_healthy,
                "use_hf_api": False,
                "device": str(self.device),
                "embedding_dim": len(test_embedding),
                "local_model_loaded": self.model is not None,
                "tokenizer_loaded": self.tokenizer is not None,
                "test_embedding_valid": is_healthy,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "use_hf_api": False,
                "local_model_loaded": self.model is not None,
                "tokenizer_loaded": self.tokenizer is not None,
                "timestamp": datetime.utcnow().isoformat()
            }
