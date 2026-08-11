"""Vault persistence layer (repository pattern)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.vault.models import Category, Vault, VaultItem


class VaultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_vault(
        self, *, owner_id: uuid.UUID, name: str, description: str | None
    ) -> Vault:
        vault = Vault(owner_id=owner_id, name=name, description=description)
        self._session.add(vault)
        await self._session.flush()
        return vault

    async def get_vault(self, vault_id: uuid.UUID) -> Vault | None:
        return await self._session.get(Vault, vault_id)

    async def list_vaults(self, owner_id: uuid.UUID) -> list[Vault]:
        stmt = select(Vault).where(Vault.owner_id == owner_id).order_by(Vault.created_at.desc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def count_vaults(self, owner_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(Vault).where(Vault.owner_id == owner_id)
        return (await self._session.execute(stmt)).scalar_one()

    async def create_category(self, *, vault_id: uuid.UUID, name: str) -> Category:
        category = Category(vault_id=vault_id, name=name)
        self._session.add(category)
        await self._session.flush()
        return category

    async def get_category(self, category_id: uuid.UUID) -> Category | None:
        return await self._session.get(Category, category_id)

    async def list_categories(self, vault_id: uuid.UUID) -> list[Category]:
        stmt = (
            select(Category)
            .where(Category.vault_id == vault_id)
            .order_by(Category.sort_order, Category.created_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_items(
        self,
        *,
        vault_id: uuid.UUID,
        item_type: str | None = None,
        category_id: uuid.UUID | None = None,
        include_archived: bool = False,
    ) -> list[VaultItem]:
        stmt = select(VaultItem).where(VaultItem.vault_id == vault_id)
        if item_type:
            stmt = stmt.where(VaultItem.item_type == item_type)
        if category_id:
            stmt = stmt.where(VaultItem.category_id == category_id)
        if not include_archived:
            stmt = stmt.where(VaultItem.is_archived.is_(False))
        stmt = stmt.order_by(VaultItem.updated_at.desc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_item(self, item_id: uuid.UUID) -> VaultItem | None:
        return await self._session.get(VaultItem, item_id)

    async def count_items(self, vault_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(VaultItem).where(VaultItem.vault_id == vault_id)
        return (await self._session.execute(stmt)).scalar_one()
