"""
Question Answering Service Module
"""
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import main service components
from .service import (
    answer_question,
    answer_question_with_context,
    get_model_status,
    health_check,
    analyze_document_type,
    analyze_essential_elements,
    analyze_enforceability_issues,
    qa_service
)

# Import individual components for advanced usage
from .models import PipelineManager, load_local_pipeline, create_enhanced_fallback_pipeline
from .analyzer import LegalDocumentAnalyzer
from .context import ContextManager
from .config import (
    QAModelError,
    DocumentNotFoundError,
    ContextTooLongError,
    LEGAL_KEYWORDS,
    CONTRACT_PATTERNS,
    ESSENTIAL_ELEMENTS
)

# Export main public API
__all__ = [
    # Main functions
    'answer_question',
    'answer_question_with_context',
    'get_model_status', 
    'health_check',
    
    # Analysis functions
    'analyze_document_type',
    'analyze_essential_elements', 
    'analyze_enforceability_issues',
    
    # Main service instance
    'qa_service',
    
    # Components for advanced usage
    'PipelineManager',
    'LegalDocumentAnalyzer',
    'ContextManager',
    'load_local_pipeline',
    'create_enhanced_fallback_pipeline',
    
    # Configuration and constants
    'LEGAL_KEYWORDS',
    'CONTRACT_PATTERNS',
    'ESSENTIAL_ELEMENTS',
    
    # Exceptions
    'QAModelError',
    'DocumentNotFoundError',
    'ContextTooLongError'
]