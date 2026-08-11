"""Dashboard API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ActivityItem(BaseModel):
    id: str
    kind: str
    message: str
    created_at: datetime


class DashboardSummary(BaseModel):
    vaults_count: int
    items_count: int
    trusted_contacts_count: int
    pending_emergencies_count: int
    unread_notifications_count: int
    recent_activity: list[ActivityItem]
