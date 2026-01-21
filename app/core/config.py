"""
Sentifargo Production Settings Module
Centralized configuration management with Pydantic
"""

from __future__ import annotations

import os
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class DatabaseSettings(BaseModel):
    """Database configuration."""

    url: str = Field(default="sqlite:///./data/Sentifargo.db", description="Database connection URL")
    pool_size: int = Field(default=5, ge=1, le=50)
    max_overflow: int = Field(default=10, ge=0)
    echo: bool = Field(default=False, description="Echo SQL statements")


class RedisSettings(BaseModel):
    """Redis cache configuration."""

    url: str = Field(default="redis://localhost:6379/0")
    password: str | None = None
    ttl: int = Field(default=3600, description="Default cache TTL in seconds")
    max_connections: int = Field(default=10, ge=1)


class SecuritySettings(BaseModel):
    """Security configuration."""

    secret_key: str = Field(
        default_factory=lambda: secrets.token_hex(32), description="Application secret key"
    )
    access_token_expire_minutes: int = Field(default=30, description="JWT access token TTL")
    refresh_token_expire_days: int = Field(default=7, description="JWT refresh token TTL (days)")
    auth_token: str | None = Field(default=None, description="API authentication token")
    cors_origins: list[str] = Field(default=["*"], description="Allowed CORS origins")
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=100, description="Requests per window")
    rate_limit_window: int = Field(default=60, description="Window in seconds")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


class MLSettings(BaseModel):
    """Machine Learning model configuration."""

    models_dir: Path = Field(default=Path("./models"))
    artifacts_dir: Path = Field(default=Path("./artifacts"))

    # Vision
    vision_model: str = Field(default="yolov8n")
    vision_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)

    # Voice
    voice_emotion_model: str = Field(default="default")
    whisper_model: str = Field(default="base")

    # RAG
    rag_enabled: bool = Field(default=True)
    rag_embeddings_dir: Path = Field(default=Path("./data/embeddings"))
    rag_chunk_size: int = Field(default=1000, ge=100)
    rag_chunk_overlap: int = Field(default=200, ge=0)
    rag_top_k: int = Field(default=5, ge=1)


class ExternalAPISettings(BaseModel):
    """External API configuration."""

    openai_api_key: str | None = None
    openai_model: str = Field(default="gpt-4")
    openai_max_tokens: int = Field(default=2000, ge=100)
    huggingface_token: str | None = None


class MonitoringSettings(BaseModel):
    """Monitoring and observability configuration."""

    prometheus_enabled: bool = Field(default=True)
    prometheus_port: int = Field(default=9090)
    sentry_dsn: str | None = None
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="%(asctime)s %(levelname)s %(name)s %(message)s")


class FeatureFlags(BaseModel):
    """Feature flags for enabling/disabling functionality."""

    fraud_detection: bool = Field(default=True)
    cyber_analysis: bool = Field(default=True)
    behavior_profiling: bool = Field(default=True)
    vision_analysis: bool = Field(default=True)
    voice_emotion: bool = Field(default=True)
    recommendations: bool = Field(default=True)
    rag_chat: bool = Field(default=True)


class Settings(BaseModel):
    """Main application settings."""

    # Application
    app_name: str = Field(default="Sentifargo")
    app_version: str = Field(default="1.0.0")
    app_env: Literal["development", "staging", "production"] = Field(default="development")
    debug: bool = Field(default=False)

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=4, ge=1, le=32)
    timeout: int = Field(default=120, ge=10)
    max_request_size: str = Field(default="50MB")

    # Sub-configurations
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    ml: MLSettings = Field(default_factory=MLSettings)
    external_apis: ExternalAPISettings = Field(default_factory=ExternalAPISettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    features: FeatureFlags = Field(default_factory=FeatureFlags)

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


def _load_settings_from_env() -> Settings:
    """Load settings from environment variables."""
    return Settings(
        app_name=os.getenv("APP_NAME", "Sentifargo"),
        app_version=os.getenv("APP_VERSION", "1.0.0"),
        app_env=os.getenv("APP_ENV", "development"),  # type: ignore
        debug=os.getenv("DEBUG", "false").lower() == "true",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        workers=int(os.getenv("WORKERS", "4")),
        timeout=int(os.getenv("TIMEOUT", "120")),
        max_request_size=os.getenv("MAX_REQUEST_SIZE", "50MB"),
        database=DatabaseSettings(
            url=os.getenv("DATABASE_URL", "sqlite:///./data/Sentifargo.db"),
        ),
        redis=RedisSettings(
            url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            password=os.getenv("REDIS_PASSWORD"),
            ttl=int(os.getenv("CACHE_TTL", "3600")),
        ),
        security=SecuritySettings(
            secret_key=os.getenv("SECRET_KEY", secrets.token_hex(32)),
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
            auth_token=os.getenv("AUTH_TOKEN"),
            cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
        ),
        ml=MLSettings(
            models_dir=Path(os.getenv("MODELS_DIR", "./models")),
            artifacts_dir=Path(os.getenv("ARTIFACTS_DIR", "./artifacts")),
            vision_model=os.getenv("VISION_MODEL", "yolov8n"),
            vision_confidence_threshold=float(os.getenv("VISION_CONFIDENCE_THRESHOLD", "0.5")),
            whisper_model=os.getenv("WHISPER_MODEL", "base"),
            rag_enabled=os.getenv("RAG_ENABLED", "true").lower() == "true",
            rag_chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "1000")),
            rag_top_k=int(os.getenv("RAG_TOP_K", "5")),
        ),
        external_apis=ExternalAPISettings(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4"),
            openai_max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "2000")),
            huggingface_token=os.getenv("HUGGINGFACE_TOKEN"),
        ),
        monitoring=MonitoringSettings(
            prometheus_enabled=os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true",
            prometheus_port=int(os.getenv("PROMETHEUS_PORT", "9090")),
            sentry_dsn=os.getenv("SENTRY_DSN"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        ),
        features=FeatureFlags(
            fraud_detection=os.getenv("FEATURE_FRAUD_DETECTION", "true").lower() == "true",
            cyber_analysis=os.getenv("FEATURE_CYBER_ANALYSIS", "true").lower() == "true",
            behavior_profiling=os.getenv("FEATURE_BEHAVIOR_PROFILING", "true").lower() == "true",
            vision_analysis=os.getenv("FEATURE_VISION_ANALYSIS", "true").lower() == "true",
            voice_emotion=os.getenv("FEATURE_VOICE_EMOTION", "true").lower() == "true",
            recommendations=os.getenv("FEATURE_RECOMMENDATIONS", "true").lower() == "true",
            rag_chat=os.getenv("FEATURE_RAG_CHAT", "true").lower() == "true",
        ),
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return _load_settings_from_env()


# Export settings instance for direct import
settings = get_settings()
