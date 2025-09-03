
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.schemas.news import NewsResponse, NewsSearchParams
from app.services.news_service import news_service

router = APIRouter()

@router.get("/", response_model=NewsResponse)
async def get_news(
    search: Optional[str] = Query(None, description="Search term for articles"),
    category: Optional[str] = Query(None, description="Filter by legal category"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Number of articles per page")
):
    """
    Get legal news articles with optional filtering and pagination
    """
    try:
        # Create search parameters
        params = NewsSearchParams(
            search=search,
            category=category,
            page=page,
            pageSize=page_size
        )
        
        # Get news articles
        result = await news_service.search_news(params)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/categories")
async def get_categories():
    """Get list of available legal categories for filtering"""
    try:
        from app.schemas.news import LEGAL_CATEGORIES
        
        categories = [
            {
                "value": category,
                "label": category.replace("-", " ").title()
            }
            for category in LEGAL_CATEGORIES
        ]
        return {"categories": categories}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint for the news service"""
    return {"status": "healthy", "service": "news-api"}
