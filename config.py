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

    # Security Configuration
    MAX_QUERY_LENGTH: int = int(os.getenv("MAX_QUERY_LENGTH", "2000"))
    MIN_QUERY_LENGTH: int = int(os.getenv("MIN_QUERY_LENGTH", "1"))
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

    # Guardrail Configuration
    MAX_SEQUENCES_PER_REQUEST: int = int(os.getenv("MAX_SEQUENCES_PER_REQUEST", "1000"))
    MAX_INDICES_PER_REQUEST: int = int(os.getenv("MAX_INDICES_PER_REQUEST", "1000"))

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")  # json or text
    ENABLE_PIPELINE_LOGGING: bool = os.getenv("ENABLE_PIPELINE_LOGGING", "true").lower() == "true"

    # Checkpoint Configuration
    ENABLE_CHECKPOINTS: bool = os.getenv("ENABLE_CHECKPOINTS", "false").lower() == "true"
    CHECKPOINT_DIR: str = os.getenv("CHECKPOINT_DIR", "checkpoints")

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

        if not isinstance(cls.MIN_QUERY_LENGTH, int) or cls.MIN_QUERY_LENGTH < 0:
            raise ValueError(f"Invalid MIN_QUERY_LENGTH: {cls.MIN_QUERY_LENGTH} (must be non-negative integer)")

        if cls.MIN_QUERY_LENGTH > cls.MAX_QUERY_LENGTH:
            raise ValueError(f"MIN_QUERY_LENGTH ({cls.MIN_QUERY_LENGTH}) cannot exceed MAX_QUERY_LENGTH ({cls.MAX_QUERY_LENGTH})")

        # Guardrail validation
        if not isinstance(cls.MAX_SEQUENCES_PER_REQUEST, int) or cls.MAX_SEQUENCES_PER_REQUEST < 1:
            raise ValueError(f"Invalid MAX_SEQUENCES_PER_REQUEST: {cls.MAX_SEQUENCES_PER_REQUEST} (must be positive integer)")

        if not isinstance(cls.MAX_INDICES_PER_REQUEST, int) or cls.MAX_INDICES_PER_REQUEST < 1:
            raise ValueError(f"Invalid MAX_INDICES_PER_REQUEST: {cls.MAX_INDICES_PER_REQUEST} (must be positive integer)")

        # Timeout validation
        if not isinstance(cls.THALOS_DB_CONNECT_TIMEOUT, int) or cls.THALOS_DB_CONNECT_TIMEOUT < 1:
            raise ValueError(f"Invalid THALOS_DB_CONNECT_TIMEOUT: {cls.THALOS_DB_CONNECT_TIMEOUT} (must be positive integer)")


# Singleton config instance
config = Config()
