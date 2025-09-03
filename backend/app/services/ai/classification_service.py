"""Refactored classification service using the new AI service architecture."""

import logging
from typing import Dict, Any, List, Optional
from ..base.ai_service import BaseAIService, InferenceError


logger = logging.getLogger(__name__)

class ClassificationService(BaseAIService):
    """Document classification service with HuggingFace API and local model fallback."""
    
    def __init__(self):
        super().__init__("classification", ModelType.CLASSIFICATION)
        self.document_types = {
            "contract", "lease", "legal_brief", "policy", "regulation", 
            "financial", "correspondence", "report", "general"
        }
        self.legal_domains = {
            "corporate", "real_estate", "employment", "intellectual_property",
            "litigation", "regulatory", "tax", "general"
        }
        self.urgency_keywords = {
            "high": ["urgent", "immediate", "asap", "deadline", "expires", "critical"],
            "medium": ["important", "priority", "soon", "review", "attention"],
            "low": ["routine", "standard", "regular", "normal"]
        }
    
    async def _process_with_api(self, model_url: str, text: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Process using HuggingFace API."""
        try:
            result = hf_client.classify(model_url, text)
            return result
        except Exception as e:
            self.logger.error(f"HF API classification failed: {e}")
            return None
    
    async def _process_with_local_model(self, model_instance: Any, text: str, **kwargs) -> Dict[str, Any]:
        """Process using local model."""
        try:
            if hasattr(model_instance, '__call__'):
                # Pipeline object
                result = model_instance(text)
                
                if isinstance(result, list) and len(result) > 0:
                    # Handle both single and multiple predictions
                    predictions = result[0] if isinstance(result[0], list) else result
                    best_prediction = max(predictions, key=lambda x: x.get('score', 0))
                    
                    return {
                        "document_type": self._map_classification_label(best_prediction.get('label', 'unknown')),
                        "confidence": float(best_prediction.get('score', 0.0)),
                        "raw_predictions": predictions
                    }
                else:
                    raise InferenceError("Invalid model output format")
            else:
                raise InferenceError("Invalid model instance")
                
        except Exception as e:
            self.logger.error(f"Local model classification failed: {e}")
            raise InferenceError(f"Local classification failed: {str(e)}")
    
    async def _fallback_processing(self, text: str, filename: str = "", **kwargs) -> Optional[Dict[str, Any]]:
        """Fallback processing using rule-based classification."""
        try:
            return self._rule_based_classify(text, filename)
        except Exception as e:
            self.logger.error(f"Fallback processing failed: {e}")
            return None
    
    def _rule_based_classify(self, text: str, filename: str = "") -> Dict[str, Any]:
        """Rule-based classification fallback."""
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # Document type classification
        doc_type = "general"
        confidence = 0.3
        
        # Check filename first
        if "contract" in filename_lower:
            doc_type = "contract"
            confidence = 0.7
        elif "lease" in filename_lower:
            doc_type = "lease"
            confidence = 0.7
        elif "brief" in filename_lower:
            doc_type = "legal_brief"
            confidence = 0.7
        else:
            # Check content
            contract_keywords = ["agreement", "contract", "party", "whereas", "terms", "conditions"]
            lease_keywords = ["lease", "tenant", "landlord", "rent", "premises"]
            brief_keywords = ["brief", "court", "case", "plaintiff", "defendant"]
            
            contract_score = sum(1 for kw in contract_keywords if kw in text_lower)
            lease_score = sum(1 for kw in lease_keywords if kw in text_lower)
            brief_score = sum(1 for kw in brief_keywords if kw in text_lower)
            
            if contract_score >= 3:
                doc_type = "contract"
                confidence = min(0.8, 0.4 + contract_score * 0.1)
            elif lease_score >= 2:
                doc_type = "lease"
                confidence = min(0.8, 0.4 + lease_score * 0.1)
            elif brief_score >= 2:
                doc_type = "legal_brief"
                confidence = min(0.8, 0.4 + brief_score * 0.1)
        
        # Legal domain classification
        legal_domain = "general"
        domain_confidence = 0.3
        
        domain_keywords = {
            "corporate": ["corporation", "company", "business", "merger", "acquisition"],
            "real_estate": ["property", "real estate", "land", "building", "premises"],
            "employment": ["employee", "employment", "work", "salary", "benefits"],
            "intellectual_property": ["patent", "trademark", "copyright", "ip", "intellectual"]
        }
        
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score >= 2:
                legal_domain = domain
                domain_confidence = min(0.8, 0.4 + score * 0.1)
                break
        
        # Urgency classification
        urgency = "low"
        urgency_confidence = 0.5
        
        for level, keywords in self.urgency_keywords.items():
            if any(kw in text_lower for kw in keywords):
                urgency = level
                urgency_confidence = 0.7
                break
        
        return {
            "document_type": doc_type,
            "document_type_confidence": confidence,
            "legal_domain": legal_domain,
            "legal_domain_confidence": domain_confidence,
            "urgency": urgency,
            "urgency_confidence": urgency_confidence,
            "classification_method": "rule_based",
            "extracted_entities": [],
            "complexity_metrics": self._analyze_complexity(text)
        }
    
    def _analyze_complexity(self, text: str) -> Dict[str, Any]:
        """Simple complexity analysis."""
        words = text.split()
        sentences = text.split('.')
        
        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_words_per_sentence": len(words) / max(len(sentences), 1),
            "complexity_score": min(1.0, len(words) / 1000)  # Simple metric
        }
    
    def _map_classification_label(self, label: str) -> str:
        """Map model labels to document types."""
        mapping = {
            "contract": "contract",
            "agreement": "contract",
            "lease": "lease",
            "brief": "legal_brief",
            "policy": "policy",
            "regulation": "regulation",
            "financial": "financial",
            "correspondence": "correspondence",
            "report": "report"
        }
        
        label_lower = label.lower()
        for key, value in mapping.items():
            if key in label_lower:
                return value
        
        return "general"
    
    async def classify_document(self, content: str, filename: str = "") -> Dict[str, Any]:
        """Main classification method."""
        if not content or len(content.strip()) < 50:
            return self._rule_based_classify(content, filename)
        
        try:
            # Try ML classification first
            ml_result = await self._process_with_fallback(content, filename=filename)
            
            if ml_result and ml_result.get("confidence", 0) > 0.6:
                # Enhance ML result with rule-based features
                rule_result = self._rule_based_classify(content, filename)
                
                # Merge results
                enhanced_result = ml_result.copy()
                enhanced_result.update({
                    "legal_domain": rule_result.get("legal_domain", "general"),
                    "legal_domain_confidence": rule_result.get("legal_domain_confidence", 0.3),
                    "urgency": rule_result.get("urgency", "low"),
                    "urgency_confidence": rule_result.get("urgency_confidence", 0.5),
                    "classification_method": "model_enhanced",
                    "complexity_metrics": rule_result.get("complexity_metrics", {})
                })
                
                return enhanced_result
            else:
                # Fall back to rule-based
                return self._rule_based_classify(content, filename)
                
        except Exception as e:
            self.logger.error(f"Classification failed: {e}")
            return self._rule_based_classify(content, filename)
    
    async def batch_classify(self, documents: List[Dict]) -> List[Dict]:
        """Classify multiple documents."""
        results = []
        for i, doc in enumerate(documents):
            try:
                result = await self.classify_document(
                    doc.get('content', ''), 
                    doc.get('filename', '')
                )
                result['document_id'] = doc.get('id', i)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Batch classification failed for doc {i}: {e}")
                results.append({
                    'document_id': doc.get('id', i),
                    'error': str(e),
                    'classification_method': 'error'
                })
        return results
    
    async def _health_check_test(self) -> Dict[str, Any]:
        """Health check test for classification service."""
        test_content = "This is a legal contract between Party A and Party B for the provision of services. The agreement outlines terms and conditions for both parties."
        
        try:
            result = await self.classify_document(test_content, "test_contract.pdf")
            
            success = (
                result and
                result.get("document_type") != "unknown" and
                result.get("document_type_confidence", 0) > 0 and
                "classification_method" in result
            )
            
            return {
                "success": success,
                "test_result": {
                    "document_type": result.get("document_type"),
                    "confidence": result.get("document_type_confidence"),
                    "method": result.get("classification_method")
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
