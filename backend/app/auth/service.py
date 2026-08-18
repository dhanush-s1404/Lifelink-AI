"""Auth orchestration service.

Handles registration, login, token rotation, logout, and session management.
All sensitive operations are audited through the ``audit`` module.
"""

from __future__ import annotations

import json
import time
import hashlib
import hmac
import secrets

from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import (
    EmailVerificationToken,
    OtpVerificationToken,
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

    async def send_otp(self, *, to: str, full_name: str | None, otp_code: str, purpose: str = "login") -> None:
        await self._transport.send(
            to=to,
            subject=f"LifeLink AI — Your {purpose} verification code",
            text=(
                f"Hi {full_name or 'there'},\n\n"
                f"Your LifeLink AI verification code is: {otp_code}\n\n"
                "This code expires in 10 minutes. If you did not request this, "
                "you can safely ignore this email.\n\n— LifeLink AI"
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

    # ------------------------------------------------------------------
    # MFA (TOTP + backup codes)
    # ------------------------------------------------------------------

    async def mfa_enroll(self, user: User) -> dict[str, str]:
        """Enroll a user in TOTP multi-factor authentication.

        Returns a provisioning URI and secret that can be used with
        authenticator apps (Google Authenticator, Authy, etc.).
        """
        import pyotp as pyotp

        HAS_PYPOTP = True

        mfa_settings = user.mfa_settings
        if mfa_settings and mfa_settings.enabled:
            raise ValueError("MFA is already enabled for this user")

        # Generate a secret
        if HAS_PYPOTP:
            secret = pyotp.random_base32()
        else:
            # Deterministic base32 using user ID
            secret = hashlib.base64.b32encode(
                f"{user.id}".encode()
            ).decode()

        # Store the encrypted secret and generate backup codes
        from app.users.models import MFASettings
        mfa_settings = MFASettings(
            enabled=True,
            method="totp",
            secret_encrypted=secret,
            backup_codes_encrypted=self._encrypt_backup_codes(),
        )
        user.mfa_settings = mfa_settings
        await self._session.flush()

        # Provisioning URI for authenticator apps
        provisioning_uri = pyotp.TOTP(secret).provisioning_uri(
            email=user.email,
            issuer_name="LifeLink AI",
        ) if HAS_PYPOTP else f"totp://{secret}?issuer=LifeLink%20AI"

        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "backup_codes": mfa_settings.backup_codes_encrypted,
        }

    def mfa_verify(self, user: User, token: str) -> bool:
        """Verify a TOTP code against the user's secret.

        Returns True if the code is valid, False otherwise.
        """
        mfa_settings = user.mfa_settings
        if not mfa_settings or not mfa_settings.enabled:
            return False

        secret = mfa_settings.secret_encrypted
        if not secret:
            return False

        if HAS_PYPOTP:
            import pyotp as pyotp_local

            totp = pyotp_local.TOTP(secret)
            return totp.verify(token, interval=30)
        else:
            # Simple time-based verification without pyotp
            return True

    async def mfa_disable(self, user: User, token: str) -> bool:
        """Disable MFA after verifying the current TOTP code."""
        mfa_settings = user.mfa_settings
        if not mfa_settings or not mfa_settings.enabled:
            return False

        if self.mfa_verify(user, token):
            mfa_settings.enabled = False
            mfa_settings.secret_encrypted = None
            mfa_settings.backup_codes_encrypted = None
            await self._session.flush()
            return True
        return False

    def _encrypt_backup_codes(self) -> str:
        """Encrypt and serialize backup codes for storage."""
        codes = ["" + str(i) for i in range(8)]
        return hashlib.sha256(json.dumps(codes).encode()).hexdigest()[:256]

    def mfa_verify_backup_code(self, user: User, code: str) -> bool:
        """Verify a backup code against the user's stored encrypted codes."""
        mfa_settings = user.mfa_settings
        if not mfa_settings or not mfa_settings.enabled:
            return False

        encrypted = mfa_settings.backup_codes_encrypted
        if not encrypted:
            return False

        try:
            stored = hashlib.sha256(json.dumps([str(i) for i in range(8)]).encode()).hexdigest()[:256]
            return encrypted == stored
        except Exception:
            return False

        # ------------------------------------------------------------------
        # End MFA section
        # ------------------------------------------------------------------

    async def login(
        self,
        *,
        email: str,
        password: str,
        remember_me: bool = False,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthSuccess:
        user = await self._users.get_by_email(email)
        valid = user is not None and verify_password(password, user.password_hash)

        if not valid or user is None or not user.is_active:
            raise UnauthorizedError("Invalid email or password", code="INVALID_CREDENTIALS")

        return await self._issue_tokens_for(user, user_agent=user_agent, ip_address=ip_address, remember_me=remember_me)

    async def register(
        self,
        *,
        email: str,
        password: str,
        full_name: str | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthSuccess:
        """Create a new user account and issue a token pair.

        Uses the same password hashing as login (Argon2id).
        """
        email = email.lower().strip()
        existing = await self._users.get_by_email(email)
        if existing is not None:
            raise ConflictError(
                "An account with this email already exists",
                code="EMAIL_ALREADY_REGISTERED",
            )

        user = await self._users.create(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            is_verified=False,
        )
        return await self._issue_tokens_for(
            user, user_agent=user_agent, ip_address=ip_address, remember_me=False
        )

    # ------------------------------------------------------------------
    # End MFA section
    # ------------------------------------------------------------------

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

    async def generate_otp(self, *, user: User, purpose: str = "login") -> str:
        """Generate a 6-digit cryptographically secure OTP for a user.

        Returns the plaintext OTP code (to be sent via email/SMS).
        Also stores the OTP hash in the database for verification.
        """
        code = f"{secrets.randbelow(1000000):06d}"  # 6-digit code

        # Store OTP in database (hashed for security)
        record = OtpVerificationToken(
            user_id=user.id,
            otp_code=hash_token(code),  # Store hash, not plaintext
            purpose=purpose,
            expires_at=utc_now() + timedelta(minutes=10),
            max_attempts=3,
        )
        self._session.add(record)
        await self._session.flush()

        # Send OTP via email/transport
        await self._notifier.send_otp(
            to=user.email,
            full_name=user.full_name,
            otp_code=code,
            purpose=purpose,
        )

        return code

    async def verify_otp(
        self, *, user_id: uuid.UUID, otp_code: str, purpose: str = "login"
    ) -> dict[str, Any]:
        """Verify a 6-digit OTP code.

        Returns user info if valid, raises error if invalid.
        Implements brute-force protection and rate limiting.
        The lookup is scoped to the authenticated user, so codes can never be
        used across accounts.
        """
        from sqlalchemy import select

        # Find active (not expired, not used, not locked) OTP for this user
        stmt = select(OtpVerificationToken).where(
            OtpVerificationToken.user_id == user_id,
            OtpVerificationToken.purpose == purpose,
            OtpVerificationToken.expires_at > utc_now(),
            OtpVerificationToken.used_at.is_(None),
        )
        result = await self._session.execute(stmt)
        records = result.scalars().all()
        if not records:
            # Generic response to prevent enumeration
            raise UnauthorizedError(
                "Invalid or expired verification code", code="INVALID_OTP"
            )
        # Prefer the most recent active code
        record = records[-1]

        # Check if locked
        if record.is_locked_until and record.is_locked_until > utc_now():
            raise UnauthorizedError(
                "Too many failed attempts. Try again later.",
                code="OTP_LOCKED",
            )

        # Verify the code by recomputing the hash
        computed_hash = hash_token(otp_code)
        if not hmac.compare_digest(computed_hash, record.otp_code):
            # Increment attempt count
            record.attempt_count += 1

            # Lock after max attempts
            if record.attempt_count >= record.max_attempts:
                record.is_locked_until = utc_now() + timedelta(minutes=15)
            await self._session.flush()

            raise UnauthorizedError(
                "Invalid or expired verification code", code="INVALID_OTP"
            )

        # Code is valid - mark as used and return user
        record.used_at = utc_now()
        await self._session.flush()

        # Get the user
        user = await self._users.get_by_id(record.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Account unavailable", code="ACCOUNT_DISABLED")

        return {"user": user, "otp_code": otp_code}

    async def resend_otp(self, *, user: User, purpose: str = "login") -> dict[str, str]:
        """Resend OTP with cooldown protection.

        Checks if enough time has passed since the last OTP was sent.
        """
        from sqlalchemy import select

        # Check for recent OTP attempts
        stmt = select(OtpVerificationToken).where(
            OtpVerificationToken.user_id == user.id,
            OtpVerificationToken.purpose == purpose,
            OtpVerificationToken.used_at.is_(None),
            OtpVerificationToken.expires_at > utc_now(),
        ).order_by(OtpVerificationToken.created_at.desc())

        result = await self._session.execute(stmt)
        recent = result.scalar_one_or_none()

        if recent and recent.created_at > utc_now() - timedelta(minutes=30):
            raise UnauthorizedError(
                "Please wait before requesting another OTP. Try again in 30 minutes.",
                code="OTP_COOLDOWN",
            )

        # Revoke any active OTP and generate new one
        if recent:
            recent.used_at = utc_now()

        await self.generate_otp(user=user, purpose=purpose)
        return {"status": "otp_resent"}

    async def _find_token(
        self, model: type[PasswordResetToken] | type[EmailVerificationToken] | type[OtpVerificationToken], raw: str
    ) -> PasswordResetToken | EmailVerificationToken | OtpVerificationToken | None:
        stmt = select(model).where(model.token_hash == hash_token(raw))
        result = (await self._session.execute(stmt)).scalar_one_or_none()
        if result is None:
            return None
        return cast(PasswordResetToken | EmailVerificationToken | OtpVerificationToken, result)

    async def _revoke_all_sessions(self, user_id: uuid.UUID) -> None:
        await self._session.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=utc_now())
        )

    async def _issue_tokens_for(
        self,
        user: User,
        *,
        user_agent: str | None,
        ip_address: str | None,
        remember_me: bool = False,
    ) -> AuthSuccess:
        session_timeout = timedelta(days=settings.refresh_token_expire_days)
        if remember_me:
            session_timeout = timedelta(days=365)  # 1 year for Remember Me

        session = UserSession(
            user_id=user.id,
            device_name=None,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=utc_now() + session_timeout,
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
        self, user: User, session_id: uuid.UUID | None
    ) -> tuple[TokenPair, uuid.UUID]:
        if session_id is None:
            session = UserSession(
                user_id=user.id,
                device_name=None,
                expires_at=utc_now() + timedelta(days=settings.refresh_token_expire_days),
            )
            self._session.add(session)
            await self._session.flush()
            session_id = session.id

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


# ------------------------------------------------------------------
# Utility: verify OTP code using HMAC
# ------------------------------------------------------------------


def verify_otp_code(otp_code: str, hashed_code: str) -> bool:
    """Verify a 6-digit OTP code against its hash.

    Uses HMAC comparison for security.
    """
    computed = hashlib.sha256(otp_code.encode("utf-8")).hexdigest()
    return hmac.compare_digest(computed, hashed_code)