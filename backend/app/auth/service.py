"""Auth orchestration service.

Handles registration, login, token rotation, logout, and session management.
All sensitive operations are audited through the ``audit`` module.
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import cast

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    UserSession,
)
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
from app.notifications.email import EmailTransport, get_email_transport
from app.users.models import User
from app.users.repository import UserRepository


class AuthNotifier:
    """Sends auth-related emails through a transport."""

    def __init__(self, transport: EmailTransport) -> None:
        self._transport = transport

    async def send_password_reset(self, *, to: str, full_name: str | None, token: str) -> None:
        await self._transport.send(
            to=to,
            subject="LifeLink AI — Reset your password",
            text=(
                f"Hi {full_name or 'there'},\n\n"
                "We received a request to reset your LifeLink AI password.\n"
                f"Your reset token is: {token}\n\n"
                "This token expires in 30 minutes. If you did not request this, "
                "you can safely ignore this email.\n\n— LifeLink AI"
            ),
        )

    async def send_email_verification(self, *, to: str, full_name: str | None, token: str) -> None:
        await self._transport.send(
            to=to,
            subject="LifeLink AI — Verify your email",
            text=(
                f"Hi {full_name or 'there'},\n\n"
                "Please verify your email address to finish setting up your account.\n"
                f"Your verification token is: {token}\n\n"
                "This token expires in 24 hours.\n\n— LifeLink AI"
            ),
        )


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        users: UserRepository,
        notifier: AuthNotifier | None = None,
    ) -> None:
        self._session = session
        self._users = users
        self._notifier = notifier or AuthNotifier(get_email_transport())

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

    async def request_password_reset(self, *, email: str) -> bool:
        """Issue a password reset token and email it.

        Returns True if a user exists (the caller must NOT reveal this to
        clients; the endpoint always returns the same generic response).
        """
        user = await self._users.get_by_email(email)
        if user is None or not user.is_active:
            return False

        raw = generate_secret_token()
        record = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=utc_now() + timedelta(minutes=30),
        )
        self._session.add(record)
        await self._session.flush()

        await self._notifier.send_password_reset(to=user.email, full_name=user.full_name, token=raw)
        return True

    async def confirm_password_reset(self, *, token: str, new_password: str) -> None:
        record = await self._find_token(PasswordResetToken, token)
        if record is None or record.used_at is not None or record.expires_at <= utc_now():
            raise UnauthorizedError("Reset token is invalid or expired", code="INVALID_RESET_TOKEN")

        user = await self._users.get_by_id(record.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Account unavailable", code="ACCOUNT_DISABLED")

        record.used_at = utc_now()
        user.password_hash = hash_password(new_password)
        await self._revoke_all_sessions(user.id)
        await self._session.flush()

    async def request_email_verification(self, *, user: User) -> None:
        if user.is_verified:
            return
        raw = generate_secret_token()
        record = EmailVerificationToken(
            user_id=user.id,
            email=user.email,
            token_hash=hash_token(raw),
            expires_at=utc_now() + timedelta(hours=24),
        )
        self._session.add(record)
        await self._session.flush()

        await self._notifier.send_email_verification(
            to=user.email, full_name=user.full_name, token=raw
        )

    async def confirm_email_verification(self, *, token: str) -> None:
        record = await self._find_token(EmailVerificationToken, token)
        if record is None or record.used_at is not None or record.expires_at <= utc_now():
            raise UnauthorizedError(
                "Verification token is invalid or expired", code="INVALID_VERIFICATION_TOKEN"
            )

        user = await self._users.get_by_id(record.user_id)
        if user is None:
            raise UnauthorizedError("Account unavailable", code="ACCOUNT_DISABLED")

        record.used_at = utc_now()
        user.is_verified = True
        await self._session.flush()

    async def _find_token(
        self, model: type[PasswordResetToken] | type[EmailVerificationToken], raw: str
    ) -> PasswordResetToken | EmailVerificationToken | None:
        stmt = select(model).where(model.token_hash == hash_token(raw))
        result = (await self._session.execute(stmt)).scalar_one_or_none()
        if result is None:
            return None
        return cast(PasswordResetToken | EmailVerificationToken, result)

    async def _revoke_all_sessions(self, user_id: uuid.UUID) -> None:
        await self._session.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=utc_now())
        )

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
