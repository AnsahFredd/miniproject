from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
from collections import defaultdict, deque
from typing import Dict, Deque

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        calls: int = 100,  # Max calls per window
        period: int = 60,  # Time window in seconds
        exempt_paths: list = None  # Paths to exempt from rate limiting
    ):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.exempt_paths = exempt_paths or []
        # Use deque to store timestamps for each IP
        self.clients: Dict[str, Deque[float]] = defaultdict(lambda: deque())

    def _is_exempt_path(self, path: str) -> bool:
        """Check if the path should be exempt from rate limiting"""
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False

    def _clean_old_requests(self, client_history: Deque[float], current_time: float):
        """Remove requests older than the time window"""
        while client_history and client_history[0] <= current_time - self.period:
            client_history.popleft()

    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client has exceeded rate limit"""
        current_time = time.time()
        client_history = self.clients[client_ip]
        
        # Clean old requests
        self._clean_old_requests(client_history, current_time)
        
        # Check if limit exceeded
        if len(client_history) >= self.calls:
            return True
        
        # Add current request
        client_history.append(current_time)
        return False

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if path is exempt
        if self._is_exempt_path(request.url.path):
            return await call_next(request)
        
        # Check rate limit
        if self._is_rate_limited(client_ip):
            raise HTTPException(
                status_code=429, 
                detail={
                    "error": "Too many requests",
                    "message": f"Rate limit exceeded. Max {self.calls} requests per {self.period} seconds.",
                    "retry_after": self.period
                }
            )
        
        return await call_next(request)



