"""Vault orchestration service with ownership checks and encryption."""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.vault.encryption import decrypt, encrypt
from app.vault.models import ItemType, ItemVersion, Vault, VaultItem
from app.vault.repository import VaultRepository
from app.vault.schemas import CategoryOut, ItemDetailOut, ItemOut, VaultOut


class VaultService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = VaultRepository(session)

    # ------------------------------------------------------------------ vaults

    async def create_vault(
        self, *, owner_id: uuid.UUID, name: str, description: str | None
    ) -> VaultOut:
        vault = await self._repo.create_vault(owner_id=owner_id, name=name, description=description)
        return VaultOut.model_validate(vault)

    async def list_vaults(self, owner_id: uuid.UUID) -> list[VaultOut]:
        return [VaultOut.model_validate(v) for v in await self._repo.list_vaults(owner_id)]

    async def get_vault(self, vault_id: uuid.UUID, user_id: uuid.UUID) -> VaultOut:
        vault = await self._require_owned_vault(vault_id, user_id)
        return VaultOut.model_validate(vault)

    async def update_vault(
        self, vault_id: uuid.UUID, user_id: uuid.UUID, *, name: str | None, description: str | None
    ) -> VaultOut:
        vault = await self._require_owned_vault(vault_id, user_id)
        if name is not None:
            vault.name = name
        if description is not None:
            vault.description = description
        await self._session.flush()
        await self._session.refresh(vault)
        return VaultOut.model_validate(vault)

    async def delete_vault(self, vault_id: uuid.UUID, user_id: uuid.UUID) -> None:
        vault = await self._require_owned_vault(vault_id, user_id)
        await self._session.delete(vault)
        await self._session.flush()

    # --------------------------------------------------------------- categories

    async def create_category(
        self, vault_id: uuid.UUID, user_id: uuid.UUID, *, name: str
    ) -> CategoryOut:
        await self._require_owned_vault(vault_id, user_id)
        category = await self._repo.create_category(vault_id=vault_id, name=name)
        return CategoryOut.model_validate(category)

    async def list_categories(self, vault_id: uuid.UUID, user_id: uuid.UUID) -> list[CategoryOut]:
        await self._require_owned_vault(vault_id, user_id)
        return [CategoryOut.model_validate(c) for c in await self._repo.list_categories(vault_id)]

    # ------------------------------------------------------------------- items

    async def create_item(
        self,
        *,
        vault_id: uuid.UUID,
        user_id: uuid.UUID,
        item_type: ItemType,
        title: str,
        content: dict[str, Any],
        category_id: uuid.UUID | None,
        masked_summary: str | None,
    ) -> ItemDetailOut:
        vault = await self._require_owned_vault(vault_id, user_id)
        if category_id:
            category = await self._repo.get_category(category_id)
            if category is None or category.vault_id != vault.id:
                raise NotFoundError("Category not found", code="CATEGORY_NOT_FOUND")

        item = VaultItem(
            vault_id=vault_id,
            created_by=user_id,
            item_type=item_type,
            title=title,
            category_id=category_id,
            content_encrypted=encrypt(json.dumps(content)),
            masked_summary=masked_summary,
        )
        self._session.add(item)
        await self._session.flush()

        self._session.add(
            ItemVersion(
                item_id=item.id,
                version_number=1,
                content_encrypted=item.content_encrypted,
                created_by=user_id,
                note="Initial version",
            )
        )
        await self._session.flush()
        return await self._item_detail(item, user_id)

    async def list_items(
        self,
        *,
        vault_id: uuid.UUID,
        user_id: uuid.UUID,
        item_type: str | None = None,
        category_id: uuid.UUID | None = None,
        include_archived: bool = False,
    ) -> list[ItemOut]:
        await self._require_owned_vault(vault_id, user_id)
        items = await self._repo.list_items(
            vault_id=vault_id,
            item_type=item_type,
            category_id=category_id,
            include_archived=include_archived,
        )
        versions = await self._latest_version_map(vault_id)
        return [_item_out(item, versions.get(item.id, 1)) for item in items]

    async def get_item(self, item_id: uuid.UUID, user_id: uuid.UUID) -> ItemDetailOut:
        item = await self._require_owned_item(item_id, user_id)
        return await self._item_detail(item, user_id)

    async def update_item(
        self,
        item_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        title: str | None,
        category_id: uuid.UUID | None,
        content: dict[str, Any] | None,
        masked_summary: str | None,
        is_archived: bool | None,
    ) -> ItemDetailOut:
        item = await self._require_owned_item(item_id, user_id)

        if category_id is not None:
            category = await self._repo.get_category(category_id)
            if category is None or category.vault_id != item.vault_id:
                raise NotFoundError("Category not found", code="CATEGORY_NOT_FOUND")
            item.category_id = category_id
        if title is not None:
            item.title = title
        if masked_summary is not None:
            item.masked_summary = masked_summary
        if is_archived is not None:
            item.is_archived = is_archived

        if content is not None:
            # New version snapshot.
            latest = (
                await self._session.execute(
                    select(func.max(ItemVersion.version_number)).where(
                        ItemVersion.item_id == item.id
                    )
                )
            ).scalar_one()
            version_number = (latest or 0) + 1
            item.content_encrypted = encrypt(json.dumps(content))
            self._session.add(
                ItemVersion(
                    item_id=item.id,
                    version_number=version_number,
                    content_encrypted=item.content_encrypted,
                    created_by=user_id,
                    note="Updated",
                )
            )
        await self._session.flush()
        await self._session.refresh(item)
        return await self._item_detail(item, user_id)

    async def delete_item(self, item_id: uuid.UUID, user_id: uuid.UUID) -> None:
        item = await self._require_owned_item(item_id, user_id)
        await self._session.delete(item)
        await self._session.flush()

    async def list_versions(self, item_id: uuid.UUID, user_id: uuid.UUID) -> list[dict]:
        item = await self._require_owned_item(item_id, user_id)
        stmt = (
            select(ItemVersion)
            .where(ItemVersion.item_id == item.id)
            .order_by(ItemVersion.version_number.desc())
        )
        versions = (await self._session.execute(stmt)).scalars().all()
        return [
            {
                "id": str(v.id),
                "version_number": v.version_number,
                "created_at": v.created_at,
                "note": v.note,
            }
            for v in versions
        ]

    # ------------------------------------------------------------------ helpers

    async def _require_owned_vault(self, vault_id: uuid.UUID, user_id: uuid.UUID) -> Vault:
        vault = await self._repo.get_vault(vault_id)
        if vault is None:
            raise NotFoundError("Vault not found", code="VAULT_NOT_FOUND")
        if vault.owner_id != user_id:
            raise ForbiddenError("You do not have access to this vault", code="VAULT_ACCESS_DENIED")
        return vault

    async def _require_owned_item(self, item_id: uuid.UUID, user_id: uuid.UUID) -> VaultItem:
        item = await self._repo.get_item(item_id)
        if item is None:
            raise NotFoundError("Item not found", code="ITEM_NOT_FOUND")
        vault = await self._repo.get_vault(item.vault_id)
        if vault is None or vault.owner_id != user_id:
            raise ForbiddenError("You do not have access to this item", code="ITEM_ACCESS_DENIED")
        return item

    async def _item_detail(self, item: VaultItem, user_id: uuid.UUID) -> ItemDetailOut:
        version = (
            await self._session.execute(
                select(func.max(ItemVersion.version_number)).where(ItemVersion.item_id == item.id)
            )
        ).scalar_one()
        decrypted = decrypt(item.content_encrypted)
        content = json.loads(decrypted) if decrypted else {}
        return ItemDetailOut(
            id=item.id,
            vault_id=item.vault_id,
            category_id=item.category_id,
            item_type=item.item_type,
            title=item.title,
            masked_summary=item.masked_summary,
            is_archived=item.is_archived,
            version=version or 1,
            created_at=item.created_at,
            updated_at=item.updated_at,
            content=content,
        )

    async def _latest_version_map(self, vault_id: uuid.UUID) -> dict[uuid.UUID, int]:
        stmt = (
            select(ItemVersion.item_id, func.max(ItemVersion.version_number))
            .join(VaultItem, VaultItem.id == ItemVersion.item_id)
            .where(VaultItem.vault_id == vault_id)
            .group_by(ItemVersion.item_id)
        )
        return {item_id: version for item_id, version in (await self._session.execute(stmt)).all()}


def _item_out(item: VaultItem, version: int) -> ItemOut:
    return ItemOut(
        id=item.id,
        vault_id=item.vault_id,
        category_id=item.category_id,
        item_type=item.item_type,
        title=item.title,
        masked_summary=item.masked_summary,
        is_archived=item.is_archived,
        version=version,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )
