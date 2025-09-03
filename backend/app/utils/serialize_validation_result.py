"""Utility functions for document service operations."""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from bson import ObjectId

logger = logging.getLogger("document_utils")

def serialize_validation_result(validation_result) -> Dict[str, Any]:
    """
    Safely serialize ValidationResult object to JSON-compatible dict.
    
    Args:
        validation_result: ValidationResult object or None
        
    Returns:
        Dict containing serialized validation data
    """
    if not validation_result:
        return {}
    
    try:
        return {
            "is_valid": bool(validation_result.is_valid),
            "contract_type": (
                validation_result.contract_type.value 
                if hasattr(validation_result.contract_type, 'value') 
                else str(validation_result.contract_type)
            ),
            "confidence": float(validation_result.confidence),
            "message": str(validation_result.message) if validation_result.message else "",
            "found_elements": (
                list(validation_result.found_elements) 
                if validation_result.found_elements else []
            ),
            "missing_elements": (
                list(validation_result.missing_elements) 
                if validation_result.missing_elements else []
            ),
            "validation_timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error serializing validation result: {str(e)}")
        return {
            "is_valid": False,
            "contract_type": "unknown",
            "confidence": 0.0,
            "message": f"Serialization error: {str(e)}",
            "found_elements": [],
            "missing_elements": [],
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "serialization_error": True
        }

def convert_objectid_to_str(document) -> Dict[str, Any]:
    """
    Convert MongoDB document with ObjectId fields to dict with string representations.
    
    Args:
        document: MongoDB document (Beanie model or raw dict)
        
    Returns:
        Dict with ObjectId and datetime fields converted to strings
    """
    if hasattr(document, 'model_dump'):
        # For Beanie/Motor documents
        doc_dict = document.model_dump(by_alias=True)
    elif hasattr(document, 'dict'):
        # For Pydantic models
        doc_dict = document.dict(by_alias=True)
    else:
        # For raw MongoDB documents
        doc_dict = dict(document) if document else {}
    
    # Convert ObjectId and datetime fields recursively
    return _convert_fields_recursive(doc_dict)

def _convert_fields_recursive(obj) -> Any:
    """Recursively convert ObjectId and datetime fields to strings."""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {
            key: _convert_fields_recursive(value) 
            for key, value in obj.items()
        }
    elif isinstance(obj, list):
        return [_convert_fields_recursive(item) for item in obj]
    else:
        return obj

def create_validation_details(validation_result, content_length: int) -> Dict[str, Any]:
    """
    Create detailed validation information for rejected documents.
    
    Args:
        validation_result: ValidationResult object
        content_length: Length of document content
        
    Returns:
        Dict containing detailed validation information
    """
    if not validation_result:
        return {
            "error_type": "validation_system_error",
            "error_message": "No validation result available",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    is_borderline = 0.25 <= validation_result.confidence < 0.40
    
    return {
        "is_valid": validation_result.is_valid,
        "contract_type": (
            validation_result.contract_type.value 
            if hasattr(validation_result.contract_type, 'value') 
            else str(validation_result.contract_type)
        ),
        "confidence": float(validation_result.confidence),
        "missing_elements": (
            list(validation_result.missing_elements) 
            if validation_result.missing_elements else []
        ),
        "found_elements": (
            list(validation_result.found_elements) 
            if validation_result.found_elements else []
        ),
        "message": str(validation_result.message),
        "content_length": content_length,
        "validation_timestamp": datetime.now(timezone.utc).isoformat(),
        "is_borderline": is_borderline,
        "confidence_category": _get_confidence_category(validation_result.confidence)
    }

def create_contract_validation_metadata(validation_result) -> Dict[str, Any]:
    """
    Create contract validation metadata for accepted documents.
    
    Args:
        validation_result: ValidationResult object
        
    Returns:
        Dict containing contract validation metadata
    """
    if not validation_result:
        return {}
    
    return {
        "is_valid": validation_result.is_valid,
        "contract_type": (
            validation_result.contract_type.value 
            if hasattr(validation_result.contract_type, 'value') 
            else str(validation_result.contract_type)
        ),
        "confidence": float(validation_result.confidence),
        "validated_at": datetime.now(timezone.utc),
        "validation_version": "1.0"  # For tracking validation algorithm versions
    }

def _get_confidence_category(confidence: float) -> str:
    """Categorize confidence level."""
    if confidence >= 0.8:
        return "high"
    elif confidence >= 0.6:
        return "medium"
    elif confidence >= 0.4:
        return "low"
    else:
        return "very_low"

def serialize_document_for_response(document, include_content: bool = False) -> Dict[str, Any]:
    """
    Serialize document for API response with optional content inclusion.
    
    Args:
        document: Document object to serialize
        include_content: Whether to include full document content
        
    Returns:
        Serialized document dict
    """
    # Convert ObjectIds and datetimes
    doc_dict = convert_objectid_to_str(document)
    
    # Ensure required fields
    doc_dict.update({
        "id": str(document.id) if hasattr(document, 'id') else doc_dict.get('_id'),
        "user_id": str(document.user_id) if hasattr(document, 'user_id') else '',
        "filename": getattr(document, 'filename', ''),
        "file_type": getattr(document, 'file_type', ''),
        "tags": getattr(document, 'tags', []),
        "summary": getattr(document, 'summary', '')
    })
    
    # Include content only if requested
    if include_content and hasattr(document, 'content'):
        doc_dict["content"] = document.content
    elif "content" in doc_dict:
        # Remove content if not requested
        del doc_dict["content"]
    
    # Add classification result if available
    if hasattr(document, "classification_result") and document.classification_result:
        doc_dict["classification"] = document.classification_result
    
    # Add validation info if available
    if hasattr(document, "contract_validation") and document.contract_validation:
        doc_dict["contract_validation"] = _convert_fields_recursive(document.contract_validation)
    
    return doc_dict

def extract_key_clauses(content: str, classification_result: Optional[Dict] = None) -> list:
    """
    Extract key clauses from document content for display.
    
    Args:
        content: Document content
        classification_result: Optional classification results
        
    Returns:
        List of key clauses
    """
    clauses = []
    
    if not content:
        return ["No content available for clause extraction"]
    
    lines = content.split('\n')
    
    # Look for numbered clauses or important contract terms
    important_keywords = [
        'compensation', 'payment', 'salary', 'term', 'termination', 
        'confidentiality', 'liability', 'warranty', 'intellectual property', 
        'rent', 'deposit', 'obligations', 'responsibilities', 'scope',
        'deliverables', 'timeline', 'deadline'
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for numbered clauses (1., 2., etc.) or important terms
        if (len(line) > 10 and len(line) < 200 and
            (line[0].isdigit() or 
             any(keyword in line.lower() for keyword in important_keywords))):
            clauses.append(line)
            
        if len(clauses) >= 6:  # Limit to 6 key clauses
            break
    
    # If we found clauses, return them
    if clauses:
        return clauses[:6]
    
    # Fallback: extract from classification entities if available
    if classification_result and 'extracted_entities' in classification_result:
        entities = classification_result['extracted_entities']
        entity_clauses = []
        
        for entity in entities[:5]:  # Limit to first 5 entities
            entity_type = entity.get('type', '')
            entity_text = entity.get('text', '')
            
            if entity_type in ['MONEY', 'DATE', 'ORG', 'PERSON'] and entity_text:
                entity_clauses.append(f"{entity_type}: {entity_text}")
        
        if entity_clauses:
            return entity_clauses
    
    # Final fallback
    return [
        "Document successfully processed and validated",
        "Key contractual terms and obligations identified",
        "Available for Q&A and detailed analysis"
    ]

def get_document_stats(documents: list) -> Dict[str, Any]:
    """
    Calculate statistics for a list of documents.
    
    Args:
        documents: List of document objects
        
    Returns:
        Dict containing document statistics
    """
    if not documents:
        return {
            "total_documents": 0,
            "contract_types": {},
            "confidence_distribution": {},
            "tags_frequency": {}
        }
    
    contract_types = {}
    confidence_ranges = {"high": 0, "medium": 0, "low": 0, "very_low": 0}
    all_tags = []
    
    for doc in documents:
        # Count contract types
        if hasattr(doc, 'contract_validation') and doc.contract_validation:
            contract_type = doc.contract_validation.get('contract_type', 'unknown')
            contract_types[contract_type] = contract_types.get(contract_type, 0) + 1
            
            # Count confidence ranges
            confidence = doc.contract_validation.get('confidence', 0.0)
            category = _get_confidence_category(confidence)
            confidence_ranges[category] += 1
        
        # Collect tags
        if hasattr(doc, 'tags') and doc.tags:
            all_tags.extend(doc.tags)
    
    # Count tag frequency
    tags_frequency = {}
    for tag in all_tags:
        tags_frequency[tag] = tags_frequency.get(tag, 0) + 1
    
    return {
        "total_documents": len(documents),
        "contract_types": contract_types,
        "confidence_distribution": confidence_ranges,
        "tags_frequency": dict(sorted(tags_frequency.items(), key=lambda x: x[1], reverse=True)[:10])
    }