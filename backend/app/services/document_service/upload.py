from app.services.document_service.serialization import convert_objectid_to_str, serialize_validation_result
from app.services.document_service.exceptions import ContractValidationError

import logging
import time
from datetime import datetime, timezone
from bson import ObjectId
import numpy as np

from app.services.document_validator import LegalContractValidator
from app.models.document import AcceptedDocument
from app.models.rejected_document import RejectedDocument
from app.utils.file_utils import parse_file_content
from app.schemas.document import AcceptedDocumentRead, RejectedDocumentRead

logger = logging.getLogger("document_upload")

validator = LegalContractValidator()


async def handle_document_upload(user_id: str, file):
    logger.info(f"[UPLOAD START] User={user_id}, File={file.filename}, Type={file.content_type}")

    # Step 1: Check for empty files 
    content_bytes = await file.read()
    if not content_bytes:
        reason = "Empty file uploaded"
        rejected = await RejectedDocument(
            filename=file.filename,
            file_type=file.content_type,
            reason=reason,
            user_id=user_id,
            upload_date=datetime.now(timezone.utc)
        ).insert()
        return RejectedDocumentRead.model_validate(convert_objectid_to_str(rejected))

    await file.seek(0)

    # Step 2: Extract text 
    try:
        content = await parse_file_content(file)
    except Exception as e:
        reason = f"Text extraction failed: {str(e)}"
        rejected = await RejectedDocument(
            filename=file.filename,
            file_type=file.content_type,
            reason=reason,
            user_id=user_id,
            upload_date=datetime.now(timezone.utc)
        ).insert()
        return RejectedDocumentRead.model_validate(convert_objectid_to_str(rejected))

    if not content or len(content.strip()) < 50:
        reason = f"Document content insufficient (only {len(content.strip())} characters, minimum 50 required)"
        rejected = await RejectedDocument(
            filename=file.filename,
            file_type=file.content_type,
            reason=reason,
            user_id=user_id,
            upload_date=datetime.now(timezone.utc)
        ).insert()
        return RejectedDocumentRead.model_validate(convert_objectid_to_str(rejected))

    # Step 3: Contract validation (ONLY validation, no AI processing)
    try:
        validation_result = validator.validate(content)
        if not validation_result.is_valid:
            reason = f"Contract validation failed: {validation_result.message}"
            rejected = await RejectedDocument(
                filename=file.filename,
                file_type=file.content_type,
                reason=reason,
                user_id=user_id,
                upload_date=datetime.now(timezone.utc),
                validation_details=serialize_validation_result(validation_result)
            ).insert()
            rejection_response = RejectedDocumentRead.model_validate(convert_objectid_to_str(rejected))
            rejection_dict = rejection_response.model_dump()
            rejection_dict["validation_error"] = True
            rejection_dict["validation_details"] = serialize_validation_result(validation_result)
            return rejection_dict
    except Exception as e:
        reason = f"Contract validation system error: {str(e)}"
        rejected = await RejectedDocument(
            filename=file.filename,
            file_type=file.content_type,
            reason=reason,
            user_id=user_id,
            upload_date=datetime.now(timezone.utc),
            validation_details={"error": str(e)}
        ).insert()
        return RejectedDocumentRead.model_validate(convert_objectid_to_str(rejected))

    # Step 4: Basic contract type tag (from validation only)
    contract_type = validation_result.contract_type.value \
        if hasattr(validation_result.contract_type, 'value') \
        else str(validation_result.contract_type)
    
    basic_tags = [f"contract_{contract_type}", "validated_contract"]

    # Step 5: Save document with PENDING processing status
    document = AcceptedDocument(
        filename=file.filename,
        file_type=file.content_type,
        content=content,
        # AI fields are initially empty/default - will be populated by background task
        summary="Processing...",  # Placeholder
        embedding=[],  # Empty initially
        tags=basic_tags,  # Only basic tags from validation
        user_id=user_id,
        upload_date=datetime.now(timezone.utc),
        processing_status="pending",  # PENDING - background task will complete
        processed=False,  # Not fully processed yet
        analysis_status="pending",  # AI analysis pending
        classification_result={},  # Empty initially
        contract_validation={
            "is_valid": validation_result.is_valid,
            "contract_type": contract_type,
            "confidence": float(validation_result.confidence),
            "validated_at": datetime.now(timezone.utc)
        }
    )
    saved_doc = await document.insert()

    logger.info(f"[UPLOAD COMPLETE] Document {saved_doc.id} saved with pending status")

    # Step 6: Return minimal response data for immediate use
    saved_doc_dict = convert_objectid_to_str(saved_doc)
    response_data = AcceptedDocumentRead.model_validate(saved_doc_dict, from_attributes=True)

    result = response_data.model_dump()
    result['document_id'] = str(saved_doc.id)
    result['contract_validation'] = serialize_validation_result(validation_result)
    
    # Indicate that background processing is needed
    result['needs_background_processing'] = True
    result['status'] = 'pending'
    
    return result