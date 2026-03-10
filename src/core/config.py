from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr

class Settings(BaseSettings):
    """
    Production-grade configuration management.
    Sensitive values like API keys are wrapped in SecretStr to prevent accidental logging.
    """
    # App Metadata
    PROJECT_NAME: str = "Enterprise LLM Guardrails"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment Configuration
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True

    # LLM Provider Settings
    # Field alias allows for flexible environment variable mapping
    OPENAI_API_KEY: SecretStr = Field(..., validation_alias="OPENAI_API_KEY")
    OPENAI_MODEL: str = "gpt-4-turbo"

    model_config = SettingsConfigDict(
        # Load environment variables from .env if present
        env_file=".env",
        env_file_encoding="utf-8",
        # Case-sensitive prevents ambiguity with system env vars
        case_sensitive=True,
    )

# Singleton instance to be used across the application
settings = Settings()
