import os
import logging
from pathlib import Path
import re
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
from typing import Dict, List, Optional
from app.utils.hf_cache import cache_manager

logger = logging.getLogger(__name__)

# === Load model names from environment variables ===
CLASSIFICATION_MODEL = os.getenv("CLASSIFICATION_MODEL", "AnsahFredd/classification_model")
CLASSIFICATION_MODEL_PATH = os.getenv("CLASSIFICATION_MODEL_PATH", "AnsahFredd/classification_model")

logger.info(f"ClassificationService initialized. Primary: {CLASSIFICATION_MODEL}, fallbacks: ['nlpaueb/legal-bert-base-uncased']")

# === Load Classification Model with cache management ===
classification_pipeline = None

try:
    logger.info(f"🔄 Loading primary classification model: {CLASSIFICATION_MODEL}")
    
    classification_pipeline = cache_manager.load_model_with_retry(
        CLASSIFICATION_MODEL, 
        model_type="classification"
    )
    
    if classification_pipeline:
        logger.info("✅ Primary classification model loaded successfully")
    else:
        raise RuntimeError("Cache manager returned None")
    
except Exception as e:
    logger.error(f"❌ Failed to load primary classification model: {e}")
    
    # Try alternative model
    try:
        logger.info(f"🔄 Loading alternative classification model: {CLASSIFICATION_MODEL_PATH}")
        classification_pipeline = cache_manager.load_model_with_retry(
            CLASSIFICATION_MODEL_PATH, 
            model_type="classification"
        )
        
        if classification_pipeline:
            logger.info("✅ Alternative classification model loaded successfully")
        else:
            raise RuntimeError("Cache manager returned None")
        
    except Exception as e2:
        logger.error(f"❌ Failed to load alternative classification model: {e2}")
        
        # Final fallback - try a general legal BERT model
        try:
            logger.info("🔄 Attempting fallback to nlpaueb/legal-bert-base-uncased...")
            classification_pipeline = cache_manager.load_model_with_retry(
                "nlpaueb/legal-bert-base-uncased", 
                model_type="classification"
            )
            
            if classification_pipeline:
                logger.info("✅ Fallback classification model loaded successfully")
            else:
                raise RuntimeError("Cache manager returned None")
            
        except Exception as fallback_error:
            logger.error(f"❌ Complete failure to load classification model: {fallback_error}")
            classification_pipeline = None


class DocumentClassificationService:
    def __init__(self):
        self.classification_pipeline = classification_pipeline
        
        # Legal document type mapping
        self.document_types = {
            'contract': ['contract', 'agreement', 'deed', 'covenant', 'compact'],
            'lease': ['lease', 'rental', 'tenancy', 'rent'],
            'legal_brief': ['brief', 'motion', 'petition', 'complaint', 'pleading'],
            'policy': ['policy', 'procedure', 'guideline', 'standard', 'protocol'],
            'regulation': ['regulation', 'statute', 'law', 'code', 'ordinance'],
            'financial': ['invoice', 'receipt', 'financial', 'budget', 'statement'],
            'correspondence': ['letter', 'memo', 'email', 'correspondence', 'notice'],
            'report': ['report', 'analysis', 'study', 'review', 'assessment']
        }
        
        # Priority/urgency keywords
        self.urgency_keywords = {
            'high': ['urgent', 'immediate', 'critical', 'emergency', 'deadline', 'expires'],
            'medium': ['important', 'priority', 'attention', 'review', 'action required'],
            'low': ['information', 'fyi', 'reference', 'notice', 'update']
        }
        
        # Legal domain categories
        self.legal_domains = {
            'real_estate': ['property', 'real estate', 'lease', 'rent', 'landlord', 'tenant'],
            'corporate': ['corporation', 'company', 'business', 'merger', 'acquisition'],
            'employment': ['employment', 'employee', 'worker', 'job', 'salary', 'benefits'],
            'intellectual_property': ['patent', 'trademark', 'copyright', 'ip', 'invention'],
            'litigation': ['lawsuit', 'court', 'judge', 'trial', 'plaintiff', 'defendant'],
            'compliance': ['compliance', 'regulation', 'audit', 'violation', 'penalty']
        }
        
        model_status = "loaded" if self.classification_pipeline else "failed"
        logger.info(f"Classification service initialized - model status: {model_status}")
    
    def classify_document(self, content: str, filename: str = "") -> Dict:
        """
        Classify a legal document into various categories.
        
        Args:
            content: Document text content
            filename: Optional filename for additional context
            
        Returns:
            Dictionary with classification results
        """
        if not content or len(content.strip()) < 50:
            return {
                'document_type': 'unknown',
                'document_type_confidence': 0.0,
                'legal_domain': 'general',
                'legal_domain_confidence': 0.0,
                'urgency': 'low',
                'urgency_confidence': 0.0,
                'extracted_entities': [],
                'classification_method': 'fallback'
            }
        
        try:
            # Try ML model classification first
            if self.classification_pipeline:
                ml_result = self._classify_with_model(content)
                if ml_result['document_type_confidence'] > 0.7:
                    # High confidence ML result
                    ml_result.update(self._classify_with_rules(content, filename))
                    ml_result['classification_method'] = 'ml_model'
                    return ml_result
            
            # Fallback to rule-based classification
            rule_result = self._classify_with_rules(content, filename)
            rule_result['classification_method'] = 'rule_based'
            return rule_result
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return self._get_fallback_classification(content, filename)
    
    def _classify_with_model(self, content: str) -> Dict:
        """Use ML model for classification."""
        try:
            # Truncate content to model's max length
            max_length = 512
            if len(content) > max_length:
                content = content[:max_length]
            
            result = self.classification_pipeline(content)
            
            # Process model output
            if isinstance(result, list) and len(result) > 0:
                prediction = result[0]
                label = prediction.get('label', 'unknown').lower()
                confidence = prediction.get('score', 0.0)
                
                # Map model labels to our document types
                document_type = self._map_model_label_to_type(label)
                
                return {
                    'document_type': document_type,
                    'document_type_confidence': confidence,
                    'model_label': label,
                    'raw_prediction': result
                }
            
        except Exception as e:
            logger.error(f"Model classification error: {e}")
        
        return {
            'document_type': 'unknown',
            'document_type_confidence': 0.0
        }
    
    def _classify_with_rules(self, content: str, filename: str = "") -> Dict:
        """Rule-based classification using keyword matching."""
        content_lower = content.lower()
        filename_lower = filename.lower() if filename else ""
        text_to_analyze = content_lower + " " + filename_lower
        
        # Document type classification
        doc_type_scores = {}
        for doc_type, keywords in self.document_types.items():
            score = sum(1 for keyword in keywords if keyword in text_to_analyze)
            if score > 0:
                doc_type_scores[doc_type] = score
        
        best_doc_type = max(doc_type_scores.items(), key=lambda x: x[1]) if doc_type_scores else ('general', 0)
        doc_type_confidence = min(best_doc_type[1] / 3.0, 1.0)  # Normalize to 0-1
        
        # Legal domain classification
        domain_scores = {}
        for domain, keywords in self.legal_domains.items():
            score = sum(1 for keyword in keywords if keyword in text_to_analyze)
            if score > 0:
                domain_scores[domain] = score
        
        best_domain = max(domain_scores.items(), key=lambda x: x[1]) if domain_scores else ('general', 0)
        domain_confidence = min(best_domain[1] / 2.0, 1.0)
        
        # Urgency classification
        urgency_scores = {}
        for urgency, keywords in self.urgency_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_to_analyze)
            if score > 0:
                urgency_scores[urgency] = score
        
        best_urgency = max(urgency_scores.items(), key=lambda x: x[1]) if urgency_scores else ('low', 0)
        urgency_confidence = min(best_urgency[1] / 2.0, 1.0)
        
        # Extract entities
        entities = self._extract_legal_entities(content)
        
        return {
            'document_type': best_doc_type[0],
            'document_type_confidence': doc_type_confidence,
            'legal_domain': best_domain[0],
            'legal_domain_confidence': domain_confidence,
            'urgency': best_urgency[0],
            'urgency_confidence': urgency_confidence,
            'extracted_entities': entities
        }
    
    def _extract_legal_entities(self, content: str) -> List[Dict]:
        """Extract legal entities using regex patterns."""
        entities = []
        
        # Date patterns
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        dates = re.findall(date_pattern, content, re.IGNORECASE)
        for date in dates[:5]:  # Limit to 5 dates
            entities.append({'type': 'date', 'value': date})
        
        # Money amounts
        money_pattern = r'\$[\d,]+(?:\.\d{2})?'
        amounts = re.findall(money_pattern, content)
        for amount in amounts[:5]:  # Limit to 5 amounts
            entities.append({'type': 'money', 'value': amount})
        
        # Legal roles
        role_patterns = {
            'party': r'(?:plaintiff|defendant|appellant|appellee|petitioner|respondent)',
            'legal_entity': r'(?:corporation|llc|inc\.|company|firm)',
            'court': r'(?:court|tribunal|judge|magistrate)'
        }
        
        for entity_type, pattern in role_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches[:3]:  # Limit each type
                entities.append({'type': entity_type, 'value': match})
        
        return entities
    
    def _map_model_label_to_type(self, model_label: str) -> str:
        """Map model output labels to our document types."""
        label_mapping = {
            'contract': 'contract',
            'agreement': 'contract',
            'lease': 'lease',
            'brief': 'legal_brief',
            'motion': 'legal_brief',
            'policy': 'policy',
            'regulation': 'regulation',
            'financial': 'financial',
            'correspondence': 'correspondence',
            'report': 'report'
        }
        
        return label_mapping.get(model_label, 'general')
    
    def _get_fallback_classification(self, content: str, filename: str) -> Dict:
        """Fallback classification when everything else fails."""
        # Very basic classification based on content length and filename
        content_length = len(content.strip())
        
        if 'contract' in filename.lower() or 'agreement' in filename.lower():
            doc_type = 'contract'
        elif 'lease' in filename.lower():
            doc_type = 'lease'
        elif 'brief' in filename.lower() or 'motion' in filename.lower():
            doc_type = 'legal_brief'
        elif content_length > 5000:
            doc_type = 'report'
        else:
            doc_type = 'general'
        
        return {
            'document_type': doc_type,
            'document_type_confidence': 0.3,
            'legal_domain': 'general',
            'legal_domain_confidence': 0.0,
            'urgency': 'low',
            'urgency_confidence': 0.0,
            'extracted_entities': [],
            'classification_method': 'fallback'
        }

    def get_model_info(self) -> dict:
        """Return information about the loaded classification model."""
        try:
            model_name = CLASSIFICATION_MODEL if self.classification_pipeline else "none"
            return {
                "model_type": model_name,
                "alternative_model": CLASSIFICATION_MODEL_PATH,
                "model_loaded": self.classification_pipeline is not None,
                "pipeline_task": "text-classification",
                "source": "hugging_face_hub"
            }
        except Exception as e:
            return {
                "error": str(e),
                "model_loaded": False
            }


# Initialize global service instance
classification_service = DocumentClassificationService()

def classify_document(content: str, filename: str = "") -> Dict:
    """Convenience function for document classification."""
    return classification_service.classify_document(content, filename)
