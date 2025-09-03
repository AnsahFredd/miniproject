"""Standardized response models."""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    
    success: bool = True
    message: str
    data: Optional[T] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None

class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: bool = True
    error_id: str
    timestamp: datetime
    message: str
    error_code: str
    status_code: int
    details: Dict[str, Any] = Field(default_factory=dict)
    user_action: Optional[str] = None
    request_info: Optional[Dict[str, str]] = None

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    
    success: bool = True
    message: str
    data: List[T]
    pagination: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field details."""
    
    field_errors: Dict[str, str] = Field(default_factory=dict)

def create_success_response(
    data: Any = None,
    message: str = "Success",
    request_id: str = None
) -> Dict[str, Any]:
    """Create standardized success response."""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id
    }

def create_paginated_response(
    data: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "Success"
) -> Dict[str, Any]:
    """Create paginated response."""
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "success": True,
        "message": message,
        "data": data,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "timestamp": datetime.utcnow().isoformat()
    }
