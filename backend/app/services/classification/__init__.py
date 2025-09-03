"""
Enhanced document classification service with better error handling
"""

import logging
import re
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import numpy as np
from app.services.classification.model_handler import ModelHandler
from app.services.classification.rule_classifier import RuleBasedClassifier

logger = logging.getLogger(__name__)

# Initialize components
model_handler = ModelHandler()
rule_based_classifier = RuleBasedClassifier()


def safe_confidence_check(confidence_value, threshold: float = 0.5) -> bool:
    """
    Safely check confidence values to avoid 'truth value of array is ambiguous' error
    """
    try:
        if confidence_value is None:
            return False
        
        # Handle numpy arrays
        if hasattr(confidence_value, '__array__') or isinstance(confidence_value, np.ndarray):
            # Convert to scalar if it's a single-element array
            if hasattr(confidence_value, 'size') and confidence_value.size == 1:
                confidence_value = float(confidence_value.item())
            else:
                # For multi-element arrays, take the maximum
                confidence_value = float(np.max(confidence_value))
        
        # Handle lists and tuples
        elif isinstance(confidence_value, (list, tuple)):
            if len(confidence_value) == 1:
                confidence_value = float(confidence_value[0])
            else:
                confidence_value = float(max(confidence_value))
        
        # Handle other iterables
        elif hasattr(confidence_value, '__iter__') and not isinstance(confidence_value, (str, bytes)):
            try:
                confidence_value = float(max(confidence_value))
            except (ValueError, TypeError):
                logger.warning(f"Could not convert iterable to confidence value: {type(confidence_value)}")
                return False
        
        # Now we should have a scalar value
        return bool(float(confidence_value) >= threshold)
        
    except Exception as e:
        logger.warning(f"Error in safe_confidence_check: {e}, defaulting to False")
        return False

def safe_float_conversion(value, default: float = 0.0) -> float:
    """Safely convert various types to float"""
    try:
        if value is None:
            return default
        
        # Handle numpy arrays
        if hasattr(value, '__array__') or isinstance(value, np.ndarray):
            if hasattr(value, 'size') and value.size == 1:
                return float(value.item())
            else:
                return float(np.max(value))
        
        # Handle lists and tuples
        elif isinstance(value, (list, tuple)):
            if len(value) == 1:
                return float(value[0])
            else:
                return float(max(value))
        
        # Handle other iterables
        elif hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
            try:
                return float(max(value))
            except (ValueError, TypeError):
                return default
        
        # Direct conversion
        return float(value)
        
    except Exception as e:
        logger.warning(f"Error converting {type(value)} to float: {e}")
        return default

async def classify_document(content: str, filename: str = "unknown") -> Dict[str, Any]:
    """
    Enhanced document classification with better error handling
    
    Args:
        content: Document text content
        filename: Document filename for logging
    
    Returns:
        Dictionary with classification results
    """
    logger.info(f"[CLASSIFICATION] Starting classification for {filename}")
    
    # Initialize result with safe defaults
    result = {
        "document_type": "general",
        "document_type_confidence": 0.0,
        "legal_domain": "general", 
        "legal_domain_confidence": 0.0,
        "urgency": "low",
        "classification_method": "unknown",
        "extracted_entities": [],
        "processing_errors": []
    }
    
    # Early validation
    if not content or not content.strip():
        logger.warning(f"[CLASSIFICATION] Empty content for {filename}")
        result.update({
            "classification_method": "empty_content",
            "processing_errors": ["Content is empty or whitespace only"]
        })
        return result
    
    if len(content.strip()) < 50:
        logger.warning(f"[CLASSIFICATION] Content too short for {filename}: {len(content)} chars")
        result.update({
            "classification_method": "content_too_short", 
            "processing_errors": [f"Content too short: {len(content)} characters"]
        })
        return result
    
    # Try AI model classification first
    ai_result = None
    try:
        logger.info(f"[CLASSIFICATION] Attempting AI classification for {filename}")
        
        # Ensure model is initialized
        if not model_handler.initialized:
            await model_handler.initialize()
        
        # Try AI classification with error handling
        ai_result = await model_handler.classify_text(content)
        
        if ai_result and "error" not in ai_result:
            logger.info(f"[CLASSIFICATION] AI classification successful for {filename}")
            
            # Safely extract values with error handling
            doc_type = ai_result.get("document_type", "general")
            doc_confidence = safe_float_conversion(ai_result.get("confidence", 0.0))
            
            # Apply confidence threshold with safe checking
            if safe_confidence_check(doc_confidence, 0.3):
                result.update({
                    "document_type": doc_type,
                    "document_type_confidence": doc_confidence,
                    "classification_method": "ai_model",
                    "model_source": ai_result.get("model_source", "unknown")
                })
                logger.info(f"[CLASSIFICATION] AI result accepted: {doc_type} (confidence: {doc_confidence:.2f})")
            else:
                logger.info(f"[CLASSIFICATION] AI confidence too low: {doc_confidence:.2f}, falling back to rules")
                result["processing_errors"].append(f"AI confidence too low: {doc_confidence:.2f}")
        else:
            error_msg = ai_result.get("error", "Unknown AI error") if ai_result else "AI classification returned None"
            logger.warning(f"[CLASSIFICATION] AI classification failed for {filename}: {error_msg}")
            result["processing_errors"].append(f"AI classification failed: {error_msg}")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[CLASSIFICATION] AI classification exception for {filename}: {error_msg}")
        result["processing_errors"].append(f"AI classification exception: {error_msg}")
        
        # Handle the specific array ambiguity error
        if "truth value of an array" in error_msg:
            logger.warning(f"[CLASSIFICATION] Array ambiguity error detected for {filename}")
            result["processing_errors"].append("Array ambiguity error in AI model - using rule-based fallback")
    
    # If AI classification didn't work or had low confidence, try rule-based
    if result["classification_method"] in ["unknown", "content_too_short", "empty_content"] or result["document_type_confidence"] < 0.3:
        try:
            logger.info(f"[CLASSIFICATION] Attempting rule-based classification for {filename}")
            
            rule_result = rule_based_classifier.classify(content)
            
            if rule_result and safe_confidence_check(rule_result.get("confidence", 0), 0.2):
                # Use rule-based result if AI failed or had very low confidence
                if result["document_type_confidence"] < safe_float_conversion(rule_result.get("confidence", 0)):
                    result.update({
                        "document_type": rule_result.get("document_type", "general"),
                        "document_type_confidence": safe_float_conversion(rule_result.get("confidence", 0)),
                        "legal_domain": rule_result.get("legal_domain", "general"),
                        "urgency": rule_result.get("urgency", "low"),
                        "classification_method": "rule_based",
                        "extracted_entities": rule_result.get("extracted_entities", [])
                    })
                    logger.info(f"[CLASSIFICATION] Rule-based result used: {result['document_type']} (confidence: {result['document_type_confidence']:.2f})")
                else:
                    logger.info(f"[CLASSIFICATION] Rule-based confidence lower than AI, keeping AI result")
            else:
                logger.info(f"[CLASSIFICATION] Rule-based classification had low confidence")
                result["processing_errors"].append("Rule-based classification had low confidence")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[CLASSIFICATION] Rule-based classification failed for {filename}: {error_msg}")
            result["processing_errors"].append(f"Rule-based classification failed: {error_msg}")
    
    # Final fallback - ensure we have valid values
    if result["classification_method"] == "unknown":
        result["classification_method"] = "fallback"
        logger.warning(f"[CLASSIFICATION] Using fallback classification for {filename}")
    
    # Ensure all confidence values are properly formatted
    result["document_type_confidence"] = safe_float_conversion(result["document_type_confidence"])
    result["legal_domain_confidence"] = safe_float_conversion(result.get("legal_domain_confidence", 0.0))
    
    # Additional content analysis for legal domain if not set
    if result["legal_domain"] == "general" and result["document_type"] != "general":
        try:
            legal_domain = _determine_legal_domain(content, result["document_type"])
            if legal_domain != "general":
                result["legal_domain"] = legal_domain
                result["legal_domain_confidence"] = min(result["document_type_confidence"], 0.8)
        except Exception as e:
            logger.error(f"[CLASSIFICATION] Legal domain determination failed: {e}")
    
    # Log final result
    logger.info(f"[CLASSIFICATION] Final result for {filename}:")
    logger.info(f"  - Document Type: {result['document_type']} (confidence: {result['document_type_confidence']:.2f})")
    logger.info(f"  - Legal Domain: {result['legal_domain']} (confidence: {result['legal_domain_confidence']:.2f})")
    logger.info(f"  - Urgency: {result['urgency']}")
    logger.info(f"  - Method: {result['classification_method']}")
    logger.info(f"  - Entities: {len(result['extracted_entities'])}")
    if result["processing_errors"]:
        logger.info(f"  - Errors: {len(result['processing_errors'])}")
    
    return result

def _determine_legal_domain(content: str, doc_type: str) -> str:
    """Determine legal domain based on content analysis"""
    try:
        content_lower = content.lower()
        
        # Contract-specific domains
        if doc_type in ["contract", "lease", "agreement"]:
            if any(term in content_lower for term in ["employment", "job", "salary", "employee", "employer"]):
                return "employment"
            elif any(term in content_lower for term in ["lease", "rent", "tenant", "landlord", "property"]):
                return "real_estate"
            elif any(term in content_lower for term in ["sale", "purchase", "buyer", "seller", "goods"]):
                return "commercial"
            elif any(term in content_lower for term in ["intellectual property", "patent", "copyright", "trademark"]):
                return "intellectual_property"
            elif any(term in content_lower for term in ["service", "consulting", "professional"]):
                return "service_agreement"
        
        # Other legal domains
        if any(term in content_lower for term in ["criminal", "felony", "misdemeanor", "prosecution"]):
            return "criminal"
        elif any(term in content_lower for term in ["family", "divorce", "custody", "marriage"]):
            return "family"
        elif any(term in content_lower for term in ["corporate", "corporation", "business", "company"]):
            return "corporate"
        elif any(term in content_lower for term in ["tax", "taxation", "revenue", "irs"]):
            return "tax"
        
        return "general"
        
    except Exception as e:
        logger.error(f"Error determining legal domain: {e}")
        return "general"

def get_classification_stats() -> Dict[str, Any]:
    """Get classification service statistics"""
    try:
        model_info = model_handler.get_model_info()
        return {
            "service_status": "healthy",
            "model_handler_initialized": model_handler.initialized,
            "rule_based_available": True,
            "model_info": model_info,
            "supported_types": [
                "contract", "lease", "agreement", "legal_brief", 
                "policy", "regulation", "financial", "correspondence", "report"
            ],
            "supported_domains": [
                "employment", "real_estate", "commercial", "intellectual_property",
                "service_agreement", "criminal", "family", "corporate", "tax", "general"
            ]
        }
    except Exception as e:
        return {
            "service_status": "error",
            "error": str(e),
            "model_handler_initialized": False,
            "rule_based_available": True
        }

async def health_check() -> Dict[str, Any]:
    """Comprehensive health check for classification service"""
    try:
        # Test basic classification
        test_content = "This is a test legal contract for classification health check."
        test_result = await classify_document(test_content, "health_check_test")
        
        # Check model handler
        model_health = await model_handler.health_check() if hasattr(model_handler, 'health_check') else {"healthy": False, "error": "No health check method"}
        
        return {
            "overall_health": "healthy" if test_result.get("document_type") else "degraded",
            "classification_test": {
                "success": test_result.get("document_type") is not None,
                "method_used": test_result.get("classification_method", "unknown"),
                "errors": test_result.get("processing_errors", [])
            },
            "model_handler": model_health,
            "rule_based_classifier": {"available": True},
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "overall_health": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }