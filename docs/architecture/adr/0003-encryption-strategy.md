# ADR-0003: Encryption Strategy

## Status

Accepted

## Context

LifeLink stores highly sensitive data. We separate two concerns: system security (authentication,
authorization, transport) and user vault security (encryption at rest of vault content).

## Decision

- Use authenticated encryption (AES-256-GCM) for vault item content before persistence.
- Keep encryption keys separate from encrypted data (env-injected master keys in development,
  KMS in production).
- Never claim "zero knowledge" — the master key is available to the application, so we are
  not zero-knowledge. Document the real threat model instead.
- Never store plaintext passwords; use Argon2id.
- Never log secrets, tokens, or decrypted vault content.

## Consequences

- Strong at-rest protection for vault data even if the database leaks.
- Honest threat model: operators with the master key can decrypt; document mitigations.
