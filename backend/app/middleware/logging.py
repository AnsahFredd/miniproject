import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url.path)
        
        try:
            response: Response = await call_next(request)
            process_time = time.time() - start_time
            
            # Safely get status code
            status_code = getattr(response, 'status_code', 500)
            
            # Log successful requests
            logger.info(
                "SUCCESS %s - [%s] %s (%.2fs): %d",
                client_ip,
                method,
                url,
                process_time,
                status_code
            )
            
            return response
            
        except Exception as exc:
            process_time = time.time() - start_time
            
            # Handle HTTPException specifically
            if hasattr(exc, 'status_code'):
                status_code = exc.status_code
                detail = getattr(exc, 'detail', str(exc))
            else:
                status_code = 500
                detail = str(exc)
            
            logger.error(
                "ERROR %s - [%s] %s (%.2fs): %d - %s",
                client_ip,
                method,
                url,
                process_time,
                status_code,
                detail
            )
            
            # Re-raise the exception
            raise exc