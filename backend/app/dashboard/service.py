"""Dashboard domain: aggregated summary for the authenticated user.

Counts are sourced from each domain's repository as those domains are built;
queries that reference not-yet-implemented tables return zero.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.schemas import DashboardSummary
from app.emergency.models import Emergency, EmergencyStatus
from app.trusted_contacts.models import ContactStatus, TrustedContact
from app.vault.models import Vault, VaultItem


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def summarize(self, user_id: uuid.UUID) -> DashboardSummary:
        vaults = (
            await self._session.execute(
                select(func.count()).select_from(Vault).where(Vault.owner_id == user_id)
            )
        ).scalar_one()
        items = (
            await self._session.execute(
                select(func.count())
                .select_from(VaultItem)
                .join(Vault, Vault.id == VaultItem.vault_id)
                .where(Vault.owner_id == user_id, VaultItem.is_archived.is_(False))
            )
        ).scalar_one()

        contacts = (
            await self._session.execute(
                select(func.count())
                .select_from(TrustedContact)
                .where(
                    TrustedContact.owner_id == user_id,
                    TrustedContact.status == ContactStatus.ACTIVE,
                )
            )
        ).scalar_one()

        pending_emergencies = (
            await self._session.execute(
                select(func.count())
                .select_from(Emergency)
                .where(
                    Emergency.owner_id == user_id,
                    Emergency.status == EmergencyStatus.PENDING,
                )
            )
        ).scalar_one()

        return DashboardSummary(
            vaults_count=vaults,
            items_count=items,
            trusted_contacts_count=contacts,
            pending_emergencies_count=pending_emergencies,
            unread_notifications_count=0,
            recent_activity=[],
        )
