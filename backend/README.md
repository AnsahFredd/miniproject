# LawLens Legal AI Assistant Backend

A comprehensive legal AI assistant backend built with FastAPI, featuring document processing, AI-powered analysis, user authentication, and various AI services for legal document management.

## Features

- **Legal Document Processing**: Upload, analyze, and extract information from legal documents
- **AI-Powered Services**: Summarization, classification, Q&A, and embedding generation
- **User Authentication**: JWT-based authentication with password reset functionality
- **Document Search**: Vector-based document search and retrieval
- **Rate Limiting & Security**: Built-in rate limiting and security headers
- **Async Processing**: Celery integration for background tasks
- **MongoDB Integration**: Document storage and user management
- **HuggingFace Integration**: Multiple AI models for different legal tasks

## Project Structure

\`\`\`
├── main.py                     # FastAPI application entry point
├── core/                       # Core application components
│   ├── config.py              # Configuration management
│   ├── exceptions.py          # Custom exceptions and handlers
│   ├── middleware.py          # Custom middleware
│   └── ...
├── routes/                     # API route handlers
│   ├── auth.py               # Authentication endpoints
│   ├── document.py           # Document management
│   └── ...
├── services/                   # Business logic services
│   ├── auth/                 # Authentication services
│   ├── document/             # Document processing
│   ├── ai/                   # AI services
│   └── ...
├── models/                     # Data models
├── schemas/                    # Pydantic schemas
├── database/                   # Database configuration
├── dependencies/               # FastAPI dependencies
├── middleware/                 # Custom middleware
├── crud/                       # Database operations
├── scripts/                    # Utility scripts
└── utils/                      # Common utilities
\`\`\`

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see `.env.example`)
4. Run the application: `python main.py`

## Environment Variables

See `.env.example` for required environment variables including:
- Database configuration
- JWT secrets
- HuggingFace API tokens
- External service credentials

## API Documentation

When running in development mode, API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

This project is licensed under the MIT License.
\`\`\`

```python file=".env.example"
# Application Settings
ENV=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Database
DB_URI=mongodb://localhost:27017
DB_NAME=lawlens

# Security
SECURITY_JWT_SECRET=your-super-secret-jwt-key-here
SECURITY_JWT_REFRESH_TOKEN=your-refresh-token-secret-here
SECURITY_ALGORITHM=HS256
SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES=15
SECURITY_REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Models
AI_HUGGINGFACE_API_TOKEN=your-huggingface-token-here
AI_HUGGINGFACE_CACHE_DIR=./cache
AI_TRANSFORMERS_CACHE=./transformers_cache

# Document Processing
DOC_MAX_TEXT_LENGTH=100000
DOC_CONFIDENCE_THRESHOLD=0.7
DOC_MAX_FILE_SIZE=10000000
DOC_SUPPORTED_FORMATS=pdf,docx,txt
DOC_CHUNK_SIZE=500
DOC_CHUNK_OVERLAP=50
DOC_MAX_TOKENS=512

# Performance
PERF_BATCH_SIZE=32
PERF_MAX_WORKERS=4
PERF_ENABLE_ASYNC_PROCESSING=true
PERF_CONCURRENT_REQUESTS=5

# External Services
EXT_CELERY_BROKER_URL=redis://localhost:6379/0
EXT_CELERY_BACKEND_URL=redis://localhost:6379/0
EXT_REDIS_URL=redis://localhost:6379/0
EXT_OPENAI_API_KEY=your-openai-api-key-here
EXT_MODEL=gpt-4o-mini

# SMTP
EXT_SMTP_HOST=smtp.gmail.com
EXT_SMTP_PORT=587
EXT_SMTP_USERNAME=your-email@gmail.com
EXT_SMTP_PASSWORD=your-app-password
EXT_SMTP_FROM=your-email@gmail.com
EXT_SMTP_TLS=true
EXT_SMTP_SSL=false
EXT_RESET_TOKEN_EXPIRE_HOURS=24

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Caching
ENABLE_CACHING=true
CACHE_TTL=300

# Search
VECTOR_STORE_PATH=/data/vector_store
SEARCH_RESULTS_LIMIT=10

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173



# ## Local AI Models Setup Guide

# This guide explains how to set up and use local AI models for offline operation.

# ## Overview

# The AI system has been configured to use **only local models** with no online dependencies. All Hugging Face API calls and automatic model downloads have been removed.

# ## Quick Start

# 1. **Run the setup script:**
#    \`\`\`bash
#    python scripts/setup_local_models.py
#    \`\`\`

# 2. **Create model directories:**
#    \`\`\`bash
#    python scripts/setup_local_models.py create-dirs
#    \`\`\`

# 3. **Download models** (see detailed instructions below)

# 4. **Validate setup:**
#    \`\`\`bash
#    python scripts/setup_local_models.py validate
#    \`\`\`

# ## Model Directory Structure

# \`\`\`
# ./models/
# ├── summarization/
# │   ├── config.json
# │   ├── pytorch_model.bin
# │   ├── tokenizer.json
# │   └── tokenizer_config.json
# ├── classification/
# │   ├── config.json
# │   ├── pytorch_model.bin
# │   ├── tokenizer.json
# │   └── tokenizer_config.json
# ├── qa/
# │   ├── config.json
# │   ├── pytorch_model.bin
# │   ├── tokenizer.json
# │   └── tokenizer_config.json
# └── embedding/
#     ├── config.json
#     ├── pytorch_model.bin
#     ├── tokenizer.json
#     └── tokenizer_config.json
# \`\`\`

# ## Downloading Models

# ### Method 1: Hugging Face CLI (Recommended)

# \`\`\`bash
# # Install Hugging Face CLI
# pip install huggingface_hub

# # Download models
# huggingface-cli download facebook/bart-large-cnn --local-dir ./models/summarization
# huggingface-cli download microsoft/DialoGPT-medium --local-dir ./models/classification  
# huggingface-cli download deepset/roberta-base-squad2 --local-dir ./models/qa
# huggingface-cli download sentence-transformers/all-MiniLM-L6-v2 --local-dir ./models/embedding
# \`\`\`

# ### Method 2: Python Script

# ```python
# from transformers import AutoModel, AutoTokenizer

# # Example for summarization model
# model = AutoModel.from_pretrained('facebook/bart-large-cnn')
# tokenizer = AutoTokenizer.from_pretrained('facebook/bart-large-cnn')
# model.save_pretrained('./models/summarization')
# tokenizer.save_pretrained('./models/summarization')
