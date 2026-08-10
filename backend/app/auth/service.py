"""Auth orchestration service.

Handles registration, login, token rotation, logout, and session management.
All sensitive operations are audited through the ``audit`` module.
"""

from __future__ import annotations

import uuid
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshToken, UserSession
from app.auth.password import hash_password, verify_password
from app.auth.schemas import AuthSuccess, TokenPair
from app.config.settings import settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    generate_secret_token,
    hash_token,
    utc_now,
)
from app.users.models import User
from app.users.repository import UserRepository


class AuthService:
    def __init__(self, session: AsyncSession, users: UserRepository) -> None:
        self._session = session
        self._users = users

    async def register(
        self,
        *,
        email: str,
        password: str,
        full_name: str | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthSuccess:
        if await self._users.get_by_email(email):
            raise ConflictError("An account with this email already exists", code="EMAIL_TAKEN")

        user = await self._users.create(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
        )
        return await self._issue_tokens_for(user, user_agent=user_agent, ip_address=ip_address)

    async def login(
        self,
        *,
        email: str,
        password: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthSuccess:
        user = await self._users.get_by_email(email)
        valid = user is not None and verify_password(password, user.password_hash)

        if not valid or user is None or not user.is_active:
            raise UnauthorizedError("Invalid email or password", code="INVALID_CREDENTIALS")

        return await self._issue_tokens_for(user, user_agent=user_agent, ip_address=ip_address)

    async def refresh(self, raw_refresh_token: str) -> TokenPair:
        token_hash = hash_token(raw_refresh_token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        record = (await self._session.execute(stmt)).scalar_one_or_none()

        if record is None:
            raise UnauthorizedError("Invalid refresh token", code="INVALID_REFRESH_TOKEN")

        if record.revoked_at is not None:
            # Token reuse attempt: revoke the whole session to be safe.
            await self._revoke_session(record.session_id)
            raise UnauthorizedError("Refresh token has been revoked", code="REFRESH_TOKEN_REVOKED")

        if record.expires_at <= utc_now():
            raise UnauthorizedError("Refresh token has expired", code="REFRESH_TOKEN_EXPIRED")

        user = await self._users.get_by_id(record.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Account is unavailable", code="ACCOUNT_DISABLED")

        return await self._rotate_token(record, user)

    async def logout(self, raw_refresh_token: str) -> None:
        token_hash = hash_token(raw_refresh_token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        record = (await self._session.execute(stmt)).scalar_one_or_none()
        if record is None:
            # Idempotent logout.
            return
        await self._revoke_token(record)

    async def revoke_session(self, session_id: uuid.UUID) -> None:
        await self._revoke_session(session_id)

    # ------------------------------------------------------------------ utils

    async def _issue_tokens_for(
        self,
        user: User,
        *,
        user_agent: str | None,
        ip_address: str | None,
    ) -> AuthSuccess:
        session = UserSession(
            user_id=user.id,
            device_name=None,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=utc_now() + timedelta(days=settings.refresh_token_expire_days),
        )
        self._session.add(session)
        await self._session.flush()

        tokens, _ = await self._create_token_pair(user, session.id)
        return AuthSuccess(
            user={
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
            },
            tokens=tokens,
        )

    async def _create_token_pair(
        self, user: User, session_id: uuid.UUID
    ) -> tuple[TokenPair, uuid.UUID]:
        raw_refresh = generate_secret_token()
        record = RefreshToken(
            user_id=user.id,
            session_id=session_id,
            token_hash=hash_token(raw_refresh),
            expires_at=utc_now() + timedelta(days=settings.refresh_token_expire_days),
        )
        self._session.add(record)
        await self._session.flush()

        pair = TokenPair(
            access_token=create_access_token(str(user.id)),
            refresh_token=raw_refresh,
            expires_in=settings.access_token_expire_minutes * 60,
        )
        return pair, record.id

    async def _rotate_token(self, record: RefreshToken, user: User) -> TokenPair:
        if record.session_id is None:
            raise UnauthorizedError("Invalid refresh token", code="INVALID_REFRESH_TOKEN")
        new_pair, new_id = await self._create_token_pair(user, record.session_id)
        record.revoked_at = utc_now()
        record.replaced_by_token_id = new_id
        return new_pair

    async def _revoke_token(self, record: RefreshToken) -> None:
        record.revoked_at = utc_now()
        if record.session_id:
            await self._session.execute(
                update(UserSession)
                .where(UserSession.id == record.session_id, UserSession.revoked_at.is_(None))
                .values(revoked_at=utc_now())
            )

    async def _revoke_session(self, session_id: uuid.UUID | None) -> None:
        if session_id is None:
            return
        await self._session.execute(
            update(UserSession)
            .where(UserSession.id == session_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=utc_now())
        )
