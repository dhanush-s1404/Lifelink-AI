# LifeLink AI Threat Model

## Assets

- User credentials (passwords, refresh tokens, sessions)
- Vault content (identity, financial, medical, legal, property data)
- Documents (files)
- Contact trust graph (who is allowed to access what)
- Audit logs
- Encryption keys

## Trust boundaries

1. **Browser / client** — untrusted, must validate and authorize everything server-side.
2. **API / application** — trusted application code; must never trust client input.
3. **Database / object storage** — vault content encrypted at rest with keys not co-located.
4. **AI provider** — treats AI as a remote party; never send secrets it doesn't need.
5. **Administrators** — never have automatic access to decrypted vault content.

## Adversaries & mitigations

| Adversary | Goal | Mitigation |
| --------- | ---- | ---------- |
| Unauthenticated attacker | Access another user's vault | AuthN (Argon2id, JWT), rate limiting, CORS |
| Authenticated attacker | Cross-user access / privilege escalation | Resource-level authorization, ownership checks, RBAC |
| Revoked/expired session holder | Continued access | Token rotation, revocation, session management |
| Data breach (DB) | Read plaintext vault data | AES-256-GCM encryption at rest, separate keys |
| Admin / operator | Read private vault content | Admin role scoped to system data only |
| AI provider | Steal secrets | Only send authorized, necessary context; no raw secrets |
| Phishing | Steal credentials | Email verification, security notifications |
| Malware upload | Execute/steal | MIME + extension validation, size limits, object storage |

## What we explicitly do NOT claim

- **Zero knowledge**: application holds the master key in its environment, so operators with
  key access could decrypt. We document this honestly and mitigate with key separation,
  KMS readiness, and minimal key exposure.
- **Perfect protection against a compromised server**: if an attacker controls the running
  application, they can use its keys.

## Security controls checklist

- [ ] Argon2id password hashing
- [ ] JWT access + rotating refresh tokens
- [ ] RBAC + resource-level authorization
- [ ] CORS allow-list, secure headers (Nginx)
- [ ] Input validation (Pydantic), request size limits
- [ ] Encrypted vault content at rest (AES-256-GCM)
- [ ] Safe file upload (MIME, extension, size, safe filenames)
- [ ] Comprehensive audit logging
- [ ] No secrets in logs or errors
