"""E2E tests for access control enforcement across all operations.

Uses the real HTTP API: owner vs trusted contact (with/without read grant)
vs stranger, including the escalated-emergency read grant.
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
        "/api/v1/vaults", json={"name": "Access Test"}, headers=auth(token),
    )
    assert vault.status_code == 201
    vault_id = vault.json()["id"]

    item = await client.post(
        f"/api/v1/vaults/{vault_id}/items",
        json={"item_type": "document", "title": "Sensitive", "content": {"notes": "x"}},
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


async def test_access_control_full_enforcement(client) -> None:
    """Owner full access, trusted contact read-only, stranger fully denied."""
    owner = await e2e_auth(client, "owner@example.com")
    contact = await make_active_contact(client, owner["access"], "contact@example.com")
    stranger = await e2e_auth(client, "stranger@example.com")
    ctx = await setup_vault_with_document(client, owner["access"])

    # === OWNER OPERATIONS (all succeed) ===
    assert (
        await client.post(
            f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents",
            files={"file": ("extra.pdf", b"EXTRA", "application/pdf")},
            headers=auth(owner["access"]),
        )
    ).status_code == 201
    assert (
        await client.get(
            f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents",
            headers=auth(owner["access"]),
        )
    ).status_code == 200
    assert (
        await client.get(
            f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents/{ctx['doc_id']}/download",
            headers=auth(owner["access"]),
        )
    ).status_code == 200
    assert (
        await client.delete(
            f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents/{ctx['doc_id']}",
            headers=auth(owner["access"]),
        )
    ).status_code == 204

    # Re-upload a document so contacts/strangers have something to probe.
    doc = await client.post(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents",
        files={"file": ("secret.pdf", b"SECRET-PDF", "application/pdf")},
        headers=auth(owner["access"]),
    )
    assert doc.status_code == 201
    doc_id = doc.json()["document"]["id"]

    # === CONTACT OPERATIONS (read allowed, write denied) ===
    assert (
        await client.get(
            f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents",
            headers=auth(contact),
        )
    ).status_code == 200
    assert (
        await client.get(
            f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents/{doc_id}/download",
            headers=auth(contact),
        )
    ).status_code == 200
    upload = await client.post(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents",
        files={"file": ("test.pdf", b"x", "application/pdf")},
        headers=auth(contact),
    )
    assert upload.status_code == 403
    deleted = await client.delete(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents/{doc_id}",
        headers=auth(contact),
    )
    assert deleted.status_code == 403

    # === STRANGER OPERATIONS (all denied) ===
    listing = await client.get(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents",
        headers=auth(stranger["access"]),
    )
    assert listing.status_code == 403
    upload = await client.post(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents",
        files={"file": ("test.pdf", b"x", "application/pdf")},
        headers=auth(stranger["access"]),
    )
    assert upload.status_code == 403
    download = await client.get(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents/{doc_id}/download",
        headers=auth(stranger["access"]),
    )
    assert download.status_code == 403
    deleted = await client.delete(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents/{doc_id}",
        headers=auth(stranger["access"]),
    )
    assert deleted.status_code == 403


async def test_access_control_emergency_bypass(client, db_session) -> None:
    """Escalated emergency grants read access to the activating contact."""
    owner = await e2e_auth(client, "owner@example.com")
    # Contact WITHOUT the can_view_vaults grant -> no ordinary read access.
    contact = await make_active_contact(
        client, owner["access"], "contact@example.com", can_view_vaults=False
    )
    owner_id = await user_id(client, owner["access"])
    ctx = await setup_vault_with_document(client, owner["access"])

    # Before emergency: contact denied.
    denied = await client.get(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents/{ctx['doc_id']}/download",
        headers=auth(contact),
    )
    assert denied.status_code == 403

    # Contact activates an emergency.
    emergency = await client.post(
        "/api/v1/emergencies",
        json={"owner_id": owner_id, "reason": "Test"},
        headers=auth(contact),
    )
    assert emergency.status_code == 201
    emergency_id = emergency.json()["id"]

    # Still denied while pending.
    pending = await client.get(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents/{ctx['doc_id']}/download",
        headers=auth(contact),
    )
    assert pending.status_code == 403

    # Force escalation.
    emergency_row = await db_session.get(Emergency, emergency_id)
    assert emergency_row is not None
    emergency_row.grace_end_at = utc_now() - timedelta(minutes=1)
    await db_session.commit()

    # Reading the emergency detail lazily escalates it.
    detail = await client.get(f"/api/v1/emergencies/{emergency_id}", headers=auth(contact))
    assert detail.status_code == 200
    assert detail.json()["status"] == "escalated"

    # After escalation the activating contact can download.
    download = await client.get(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents/{ctx['doc_id']}/download",
        headers=auth(contact),
    )
    assert download.status_code == 200
    assert download.content == b"SECRET-PDF"
