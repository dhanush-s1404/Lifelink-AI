"""Integration tests for the core ORM models."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.auth.models import RefreshToken, UserSession
from app.users.models import User, UserRole


async def test_create_user_persists(db_session) -> None:
    user = User(email="alice@example.com", password_hash="hashed-value", full_name="Alice")
    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.email == "alice@example.com"))
    stored = result.scalar_one()
    assert stored.id is not None
    assert stored.full_name == "Alice"
    assert stored.role == UserRole.USER
    assert stored.is_active is True
    assert stored.is_verified is False
    assert stored.created_at is not None


async def test_email_is_unique(db_session) -> None:
    from sqlalchemy.exc import IntegrityError

    db_session.add(User(email="dup@example.com", password_hash="h1"))
    await db_session.commit()

    db_session.add(User(email="dup@example.com", password_hash="h2"))
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_session_and_refresh_token_link_to_user(db_session) -> None:
    from datetime import UTC, datetime, timedelta

    user = User(email="bob@example.com", password_hash="hashed")
    db_session.add(user)
    await db_session.flush()

    session = UserSession(
        user_id=user.id,
        device_name="Chrome on Windows",
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    db_session.add(session)
    await db_session.flush()

    token = RefreshToken(
        user_id=user.id,
        session_id=session.id,
        token_hash="sha256-of-token",
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    db_session.add(token)
    await db_session.commit()

    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == "sha256-of-token")
    )
    stored = result.scalar_one()
    assert stored.user_id == user.id
    assert stored.session_id == session.id
    assert stored.revoked_at is None


async def test_mfa_settings_one_to_one(db_session) -> None:
    from app.users.models import MFASettings

    user = User(email="mfa@example.com", password_hash="hashed")
    db_session.add(user)
    await db_session.flush()

    db_session.add(MFASettings(user_id=user.id, enabled=True, secret_encrypted="enc-secret"))
    await db_session.commit()

    result = await db_session.execute(select(MFASettings).where(MFASettings.user_id == user.id))
    mfa = result.scalar_one()
    assert mfa.enabled is True
    assert mfa.user.email == "mfa@example.com"
