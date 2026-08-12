"""Document orchestration service with ownership checks."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.documents.models import Document
from app.documents.repository import DocumentRepository
from app.documents.schemas import DocumentOut, DocumentUploadOut
from app.documents.storage import ObjectStorage, StorageError, generate_object_key
from app.vault.models import VaultItem
from app.vault.repository import VaultRepository

# Whitelist of allowed document MIME types (upload validation).
ALLOWED_MIME_TYPES: dict[str, set[str]] = {
    "application/pdf": {".pdf"},
    "image/png": {".png"},
    "image/jpeg": {".jpg", ".jpeg"},
    "image/webp": {".webp"},
    "text/plain": {".txt", ".md", ".log"},
    "text/csv": {".csv"},
    "application/json": {".json"},
    "application/msword": {".doc"},
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {".docx"},
    "application/vnd.ms-excel": {".xls"},
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {".xlsx"},
}

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


@dataclass
class UploadInput:
    vault_item_id: uuid.UUID
    owner_id: uuid.UUID
    filename: str
    content_type: str
    content: bytes


class DocumentService:
    def __init__(self, session: AsyncSession, storage: ObjectStorage) -> None:
        self._session = session
        self._repo = DocumentRepository(session)
        self._vaults = VaultRepository(session)
        self._storage = storage

    async def upload(self, upload: UploadInput) -> DocumentUploadOut:
        item = await self._require_owned_item(upload.vault_item_id, upload.owner_id)
        self._validate(upload)

        key = generate_object_key(original_name=upload.filename)
        try:
            await self._storage.put(key=key, data=upload.content, content_type=upload.content_type)
        except StorageError as exc:
            raise StorageError("Unable to store the uploaded file") from exc

        document = await self._repo.create(
            vault_item_id=item.id,
            owner_id=upload.owner_id,
            original_filename=upload.filename,
            content_type=upload.content_type,
            size_bytes=len(upload.content),
            storage_key=key,
        )
        return DocumentUploadOut(document=DocumentOut.model_validate(document))

    async def list_for_item(self, vault_item_id: uuid.UUID, user_id: uuid.UUID) -> list[DocumentOut]:
        item = await self._require_owned_item(vault_item_id, user_id)
        return [
            DocumentOut.model_validate(d)
            for d in await self._repo.list_for_item(item.id)
        ]

    async def download(self, document_id: uuid.UUID, vault_item_id: uuid.UUID, user_id: uuid.UUID) -> tuple[str, str, bytes]:
        item = await self._require_owned_item(vault_item_id, user_id)
        document = await self._repo.get_for_item(document_id, item.id)
        if document is None:
            raise NotFoundError("Document not found", code="DOCUMENT_NOT_FOUND")

        try:
            data = await self._storage.get(document.storage_key)
        except StorageError as exc:
            raise NotFoundError("Document content is unavailable", code="DOCUMENT_CONTENT_MISSING") from exc
        return document.original_filename, document.content_type, data

    async def delete(self, document_id: uuid.UUID, vault_item_id: uuid.UUID, user_id: uuid.UUID) -> None:
        item = await self._require_owned_item(vault_item_id, user_id)
        document = await self._repo.get_for_item(document_id, item.id)
        if document is None:
            raise NotFoundError("Document not found", code="DOCUMENT_NOT_FOUND")

        await self._storage.delete(document.storage_key)
        await self._session.delete(document)
        await self._session.flush()

    # ------------------------------------------------------------------ helpers

    def _validate(self, upload: UploadInput) -> None:
        allowed_exts = ALLOWED_MIME_TYPES.get(upload.content_type)
        if allowed_exts is None:
            raise ValidationAppError(
                "This file type is not allowed", code="DOCUMENT_TYPE_NOT_ALLOWED"
            )
        ext = (upload.filename.rsplit(".", 1)[-1].lower() if "." in upload.filename else "")
        if f".{ext}" not in allowed_exts:
            raise ValidationAppError(
                "File extension does not match its type", code="DOCUMENT_EXTENSION_MISMATCH"
            )
        if not upload.content:
            raise ValidationAppError("Empty files are not allowed", code="DOCUMENT_EMPTY")
        if len(upload.content) > MAX_UPLOAD_BYTES:
            raise ValidationAppError("File is too large (max 20 MB)", code="DOCUMENT_TOO_LARGE")

    async def _require_owned_item(self, vault_item_id: uuid.UUID, user_id: uuid.UUID) -> VaultItem:
        item = await self._vaults.get_item(vault_item_id)
        if item is None:
            raise NotFoundError("Item not found", code="ITEM_NOT_FOUND")
        vault = await self._vaults.get_vault(item.vault_id)
        if vault is None or vault.owner_id != user_id:
            raise ForbiddenError(
                "You do not have access to this item", code="ITEM_ACCESS_DENIED"
            )
        return item
