from beanie import Document
from pydantic import Field
from datetime import datetime
from beanie import PydanticObjectId
from typing import Optional, Dict, Any


class RejectedDocument(Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    user_id: str
    filename: str
    file_type: str
    reason: str
    reviewed: bool = False
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    validation_details: Optional[Dict[str, Any]] = Field(default=None)

    class Settings:
        name = "rejected_documents"

    class Config:
        populate_by_name = True
        json_encoders = {PydanticObjectId: str}
