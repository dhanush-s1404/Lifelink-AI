"""Shared response/request schemas used across modules."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Page[T](BaseModel):
    """Generic paginated response envelope.

    - ``items``: the page's records.
    - ``total``: total number of records matching the query.
    - ``page``: 1-based current page number.
    - ``size``: number of records per page.
    - ``pages``: total number of pages.
    """

    items: list[T]
    total: int
    page: int = Field(ge=1)
    size: int = Field(ge=1)
    pages: int = Field(ge=0)

    @classmethod
    def build(cls, items: list[T], total: int, page: int, size: int) -> Page[T]:
        pages = (total + size - 1) // size if size > 0 else 0
        return cls(items=items, total=total, page=page, size=size, pages=pages)
