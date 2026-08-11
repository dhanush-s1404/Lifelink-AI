"""ORM model registry.

Importing this module registers every ORM model on ``Base.metadata`` so Alembic
autogenerate and other tooling can discover the full schema.
"""

from __future__ import annotations

from app.auth.models import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    UserSession,
)
from app.trusted_contacts.models import ContactStatus, TrustedContact
from app.users.models import MFASettings, User
from app.vault.models import Category, ItemType, ItemVersion, Vault, VaultItem

__all__ = [
    "Category",
    "ContactStatus",
    "EmailVerificationToken",
    "ItemType",
    "ItemVersion",
    "MFASettings",
    "PasswordResetToken",
    "RefreshToken",
    "TrustedContact",
    "User",
    "UserSession",
    "Vault",
    "VaultItem",
    "import_all_models",
]


def import_all_models() -> None:
    """No-op that guarantees model modules are imported."""
    return None
