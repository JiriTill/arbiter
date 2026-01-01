"""
Configuration settings using pydantic-settings.
Loads from environment variables and .env file.
"""

from functools import lru_cache
from typing import Literal
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
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    
    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    database_url: str = ""
    
    # OpenAI
    openai_api_key: str = ""
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Frontend (CORS)
    frontend_url: str = "http://localhost:3000"
    
    # Optional: Sentry
    sentry_dsn: str | None = None
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def cors_origins(self) -> list[str]:
        """Get CORS origins based on environment."""
        origins = [self.frontend_url]
        if self.is_development:
            # Allow localhost variants in development
            origins.extend([
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
            ])
        return origins


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
