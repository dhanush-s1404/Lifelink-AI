"""Integration tests for password reset and email verification flows."""

from __future__ import annotations

import re

from sqlalchemy import select

from app.auth.models import EmailVerificationToken, PasswordResetToken
from app.core.security import hash_token
from app.users.repository import UserRepository

TOKEN_RE = re.compile(r"Your (?:reset|verification) token is: ([A-Za-z0-9_\-]+)")


def extract_token(text: str) -> str:
    match = TOKEN_RE.search(text)
    assert match, f"no token found in email: {text}"
    return match.group(1)


async def register_user(client, email="carol@example.com", password="StrongPass123!"):
    return await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Carol"},
    )


async def login_user(client, email="carol@example.com", password="StrongPass123!"):
    return await client.post("/api/v1/auth/login", json={"email": email, "password": password})


# ----------------------------------------------------------------- password reset


async def test_password_reset_request_always_returns_202(client) -> None:
    resp = await client.post(
        "/api/v1/auth/password-reset/request", json={"email": "ghost@example.com"}
    )
    assert resp.status_code == 202
    assert resp.json()["status"] == "request_received"


async def test_password_reset_full_flow(client, db_session) -> None:
    await register_user(client)

    resp = await client.post(
        "/api/v1/auth/password-reset/request", json={"email": "carol@example.com"}
    )
    assert resp.status_code == 202

    assert len(client.captured_emails) == 1
    email = client.captured_emails[0]
    assert email["to"] == "carol@example.com"
    raw_token = extract_token(email["text"])

    record = (
        await db_session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(raw_token))
        )
    ).scalar_one()
    assert record.used_at is None

    # Wrong token is rejected.
    bad = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": "x" * 64, "new_password": "NewPass123!"},
    )
    assert bad.status_code == 401

    # Correct token resets the password and revokes sessions.
    ok = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "BrandNewPass123!"},
    )
    assert ok.status_code == 204

    # Old password no longer works; new one does.
    old = await login_user(client, password="StrongPass123!")
    assert old.status_code == 401
    new = await login_user(client, password="BrandNewPass123!")
    assert new.status_code == 200


async def test_password_reset_token_is_single_use(client, db_session) -> None:
    await register_user(client)
    await client.post("/api/v1/auth/password-reset/request", json={"email": "carol@example.com"})
    raw_token = extract_token(client.captured_emails[0]["text"])

    first = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "BrandNewPass123!"},
    )
    assert first.status_code == 204

    second = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "YetAnotherPass123!"},
    )
    assert second.status_code == 401


async def test_password_reset_confirm_rejects_expired_token(client, db_session) -> None:
    from datetime import timedelta

    from app.core.security import utc_now

    await register_user(client)
    await client.post("/api/v1/auth/password-reset/request", json={"email": "carol@example.com"})
    raw_token = extract_token(client.captured_emails[0]["text"])

    record = (
        await db_session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(raw_token))
        )
    ).scalar_one()
    record.expires_at = utc_now() - timedelta(minutes=1)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "BrandNewPass123!"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_RESET_TOKEN"


# ----------------------------------------------------------------- email verification


async def test_email_verification_requires_auth(client) -> None:
    resp = await client.post("/api/v1/auth/verify-email/request", json={})
    assert resp.status_code == 401


async def test_email_verification_full_flow(client, db_session) -> None:
    await register_user(client)
    login = await login_user(client)
    access = login.json()["tokens"]["access_token"]

    user = await UserRepository(db_session).get_by_email("carol@example.com")
    assert user is not None and user.is_verified is False

    resp = await client.post(
        "/api/v1/auth/verify-email/request",
        json={},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 202

    assert len(client.captured_emails) == 1
    raw_token = extract_token(client.captured_emails[0]["text"])

    record = (
        await db_session.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == hash_token(raw_token)
            )
        )
    ).scalar_one()
    assert record is not None

    ok = await client.post("/api/v1/auth/verify-email/confirm", json={"token": raw_token})
    assert ok.status_code == 204

    await db_session.refresh(user)
    assert user.is_verified is True
