"""Object storage abstraction.

Documents are stored as opaque blobs in an S3-compatible object store (MinIO in
dev, AWS S3 in production). An in-memory implementation is provided for tests so
the rest of the system never depends on a running object store.

Only the application holds bucket credentials; content is stored at rest
encrypted or not, depending on configuration. Object keys are opaque (never user
filenames) to prevent traversal and collisions.
"""

from __future__ import annotations

import asyncio
import io
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config.settings import settings


class StorageError(Exception):
    """Raised when an object-store operation fails."""


class ObjectStorage(ABC):
    """Async object storage interface (all operations are safe to await)."""

    @abstractmethod
    async def put(self, *, key: str, data: bytes, content_type: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def exists(self, key: str) -> bool:
        raise NotImplementedError


def generate_object_key(*, original_name: str) -> str:
    """Build an opaque storage key: ``<random-uuid>/<safe-basename>``."""
    safe = Path(original_name).name or "file"
    safe = "".join(ch for ch in safe if ch.isalnum() or ch in "._- ").strip().replace(" ", "_")
    return f"{uuid.uuid4().hex}/{safe}"


class S3ObjectStorage(ObjectStorage):
    """S3 / MinIO implementation using boto3 (run off the event loop)."""

    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool,
    ) -> None:
        scheme = "https" if secure else "http"
        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=f"{scheme}://{endpoint}",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
            config=Config(signature_version="s3v4"),
        )

    def _ensure_bucket_sync(self) -> None:
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            try:
                self._client.create_bucket(Bucket=self._bucket)
            except (BotoCoreError, ClientError) as exc:
                raise StorageError("Unable to create object storage bucket") from exc

    async def put(self, *, key: str, data: bytes, content_type: str) -> None:
        await asyncio.to_thread(self._put_sync, key, data, content_type)

    def _put_sync(self, key: str, data: bytes, content_type: str) -> None:
        try:
            self._client.put_object(
                Bucket=self._bucket, Key=key, Body=io.BytesIO(data), ContentType=content_type
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError("Unable to store object") from exc

    async def get(self, key: str) -> bytes:
        return await asyncio.to_thread(self._get_sync, key)

    def _get_sync(self, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            return response["Body"].read()
        except (BotoCoreError, ClientError) as exc:
            raise StorageError("Unable to read object") from exc

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._delete_sync, key)

    def _delete_sync(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except (BotoCoreError, ClientError) as exc:
            raise StorageError("Unable to delete object") from exc

    async def exists(self, key: str) -> bool:
        return await asyncio.to_thread(self._exists_sync, key)

    def _exists_sync(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError:
            return False


class InMemoryObjectStorage(ObjectStorage):
    """Dict-backed storage for tests and local development."""

    def __init__(self) -> None:
        self._blobs: dict[str, bytes] = {}

    async def put(self, *, key: str, data: bytes, content_type: str) -> None:
        self._blobs[key] = data

    async def get(self, key: str) -> bytes:
        if key not in self._blobs:
            raise StorageError("Object not found")
        return self._blobs[key]

    async def delete(self, key: str) -> None:
        self._blobs.pop(key, None)

    async def exists(self, key: str) -> bool:
        return key in self._blobs


def build_object_storage() -> ObjectStorage:
    if settings.environment == "test":
        return InMemoryObjectStorage()
    return S3ObjectStorage(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_root_user,
        secret_key=settings.minio_root_password,
        bucket=settings.minio_bucket,
        secure=settings.minio_secure,
    )


def get_object_storage() -> ObjectStorage:
    """FastAPI dependency for the object storage (overridable in tests)."""
    return build_object_storage()
