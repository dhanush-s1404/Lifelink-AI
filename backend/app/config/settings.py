from __future__ import annotations

import os
from datetime import timedelta
from functools import lru_cache
from typing import cast, List

from pydantic import Field, model_validator

from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_cors_origins(v: str) -> List[str]:
    """Parse comma-separated CORS origins from env string."""
    if not v:
        return ["http://localhost:3000"]
    return [origin.strip() for origin in v.split(",") if origin.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", secrets_strict=False)

    # General
    environment: str = "development"
    log_level: str = "INFO"
    app_name: str = "LifeLink AI"
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Database
    postgres_user: str = "lifelink"
    postgres_password: str = ""
    postgres_db: str = "lifelink"
    database_url: str = "postgresql+asyncpg://lifelink:@localhost:5432/lifelink"

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # Auth
    secret_key: str = ""
    algorithm: str = "HS256"
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Vault
    vault_master_key: str = ""

    # MinIO
    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_root_user: str = "minioadmin"
    minio_root_password: str = ""
    minio_bucket: str = "lifelink"
    minio_secure: bool = False

    # Email
    email_transport: str = "console"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "noreply@lifelink.local"

    # Frontend
    frontend_url: str = "http://localhost:3000"

    # Observability
    otel_endpoint: str = ""
    opentelemetry_endpoint: str = ""
    enable_metrics: bool = True

    # Rate limiting
    rate_limit_default: int = 100
    rate_limit_auth: int = 10

    # MFA
    mfa_enabled: bool = False
    mfa_totp_issuer: str = "LifeLink AI"

    # Session
    session_timeout_minutes: int = 30

# CORS origins: comma-separated list from env var (e.g. "http://localhost:3000,https://app.example.com")
# Parsed by _parse_cors_origins(). Default is localhost for development.
# NOTE: allow_credentials=True requires explicit origins (cannot use "*")
cors_origins: str = "http://localhost:3000"

@model_validator(mode="after")
def _validate_cors_origins(self) -> "Settings":
    """Parse CORS origins from comma-separated env string."""
    self.backend_cors_origins = _parse_cors_origins(self.cors_origins)
    return self

    @model_validator(mode="after")
    def _backfill_aliases(self) -> "Settings":
        if not self.jwt_secret_key:
            self.jwt_secret_key = self.secret_key
        if not self.jwt_algorithm:
            self.jwt_algorithm = self.algorithm
        if not self.opentelemetry_endpoint:
            self.opentelemetry_endpoint = self.otel_endpoint
        return self


settings = Settings()


@lru_cache
def get_settings() -> Settings:
    return settings