# Admin routes for LifeLink AI - document and access management.
# Provides administrative endpoints for user management, vault administration,
# document oversight, access control management, and system statistics.
# These endpoints are restricted to authenticated administrators only.

from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])