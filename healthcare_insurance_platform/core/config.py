"""Configuration management for the Healthcare Insurance Platform."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "testing", "production"] = "development"

    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/healthcare_insurance"
    )
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Vector Database Configuration
    chroma_persist_directory: str = "./data/chroma"
    chroma_collection_name: str = "policy_documents"

    # LLM Configuration
    llm_provider: Literal["openai", "anthropic", "local"] = "openai"
    openai_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_timeout: int = 60  # seconds
    llm_max_retries: int = 3
    llm_retry_delay: float = 1.0  # seconds
    
    # Local LLM Configuration (for local models)
    local_llm_url: str = Field(default="http://localhost:8080")
    local_llm_model: str = Field(default="llama2")

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    api_workers: int = 4

    # Security Configuration
    secret_key: str = Field(default="change_this_in_production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Logging Configuration
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"

    # Rate Limiting
    rate_limit_per_minute: int = 60

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str, info) -> str:
        """Validate OpenAI API key is set when using OpenAI provider."""
        # Only require API key in production and when using OpenAI
        environment = info.data.get('environment', 'development')
        llm_provider = info.data.get('llm_provider', 'openai')
        if not v and environment == 'production' and llm_provider == 'openai':
            raise ValueError("OpenAI API key must be set in production when using OpenAI provider")
        return v
    
    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: str, info) -> str:
        """Validate Anthropic API key is set when using Anthropic provider."""
        # Only require API key in production and when using Anthropic
        environment = info.data.get('environment', 'development')
        llm_provider = info.data.get('llm_provider', 'openai')
        if not v and environment == 'production' and llm_provider == 'anthropic':
            raise ValueError("Anthropic API key must be set in production when using Anthropic provider")
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment == "testing"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
