# Access Control

LifeLink AI grants access to vault resources through a single, centralized
`AccessControlService` (`backend/app/access_control/`). Every vault, item and
document read/write is checked against the same rules — no ad-hoc ownership
checks scattered across domains.

## Grant sources

For a given user and vault, access is computed in order:

1. **Owner** — the user owns the vault → **write** access (read + modify).
2. **Trusted contact** — an *active* trust link exists and the owner granted the
   contact `can_view_vaults` → **read-only** access.
3. **Escalated emergency** — the user activated an emergency for the owner that
   has escalated (grace period elapsed without owner response) → **read-only**
   access. This is the emergency release path surfaced through normal reads.

Anything else is `none` and every read/write endpoint returns `403`.

## Access levels

| Level   | Can read vault / items / documents | Can create / update / delete |
| ------- | ---------------------------------- | ---------------------------- |
| `WRITE` | Yes                                | Yes (owner only)             |
| `READ`  | Yes                                | No                           |
| `NONE`  | No                                 | No                           |

## Error codes

| Code                    | Meaning                                      |
| ----------------------- | -------------------------------------------- |
| `VAULT_ACCESS_DENIED`   | User cannot read the vault (vault not owned, no grant) |
| `VAULT_WRITE_DENIED`    | User can read but only the owner may modify  |
| `ITEM_ACCESS_DENIED`    | User cannot read the item                    |
| `ITEM_WRITE_DENIED`     | User can read but only the owner may modify the item |

Writes to a shared vault are rejected with `*_WRITE_DENIED`, which is distinct
from `*_ACCESS_DENIED` so clients can show "read-only" vs "no access".

## API surface

- `GET /api/v1/vaults` — vaults the user owns.
- `GET /api/v1/vaults/shared` — vaults the user may read via trust grants.
- Existing `GET` item/document endpoints already enforce read level; existing
  `POST/PATCH/DELETE` endpoints enforce write (owner-only).

## Toggling grants

Owners switch a contact's `can_view_vaults` permission through
`PATCH /api/v1/contacts/{id}`. Revoking the flag immediately removes read
access (unless an escalated emergency is active).

See also: [Threat model](../security/threat-model.md), which documents
"authenticated attacker / privilege escalation" mitigations.