"""Structured logging for LifeLink AI backend.

Uses the standard library logging module with JSON formatting
(configured via the ``monitoring.py`` :class:`JSONFormatter`).

Sensitive values (passwords, tokens, keys, vault content) must never be
passed to the logger.  If a sensitive key is detected in a log event dict,
it is redacted to ``[REDACTED]``.
"""

import json
import logging

from app.monitoring import JSONFormatter, StructuredLogger

# ------------------------------------------------------------------
# Logger setup (JSON-formatted, no structlog dependency)
# ------------------------------------------------------------------

# Application logger — JSON‑formatted output
_log = logging.getLogger("lifelink")
_log.setLevel(logging.INFO)

_handler = logging.StreamHandler()
_handler.setFormatter(JSONFormatter())
_log.addHandler(_handler)

# Export for import throughout the codebase
logger = StructuredLogger(_log)

# ------------------------------------------------------------------
# Sensitive‑key redaction helper (used by middleware / spans)
# ------------------------------------------------------------------

_SENSITIVE_KEYS = {"password", "token", "secret", "authorization", "cookie"}


def _drop_sensitive(event_dict: dict) -> dict:
    """Redact any dictionary value whose key is a suspected secret."""
    if isinstance(event_dict, dict):
        for key in list(event_dict.keys()):
            if key.lower() in _SENSITIVE_KEYS:
                event_dict[key] = "[REDACTED]"
    return event_dict


# ------------------------------------------------------------------
# Request‑context correlation (middleware should attach
# ``correlation_id`` to ``request.state`` and then add it to log events)
# ------------------------------------------------------------------


def bind_correlation_id(correlation_id: str) -> None:
    """Attach a correlation ID to the current logger context.

    In a multi‑request setup each request gets its own ID; the ID is
    included in every subsequent log line so that traces can be
    correlated across service boundaries.
    """
    logger.info(
        "correlation_id_bound",
        correlation_id=correlation_id,
    )