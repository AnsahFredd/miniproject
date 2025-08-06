from pydantic import BaseModel, Field
from typing import Optional, List
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



class AcceptedDocumentCreate(AcceptedDocumentBase):
    user_id: str


class AcceptedDocumentRead(AcceptedDocumentBase):
    id: str = Field(alias="_id")
    user_id: str
    upload_date: datetime

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


class RejectedDocumentCreate(RejectedDocumentBase):
    user_id: str


class RejectedDocumentRead(RejectedDocumentBase):
    id: str = Field(alias="_id")
    user_id: str
    upload_date: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        from_attributes = True
