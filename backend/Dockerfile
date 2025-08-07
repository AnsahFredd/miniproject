# ---------- Base build image ----------
FROM python:3.11-slim AS build
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements early for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy app code and local models
COPY . /app

ENV NLTK_DATA=/app/nltk_data
ENV HF_HOME=/app/ai/models

# ---------- Runtime image ----------
FROM python:3.11-slim AS runtime
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NLTK_DATA=/app/nltk_data \
    HF_HOME=/app/ai/models

WORKDIR /app

# System runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy entire Python env including site-packages
COPY --from=build /usr/local /usr/local

# Copy app code and data
COPY --from=build /app /app
RUN pip install uvicorn[standard]

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app && \
    mkdir -p /app/nltk_data && \
    chown -R app:app /app/nltk_data
USER app

# Try downloading punkt (fails silently if no network)
RUN python -c "import nltk; nltk.download('punkt', download_dir='/app/nltk_data')" || echo "NLTK download will happen at runtime"

# Port for Render
EXPOSE 8000

# Start server
