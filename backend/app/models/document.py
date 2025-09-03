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

    processing_status: str = Field(default="pending")
                                   
    contract_analyzed: bool = False  # Simple boolean flag
    analysis_completed_at: Optional[datetime] = None  # When analysis was completed

    processed_at: Optional[datetime] = None  # When document processing completed
    processing_started_at: Optional[datetime] = None  # When background processing started
    processing_completed_at: Optional[datetime] = None  # When background processing completed
    processing_failed_at: Optional[datetime] = None  # When processing failed
    processing_error: Optional[str] = None  # Error m

    # Additional fields for better tracking
    document_type: Optional[str] = None  # contract, lease, agreement, etc.
    analysis_results: Optional[Dict[str, Any]] = Field(default_factory=dict)  # Store analysis results
    
    classification_result: Optional[Dict[str, Any]] = Field(default=None)  # AI classification results
    contract_validation: Optional[Dict[str, Any]] = Field(default=None)  # Contract validation metadata

    processing_task_id: Optional[str] = None  # Celery task ID for processing


    class Settings:
        name = "documents"

    class Config:
        populate_by_name = True
        json_encoders = {PydanticObjectId: str}

    def set_processing_started(self, task_id: str = None):
        """Mark document as processing started"""
        self.processing_status = "processing"
        self.analysis_status = "processing"
        self.processing_started_at = datetime.now(timezone.utc)
        if task_id:
            self.processing_task_id = task_id

    def set_processing_completed(self):
        """Mark document as processing completed"""
        self.processing_status = "completed"
        self.analysis_status = "completed"
        self.processed = True
        self.contract_analyzed = True
        self.processing_completed_at = datetime.now(timezone.utc)
        self.processed_at = datetime.now(timezone.utc)
        self.analysis_completed_at = datetime.now(timezone.utc)

    def set_processing_failed(self, error_message: str):
        """Mark document as processing failed"""
        self.processing_status = "failed"
        self.analysis_status = "failed"
        self.processing_error = error_message
        self.processing_failed_at = datetime.now(timezone.utc)