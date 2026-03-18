"""
HRCE Backend — Application Settings
Loads configuration from environment variables / .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_secret_key: str = "change-me"
    debug: bool = True

    # CORS — comma-separated origins, e.g. "http://localhost:3000,https://hrce.example.com"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "hrce"
    postgres_user: str = "hrce_user"
    postgres_password: str = "hrce_password"
    database_url: str = "postgresql+asyncpg://hrce_user:hrce_password@localhost:5432/hrce"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_name: str = "hrce-documents"
    minio_secure: bool = False

    # AI / LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    
    # Groq
    groq_api_key: str = ""
    groq_model: str = "llama3-8b-8192"

    # LangSmith
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "hrce-dev"

    # JWT
    jwt_secret_key: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60


settings = Settings()

