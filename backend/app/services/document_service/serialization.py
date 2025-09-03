import logging
from datetime import datetime
from bson import ObjectId

logger = logging.getLogger("document_serialization")

def convert_objectid_to_str(document) -> dict:
    """Convert MongoDB document with ObjectId to dict with string id"""
    if hasattr(document, 'model_dump'):
        doc_dict = document.model_dump(by_alias=True)
    else:
        doc_dict = dict(document)

    if '_id' in doc_dict and isinstance(doc_dict['_id'], ObjectId):
        doc_dict['_id'] = str(doc_dict['_id'])

    for key, value in doc_dict.items():
        if isinstance(value, ObjectId):
            doc_dict[key] = str(value)
        elif isinstance(value, datetime):
            doc_dict[key] = value.isoformat()
        elif isinstance(value, dict):
            for nested_key, nested_value in value.items():
                if isinstance(nested_value, datetime):
                    value[nested_key] = nested_value.isoformat()
                elif isinstance(nested_value, ObjectId):
                    value[nested_key] = str(nested_value)
    return doc_dict


def serialize_validation_result(validation_result: dict) -> dict:
    """Safely serialize ValidationResult object to JSON-compatible dict"""
    if not validation_result:
        return {}
    return {
        "is_valid": validation_result.is_valid,
        "contract_type": validation_result.contract_type.value if hasattr(validation_result.contract_type, 'value') else str(validation_result.contract_type),
        "confidence": float(validation_result.confidence),
        "message": str(validation_result.message),
        "found_elements": list(validation_result.found_elements) if validation_result.found_elements else [],
        "missing_elements": list(validation_result.missing_elements) if validation_result.missing_elements else []
    }


def serialize_document(document) -> dict:
    """Serialize document with classification info if available."""
    from app.models.document import AcceptedDocument  # avoid circular imports

    doc_dict = convert_objectid_to_str(document)

    if isinstance(doc_dict.get('upload_date'), datetime):
        doc_dict['upload_date'] = doc_dict['upload_date'].isoformat()

    doc_dict.update({
        "id": str(document.id),
        "user_id": str(document.user_id),
        "filename": document.filename,
        "file_type": document.file_type,
        "content": getattr(document, "content", None),
        "summary": getattr(document, "summary", None),
        "tags": getattr(document, "tags", []),
    })

    if hasattr(document, "classification_result") and document.classification_result:
        doc_dict["classification"] = document.classification_result

    if hasattr(document, "contract_validation") and document.contract_validation:
        contract_validation = document.contract_validation
        if isinstance(contract_validation, dict):
            contract_validation = contract_validation.copy()
            if "validated_at" in contract_validation and isinstance(contract_validation["validated_at"], datetime):
                contract_validation["validated_at"] = contract_validation["validated_at"].isoformat()
            if "confidence" in contract_validation:
                contract_validation["confidence"] = float(contract_validation["confidence"])
        doc_dict["contract_validation"] = contract_validation

    return doc_dict
