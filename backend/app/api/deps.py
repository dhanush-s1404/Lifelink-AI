"""Shared FastAPI dependencies (dependency injection)."""

from __future__ import annotations

from fastapi import Request

from app.database import get_session

__all__ = ["get_session", "get_request"]


async def get_request(request: Request) -> Request:
    """Expose the raw request for middleware-style logic inside endpoints."""
    return request
