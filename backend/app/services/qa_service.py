import os
import logging
from pathlib import Path
import re
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline
import torch
from typing import Dict, List, Optional
from app.models.document import AcceptedDocument
from bson import ObjectId
from app.utils.model_loader import load_model_for_qa

logger = logging.getLogger(__name__)

# === Base Paths for QA Models ===
GENERAL_QA_MODEL_DIR = Path(__file__).resolve().parent.parent / "ai/models/deberta-v3-large"
LEGAL_QA_MODEL_DIR = Path(__file__).resolve().parent.parent / "ai/models/roberta-base-squad2"

GENERAL_QA_MODEL_DIR = GENERAL_QA_MODEL_DIR.as_posix()
LEGAL_QA_MODEL_DIR = LEGAL_QA_MODEL_DIR.as_posix()

# === Load General QA Model Using Smart Loader ===
general_qa_pipeline = None
try:
    general_model, general_tokenizer = load_model_for_qa(GENERAL_QA_MODEL_DIR, "microsoft/deberta-v3-large")
    general_qa_pipeline = pipeline("question-answering", model=general_model, tokenizer=general_tokenizer)
    logger.info("✅ General QA model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load general QA model: {e}")
    # Fallback to direct HuggingFace loading
    try:
        logger.info("🔄 Attempting fallback to direct HuggingFace loading for general QA...")
        general_model = AutoModelForQuestionAnswering.from_pretrained("microsoft/deberta-v3-large")
        general_tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-v3-large")
        general_qa_pipeline = pipeline("question-answering", model=general_model, tokenizer=general_tokenizer)
        logger.info("✅ Fallback general QA model loaded successfully")
    except Exception as fallback_error:
        logger.error(f"❌ Complete failure to load general QA model: {fallback_error}")
        general_qa_pipeline = None

# === Load Legal QA Model Using Smart Loader ===
legal_qa_pipeline = None
try:
    legal_model, legal_tokenizer = load_model_for_qa(LEGAL_QA_MODEL_DIR, "deepset/roberta-base-squad2")
    legal_qa_pipeline = pipeline("question-answering", model=legal_model, tokenizer=legal_tokenizer)
    logger.info("✅ Legal QA model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load legal QA model: {e}")
    # Fallback to direct HuggingFace loading
    try:
        logger.info("🔄 Attempting fallback to direct HuggingFace loading for legal QA...")
        legal_model = AutoModelForQuestionAnswering.from_pretrained("deepset/roberta-base-squad2")
        legal_tokenizer = AutoTokenizer.from_pretrained("deepset/roberta-base-squad2")
        legal_qa_pipeline = pipeline("question-answering", model=legal_model, tokenizer=legal_tokenizer)
        logger.info("✅ Fallback legal QA model loaded successfully")
    except Exception as fallback_error:
        logger.error(f"❌ Complete failure to load legal QA model: {fallback_error}")
        legal_qa_pipeline = None

# Ensure at least one model loaded
if not general_qa_pipeline and not legal_qa_pipeline:
    raise RuntimeError("❌ No QA models could be loaded!")

class QuestionAnsweringService:
    def __init__(self):
        self.documents = {}  # Cache for document content
        self.general_qa_pipeline = general_qa_pipeline
        self.legal_qa_pipeline = legal_qa_pipeline
        
        # Legal keywords to determine which model to use
        self.legal_keywords = {
            'contract', 'agreement', 'clause', 'legal', 'law', 'court', 'case', 'defendant', 
            'plaintiff', 'liability', 'breach', 'damages', 'jurisdiction', 'statute', 
            'regulation', 'compliance', 'terms', 'conditions', 'warranty', 'indemnity',
            'termination', 'penalty', 'arbitration', 'litigation', 'patent', 'copyright',
            'trademark', 'intellectual property', 'confidentiality', 'non-disclosure'
        }
        
        general_status = "loaded" if self.general_qa_pipeline else "failed"
        legal_status = "loaded" if self.legal_qa_pipeline else "failed"
        
        logger.info(f"QA service initialized with models:")
        logger.info(f"  - General QA: {GENERAL_QA_MODEL_DIR} - {general_status}")
        logger.info(f"  - Legal QA: {LEGAL_QA_MODEL_DIR} - {legal_status}")
    
    def _is_legal_question(self, question: str, context: str = "") -> bool:
        """Determine if a question is legal-related."""
        text_to_check = (question + " " + context).lower()
        legal_word_count = sum(1 for keyword in self.legal_keywords if keyword in text_to_check)
        return legal_word_count >= 2  # At least 2 legal keywords
    
    def _select_qa_pipeline(self, question: str, context: str = ""):
        """Select appropriate QA pipeline based on question and context."""
        if self._is_legal_question(question, context):
            if self.legal_qa_pipeline:
                logger.info("Using legal QA model")
                return self.legal_qa_pipeline
            elif self.general_qa_pipeline:
                logger.info("Legal QA model unavailable, using general QA model")
                return self.general_qa_pipeline
        else:
            if self.general_qa_pipeline:
                logger.info("Using general QA model")
                return self.general_qa_pipeline
            elif self.legal_qa_pipeline:
                logger.info("General QA model unavailable, using legal QA model")
                return self.legal_qa_pipeline
        
        # This shouldn't happen given our initialization check, but just in case
        raise RuntimeError("No QA models available")
    
    def add_document(self, doc_id: str, content: str):
        """Add a document to the knowledge base."""
        self.documents[doc_id] = content
        logger.info(f"Added document {doc_id} to knowledge base")
    
    async def load_document_from_db(self, document_id: str, user_id: str) -> Optional[str]:
        """Load document content from database if not in cache."""
        if document_id in self.documents:
            return self.documents[document_id]
        
        try:
            document = await AcceptedDocument.find_one({
                "_id": ObjectId(document_id),
                "user_id": user_id
            })
            
            if document and document.content:
                self.documents[document_id] = document.content
                return document.content
                
        except Exception as e:
            logger.error(f"Error loading document {document_id}: {e}")
        
        return None
    
    async def answer_question(self, question: str, user_id: str, document_id: Optional[str] = None) -> Dict:
        """
        Answer a question using the appropriate model.
        
        Args:
            question: The question to answer
            user_id: User ID for document access control
            document_id: Optional specific document to search in
            
        Returns:
            Dictionary with answer, confidence score, and source
        """
        try:
            if document_id:
                # Answer from specific document
                context = await self.load_document_from_db(document_id, user_id)
                if not context:
                    return {
                        "answer": "Document not found or you don't have access to it.",
                        "confidence_score": 0.0,
                        "source_document": None,
                        "model_used": None
                    }
                source = document_id
            else:
                # Search all user's documents for best match
                context, source = await self._find_best_context_from_db(question, user_id)
            
            if not context:
                return {
                    "answer": "No documents available to answer the question.",
                    "confidence_score": 0.0,
                    "source_document": None,
                    "model_used": None
                }
            
            # Select appropriate QA pipeline
            qa_pipeline = self._select_qa_pipeline(question, context)
            model_type = "legal" if qa_pipeline == self.legal_qa_pipeline else "general"
            
            # Get answer from the model
            result = qa_pipeline(question=question, context=context)
            
            return {
                "answer": result["answer"],
                "confidence_score": result["score"],
                "source_document": source,
                "model_used": model_type
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                "answer": f"Error processing question: {str(e)}",
                "confidence_score": 0.0,
                "source_document": None,
                "model_used": None
            }
    
    def _preprocess_context(self, search_results: List[Dict]) -> str:
        """
        Preprocess search results to create better context.
        """
        if not search_results:
            return ""
        
        # Combine all search results with proper formatting
        context_parts = []
        for i, result in enumerate(search_results, 1):
            title = result.get('title', 'Document')
            section = result.get('section', 'No section')
            description = result.get('description', '')
            
            # Clean up the description
            description = re.sub(r'\s+', ' ', description).strip()
            
            context_part = f"Document {i} - {title} ({section}): {description}"
            context_parts.append(context_part)
        
        # Join with clear separators and limit total length
        full_context = "\n\n".join(context_parts)
        
        # Limit context to prevent token overflow (roughly 512 tokens = ~2000 chars)
        if len(full_context) > 2000:
            full_context = full_context[:2000] + "..."
            logger.warning("Context truncated due to length")
        
        return full_context
    
    def _postprocess_answer(self, answer: str, question: str) -> str:
        """
        Postprocess the answer to make it more complete and readable.
        """
        if not answer or len(answer.strip()) < 10:
            return "I couldn't find a specific answer to your question in the provided documents."
        
        # Clean up the answer
        answer = answer.strip()
        
        # If answer seems incomplete (ends abruptly), try to complete it
        if not answer.endswith(('.', '!', '?', ';')) and len(answer) > 20:
            answer += "..."
        
        # Ensure answer makes sense in context
        if len(answer) < 20:
            return f"Based on the documents, {answer}. However, the available information is limited."
        
        return answer
    
    async def answer_question_with_context(self, question: str, search_results: List[Dict], user_id: str, force_model: Optional[str] = None) -> Dict:
        """
        Answer a question using provided context (e.g., from search results).
        
        Args:
            question: The question to answer
            search_results: Search results to use as context
            user_id: User ID for logging/security
            force_model: Optional model type to force ("legal" or "general")
            
        Returns:
            Dictionary with answer, confidence score, source, and model used
        """
        try:
            if not search_results:
                return {
                    "answer": "No context provided to answer the question.",
                    "confidence_score": 0.0,
                    "source_document": "search_results",
                    "model_used": None
                }
            
            # Preprocess context
            context = self._preprocess_context(search_results)
            
            if not context:
                return {
                    "answer": "The provided search results don't contain sufficient information to answer the question.",
                    "confidence_score": 0.0,
                    "source_document": "search_results",
                    "model_used": None
                }
            
            logger.info(f"Processing question: {question}")
            logger.info(f"Context length: {len(context)} characters")
            
            # Select appropriate QA pipeline
            if force_model == "legal" and self.legal_qa_pipeline:
                qa_pipeline = self.legal_qa_pipeline
                model_type = "legal"
            elif force_model == "general" and self.general_qa_pipeline:
                qa_pipeline = self.general_qa_pipeline
                model_type = "general"
            else:
                qa_pipeline = self._select_qa_pipeline(question, context)
                model_type = "legal" if qa_pipeline == self.legal_qa_pipeline else "general"
            
            # Get answer from the model
            try:
                result = qa_pipeline(
                    question=question, 
                    context=context,
                    max_answer_len=150,  # Allow longer answers
                    max_seq_len=512,    # Standard BERT limit
                    max_question_len=64
                )
                
                # Postprocess the answer
                processed_answer = self._postprocess_answer(result["answer"], question)

                logger.info(f"Raw answer: {result['answer']}")
                logger.info(f"Processed answer: {processed_answer}")
                logger.info(f"Confidence: {result['score']}")
                logger.info(f"Model used: {model_type}")
            
                return {
                    "answer": processed_answer,
                    "confidence_score": result["score"],
                    "source_document": "search_results",
                    "model_used": model_type
                }
            
            except Exception as model_error:
                logger.error(f"Model inference error: {model_error}")
                
                # Try the other model if one fails
                try:
                    if qa_pipeline == self.legal_qa_pipeline and self.general_qa_pipeline:
                        alternative_pipeline = self.general_qa_pipeline
                        alternative_model_type = "general"
                    elif qa_pipeline == self.general_qa_pipeline and self.legal_qa_pipeline:
                        alternative_pipeline = self.legal_qa_pipeline
                        alternative_model_type = "legal"
                    else:
                        raise Exception("No alternative model available")
                    
                    result = alternative_pipeline(
                        question=question,
                        context=context,
                        max_answer_len=150,
                        max_seq_len=512,
                        max_question_len=64
                    )
                    
                    processed_answer = self._postprocess_answer(result["answer"], question)
                    logger.info(f"Fallback to {alternative_model_type} model successful")
                    
                    return {
                        "answer": processed_answer,
                        "confidence_score": result["score"],
                        "source_document": "search_results",
                        "model_used": f"{alternative_model_type} (fallback)"
                    }
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {fallback_error}")
                
                # Final fallback: extract relevant sentences from context
                fallback_answer = self._extract_relevant_info(question, context)

                return {
                    "answer": fallback_answer,
                    "confidence_score": 0.5,
                    "source_document": "search_results",
                    "model_used": "fallback_extraction"
                }
            
        except Exception as e:
            logger.error(f"Error answering question with context: {e}")
            return {
                "answer": f"Error processing question: {str(e)}",
                "confidence_score": 0.0,
                "source_document": "search_results",
                "model_used": None
            }
    
    def _extract_relevant_info(self, question: str, context: str) -> str:
        """
        Fallback method to extract relevant information when QA model fails.
        """
        question_lower = question.lower()
        context_sentences = context.split('.')
        
        # Look for sentences containing key terms from the question
        question_words = set(question_lower.split())
        relevant_sentences = []
        
        for sentence in context_sentences:
            sentence_lower = sentence.lower()
            # Count how many question words appear in this sentence
            matches = sum(1 for word in question_words if word in sentence_lower)
            if matches >= 2:  # At least 2 matching words
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            # Return the most relevant sentence(s)
            answer = '. '.join(relevant_sentences[:2])  # Max 2 sentences
            return f"Based on the available information: {answer}."
        else:
            return "I couldn't find specific information related to your question in the provided documents."
    
    async def _find_best_context_from_db(self, question: str, user_id: str) -> tuple:
        """Find the best document context for the question from user's documents."""
        try:
            # Get all user documents
            documents = await AcceptedDocument.find(
                AcceptedDocument.user_id == user_id
            ).to_list()
            
            if not documents:
                return "", None
            
            best_score = 0.0
            best_context = ""
            best_doc_id = None
            
            # Select pipeline for initial scoring
            qa_pipeline = self._select_qa_pipeline(question)
            
            for doc in documents:
                if not doc.content:
                    continue
                    
                try:
                    result = qa_pipeline(question=question, context=doc.content)
                    if result["score"] > best_score:
                        best_score = result["score"]
                        best_context = doc.content
                        best_doc_id = str(doc.id)
                        
                        # Cache the document content
                        self.documents[str(doc.id)] = doc.content
                        
                except Exception as e:
                    logger.warning(f"Error processing document {doc.id}: {e}")
                    continue
            
            return best_context, best_doc_id
            
        except Exception as e:
            logger.error(f"Error finding best context: {e}")
            return "", None

    def get_model_info(self) -> dict:
        """Return information about the loaded QA models."""
        try:
            return {
                "general_model": {
                    "type": "microsoft/deberta-v3-large",
                    "path": GENERAL_QA_MODEL_DIR,
                    "loaded": self.general_qa_pipeline is not None
                },
                "legal_model": {
                    "type": "deepset/roberta-base-squad2",
                    "path": LEGAL_QA_MODEL_DIR,
                    "loaded": self.legal_qa_pipeline is not None
                },
                "pipeline_task": "question-answering"
            }
        except Exception as e:
            return {
                "error": str(e),
                "models_loaded": False
            }


# Initialize global service instance
qa_service = QuestionAnsweringService()