"""Application configuration with environment variables"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # Spotify OAuth
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str = "http://localhost:8000/callback"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/superior_spotify"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "change-this-in-production"

    # CORS
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    cors_origins: List[str] = ["http://localhost:3000"]

    # Application
    environment: str = "development"
    debug: bool = True

    @property
    def spotify_redirect_uri_decoded(self) -> str:
        """Return redirect URI for Spotify OAuth callback"""
        return self.spotify_redirect_uri


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
