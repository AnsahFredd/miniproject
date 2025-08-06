from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.services.document_analysis_service import get_document_analysis
from app.dependencies.auth import get_current_user
router = APIRouter(prefix="/api/v1/documents", tags=["Document Analysis"])

@router.get("/{id}/analysis")
async def analyze_document_endpoint(
    id: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive document analysis for the frontend interface
    """
    try:
    
        analysis = await get_document_analysis(id)
        
        if 'error' in analysis:
            raise HTTPException(status_code=400, detail=analysis['error'])
        
        # Format response for frontend consumption
        response = {
            'document_info': {
                **analysis['document_info'],
                'content': analysis['content']
            },
            'clause_overview': analysis['clause_overview'],
            'summary': {
                'text': analysis['summary'],
                'key_points': analysis['key_terms'][:5]  # Top 5 key terms
            },
            'financial_summary': {
                'rent_amount': analysis['financial_info'].get('rent_amount'),
                'deposit': analysis['financial_info'].get('deposit'),
                'other_fees': analysis['financial_info'].get('other_fees', [])
            },
            'parties_involved': analysis['parties'],
            'important_dates': analysis['dates_and_terms']['dates'],
            'term_information': analysis['dates_and_terms']['term_lengths'],
            'metadata': {
                'analyzed_at': datetime.now().isoformat(),
                'user_id': current_user
            }
        }
        
        return response
        
    except Exception as e:
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
        
        doc = await AcceptedDocument.get(id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if doc.user_id != current_user:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            'summary': doc.summary or "Summary not available",
            'filename': doc.filename,
            'document_id': id
        }
        
    except HTTPException:
        raise
    except Exception as e:
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
        analysis = await get_document_analysis(id)
        
        if 'error' in analysis:
            raise HTTPException(status_code=400, detail=analysis['error'])
        
        return {
            'clauses': analysis['clause_overview'],
            'total_clauses': len(analysis['clause_overview']),
            'document_id': id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract clauses: {str(e)}")