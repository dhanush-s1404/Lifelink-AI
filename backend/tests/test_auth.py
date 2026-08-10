"""Integration tests for the auth API."""

from __future__ import annotations

from datetime import timedelta

import jwt

from app.config.settings import settings
from app.core.security import hash_token, utc_now
from app.users.repository import UserRepository


async def register_user(
    client, email="alice@example.com", password="StrongPass123!", full_name="Alice"
):
    return await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )


async def login_user(client, email="alice@example.com", password="StrongPass123!"):
    return await client.post("/api/v1/auth/login", json={"email": email, "password": password})


# --------------------------------------------------------------------------- register


async def test_register_returns_tokens(client) -> None:
    resp = await register_user(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["email"] == "alice@example.com"
    assert body["user"]["role"] == "user"
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]
    assert body["tokens"]["token_type"] == "bearer"


async def test_register_duplicate_email_conflicts(client) -> None:
    await register_user(client)
    resp = await register_user(client)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "EMAIL_TAKEN"


async def test_register_rejects_weak_password(client) -> None:
    resp = await register_user(client, password="short")
    assert resp.status_code == 422


async def test_password_stored_hashed(client, db_session) -> None:
    await register_user(client)
    user = await UserRepository(db_session).get_by_email("alice@example.com")
    assert user is not None
    assert user.password_hash != "StrongPass123!"
    assert user.password_hash.startswith("$argon2")


# --------------------------------------------------------------------------- login


async def test_login_success(client) -> None:
    await register_user(client)
    resp = await login_user(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["email"] == "alice@example.com"
    assert body["tokens"]["access_token"]


async def test_login_wrong_password_rejected(client) -> None:
    await register_user(client)
    resp = await login_user(client, password="WrongPass123!")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_login_unknown_email_rejected(client) -> None:
    resp = await login_user(client, email="ghost@example.com")
    assert resp.status_code == 401


# --------------------------------------------------------------------------- me


async def test_me_requires_auth(client) -> None:
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "NOT_AUTHENTICATED"


async def test_me_returns_profile(client) -> None:
    await register_user(client)
    resp = await login_user(client)
    access = resp.json()["tokens"]["access_token"]
    me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"


async def test_me_invalid_token_rejected(client) -> None:
    resp = await client.get(
        "/api/v1/users/me", headers={"Authorization": "Bearer not.a.valid.token"}
    )
    assert resp.status_code == 401


async def test_me_expired_token_rejected(client) -> None:
    expired = jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000000",
            "type": "access",
            "iat": utc_now() - timedelta(hours=2),
            "exp": utc_now() - timedelta(hours=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    resp = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401


async def test_me_wrong_token_type_rejected(client) -> None:
    """An access token crafted as a refresh-style token must be rejected."""
    payload = {
        "sub": "00000000-0000-0000-0000-000000000000",
        "type": "refresh",
        "iat": utc_now(),
        "exp": utc_now() + timedelta(minutes=15),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    resp = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


# --------------------------------------------------------------------------- refresh rotation


async def test_refresh_rotates_tokens(client) -> None:
    await register_user(client)
    login = await login_user(client)
    old_refresh = login.json()["tokens"]["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 200
    new_pair = resp.json()
    assert new_pair["access_token"]
    assert new_pair["refresh_token"] != old_refresh

    # Old token must now be rejected (rotation)
    reuse = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse.status_code == 401


async def test_refresh_invalid_token_rejected(client) -> None:
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token-value"}
    )
    assert resp.status_code == 401


async def test_refresh_expired_token_rejected(client, db_session) -> None:
    from sqlalchemy import select

    from app.auth.models import RefreshToken

    await register_user(client)
    login = await login_user(client)
    raw_token = login.json()["tokens"]["refresh_token"]

    record = (
        await db_session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token))
        )
    ).scalar_one()
    record.expires_at = utc_now() - timedelta(minutes=1)
    await db_session.commit()

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": raw_token})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "REFRESH_TOKEN_EXPIRED"


# --------------------------------------------------------------------------- logout


async def test_logout_revokes_refresh_token(client) -> None:
    await register_user(client)
    login = await login_user(client)
    refresh = login.json()["tokens"]["refresh_token"]

    resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh})
    assert resp.status_code == 204

    reuse = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert reuse.status_code == 401


async def test_logout_is_idempotent(client) -> None:
    await register_user(client)
    login = await login_user(client)
    refresh = login.json()["tokens"]["refresh_token"]
    await client.post("/api/v1/auth/logout", json={"refresh_token": refresh})
    again = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh})
    assert again.status_code == 204


# --------------------------------------------------------------------------- sessions


async def test_sessions_requires_auth(client) -> None:
    resp = await client.get("/api/v1/auth/sessions")
    assert resp.status_code == 401


async def test_sessions_lists_logins(client) -> None:
    await register_user(client)
    await login_user(client)
    login = await login_user(client)
    access = login.json()["tokens"]["access_token"]
    resp = await client.get("/api/v1/auth/sessions", headers={"Authorization": f"Bearer {access}"})
    assert resp.status_code == 200
    sessions = resp.json()
    assert len(sessions) >= 2


# --------------------------------------------------------------------------- RBAC


async def test_require_admin_blocks_regular_user(client) -> None:
    from fastapi import APIRouter, Depends

    from app.auth.deps import require_role
    from app.main import app
    from app.users.models import User, UserRole

    test_router = APIRouter()
    require_admin = require_role(UserRole.ADMIN)

    @test_router.get("/_test-admin")
    async def _admin_only(user: User = Depends(require_admin)):
        return {"ok": user.email}

    app.include_router(test_router)

    await register_user(client)
    login = await login_user(client)
    access = login.json()["tokens"]["access_token"]

    resp = await client.get("/_test-admin", headers={"Authorization": f"Bearer {access}"})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


async def test_require_admin_allows_admin(client, db_session) -> None:
    from fastapi import APIRouter, Depends

    from app.auth.deps import require_role
    from app.auth.password import hash_password
    from app.main import app
    from app.users.models import User, UserRole

    test_router = APIRouter()
    require_admin = require_role(UserRole.ADMIN)

    @test_router.get("/_test-admin-ok")
    async def _admin_only(user: User = Depends(require_admin)):
        return {"ok": user.email}

    app.include_router(test_router)

    await register_user(client)
    admin = User(
        email="boss@example.com",
        password_hash=hash_password("StrongPass123!"),
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    await db_session.commit()

    from app.auth.service import AuthService
    from app.users.repository import UserRepository

    service = AuthService(db_session, UserRepository(db_session))
    result = await service.login(
        email="boss@example.com", password="StrongPass123!", user_agent=None, ip_address=None
    )
    await db_session.commit()

    resp = await client.get(
        "/_test-admin-ok", headers={"Authorization": f"Bearer {result.tokens.access_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] == "boss@example.com"
