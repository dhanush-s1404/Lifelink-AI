"""Vault API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.auth.deps import get_current_user
from app.users.models import User
from app.vault.schemas import (
    CategoryCreate,
    CategoryOut,
    ItemCreate,
    ItemDetailOut,
    ItemOut,
    ItemUpdate,
    VaultCreate,
    VaultOut,
    VaultUpdate,
)
from app.vault.service import VaultService

router = APIRouter(prefix="/vaults", tags=["vault"])


def _service(session: AsyncSession) -> VaultService:
    return VaultService(session)


# --------------------------------------------------------------------------- vaults


@router.get("", response_model=list[VaultOut])
async def list_vaults(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[VaultOut]:
    return await _service(session).list_vaults(user.id)


@router.post("", response_model=VaultOut, status_code=201)
async def create_vault(
    body: VaultCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> VaultOut:
    return await _service(session).create_vault(
        owner_id=user.id, name=body.name, description=body.description
    )


@router.get("/shared", response_model=list[VaultOut])
async def list_shared_vaults(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[VaultOut]:
    """Vaults the user may read via trusted-contact grants (cannot modify)."""
    return await _service(session).list_shared_vaults(user.id)


@router.get("/{vault_id}", response_model=VaultOut)
async def get_vault(
    vault_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> VaultOut:
    return await _service(session).get_vault(vault_id, user.id)


@router.patch("/{vault_id}", response_model=VaultOut)
async def update_vault(
    vault_id: uuid.UUID,
    body: VaultUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> VaultOut:
    return await _service(session).update_vault(
        vault_id, user.id, name=body.name, description=body.description
    )


@router.delete("/{vault_id}", status_code=204)
async def delete_vault(
    vault_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> None:
    await _service(session).delete_vault(vault_id, user.id)


# ----------------------------------------------------------------------- categories


@router.get("/{vault_id}/categories", response_model=list[CategoryOut])
async def list_categories(
    vault_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[CategoryOut]:
    return await _service(session).list_categories(vault_id, user.id)


@router.post("/{vault_id}/categories", response_model=CategoryOut, status_code=201)
async def create_category(
    vault_id: uuid.UUID,
    body: CategoryCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> CategoryOut:
    return await _service(session).create_category(vault_id, user.id, name=body.name)


# --------------------------------------------------------------------------- items


@router.get("/{vault_id}/items", response_model=list[ItemOut])
async def list_items(
    vault_id: uuid.UUID,
    item_type: str | None = Query(default=None),
    category_id: uuid.UUID | None = Query(default=None),
    include_archived: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[ItemOut]:
    return await _service(session).list_items(
        vault_id=vault_id,
        user_id=user.id,
        item_type=item_type,
        category_id=category_id,
        include_archived=include_archived,
    )


@router.post("/{vault_id}/items", response_model=ItemDetailOut, status_code=201)
async def create_item(
    vault_id: uuid.UUID,
    body: ItemCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> ItemDetailOut:
    return await _service(session).create_item(
        vault_id=vault_id,
        user_id=user.id,
        item_type=body.item_type,
        title=body.title,
        content=body.content,
        category_id=body.category_id,
        masked_summary=body.masked_summary,
    )


@router.get("/{vault_id}/items/{item_id}", response_model=ItemDetailOut)
async def get_item(
    vault_id: uuid.UUID,
    item_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> ItemDetailOut:
    # Ownership of the item is checked inside the service.
    return await _service(session).get_item(item_id, user.id)


@router.patch("/{vault_id}/items/{item_id}", response_model=ItemDetailOut)
async def update_item(
    vault_id: uuid.UUID,
    item_id: uuid.UUID,
    body: ItemUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> ItemDetailOut:
    return await _service(session).update_item(
        item_id,
        user.id,
        title=body.title,
        category_id=body.category_id,
        content=body.content,
        masked_summary=body.masked_summary,
        is_archived=body.is_archived,
    )


@router.delete("/{vault_id}/items/{item_id}", status_code=204)
async def delete_item(
    vault_id: uuid.UUID,
    item_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> None:
    await _service(session).delete_item(item_id, user.id)


@router.get("/{vault_id}/items/{item_id}/versions")
async def list_item_versions(
    vault_id: uuid.UUID,
    item_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[dict]:
    return await _service(session).list_versions(item_id, user.id)
