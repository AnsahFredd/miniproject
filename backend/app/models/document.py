from beanie import Document
from pydantic import Field
from typing import Any, Dict, Optional, List
from datetime import datetime,timezone
from beanie import PydanticObjectId
from app.schemas.ai_extraction import ExpiryExtractionResponse

class AcceptedDocument(Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    user_id: str
    filename: str
    file_type: str
    content: Optional[str] = None
    summary: Optional[str] = None
    section: Optional[str] = None
      
    # Embedding Fields
    embedding: Optional[List[float]] = None  # For AI features
    chunks: Optional[List[str]] = Field(default_factory=list) # Split chunks from full content
    embedding_chunks: Optional[List[float]] = Field(default_factory=list) # List of vectors
    embedding_generated_at: Optional[datetime] = None

    tags: Optional[List[str]] = Field(default_factory=list)
    processed: bool = False
    confidence_score: Optional[float] = None
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    expiry_analysis: Optional[ExpiryExtractionResponse] = None
    analyzed_by: Optional[str] = None
    last_analyzed: Optional[datetime] = None  

    analysis_status: Optional[str] = Field(default="pending")  # pending, processing, completed, failed
    questions_asked: Optional[List[Dict[str, Any]]] = Field(default_factory=list)  # Store Q&A history
    contract_analyzed: bool = False  # Simple boolean flag
    analysis_completed_at: Optional[datetime] = None  # When analysis was completed

    # Additional fields for better tracking
    document_type: Optional[str] = None  # contract, lease, agreement, etc.
    analysis_results: Optional[Dict[str, Any]] = Field(default_factory=dict)  # Store analysis results


    class Settings:
        name = "documents"

    class Config:
        populate_by_name = True
        json_encoders = {PydanticObjectId: str}
