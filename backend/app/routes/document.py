from fastapi import APIRouter, UploadFile, File, Depends, Query, Request
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from datetime import datetime
from beanie import PydanticObjectId
from app.models.document import AcceptedDocument
from app.services.document_service import (
    handle_document_upload, 
    get_user_rejected_documents, 
    get_document_by_id, 
    get_documents_by_type, 
    get_user_validation_stats, 
    delete_document_by_id,
    get_user_documents
)
from app.tasks.document_tasks import process_document_async
from app.dependencies.auth import get_current_user
from app.core.exceptions import APIError, ValidationError
from app.core.response_models import create_success_response, create_paginated_response
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Documents"])
try:
    BACKGROUND_PROCESSING_AVAILABLE = True
except ImportError as e:
    logger.error(f"Background processing not available: {e}")
    process_document_async = None
    BACKGROUND_PROCESSING_AVAILABLE = False

@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    user = Depends(get_current_user)
):
    """
    Upload and validate a legal contract document.
    Now returns immediately after validation, with AI processing happening in background.
    """
    try:
        # Input validation
        if not file.filename:
            raise ValidationError(
                message="No filename provided",
                field_errors={"file": "File must have a valid filename"}
            )
        
        # File type validation
        allowed_extensions = {'.pdf', '.doc', '.docx', '.txt'}
        file_extension = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_extensions:
            raise ValidationError(
                message=f"Unsupported file type: {file_extension}",
                field_errors={
                    "file": f"File type {file_extension} is not supported. Use: {', '.join(allowed_extensions)}"
                }
            )
        
        # File size validation - create a copy to avoid seek issues
        try:
            content = await file.read()
        except Exception as e:
            logger.error(f"Failed to read uploaded file: {e}")
            raise ValidationError(
                message="Failed to read uploaded file",
                field_errors={"file": "Unable to read the uploaded file"}
            )
        
        max_size = 10 * 1024 * 1024  # 10MB
        
        if len(content) == 0:
            raise ValidationError(
                message="Empty file uploaded",
                field_errors={"file": "File appears to be empty"}
            )
        
        if len(content) > max_size:
            file_size_mb = round(len(content) / (1024 * 1024), 2)
            raise ValidationError(
                message=f"File too large: {file_size_mb}MB",
                field_errors={"file": f"File size ({file_size_mb}MB) exceeds 10MB limit"}
            )
        
        # Create a new UploadFile object from the content for processing
        try:
            # Reset the original file or create a new one from content
            file_for_processing = UploadFile(
                filename=file.filename,
                file=io.BytesIO(content),
                headers=file.headers
            )
        except Exception as e:
            logger.error(f"Failed to prepare file for processing: {e}")
            raise ValidationError(
                message="Failed to prepare file for processing",
                field_errors={"file": "Unable to prepare the file for processing"}
            )
        
        # Process document (validation only, no AI processing)
        try:
            result = await handle_document_upload(user.id, file_for_processing)
        except Exception as e:
            logger.error(f"Document upload service failed: {e}", exc_info=True)
            raise APIError(
                message="Failed to process document upload",
                status_code=500,
                error_code="UPLOAD_SERVICE_ERROR",
                user_action="Please try again. If the problem persists, contact support."
            )
        
        # Handle different result types
        if isinstance(result, dict):
            if result.get("validation_error"):
                # Document was rejected due to validation
                return JSONResponse(
                    status_code=422,
                    content={
                        "success": False,
                        "message": "Document validation failed",
                        "error_code": "VALIDATION_FAILED",
                        "validation_details": result.get("validation_details", {}),
                        "user_action": "Please ensure your document is a valid legal contract",
                        "timestamp": result.get("upload_date")
                    }
                )
            elif result.get("needs_background_processing") and "document_id" in result:
                # Document was accepted and needs background processing
                document_id = result["document_id"]
                logger.info(f"Document uploaded successfully, starting background processing: {document_id}")
                
                # START BACKGROUND PROCESSING
                if BACKGROUND_PROCESSING_AVAILABLE and process_document_async:
                    try:
                        task = process_document_async.delay(document_id, str(user.id))
                        logger.info(f"Started background AI processing task {task.id} for document {document_id}")
                        
                        # Return immediate response with processing status
                        upload_date = result.get("upload_date")
                        if isinstance(upload_date, datetime):
                            upload_date = upload_date.isoformat()

                        return JSONResponse(
                            status_code=202,  # 202 Accepted - processing started
                            content={
                                "success": True,
                                "message": f"Document '{file.filename}' uploaded successfully. AI analysis in progress.",
                                "data": {
                                    "document_id": document_id,
                                    "id": document_id,
                                    "filename": result.get("filename", file.filename),
                                    "status": "processing",  # Processing in background
                                    "upload_date": upload_date,
                                    "contract_validation": result.get("contract_validation", {}),
                                    "processing_task_id": task.id,
                                    "processing_status": "started",
                                    # These will be populated by background task
                                    "summary": "Processing...",
                                    "classification": {},
                                    "ai_tags": []
                                },
                                "processing": {
                                    "task_id": task.id,
                                    "status": "started",
                                    "message": "AI analysis (classification, summarization, embedding) in progress",
                                    "estimated_completion": "2-5 minutes"
                                },
                                "request_id": getattr(request.state, 'request_id', None)
                            }
                        )
                        
                    except Exception as e:
                        logger.error(f"Failed to start background processing for {document_id}: {e}")
                        # Still return success since upload worked
                        upload_date = result.get("upload_date")
                        if isinstance(upload_date, datetime):
                            upload_date = upload_date.isoformat()

                        return JSONResponse(
                            status_code=200,
                            content={
                                "success": True,
                                "message": f"Document '{file.filename}' uploaded successfully, but AI processing failed to start",
                                "data": {
                                    "document_id": document_id,
                                    "id": document_id,
                                    "filename": result.get("filename", file.filename),
                                    "status": "uploaded",
                                    "upload_date": upload_date,
                                    "contract_validation": result.get("contract_validation", {}),
                                    "processing_error": str(e),
                                    "summary": "AI processing unavailable",
                                    "classification": {},
                                    "ai_tags": []
                                },
                                "request_id": getattr(request.state, 'request_id', None)
                            }
                        )
                else:
                    # Background processing not available
                    logger.warning("Background processing not available, returning upload success without processing")
                    upload_date = result.get("upload_date")
                    if isinstance(upload_date, datetime):
                        upload_date = upload_date.isoformat()

                    return JSONResponse(
                        status_code=200,
                        content={
                            "success": True,
                            "message": f"Document '{file.filename}' uploaded successfully (background processing unavailable)",
                            "data": {
                                "document_id": document_id,
                                "id": document_id,
                                "filename": result.get("filename", file.filename),
                                "status": "uploaded",
                                "upload_date": upload_date,
                                "contract_validation": result.get("contract_validation", {}),
                                "processing_error": "Background processing service unavailable",
                                "summary": "AI processing unavailable",
                                "classification": {},
                                "ai_tags": []
                            },
                            "request_id": getattr(request.state, 'request_id', None)
                        }
                    )
        
        # Handle rejected document response
        if hasattr(result, 'model_dump'):
            result_data = result.model_dump()
        elif hasattr(result, 'dict'):
            result_data = result.dict()
        else:
            result_data = dict(result) if result else {}
            
        # Ensure datetime objects are serialized
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_datetime(item) for item in obj]
            return obj
            
        result_data = serialize_datetime(result_data)
        
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": f"Document '{file.filename}' was rejected",
                "error_code": "DOCUMENT_REJECTED",
                "rejection_details": result_data,
                "user_action": "Please review the rejection reason and try again with a valid legal contract"
            }
        )
        
    except ValidationError:
        raise
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in document upload: {str(e)}", exc_info=True)
        raise APIError(
            message="An unexpected error occurred while processing your document",
            status_code=500,
            error_code="INTERNAL_ERROR",
            user_action="Please try again. If the problem persists, contact support."
        )

@router.get("/{document_id}/processing-status")
async def get_processing_status(
    document_id: str,
    request: Request,
    user = Depends(get_current_user)
):
    """Get the processing status of a document."""
    try:
        # Convert document_id to ObjectId
        try:
            doc_obj_id = PydanticObjectId(document_id)
        except Exception as e:
            logger.error(f"Invalid document ID format: {document_id}")
            raise APIError(
                message="Invalid document ID format",
                status_code=400,
                error_code="INVALID_DOCUMENT_ID"
            )
        
        # Use Beanie model to find document - user_id should be string, not ObjectId
        current_user_id_str = str(user.id)
        
        logger.debug(f"Looking for document {document_id} for user {current_user_id_str}")
        
        # Query using Beanie model
        document = await AcceptedDocument.find_one({
            "_id": doc_obj_id,
            "user_id": current_user_id_str
        })

        if not document:
            # Debug: Check if document exists at all
            doc_exists = await AcceptedDocument.find_one({"_id": doc_obj_id})
            if doc_exists:
                logger.warning(f"Document exists but user mismatch. Doc user_id: {doc_exists.user_id}, Current user: {current_user_id_str}")
            else:
                logger.warning(f"Document {document_id} not found in database")
            
            raise APIError(
                message="Document not found",
                status_code=404,
                error_code="DOCUMENT_NOT_FOUND"
            )
        
        # Get processing status from document - use correct field names from your model
        analysis_status = getattr(document, 'analysis_status', None) or getattr(document, 'processing_status', None) or "pending"
        
        response_data = {
            "document_id": document_id,
            "status": analysis_status,
            "processing_status": analysis_status,  # For backwards compatibility
            "processed": getattr(document, 'processed', False),
            "contract_analyzed": getattr(document, 'contract_analyzed', False),
            "filename": document.filename,
            "upload_date": document.upload_date.isoformat() if document.upload_date else None,
            "analysis_completed_at": document.analysis_completed_at.isoformat() if getattr(document, 'analysis_completed_at', None) else None,
            "last_analyzed": document.last_analyzed.isoformat() if getattr(document, 'last_analyzed', None) else None,
            "summary": getattr(document, 'summary', None),
            "tags": getattr(document, 'tags', []) or [],
            "classification_result": getattr(document, 'classification_result', {}) or {},
            # Add the missing fields
            "processing_started_at": document.processing_started_at.isoformat() if getattr(document, 'processing_started_at', None) else None,
            "processing_completed_at": document.processing_completed_at.isoformat() if getattr(document, 'processing_completed_at', None) else None,
            "processing_error": getattr(document, 'processing_error', None)
        }
        
        # If we have a task ID stored in the document (if you're storing it)
        if hasattr(document, 'processing_task_id') and getattr(document, 'processing_task_id', None):
            try:
                from app.core.celery_app import celery_app
                task_id = document.processing_task_id
                task_result = celery_app.AsyncResult(task_id)
                response_data.update({
                    "task_id": task_id,
                    "task_state": task_result.state,
                    "task_info": task_result.info if task_result.info else {}
                })
            except Exception as e:
                logger.warning(f"Could not get task status: {e}")
        
        return create_success_response(
            data=response_data,
            message="Processing status retrieved successfully",
            request_id=getattr(request.state, 'request_id', None)
        )
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Error getting processing status for {document_id}: {str(e)}", exc_info=True)
        raise APIError(
            message="Failed to get processing status",
            status_code=500,
            error_code="STATUS_ERROR"
        )


# Rest of your existing endpoints remain the same...
@router.get("/")
async def list_documents(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user = Depends(get_current_user)
):
    """List all accepted documents with pagination."""
    try:
        documents = await get_user_documents(user.id)
        
        # Simple pagination
        total = len(documents)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_docs = documents[start_idx:end_idx]
        
        return create_paginated_response(
            data=paginated_docs,
            total=total,
            page=page,
            page_size=page_size,
            message=f"Retrieved {len(paginated_docs)} documents"
        )
        
    except Exception as e:
        logger.error(f"Error fetching documents for user {user.id}: {str(e)}")
        raise APIError(
            message="Failed to retrieve documents",
            status_code=500,
            error_code="FETCH_ERROR",
            user_action="Please refresh the page or try again later"
        )

@router.get("/rejected")
async def list_rejected_documents(
    request: Request,
    user = Depends(get_current_user)
):
    """List all rejected documents."""
    try:
        rejected_docs = await get_user_rejected_documents(user.id)
        
        return create_success_response(
            data=rejected_docs,
            message=f"Retrieved {len(rejected_docs)} rejected documents",
            request_id=getattr(request.state, 'request_id', None)
        )
        
    except Exception as e:
        logger.error(f"Error fetching rejected documents for user {user.id}: {str(e)}")
        raise APIError(
            message="Failed to retrieve rejected documents",
            status_code=500,
            error_code="FETCH_ERROR"
        )

@router.get("/{document_id}")
async def get_document(
    document_id: str,
    request: Request,
    user = Depends(get_current_user)
):
    """Get a specific document by ID."""
    try:
        document = await get_document_by_id(user.id, document_id)
        
        return create_success_response(
            data=document,
            message="Document retrieved successfully",
            request_id=getattr(request.state, 'request_id', None)
        )
        
    except Exception as e:
        logger.error(f"Error fetching document {document_id}: {str(e)}")
        raise APIError(
            message="Failed to retrieve document",
            status_code=500,
            error_code="FETCH_ERROR"
        )

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    request: Request,
    user = Depends(get_current_user)
):
    """Delete a document."""
    try:
        result = await delete_document_by_id(user.id, document_id)
        
        return create_success_response(
            data={"document_id": document_id},
            message="Document deleted successfully",
            request_id=getattr(request.state, 'request_id', None)
        )
        
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        raise APIError(
            message="Failed to delete document",
            status_code=500,
            error_code="DELETE_ERROR"
        )

@router.get("/filter/by-type")
async def filter_documents(
    request: Request,
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    urgency: Optional[str] = Query(None, description="Filter by urgency level"),
    user = Depends(get_current_user)
):
    """Filter documents by type or urgency."""
    try:
        documents = await get_documents_by_type(
            user.id, document_type, urgency
        )
        
        return create_success_response(
            data={
                "documents": documents,
                "filters": {
                    "document_type": document_type,
                    "urgency": urgency
                },
                "count": len(documents)
            },
            message=f"Found {len(documents)} documents matching filters",
            request_id=getattr(request.state, 'request_id', None)
        )
    
    except Exception as e:
        logger.error(f"Error filtering documents: {str(e)}")
        raise APIError(
            message="Failed to filter documents",
            status_code=500,
            error_code="FILTER_ERROR"
        )

@router.get("/stats/validation")
async def get_validation_stats(
    request: Request,
    user = Depends(get_current_user)
):
    """Get validation statistics for the user."""
    try:
        stats = await get_user_validation_stats(user.id)
        
        return create_success_response(
            data=stats,
            message="Validation statistics retrieved successfully",
            request_id=getattr(request.state, 'request_id', None)
        )
        
    except Exception as e:
        logger.error(f"Error fetching validation stats: {str(e)}")
        raise APIError(
            message="Failed to retrieve validation statistics",
            status_code=500,
            error_code="STATS_ERROR"
        )

@router.get("/validation/requirements")
async def get_validation_requirements(request: Request):
    """Get contract validation requirements and guidelines."""
    return create_success_response(
        data={
            "title": "Legal Contract Validation Requirements",
            "description": "Requirements for valid legal contract documents",
            "required_elements": [
                {
                    "name": "Contract Formation OR Party Identification",
                    "description": "Either clear contract formation language or identified parties",
                    "examples": ["This agreement is made", "Between John Doe and ABC Company"]
                },
                {
                    "name": "Legal Obligations OR Substantive Terms", 
                    "description": "Either legal obligations/rights or substantive contract terms",
                    "examples": ["The tenant shall pay", "Monthly rent of $2,500", "Terms and conditions"]
                },
                {
                    "name": "Document Structure",
                    "description": "Proper document formatting with adequate content",
                    "examples": ["Multiple paragraphs", "At least 150 words", "Organized sections"]
                }
            ],
            "validation_changes": {
                "confidence_threshold": "40% (reduced from 55%)",
                "minimum_length": "150 characters (reduced from 200)",
                "requirement_flexibility": "Now requires either formation OR parties, and either obligations OR terms",
                "borderline_handling": "Documents with 25-40% confidence flagged for potential manual review"
            },
            "supported_formats": ["PDF", "DOC", "DOCX", "TXT"],
            "max_file_size": "10MB",
            "minimum_confidence": "40%"
        },
        message="Updated validation requirements retrieved successfully",
        request_id=getattr(request.state, 'request_id', None)
    )