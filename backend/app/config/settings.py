from __future__ import annotations

import os
from datetime import timedelta
from functools import lru_cache
from typing import cast

from functools import lru_cache

from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="")

    # General
    environment: str = "development"
    log_level: str = "INFO"
    app_name: str = "LifeLink AI"
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: list[str] = ["http://localhost:3000"]

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
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Vault
    vault_master_key: str = ""

    # MinIO
    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = ""

    # Frontend
    frontend_url: str = "http://localhost:3000"

    # Observability
    otel_endpoint: str = ""
    enable_metrics: bool = True

    # Rate limiting
    rate_limit_default: int = 100
    rate_limit_auth: int = 10

    # MFA
    mfa_enabled: bool = False
    mfa_totp_issuer: str = "LifeLink AI"

    # Session
    session_timeout_minutes: int = 30

    # CORS
    cors_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_credentials: bool = True

settings = Settings()


@lru_cache
def get_settings() -> Settings:
    return settings