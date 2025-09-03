from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from datetime import datetime

class NewsSource(BaseModel):
    id: Optional[str] = None
    name: str

class NewsAPIArticle(BaseModel):
    source: NewsSource
    author: Optional[str] = None
    title: str
    description: Optional[str] = None
    url: HttpUrl
    urlToImage: Optional[HttpUrl] = None
    publishedAt: str
    content: Optional[str] = None

class NewsAPIResponse(BaseModel):
    status: str
    totalResults: int
    articles: List[NewsAPIArticle]

class LegalNewsItem(BaseModel):
    id: str
    title: str
    summary: str
    publishedDate: str
    source: str
    url: HttpUrl
    imageUrl: Optional[HttpUrl] = None
    category: str
    author: Optional[str] = None

class NewsSearchParams(BaseModel):
    category: Optional[str] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)

class NewsResponse(BaseModel):
    articles: List[LegalNewsItem]
    totalResults: int
    page: int
    pageSize: int
    totalPages: int

class ApiError(BaseModel):
    message: str
    status: int

# Updated legal categories with more focus on contracts and law
LEGAL_CATEGORIES = [
    "contracts",           # NEW: Primary contract category
    "business-law",
    "employment-law", 
    "criminal-law",
    "civil-rights",
    "corporate-law",
    "intellectual-property",
    "environmental-law",
    "healthcare-law",
    "immigration-law",
    "tax-law",
    "real-estate-law",
    "family-law",
    "litigation",          # NEW: Added litigation
    "constitutional-law",  # NEW: Added constitutional
    "regulatory"          # NEW: Added regulatory
]

# Contract-specific subcategories for better filtering
CONTRACT_SUBCATEGORIES = [
    "breach-of-contract",
    "contract-negotiation",
    "employment-contracts",
    "commercial-agreements",
    "licensing-agreements",
    "merger-agreements",
    "real-estate-contracts",
    "construction-contracts",
    "service-agreements",
    "partnership-agreements"
]

# Legal news sources for better targeting
LEGAL_NEWS_SOURCES = [
    "law.com",
    "law360.com", 
    "americanlawyer.com",
    "legaltech.com",
    "courthousenews.com",
    "lexology.com",
    "jdsupra.com",
    "lawandcrime.com",
    "abovethelaw.com",
    "reuters.com",          # Keep for legal business news
    "wsj.com",             # Keep for legal business news
    "bloomberg.com"        # Keep for legal business news
]