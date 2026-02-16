"""
Core Configuration for CyberXLTR Admin Platform
"""

import os
import logging
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings with environment variable support
    """

    # Application
    app_name: str = "CyberXLTR Admin"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")

    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8001, env="PORT")

    # PostgreSQL Database Configuration (RDS-compatible)
    database_url: str = Field(
        default="postgresql://admin:password@localhost:5433/cyberxltr_admin",
        env="DATABASE_URL"
    )

    # Security
    secret_key: str = Field(
        "development_jwt_secret_key_min_32_chars_long_replace_in_prod",
        env="JWT_SECRET_KEY",
        min_length=32
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        env="CORS_ORIGINS"
    )

    # ── Inter-Service Communication (VPC Peering) ──
    # URL of the CyberXLTR main service (via VPC peering or private networking)
    cyberxltr_service_url: str = Field(
        default="http://localhost:8000",
        env="CYBERXLTR_SERVICE_URL"
    )
    # Shared API key for service-to-service authentication
    inter_service_api_key: str = Field(
        default="dev-inter-service-key-change-in-production-min32chars",
        env="INTER_SERVICE_API_KEY"
    )
    # Enable/disable sync (useful for development without CyberXLTR running)
    sync_enabled: bool = Field(default=True, env="SYNC_ENABLED")
    # Retry configuration for sync calls
    sync_max_retries: int = Field(default=3, env="SYNC_MAX_RETRIES")
    sync_retry_delay: int = Field(default=5, env="SYNC_RETRY_DELAY")
    sync_timeout: int = Field(default=30, env="SYNC_TIMEOUT")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()
