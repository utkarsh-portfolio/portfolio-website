"""
Application Configuration
Manages environment variables and application settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Loan Eligibility Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # API Settings
    API_V1_PREFIX: str = "/api/v1"

    # Google Cloud Platform
    GCP_PROJECT_ID: Optional[str] = None
    GCP_LOCATION: str = "us-central1"

    # Dialogflow CX
    DIALOGFLOW_AGENT_ID: Optional[str] = None
    DIALOGFLOW_LANGUAGE_CODE: str = "en"

    # Vertex AI / LLM Settings
    VERTEX_AI_MODEL: str = "gemini-1.5-pro"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 1024

    # OpenAI (alternative LLM)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"

    # Security
    API_KEY: Optional[str] = None
    CORS_ORIGINS: list = ["*"]

    # Logging
    LOG_LEVEL: str = "INFO"
    SPLUNK_HEC_URL: Optional[str] = None
    SPLUNK_HEC_TOKEN: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
