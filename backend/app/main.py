from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.middleware.logging import LoggingMiddleware
from app.database.mongo import connect_to_mongo, close_mongo_connection
from app.routes.document_analysis import router as document_analysis_router
from app.routes.ai_extraction import router as expiry_extraction_router
from app.routes.user import router as user_router
from app.routes.search import router as search_router
from app.routes.embedding import router as embeddings_router
from app.routes.question import router as question_router
from app.routes.document import router as document_router
from app.core.rate_limiter import RateLimitMiddleware


# Import routers
from app.routes import (
    auth,
    summarize,
    chat,
)

# Lifespan event for startup/shutdown

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


# FastAPI App

app = FastAPI(
    title="LawLens API",
    version="1.0.0",
    description="Legal AI assistant backend",
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)     

# Add CORS middleware with proper configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,  # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
    # max_age=600,  # Cache preflight requests for 10 minutes
)


app.add_middleware(
    RateLimitMiddleware, 
    calls=100, 
    period=60,
    exempt_paths=[
        "/api/v1/auth/verify-reset-token",  # Exempt password reset verification
        "/api/v1/auth/password-reset",      # Exempt password reset
        "/api/v1/auth/forgot-password",     # Exempt forgot password
        "/docs",                            # Exempt API docs
        "/redoc",                          # Exempt API docs
        "/openapi.json",                   # Exempt OpenAPI spec
        ]
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "FastAPI server is running",
        "environment": settings.ENV,
    }

# Middleware
app.add_middleware(LoggingMiddleware)

# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(document_router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(question_router,prefix="/api/v1/questions", tags=["Questions"])
app.include_router(document_analysis_router)
app.include_router(summarize.router, prefix="/api/v1/summarize", tags=["Summarization"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])
app.include_router(embeddings_router, prefix="/api/v1/embedding", tags=["Embeddings"])
app.include_router(expiry_extraction_router, prefix="/api/v1/expiry", tags=["Expiry Analysis"])
app.include_router(user_router, prefix="/api/v1/user")

