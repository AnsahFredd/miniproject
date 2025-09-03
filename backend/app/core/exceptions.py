"""Global exception handlers and custom exceptions."""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import traceback
import uuid

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base API error with structured response."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = None,
        details: Dict[str, Any] = None,
        user_action: str = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "INTERNAL_ERROR"
        self.details = details or {}
        self.user_action = user_action
        super().__init__(message)

class ValidationError(APIError):
    """Validation error with field-specific details."""
    
    def __init__(self, message: str, field_errors: Dict[str, str] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"field_errors": field_errors or {}},
            user_action="Please check the highlighted fields and try again."
        )

class AuthenticationError(APIError):
    """Authentication-related errors."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            user_action="Please log in to continue."
        )

class AuthorizationError(APIError):
    """Authorization-related errors."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            user_action="You don't have permission to perform this action."
        )

class NotFoundError(APIError):
    """Resource not found errors."""
    
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            error_code="NOT_FOUND",
            user_action="Please check the URL or resource identifier."
        )

class RateLimitError(APIError):
    """Rate limiting errors."""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Too many requests",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
            user_action=f"Please wait {retry_after} seconds before trying again."
        )

def create_error_response(
    error: Exception,
    request: Request = None,
    include_traceback: bool = False
) -> Dict[str, Any]:
    """Create standardized error response."""
    
    error_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    if isinstance(error, APIError):
        response = {
            "error": True,
            "error_id": error_id,
            "timestamp": timestamp,
            "message": error.message,
            "error_code": error.error_code,
            "status_code": error.status_code,
            "details": error.details,
            "user_action": error.user_action
        }
    elif isinstance(error, HTTPException):
        response = {
            "error": True,
            "error_id": error_id,
            "timestamp": timestamp,
            "message": str(error.detail),
            "error_code": "HTTP_ERROR",
            "status_code": error.status_code,
            "details": {},
            "user_action": "Please try again or contact support if the problem persists."
        }
    else:
        # Generic error
        response = {
            "error": True,
            "error_id": error_id,
            "timestamp": timestamp,
            "message": "An unexpected error occurred",
            "error_code": "INTERNAL_ERROR",
            "status_code": 500,
            "details": {},
            "user_action": "Please try again. If the problem persists, contact support."
        }
    
    # Add request context if available
    if request:
        response["request_info"] = {
            "method": request.method,
            "url": str(request.url),
            "user_agent": request.headers.get("user-agent", "unknown")
        }
    
    # Add traceback for debugging (only in development)
    if include_traceback and hasattr(error, '__traceback__'):
        response["traceback"] = traceback.format_exception(
            type(error), error, error.__traceback__
        )
    
    # Log the error
    logger.error(
        f"API Error [{error_id}]: {response['message']}",
        extra={
            "error_id": error_id,
            "error_code": response["error_code"],
            "status_code": response["status_code"],
            "request_method": request.method if request else None,
            "request_url": str(request.url) if request else None
        },
        exc_info=True
    )
    
    return response

async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors."""
    response = create_error_response(exc, request)
    return JSONResponse(
        status_code=exc.status_code,
        content=response
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    response = create_error_response(exc, request)
    return JSONResponse(
        status_code=exc.status_code,
        content=response
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    field_errors = {}
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        field_errors[field_path] = error["msg"]
    
    validation_error = ValidationError(
        message="Request validation failed",
        field_errors=field_errors
    )
    
    response = create_error_response(validation_error, request)
    return JSONResponse(
        status_code=422,
        content=response
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    response = create_error_response(exc, request, include_traceback=False)
    return JSONResponse(
        status_code=500,
        content=response
    )
