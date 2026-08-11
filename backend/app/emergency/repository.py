"""Emergency persistence layer (repository pattern)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.emergency.models import Emergency, EmergencyStatus


class EmergencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        owner_id: uuid.UUID,
        activated_by: uuid.UUID,
        grace_end_at,
        reason: str | None,
    ) -> Emergency:
        emergency = Emergency(
            owner_id=owner_id,
            activated_by=activated_by,
            grace_end_at=grace_end_at,
            reason=reason,
        )
        self._session.add(emergency)
        await self._session.flush()
        return emergency

    async def get(self, emergency_id: uuid.UUID) -> Emergency | None:
        return await self._session.get(Emergency, emergency_id)

    async def get_active_for_owner(self, owner_id: uuid.UUID) -> Emergency | None:
        stmt = (
            select(Emergency)
            .where(
                Emergency.owner_id == owner_id,
                Emergency.status == EmergencyStatus.PENDING,
            )
            .order_by(Emergency.created_at.desc())
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalars().first()

    async def list_for_owner(self, owner_id: uuid.UUID) -> list[Emergency]:
        stmt = (
            select(Emergency)
            .where(Emergency.owner_id == owner_id)
            .order_by(Emergency.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_activated_by(self, contact_id: uuid.UUID) -> list[Emergency]:
        stmt = (
            select(Emergency)
            .where(Emergency.activated_by == contact_id)
            .order_by(Emergency.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def count_active(self, owner_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Emergency)
            .where(
                Emergency.owner_id == owner_id,
                Emergency.status == EmergencyStatus.PENDING,
            )
        )
        return (await self._session.execute(stmt)).scalar_one()
