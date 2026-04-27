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

from pydantic import BaseModel, Field, field_validator, model_validator


def _load_dotenv_defaults(env_path: Path) -> None:
    """Load `.env` key/values only when not already present in the process env."""
    if not env_path.exists():
        return
    try:
        raw = env_path.read_text(encoding="utf-8")
    except OSError:
        return

    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or key in os.environ:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ[key] = value


def _load_env_chain(repo_root: Path) -> None:
    """Load env files in priority order. Earlier wins because the loader
    only fills keys that are not yet present in os.environ.

      1. .env.local                  (machine-local overrides, gitignored)
      2. .env.<APP_ENV>              (e.g. .env.development; APP_ENV from process env)
      3. .env                        (base/production defaults committed for the prod target)
    """
    _load_dotenv_defaults(repo_root / ".env.local")
    app_env = os.environ.get("APP_ENV", "").strip().lower()
    if app_env:
        _load_dotenv_defaults(repo_root / f".env.{app_env}")
    _load_dotenv_defaults(repo_root / ".env")


_load_env_chain(Path(__file__).resolve().parents[2])


class DatabaseSettings(BaseModel):
    """Database configuration."""

    url: str = Field(
        default="sqlite:///./data/Sentifargo.db", description="Database connection URL"
    )
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
    allowed_hosts: list[str] = Field(default=["*"], description="Allowed hostnames")
    force_https: bool = Field(default=False, description="Redirect HTTP to HTTPS")
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=100, description="Requests per window")
    rate_limit_window: int = Field(default=60, description="Window in seconds")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [host.strip() for host in v.split(",") if host.strip()]
        return v

    @field_validator("force_https", mode="before")
    @classmethod
    def parse_force_https(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.strip().lower() in {"1", "true", "yes", "on"}
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
    anthropic_api_key: str | None = None


class AgentSettings(BaseModel):
    """Multi-agent (Claude) configuration."""

    planner_model: str = Field(default="claude-opus-4-7")
    triage_model: str = Field(default="claude-haiku-4-5")
    synthesis_model: str = Field(default="claude-haiku-4-5")
    thinking_budget: int = Field(default=4000, ge=0, le=64000)
    max_tool_calls: int = Field(default=8, ge=1, le=64)
    max_tokens_per_turn: int = Field(default=30000, ge=1024, le=200000)
    cache_ttl_seconds: int = Field(default=300, ge=60, le=3600)
    confidence_escalation_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    llm_mode: Literal["offline", "online", "auto"] = Field(default="auto")


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
    app_env: Literal["development", "staging", "production", "test"] = Field(default="development")
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
    agent: AgentSettings = Field(default_factory=AgentSettings)

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.app_env != "production":
            return self

        if not self.security.secret_key.strip():
            raise ValueError("SECRET_KEY must be set for production deployments")

        if not self.security.cors_origins or any(
            origin == "*" or not origin.strip() for origin in self.security.cors_origins
        ):
            raise ValueError("CORS_ORIGINS must be explicit for production deployments")

        if not self.security.allowed_hosts or any(
            host == "*" or not host.strip() for host in self.security.allowed_hosts
        ):
            raise ValueError("ALLOWED_HOSTS must be explicit for production deployments")

        if not self.security.force_https:
            raise ValueError("FORCE_HTTPS must be true for production deployments")

        if self.database.url.startswith("sqlite"):
            raise ValueError("DATABASE_URL must point to Postgres in production deployments")

        if not self.redis.url.strip():
            raise ValueError("REDIS_URL must be set for production deployments")

        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


def _load_settings_from_env() -> Settings:
    """Load settings from environment variables."""
    app_env = os.getenv("APP_ENV", "development")
    is_production = app_env == "production"
    return Settings(
        app_name=os.getenv("APP_NAME", "Sentifargo"),
        app_version=os.getenv("APP_VERSION", "1.0.0"),
        app_env=app_env,  # type: ignore
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
            secret_key=os.getenv("SECRET_KEY", "" if is_production else secrets.token_hex(32)),
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
            auth_token=os.getenv("AUTH_TOKEN"),
            cors_origins=os.getenv("CORS_ORIGINS", "" if is_production else "*"),
            allowed_hosts=os.getenv("ALLOWED_HOSTS", "" if is_production else "*"),
            force_https=os.getenv("FORCE_HTTPS", "true" if is_production else "false"),
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
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        ),
        agent=AgentSettings(
            planner_model=os.getenv("AGENT_PLANNER_MODEL", "claude-opus-4-7"),
            triage_model=os.getenv("AGENT_TRIAGE_MODEL", "claude-haiku-4-5"),
            synthesis_model=os.getenv("AGENT_SYNTHESIS_MODEL", "claude-haiku-4-5"),
            thinking_budget=int(os.getenv("AGENT_THINKING_BUDGET", "4000")),
            max_tool_calls=int(os.getenv("AGENT_MAX_TOOL_CALLS", "8")),
            max_tokens_per_turn=int(os.getenv("AGENT_MAX_TOKENS_PER_TURN", "30000")),
            cache_ttl_seconds=int(os.getenv("AGENT_CACHE_TTL_SECONDS", "300")),
            confidence_escalation_threshold=float(
                os.getenv("AGENT_CONFIDENCE_ESCALATION_THRESHOLD", "0.6")
            ),
            llm_mode=os.getenv("LLM_MODE", "auto"),  # type: ignore
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
