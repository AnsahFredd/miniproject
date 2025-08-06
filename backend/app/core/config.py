from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
 

class Settings(BaseSettings):
    # ── Environment ────────────────────────────────────────────────
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENV: str

    # ── Security ───────────────────────────────────────────────────
    ALLOWED_HOSTS: List[str]
    

    # ── Hugging Face & AI ──────────────────────────────────────────
    HUGGINGFACE_API_KEY: str
    HUGGINGFACE_CACHE_DIR: str = "./cache"
    HF_HUB_ENABLE_HF_TRANSFER: int = 1
    HF_HUB_DOWNLOAD_TIMEOUT: int = 1800
    MODEL_DOWNLOAD_RETRIES: int = 10
    MODEL_DOWNLOAD_RETRY_DELAY_S: int = 30

    # ── Celery ─────────────────────────────────────────────────────
    CELERY_BROKER_URL: str
    CELERY_BACKEND_URL: str

    # ── Document Processing ────────────────────────────────────────
    MAX_TEXT_LENGTH: int = 100_000
    CONFIDENCE_THRESHOLD: float = 0.7
    MAX_FILE_SIZE: int = 10_000_000
    SUPPORTED_FORMATS: str = "pdf,docx,txt"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    MAX_TOKENS: int = 512

    # ── Model Paths ────────────────────────────────────────────────
    # Q&A Models for contract question answering
    QA_MODEL: str = "app/ai/models/deberta-v3-large"
    LEGAL_QA_MODEL: str = "app/ai/models/roberta-base-squad2"
    
    # Core AI Models
    SUMMARIZATION_MODEL: str = "app/ai/models/bart-large-cnn"
    EMBEDDING_MODEL: str = "app/ai/models/InLegalBERT"
    CLASSIFICATION_MODEL: str = "app/ai/models/InLegalBERT-classification"
    CLASSIFICATION_MODEL_PATH: str = "app/ai/models/legal-bert-base-uncased"

    # ── Search / Vector Store ──────────────────────────────────────
    VECTOR_STORE_PATH: str = "/data/vector_store"
    SEARCH_RESULTS_LIMIT: int = 10

    # ── Performance ────────────────────────────────────────────────
    BATCH_SIZE: int = 32
    MAX_WORKERS: int = 4
    ENABLE_ASYNC_PROCESSING: bool = True
    CONCURRENT_REQUESTS: int = 5

    # ── Logging 
    LOG_LEVEL: str = "INFO"

    # ── Rate Limiting 
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    # ── Caching 
    ENABLE_CACHING: bool = True
    CACHE_TTL: int = 300

    # ── Redis 
    REDIS_URL: str

    # ── Summarization Runtime Controls 
    SUMMARIZATION_ASYNC_THRESHOLD_WORDS: int = 2000
    SUMMARIZATION_MAX_BUDGET_S: int = 60
    SUMMARIZATION_MAX_SUMMARY_WORDS: int = 500

    # ── OpenAI 
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"

    # ── Database 
    DB_URI: str
    DB_NAME: str

    # ── JWT Auth 
    JWT_SECRET: str
    JWT_REFRESH_TOKEN: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── SMTP / EMAIL 
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM: str
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    RESET_TOKEN_EXPIRE_HOURS: int

    # ── CORS ───────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors_origins(cls, v):
        if isinstance(v, str):
            cleaned = v.strip().strip("[]")
            return [p.strip().strip('"').strip("'") for p in cleaned.split(",") if p.strip()]
        return v

    def model_post_init(self, __context) -> None:
        if self.ENV == "production":
            self.CORS_ORIGINS = [
                 "lawlens-mu.vercel.app",
                "https://www.lawlens.com",
            ]
        elif self.ENV == "staging":
            self.CORS_ORIGINS = [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ]
        else:
            self.CORS_ORIGINS = [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]


# Instantiate settings
settings = Settings()