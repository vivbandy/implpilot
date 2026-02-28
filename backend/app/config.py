"""Application configuration management."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./implpilot.db"

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # AI
    anthropic_api_key: str = ""

    # Email
    resend_api_key: str = ""
    from_email: str = "notifications@yourcompany.com"

    # External integrations
    jira_base_url: str = ""
    jira_api_token: str = ""
    zendesk_base_url: str = ""
    zendesk_api_token: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
