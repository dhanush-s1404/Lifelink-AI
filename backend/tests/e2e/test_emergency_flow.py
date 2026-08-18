"""E2E tests for the emergency flow: activation, contact participation, vault release.

These exercise the real HTTP API end-to-end: owner -> trusted contact ->
activation -> escalation -> vault release -> document download.
"""

from __future__ import annotations

from datetime import timedelta

from app.core.security import utc_now
from app.emergency.models import Emergency

from tests.test_documents import auth, e2e_auth


async def user_id(client, token: str) -> str:
    me = await client.get("/api/v1/users/me", headers=auth(token))
    assert me.status_code == 200
    return me.json()["id"]


async def make_active_contact(
    client, owner_token: str, contact_email: str, *, can_view_vaults: bool = True
) -> str:
    """Owner invites the contact and the contact accepts. Returns contact access token."""
    contact = await e2e_auth(client, contact_email)
    invite = await client.post(
        "/api/v1/contacts",
        json={
            "email": contact_email,
            "can_view_vaults": can_view_vaults,
            "can_activate_emergency": True,
            "access_grace_days": 1,
        },
        headers=auth(owner_token),
    )
    assert invite.status_code == 201
    accept = await client.post(
        f"/api/v1/contacts/{invite.json()['id']}/accept",
        headers=auth(contact["access"]),
    )
    assert accept.status_code == 200
    return contact["access"]


async def setup_vault_with_document(client, token: str) -> dict:
    from io import BytesIO

    vault = await client.post(
        "/api/v1/vaults", json={"name": "Test Vault"}, headers=auth(token),
    )
    assert vault.status_code == 201
    vault_id = vault.json()["id"]

    item = await client.post(
        f"/api/v1/vaults/{vault_id}/items",
        json={"item_type": "document", "title": "Important", "content": {"notes": "x"}},
        headers=auth(token),
    )
    assert item.status_code == 201
    item_id = item.json()["id"]

    doc = await client.post(
        f"/api/v1/vaults/{vault_id}/items/{item_id}/documents",
        files={"file": ("secret.pdf", BytesIO(b"SECRET-PDF"), "application/pdf")},
        headers=auth(token),
    )
    assert doc.status_code == 201
    doc_id = doc.json()["document"]["id"]
    return {"vault_id": vault_id, "item_id": item_id, "doc_id": doc_id}


async def test_emergency_activation_flow(client, db_session) -> None:
    """Full emergency lifecycle: activation -> escalation -> release -> read access."""
    owner = await e2e_auth(client, "owner@example.com")
    contact_token = await make_active_contact(
        client, owner["access"], "contact@example.com", can_view_vaults=False
    )
    owner_id = await user_id(client, owner["access"])
    ctx = await setup_vault_with_document(client, owner["access"])

    # Contact cannot read before any emergency is active.
    denied = await client.get(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents/{ctx['doc_id']}/download",
        headers=auth(contact_token),
    )
    assert denied.status_code == 403

    # Trusted contact raises an emergency for the owner.
    emergency = await client.post(
        "/api/v1/emergencies",
        json={"owner_id": owner_id, "reason": "Medical emergency"},
        headers=auth(contact_token),
    )
    assert emergency.status_code == 201
    emergency_id = emergency.json()["id"]

    # Owner sees the pending emergency.
    as_owner = await client.get("/api/v1/emergencies", headers=auth(owner["access"]))
    assert as_owner.status_code == 200
    assert as_owner.json()[0]["status"] == "pending"

    # Vault release is forbidden before the grace period elapses.
    before = await client.get(
        f"/api/v1/emergencies/{emergency_id}/release", headers=auth(contact_token)
    )
    assert before.status_code == 403
    assert before.json()["error"]["code"] == "EMERGENCY_NOT_ESCALATED"

    # Force escalation by pushing the grace deadline into the past.
    emergency_row = await db_session.get(Emergency, emergency_id)
    assert emergency_row is not None
    emergency_row.grace_end_at = utc_now() - timedelta(minutes=1)
    await db_session.commit()

    # Release now returns the owner's vault items to the activating contact.
    release = await client.get(
        f"/api/v1/emergencies/{emergency_id}/release", headers=auth(contact_token)
    )
    assert release.status_code == 200
    assert len(release.json()) == 1
    assert release.json()[0]["title"] == "Important"

    # Contact can now download the document.
    download = await client.get(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents/{ctx['doc_id']}/download",
        headers=auth(contact_token),
    )
    assert download.status_code == 200
    assert download.content == b"SECRET-PDF"


async def test_emergency_contact_no_read_without_flag(client) -> None:
    """A contact without the can_view_vaults flag cannot read vault items."""
    owner = await e2e_auth(client, "owner@example.com")
    contact_token = await make_active_contact(
        client, owner["access"], "contact_no_access@example.com", can_view_vaults=False
    )
    ctx = await setup_vault_with_document(client, owner["access"])

    download = await client.get(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents/{ctx['doc_id']}/download",
        headers=auth(contact_token),
    )
    assert download.status_code == 403
    assert download.json()["error"]["code"] == "ITEM_ACCESS_DENIED"


async def test_multiple_contacts_activation(client) -> None:
    """Multiple contacts can participate; only one active emergency per owner."""
    owner = await e2e_auth(client, "owner@example.com")
    contact1 = await make_active_contact(client, owner["access"], "contact1@example.com")
    contact2 = await make_active_contact(client, owner["access"], "contact2@example.com")
    owner_id = await user_id(client, owner["access"])

    # Contact 1 activates.
    emergency = await client.post(
        "/api/v1/emergencies",
        json={"owner_id": owner_id, "reason": "Test emergency"},
        headers=auth(contact1),
    )
    assert emergency.status_code == 201
    emergency_id = emergency.json()["id"]

    # Contact 2 trying to activate again conflicts.
    dup = await client.post(
        "/api/v1/emergencies",
        json={"owner_id": owner_id, "reason": "Second attempt"},
        headers=auth(contact2),
    )
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "EMERGENCY_ALREADY_ACTIVE"

    # The activating contact can view the emergency detail.
    status1 = await client.get(f"/api/v1/emergencies/{emergency_id}", headers=auth(contact1))
    assert status1.status_code == 200
    assert status1.json()["status"] == "pending"
