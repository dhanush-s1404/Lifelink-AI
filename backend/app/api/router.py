"""Top-level API router assembling all versioned sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.config.settings import settings

api_router = APIRouter(prefix=settings.api_v1_prefix)

# Domain routers are mounted in their respective milestones:
#   from app.auth import router as auth_router
#   api_router.include_router(auth_router)


def include_domain_routers(router: APIRouter) -> APIRouter:
    """Mount domain routers onto the versioned router."""
    # (deferred to later milestones)
    return router


@api_router.get("/ping", tags=["system"])
async def ping() -> dict[str, str]:
    return {"status": "pong"}
