from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.services.document_analysis_service import get_document_analysis
from app.dependencies.auth import get_current_user
router = APIRouter(prefix="", tags=["Document Analysis"])
import logging
from app.models.document import AcceptedDocument
from bson import ObjectId

logger = logging.getLogger(__name__)

def compare_user_ids(current_user, doc_user_id):
    """
    Helper function to properly compare user IDs regardless of type
    """
    # Extract user ID from current_user (could be string, ObjectId, or user object)
    if hasattr(current_user, 'id'):
        current_user_id = str(current_user.id)
    elif hasattr(current_user, '_id'):
        current_user_id = str(current_user._id)
    else:
        current_user_id = str(current_user)
    
    # Convert document user ID to string
    doc_user_id_str = str(doc_user_id)
    
    return current_user_id == doc_user_id_str, current_user_id, doc_user_id_str

# Updated analyze_document_endpoint with better user comparison
@router.get("/{document_id}/analysis")
async def analyze_document_endpoint(
    document_id: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive document analysis for the frontend interface
    """
    try:
        logger.info(f"=== DEBUG: Analysis request for document {document_id} by user {current_user} ===")
        logger.info(f"Current user type: {type(current_user)}")

        # Add validation for document ID
        if not document_id or document_id == "undefined" or document_id == "null":
            raise HTTPException(
                status_code=400, 
                detail="Invalid document ID provided"
            )
        
        # Check if document exists and belongs to user first
        try:
            logger.info(f"Looking for document with ID: {document_id}")

            # Validate ObjectId format
            try:
                obj_id = ObjectId(document_id)
                logger.info(f"Valid ObjectId created: {obj_id}")
            except Exception as oid_error:
                logger.error(f"Invalid ObjectId format for {document_id}: {oid_error}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid document ID format"
                )

            # Find document first
            doc = await AcceptedDocument.find_one({"_id": obj_id})
            
            if not doc:
                logger.error(f"Document {document_id} not found in database")
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Use helper function for user comparison
            is_owner, current_user_str, doc_user_str = compare_user_ids(current_user, doc.user_id)
            
            logger.info(f"User comparison: current='{current_user_str}', doc_owner='{doc_user_str}', match={is_owner}")
            
            if not is_owner:
                logger.warning(f"Access denied - Document belongs to user '{doc_user_str}', current user is '{current_user_str}'")
                raise HTTPException(status_code=403, detail="Access denied")
            
            logger.info(f"User access validated successfully for document {document_id}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error finding document {document_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(e)}"
            )
        
        # Now get the analysis
        logger.info(f"Starting analysis for document {document_id}")
        analysis = await get_document_analysis(document_id)
        
        if 'error' in analysis:
            logger.error(f"Analysis failed for document {document_id}: {analysis['error']}")
            raise HTTPException(status_code=400, detail=analysis['error'])
        
        # Ensure all required fields are present with safe defaults
        response = {
            'document_info': analysis.get('document_info', {}),
            'clause_overview': analysis.get('clause_overview', []),
            'summary': analysis.get('summary', {'text': 'Summary not available'}),
            'financial_summary': analysis.get('financial_summary', {
                'rent_amount': None,
                'deposit': None,
                'other_fees': []
            }),
            'parties_involved': analysis.get('parties_involved', []),
            'important_dates': analysis.get('important_dates', []),
            'term_information': analysis.get('term_information', {
                'lease_duration': None,
                'primary_term': None,
                'renewal_option': 'Not specified',
                'renewal_term': 'Not specified'
            }),
            'key_terms': analysis.get('key_terms', []),
            'metadata': {
                'analyzed_at': datetime.now().isoformat(),
                'user_id': current_user_str,
                'document_id': document_id
            }
        }
        
        logger.info(f"Analysis completed successfully for document {document_id}")
        logger.info(f"Response contains {len(response['clause_overview'])} clauses")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in document analysis {document_id}: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{id}/summary")
async def get_document_summary(
    id: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Get just the document summary (for quick preview)
    """
    try:
        from app.models.document import AcceptedDocument
        from bson import ObjectId
        
        # Validate document ID
        if not id or id == "undefined" or id == "null":
            raise HTTPException(status_code=400, detail="Invalid document ID")
        
        try:
            obj_id = ObjectId(id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid document ID format")
        
        doc = await AcceptedDocument.find_one({
            "_id": obj_id,
            "user_id": current_user
        })
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            'summary': doc.summary or "Summary not available",
            'filename': doc.filename,
            'document_id': id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary for document {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

@router.get("/{id}/clauses")
async def get_document_clauses(
    id: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get extracted clauses and their categories
    """
    try:
        # Validate document ID
        if not id or id == "undefined" or id == "null":
            raise HTTPException(status_code=400, detail="Invalid document ID")
        
        analysis = await get_document_analysis(id)
        
        if 'error' in analysis:
            raise HTTPException(status_code=400, detail=analysis['error'])
        
        clauses = analysis.get('clause_overview', [])
        return {
            'clauses': clauses,
            'total_clauses': len(clauses),
            'document_id': id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting clauses for document {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to extract clauses: {str(e)}")


@router.get("/{document_id}/status")
async def get_document_status(
    document_id: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Check if document exists and get its processing status
    """
    try:
        if not document_id or document_id == "undefined" or document_id == "null":
            raise HTTPException(status_code=400, detail="Invalid document ID")
        
        from app.models.document import AcceptedDocument
        from bson import ObjectId
        
        try:
            obj_id = ObjectId(document_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid document ID format")
        
        doc = await AcceptedDocument.find_one({
            "_id": obj_id,
            "user_id": current_user
        })
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "document_id": document_id,
            "filename": doc.filename,
            "status": getattr(doc, 'analysis_status', 'completed'),
            "upload_date": doc.upload_date.isoformat(),
            "exists": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking document status {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Error checking document status")