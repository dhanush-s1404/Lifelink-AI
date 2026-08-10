"""Auth dependencies: current user resolution and RBAC guards."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import TokenError, decode_access_token
from app.users.models import User, UserRole
from app.users.repository import UserRepository


async def get_current_user(request: Request, session: AsyncSession = Depends(get_session)) -> User:
    """Resolve the authenticated user from the Bearer access token."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise UnauthorizedError("Authentication required", code="NOT_AUTHENTICATED")

    token = auth_header.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
    except TokenError as exc:
        raise UnauthorizedError(str(exc), code="INVALID_TOKEN") from exc

    user_id = payload.get("sub")
    try:
        parsed = uuid.UUID(user_id) if user_id else None
    except (ValueError, TypeError):
        parsed = None

    user = await UserRepository(session).get_by_id(parsed) if parsed else None
    if user is None or not user.is_active:
        raise UnauthorizedError("Account unavailable", code="ACCOUNT_DISABLED")
    return user


def require_role(*roles: UserRole):
    """Guard requiring one of the given roles on the current user."""

    async def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise ForbiddenError("You do not have permission to perform this action")
        return user

    return _guard


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]
