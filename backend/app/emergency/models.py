"""Emergency ORM models.

An emergency is triggered by a trusted contact for an owner. After a grace
period (the contact's ``access_grace_days``) without the owner confirming they
are okay, the emergency escalates and the contact gains read access to the
owner's vault contents.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel
from app.users.models import User


class EmergencyStatus(StrEnum):
    PENDING = "pending"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class Emergency(BaseModel):
    """An active or historical emergency for an owner.

    ``activated_by`` is the trusted contact who triggered it. The emergency
    escalates once ``grace_end_at`` passes while still ``pending``.
    """

    __tablename__ = "emergencies"
    __table_args__ = (
        Index("ix_emergencies_owner_id", "owner_id"),
        Index("ix_emergencies_activated_by", "activated_by"),
        Index("ix_emergencies_status", "status"),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    activated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[EmergencyStatus] = mapped_column(
        Enum(
            EmergencyStatus,
            name="emergency_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=EmergencyStatus.PENDING,
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    grace_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner: Mapped[User] = relationship(foreign_keys=[owner_id])
    activator: Mapped[User] = relationship(foreign_keys=[activated_by])
