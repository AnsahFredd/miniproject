"""
Document context and database operations
"""
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
import logging
from bson import ObjectId
from app.models.document import AcceptedDocument
from .analyzer import LegalDocumentAnalyzer
from ..legal_ai_service import legal_ai_service
from .config import LEGAL_KEYWORDS

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages document loading and context selection"""
    
    def __init__(self):
        self.documents = {}
        self.legal_analyzer = LegalDocumentAnalyzer()
        self.legal_keywords = LEGAL_KEYWORDS
    
    def add_document(self, document_id: str, content: str):
        """Add a document to the QA knowledge base with AI analysis"""
        try:
            # Try AI analysis first
            try:
                ai_analysis = legal_ai_service.analyze_contract_type(content)
                if ai_analysis.get("success"):
                    analysis_data = ai_analysis["analysis"]
                    doc_type = analysis_data.get("document_type", "Unknown")
                    logger.info(f"AI Analysis: Document is {doc_type}")
                else:
                    # Fallback to pattern matching
                    doc_analysis = self.legal_analyzer.analyze_document_type(content)
                    elements_analysis = self.legal_analyzer.analyze_essential_elements(content)
                    analysis_data = {"document_type": doc_analysis["document_type"]}
            except Exception as e:
                logger.warning(f"AI analysis failed, using fallback: {e}")
                doc_analysis = self.legal_analyzer.analyze_document_type(content)
                elements_analysis = self.legal_analyzer.analyze_essential_elements(content)
                analysis_data = {"document_type": doc_analysis["document_type"]}
            
            self.documents[document_id] = {
                'content': content,
                'added_at': datetime.now().isoformat(),
                'ai_analysis': analysis_data,
                'content_length': len(content)
            }
            
            doc_type = analysis_data.get("document_type", "Unknown")
            logger.info(f"Added document {document_id} to QA knowledge base - Type: {doc_type}")
            
        except Exception as e:
            logger.error(f"Failed to add document {document_id} to QA service: {e}")
            raise

    async def load_document_from_db(self, document_id: str, user_id: str) -> Optional[str]:
        """Load document content from database with AI analysis"""
        try:
            document = await AcceptedDocument.find_one({
                "_id": ObjectId(document_id),
                "user_id": user_id
            })
            
            if document and document.content:
                # Analyze with AI when loading
                try:
                    ai_analysis = legal_ai_service.analyze_contract_type(document.content)
                    if ai_analysis.get("success"):
                        analysis_data = ai_analysis["analysis"]
                    else:
                        doc_analysis = self.legal_analyzer.analyze_document_type(document.content)
                        analysis_data = {"document_type": doc_analysis["document_type"]}
                except Exception as e:
                    logger.warning(f"AI analysis on load failed: {e}")
                    analysis_data = {"document_type": "Analysis Failed"}
                
                self.documents[document_id] = {
                    'content': document.content,
                    'loaded_at': datetime.now().isoformat(),
                    'ai_analysis': analysis_data,
                    'content_length': len(document.content)
                }
                return document.content
            
            return None
        except Exception as e:
            logger.error(f"Failed to load document {document_id} from database: {e}")
            return None

    async def find_best_context_from_db(self, question: str, user_id: str) -> Tuple[Optional[str], Optional[str]]:
        """Enhanced context finding using AI-powered semantic matching"""
        try:
            documents = await AcceptedDocument.find(
                AcceptedDocument.user_id == user_id
            ).to_list()
            
            if not documents:
                return None, None
            
            question_lower = question.lower()
            best_match = None
            best_score = 0
            
            for doc in documents:
                if not doc.content:
                    continue
                
                # Try AI-powered document relevance scoring
                try:
                    # Use AI to determine document relevance to question
                    ai_relevance_prompt = f"Rate relevance (0-10) of this document to question: '{question}'. Document preview: {doc.content[:500]}..."
                    
                    # For now, use enhanced keyword matching with AI insights
                    content_lower = doc.content.lower()
                    score = 0
                    
                    # Enhanced scoring algorithm
                    question_words = set(question_lower.split())
                    content_words = set(content_lower.split())
                    common_words = question_words.intersection(content_words)
                    keyword_score = len(common_words) * 2
                    
                    # Legal keyword bonus
                    legal_question_words = question_words.intersection(self.legal_keywords)
                    if legal_question_words:
                        legal_content_words = content_words.intersection(self.legal_keywords)
                        legal_overlap = legal_question_words.intersection(legal_content_words)
                        keyword_score += len(legal_overlap) * 5
                    
                    # Document type relevance
                    if any(term in question_lower for term in ['contract type', 'document type', 'what type']):
                        keyword_score += 10
                    
                    # Specific legal question types
                    if any(term in question_lower for term in ['enforceable', 'parties', 'missing', 'valid']):
                        keyword_score += 8
                    
                    score = keyword_score
                    
                except Exception as e:
                    logger.warning(f"AI relevance scoring failed: {e}")
                    # Fallback to basic keyword matching
                    content_lower = doc.content.lower()
                    question_words = set(question_lower.split())
                    content_words = set(content_lower.split())
                    common_words = question_words.intersection(content_words)
                    score = len(common_words)
                
                if score > best_score:
                    best_score = score
                    best_match = doc
            
            if best_match:
                doc_id = str(best_match.id)
                
                # Analyze document when selecting
                try:
                    ai_analysis = legal_ai_service.analyze_contract_type(best_match.content)
                    if ai_analysis.get("success"):
                        analysis_data = ai_analysis["analysis"]
                    else:
                        doc_analysis = self.legal_analyzer.analyze_document_type(best_match.content)
                        analysis_data = {"document_type": doc_analysis["document_type"]}
                except Exception as e:
                    logger.warning(f"Document analysis failed: {e}")
                    analysis_data = {"document_type": "Analysis Failed"}
                
                self.documents[doc_id] = {
                    'content': best_match.content,
                    'loaded_at': datetime.now().isoformat(),
                    'ai_analysis': analysis_data,
                    'content_length': len(best_match.content)
                }
                return best_match.content, doc_id
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error finding best context from DB: {e}")
            return None, None

    def find_relevant_source_section(self, answer: str, context: str) -> str:
        """Find the most relevant source section for the answer"""
        if not answer or "Error" in answer:
            return context[:500]
        
        # Try to find exact matches first
        paragraphs = context.split('\n\n')
        for para in paragraphs:
            if answer.lower() in para.lower():
                return para.strip()
        
        # Try sentence-level matching
        sentences = context.split('. ')
        for i, sentence in enumerate(sentences):
            if answer.lower() in sentence.lower():
                start = max(0, i - 1)
                end = min(len(sentences), i + 2)
                result = '. '.join(sentences[start:end])
                if not result.endswith('.'):
                    result += '.'
                return result
        
        # Fallback to first significant paragraph
        return context[:500]

    def get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """Get metadata for a cached document"""
        if document_id in self.documents:
            doc_data = self.documents[document_id]
            return {
                'ai_analysis': doc_data.get('ai_analysis', {}),
                'content_length': doc_data.get('content_length', 0),
                'loaded_at': doc_data.get('loaded_at') or doc_data.get('added_at'),
                'cached': True
            }
        return {'cached': False}