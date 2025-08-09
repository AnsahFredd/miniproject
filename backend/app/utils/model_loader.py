import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Any
from transformers import (
    AutoTokenizer, 
    AutoModel,
    AutoModelForSeq2SeqLM,
    AutoModelForSequenceClassification,
    AutoModelForQuestionAnswering
)
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Model mappings: local_path -> huggingface_model_id
MODEL_MAPPINGS = {
    "app/ai/models/bart-large-cnn": "facebook/bart-large-cnn",
    "app/ai/models/InLegalBERT": "law-ai/InLegalBERT",
    "app/ai/models/deberta-v3-large": "microsoft/deberta-v3-large",
    "app/ai/models/roberta-base-squad2": "deepset/roberta-base-squad2",
    "app/ai/models/InLegalBERT-classification": "law-ai/InLegalBERT",
    "app/ai/models/legal-bert-base-uncased": "nlpaueb/legal-bert-base-uncased",
}

def model_exists_locally(path: str) -> bool:
    """Check if model exists locally with proper files."""
    model_path = Path(path)
    if not model_path.exists():
        return False
    
    # Check for essential model files
    config_exists = (model_path / "config.json").exists()
    model_file_exists = (
        (model_path / "pytorch_model.bin").exists() or 
        (model_path / "model.safetensors").exists() or
        any(model_path.glob("pytorch_model-*.bin")) or
        any(model_path.glob("model-*.safetensors"))
    )
    
    return config_exists and model_file_exists

def load_tokenizer_smart(local_path: str, hf_model_id: Optional[str] = None) -> Any:
    """
    Load tokenizer from local path if available, otherwise from Hugging Face.
    """
    if hf_model_id is None:
        hf_model_id = MODEL_MAPPINGS.get(local_path, local_path)
    
    if model_exists_locally(local_path):
        logger.info(f"Loading tokenizer from local path: {local_path}")
        return AutoTokenizer.from_pretrained(local_path)
    else:
        logger.info(f"Local tokenizer not found, loading from HF: {hf_model_id}")
        return AutoTokenizer.from_pretrained(hf_model_id)

def load_model_for_summarization(local_path: str, hf_model_id: Optional[str] = None) -> Tuple[Any, Any]:
    """Load summarization model and tokenizer."""
    if hf_model_id is None:
        hf_model_id = MODEL_MAPPINGS.get(local_path, local_path)
    
    tokenizer = load_tokenizer_smart(local_path, hf_model_id)
    
    if model_exists_locally(local_path):
        logger.info(f"Loading summarization model from local path: {local_path}")
        model = AutoModelForSeq2SeqLM.from_pretrained(local_path)
    else:
        logger.info(f"Local model not found, loading from HF: {hf_model_id}")
        model = AutoModelForSeq2SeqLM.from_pretrained(hf_model_id)
    
    return model, tokenizer

def load_model_for_classification(local_path: str, hf_model_id: Optional[str] = None) -> Tuple[Any, Any]:
    """Load classification model and tokenizer."""
    if hf_model_id is None:
        hf_model_id = MODEL_MAPPINGS.get(local_path, local_path)
    
    tokenizer = load_tokenizer_smart(local_path, hf_model_id)
    
    if model_exists_locally(local_path):
        logger.info(f"Loading classification model from local path: {local_path}")
        model = AutoModelForSequenceClassification.from_pretrained(local_path)
    else:
        logger.info(f"Local model not found, loading from HF: {hf_model_id}")
        model = AutoModelForSequenceClassification.from_pretrained(hf_model_id)
    
    return model, tokenizer

def load_model_for_qa(local_path: str, hf_model_id: Optional[str] = None) -> Tuple[Any, Any]:
    """Load Q&A model and tokenizer."""
    if hf_model_id is None:
        hf_model_id = MODEL_MAPPINGS.get(local_path, local_path)
    
    tokenizer = load_tokenizer_smart(local_path, hf_model_id)
    
    if model_exists_locally(local_path):
        logger.info(f"Loading Q&A model from local path: {local_path}")
        model = AutoModelForQuestionAnswering.from_pretrained(local_path)
    else:
        logger.info(f"Local model not found, loading from HF: {hf_model_id}")
        model = AutoModelForQuestionAnswering.from_pretrained(hf_model_id)
    
    return model, tokenizer

def load_embedding_model_smart(local_path: str, hf_model_id: Optional[str] = None) -> Any:
    """Load embedding model (SentenceTransformer or regular transformers)."""
    if hf_model_id is None:
        hf_model_id = MODEL_MAPPINGS.get(local_path, local_path)
    
    try:
        if model_exists_locally(local_path):
            logger.info(f"Loading embedding model from local path: {local_path}")
            # Try sentence transformer format first
            if (Path(local_path) / "modules.json").exists():
                return SentenceTransformer(local_path)
            else:
                return SentenceTransformer(local_path)  # Will auto-detect format
        else:
            logger.info(f"Local embedding model not found, loading from HF: {hf_model_id}")
            return SentenceTransformer(hf_model_id)
    except Exception as e:
        logger.warning(f"Failed to load as SentenceTransformer: {e}")
        # Fallback to regular transformers
        tokenizer = load_tokenizer_smart(local_path, hf_model_id)
        if model_exists_locally(local_path):
            model = AutoModel.from_pretrained(local_path)
        else:
            model = AutoModel.from_pretrained(hf_model_id)
        return model, tokenizer

# Convenience functions for your existing services
def get_summarization_model(settings):
    """Get summarization model based on settings."""
    return load_model_for_summarization(settings.SUMMARIZATION_MODEL)

def get_classification_model(settings):
    """Get classification model based on settings."""
    return load_model_for_classification(settings.CLASSIFICATION_MODEL)

def get_qa_model(settings):
    """Get Q&A model based on settings."""
    return load_model_for_qa(settings.QA_MODEL)

def get_legal_qa_model(settings):
    """Get legal Q&A model based on settings."""
    return load_model_for_qa(settings.LEGAL_QA_MODEL)

def get_embedding_model(settings):
    """Get embedding model based on settings."""
    return load_embedding_model_smart(settings.EMBEDDING_MODEL)