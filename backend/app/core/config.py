"""Enhanced configuration with better organization and validation."""

from typing import List, Optional
from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    DB_URI: str = "mongodb://localhost:27017"  # default fallback
    DB_NAME: str = "lawlens"
    
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)


class SecuritySettings(BaseSettings):
    """Security and authentication configuration."""
    JWT_SECRET: str = Field(..., description="JWT secret key")
    JWT_REFRESH_TOKEN: str = Field(..., description="JWT refresh token secret")
    ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access token expiry in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiry in days")
    ALLOWED_HOSTS: List[str] = Field(default_factory=list, description="Allowed CORS hosts")

    NEWS_API_KEY: str = Field(..., description="News API")
    # Pagination
    NEWS_DEFAULT_PAGE_SIZE: int = 12
    NEWS_MAX_PAGE_SIZE: int = 100

    # Search Configuration  
    NEWS_SEARCH_DAYS_BACK: int = 30             # How many days back to search
    NEWS_ENABLE_BROAD_SEARCH: bool = True        # Enable fallback broad search

    # Rate Limiting & Timeouts
    NEWS_MAX_RETRIES: int = 3
    NEWS_REQUEST_TIMEOUT: int = 30
    DEFAULT_NEWS_SOURCES: str = Field(
        "business, tech, general",
        description="business, tech, general"
    )


class AIModelSettings(BaseSettings):
    """AI model configuration."""
    HF_API_TOKEN: str = Field(..., description="HuggingFace API token")
    HUGGINGFACE_CACHE_DIR: str = Field(default="./cache")
    TRANSFORMERS_CACHE: str = Field(..., description="Transformers cache directory")

    # Model URLs
    QA_MODEL: Optional[str] = Field(default=None)
    LEGAL_QA_MODEL: Optional[str] = Field(default=None)
    SUMMARIZATION_MODEL: Optional[str] = Field(default=None)
    EMBEDDING_MODEL: Optional[str] = Field(default=None)
    CLASSIFICATION_MODEL: Optional[str] = Field(default=None)
    LEGAL_NAME_MODEL: Optional[str] = Field(default=None)
    
    # Download settings
    HF_HUB_ENABLE_HF_TRANSFER: int = Field(default=1)
    HF_HUB_DOWNLOAD_TIMEOUT: int = Field(default=3600)
    MODEL_DOWNLOAD_RETRIES: int = Field(default=10)
    MODEL_DOWNLOAD_RETRY_DELAY_S: int = Field(default=30)
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)


class DocumentProcessingSettings(BaseSettings):
    """Document processing configuration."""
    MAX_TEXT_LENGTH: int = Field(default=100_000)
    CONFIDENCE_THRESHOLD: float = Field(default=0.7)
    MAX_FILE_SIZE: int = Field(default=10_000_000)
    SUPPORTED_FORMATS: str = Field(default="pdf,docx,txt")
    CHUNK_SIZE: int = Field(default=500)
    CHUNK_OVERLAP: int = Field(default=50)
    MAX_TOKENS: int = Field(default=1024)

    MODEL_MAX_LENGTH: int = Field(default=1024)  
    PROCESSING_MAX_LENGTH: int = Field(default=512) 
    ENABLE_TRUNCATION: bool = Field(default=True)  
    CHUNK_STRATEGY: str = Field(default="smart") 
    
    @computed_field
    @property
    def SUPPORTED_FORMATS_LIST(self) -> List[str]:
        """Get supported formats as a list."""
        return [fmt.strip() for fmt in self.SUPPORTED_FORMATS.split(",")]
    
    model_config = SettingsConfigDict(case_sensitive=False)


class PerformanceSettings(BaseSettings):
    """Performance and processing configuration."""
    BATCH_SIZE: int = Field(default=32)
    MAX_WORKERS: int = Field(default=4)
    ENABLE_ASYNC_PROCESSING: bool = Field(default=True)
    CONCURRENT_REQUESTS: int = Field(default=5)
    
    # Summarization specific
    SUMMARIZATION_ASYNC_THRESHOLD_WORDS: int = Field(default=2000)
    SUMMARIZATION_MAX_BUDGET_S: int = Field(default=60)
    SUMMARIZATION_MAX_SUMMARY_WORDS: int = Field(default=500)
    
    model_config = SettingsConfigDict(case_sensitive=False)


class ExternalServicesSettings(BaseSettings):
    """External services configuration."""
    # Redis Cloud Configuration
    REDIS_URL: str = Field(
        default="redis://default:password@redis-14071.c57.us-east-1-4.ec2.redns.redis-cloud.com:14071",
        description="Redis Cloud connection URL"
    )
    
    # Alternative Redis settings (if you prefer individual components)
    REDIS_HOST: str = Field(
        default="redis-14071.c57.us-east-1-4.ec2.redns.redis-cloud.com",
        description="Redis host"
    )
    REDIS_PORT: int = Field(default=14071, description="Redis port")
    REDIS_USERNAME: str = Field(default="default", description="Redis username")
    REDIS_PASSWORD: str = Field(default="password", description="Redis password")
    
    # Celery Configuration (using Redis Cloud)
    CELERY_BROKER_URL: Optional[str] = Field(default=None, description="Celery broker URL")
    CELERY_BACKEND_URL: Optional[str] = Field(default=None, description="Celery backend URL")

    CELERY_TASK_DEFAULT_QUEUE: str = Field(default="lawlens", description="Default Celery task queue")
    CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS: dict = Field(
        default_factory=lambda: {"global_keyprefix": "lawlens:"},
        description="Celery result backend transport options"
    )

    # Redis Cloud Optimizations
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP: bool = Field(default=True, description="Enable Celery broker connection retry on startup")
    CELERY_TASK_SOFT_TIME_LIMIT: int = Field(default=600, description="Celery task soft time limit in seconds")
    CELERY_TASK_TIME_LIMIT: int = Field(default=900, description="Celery task hard time limit in seconds")
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = Field(default=1, description="Celery worker prefetch multiplier")
    
    def prepare_redis_url(self, url: str) -> str:
        """Prepare Redis URL with proper SSL and database configuration."""
        if not url:
            url = self.REDIS_URL
            
        # Ensure database index
        if not any(url.endswith(f'/{i}') for i in range(10)):
            if not url.endswith('/'):
                url += '/0'
            else:
                url += '0'
        
        # Add SSL parameter for secure Redis
        if url.startswith("rediss://") and "ssl_cert_reqs" not in url:
            separator = "?" if "?" not in url else "&"
            url += f"{separator}ssl_cert_reqs=CERT_NONE"
            
        return url
    
    def get_effective_celery_broker_url(self) -> str:
        """Get effective Celery broker URL, defaulting to Redis URL if not set."""
        broker_url = self.CELERY_BROKER_URL or self.REDIS_URL
        return self.prepare_redis_url(broker_url)

    def get_effective_celery_backend_url(self) -> str:
        """Get effective Celery backend URL, defaulting to Redis URL if not set."""
        backend_url = self.CELERY_BACKEND_URL or self.REDIS_URL
        return self.prepare_redis_url(backend_url)
    
    # OpenAI
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini")
    
    # SMTP
    SMTP_HOST: str = Field(..., description="SMTP host")
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: str = Field(..., description="SMTP username")
    SMTP_PASSWORD: str = Field(..., description="SMTP password")
    SMTP_FROM: str = Field(..., description="SMTP from address")
    SMTP_TLS: bool = Field(default=True)
    SMTP_SSL: bool = Field(default=False)
    RESET_TOKEN_EXPIRE_HOURS: int = Field(default=2)
    
    model_config = SettingsConfigDict(case_sensitive=False)


class Settings(BaseSettings):
    """Main application settings."""
    
    @property
    def DB_URI(self) -> str:
        return self.DATABASE.DB_URI
    
    @property
    def DB_NAME(self) -> str:
        return self.DATABASE.DB_NAME
    
    @property
    def CELERY_TASK_DEFAULT_QUEUE(self) -> str:
        """Get Celery default queue."""
        return self.EXTERNAL_SERVICES.CELERY_TASK_DEFAULT_QUEUE

    @property
    def CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS(self) -> dict:
        """Get Celery result backend transport options."""
        return self.EXTERNAL_SERVICES.CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS
    
    # Convenience properties for new Celery settings
    @property
    def CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP(self) -> bool:
        """Get Celery broker connection retry setting."""
        return self.EXTERNAL_SERVICES.CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP
    
    @property
    def CELERY_TASK_SOFT_TIME_LIMIT(self) -> int:
        """Get Celery task soft time limit."""
        return self.EXTERNAL_SERVICES.CELERY_TASK_SOFT_TIME_LIMIT
    
    @property
    def CELERY_TASK_TIME_LIMIT(self) -> int:
        """Get Celery task time limit."""
        return self.EXTERNAL_SERVICES.CELERY_TASK_TIME_LIMIT

    @property
    def CELERY_WORKER_PREFETCH_MULTIPLIER(self) -> int:
        """Get Celery worker prefetch multiplier."""
        return self.EXTERNAL_SERVICES.CELERY_WORKER_PREFETCH_MULTIPLIER

    # Include security settings directly
    JWT_SECRET: str
    JWT_REFRESH_TOKEN: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Application settings
    DEBUG: bool = Field(default=True)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    ENV: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_WINDOW: int = Field(default=60)
    
    # Caching
    ENABLE_CACHING: bool = Field(default=True)
    CACHE_TTL: int = Field(default=300)
    
    # Search
    VECTOR_STORE_PATH: str = Field(default="/data/vector_store")
    SEARCH_RESULTS_LIMIT: int = Field(default=10)
    
    # CORS
    CORS_ORIGINS: List[str] = Field(default_factory=list)
    
    # Nested settings
    DATABASE: DatabaseSettings = Field(default_factory=DatabaseSettings)
    SECURITY: SecuritySettings = Field(default_factory=SecuritySettings)
    AI_MODELS: AIModelSettings = Field(default_factory=AIModelSettings)
    DOCUMENT_PROCESSING: DocumentProcessingSettings = Field(default_factory=DocumentProcessingSettings)
    PERFORMANCE: PerformanceSettings = Field(default_factory=PerformanceSettings)
    EXTERNAL_SERVICES: ExternalServicesSettings = Field(default_factory=ExternalServicesSettings)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False
    )
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            cleaned = v.strip().strip("[]")
            return [p.strip().strip('"').strip("'") for p in cleaned.split(",") if p.strip()]
        return v
    
    def model_post_init(self, __context) -> None:
        """Set environment-specific CORS origins."""
        if self.ENV == "production":
            self.CORS_ORIGINS = [
                "https://lawlens-mu.vercel.app",
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
            ]
    
    @property
    def FRONTEND_URL(self) -> str:
        """Return the primary frontend URL for building links in emails etc"""
        return self.CORS_ORIGINS[0]
    
    # Convenience properties for Redis access
    @property
    def REDIS_URL(self) -> str:
        """Get Redis URL from external services."""
        return self.EXTERNAL_SERVICES.REDIS_URL
    
    @property
    def CELERY_BROKER_URL(self) -> str:
        """Get Celery broker URL."""
        return self.EXTERNAL_SERVICES.get_effective_celery_broker_url()
    
    @property
    def CELERY_BACKEND_URL(self) -> str:
        """Get Celery backend URL."""
        return self.EXTERNAL_SERVICES.get_effective_celery_backend_url()


# Instantiate settings
settings = Settings()