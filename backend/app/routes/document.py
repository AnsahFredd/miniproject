from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.services.document_service import handle_document_upload, get_user_documents, get_document_by_id, delete_document_by_id
from app.schemas.document import AcceptedDocumentRead
from app.dependencies.auth import get_current_user
from typing import List
from fastapi.responses import JSONResponse



router = APIRouter(tags=["Documents"])

@router.post("/upload", response_model=AcceptedDocumentRead)
async def upload_document(file: UploadFile = File(...), user=Depends(get_current_user)):
    """Upload and process a document, automatically adding it to QA system."""
    return await handle_document_upload(user.id, file)


@router.get("/", response_model=List[AcceptedDocumentRead])
async def list_documents(user=Depends(get_current_user)):
    """List all uploaded documents."""
    return await get_user_documents(user.id)


@router.get("/{document_id}", response_model=AcceptedDocumentRead)
async def get_document(document_id: str, user=Depends(get_current_user)):
    """Get a specific document by ID."""
    return await get_document_by_id(user.id, document_id)


@router.delete("/{document_id}")
async def delete_document(document_id: str, user=Depends(get_current_user)):
    """Delete a document and remove it from QA system."""
    result = await delete_document_by_id(user.id, document_id)
    return JSONResponse(content=result)

