"""
Configuration management for MNN Pipeline.

Centralizes all environment variable loading and validation.
"""
import os
from typing import Optional


class Config:
    """Application configuration loaded from environment variables."""

    # Database Configuration
    THALOS_DB_DSN: Optional[str] = os.getenv("THALOS_DB_DSN")
    THALOS_DB_CONNECT_TIMEOUT: int = int(os.getenv("THALOS_DB_CONNECT_TIMEOUT", "10"))

    # Hardware Configuration
    THALOS_HARDWARE_ID: Optional[str] = os.getenv("THALOS_HARDWARE_ID")

    # API Configuration
    MNN_API_HOST: str = os.getenv("MNN_API_HOST", "127.0.0.1")
    MNN_API_PORT: int = int(os.getenv("MNN_API_PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    API_AUTH_ENABLED: bool = os.getenv("API_AUTH_ENABLED", "false").lower() == "true"
    MNN_AUTH_SECRET: str = os.getenv("MNN_AUTH_SECRET", "")
    MNN_ADMIN_USERNAME: str = os.getenv("MNN_ADMIN_USERNAME", "admin")
    MNN_ADMIN_PASSWORD: str = os.getenv("MNN_ADMIN_PASSWORD", "admin123!")
    MNN_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("MNN_TOKEN_EXPIRE_MINUTES", "120"))

    # Optional Infrastructure Integrations
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "")
    KEYCLOAK_URL: str = os.getenv("KEYCLOAK_URL", "")
    KEYCLOAK_REALM: str = os.getenv("KEYCLOAK_REALM", "master")

    # Security Configuration
    MAX_QUERY_LENGTH: int = int(os.getenv("MAX_QUERY_LENGTH", "1000"))
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")  # json or text

    # Cache Configuration
    CACHE_SIZE: int = int(os.getenv("CACHE_SIZE", "256"))

    @classmethod
    def validate(cls) -> None:
        """Validate configuration at startup."""
        # Port validation
        if not isinstance(cls.MNN_API_PORT, int) or cls.MNN_API_PORT < 1 or cls.MNN_API_PORT > 65535:
            raise ValueError(f"Invalid MNN_API_PORT: {cls.MNN_API_PORT} (must be between 1 and 65535)")

        # Query length validation
        if not isinstance(cls.MAX_QUERY_LENGTH, int) or cls.MAX_QUERY_LENGTH < 1:
            raise ValueError(f"Invalid MAX_QUERY_LENGTH: {cls.MAX_QUERY_LENGTH} (must be positive integer)")

        # Timeout validation
        if not isinstance(cls.THALOS_DB_CONNECT_TIMEOUT, int) or cls.THALOS_DB_CONNECT_TIMEOUT < 1:
            raise ValueError(f"Invalid THALOS_DB_CONNECT_TIMEOUT: {cls.THALOS_DB_CONNECT_TIMEOUT} (must be positive integer)")

        # Token expiry validation
        if not isinstance(cls.MNN_TOKEN_EXPIRE_MINUTES, int) or cls.MNN_TOKEN_EXPIRE_MINUTES < 1:
            raise ValueError(
                f"Invalid MNN_TOKEN_EXPIRE_MINUTES: {cls.MNN_TOKEN_EXPIRE_MINUTES} (must be positive integer)"
            )


# Singleton config instance
config = Config()
