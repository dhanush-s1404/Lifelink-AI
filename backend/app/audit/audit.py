from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.logging import logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

#: Absolute path to the audit log file. Override via the ``AUDIT_LOG_PATH``
#: environment variable or keep the default under the project directory.
DEFAULT_AUDIT_LOG = Path(__file__).resolve().parent.parent.parent / "audit" / "audit.log"


def _get_audit_log_path() -> Path:
    """Return the audit log path, respecting the ``AUDIT_LOG_PATH`` env var."""
    import os
    return Path(os.getenv("AUDIT_LOG_PATH", DEFAULT_AUDIT_LOG))


AUDIT_LOG_PATH = _get_audit_log_path()

#: Maximum number of entries to keep in the log file. Older entries are
#: truncated when the limit is exceeded.
AUDIT_MAX_ENTRIES = 100_000

#: Global lock so that concurrent requests do not write interleaved JSON.
_audit_lock = threading.Lock()

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _now_utc() -> str:
    """Return the current UTC time as an ISO‑8601 string."""
    return datetime.now(UTC).isoformat()


def _trim_log() -> None:
    """Remove oldest entries so that ``AUDIT_MAX_ENTRIES`` is never exceeded."""
    if not AUDIT_LOG_PATH.exists():
        return

    lines: list[str] = AUDIT_LOG_PATH.read_text().splitlines()
    if len(lines) <= AUDIT_MAX_ENTRIES:
        return

    # Keep the most recent entries
    trimmed = lines[-AUDIT_MAX_ENTRIES :]
    AUDIT_LOG_PATH.write_text("\n".join(trimmed), encoding="utf-8")


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def audit_action(
    *,
    actor: str,
    action: str,
    resource_type: str,
    resource_id: str,
    outcome: str,
    details: dict[str, Any] | None = None,
) -> None:
    """Emit a single audit entry.

    Parameters
    ----------
    actor:
        The identity of the actor (e.g. ``user.id``, ``service.name``).
    action:
        The name of the action that was performed (e.g. ``vault.read``,
        ``item.create``, ``emergency.activate``).
    resource_type:
        The type of resource affected (e.g. ``vault``, ``item``, ``document``,
        ``emergency``, ``contact``).
    resource_id:
        The persistent identifier of the resource affected.
    outcome:
        ``"success"`` or ``"failure"`` (or any application‑specific token).
    details:
        Optional free‑form dictionary with extra context (e.g. IP address,
        error code, item count).  *None* is equivalent to an empty dict.
    """
    entry: dict[str, Any] = {
        "timestamp": _now_utc(),
        "actor": actor,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "outcome": outcome,
        "details": details or {},
    }

    with _audit_lock:
        # Append the entry as a single JSON line.
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_LOG_PATH.open("a", encoding="utf-8").write(json.dumps(entry) + "\n")
        # Enforce the maximum size after every write.
        _trim_log()

    # Also emit a structured log line so that the application logger (Structured
    # Logging) can correlate the event with other request‑scoped data.
    logger.info(
        "audit_entry",
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome,
        details=json.dumps(entry["details"]),
    )


# ----------------------------------------------------------------------
# Convenient wrappers for the most common security‑sensitive operations
# ----------------------------------------------------------------------


def audit_vault_read(actor: str, vault_id: str, outcome: str = "success", **details: Any) -> None:
    """Audit a vault read operation."""
    audit_action(
        actor=actor,
        action="vault.read",
        resource_type="vault",
        resource_id=vault_id,
        outcome=outcome,
        details=details,
    )


def audit_vault_write(actor: str, vault_id: str, outcome: str = "success", **details: Any) -> None:
    """Audit a vault write/create/delete operation."""
    audit_action(
        actor=actor,
        action="vault.write",
        resource_type="vault",
        resource_id=vault_id,
        outcome=outcome,
        details=details,
    )


def audit_item_read(actor: str, item_id: str, outcome: str = "success", **details: Any) -> None:
    """Audit an item read operation."""
    audit_action(
        actor=actor,
        action="item.read",
        resource_type="item",
        resource_id=item_id,
        outcome=outcome,
        details=details,
    )


def audit_item_write(actor: str, item_id: str, outcome: str = "success", **details: Any) -> None:
    """Audit an item create/update/delete operation."""
    audit_action(
        actor=actor,
        action="item.write",
        resource_type="item",
        resource_id=item_id,
        outcome=outcome,
        details=details,
    )


def audit_document_upload(actor: str, document_id: str, outcome: str = "success", **details: Any) -> None:
    """Audit a document upload operation."""
    audit_action(
        actor=actor,
        action="document.upload",
        resource_type="document",
        resource_id=document_id,
        outcome=outcome,
        details=details,
    )


def audit_document_download(actor: str, document_id: str, outcome: str = "success", **details: Any) -> None:
    """Audit a document download operation."""
    audit_action(
        actor=actor,
        action="document.download",
        resource_type="document",
        resource_id=document_id,
        outcome=outcome,
        details=details,
    )


def audit_emergency_activate(actor: str, emergency_id: str, outcome: str = "success", **details: Any) -> None:
    """Audit an emergency activation operation."""
    audit_action(
        actor=actor,
        action="emergency.activate",
        resource_type="emergency",
        resource_id=emergency_id,
        outcome=outcome,
        details=details,
    )


def audit_emergency_release(actor: str, emergency_id: str, outcome: str = "success", **details: Any) -> None:
    """Audit an emergency release/vault access operation."""
    audit_action(
        actor=actor,
        action="emergency.release",
        resource_type="emergency",
        resource_id=emergency_id,
        outcome=outcome,
        details=details,
    )


def audit_contact_invite(actor: str, contact_id: str, outcome: str = "success", **details: Any) -> None:
    """Audit a contact invitation operation."""
    audit_action(
        actor=actor,
        action="contact.invite",
        resource_type="contact",
        resource_id=contact_id,
        outcome=outcome,
        details=details,
    )


def audit_contact_accept(actor: str, contact_id: str, outcome: str = "success", **details: Any) -> None:
    """Audit a contact acceptance operation."""
    audit_action(
        actor=actor,
        action="contact.accept",
        resource_type="contact",
        resource_id=contact_id,
        outcome=outcome,
        details=details,
    )