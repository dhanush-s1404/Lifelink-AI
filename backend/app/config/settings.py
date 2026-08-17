"""Application configuration using pydantic-settings.

# ------------------------------------------------------------------
# Production secret validation
# ------------------------------------------------------------------
import os

_PROD_SECRET_FLAGS = {"change_me", "dev_secret", "default", "password"}


def _validate_secret(name: str, value: str | None) -> None:
    """Validate that a secret is not a known default/insecure value."""
    if value is None:
        return  # Optional secret, that's fine
    lower = value.lower().strip()
    if lower in _PROD_SECRET_FLAGS:
        raise ValueError(
            f"Insecure secret detected for {name}: {value!r}. "
            "Do not use default secrets in production."
        )


# Validate key secrets at import time
_secrets_checked = False


def _check_secrets() -> None:
    global _secrets_checked
    if _secrets_checked:
        return
    _secrets_checked = True
    
    for env_name in ["JWT_SECRET", "ENCRYPTION_KEY", "MINIO_ACCESS_KEY",
                     "MINIO_SECRET_KEY", "POSTGRES_PASSWORD", "REDIS_PASSWORD",
                     "EMAIL_HOST_PASSWORD"]:
        val = os.getenv(env_name)
        if val and val.lower().strip() in _PROD_SECRET_FLAGS:
            raise ValueError(
                f"Insecure secret detected for {env_name}: {val!r}. "
                "Do not use default secrets in production."
            )ardcoded.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings, loaded from environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # General
    environment: str = "development"
    log_level: str = "INFO"
    app_name: str = "LifeLink AI"
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database
    postgres_user: str = "lifelink"
    postgres_password: str = "lifelink"
    postgres_db: str = "lifelink"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Auth
    jwt_secret_key: str = Field(default="change_me_jwt_secret_key_123", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # Vault encryption (KMS-backed in production; never commit real keys)
    vault_master_key: str = Field(default="dev_vault_master_key_change_me", min_length=16)

    # MinIO / object storage
    minio_endpoint: str = "localhost:9000"
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin"
    minio_bucket: str = "lifelink-documents"
    minio_secure: bool = False

    # AI
    ai_provider: str = "mock"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"

    # Email
    email_transport: str = "console"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "lifelink@example.com"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
