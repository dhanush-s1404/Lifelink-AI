"""User persistence layer (repository pattern)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower().strip())
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        full_name: str | None = None,
        is_verified: bool = False,
    ) -> User:
        user = User(
            email=email.lower().strip(),
            password_hash=password_hash,
            full_name=full_name,
            is_verified=is_verified,
        )
        self._session.add(user)
        await self._session.flush()
        return user
