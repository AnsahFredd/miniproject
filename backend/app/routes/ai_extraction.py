# import os
# from fastapi import APIRouter, Depends, HTTPException, status
# from app.schemas.ai_extraction import ExpiryExtractionRequest, ExpiryExtractionResponse
# from app.models.user import User
# from app.dependencies.auth import get_current_user
# from app.models.document import AcceptedDocument
# from beanie import PydanticObjectId
# import PyPDF2
# from app.services.ai_extraction_service import extract_expiry_with_ai, extract_expiry_with_rules
# from datetime import datetime, timedelta, timezone
# from typing import List, Optional
# import logging

# from app.core.config import settings

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# router = APIRouter(tags=["AI Analysis"])


# @router.post("/extract-expiry", response_model=ExpiryExtractionResponse)
# async def extract_contract_expiry(
#     request: ExpiryExtractionRequest,
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Extract contract expiry date from a document using AI and rule-based methods
#     """
#     try:
#         # Validate ObjectId format
#         try:
#             document_id = PydanticObjectId(request.document_id)
#         except Exception:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Invalid document ID format"
#             )
        
#         # Get the document from MongoDB using Beanie
#         document = await AcceptedDocument.find_one(
#             AcceptedDocument.id == document_id,
#             AcceptedDocument.user_id == current_user.id
#         )
        
#         if not document:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Document not found"
#             )
        
#         # Get document content/text
#         document_text = ""
        
#         # Try different field names for text content
#         if hasattr(document, 'content') and document.content:
#             document_text = document.content
#         elif hasattr(document, 'extracted_text') and document.extracted_text:
#             document_text = document.extracted_text
#         elif hasattr(document, 'text') and document.text:
#             document_text = document.text
        
#         # If no text content found, try to read from file
#         if not document_text.strip():
#             file_path = getattr(document, 'file_path', None) or getattr(document, 'path', None)
            
#             if file_path and os.path.exists(file_path):
#                 try:
#                     # Handle different file types
#                     if file_path.lower().endswith('.txt'):
#                         with open(file_path, 'r', encoding='utf-8') as f:
#                             document_text = f.read()
#                     elif file_path.lower().endswith('.pdf'):
#                         # Extract text from PDF using PyPDF2
#                         with open(file_path, 'rb') as f:
#                             pdf_reader = PyPDF2.PdfReader(f)
#                             document_text = ""
#                             for page in pdf_reader.pages:
#                                 document_text += page.extract_text()
#                     elif file_path.lower().endswith(('.docx', '.doc')):
#                         # For Word documents, you might want to use python-docx
#                         raise HTTPException(
#                             status_code=status.HTTP_400_BAD_REQUEST,
#                             detail="Word document processing not implemented. Please convert to PDF or TXT."
#                         )
#                     else:
#                         raise HTTPException(
#                             status_code=status.HTTP_400_BAD_REQUEST,
#                             detail="Unsupported file type for text extraction"
#                         )
#                 except Exception as e:
#                     logger.error(f"Error reading document file: {str(e)}")
#                     raise HTTPException(
#                         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                         detail=f"Could not read document content: {str(e)}"
#                     )
        
#         if not document_text.strip():
#             return ExpiryExtractionResponse(
#                 document_id=request.document_id,
#                 error="No text content found in document"
#             )
        
#         logger.info(f"Analyzing document {request.document_id} for expiry dates")
        
#         # Try AI extraction first if OpenAI key is available
#         result = None
#         if settings.OPENAI_API_KEY:
#             try:
#                 # Use custom prompt if provided, otherwise use default
#                 custom_prompt = getattr(request, 'prompt', None)
#                 result = extract_expiry_with_ai(document_text, custom_prompt)
#                 logger.info(f"AI extraction result: {result}")
#             except Exception as e:
#                 logger.warning(f"AI extraction failed, falling back to rules: {str(e)}")
        
#         # Fallback to rule-based extraction
#         if not result or result.get('error') or not result.get('expiry_date'):
#             result = extract_expiry_with_rules(document_text)
#             logger.info(f"Rule-based extraction result: {result}")
        
#         # Update document with analysis results using Beanie
#         try:
#             # Add analysis fields to the document
#             document.expiry_analysis = result
#             document.last_analyzed = datetime.now(timezone.utc)
#             document.analyzed_by = current_user.id
            
#             # Save the updated document
#             await document.save()
#             logger.info(f"Updated document {request.document_id} with analysis results")
#         except Exception as e:
#             logger.warning(f"Failed to update document with analysis results: {str(e)}")
        
#         # Add document_id to result
#         result["document_id"] = request.document_id
        
#         return ExpiryExtractionResponse(**result)
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Unexpected error in extract_contract_expiry: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to analyze document: {str(e)}"
#         )


# @router.post("/extract-expiry-bulk")
# async def extract_expiry_bulk(
#     document_ids: List[str],
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Extract expiry dates from multiple documents
#     """
#     results = []
    
#     for doc_id in document_ids:
#         try:
#             # Validate ObjectId format
#             try:
#                 PydanticObjectId(doc_id)
#             except Exception:
#                 results.append({
#                     "document_id": doc_id,
#                     "error": "Invalid document ID format",
#                     "success": False
#                 })
#                 continue
            
#             request = ExpiryExtractionRequest(document_id=doc_id)
#             result = await extract_contract_expiry(request, current_user)
#             results.append({
#                 "document_id": doc_id,
#                 "result": result.model_dump(),
#                 "success": True
#             })
#         except HTTPException as http_exc:
#             results.append({
#                 "document_id": doc_id,
#                 "error": http_exc.detail,
#                 "success": False
#             })
#         except Exception as e:
#             results.append({
#                 "document_id": doc_id,
#                 "error": str(e),
#                 "success": False
#             })
    
#     return {"results": results}


# @router.get("/documents/{document_id}/expiry-analysis")
# async def get_expiry_analysis(
#     document_id: str,
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get previously stored expiry analysis for a document
#     """
#     try:
#         # Validate ObjectId format
#         try:
#             doc_id = PydanticObjectId(document_id)
#         except Exception:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Invalid document ID format"
#             )
        
#         # Get the document from MongoDB using Beanie
#         document = await AcceptedDocument.find_one(
#             AcceptedDocument.id == doc_id,
#             AcceptedDocument.user_id == current_user.id
#         )
        
#         if not document:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Document not found"
#             )
        
#         expiry_analysis = getattr(document, 'expiry_analysis', None)
#         if not expiry_analysis:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="No expiry analysis found for this document"
#             )
        
#         return {
#             "document_id": document_id,
#             "document_name": getattr(document, 'name', None) or getattr(document, 'filename', None),
#             "analysis": expiry_analysis,
#             "last_analyzed": getattr(document, 'last_analyzed', None),
#             "success": True
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error retrieving expiry analysis: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to retrieve analysis: {str(e)}"
#         )


# @router.get("/documents/expiring-soon")
# async def get_expiring_documents(
#     days_ahead: int = 30,
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get documents that are expiring within the specified number of days
#     """
#     try:
#         from datetime import datetime, timedelta
        
#         # Calculate the date range
#         today = datetime.now(timezone.utc).date()
#         future_date = today + timedelta(days=days_ahead)
        
#         # Query documents with expiry analysis using Beanie
#         # Note: This assumes your AcceptedDocument model has expiry_analysis field
#         documents = await AcceptedDocument.find(
#             AcceptedDocument.user_id == current_user.id,
#             # Add more complex filtering if needed based on your model structure
#         ).to_list()
        
#         # Filter documents with valid expiry dates
#         expiring_docs = []
#         for doc in documents:
#             expiry_analysis = getattr(doc, 'expiry_analysis', None)
#             if expiry_analysis and expiry_analysis.get('expiry_date'):
#                 try:
#                     expiry_date_str = expiry_analysis['expiry_date']
#                     # Parse the expiry date (adjust format as needed)
#                     expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                    
#                     # Check if within range
#                     if today <= expiry_date <= future_date:
#                         doc_dict = doc.dict()
#                         doc_dict['expiry_date_parsed'] = expiry_date.isoformat()
#                         expiring_docs.append(doc_dict)
#                 except Exception as e:
#                     logger.warning(f"Error parsing expiry date for document {doc.id}: {str(e)}")
#                     continue
        
#         # Sort by expiry date
#         expiring_docs.sort(key=lambda x: x['expiry_date_parsed'])
        
#         return {
#             "documents": expiring_docs,
#             "count": len(expiring_docs),
#             "days_ahead": days_ahead,
#             "success": True
#         }
        
#     except Exception as e:
#         logger.error(f"Error retrieving expiring documents: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to retrieve expiring documents: {str(e)}"
#         )


# @router.get("/documents/analysis-stats")
# async def get_analysis_stats(
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get statistics about document analysis for the current user
#     """
#     try:
#         # Get all user documents
#         documents = await AcceptedDocument.find(
#             AcceptedDocument.user_id == current_user.id
#         ).to_list()
        
#         total_docs = len(documents)
#         analyzed_docs = 0
#         expiring_soon = 0
#         expired_docs = 0
        
#         today = datetime.now(timezone.utc).date()
#         thirty_days_from_now = today + timedelta(days=30)
        
#         for doc in documents:
#             expiry_analysis = getattr(doc, 'expiry_analysis', None)
#             if expiry_analysis:
#                 analyzed_docs += 1
                
#                 if expiry_analysis.get('expiry_date'):
#                     try:
#                         expiry_date = datetime.strptime(
#                             expiry_analysis['expiry_date'], '%Y-%m-%d'
#                         ).date()
                        
#                         if expiry_date < today:
#                             expired_docs += 1
#                         elif expiry_date <= thirty_days_from_now:
#                             expiring_soon += 1
#                     except Exception:
#                         continue
        
#         return {
#             "total_documents": total_docs,
#             "analyzed_documents": analyzed_docs,
#             "expiring_soon": expiring_soon,
#             "expired_documents": expired_docs,
#             "analysis_completion_rate": round((analyzed_docs / total_docs * 100), 2) if total_docs > 0 else 0,
#             "success": True
#         }
        
#     except Exception as e:
#         logger.error(f"Error retrieving analysis stats: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to retrieve analysis stats: {str(e)}"
#         )