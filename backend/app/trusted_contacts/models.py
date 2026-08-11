"""Trusted contacts ORM models.

A trusted contact is another user who the owner designates to receive emergency
access. The relationship requires mutual consent: the owner invites by email, and
the contact must accept before the trust link becomes ``active``.
"""

from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel
from app.users.models import User


class ContactStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"


class TrustedContact(BaseModel):
    """A bidirectional trust link between two users.

    ``owner_id`` is the user who extended the invitation; ``contact_id`` is the
    invited user. Permissions granted to the contact are stored here.
    """

    __tablename__ = "trusted_contacts"
    __table_args__ = (
        UniqueConstraint("owner_id", "contact_id", name="uq_trusted_contacts_owner_contact"),
        Index("ix_trusted_contacts_owner_id", "owner_id"),
        Index("ix_trusted_contacts_contact_id", "contact_id"),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[ContactStatus] = mapped_column(
        Enum(
            ContactStatus,
            name="contact_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=ContactStatus.PENDING,
        nullable=False,
    )
    can_activate_emergency: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_view_vaults: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    access_grace_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    owner: Mapped[User] = relationship(foreign_keys=[owner_id])
    contact: Mapped[User] = relationship(foreign_keys=[contact_id])
