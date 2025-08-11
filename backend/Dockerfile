# ---------- Base build image ----------
FROM python:3.11-slim AS build

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NLTK_DATA=/app/nltk_data \
    HF_HOME=/app/ai/models

WORKDIR /app

# Install build dependencies in single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements early for better layer caching
COPY requirements.txt .

# Install Python dependencies (including uvicorn here to avoid reinstalling later)
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install uvicorn[standard]

# Copy only necessary app code (exclude models via .dockerignore)
COPY . /app

# Create NLTK data directory and try to download punkt
RUN mkdir -p /app/nltk_data && \
    python -c "import nltk; nltk.download('punkt', download_dir='/app/nltk_data')" || echo "NLTK download will happen at runtime"

# ---------- Runtime image ----------
FROM python:3.11-slim AS runtime

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NLTK_DATA=/app/nltk_data \
    HF_HOME=/app/ai/models

WORKDIR /app

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user first
RUN useradd --create-home --shell /bin/bash app

# Copy Python environment from build stage
COPY --from=build /usr/local /usr/local

# Copy only necessary app code from build stage
COPY --from=build --chown=app:app /app /app

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
