"""Vault domain ORM models: vaults, categories, items, versions."""

from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class ItemType(StrEnum):
    DOCUMENT = "document"
    NOTE = "note"
    FINANCIAL = "financial"
    INSURANCE = "insurance"
    MEDICAL = "medical"
    LEGAL = "legal"
    EMERGENCY = "emergency"
    CONTACT = "contact"
    DIGITAL_ASSET = "digital_asset"


class Vault(BaseModel):
    """A user's vault container."""

    __tablename__ = "vaults"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    categories: Mapped[list[Category]] = relationship(
        back_populates="vault", cascade="all, delete-orphan"
    )
    items: Mapped[list[VaultItem]] = relationship(
        back_populates="vault", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_vaults_owner_id", "owner_id"),)


class Category(BaseModel):
    """A grouping inside a vault (e.g. Insurance, Legal, Property)."""

    __tablename__ = "categories"

    vault_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)

    vault: Mapped[Vault] = relationship(back_populates="categories")
    items: Mapped[list[VaultItem]] = relationship(back_populates="category")

    __table_args__ = (
        Index("ix_categories_vault_id", "vault_id"),
        Index("ix_categories_vault_name", "vault_id", "name"),
    )


class VaultItem(BaseModel):
    """A single vault record. Sensitive content is stored encrypted.

    ``content_encrypted`` holds the AES-256-GCM payload of the item's content
    JSON. ``title`` and ``masked_summary`` are kept in plaintext for safe
    indexing/search while exposing only non-sensitive metadata.
    """

    __tablename__ = "vault_items"

    vault_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    item_type: Mapped[ItemType] = mapped_column(
        Enum(ItemType, name="item_type", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    masked_summary: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    vault: Mapped[Vault] = relationship(back_populates="items")
    category: Mapped[Category | None] = relationship(back_populates="items")
    versions: Mapped[list[ItemVersion]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="vault_item", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_vault_items_vault_id", "vault_id"),
        Index("ix_vault_items_category_id", "category_id"),
        Index("ix_vault_items_type", "item_type"),
        Index("ix_vault_items_title", "title"),
    )


class ItemVersion(BaseModel):
    """Immutable snapshot of an item's encrypted content."""

    __tablename__ = "item_versions"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vault_items.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(nullable=False)
    content_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)

    item: Mapped[VaultItem] = relationship(back_populates="versions")

    __table_args__ = (
        Index("ix_item_versions_item_id", "item_id"),
        Index("ix_item_versions_version", "item_id", "version_number", unique=True),
    )
