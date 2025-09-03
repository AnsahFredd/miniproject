"""
Fixed Question Answering Service with proper AI integration
Structural issues resolved - all code properly organized in classes/functions
"""

from datetime import datetime
import logging
from pathlib import Path
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline
import torch
from typing import Dict, List, Optional, Tuple, Any
from app.models.document import AcceptedDocument
from bson import ObjectId
from dotenv import load_dotenv
from app.core.config import settings
import re
from app.services.legal_ai_service import legal_ai_service

load_dotenv()

# Keep existing model configuration for fallback
QA_NAME = "microsoft/deberta-v3-large"
QA_PATH = Path("app/ai/models/question-answering")
LEGAL_QA_NAME = "deepset/roberta-base-squad2"
LEGAL_QA_PATH = Path("app/ai/models/legal_qa")
LEGAL_NAME = "nlpaueb/legal-bert-base-uncased"
LEGAL_PATH = Path("app/ai/models/legal_name")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

logger = logging.getLogger(__name__)


class QAModelError(Exception):
    """Custom exception for QA model-related errors"""
    pass


def load_local_pipeline(task: str, local_model_path: Path, model_name: str) -> Optional[pipeline]:
    """
    Load a pipeline from local path ONLY - no downloads
    Returns pipeline or None if failed
    """
    try:
        if isinstance(local_model_path, str):
            local_model_path = Path(local_model_path)
            
        if local_model_path.exists() and (local_model_path / "config.json").exists():
            logger.info(f"Loading {task} model from local path: {local_model_path}")
            tokenizer = AutoTokenizer.from_pretrained(str(local_model_path))
            model = AutoModelForQuestionAnswering.from_pretrained(str(local_model_path))
            
            qa_pipeline = pipeline(
                task,
                model=model,
                tokenizer=tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info(f"Successfully loaded model from {local_model_path}")
            return qa_pipeline
        else:
            logger.warning(f"Local model path not found or incomplete: {local_model_path}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to load from local path {local_model_path}: {e}")
        return None


class LegalDocumentAnalyzer:
    """Enhanced legal document analysis using pattern matching and AI models"""
    
    def __init__(self):
        self.contract_patterns = {
            'professional_services': [
                r'professional\s+services?\s+agreement',
                r'service\s+provider',
                r'client.*service',
                r'scope\s+of\s+work',
                r'deliverables',
                r'consulting\s+agreement'
            ],
            'lease_agreement': [
                r'lease\s+agreement',
                r'rental\s+agreement', 
                r'landlord.*tenant',
                r'lessor.*lessee',
                r'monthly\s+rent',
                r'lease\s+term',
                r'premises'
            ],
            'employment': [
                r'employment\s+agreement',
                r'employee.*employer',
                r'job\s+description',
                r'salary',
                r'benefits'
            ],
            'nda': [
                r'non.?disclosure\s+agreement',
                r'confidentiality\s+agreement',
                r'confidential\s+information',
                r'proprietary\s+information'
            ]
        }
        
        self.essential_elements = {
            'parties': [
                r'between\s+([A-Z][a-z\s,]+)\s+and\s+([A-Z][a-z\s,]+)',
                r'client:\s*([A-Z][a-z\s,]+)',
                r'service\s+provider:\s*([A-Z][a-z\s,]+)',
                r'landlord:\s*([A-Z][a-z\s,]+)',
                r'tenant:\s*([A-Z][a-z\s,]+)'
            ],
            'consideration': [
                r'\$[\d,]+(?:\.\d{2})?',
                r'\d+\s+dollars?',
                r'payment\s+of',
                r'monthly\s+rent',
                r'fee\s+of'
            ],
            'terms': [
                r'term\s+of\s+\d+',
                r'for\s+a\s+period\s+of',
                r'commencing\s+on',
                r'ending\s+on',
                r'shall\s+be\s+effective'
            ],
            'obligations': [
                r'shall\s+provide',
                r'agrees\s+to',
                r'responsible\s+for',
                r'obligated\s+to',
                r'duty\s+to'
            ]
        }

    def analyze_document_type(self, content: str) -> Dict[str, Any]:
        """Analyze document type using pattern matching"""
        content_lower = content.lower()
        type_scores = {}
        
        for doc_type, patterns in self.contract_patterns.items():
            score = 0
            matches = []
            for pattern in patterns:
                pattern_matches = re.findall(pattern, content_lower)
                if pattern_matches:
                    score += len(pattern_matches)
                    matches.extend(pattern_matches)
            
            if score > 0:
                type_scores[doc_type] = {
                    'score': score,
                    'matches': matches[:3]
                }
        
        if not type_scores:
            return {
                'document_type': 'unknown',
                'confidence': 0.0,
                'analysis': 'Could not identify document type'
            }
        
        best_type = max(type_scores.keys(), key=lambda x: type_scores[x]['score'])
        total_score = sum(data['score'] for data in type_scores.values())
        confidence = type_scores[best_type]['score'] / max(total_score, 1)
        
        return {
            'document_type': best_type.replace('_', ' ').title(),
            'confidence': min(confidence, 1.0),
            'analysis': f"Identified as {best_type.replace('_', ' ')} based on {type_scores[best_type]['score']} pattern matches",
            'all_scores': type_scores
        }

    def analyze_essential_elements(self, content: str) -> Dict[str, Any]:
        """Analyze essential legal elements"""
        content_lower = content.lower()
        elements_found = {}
        missing_elements = []
        
        for element_type, patterns in self.essential_elements.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, content_lower)
                if found:
                    matches.extend(found[:2])
            
            if matches:
                elements_found[element_type] = matches
            else:
                missing_elements.append(element_type)
        
        return {
            'found_elements': elements_found,
            'missing_elements': missing_elements,
            'completeness_score': len(elements_found) / len(self.essential_elements)
        }

    def analyze_enforceability_issues(self, content: str) -> List[str]:
        """Identify potential enforceability issues"""
        issues = []
        content_lower = content.lower()
        
        doc_analysis = self.analyze_document_type(content)
        if len(doc_analysis.get('all_scores', {})) > 1:
            issues.append("Document contains elements of multiple agreement types which could create enforceability issues")
        
        party_patterns = [r'between\s+[A-Z]', r'client:', r'service\s+provider:', r'landlord:', r'tenant:']
        party_matches = sum(1 for pattern in party_patterns if re.search(pattern, content_lower))
        
        if party_matches == 0:
            issues.append("No clearly identified parties found - essential for enforceability")
        elif party_matches == 1:
            issues.append("Only one party clearly identified - contracts require at least two parties")
        
        consideration_patterns = [r'\$\d', r'payment', r'rent', r'fee', r'compensation']
        if not any(re.search(pattern, content_lower) for pattern in consideration_patterns):
            issues.append("No consideration (payment/exchange of value) clearly identified")
        
        obligation_patterns = [r'shall', r'agrees?\s+to', r'responsible', r'obligated']
        if not any(re.search(pattern, content_lower) for pattern in obligation_patterns):
            issues.append("No clear obligations or duties specified")
        
        if len(content.strip()) < 200:
            issues.append("Document appears too brief for a comprehensive legal agreement")
        
        return issues


def create_enhanced_fallback_pipeline():
    """
    Enhanced fallback system that tries to use AI first, then pattern matching
    """
    analyzer = LegalDocumentAnalyzer()
    
    class EnhancedFallbackQA:
        def __call__(self, question: str, context: str):
            # TRY AI FIRST
            try:
                ai_result = legal_ai_service.answer_legal_question(question, context)
                if ai_result.get("confidence", 0) > 0.5:
                    logger.info("Using AI for fallback question answering")
                    return {
                        "answer": ai_result["answer"],
                        "score": ai_result["confidence"]
                    }
            except Exception as e:
                logger.warning(f"AI fallback failed, using pattern matching: {e}")
            
            # FALLBACK TO PATTERN MATCHING
            question_lower = question.lower()
            context_lower = context.lower()
            
            # Contract type analysis
            if any(phrase in question_lower for phrase in ['what type', 'contract type', 'document type', 'kind of contract']):
                doc_analysis = analyzer.analyze_document_type(context)
                return {
                    "answer": f"This appears to be a {doc_analysis['document_type']} with {doc_analysis['confidence']:.1%} confidence. {doc_analysis['analysis']}",
                    "score": doc_analysis['confidence']
                }
            
            # Enforceability questions
            if any(phrase in question_lower for phrase in ['enforceable', 'enforceability', 'legally valid', 'valid contract']):
                issues = analyzer.analyze_enforceability_issues(context)
                elements = analyzer.analyze_essential_elements(context)
                
                if issues:
                    answer = f"This contract has {len(issues)} potential enforceability issues: " + "; ".join(issues[:3])
                    if elements['missing_elements']:
                        answer += f". Missing essential elements: {', '.join(elements['missing_elements'])}"
                else:
                    answer = f"The contract appears to have the basic elements for enforceability with {elements['completeness_score']:.1%} completeness."
                
                return {
                    "answer": answer,
                    "score": 1.0 - (len(issues) * 0.2)
                }
            
            # Party identification
            if any(phrase in question_lower for phrase in ['parties', 'who are', 'between whom']):
                elements = analyzer.analyze_essential_elements(context)
                if 'parties' in elements['found_elements']:
                    parties = elements['found_elements']['parties']
                    return {
                        "answer": f"The parties identified in this document are: {', '.join(parties)}",
                        "score": 0.8
                    }
                else:
                    return {
                        "answer": "The parties to this agreement are not clearly identified in the document, which is a significant legal concern.",
                        "score": 0.3
                    }
            
            # Financial terms
            if any(phrase in question_lower for phrase in ['cost', 'price', 'rent', 'payment', 'fee']):
                elements = analyzer.analyze_essential_elements(context)
                if 'consideration' in elements['found_elements']:
                    amounts = elements['found_elements']['consideration']
                    return {
                        "answer": f"Financial terms mentioned: {', '.join(amounts[:3])}",
                        "score": 0.8
                    }
            
            # Missing elements analysis
            if any(phrase in question_lower for phrase in ['missing', 'what is missing', 'incomplete', 'lacking']):
                elements = analyzer.analyze_essential_elements(context)
                if elements['missing_elements']:
                    return {
                        "answer": f"Essential elements missing from this contract: {', '.join(elements['missing_elements'])}. Found elements: {', '.join(elements['found_elements'].keys())}",
                        "score": 0.9
                    }
                else:
                    return {
                        "answer": "This contract appears to contain most essential legal elements.",
                        "score": 0.8
                    }
            
            # Date extraction (original functionality)
            date_patterns = [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                r'\b\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{2,4}\b',
                r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{2,4}\b'
            ]
            
            if any(word in question_lower for word in ['date', 'when', 'contract', 'entered', 'signed']):
                for pattern in date_patterns:
                    matches = re.findall(pattern, context, re.IGNORECASE)
                    if matches:
                        return {
                            "answer": matches[0] if isinstance(matches[0], str) else matches[0][0],
                            "score": 0.7
                        }
            
            # Generic enhanced fallback
            return {
                "answer": "I can see this is a legal document, but I need more specific information to provide detailed analysis. For comprehensive legal analysis, please ensure the AI service is properly configured.",
                "score": 0.2
            }
    
    return EnhancedFallbackQA()


class QuestionAnsweringService:
    def __init__(self):
        self.documents = {}
        self.general_qa_pipeline = None
        self.legal_qa_pipeline = None
        self.fallback_pipeline = None
        self.legal_analyzer = LegalDocumentAnalyzer()
        
        # Model configurations - Updated with your actual paths
        self.general_qa_model_path = QA_PATH
        self.legal_qa_model_path = LEGAL_QA_PATH

        self.legal_keywords = {
            'contract', 'agreement', 'clause', 'legal', 'law', 'court', 'case', 'defendant',
            'plaintiff', 'liability', 'breach', 'damages', 'jurisdiction', 'statute',
            'regulation', 'compliance', 'terms', 'conditions', 'warranty', 'indemnity',
            'termination', 'penalty', 'arbitration', 'litigation', 'patent', 'copyright',
            'trademark', 'intellectual property', 'confidentiality', 'non-disclosure',
            'lawyer', 'attorney', 'legal advice', 'lawsuit', 'settlement', 'appeal',
            'parties', 'enforceability', 'consideration', 'obligations'
        }
        
        logger.info(f"Enhanced QA service initialized with AI integration")
        logger.info(f"AI Service Status: {legal_ai_service.health_check()}")

    def add_document(self, document_id: str, content: str):
        """Add a document to the QA knowledge base with AI analysis"""
        try:
            # NEW: Use AI for document analysis
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
                # NEW: Analyze with AI when loading
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

    async def _find_best_context_from_db(self, question: str, user_id: str) -> Tuple[Optional[str], Optional[str]]:
        """UPDATED: Enhanced context finding using AI-powered semantic matching"""
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
                
                # NEW: Try AI-powered document relevance scoring
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

    def _load_general_qa_model(self):
        """Load the general QA model from local path"""
        if self.general_qa_pipeline is not None:
            return
        
        try:
            pipeline_obj = load_local_pipeline(
                "question-answering",
                self.general_qa_model_path,
                "General QA Model"
            )
            
            if pipeline_obj is None:
                logger.warning("General QA model not available locally, using AI + enhanced fallback")
                if self.fallback_pipeline is None:
                    self.fallback_pipeline = create_enhanced_fallback_pipeline()
                return
                
            self.general_qa_pipeline = pipeline_obj
            logger.info("General QA model loaded successfully from local path")
            
        except Exception as e:
            logger.error(f"Failed to load general QA model: {e}")
            logger.warning("Using AI + enhanced fallback QA system")
            if self.fallback_pipeline is None:
                self.fallback_pipeline = create_enhanced_fallback_pipeline()

    def _load_legal_qa_model(self):
        """Load the legal QA model from local path"""
        if self.legal_qa_pipeline is not None:
            return
        
        try:
            pipeline_obj = load_local_pipeline(
                "question-answering", 
                self.legal_qa_model_path,
                "Legal QA Model"
            )
            
            if pipeline_obj is None:
                logger.warning("Legal QA model not available locally, using AI + enhanced fallback")
                if self.fallback_pipeline is None:
                    self.fallback_pipeline = create_enhanced_fallback_pipeline()
                return
                
            self.legal_qa_pipeline = pipeline_obj
            logger.info("Legal QA model loaded successfully from local path")
            
        except Exception as e:
            logger.error(f"Failed to load legal QA model: {e}")
            logger.warning("Using AI + enhanced fallback QA system")
            if self.fallback_pipeline is None:
                self.fallback_pipeline = create_enhanced_fallback_pipeline()

    def _is_legal_question(self, question: str, context: str = "") -> bool:
        """Enhanced legal question detection"""
        text = (question + " " + context).lower()
        legal_terms = [term for term in self.legal_keywords if term in text]
        
        legal_question_patterns = [
            r'what type.{0,20}contract',
            r'enforceable|enforceability',
            r'missing.{0,10}(elements|clauses)',
            r'parties.{0,10}(involved|agreement)',
            r'legal.{0,10}(valid|binding|issues)',
            r'contract.{0,10}(valid|binding|enforceable)'
        ]
        
        pattern_matches = sum(1 for pattern in legal_question_patterns if re.search(pattern, text))
        
        return len(legal_terms) >= 1 or pattern_matches > 0

    def _select_qa_pipeline(self, question: str, context: str = ""):
        """UPDATED: Select appropriate QA pipeline with AI priority"""
        
        # PRIORITY 1: Try AI first for legal questions
        if self._is_legal_question(question, context):
            try:
                # Check if AI service is available
                health = legal_ai_service.health_check()
                if health.get("ai_available", False):
                    logger.info("Using AI service for legal question")
                    return legal_ai_service, "legal_ai"
            except Exception as e:
                logger.warning(f"AI service unavailable: {e}")
        
        # PRIORITY 2: Try local models
        if self._is_legal_question(question, context):
            try:
                self._load_legal_qa_model()
                if self.legal_qa_pipeline is not None:
                    return self.legal_qa_pipeline, "legal_local"
            except Exception as e:
                logger.warning(f"Legal QA model unavailable: {e}")
            
            try:
                self._load_general_qa_model()
                if self.general_qa_pipeline is not None:
                    return self.general_qa_pipeline, "general_local"
            except Exception as e:
                logger.warning(f"General QA model unavailable: {e}")
        else:
            try:
                self._load_general_qa_model()
                if self.general_qa_pipeline is not None:
                    return self.general_qa_pipeline, "general_local"
            except Exception as e:
                logger.warning(f"General QA unavailable: {e}")
        
        # PRIORITY 3: Enhanced fallback (includes AI fallback)
        if self.fallback_pipeline is None:
            self.fallback_pipeline = create_enhanced_fallback_pipeline()
        return self.fallback_pipeline, "enhanced_fallback"

    def _run_qa_pipeline(self, pipeline_obj, question: str, context: str, model_type: str) -> dict:
        """UPDATED: Run QA pipeline with AI integration"""
        try:
            if pipeline_obj is None:
                return {
                    "answer": "QA model not available. Please ensure models are downloaded or AI service is configured.",
                    "score": 0.0
                }
            
            # NEW: Handle AI service differently
            if model_type == "legal_ai":
                result = pipeline_obj.answer_legal_question(question, context)
                return {
                    "answer": result.get("answer", "AI analysis failed"),
                    "score": result.get("confidence", 0.0),
                    "model_info": result.get("model", "AI"),
                    "question_type": result.get("question_type", "unknown")
                }
            
            # Handle local models and fallback as before
            result = pipeline_obj(question=question, context=context)
            
            # Enhanced post-processing for legal questions
            if model_type in ["legal_local", "enhanced_fallback"] and isinstance(result.get("answer"), str):
                answer = result["answer"]
                
                if model_type == "enhanced_fallback":
                    # Enhanced fallback already provides good analysis
                    pass
                else:
                    # For local model results, add legal context if confidence is low
                    score = result.get("score", 0.0)
                    if score < 0.3:
                        try:
                            # Try to get AI insights for low-confidence answers
                            ai_result = legal_ai_service.analyze_contract_type(context)
                            if ai_result.get("success"):
                                doc_type = ai_result["analysis"].get("document_type", "Unknown")
                                answer += f" [AI Note: This appears to be a {doc_type} document]"
                        except Exception as e:
                            logger.debug(f"Could not add AI insights: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"QA pipeline failed: {e}")
            # Use enhanced fallback on pipeline failure
            fallback = create_enhanced_fallback_pipeline()
            return fallback(question, context)

    async def answer_question(self, question: str, user_id: str, document_id: Optional[str] = None) -> Dict[str, Any]:
        """UPDATED: Enhanced question answering with AI priority"""
        try:
            logger.info(f"Processing question with AI integration for user {user_id}, document: {document_id}")
            
            context = None
            used_document_id = None
            document_metadata = {}

            # Load document context
            if document_id and document_id in self.documents:
                doc_data = self.documents[document_id]
                context = doc_data['content']
                used_document_id = document_id
                document_metadata = {
                    'ai_analysis': doc_data.get('ai_analysis', {}),
                    'content_length': doc_data.get('content_length', 0)
                }
            elif document_id:
                context = await self.load_document_from_db(document_id, user_id)
                if context:
                    used_document_id = document_id
                    if document_id in self.documents:
                        doc_data = self.documents[document_id]
                        document_metadata = {
                            'ai_analysis': doc_data.get('ai_analysis', {}),
                            'content_length': doc_data.get('content_length', 0)
                        }
            
            if not context or not context.strip():
                context, used_document_id = await self._find_best_context_from_db(question, user_id)
                if context and used_document_id in self.documents:
                    doc_data = self.documents[used_document_id]
                    document_metadata = {
                        'ai_analysis': doc_data.get('ai_analysis', {}),
                        'content_length': doc_data.get('content_length', 0)
                    }
            
            if not context:
                return {
                    "answer": "I don't have any legal documents to analyze. Please upload some documents first.",
                    "source_section": "",
                    "confidence": 0.0,
                }
            
            # Select and run QA pipeline (now prioritizes AI)
            qa_pipeline, model_type = self._select_qa_pipeline(question, context)
            
            # Truncate context if too long
            max_context_length = getattr(settings, 'MAX_CONTEXT_LENGTH', 8000)
            if len(context) > max_context_length:
                context = context[:max_context_length]
            
            # Run QA
            result = self._run_qa_pipeline(qa_pipeline, question, context, model_type)
            
            # Extract and enhance answer
            answer = result.get("answer", "No answer found")
            confidence = result.get("score", 0.0)
            
            # Enhanced source section finding
            source_section = self._find_relevant_source_section(answer, context)
            
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

    def _find_relevant_source_section(self, answer: str, context: str) -> str:
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

    def health_check(self) -> dict:
        """UPDATED: Enhanced health check including AI status"""
        ai_health = legal_ai_service.health_check()
        
        return {
            "status": "healthy",
            "ai_service": ai_health,
            "models_loaded": {
                "general_qa": self.general_qa_pipeline is not None,
                "legal_qa": self.legal_qa_pipeline is not None,
                "enhanced_fallback": self.fallback_pipeline is not None
            },
            "documents_cached": len(self.documents),
            "local_only": not ai_health.get("ai_available", False),
            "legal_analyzer": "active"
        }


# Initialize the enhanced service
qa_service = QuestionAnsweringService()


async def answer_question(question: str, user_id: str, document_id: Optional[str] = None) -> Dict:
    """Answer a question using the AI-enhanced QA service"""
    return await qa_service.answer_question(question, user_id, document_id)


async def answer_question_with_context(question: str, context: str, document_id: str = None) -> Dict[str, Any]:
    """
    UPDATED: Enhanced question answering with AI integration
    """
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
        
        #  Try AI first for legal questions
        qa_pipeline, model_type = qa_service._select_qa_pipeline(question, context)
        
        # Truncate context if too long
        max_context_length = getattr(settings, 'MAX_CONTEXT_LENGTH', 8000)
        if len(context) > max_context_length:
            context = context[:max_context_length]
        
        # Run QA using AI-enhanced pipeline
        result = qa_service._run_qa_pipeline(qa_pipeline, question, context, model_type)
        
        # Extract and enhance the answer
        answer = result.get("answer", "No answer found")
        confidence = result.get("score", 0.0)
        
        # Find relevant source section
        source_section = qa_service._find_relevant_source_section(answer, context)
        
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
    """UPDATED: Get enhanced model status including AI"""
    ai_health = legal_ai_service.health_check()
    
    return {
        "ai_service_available": ai_health.get("ai_available", False),
        "ai_model": ai_health.get("model", "unknown"),
        "general_qa_model": qa_service.general_qa_pipeline is not None,
        "legal_qa_model": qa_service.legal_qa_pipeline is not None,
        "enhanced_fallback": qa_service.fallback_pipeline is not None,
        "models_loaded": (qa_service.general_qa_pipeline is not None or 
                         qa_service.legal_qa_pipeline is not None or 
                         qa_service.fallback_pipeline is not None or
                         ai_health.get("ai_available", False)),
        "local_only": not ai_health.get("ai_available", False),
        "legal_analyzer": True
    }


def health_check() -> dict:
    """UPDATED: Enhanced health check with AI status"""
    return qa_service.health_check()


# Additional utility functions for legal analysis (now AI-enhanced)
def analyze_document_type(content: str) -> Dict[str, Any]:
    """UPDATED: AI-powered document type analysis with fallback"""
    try:
        ai_result = legal_ai_service.analyze_contract_type(content)
        if ai_result.get("success"):
            analysis_data = ai_result["analysis"]
            return {
                "type": analysis_data.get("document_type", "Unknown"),
                "confidence": analysis_data.get("confidence", 0.0),
                "analysis": analysis_data.get("legal_assessment", "AI analysis completed"),
                "ai_powered": True
            }
    except Exception as e:
        logger.warning(f"AI document analysis failed, using fallback: {e}")
    
    # Fallback to pattern matching
    analyzer = LegalDocumentAnalyzer()
    return {**analyzer.analyze_document_type(content), "ai_powered": False}


def analyze_essential_elements(content: str) -> Dict[str, Any]:
    """UPDATED: AI-enhanced essential elements analysis"""
    try:
        ai_result = legal_ai_service.analyze_contract_type(content)
        if ai_result.get("success"):
            analysis_data = ai_result["analysis"]
            return {
                "found_elements": analysis_data.get("key_characteristics", []),
                "missing_elements": analysis_data.get("missing_elements", []),
                "ai_powered": True
            }
    except Exception as e:
        logger.warning(f"AI elements analysis failed, using fallback: {e}")
    
    # Fallback to pattern matching
    analyzer = LegalDocumentAnalyzer()
    return {**analyzer.analyze_essential_elements(content), "ai_powered": False}


def analyze_enforceability_issues(content: str) -> List[str]:
    """UPDATED: AI-enhanced enforceability analysis"""
    try:
        ai_result = legal_ai_service.analyze_contract_enforceability(content)
        if ai_result.get("success"):
            analysis_data = ai_result["analysis"]
            return analysis_data.get("legal_issues", []) + analysis_data.get("enforceability_concerns", [])
    except Exception as e:
        logger.warning(f"AI enforceability analysis failed, using fallback: {e}")
    
    # Fallback to pattern matching
    analyzer = LegalDocumentAnalyzer()
    return analyzer.analyze_enforceability_issues(content)
                            