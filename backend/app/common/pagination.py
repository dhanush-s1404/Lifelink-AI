"""Common pagination helpers."""

from __future__ import annotations

from math import ceil

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Query parameters accepted by list endpoints."""

    page: int = Field(default=1, ge=1, le=10000)
    size: int = Field(default=20, ge=1, le=100)
    sort: str | None = Field(default=None, description="Column to sort by, e.g. created_at")
    order: str = Field(default="desc", pattern="^(asc|desc)$")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


def total_pages(total: int, size: int) -> int:
    return ceil(total / size) if size > 0 else 0
