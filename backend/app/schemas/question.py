from typing import List, Optional
from pydantic import BaseModel


class SearchContext(BaseModel):
    id: str
    title: str
    section: str
    description: str
    similarity_score: float


class QuestionRequest(BaseModel):
    question: str
    context: Optional[List[SearchContext]] = None
    document_id: Optional[str] = None


class QuestionResponse(BaseModel):
    answer: str
    confidence_score: float
    source_document: Optional[str] = None

''