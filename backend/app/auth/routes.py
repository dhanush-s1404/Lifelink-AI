"""Auth API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, HTTPException, status
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
    OtpVerifyRequest,
    OtpResendRequest,
)
from app.auth.service import AuthNotifier, AuthService
from app.ai.assistant import AIAssistant
from app.core.security import utc_now
from app.notifications.email import EmailTransport, get_email_transport
from app.users.models import User
from app.users.repository import UserRepository
from app.security.middleware import RateLimiter

# Rate limiter instances per endpoint
login_limiter = RateLimiter(calls=5, period=60)      # 5 login attempts per minute
register_limiter = RateLimiter(calls=3, period=60)   # 3 registration attempts per minute
otp_limiter = RateLimiter(calls=3, period=60)        # 3 OTP attempts per minute
email_limiter = RateLimiter(calls=5, period=60)     # 5 email verification attempts per minute
ai_limiter = RateLimiter(calls=10, period=60)       # 10 AI chat requests per minute

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_context(request: Request) -> dict:
    return {
        "user_agent": request.headers.get("User-Agent"),
        "ip_address": request.client.host if request.client else None,
    }


def _check_rate_limit(limiter: RateLimiter, request: Request) -> None:
    """Check rate limit and raise 429 if exceeded."""
    if not limiter.allow(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again later.",
        )


def _service(session: AsyncSession, transport: EmailTransport) -> AuthService:
    return AuthService(session, UserRepository(session), AuthNotifier(transport))


@router.post("/register", response_model=AuthSuccess, status_code=201)
async def register(
    body: RegisterRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    transport: EmailTransport = Depends(get_email_transport),
) -> AuthSuccess:
    _check_rate_limit(register_limiter, request)
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
    _check_rate_limit(login_limiter, request)
    service = AuthService(session, UserRepository(session))
    return await service.login(
        email=body.email,
        password=body.password,
        remember_me=body.remember_me if hasattr(body, "remember_me") else False,
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
    request: Request,
    session: AsyncSession = Depends(get_session),
    transport: EmailTransport = Depends(get_email_transport),
) -> dict:
    """Request a password reset.

    Always returns 202 regardless of whether the email exists (anti-enumeration).
    """
    _check_rate_limit(email_limiter, request)
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


@router.post("/otp/generate", response_model=AuthSuccess)
async def generate_otp(
    body: OtpResendRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    transport: EmailTransport = Depends(get_email_transport),
    user: User = Depends(get_current_user),
) -> AuthSuccess:
    _check_rate_limit(otp_limiter, request)
    service = _service(session, transport)
    code = await service.generate_otp(user=user, purpose=body.purpose)
    return AuthSuccess(
        user={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
        },
        tokens=None,
    )


@router.post("/otp/verify", response_model=AuthSuccess)
async def verify_otp(
    body: OtpVerifyRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> AuthSuccess:
    _check_rate_limit(otp_limiter, request)
    service = AuthService(session, UserRepository(session))
    result = await service.verify_otp(
        user_id=user.id, otp_code=body.otp_code, purpose=body.purpose
    )
    user = result["user"]
    tokens, _ = await service._create_token_pair(user, None)
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


@router.post("/otp/resend", response_model=dict[str, str])
async def resend_otp(
    body: OtpResendRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    _check_rate_limit(otp_limiter, request)
    service = AuthService(session, UserRepository(session))
    result = await service.resend_otp(user=user, purpose=body.purpose)
    return result


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


@router.post("/ai/chat", response_model=dict)
async def ai_chat(
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict:
    """Chat with the LifeLink AI assistant."""
    _check_rate_limit(ai_limiter, request)
    
    body = await request.json()
    message = body.get("message", "")
    
    if not message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message is required",
        )
    
    # Use the AI assistant to respond
    assistant = AIAssistant()
    result = assistant.ask(message, str(user.id))

    return {
        "response": result.answer,
        "status": "success",
    }
