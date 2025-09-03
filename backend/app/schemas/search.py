from pydantic import BaseModel
from typing import List, Optional


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    documentType: Optional[str] = None
    legalDomain: Optional[str] = None
    dateRange: Optional[str] = None


class SearchResult(BaseModel):
    document_id: str
    title: str
    section: str
    description: str
    similarity_score: float


class SearchResponse(BaseModel):
    results: List[SearchResult]
