"""Top-level API router assembling all versioned sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.auth.routes import router as auth_router
from app.config.settings import settings
from app.dashboard.routes import router as dashboard_router
from app.emergency.routes import router as emergency_router
from app.trusted_contacts.routes import router as contacts_router
from app.users.routes import router as users_router
from app.vault.routes import router as vault_router

api_router = APIRouter(prefix=settings.api_v1_prefix)

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(dashboard_router)
api_router.include_router(vault_router)
api_router.include_router(contacts_router)
api_router.include_router(emergency_router)


@api_router.get("/ping", tags=["system"])
async def ping() -> dict[str, str]:
    return {"status": "pong"}
