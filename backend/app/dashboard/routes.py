"""Dashboard API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.auth.deps import get_current_user
from app.dashboard.schemas import DashboardSummary
from app.dashboard.service import DashboardService
from app.users.models import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> DashboardSummary:
    return await DashboardService(session).summarize(user.id)
