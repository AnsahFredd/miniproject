import os
import logging
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from app.core.config import settings
from app.utils.lazy_model_loader import lazy_loader, require_model

logger = logging.getLogger(__name__)

class SummarizationService:
    def __init__(self):
        self.model_name = settings.SUMMARIZATION_MODEL  # facebook/bart-large-cnn
        
        logger.info(f"SummarizationService initialized. Model candidate: {self.model_name}")
        logger.info("Model will be loaded on first use (lazy loading).")
    
    @require_model('summarization_primary', settings.SUMMARIZATION_MODEL, 'summarization')
    def _get_summarizer(self):
        """Get the loaded summarization pipeline."""
        return self._current_model
    
    def _chunk_text(self, text: str, max_length: int = 1024) -> list:
        """
        Split text into chunks for processing long documents.
        BART has a max input length of ~1024 tokens.
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + 1 > max_length:
                if current_chunk:  # Only add non-empty chunks
                    chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = 1
            else:
                current_chunk.append(word)
                current_length += 1
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def summarize_text(self, text: str, max_length: int = 130, min_length: int = 30) -> str:
        """Generate a summary of the provided text."""
        try:
            if not text or len(text.strip()) == 0:
                return "No content to summarize."
            
            # Handle very short texts
            word_count = len(text.split())
            if word_count < min_length:
                logger.info("Text too short for summarization, returning original")
                return text
            
            summarizer = self._get_summarizer()
            
            # Handle long texts by chunking if necessary
            max_input_tokens = 1024  # BART's approximate max input length
            
            if word_count > max_input_tokens:
                logger.info(f"Text is long ({word_count} words), chunking for processing")
                
                # Chunk the text
                chunks = self._chunk_text(text, max_input_tokens)
                summaries = []
                
                for i, chunk in enumerate(chunks):
                    logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                    try:
                        summary = summarizer(
                            chunk,
                            max_length=min(max_length, len(chunk.split()) // 2),
                            min_length=min(min_length, len(chunk.split()) // 4),
                            do_sample=False,
                            truncation=True
                        )
                        summaries.append(summary[0]['summary_text'])
                    except Exception as chunk_error:
                        logger.warning(f"Error processing chunk {i+1}: {chunk_error}")
                        continue
                
                if not summaries:
                    return "Error: Could not summarize any part of the text."
                
                # Combine summaries
                combined_summary = " ".join(summaries)
                
                # If combined summary is still too long, summarize again
                if len(combined_summary.split()) > max_length:
                    logger.info("Re-summarizing combined chunks")
                    final_summary = summarizer(
                        combined_summary,
                        max_length=max_length,
                        min_length=min_length,
                        do_sample=False,
                        truncation=True
                    )
                    return final_summary[0]['summary_text']
                
                return combined_summary
            else:
                # Single pass summarization for shorter texts
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
            return f"Error generating summary: {str(e)}"
    
    def summarize_text_advanced(
        self, 
        text: str, 
        max_length: int = 130, 
        min_length: int = 30,
        do_sample: bool = False,
        temperature: float = 1.0,
        top_p: float = 1.0,
        repetition_penalty: float = 1.0
    ) -> str:
        """
        Advanced summarization with more control parameters.
        """
        try:
            if not text or len(text.strip()) == 0:
                return "No content to summarize."
            
            # Handle very short texts
            word_count = len(text.split())
            if word_count < min_length:
                logger.info("Text too short for summarization, returning original")
                return text
            
            summarizer = self._get_summarizer()
            
            # For advanced parameters, we might need to chunk large texts
            if word_count > 1024:
                logger.info("Using basic summarization for long text with advanced parameters")
                return self.summarize_text(text, max_length, min_length)
            
            # Advanced summarization parameters
            generation_kwargs = {
                "max_length": max_length,
                "min_length": min_length,
                "do_sample": do_sample,
                "truncation": True,
                "clean_up_tokenization_spaces": True
            }
            
            # Only add sampling parameters if do_sample is True
            if do_sample:
                generation_kwargs.update({
                    "temperature": temperature,
                    "top_p": top_p,
                    "repetition_penalty": repetition_penalty
                })
            
            summary = summarizer(text, **generation_kwargs)
            return summary[0]["summary_text"]
        
        except Exception as e:
            logger.error(f"Error during advanced text summarization: {e}")
            return f"Error generating summary: {str(e)}"
    
    def summarize_with_custom_prompt(self, text: str, custom_instruction: str = "", max_length: int = 130) -> str:
        """
        Summarize with custom instructions (experimental).
        """
        try:
            if custom_instruction:
                # Prepend instruction to text
                prompted_text = f"{custom_instruction}\n\nText to summarize:\n{text}"
            else:
                prompted_text = text
            
            return self.summarize_text(prompted_text, max_length=max_length)
        
        except Exception as e:
            logger.error(f"Error in custom prompt summarization: {e}")
            return f"Error generating summary with custom prompt: {str(e)}"
    
    def get_model_info(self) -> dict:
        """Return information about the loaded summarization model."""
        try:
            return {
                "model_type": self.model_name,
                "model_loaded": lazy_loader.is_model_loaded('summarization_primary'),
                "framework": "transformers + pytorch",
                "pipeline_task": "summarization"
            }
        except Exception as e:
            return {
                "error": str(e),
                "model_loaded": False
            }

# Backward compatibility functions (for existing code)
def summarize_text(text: str, max_length: int = 130, min_length: int = 30) -> str:
    """Backward compatible function for existing code."""
    service = SummarizationService()
    return service.summarize_text(text, max_length, min_length)

def summarize_text_advanced(
    text: str, 
    max_length: int = 130, 
    min_length: int = 30,
    do_sample: bool = False,
    temperature: float = 1.0,
    top_p: float = 1.0
) -> str:
    """Backward compatible function for existing code."""
    service = SummarizationService()
    return service.summarize_text_advanced(text, max_length, min_length, do_sample, temperature, top_p)

def get_model_info() -> dict:
    """Backward compatible function for existing code."""
    service = SummarizationService()
    return service.get_model_info()

# Global service instance for consistency with other services
summarization_service = SummarizationService()
