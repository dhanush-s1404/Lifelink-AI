"""Auth API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.auth.deps import get_current_user
from app.auth.schemas import (
    AuthSuccess,
    EmailVerificationConfirm,
    EmailVerificationRequest,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from app.auth.service import AuthNotifier, AuthService
from app.notifications.email import EmailTransport, get_email_transport
from app.users.models import User
from app.users.repository import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_context(request: Request) -> dict:
    return {
        "user_agent": request.headers.get("User-Agent"),
        "ip_address": request.client.host if request.client else None,
    }


def _service(session: AsyncSession, transport: EmailTransport) -> AuthService:
    return AuthService(session, UserRepository(session), AuthNotifier(transport))


@router.post("/register", response_model=AuthSuccess, status_code=201)
async def register(
    body: RegisterRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    transport: EmailTransport = Depends(get_email_transport),
) -> AuthSuccess:
    service = _service(session, transport)
    return await service.register(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        **_client_context(request),
    )


@router.post("/login", response_model=AuthSuccess)
async def login(
    body: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> AuthSuccess:
    service = AuthService(session, UserRepository(session))
    return await service.login(
        email=body.email,
        password=body.password,
        **_client_context(request),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    body: RefreshRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenPair:
    service = AuthService(session, UserRepository(session))
    return await service.refresh(body.refresh_token)


@router.post("/logout", status_code=204)
async def logout(
    body: LogoutRequest,
    session: AsyncSession = Depends(get_session),
) -> None:
    service = AuthService(session, UserRepository(session))
    await service.logout(body.refresh_token)


@router.post("/password-reset/request", status_code=202)
async def request_password_reset(
    body: PasswordResetRequest,
    session: AsyncSession = Depends(get_session),
    transport: EmailTransport = Depends(get_email_transport),
) -> dict:
    """Request a password reset.

    Always returns 202 regardless of whether the email exists (anti-enumeration).
    """
    service = _service(session, transport)
    await service.request_password_reset(email=body.email)
    return {"status": "request_received"}


@router.post("/password-reset/confirm", status_code=204)
async def confirm_password_reset(
    body: PasswordResetConfirm,
    session: AsyncSession = Depends(get_session),
) -> None:
    service = AuthService(session, UserRepository(session))
    await service.confirm_password_reset(token=body.token, new_password=body.new_password)


@router.post("/verify-email/request", status_code=202)
async def request_email_verification(
    body: EmailVerificationRequest,
    session: AsyncSession = Depends(get_session),
    transport: EmailTransport = Depends(get_email_transport),
    user: User = Depends(get_current_user),
) -> dict:
    service = _service(session, transport)
    await service.request_email_verification(user=user)
    return {"status": "verification_sent"}


@router.post("/verify-email/confirm", status_code=204)
async def confirm_email_verification(
    body: EmailVerificationConfirm,
    session: AsyncSession = Depends(get_session),
) -> None:
    service = AuthService(session, UserRepository(session))
    await service.confirm_email_verification(token=body.token)


@router.get("/sessions")
async def list_sessions(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[dict]:
    """List active sessions for the current user (security dashboard)."""
    return await _list_active_sessions(session, user)


async def _list_active_sessions(session: AsyncSession, user: User) -> list[dict]:
    from sqlalchemy import select

    from app.auth.models import UserSession

    stmt = (
        select(UserSession)
        .where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None))
        .order_by(UserSession.created_at.desc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": str(s.id),
            "device_name": s.device_name,
            "ip_address": s.ip_address,
            "user_agent": s.user_agent,
            "last_seen_at": s.last_seen_at,
            "created_at": s.created_at,
            "is_current": False,
        }
        for s in rows
    ]
