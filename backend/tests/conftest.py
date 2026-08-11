"""Shared test fixtures.

Integration tests run against a dedicated PostgreSQL test database
(``lifelink_test``). Schema is created/dropped once per session on a dedicated
loop; every test gets its own engine bound to its own event loop to avoid
asyncio cross-loop connection errors (especially on Windows, where asyncpg
requires a selector event loop).
"""

from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import models as _models  # noqa: F401  (register ORM models)
from app.config.settings import get_settings
from app.database.base import Base
from app.main import app

# On Windows, asyncpg requires a selector (not proactor) event loop. Set the
# policy before pytest-asyncio creates any event loops.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TEST_DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
TEST_DB_URL = f"postgresql+asyncpg://lifelink:lifelink@{TEST_DB_HOST}:5432/lifelink_test"


@pytest.fixture(scope="session")
def event_loop():
    """A single session-scoped event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def test_schema(event_loop) -> None:
    """Create the full schema once per session, drop it at the end."""
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_engine(test_schema) -> AsyncGenerator:
    """A per-test engine bound to the current test's event loop."""
    engine = create_async_engine(
        TEST_DB_URL, pool_pre_ping=True, execution_options={"eager_defaults": True}
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(bind=db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


class CapturingTransport:
    """In-memory email transport that records messages for assertions."""

    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send(self, *, to: str, subject: str, text: str, html: str | None = None) -> None:
        self.sent.append({"to": to, "subject": subject, "text": text})


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    factory = async_sessionmaker(bind=db_engine, expire_on_commit=False)

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    from app.database import get_session
    from app.notifications.email import get_email_transport

    app.dependency_overrides[get_session] = override_get_session

    transport = CapturingTransport()
    app.dependency_overrides[get_email_transport] = lambda: transport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        ac.captured_emails = transport.sent
        yield ac

    app.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest_asyncio.fixture(autouse=True)
async def _clean_db(db_engine) -> AsyncGenerator[None, None]:
    """Truncate every table between tests to keep them isolated."""
    tables = [t.name for t in Base.metadata.sorted_tables]
    if tables:
        stmt = text(f"TRUNCATE TABLE {', '.join(tables)} CASCADE")
        async with db_engine.begin() as conn:
            await conn.execute(stmt)
    yield
