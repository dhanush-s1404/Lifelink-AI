"""Emergency API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.auth.deps import get_current_user
from app.emergency.schemas import EmergencyCreate, EmergencyOut, EmergencyReleaseItem
from app.emergency.service import EmergencyNotifier, EmergencyService
from app.notifications.email import EmailTransport, get_email_transport
from app.users.models import User

router = APIRouter(prefix="/emergencies", tags=["emergency"])


def _service(session: AsyncSession, transport: EmailTransport) -> EmergencyService:
    return EmergencyService(session, EmergencyNotifier(transport))


@router.post("", response_model=EmergencyOut, status_code=201)
async def activate_emergency(
    body: EmergencyCreate,
    session: AsyncSession = Depends(get_session),
    transport: EmailTransport = Depends(get_email_transport),
    user: User = Depends(get_current_user),
) -> EmergencyOut:
    return await _service(session, transport).activate(
        owner_id=body.owner_id, activated_by=user, reason=body.reason
    )


@router.get("", response_model=list[EmergencyOut])
async def list_emergencies(
    session: AsyncSession = Depends(get_session),
    transport: EmailTransport = Depends(get_email_transport),
    user: User = Depends(get_current_user),
) -> list[EmergencyOut]:
    """Emergencies for the current user as owner."""
    return await _service(session, transport).list_for_owner(user)


@router.get("/activated", response_model=list[EmergencyOut])
async def list_activated(
    session: AsyncSession = Depends(get_session),
    transport: EmailTransport = Depends(get_email_transport),
    user: User = Depends(get_current_user),
) -> list[EmergencyOut]:
    """Emergencies the current user (as a contact) activated."""
    return await _service(session, transport).list_activated_by(user)


@router.get("/{emergency_id}", response_model=EmergencyOut)
async def get_emergency(
    emergency_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    transport: EmailTransport = Depends(get_email_transport),
    user: User = Depends(get_current_user),
) -> EmergencyOut:
    return await _service(session, transport).get(emergency_id, user)


@router.post("/{emergency_id}/confirm", response_model=EmergencyOut)
async def confirm_emergency(
    emergency_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    transport: EmailTransport = Depends(get_email_transport),
    user: User = Depends(get_current_user),
) -> EmergencyOut:
    return await _service(session, transport).confirm(emergency_id, user)


@router.post("/{emergency_id}/cancel", response_model=EmergencyOut)
async def cancel_emergency(
    emergency_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    transport: EmailTransport = Depends(get_email_transport),
    user: User = Depends(get_current_user),
) -> EmergencyOut:
    return await _service(session, transport).cancel(emergency_id, user)


@router.get("/{emergency_id}/release", response_model=list[EmergencyReleaseItem])
async def release_vault(
    emergency_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    transport: EmailTransport = Depends(get_email_transport),
    user: User = Depends(get_current_user),
) -> list[EmergencyReleaseItem]:
    return await _service(session, transport).release_vault(emergency_id, user)
