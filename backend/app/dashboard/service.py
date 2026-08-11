"""Dashboard domain: aggregated summary for the authenticated user.

Counts are sourced from each domain's repository as those domains are built;
queries that reference not-yet-implemented tables return zero.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.schemas import DashboardSummary


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def summarize(self, user_id: uuid.UUID) -> DashboardSummary:
        # Counts are wired up as the respective domains land:
        #   vaults, items, trusted_contacts, emergency, notifications.
        return DashboardSummary(
            vaults_count=0,
            items_count=0,
            trusted_contacts_count=0,
            pending_emergencies_count=0,
            unread_notifications_count=0,
            recent_activity=[],
        )
