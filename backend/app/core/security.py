"""Core security primitives: JWT handling and token hashing.

Sensitive values (raw tokens, secrets) must never be logged or returned after use.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.config.settings import settings


class TokenError(Exception):
    """Raised when a token is invalid, expired, or malformed."""


def utc_now() -> datetime:
    return datetime.now(UTC)


def generate_secret_token() -> str:
    """Generate a cryptographically secure random token (URL-safe, 48 bytes)."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """One-way hash of a token value for storage/DB lookup.

    Uses SHA-256; tokens carry enough entropy (48 random bytes) to make brute
    force infeasible, so a fast hash is acceptable here.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(subject: str, *, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived JWT access token (default from settings)."""
    expires = utc_now() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "iat": utc_now(),
        "exp": expires,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an access token. Raises TokenError on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp", "type"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Invalid token") from exc

    if payload.get("type") != "access":
        raise TokenError("Invalid token type")
    return payload
