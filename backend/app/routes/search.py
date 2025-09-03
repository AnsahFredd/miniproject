# Search endpoint using embeddings

from fastapi import APIRouter, Depends
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import perform_search
from app.dependencies.auth import get_current_user

router = APIRouter(tags=["Search"])


@router.post("/", response_model=SearchResponse)
async def semantic_search(req: SearchRequest, user: dict = Depends(get_current_user)):
    user_id = str(user.id)
    return await perform_search(
        req.query, req.top_k, 
        user_id=user_id, 
        documentType=req.documentType,  
        legalDomain=req.legalDomain,    
        dateRange=req.dateRange 
        )
