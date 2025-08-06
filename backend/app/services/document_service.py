import logging
import time
from datetime import datetime, timezone
from typing import Optional
from app.models.document import AcceptedDocument
from app.models.rejected_document import RejectedDocument
from app.utils.file_utils import parse_file_content
from app.services.summarization_service import summarize_text
from app.services.embedding_service import generate_embedding
from app.services.classification_service import classify_document  # Add classification import
from app.schemas.document import AcceptedDocumentRead, RejectedDocumentRead
from fastapi import HTTPException, status
from app.services.qa_service import qa_service  # Import QA service
from bson import ObjectId


logger = logging.getLogger("document_upload")


async def handle_document_upload(user_id: str, file):
    """
    Handles the document upload process:
    1. Check file size (reject empty).
    2. Parse text from PDF/DOCX/TXT.
    3. Reject if content is unreadable or too short.
    4. Generate AI summary, embeddings, and classification.
    5. Store in AcceptedDocument.
    """
    logger.info(f"[UPLOAD] User={user_id}, File={file.filename}, Type={file.content_type}")

    #  Step 1: Check for empty files 
    content_bytes = await file.read()
    if not content_bytes:
        reason = "Empty file uploaded"
        logger.warning(f"[REJECTED] {file.filename}: {reason}")
        rejected = await RejectedDocument(
            filename=file.filename,
            file_type=file.content_type,
            reason=reason,
            user_id=user_id,
            upload_date=datetime.now(timezone.utc)
        ).insert()
        return RejectedDocumentRead.model_validate(rejected, from_attributes=True)

    await file.seek(0)

    # Step 2: Extract text 
    try:
        logger.info(f"[PROCESS] Extracting text from {file.filename}...")
        content = await parse_file_content(file)
    except Exception as e:
        reason = f"Unreadable file: {str(e)}"
        logger.error(f"[REJECTED] {file.filename}: {reason}")
        rejected = await RejectedDocument(
            filename=file.filename,
            file_type=file.content_type,
            reason=reason,
            user_id=user_id,
            upload_date=datetime.now(timezone.utc)
        ).insert()
        return RejectedDocumentRead.model_validate(rejected, from_attributes=True)

    if not content or len(content.strip()) < 100:
        reason = "Document too short or contains no text"
        logger.warning(f"[REJECTED] {file.filename}: {reason}")
        rejected = await RejectedDocument(
            filename=file.filename,
            file_type=file.content_type,
            reason=reason,
            user_id=user_id,
            upload_date=datetime.now(timezone.utc)
        ).insert()
        return RejectedDocumentRead.model_validate(rejected, from_attributes=True)

    # Step 3: AI Features - Summary, Embeddings, and Classification
    summary, embedding, classification_result = "Summary generation failed.", [], {}
    try:
        logger.info(f"[AI] Generating summary, embeddings, and classification for {file.filename}...")
        start_time = time.time()
        
        # Generate summary and embedding
        summary = summarize_text(content)
        embedding = generate_embedding(content)
        
        # Generate classification
        classification_result = classify_document(content, file.filename)
        logger.info(f"[CLASSIFICATION] Document classified as: {classification_result.get('document_type', 'unknown')} "
                   f"(confidence: {classification_result.get('document_type_confidence', 0.0):.2f})")
        
        logger.info(f"[AI] Completed in {time.time() - start_time:.2f} seconds")
    except Exception as e:
        logger.error(f"[AI ERROR] {file.filename}: {e}")

    # Step 4: Extract tags from classification for better organization
    tags = []
    if classification_result:
        # Add document type as tag
        doc_type = classification_result.get('document_type', 'general')
        if doc_type != 'general':
            tags.append(doc_type)
        
        # Add legal domain as tag
        legal_domain = classification_result.get('legal_domain', 'general')
        if legal_domain != 'general':
            tags.append(legal_domain)
        
        # Add urgency as tag if high or medium
        urgency = classification_result.get('urgency', 'low')
        if urgency in ['high', 'medium']:
            tags.append(f"urgency_{urgency}")
        
        # Add extracted entity types as tags
        entities = classification_result.get('extracted_entities', [])
        entity_types = list(set([entity['type'] for entity in entities]))
        tags.extend([f"has_{entity_type}" for entity_type in entity_types])

    #  Step 5: Save accepted document with classification data
    logger.info(f"[ACCEPTED] Storing document {file.filename} for User={user_id}")
    document = AcceptedDocument(
        filename=file.filename,
        file_type=file.content_type,
        content=content,
        summary=summary,
        embedding=embedding,
        tags=tags,  # Add generated tags
        user_id=user_id,
        upload_date=datetime.now(timezone.utc)
    )
    
    # Add classification data to document if you want to store it
    # Note: You might need to add these fields to your AcceptedDocument model
    if hasattr(document, 'classification_result'):
        document.classification_result = classification_result
    
    saved_doc = await document.insert()

    # Step 6: Add to QA service knowledge base
    try:
        qa_service.add_document(str(saved_doc.id), content)
        logger.info(f"[QA] Added document {saved_doc.id} to QA knowledge base")
    except Exception as e:
        logger.error(f"[QA ERROR] Failed to add document to QA service: {e}") 
    
    # Step 7: Log classification summary
    if classification_result:
        logger.info(f"[CLASSIFICATION SUMMARY] {file.filename}:")
        logger.info(f"  - Type: {classification_result.get('document_type', 'unknown')} "
                   f"(confidence: {classification_result.get('document_type_confidence', 0.0):.2f})")
        logger.info(f"  - Domain: {classification_result.get('legal_domain', 'general')} "
                   f"(confidence: {classification_result.get('legal_domain_confidence', 0.0):.2f})")
        logger.info(f"  - Urgency: {classification_result.get('urgency', 'low')}")
        logger.info(f"  - Method: {classification_result.get('classification_method', 'unknown')}")
        logger.info(f"  - Entities found: {len(classification_result.get('extracted_entities', []))}")
        logger.info(f"  - Generated tags: {tags}")
    
    # Return response with document_id and classification info
    response_data = AcceptedDocumentRead.model_validate(saved_doc.model_dump(by_alias=True), from_attributes=True)

    # Add document id and classification info to the response for frontend
    result = response_data.model_dump()
    result['document_id'] = str(saved_doc.id)
    result['classification'] = classification_result  # Add classification results
    result['auto_generated_tags'] = tags  # Add the generated tags

    return result

async def get_user_documents(user_id: str):
    """
    Retrieves all documents uploaded by a user.
    """
    documents = await AcceptedDocument.find(
        AcceptedDocument.user_id == user_id
    ).sort(-AcceptedDocument.upload_date).to_list()   #Sort by upload_date descending

    return [AcceptedDocumentRead.model_validate(doc.model_dump(by_alias=True), from_attributes=True) for doc in documents]


def serialize_document(document) -> dict:
    """Serialize document with classification info if available."""
    doc_dict = {
        "id": str(document.id),
        "user_id": str(document.user_id),
        "upload_date": document.upload_date,
        "filename": document.filename,
        "file_type": document.file_type,
        "content": document.content if hasattr(document, "content") else None,
        "summary": document.summary if hasattr(document, "summary") else None,
        "tags": document.tags if hasattr(document, "tags") else [],
    }
    
    # Add classification result if available
    if hasattr(document, "classification_result"):
        doc_dict["classification"] = document.classification_result
    
    return doc_dict


async def get_document_by_id(user_id: str, document_id: str):
    try:
        document = await AcceptedDocument.find_one({
            "_id": ObjectId(document_id),
            "user_id": user_id
        })

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        return serialize_document(document)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching document: {str(e)}"
        )


async def get_documents_by_type(user_id: str, document_type: str = None, urgency: str = None):
    """
    Get documents filtered by classification type or urgency.
    """
    try:
        query = {"user_id": user_id}
        
        # Filter by tags containing the document type or urgency
        if document_type:
            query["tags"] = {"$in": [document_type]}
        
        if urgency:
            if "tags" in query:
                # If already filtering by document_type, add urgency filter
                query["$and"] = [
                    {"user_id": user_id},
                    {"tags": {"$in": [document_type]}},
                    {"tags": {"$in": [f"urgency_{urgency}"]}}
                ]
                del query["tags"]
            else:
                query["tags"] = {"$in": [f"urgency_{urgency}"]}
        
        documents = await AcceptedDocument.find(query).sort(-AcceptedDocument.upload_date).to_list()
        
        return [AcceptedDocumentRead.model_validate(doc.model_dump(by_alias=True), from_attributes=True) for doc in documents]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error filtering documents: {str(e)}"
        )
    

async def delete_document_by_id(user_id: str, document_id: str) -> dict:
    """
    Deletes a document by its ID and user ID.
    """
    try:
        document = await AcceptedDocument.find_one({
            "_id": ObjectId(document_id),
            "user_id": user_id
        })

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        await document.delete()

        # Remove QA service cache
        if document_id in qa_service.documents:
            del qa_service.documents[document_id]
            logger.info(f"[QA] Removed document {document_id} from QA knowledge base")

        logger.info(f"[DELETE] Document {document_id} deleted for User={user_id}")

        return {
            "message": "Document deleted successfully",
            "document_id": document_id
        }

    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )