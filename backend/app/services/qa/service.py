"""
Main QA service orchestration
"""
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any
from .models import PipelineManager
from .context import ContextManager
from .config import QAModelError
from ..legal_ai_service import legal_ai_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class QuestionAnsweringService:
    """Main QA service with AI integration"""
    
    def __init__(self):
        self.pipeline_manager = PipelineManager()
        self.context_manager = ContextManager()
        logger.info("Enhanced QA service initialized with AI integration")
        logger.info(f"AI Service Status: {legal_ai_service.health_check()}")

    def add_document(self, document_id: str, content: str):
        """Add a document to the QA knowledge base"""
        return self.context_manager.add_document(document_id, content)

    async def load_document_from_db(self, document_id: str, user_id: str) -> Optional[str]:
        """Load document content from database"""
        return await self.context_manager.load_document_from_db(document_id, user_id)

    async def answer_question(self, question: str, user_id: str, document_id: Optional[str] = None) -> Dict[str, Any]:
        """Enhanced question answering with AI priority"""
        try:
            logger.info(f"Processing question with AI integration for user {user_id}, document: {document_id}")
            
            context = None
            used_document_id = None
            document_metadata = {}

            # Load document context
            if document_id and document_id in self.context_manager.documents:
                doc_data = self.context_manager.documents[document_id]
                context = doc_data['content']
                used_document_id = document_id
                document_metadata = self.context_manager.get_document_metadata(document_id)
            elif document_id:
                context = await self.context_manager.load_document_from_db(document_id, user_id)
                if context:
                    used_document_id = document_id
                    document_metadata = self.context_manager.get_document_metadata(document_id)
            
            if not context or not context.strip():
                context, used_document_id = await self.context_manager.find_best_context_from_db(question, user_id)
                if context and used_document_id:
                    document_metadata = self.context_manager.get_document_metadata(used_document_id)
            
            if not context:
                return {
                    "answer": "I don't have any legal documents to analyze. Please upload some documents first.",
                    "source_section": "",
                    "confidence": 0.0,
                }
            
            # Select and run QA pipeline (now prioritizes AI)
            qa_pipeline, model_type = self.pipeline_manager.select_qa_pipeline(question, context)
            
            # Truncate context if too long
            max_context_length = getattr(settings, 'MAX_CONTEXT_LENGTH', 8000)
            if len(context) > max_context_length:
                context = context[:max_context_length]
            
            # Run QA
            result = self.pipeline_manager.run_qa_pipeline(qa_pipeline, question, context, model_type)
            
            # Extract and enhance answer
            answer = result.get("answer", "No answer found")
            confidence = result.get("score", 0.0)
            
            # Enhanced source section finding
            source_section = self.context_manager.find_relevant_source_section(answer, context)
            
            return {
                "answer": answer,
                "source_section": source_section,
                "confidence": confidence,
                "document_id": used_document_id,
                "model_type": model_type,
                "document_metadata": document_metadata,
                "ai_powered": model_type == "legal_ai"
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced answer_question: {e}")
            return {
                "answer": f"I encountered an error while analyzing your legal question: {str(e)}",
                "source_section": "",
                "confidence": 0.0,
                "document_id": document_id
            }

    def health_check(self) -> dict:
        """Enhanced health check including AI status"""
        ai_health = legal_ai_service.health_check()
        model_status = self.pipeline_manager.get_model_status()
        
        return {
            "status": "healthy",
            "ai_service": ai_health,
            "models_loaded": {
                "general_qa": model_status["general_qa_model"],
                "legal_qa": model_status["legal_qa_model"],
                "enhanced_fallback": model_status["enhanced_fallback"]
            },
            "documents_cached": len(self.context_manager.documents),
            "local_only": not ai_health.get("ai_available", False),
            "legal_analyzer": "active"
        }


# Initialize the service
qa_service = QuestionAnsweringService()


# Main functions for external use
async def answer_question(question: str, user_id: str, document_id: Optional[str] = None) -> Dict:
    """Answer a question using the AI-enhanced QA service"""
    return await qa_service.answer_question(question, user_id, document_id)


async def answer_question_with_context(question: str, context: str, document_id: str = None) -> Dict[str, Any]:
    """Enhanced question answering with AI integration"""
    try:
        logger.info(f"Processing question with AI context analysis for document: {document_id}")
        
        # Validate inputs
        if not question or not question.strip():
            return {
                "answer": "Please provide a valid question.",
                "source_section": "",
                "confidence": 0.0
            }
        
        if not context or not context.strip():
            return {
                "answer": "I'm sorry, I couldn't find any relevant information to answer your question.",
                "source_section": "",
                "confidence": 0.0
            }
        
        # Try AI first for legal questions
        qa_pipeline, model_type = qa_service.pipeline_manager.select_qa_pipeline(question, context)
        
        # Truncate context if too long
        max_context_length = getattr(settings, 'MAX_CONTEXT_LENGTH', 8000)
        if len(context) > max_context_length:
            context = context[:max_context_length]
        
        # Run QA using AI-enhanced pipeline
        result = qa_service.pipeline_manager.run_qa_pipeline(qa_pipeline, question, context, model_type)
        
        # Extract and enhance the answer
        answer = result.get("answer", "No answer found")
        confidence = result.get("score", 0.0)
        
        # Find relevant source section
        source_section = qa_service.context_manager.find_relevant_source_section(answer, context)
        
        # Add AI analysis metadata
        metadata = {"model_type": model_type}
        if model_type == "legal_ai":
            try:
                ai_analysis = legal_ai_service.analyze_contract_type(context)
                if ai_analysis.get("success"):
                    metadata["document_analysis"] = ai_analysis["analysis"]
            except Exception as e:
                logger.debug(f"Could not add AI analysis metadata: {e}")
        
        response = {
            "answer": answer,
            "source_section": source_section,
            "confidence": confidence,
            "model_type": model_type,
            "metadata": metadata,
            "ai_powered": model_type == "legal_ai"
        }
        
        logger.info(f"Successfully processed question for document: {document_id} using {model_type}")
        return response
        
    except Exception as e:
        logger.error(f"Error in AI-enhanced answer_question_with_context: {str(e)}")
        return {
            "answer": f"I encountered an error while analyzing your legal question: {str(e)}",
            "source_section": "",
            "confidence": 0.0
        }


def get_model_status() -> Dict[str, bool]:
    """Get enhanced model status including AI"""
    return qa_service.pipeline_manager.get_model_status()


def health_check() -> dict:
    """Enhanced health check with AI status"""
    return qa_service.health_check()


# Re-export analyzer functions for backward compatibility
from .analyzer import analyze_document_type, analyze_essential_elements, analyze_enforceability_issues

__all__ = [
    'answer_question',
    'answer_question_with_context', 
    'get_model_status',
    'health_check',
    'analyze_document_type',
    'analyze_essential_elements',
    'analyze_enforceability_issues',
    'qa_service'
]