from fastapi import HTTPException, status
from app.models.document import AcceptedDocument
from app.models.rejected_document import RejectedDocument
from app.schemas.document import AcceptedDocumentRead, RejectedDocumentRead
from bson import ObjectId
from app.services.document_service.serialization import convert_objectid_to_str, serialize_document
from beanie import PydanticObjectId
import logging


logger = logging.getLogger(__name__)

async def get_user_documents(user_id: str):
    documents = await AcceptedDocument.find(
        AcceptedDocument.user_id == user_id
    ).sort(-AcceptedDocument.upload_date).to_list()
    return [AcceptedDocumentRead.model_validate(convert_objectid_to_str(doc)) for doc in documents]


async def get_user_rejected_documents(user_id: str):
    rejected_documents = await RejectedDocument.find(
        RejectedDocument.user_id == user_id
    ).sort(-RejectedDocument.upload_date).to_list()
    return [RejectedDocumentRead.model_validate(convert_objectid_to_str(doc)) for doc in rejected_documents]


async def get_document_by_id(user_id: str, document_id: str):
    document = await AcceptedDocument.find_one({
        "_id": ObjectId(document_id),
        "user_id": user_id
    })
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return serialize_document(document)


async def get_documents_by_type(user_id: str, document_type: str = None, urgency: str = None):
    query = {"user_id": user_id}
    if document_type:
        query["tags"] = {"$in": [document_type]}
    if urgency:
        if "tags" in query:
            query["$and"] = [
                {"user_id": user_id},
                {"tags": {"$in": [document_type]}} if document_type else {},
                {"tags": {"$in": [f"urgency_{urgency}"]}}
            ]
            del query["tags"]
        else:
            query["tags"] = {"$in": [f"urgency_{urgency}"]}
    documents = await AcceptedDocument.find(query).sort(-AcceptedDocument.upload_date).to_list()
    return [AcceptedDocumentRead.model_validate(convert_objectid_to_str(doc)) for doc in documents]


async def delete_document_by_id(user_id: PydanticObjectId, document_id: PydanticObjectId) -> bool:
    """
    Delete a document by ID, ensuring it belongs to the given user.
    Returns True if deleted, False if not found or unauthorized.
    """
    document = await AcceptedDocument.get(document_id)

    if not document:
        logger.warning(f"Document {document_id} not found.")
        return False

    if str(document.user_id) != str(user_id):
        logger.warning(f"User {user_id} tried to delete unauthorized document {document_id}.")
        return False

    await document.delete()
    logger.info(f"Document {document_id} deleted successfully by user {user_id}.")
    return True