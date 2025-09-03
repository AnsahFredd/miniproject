"""Enhanced main application with consistent imports and clean structure."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging

from app.services.model_preloader import model_preloader
from app.core.config import settings
from app.database.mongo import connect_to_mongo, close_mongo_connection
from app.core.exceptions import (
    APIError,
    api_error_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)

from app.core.middleware import (
    RequestLoggingMiddleware, SecurityHeadersMiddleware, RateLimitMiddleware
)

from app.routes.document import router as document_router
from app.routes.auth import router as auth_router
from app.routes.user import router as user_router
from app.routes.search import router as search_router
from app.routes.embedding import router as embedding_router
from app.routes.question import router as question_router
from app.routes.summarize import router as summarize_router
from app.routes.document_analysis import router as document_analysis_router
from app.routes.news import router as news_router
from app.routes.demo import router as demo_router

from app.services.embedding import embedding_service
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    await connect_to_mongo()
    await embedding_service.initialize()

    try:
        await model_preloader.initialize_models()
        logger.info("All AI models initialized successfully at startup.")
    except Exception as e:
        logger.error(f"Failed to initialize AI models at startup: {e}")
    
    yield

    # Shutdown
    await close_mongo_connection()


# FastAPI App with enhanced configuration
app = FastAPI(
    title="LawLens API",
    version="2.0.0",
    description="Enhanced Legal AI assistant backend with robust error handling",
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add enhanced middleware in proper order
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    calls=settings.RATE_LIMIT_REQUESTS,
    period=settings.RATE_LIMIT_WINDOW,
    exempt_paths=[
        "/api/v1/auth/verify-reset-token",
        "/api/v1/auth/password-reset",
        "/api/v1/auth/forgot-password",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health"
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0","models": "models_health"}

# Register all routes with consistent structure
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)
# Add Document Analysis router
app.include_router(
    document_analysis_router,
    prefix="/api/v1/documents",
    tags=["Document Analysis"]
)

app.include_router(
    document_router,
    prefix="/api/v1/documents",
    tags=["Documents"]
)

app.include_router(
    user_router,
    prefix="/api/v1/user",
    tags=["Users"]
)


app.include_router(
    search_router,
    prefix="/api/v1/search",
    tags=["Search"]
)

app.include_router(
    embedding_router,
    prefix="/api/v1/embeddings",
    tags=["Embeddings"]
)

app.include_router(
    question_router,
    prefix="/api/v1/questions",
    tags=["Questions"]
)

app.include_router(
    summarize_router,
    prefix="/api/v1/summarize",
    tags=["Summarization"]
)

app.include_router(
    news_router,
    prefix="/api/v1/news",
    tags=["News"]
)

app.include_router(
    demo_router,
    prefix="/api/v1/demo",
    tags=["Demo Document"]
)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENV == "development"
    )
