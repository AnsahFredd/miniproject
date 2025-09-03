"""Enhanced middleware for request handling."""

import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
from typing import Callable, List


logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging and timing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        

        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started [{request_id}]: {request.method} {request.url}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "user_agent": request.headers.get("user-agent", "unknown"),
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed [{request_id}]: {response.status_code} in {duration:.3f}s",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration": duration
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed [{request_id}]: {str(e)} in {duration:.3f}s",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "duration": duration
                },
                exc_info=True
            )
            raise

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting middleware."""
    
    def __init__(self, app, calls: int = 100, period: int = 60, exempt_paths: List[str] = None):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.exempt_paths = exempt_paths or []
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if path is exempt
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries
        self.clients = {
            ip: timestamps for ip, timestamps in self.clients.items()
            if any(t > current_time - self.period for t in timestamps)
        }
        
        # Get client's request history
        if client_ip not in self.clients:
            self.clients[client_ip] = []
        
        # Filter recent requests
        self.clients[client_ip] = [
            t for t in self.clients[client_ip]
            if t > current_time - self.period
        ]
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "message": "Too many requests",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": self.period,
                    "user_action": f"Please wait {self.period} seconds before trying again."
                }
            )
        
        # Record this request
        self.clients[client_ip].append(current_time)
        
        return await call_next(request)

