"""Emergency API schemas (DTOs)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.emergency.models import EmergencyStatus
from app.vault.models import ItemType


class EmergencyCreate(BaseModel):
    """A trusted contact triggers an emergency for an owner."""

    owner_id: uuid.UUID
    reason: str | None = Field(default=None, max_length=500)


class EmergencyOut(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    owner_name: str | None = None
    owner_email: str | None = None
    activated_by: uuid.UUID
    contact_name: str | None = None
    contact_email: str | None = None
    status: EmergencyStatus
    reason: str | None
    grace_end_at: datetime
    responded_at: datetime | None
    activated_at: datetime
    created_at: datetime
    updated_at: datetime


class EmergencyReleaseItem(BaseModel):
    """A vault item released to a contact after escalation."""

    vault_id: uuid.UUID
    vault_name: str
    item_id: uuid.UUID
    item_type: ItemType
    title: str
    content: dict[str, Any]
    updated_at: datetime
