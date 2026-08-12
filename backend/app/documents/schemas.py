"""Document API schemas (DTOs)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vault_item_id: uuid.UUID
    original_filename: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime


class DocumentUploadOut(BaseModel):
    """Returned after a successful upload."""

    document: DocumentOut
    message: str = Field(default="Document uploaded successfully")
