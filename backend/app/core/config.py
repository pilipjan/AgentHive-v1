"""AgentHive Configuration Module."""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General Application
    ENVIRONMENT: str = Field(default="development", description="Runtime environment")
    DEBUG: bool = Field(default=False, description="Debug mode flag")
    APP_NAME: str = Field(default="AgentHive", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    PORT: int = Field(default=8000, description="Backend listening port")
    HOST: str = Field(default="0.0.0.0", description="Backend listening host")
    API_PREFIX: str = Field(default="/api/v1", description="API route prefix")
    SECRET_KEY: str = Field(
        default="dummy-development-secret-key-change-in-production-min-32-chars",
        description="JWT and hashing secret key",
    )

    # Database Settings
    POSTGRES_USER: str = Field(default="agenthive", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(default="agenthive_dev_password_only", description="PostgreSQL password")
    POSTGRES_DB: str = Field(default="agenthive", description="PostgreSQL database name")
    POSTGRES_HOST: str = Field(default="127.0.0.1", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5433, description="PostgreSQL port")
    DATABASE_URL: Optional[str] = Field(
        default="postgresql+asyncpg://agenthive:agenthive_dev_password_only@127.0.0.1:5433/agenthive",
        description="Async SQLAlchemy database connection URL",
    )

    # Model Provider Settings
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API Key")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API Key")
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API Key")
    OLLAMA_BASE_URL: str = Field(default="http://127.0.0.1:11434", description="Ollama inference endpoint")

    # Guardrails & Operational Limits
    MAX_TASK_RECURSION_DEPTH: int = Field(default=5, description="Max depth of task decomposition")
    MAX_AGENT_MESSAGE_CHAIN: int = Field(default=10, description="Max consecutive agent messages")
    TASK_TIMEOUT_SECONDS: int = Field(default=120, description="Max task execution duration")
    MEMORY_FIREWALL_STRICT_MODE: bool = Field(default=True, description="Strict secret/PII blocking")
    ENABLE_SIMULATED_TOOLS: bool = Field(default=True, description="Enable simulated agent tool execution")

    # CORS & Network
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
        description="Allowed CORS origins",
    )


settings = Settings()
