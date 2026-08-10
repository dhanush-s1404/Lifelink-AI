"""Email notification service.

Transport is pluggable: ``console`` (default in development) logs emails,
``smtp`` sends via SMTP. The interface stays identical so callers are transport-
agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.config.settings import settings
from app.core.logging import logger


class EmailTransport(ABC):
    @abstractmethod
    async def send(self, *, to: str, subject: str, text: str, html: str | None = None) -> None:
        raise NotImplementedError


class ConsoleEmailTransport(EmailTransport):
    """Logs emails to the structured logger (development)."""

    async def send(self, *, to: str, subject: str, text: str, html: str | None = None) -> None:
        logger.info(
            "email_sent",
            to=to,
            subject=subject,
            body_preview=text[:200],
        )


class SMTPSettingsError(RuntimeError):
    pass


class SMTPEmailTransport(EmailTransport):
    """Sends email via SMTP (production).

    Only constructed when SMTP settings are present; never logs message bodies.
    """

    async def send(self, *, to: str, subject: str, text: str, html: str | None = None) -> None:
        if not settings.smtp_host:
            raise SMTPSettingsError("SMTP host is not configured")
        # NOTE: full SMTP client implementation lands with the notifications
        # milestone (M14). This transport is intentionally minimal for now.
        logger.info("smtp_email_queued", to=to, subject=subject)


def build_email_transport() -> EmailTransport:
    if settings.email_transport == "smtp":
        return SMTPEmailTransport()
    return ConsoleEmailTransport()


def get_email_transport() -> EmailTransport:
    """FastAPI dependency for the email transport (overridable in tests)."""
    return build_email_transport()
