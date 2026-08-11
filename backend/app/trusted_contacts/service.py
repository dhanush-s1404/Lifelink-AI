"""Trusted contacts orchestration service with ownership checks."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.trusted_contacts.models import ContactStatus, TrustedContact
from app.trusted_contacts.repository import ContactRepository
from app.trusted_contacts.schemas import ContactOut
from app.users.models import User
from app.users.repository import UserRepository


class ContactService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ContactRepository(session)
        self._users = UserRepository(session)

    async def invite(
        self,
        *,
        owner: User,
        email: str,
        can_activate_emergency: bool,
        can_view_vaults: bool,
        access_grace_days: int,
    ) -> ContactOut:
        target = await self._users.get_by_email(email)
        if target is None:
            raise NotFoundError("No user found with that email", code="CONTACT_USER_NOT_FOUND")
        if target.id == owner.id:
            raise ValidationAppError("You cannot add yourself", code="CANNOT_CONTACT_SELF")

        existing = await self._repo.get_by_ids(owner_id=owner.id, contact_id=target.id)
        if existing is not None:
            raise ConflictError("That user is already a trusted contact", code="CONTACT_EXISTS")

        contact = await self._repo.create(
            owner_id=owner.id,
            contact_id=target.id,
            can_activate_emergency=can_activate_emergency,
            can_view_vaults=can_view_vaults,
            access_grace_days=access_grace_days,
        )
        return await self._to_out(contact, target)

    async def list_owned(self, user_id: uuid.UUID) -> list[ContactOut]:
        contacts = await self._repo.list_owned(user_id)
        return await self._to_outs(contacts)

    async def list_incoming(self, user_id: uuid.UUID) -> list[ContactOut]:
        contacts = await self._repo.list_incoming(user_id)
        return await self._to_outs(contacts)

    async def accept(self, contact_id: uuid.UUID, user_id: uuid.UUID) -> ContactOut:
        contact = await self._repo.get(contact_id)
        if contact is None:
            raise NotFoundError("Trusted contact not found", code="CONTACT_NOT_FOUND")
        if contact.contact_id != user_id:
            raise ForbiddenError(
                "Only the invited user can accept this request", code="CONTACT_ACCESS_DENIED"
            )
        if contact.status != ContactStatus.PENDING:
            raise ConflictError("This request has already been handled", code="CONTACT_NOT_PENDING")
        contact.status = ContactStatus.ACTIVE
        await self._session.flush()
        await self._session.refresh(contact)
        return await self._to_out(contact)

    async def decline(self, contact_id: uuid.UUID, user_id: uuid.UUID) -> None:
        contact = await self._repo.get(contact_id)
        if contact is None:
            raise NotFoundError("Trusted contact not found", code="CONTACT_NOT_FOUND")
        if contact.contact_id != user_id:
            raise ForbiddenError(
                "Only the invited user can decline this request", code="CONTACT_ACCESS_DENIED"
            )
        await self._session.delete(contact)
        await self._session.flush()

    async def remove(self, contact_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Owner revokes an existing trust link."""
        contact = await self._repo.get(contact_id)
        if contact is None:
            raise NotFoundError("Trusted contact not found", code="CONTACT_NOT_FOUND")
        if contact.owner_id != user_id:
            raise ForbiddenError(
                "Only the owner can remove this contact", code="CONTACT_ACCESS_DENIED"
            )
        await self._session.delete(contact)
        await self._session.flush()

    async def update(
        self,
        contact_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        can_activate_emergency: bool | None,
        can_view_vaults: bool | None,
        access_grace_days: int | None,
    ) -> ContactOut:
        contact = await self._repo.get(contact_id)
        if contact is None:
            raise NotFoundError("Trusted contact not found", code="CONTACT_NOT_FOUND")
        if contact.owner_id != user_id:
            raise ForbiddenError(
                "Only the owner can update this contact", code="CONTACT_ACCESS_DENIED"
            )
        if can_activate_emergency is not None:
            contact.can_activate_emergency = can_activate_emergency
        if can_view_vaults is not None:
            contact.can_view_vaults = can_view_vaults
        if access_grace_days is not None:
            contact.access_grace_days = access_grace_days
        await self._session.flush()
        await self._session.refresh(contact)
        return await self._to_out(contact)

    # ------------------------------------------------------------------ helpers

    async def _to_outs(self, contacts: list[TrustedContact]) -> list[ContactOut]:
        out = []
        for contact in contacts:
            out.append(await self._to_out(contact))
        return out

    async def _to_out(self, contact: TrustedContact, target: User | None = None) -> ContactOut:
        if target is None:
            target = await self._users.get_by_id(contact.contact_id)
        return ContactOut(
            id=contact.id,
            status=contact.status,
            contact_id=contact.contact_id,
            contact_email=target.email if target else None,
            contact_name=target.full_name if target else None,
            can_activate_emergency=contact.can_activate_emergency,
            can_view_vaults=contact.can_view_vaults,
            access_grace_days=contact.access_grace_days,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
        )
