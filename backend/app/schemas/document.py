from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional, List, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

class AcceptedDocumentBase(BaseModel):
    filename: str
    file_type: str
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = []
    processed: bool = False
    confidence_score: Optional[float] = None
    classification_result: Optional[Dict[str, Any]] = None
    contract_validation: Optional[Dict[str, Any]] = None

class AcceptedDocumentCreate(AcceptedDocumentBase):
    user_id: str

class AcceptedDocumentRead(AcceptedDocumentBase):
    id: str = Field(alias="_id")
    user_id: str
    upload_date: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_objectid_to_str(cls, v: Any) -> str:
        """Convert ObjectId to string"""
        if isinstance(v, ObjectId):
            return str(v)
        return v

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        from_attributes = True

# === Rejected Document Schemas ===

class RejectedDocumentBase(BaseModel):
    filename: str
    file_type: str
    reason: str
    reviewed: bool = False
    validation_details: Optional[Dict[str, Any]] = None

class RejectedDocumentCreate(RejectedDocumentBase):
    user_id: str

class RejectedDocumentRead(RejectedDocumentBase):
    id: str = Field(alias="_id")
    user_id: str
    upload_date: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_objectid_to_str(cls, v: Any) -> str:
        """Convert ObjectId to string"""
        if isinstance(v, ObjectId):
            return str(v)
        return v

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        from_attributes = True
