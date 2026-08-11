"""Vault API schemas (DTOs)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.vault.models import ItemType


class VaultCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class VaultUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class VaultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vault_id: uuid.UUID
    name: str
    sort_order: int


class ItemCreate(BaseModel):
    item_type: ItemType
    title: str = Field(min_length=1, max_length=200)
    category_id: uuid.UUID | None = None
    content: dict[str, Any] = Field(
        default_factory=dict, description="Sensitive fields, encrypted at rest"
    )
    masked_summary: str | None = Field(default=None, max_length=300)


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    category_id: uuid.UUID | None = None
    content: dict[str, Any] | None = None
    masked_summary: str | None = Field(default=None, max_length=300)
    is_archived: bool | None = None


class ItemOut(BaseModel):
    id: uuid.UUID
    vault_id: uuid.UUID
    category_id: uuid.UUID | None
    item_type: ItemType
    title: str
    masked_summary: str | None
    is_archived: bool
    version: int = 1
    created_at: datetime
    updated_at: datetime


class ItemDetailOut(ItemOut):
    """Item metadata plus decrypted content (only for authorized viewers)."""

    content: dict[str, Any]


class VersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version_number: int
    created_at: datetime
    note: str | None
