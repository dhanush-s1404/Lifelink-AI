"""Document API routes.

Documents attach to vault items as multipart uploads. Ownership is verified by
resolving the vault item's owning vault against the authenticated user.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.auth.deps import get_current_user
from app.documents.schemas import DocumentOut, DocumentUploadOut
from app.documents.service import DocumentService, UploadInput
from app.documents.storage import ObjectStorage, get_object_storage
from app.users.models import User

router = APIRouter(prefix="/vaults/{vault_id}/items/{item_id}/documents", tags=["documents"])


def _service(session: AsyncSession, storage: ObjectStorage) -> DocumentService:
    return DocumentService(session, storage)


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    item_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    storage: ObjectStorage = Depends(get_object_storage),
    user: User = Depends(get_current_user),
) -> list[DocumentOut]:
    return await _service(session, storage).list_for_item(item_id, user.id)


@router.post("", response_model=DocumentUploadOut, status_code=201)
async def upload_document(
    item_id: uuid.UUID,
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
    storage: ObjectStorage = Depends(get_object_storage),
    user: User = Depends(get_current_user),
) -> DocumentUploadOut:
    content = await file.read()
    return await _service(session, storage).upload(
        UploadInput(
            vault_item_id=item_id,
            owner_id=user.id,
            filename=file.filename or "file",
            content_type=file.content_type or "application/octet-stream",
            content=content,
        )
    )


@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    item_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    storage: ObjectStorage = Depends(get_object_storage),
    user: User = Depends(get_current_user),
) -> Response:
    filename, content_type, data = await _service(session, storage).download(
        document_id, item_id, user.id
    )
    quoted = filename.replace('"', "'")
    return Response(
        content=data,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{quoted}"',
            "Content-Length": str(len(data)),
        },
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    item_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    storage: ObjectStorage = Depends(get_object_storage),
    user: User = Depends(get_current_user),
) -> None:
    await _service(session, storage).delete(document_id, item_id, user.id)
