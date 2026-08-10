"""User API schemas (DTOs)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserOut(BaseModel):
    """Public user representation. Never includes secrets."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime


class UserUpdate(BaseModel):
    """Fields a user may update about themselves."""

    full_name: str | None = Field(default=None, min_length=1, max_length=120)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=8, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)
