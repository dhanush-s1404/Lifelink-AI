"""User profile API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.auth.deps import get_current_user
from app.auth.password import hash_password, verify_password
from app.core.exceptions import UnauthorizedError
from app.users.models import User
from app.users.schemas import PasswordChange, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UserUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> User:
    if body.full_name is not None:
        user.full_name = body.full_name
    await session.flush()
    return user


@router.post("/me/password", status_code=204)
async def change_password(
    body: PasswordChange,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> None:
    if not verify_password(body.current_password, user.password_hash):
        raise UnauthorizedError("Current password is incorrect", code="WRONG_PASSWORD")
    user.password_hash = hash_password(body.new_password)
    await session.flush()
