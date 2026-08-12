"""Centralized access control for vault resources.

Access is computed against three grant sources, checked in order:

1. The user owns the vault -> full access (read + write).
2. The user is an *active* trusted contact of the owner with the
   ``can_view_vaults`` permission -> read-only access.
3. The user activated an emergency for the owner that has *escalated*
   (grace period passed without owner response) -> read-only access.

Everything else is denied. Write access is reserved for the vault owner.
Only leaked paths is by design: read access never implies write access.
"""

from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from app.access_control.repository import AccessRepository
from app.core.exceptions import ForbiddenError, NotFoundError
from app.vault.models import Vault, VaultItem


class VaultAccess(StrEnum):
    """The level of access a user holds for a vault."""

    NONE = "none"
    READ = "read"
    WRITE = "write"


class AccessControlService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AccessRepository(session)

    async def access_to_vault(self, *, vault: Vault, user_id: uuid.UUID) -> VaultAccess:
        if vault.owner_id == user_id:
            return VaultAccess.WRITE

        link = await self._repo.active_view_link(
            owner_id=vault.owner_id, contact_id=user_id
        )
        if link is not None:
            return VaultAccess.READ

        emergency = await self._repo.escalated_emergency(
            owner_id=vault.owner_id, activator_id=user_id
        )
        if emergency is not None:
            return VaultAccess.READ

        return VaultAccess.NONE

    async def access_to_vault_by_id(
        self, *, vault_id: uuid.UUID, user_id: uuid.UUID
    ) -> VaultAccess:
        vault = await self._session.get(Vault, vault_id)
        if vault is None:
            return VaultAccess.NONE
        return await self.access_to_vault(vault=vault, user_id=user_id)

    async def require_read_vault(self, *, vault_id: uuid.UUID, user_id: uuid.UUID) -> Vault:
        """Return the vault or raise 404 (missing) / 403 (access denied)."""
        vault = await self._session.get(Vault, vault_id)
        if vault is None:
            raise NotFoundError("Vault not found", code="VAULT_NOT_FOUND")
        access = await self.access_to_vault(vault=vault, user_id=user_id)
        if access == VaultAccess.NONE:
            raise ForbiddenError("You do not have access to this vault", code="VAULT_ACCESS_DENIED")
        return vault

    async def require_write_vault(self, *, vault_id: uuid.UUID, user_id: uuid.UUID) -> Vault:
        vault = await self.require_read_vault(vault_id=vault_id, user_id=user_id)
        if vault.owner_id != user_id:
            raise ForbiddenError(
                "Only the owner can modify this vault", code="VAULT_WRITE_DENIED"
            )
        return vault

    async def require_read_item(self, *, item_id: uuid.UUID, user_id: uuid.UUID) -> VaultItem:
        item = await self._session.get(VaultItem, item_id)
        if item is None:
            raise NotFoundError("Item not found", code="ITEM_NOT_FOUND")
        vault = await self._session.get(Vault, item.vault_id)
        if vault is None:
            raise NotFoundError("Item not found", code="ITEM_NOT_FOUND")
        access = await self.access_to_vault(vault=vault, user_id=user_id)
        if access == VaultAccess.NONE:
            raise ForbiddenError("You do not have access to this item", code="ITEM_ACCESS_DENIED")
        return item

    async def require_write_item(self, *, item_id: uuid.UUID, user_id: uuid.UUID) -> VaultItem:
        item = await self.require_read_item(item_id=item_id, user_id=user_id)
        vault = await self._session.get(Vault, item.vault_id)
        if vault is None or vault.owner_id != user_id:
            raise ForbiddenError("Only the owner can modify this item", code="ITEM_WRITE_DENIED")
        return item

    async def list_owned_vaults(self, user_id: uuid.UUID) -> list[Vault]:
        from sqlalchemy import select

        stmt = (
            select(Vault)
            .where(Vault.owner_id == user_id)
            .order_by(Vault.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_shared_vaults(self, user_id: uuid.UUID) -> list[Vault]:
        """Vaults the user may read but does not own (via trusted contacts)."""
        owners = await self._repo.owners_shared_with(user_id)
        owners.discard(user_id)
        if not owners:
            return []

        from sqlalchemy import select

        stmt = (
            select(Vault)
            .where(Vault.owner_id.in_(owners), Vault.is_active.is_(True))
            .order_by(Vault.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_readable_vaults(self, user_id: uuid.UUID) -> list[Vault]:
        """Owned vaults first, then vaults shared via trusted contacts."""
        owned = await self.list_owned_vaults(user_id)
        owned_ids = {v.id for v in owned}
        shared = [v for v in await self.list_shared_vaults(user_id) if v.id not in owned_ids]
        return owned + shared