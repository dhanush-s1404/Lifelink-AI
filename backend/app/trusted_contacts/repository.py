"""Trusted contacts persistence layer (repository pattern)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.trusted_contacts.models import ContactStatus, TrustedContact


class ContactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, owner_id: uuid.UUID, contact_id: uuid.UUID, **perms
    ) -> TrustedContact:
        contact = TrustedContact(owner_id=owner_id, contact_id=contact_id, **perms)
        self._session.add(contact)
        await self._session.flush()
        return contact

    async def get_by_ids(
        self, *, owner_id: uuid.UUID, contact_id: uuid.UUID
    ) -> TrustedContact | None:
        stmt = select(TrustedContact).where(
            TrustedContact.owner_id == owner_id,
            TrustedContact.contact_id == contact_id,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get(self, contact_pk: uuid.UUID) -> TrustedContact | None:
        return await self._session.get(TrustedContact, contact_pk)

    async def list_owned(self, owner_id: uuid.UUID) -> list[TrustedContact]:
        stmt = (
            select(TrustedContact)
            .where(TrustedContact.owner_id == owner_id)
            .order_by(TrustedContact.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_incoming(self, contact_id: uuid.UUID) -> list[TrustedContact]:
        stmt = (
            select(TrustedContact)
            .where(TrustedContact.contact_id == contact_id)
            .order_by(TrustedContact.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def count_active(self, owner_id: uuid.UUID) -> int:
        from sqlalchemy import func

        stmt = (
            select(func.count())
            .select_from(TrustedContact)
            .where(
                TrustedContact.owner_id == owner_id,
                TrustedContact.status == ContactStatus.ACTIVE,
            )
        )
        return (await self._session.execute(stmt)).scalar_one()
