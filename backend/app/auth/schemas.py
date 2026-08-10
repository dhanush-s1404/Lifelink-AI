"""Auth API schemas (DTOs)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    full_name: str | None = Field(default=None, min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class TokenPair(BaseModel):
    """Access + refresh token pair returned on login/refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=16, max_length=512)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=16, max_length=512)


class AuthSuccess(BaseModel):
    """Envelope combining tokens with basic user info."""

    user: dict
    tokens: TokenPair


class SessionOut(BaseModel):
    """A user's active session for the security dashboard."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    device_name: str | None
    ip_address: str | None
    user_agent: str | None
    last_seen_at: datetime | None
    created_at: datetime
    is_current: bool
