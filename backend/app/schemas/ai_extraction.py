# Extract expiry dates of contracts
from typing import Optional

from pydantic import BaseModel



class ExpiryExtractionRequest(BaseModel):
    document_id: str
    prompt: Optional[str] = None

class ExpiryExtractionResponse(BaseModel):
    expiry_date: Optional[str] = None
    contract_name: Optional[str] = None
    contract_title: Optional[str] = None
    confidence: Optional[float] = None
    extracted_text: Optional[str] = None
    error: Optional[str] = None