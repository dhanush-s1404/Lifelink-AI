"""Document persistence layer (repository pattern)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.models import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        vault_item_id: uuid.UUID,
        owner_id: uuid.UUID,
        original_filename: str,
        content_type: str,
        size_bytes: int,
        storage_key: str,
    ) -> Document:
        from app.core.security import utc_now

        document = Document(
            vault_item_id=vault_item_id,
            owner_id=owner_id,
            original_filename=original_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_key=storage_key,
            uploaded_at=utc_now(),
        )
        self._session.add(document)
        await self._session.flush()
        return document

    async def get(self, document_id: uuid.UUID) -> Document | None:
        return await self._session.get(Document, document_id)

    async def get_for_item(self, document_id: uuid.UUID, vault_item_id: uuid.UUID) -> Document | None:
        stmt = select(Document).where(
            Document.id == document_id,
            Document.vault_item_id == vault_item_id,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_for_item(self, vault_item_id: uuid.UUID) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.vault_item_id == vault_item_id)
            .order_by(Document.uploaded_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
