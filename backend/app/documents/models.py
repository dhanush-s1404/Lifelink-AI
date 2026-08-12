"""Document ORM models.

Documents are file attachments on vault items. File bytes live in object
storage; this table stores metadata and the opaque storage key.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel
from app.users.models import User
from app.vault.models import VaultItem


class Document(BaseModel):
    """Metadata for a stored file attached to a vault item."""

    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_vault_item_id", "vault_item_id"),
        Index("ix_documents_owner_id", "owner_id"),
    )

    vault_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vault_items.id", ondelete="CASCADE"), nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    vault_item: Mapped[VaultItem] = relationship(back_populates="documents")
    owner: Mapped[User] = relationship()

    def __repr__(self) -> str:
        return f"<Document id={self.id} file={self.original_filename!r} size={self.size_bytes}>"
