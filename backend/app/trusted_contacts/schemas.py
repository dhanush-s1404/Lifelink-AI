"""Trusted contacts API schemas (DTOs)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.trusted_contacts.models import ContactStatus


class ContactInvite(BaseModel):
    email: EmailStr
    can_activate_emergency: bool = True
    can_view_vaults: bool = True
    access_grace_days: int = Field(default=30, ge=1, le=365)


class ContactUpdate(BaseModel):
    can_activate_emergency: bool | None = None
    can_view_vaults: bool | None = None
    access_grace_days: int | None = Field(default=None, ge=1, le=365)


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: ContactStatus
    contact_id: uuid.UUID
    contact_email: str | None = None
    contact_name: str | None = None
    can_activate_emergency: bool
    can_view_vaults: bool
    access_grace_days: int
    created_at: datetime
    updated_at: datetime
