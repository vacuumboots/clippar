"""Configuration management for Clipplex."""

import os
from typing import Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Plex Configuration
    plex_url: str
    plex_token: str
    
    # Application Configuration
    secret_key: str = "change-this-in-production"
    debug: bool = False
    
    # Media Paths
    media_static_path: str = "app/static/media"
    media_mount_path: str = "/media"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 5000
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Environment variable prefixes
        env_prefix = ""


# Global settings instance
settings = Settings()


class PlexConfig(BaseModel):
    """Plex server configuration."""
    url: str
    token: str
    
    @classmethod
    def from_settings(cls) -> "PlexConfig":
        return cls(
            url=settings.plex_url,
            token=settings.plex_token
        )


