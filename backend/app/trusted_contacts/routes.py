"""Trusted contacts API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.auth.deps import get_current_user
from app.trusted_contacts.schemas import ContactInvite, ContactOut, ContactUpdate
from app.trusted_contacts.service import ContactService
from app.users.models import User

router = APIRouter(prefix="/contacts", tags=["trusted-contacts"])


def _service(session: AsyncSession) -> ContactService:
    return ContactService(session)


@router.get("", response_model=list[ContactOut])
async def list_contacts(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[ContactOut]:
    return await _service(session).list_owned(user.id)


@router.get("/incoming", response_model=list[ContactOut])
async def list_incoming(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[ContactOut]:
    return await _service(session).list_incoming(user.id)


@router.post("", response_model=ContactOut, status_code=201)
async def invite_contact(
    body: ContactInvite,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> ContactOut:
    return await _service(session).invite(
        owner=user,
        email=body.email,
        can_activate_emergency=body.can_activate_emergency,
        can_view_vaults=body.can_view_vaults,
        access_grace_days=body.access_grace_days,
    )


@router.post("/{contact_id}/accept", response_model=ContactOut)
async def accept_contact(
    contact_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> ContactOut:
    return await _service(session).accept(contact_id, user.id)


@router.post("/{contact_id}/decline", status_code=204)
async def decline_contact(
    contact_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> None:
    await _service(session).decline(contact_id, user.id)


@router.patch("/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: uuid.UUID,
    body: ContactUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> ContactOut:
    return await _service(session).update(
        contact_id,
        user.id,
        can_activate_emergency=body.can_activate_emergency,
        can_view_vaults=body.can_view_vaults,
        access_grace_days=body.access_grace_days,
    )


@router.delete("/{contact_id}", status_code=204)
async def remove_contact(
    contact_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> None:
    await _service(session).remove(contact_id, user.id)
