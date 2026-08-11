"""Authenticated encryption for vault content.

Uses AES-256-GCM with a 96-bit nonce. The key is derived from the configured
vault master key (environment-provided; KMS-backed in production). The threat
model is documented in docs/security/threat-model.md — this is NOT zero-knowledge:
an operator with the master key can decrypt.

Payload format: base64(nonce || ciphertext || tag).
"""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config.settings import settings
from app.core.exceptions import AppError

_NONCE_LEN = 12
_TAG_LEN = 16


class EncryptionError(AppError):
    code = "DECRYPTION_ERROR"
    status_code = 400


def _derive_key(master_key: str) -> bytes:
    """Derive a 32-byte AES key from the master key string."""
    return hashlib.sha256(master_key.encode("utf-8")).digest()


def encrypt(plaintext: str, *, key: str | None = None) -> str:
    """Encrypt plaintext with AES-256-GCM, returning a URL-safe string."""
    aad = None
    aesgcm = AESGCM(_derive_key(key or settings.vault_master_key))
    nonce = os.urandom(_NONCE_LEN)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), aad)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")


def decrypt(payload: str, *, key: str | None = None) -> str:
    """Decrypt an AES-256-GCM payload produced by :func:`encrypt`."""
    try:
        raw = base64.urlsafe_b64decode(payload.encode("ascii"))
        nonce, ciphertext = raw[:_NONCE_LEN], raw[_NONCE_LEN:]
        aesgcm = AESGCM(_derive_key(key or settings.vault_master_key))
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except (InvalidTag, ValueError, TypeError) as exc:
        raise EncryptionError("Unable to decrypt this value") from exc
    return plaintext.decode("utf-8")
