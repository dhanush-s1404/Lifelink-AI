"""Access-control persistence queries (trust links + escalated emergencies)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.emergency.models import Emergency, EmergencyStatus
from app.trusted_contacts.models import ContactStatus, TrustedContact


class AccessRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def active_view_link(
        self, *, owner_id: uuid.UUID, contact_id: uuid.UUID
    ) -> TrustedContact | None:
        """Return the active trust link granting the contact vault read access."""
        stmt = select(TrustedContact).where(
            TrustedContact.owner_id == owner_id,
            TrustedContact.contact_id == contact_id,
            TrustedContact.status == ContactStatus.ACTIVE,
            TrustedContact.can_view_vaults.is_(True),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def escalated_emergency(
        self, *, owner_id: uuid.UUID, activator_id: uuid.UUID
    ) -> Emergency | None:
        """An escalated emergency whose activator may read the owner's vault."""
        stmt = select(Emergency).where(
            Emergency.owner_id == owner_id,
            Emergency.activated_by == activator_id,
            Emergency.status == EmergencyStatus.ESCALATED,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def owners_shared_with(self, user_id: uuid.UUID) -> set[uuid.UUID]:
        """All owner user-ids that have shared vault read access with ``user_id``."""
        stmt = select(TrustedContact.owner_id).where(
            TrustedContact.contact_id == user_id,
            TrustedContact.status == ContactStatus.ACTIVE,
            TrustedContact.can_view_vaults.is_(True),
        )
        return set((await self._session.execute(stmt)).scalars().all())