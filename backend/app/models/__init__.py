"""ORM model registry.

Importing this module registers every ORM model on ``Base.metadata`` so Alembic
autogenerate and other tooling can discover the full schema.
"""

from __future__ import annotations

from app.auth.models import RefreshToken, UserSession
from app.users.models import MFASettings, User

__all__ = [
    "MFASettings",
    "RefreshToken",
    "User",
    "UserSession",
    "import_all_models",
]


def import_all_models() -> None:
    """No-op that guarantees model modules are imported."""
    return None
