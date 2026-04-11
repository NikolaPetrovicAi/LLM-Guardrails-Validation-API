from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Explicitly load .env as pydantic-settings might have issues on Python 3.14
load_dotenv(dotenv_path=".env")


class Settings(BaseSettings):
    """
    Production-grade configuration management.
    Sensitive values are wrapped in SecretStr to prevent accidental logging.
    """

    # App Metadata
    PROJECT_NAME: str = "Enterprise LLM Guardrails"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Environment Configuration
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True

    # LLM Provider Settings
    LLM_PROVIDER: str = "openai"  # openai, anthropic

    # OpenAI Settings
    OPENAI_API_KEY: SecretStr = Field(
        default=SecretStr("fake-key-for-testing"), validation_alias="OPENAI_API_KEY"
    )
    OPENAI_MODEL: str = "gpt-4o"

    # Anthropic Settings
    ANTHROPIC_API_KEY: SecretStr = Field(
        default=SecretStr("fake-key-for-testing"), validation_alias="ANTHROPIC_API_KEY"
    )
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20240620"

    # Token Pricing (USD per 1k tokens)
    # Default prices for gpt-4o
    PRICE_PROMPT_1K: float = 0.005
    PRICE_COMPLETION_1K: float = 0.015

    # Optimization Settings
    CACHE_PATH: str = ".cache"
    CACHE_EXPIRE: int = 3600  # seconds

    # Resilience Settings
    MAX_RETRIES: int = 3
    RETRY_MIN_SECONDS: int = 1
    RETRY_MAX_SECONDS: int = 10

    # Langfuse Settings
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: SecretStr | None = None
    LANGFUSE_BASE_URL: str = "https://cloud.langfuse.com"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


# Singleton instance to be used across the application
settings = Settings()
