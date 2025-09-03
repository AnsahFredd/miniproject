"""AI services module - exports AI functionality without circular dependencies."""

from .classification_service import classify_document
from .summarization_service import summarize_text

# Export the main AI functions that other services need
__all__ = [
    'classify_document',
    'summarize_text'
]
