"""Application configuration."""

from functools import lru_cache
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Hostel Management System"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://postgres:Kiran$123@localhost:5432/hostel_db"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = Field(default="change-me-in-production-min-32-chars")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: Union[List[str], str] = "http://localhost:3000,http://localhost:3001"
    cors_allow_credentials: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Rate Limiting
    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = 60

    # Payment
    payment_provider: str = "razorpay"  # razorpay or mock
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    payment_currency: str = "INR"

    # Notification
    notification_provider: str = "mock"
    sendgrid_api_key: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    fcm_server_key: str = ""

    # OTP
    otp_provider: str = "mock"  # twilio or mock
    otp_expiry_minutes: int = 5
    twilio_verify_service_sid: str = ""

    # Storage
    storage_provider: str = "local"  # local, s3, gcs
    storage_path: str = "./storage"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_bucket_name: str = ""
    aws_region: str = "us-east-1"

    # File Upload Constraints
    max_file_size_mb: int = 10
    allowed_file_types: Union[List[str], str] = "application/pdf,image/jpeg,image/png"

    @field_validator("allowed_file_types", mode="before")
    @classmethod
    def parse_allowed_file_types(cls, v):
        """Parse allowed file types from string or list."""
        if isinstance(v, str):
            return [ft.strip() for ft in v.split(",") if ft.strip()]
        return v

    # Data Retention
    attachment_retention_months: int = 24
    soft_delete_retention_days: int = 90
    audit_log_retention_months: int = 36

    # Timezone
    storage_timezone: str = "UTC"
    default_display_timezone: str = "Asia/Kolkata"
    
    # Registration settings
    registration_enabled: bool = True
    email_verification_required: bool = True
    visitor_default_duration_days: int = 30
    
    # Frontend URL for email links
    frontend_url: str = "http://localhost:3000"

    # Tax (disabled)
    tax_enabled: bool = False
    tax_rate: float = 0.0

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()