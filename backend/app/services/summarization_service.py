import os
import logging
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from app.utils.model_loader import load_model_for_summarization

logger = logging.getLogger(__name__)

# === Base Path for Summarization Model ===
MODEL_DIR = Path(__file__).resolve().parent.parent / "ai/models/bart-large-cnn"
MODEL_DIR = MODEL_DIR.as_posix()

# === Load Summarization Model Using Smart Loader ===
try:
    model, tokenizer = load_model_for_summarization(MODEL_DIR, "facebook/bart-large-cnn")
    summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)
    logger.info("✅ Summarization model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load summarization model: {e}")
    # Fallback to direct HuggingFace loading
    try:
        logger.info("🔄 Attempting fallback to direct HuggingFace loading...")
        model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn")
        tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
        summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)
        logger.info("✅ Fallback summarization model loaded successfully")
    except Exception as fallback_error:
        logger.error(f"❌ Complete failure to load summarization model: {fallback_error}")
        raise fallback_error

def summarize_text(text: str, max_length: int = 130, min_length: int = 30) -> str:
    """Generate a summary of the provided text."""
    try:
        if not text or len(text.strip()) == 0:
            return "No content to summarize."
        
        # Handle very short texts
        if len(text.split()) < min_length:
            logger.info("Text too short for summarization, returning original")
            return text
        
        summary = summarizer(
            text, 
            max_length=max_length, 
            min_length=min_length, 
            do_sample=False,
            truncation=True
        )
        return summary[0]["summary_text"]
    
    except Exception as e:
        logger.error(f"Error during text summarization: {e}")
        # Return a fallback response instead of crashing
        return f"Error generating summary: {str(e)}"

def summarize_text_advanced(
    text: str, 
    max_length: int = 130, 
    min_length: int = 30,
    do_sample: bool = False,
    temperature: float = 1.0,
    top_p: float = 1.0
) -> str:
    """
    Advanced summarization with more control parameters.
    """
    try:
        if not text or len(text.strip()) == 0:
            return "No content to summarize."
        
        # Handle very short texts
        if len(text.split()) < min_length:
            logger.info("Text too short for summarization, returning original")
            return text
        
        # Advanced summarization parameters
        summary = summarizer(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=do_sample,
            temperature=temperature if do_sample else 1.0,
            top_p=top_p if do_sample else 1.0,
            truncation=True,
            clean_up_tokenization_spaces=True
        )
        
        return summary[0]["summary_text"]
    
    except Exception as e:
        logger.error(f"Error during advanced text summarization: {e}")
        return f"Error generating summary: {str(e)}"

def get_model_info() -> dict:
    """Return information about the loaded summarization model."""
    try:
        return {
            "model_type": "facebook/bart-large-cnn",
            "local_path": MODEL_DIR,
            "model_loaded": summarizer is not None,
            "tokenizer_vocab_size": len(tokenizer) if tokenizer else 0
        }
    except Exception as e:
        return {
            "error": str(e),
            "model_loaded": False
        }