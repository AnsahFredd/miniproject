import logging
from typing import Dict, List, Any
from .model_handler import ModelHandler
from .rule_classifier import RuleBasedClassifier
from .entity_extracter import EntityExtractor
from .complexity_analyzer import ComplexityAnalyzer

logger = logging.getLogger(__name__)

class DocumentClassificationService:
    def __init__(self):
        self.model_handler = ModelHandler()
        self.rule_classifier = RuleBasedClassifier()
        self.entity_extractor = EntityExtractor()
        self.complexity_analyzer = ComplexityAnalyzer()
        
        logger.info("DocumentClassificationService initialized")

    def classify_document(self, content: str, filename: str = "") -> Dict:
        """Main classification method - SYNCHRONOUS VERSION"""
        if not content or len(content.strip()) < 50:
            return self._get_fallback_classification(content, filename)

        # Try model classification - this will be synchronous for now
        try:
            # For synchronous operation, we'll use rule-based approach
            rule_result = self.rule_classifier.classify(content, filename)
            rule_result["extracted_entities"] = self.entity_extractor.extract_entities(content)
            rule_result["complexity_metrics"] = self.complexity_analyzer.analyze_complexity(content)
            rule_result["classification_method"] = "rule_based_sync"
            return rule_result
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return self._get_fallback_classification(content, filename)

    async def classify_document_async(self, content: str, filename: str = "") -> Dict:
        """Main classification method - ASYNC VERSION"""
        if not content or len(content.strip()) < 50:
            return self._get_fallback_classification(content, filename)

        try:
            # Try model classification
            ml_result = await self.model_handler.classify_text(content)
            
            # If model confidence is high, enhance with additional features
            if ml_result.get("confidence", 0) > 0.6:
                rule_features = self.rule_classifier.classify(content, filename)
                entities = self.entity_extractor.extract_entities(content)
                complexity = self.complexity_analyzer.analyze_complexity(content)
                
                # Merge results - be careful with key naming
                enhanced_result = {
                    "document_type": ml_result.get("document_type", "general"),
                    "document_type_confidence": ml_result.get("confidence", 0.0),
                    "legal_domain": rule_features.get("legal_domain", "general"),
                    "legal_domain_confidence": rule_features.get("legal_domain_confidence", 0.0),
                    "urgency": rule_features.get("urgency", "low"),
                    "urgency_confidence": rule_features.get("urgency_confidence", 0.0),
                    "extracted_entities": entities,
                    "complexity_metrics": complexity,
                    "classification_method": "model_enhanced",
                    "model_source": ml_result.get("model_source", "unknown")
                }
                return enhanced_result

            # Fallback to rule-based
            rule_result = self.rule_classifier.classify(content, filename)
            rule_result["extracted_entities"] = self.entity_extractor.extract_entities(content)
            rule_result["complexity_metrics"] = self.complexity_analyzer.analyze_complexity(content)
            rule_result["classification_method"] = "rule_based"
            return rule_result
            
        except Exception as e:
            logger.error(f"Async classification error: {e}")
            # Fallback to rule-based
            rule_result = self.rule_classifier.classify(content, filename)
            rule_result["extracted_entities"] = self.entity_extractor.extract_entities(content)
            rule_result["complexity_metrics"] = self.complexity_analyzer.analyze_complexity(content)
            rule_result["classification_method"] = "rule_based_fallback"
            rule_result["error"] = str(e)
            return rule_result

    def _get_fallback_classification(self, content: str, filename: str) -> Dict:
        """Simple fallback for short content"""
        filename_lower = filename.lower()
        
        if 'contract' in filename_lower:
            doc_type = "contract"
        elif 'lease' in filename_lower:
            doc_type = "lease"
        elif 'brief' in filename_lower:
            doc_type = "legal_brief"
        else:
            doc_type = "general"

        return {
            "document_type": doc_type,
            "document_type_confidence": 0.3,
            "legal_domain": "general",
            "legal_domain_confidence": 0.0,
            "urgency": "low",
            "urgency_confidence": 0.0,
            "classification_method": "fallback",
            "extracted_entities": [],
            "complexity_metrics": self.complexity_analyzer.analyze_complexity(content)
        }

    def batch_classify(self, documents: List[Dict]) -> List[Dict]:
        """Classify multiple documents"""
        results = []
        for i, doc in enumerate(documents):
            result = self.classify_document(doc.get('content', ''), doc.get('filename', ''))
            result['document_id'] = doc.get('id', i)
            results.append(result)
        return results

    async def batch_classify_async(self, documents: List[Dict]) -> List[Dict]:
        """Classify multiple documents - async version"""
        results = []
        for i, doc in enumerate(documents):
            result = await self.classify_document_async(doc.get('content', ''), doc.get('filename', ''))
            result['document_id'] = doc.get('id', i)
            results.append(result)
        return results

    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        try:
            test_content = "This is a legal contract between Party A and Party B."
            result = self.classify_document(test_content, "test_contract.pdf")
            
            is_healthy = (
                result.get("document_type") != "unknown" and
                result.get("document_type_confidence", 0) > 0
            )
            
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "model_info": self.model_handler.get_model_info(),
                "test_result": result if is_healthy else None
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }