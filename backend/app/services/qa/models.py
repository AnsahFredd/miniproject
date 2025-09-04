"""
Model loading and pipeline management
"""
from pathlib import Path
from typing import Optional, Tuple, Any
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline
import torch
import logging
import re
from .config import QA_PATH, LEGAL_QA_PATH, LEGAL_KEYWORDS, DEVICE, LEGAL_QUESTION_PATTERNS, QAModelError
from ..legal_ai_service import legal_ai_service

logger = logging.getLogger(__name__)

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


class PipelineManager:
    """Manages QA pipeline selection and loading"""
    
    def __init__(self):
        self.general_qa_pipeline = None
        self.legal_qa_pipeline = None
        self.fallback_pipeline = None
        self.legal_keywords = LEGAL_KEYWORDS
        self.legal_question_patterns = LEGAL_QUESTION_PATTERNS
    
    def is_legal_question(self, question: str, context: str = "") -> bool:
        """Enhanced legal question detection"""
        text = (question + " " + context).lower()
        legal_terms = [term for term in self.legal_keywords if term in text]
        
        pattern_matches = sum(1 for pattern in self.legal_question_patterns if re.search(pattern, text))
        
        return len(legal_terms) >= 1 or pattern_matches > 0
    
    def select_qa_pipeline(self, question: str, context: str = "") -> Tuple[Any, str]:
        """Select appropriate QA pipeline with AI priority"""
        
        # PRIORITY 1: Try AI first for legal questions
        if self.is_legal_question(question, context):
            try:
                # Check if AI service is available
                health = legal_ai_service.health_check()
                if health.get("ai_available", False):
                    logger.info("Using AI service for legal question")
                    return legal_ai_service, "legal_ai"
            except Exception as e:
                logger.warning(f"AI service unavailable: {e}")
        
        # PRIORITY 2: Try local models
        if self.is_legal_question(question, context):
            try:
                self.load_legal_qa_model()
                if self.legal_qa_pipeline is not None:
                    return self.legal_qa_pipeline, "legal_local"
            except Exception as e:
                logger.warning(f"Legal QA model unavailable: {e}")
            
            try:
                self.load_general_qa_model()
                if self.general_qa_pipeline is not None:
                    return self.general_qa_pipeline, "general_local"
            except Exception as e:
                logger.warning(f"General QA model unavailable: {e}")
        else:
            try:
                self.load_general_qa_model()
                if self.general_qa_pipeline is not None:
                    return self.general_qa_pipeline, "general_local"
            except Exception as e:
                logger.warning(f"General QA unavailable: {e}")
        
        # PRIORITY 3: Enhanced fallback (includes AI fallback)
        if self.fallback_pipeline is None:
            self.fallback_pipeline = create_enhanced_fallback_pipeline()
        return self.fallback_pipeline, "enhanced_fallback"
    
    def load_general_qa_model(self):
        """Load the general QA model from local path"""
        if self.general_qa_pipeline is not None:
            return
        
        try:
            pipeline_obj = load_local_pipeline(
                "question-answering",
                QA_PATH,
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
    
    def load_legal_qa_model(self):
        """Load the legal QA model from local path"""
        if self.legal_qa_pipeline is not None:
            return
        
        try:
            pipeline_obj = load_local_pipeline(
                "question-answering", 
                LEGAL_QA_PATH,
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

    def run_qa_pipeline(self, pipeline_obj, question: str, context: str, model_type: str) -> dict:
        """Run QA pipeline with AI integration"""
        try:
            if pipeline_obj is None:
                return {
                    "answer": "QA model not available. Please ensure models are downloaded or AI service is configured.",
                    "score": 0.0
                }
            
            # Handle AI service differently
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

    def get_model_status(self) -> dict:
        """Get model loading status"""
        ai_health = legal_ai_service.health_check()
        
        return {
            "ai_service_available": ai_health.get("ai_available", False),
            "ai_model": ai_health.get("model", "unknown"),
            "general_qa_model": self.general_qa_pipeline is not None,
            "legal_qa_model": self.legal_qa_pipeline is not None,
            "enhanced_fallback": self.fallback_pipeline is not None,
            "models_loaded": (self.general_qa_pipeline is not None or 
                             self.legal_qa_pipeline is not None or 
                             self.fallback_pipeline is not None or
                             ai_health.get("ai_available", False)),
            "local_only": not ai_health.get("ai_available", False)
        }


def create_enhanced_fallback_pipeline():
    """Enhanced fallback system that tries to use AI first, then pattern matching"""
    from .analyzer import LegalDocumentAnalyzer
    from .config import DATE_PATTERNS
    
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
            if any(word in question_lower for word in ['date', 'when', 'contract', 'entered', 'signed']):
                for pattern in DATE_PATTERNS:
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