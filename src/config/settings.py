"""
Application configuration settings using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn, RedisDsn
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings."""

    # Database configuration
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/legal_analysis",
        env="DATABASE_URL"
    )

    # Redis configuration
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )

    # DeepSeek API
    deepseek_api_key: str = Field(
        default="",
        env="DEEPSEEK_API_KEY"
    )
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        env="DEEPSEEK_BASE_URL"
    )

    # Indian Kanoon API
    indian_kanoon_api_key: str = Field(
        default="",
        env="INDIAN_KANOON_API_KEY"
    )
    indian_kanoon_base_url: str = Field(
        default="https://api.indiankanoon.org",
        env="INDIAN_KANOON_BASE_URL"
    )

    # JWT Configuration
    jwt_secret_key: str = Field(
        default="your_jwt_secret_key_change_in_production",
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        env="JWT_ALGORITHM"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # AWS S3 Configuration
    s3_bucket_name: Optional[str] = Field(
        default=None,
        env="S3_BUCKET_NAME"
    )
    s3_access_key: Optional[str] = Field(
        default=None,
        env="S3_ACCESS_KEY"
    )
    s3_secret_key: Optional[str] = Field(
        default=None,
        env="S3_SECRET_KEY"
    )
    s3_region: str = Field(
        default="ap-south-1",
        env="S3_REGION"
    )

    # Application Settings
    debug: bool = Field(
        default=True,
        env="DEBUG"
    )
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        env="ALLOWED_HOSTS"
    )
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS"
    )

    # File upload settings
    max_upload_size_mb: int = Field(
        default=50,
        env="MAX_UPLOAD_SIZE_MB"
    )
    allowed_file_types: List[str] = Field(
        default=["pdf", "doc", "docx", "txt", "rtf"],
        env="ALLOWED_FILE_TYPES"
    )

    # OCR Configuration
    tesseract_path: Optional[str] = Field(
        default=None,
        env="TESSERACT_PATH"
    )
    ocr_enabled: bool = Field(
        default=True,
        env="OCR_ENABLED"
    )

    # Email Configuration
    smtp_host: Optional[str] = Field(
        default=None,
        env="SMTP_HOST"
    )
    smtp_port: Optional[int] = Field(
        default=None,
        env="SMTP_PORT"
    )
    smtp_user: Optional[str] = Field(
        default=None,
        env="SMTP_USER"
    )
    smtp_password: Optional[str] = Field(
        default=None,
        env="SMTP_PASSWORD"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()