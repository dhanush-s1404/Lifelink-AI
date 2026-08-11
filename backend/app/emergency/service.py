"""Emergency orchestration service.

Rules enforced here:
- Only an **active trusted contact** of the owner, with ``can_activate_emergency``
  permission, may trigger an emergency.
- A pending emergency escalates once ``grace_end_at`` passes with no owner response.
- Once escalated, only the activating contact may read the released vault items.
- The owner may confirm (resolve) or cancel at any time while pending/escalated.
"""

from __future__ import annotations

import json
import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationAppError,
)
from app.core.security import utc_now
from app.emergency.models import Emergency, EmergencyStatus
from app.emergency.repository import EmergencyRepository
from app.emergency.schemas import EmergencyOut, EmergencyReleaseItem
from app.notifications.email import EmailTransport
from app.trusted_contacts.models import ContactStatus, TrustedContact
from app.users.models import User
from app.users.repository import UserRepository
from app.vault.encryption import decrypt
from app.vault.models import Vault, VaultItem


class EmergencyNotifier:
    """Sends emergency-related emails through a transport."""

    def __init__(self, transport: EmailTransport) -> None:
        self._transport = transport

    async def notify_owner_emergency(self, *, to: str, name: str | None, contact: str) -> None:
        await self._transport.send(
            to=to,
            subject="LifeLink AI — An emergency was raised for you",
            text=(
                f"Hi {name or 'there'},\n\n"
                f"Your trusted contact {contact} has raised an emergency for you.\n"
                "If you are okay, please confirm as soon as possible.\n"
                "If you do not respond within the grace period, your contact will be "
                "granted read access to your vault.\n\n— LifeLink AI"
            ),
        )

    async def notify_owner_resolved(self, *, to: str, name: str | None) -> None:
        await self._transport.send(
            to=to,
            subject="LifeLink AI — Emergency confirmed",
            text=(
                f"Hi {name or 'there'},\n\n"
                "Thanks for confirming you are okay. The emergency has been resolved "
                "and no access was granted.\n\n— LifeLink AI"
            ),
        )

    async def notify_contact_escalated(self, *, to: str, name: str | None) -> None:
        await self._transport.send(
            to=to,
            subject="LifeLink AI — Emergency escalated",
            text=(
                f"Hi {name or 'there'},\n\n"
                "The emergency you raised has escalated: the owner did not respond "
                "within the grace period. You now have read access to their vault.\n\n"
                "— LifeLink AI"
            ),
        )


class EmergencyService:
    def __init__(self, session: AsyncSession, notifier: EmergencyNotifier) -> None:
        self._session = session
        self._repo = EmergencyRepository(session)
        self._users = UserRepository(session)
        self._notifier = notifier

    # ------------------------------------------------------------------ actions

    async def activate(
        self, *, owner_id: uuid.UUID, activated_by: User, reason: str | None
    ) -> EmergencyOut:
        if owner_id == activated_by.id:
            raise ValidationAppError(
                "You cannot raise an emergency for yourself", code="SELF_EMERGENCY"
            )

        link = await self._active_link(owner_id=owner_id, contact_id=activated_by.id)
        if link is None:
            raise ForbiddenError(
                "You are not an active trusted contact of this owner",
                code="EMERGENCY_ACCESS_DENIED",
            )
        if not link.can_activate_emergency:
            raise ForbiddenError(
                "This owner has not granted you emergency access", code="EMERGENCY_NOT_PERMITTED"
            )

        existing = await self._repo.get_active_for_owner(owner_id)
        if existing is not None:
            raise ConflictError(
                "An emergency is already active for this owner", code="EMERGENCY_ALREADY_ACTIVE"
            )

        emergency = await self._repo.create(
            owner_id=owner_id,
            activated_by=activated_by.id,
            grace_end_at=utc_now() + timedelta(days=link.access_grace_days),
            reason=reason,
        )

        owner = await self._users.get_by_id(owner_id)
        if owner is not None:
            await self._notifier.notify_owner_emergency(
                to=owner.email,
                name=owner.full_name,
                contact=activated_by.full_name or activated_by.email,
            )
        return await self._to_out(emergency)

    async def list_for_owner(self, owner: User) -> list[EmergencyOut]:
        out = []
        for emergency in await self._repo.list_for_owner(owner.id):
            await self._maybe_escalate(emergency)
            out.append(await self._to_out(emergency))
        return out

    async def list_activated_by(self, contact: User) -> list[EmergencyOut]:
        out = []
        for emergency in await self._repo.list_activated_by(contact.id):
            await self._maybe_escalate(emergency)
            out.append(await self._to_out(emergency))
        return out

    async def get(self, emergency_id: uuid.UUID, user: User) -> EmergencyOut:
        emergency = await self._require_participant(emergency_id, user)
        await self._maybe_escalate(emergency)
        return await self._to_out(emergency)

    async def confirm(self, emergency_id: uuid.UUID, owner: User) -> EmergencyOut:
        emergency = await self._repo.get(emergency_id)
        if emergency is None:
            raise NotFoundError("Emergency not found", code="EMERGENCY_NOT_FOUND")
        if emergency.owner_id != owner.id:
            raise ForbiddenError(
                "Only the owner can confirm this emergency", code="EMERGENCY_ACCESS_DENIED"
            )
        if emergency.status in (EmergencyStatus.RESOLVED, EmergencyStatus.CANCELLED):
            raise ConflictError("This emergency has already been closed", code="EMERGENCY_CLOSED")

        emergency.status = EmergencyStatus.RESOLVED
        emergency.responded_at = utc_now()
        await self._session.flush()
        await self._session.refresh(emergency)

        contact = await self._users.get_by_id(emergency.activated_by)
        if contact is not None:
            await self._notifier.notify_owner_resolved(to=contact.email, name=contact.full_name)
        return await self._to_out(emergency)

    async def cancel(self, emergency_id: uuid.UUID, owner: User) -> EmergencyOut:
        emergency = await self._repo.get(emergency_id)
        if emergency is None:
            raise NotFoundError("Emergency not found", code="EMERGENCY_NOT_FOUND")
        if emergency.owner_id != owner.id:
            raise ForbiddenError(
                "Only the owner can cancel this emergency", code="EMERGENCY_ACCESS_DENIED"
            )
        if emergency.status in (EmergencyStatus.RESOLVED, EmergencyStatus.CANCELLED):
            raise ConflictError("This emergency has already been closed", code="EMERGENCY_CLOSED")

        emergency.status = EmergencyStatus.CANCELLED
        emergency.responded_at = utc_now()
        await self._session.flush()
        await self._session.refresh(emergency)
        return await self._to_out(emergency)

    async def release_vault(
        self, emergency_id: uuid.UUID, user: User
    ) -> list[EmergencyReleaseItem]:
        """Grant the activating contact read access after escalation."""
        emergency = await self._repo.get(emergency_id)
        if emergency is None:
            raise NotFoundError("Emergency not found", code="EMERGENCY_NOT_FOUND")
        if emergency.activated_by != user.id:
            raise ForbiddenError(
                "Only the contact who raised this emergency may view it",
                code="EMERGENCY_ACCESS_DENIED",
            )

        await self._maybe_escalate(emergency)
        if emergency.status != EmergencyStatus.ESCALATED:
            raise ForbiddenError(
                "Vault access unlocks only after the grace period passes",
                code="EMERGENCY_NOT_ESCALATED",
            )

        vaults = (
            (await self._session.execute(select(Vault).where(Vault.owner_id == emergency.owner_id)))
            .scalars()
            .all()
        )
        items: list[EmergencyReleaseItem] = []
        for vault in vaults:
            rows = (
                (
                    await self._session.execute(
                        select(VaultItem).where(
                            VaultItem.vault_id == vault.id, VaultItem.is_archived.is_(False)
                        )
                    )
                )
                .scalars()
                .all()
            )
            for item in rows:
                try:
                    content = json.loads(decrypt(item.content_encrypted))
                except Exception:
                    content = {}
                items.append(
                    EmergencyReleaseItem(
                        vault_id=vault.id,
                        vault_name=vault.name,
                        item_id=item.id,
                        item_type=item.item_type,
                        title=item.title,
                        content=content,
                        updated_at=item.updated_at,
                    )
                )
        return items

    # ------------------------------------------------------------------ helpers

    async def _active_link(
        self, *, owner_id: uuid.UUID, contact_id: uuid.UUID
    ) -> TrustedContact | None:
        stmt = select(TrustedContact).where(
            TrustedContact.owner_id == owner_id,
            TrustedContact.contact_id == contact_id,
            TrustedContact.status == ContactStatus.ACTIVE,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def _require_participant(self, emergency_id: uuid.UUID, user: User) -> Emergency:
        emergency = await self._repo.get(emergency_id)
        if emergency is None:
            raise NotFoundError("Emergency not found", code="EMERGENCY_NOT_FOUND")
        if emergency.owner_id != user.id and emergency.activated_by != user.id:
            raise ForbiddenError(
                "You are not involved in this emergency", code="EMERGENCY_ACCESS_DENIED"
            )
        return emergency

    async def _maybe_escalate(self, emergency: Emergency) -> None:
        """Escalate a pending emergency once its grace period has passed."""
        if emergency.status == EmergencyStatus.PENDING and emergency.grace_end_at <= utc_now():
            emergency.status = EmergencyStatus.ESCALATED
            await self._session.flush()
            await self._session.refresh(emergency)
            contact = await self._users.get_by_id(emergency.activated_by)
            if contact is not None:
                await self._notifier.notify_contact_escalated(
                    to=contact.email, name=contact.full_name
                )

    async def _to_out(self, emergency: Emergency) -> EmergencyOut:
        owner = await self._users.get_by_id(emergency.owner_id)
        contact = await self._users.get_by_id(emergency.activated_by)
        return EmergencyOut(
            id=emergency.id,
            owner_id=emergency.owner_id,
            owner_name=owner.full_name if owner else None,
            owner_email=owner.email if owner else None,
            activated_by=emergency.activated_by,
            contact_name=contact.full_name if contact else None,
            contact_email=contact.email if contact else None,
            status=emergency.status,
            reason=emergency.reason,
            grace_end_at=emergency.grace_end_at,
            responded_at=emergency.responded_at,
            activated_at=emergency.activated_at,
            created_at=emergency.created_at,
            updated_at=emergency.updated_at,
        )
