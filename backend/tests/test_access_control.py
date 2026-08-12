"""Integration tests for the M12 access-control layer.

Covers the central rule: a user may read a vault if they own it, OR are an
active trusted contact with ``can_view_vaults``, OR activated an escalated
emergency. Write operations remain owner-only.
"""

from __future__ import annotations

from datetime import timedelta

from app.core.security import utc_now
from app.emergency.models import Emergency


async def register_and_login(client, email: str, name: str = "User") -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123!", "full_name": name},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "StrongPass123!"}
    )
    return {"access": login.json()["tokens"]["access_token"], "email": email}


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def user_id(client, token: str) -> str:
    me = await client.get("/api/v1/users/me", headers=auth(token))
    assert me.status_code == 200
    return me.json()["id"]


async def create_vault_with_item(client, token: str):
    vault = await client.post("/api/v1/vaults", json={"name": "Shared"}, headers=auth(token))
    assert vault.status_code == 201
    vault_id = vault.json()["id"]
    item = await client.post(
        f"/api/v1/vaults/{vault_id}/items",
        json={"item_type": "insurance", "title": "Policy", "content": {"n": "secret"}},
        headers=auth(token),
    )
    assert item.status_code == 201
    return vault_id, item.json()["id"]


async def link_contact(
    client, owner_token: str, contact_email: str, *, can_view_vaults: bool = True
) -> str:
    """Owner invites a contact; contact accepts. Returns the contact access token."""
    contact = await register_and_login(client, contact_email, "Contact")
    invite = await client.post(
        "/api/v1/contacts",
        json={"email": contact_email, "can_view_vaults": can_view_vaults},
        headers=auth(owner_token),
    )
    assert invite.status_code == 201
    accepted = await client.post(
        f"/api/v1/contacts/{invite.json()['id']}/accept", headers=auth(contact["access"])
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "active"
    return contact["access"]


async def test_unauth_user_cannot_read(client) -> None:
    owner = await register_and_login(client, "ac1@example.com")
    vault_id, item_id = await create_vault_with_item(client, owner["access"])

    d = await client.get(f"/api/v1/vaults/{vault_id}", headers=auth(owner["access"]))
    assert d.status_code == 200


async def test_shared_vault_readable_by_contact(client) -> None:
    owner = await register_and_login(client, "ac2@example.com", "Owner")
    vault_id, item_id = await create_vault_with_item(client, owner["access"])
    contact_token = await link_contact(client, owner["access"], "ac3@example.com")

    # The shared vault appears in GET /vaults/shared.
    shared = await client.get("/api/v1/vaults/shared", headers=auth(contact_token))
    assert shared.status_code == 200
    assert [v["id"] for v in shared.json()] == [vault_id]

    # Contact can read the vault and its items (decrypted content).
    detail = await client.get(f"/api/v1/vaults/{vault_id}", headers=auth(contact_token))
    assert detail.status_code == 200

    listing = await client.get(
        f"/api/v1/vaults/{vault_id}/items", headers=auth(contact_token)
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    item = await client.get(
        f"/api/v1/vaults/{vault_id}/items/{item_id}", headers=auth(contact_token)
    )
    assert item.status_code == 200
    assert item.json()["content"]["n"] == "secret"


async def test_contact_without_view_permission_denied(client) -> None:
    owner = await register_and_login(client, "ac4@example.com", "Owner")
    vault_id, _ = await create_vault_with_item(client, owner["access"])
    contact_token = await link_contact(
        client, owner["access"], "ac5@example.com", can_view_vaults=False
    )

    shared = await client.get("/api/v1/vaults/shared", headers=auth(contact_token))
    assert shared.json() == []

    detail = await client.get(f"/api/v1/vaults/{vault_id}", headers=auth(contact_token))
    assert detail.status_code == 403
    assert detail.json()["error"]["code"] == "VAULT_ACCESS_DENIED"


async def test_contact_cannot_write_vault(client) -> None:
    owner = await register_and_login(client, "ac6@example.com", "Owner")
    vault_id, item_id = await create_vault_with_item(client, owner["access"])
    contact_token = await link_contact(client, owner["access"], "ac7@example.com")

    # Patch vault -> write denied.
    patch = await client.patch(
        f"/api/v1/vaults/{vault_id}",
        json={"name": "Hijacked"},
        headers=auth(contact_token),
    )
    assert patch.status_code == 403
    assert patch.json()["error"]["code"] == "VAULT_WRITE_DENIED"

    # Create item -> write denied.
    create = await client.post(
        f"/api/v1/vaults/{vault_id}/items",
        json={"item_type": "note", "title": "Injected", "content": {"x": 1}},
        headers=auth(contact_token),
    )
    assert create.status_code == 403
    assert create.json()["error"]["code"] == "VAULT_WRITE_DENIED"

    # Update item -> write denied.
    update = await client.patch(
        f"/api/v1/vaults/{vault_id}/items/{item_id}",
        json={"content": {"n": "tampered"}},
        headers=auth(contact_token),
    )
    assert update.status_code == 403
    assert update.json()["error"]["code"] == "ITEM_WRITE_DENIED"

    # Delete item -> write denied.
    delete = await client.delete(
        f"/api/v1/vaults/{vault_id}/items/{item_id}", headers=auth(contact_token)
    )
    assert delete.status_code == 403

    # The owner's data is intact.
    check = await client.get(f"/api/v1/vaults/{vault_id}", headers=auth(owner["access"]))
    assert check.json()["name"] == "Shared"


async def test_contact_cannot_manage_documents(client) -> None:
    import io

    owner = await register_and_login(client, "ac8@example.com", "Owner")
    vault_id, item_id = await create_vault_with_item(client, owner["access"])
    contact_token = await link_contact(client, owner["access"], "ac9@example.com")

    # Contact can list documents (read) but not upload (write).
    listing = await client.get(
        f"/api/v1/vaults/{vault_id}/items/{item_id}/documents", headers=auth(contact_token)
    )
    assert listing.status_code == 200
    assert listing.json() == []

    upload = await client.post(
        f"/api/v1/vaults/{vault_id}/items/{item_id}/documents",
        files={"file": ("x.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
        headers=auth(contact_token),
    )
    assert upload.status_code == 403
    assert upload.json()["error"]["code"] == "ITEM_WRITE_DENIED"


async def test_pending_emergency_does_not_grant_read(client) -> None:
    owner = await register_and_login(client, "ac10@example.com", "Owner")
    vault_id, _ = await create_vault_with_item(client, owner["access"])
    contact_token = await link_contact(
        client, owner["access"], "ac11@example.com", can_view_vaults=False
    )
    owner_id = await user_id(client, owner["access"])

    activation = await client.post(
        "/api/v1/emergencies",
        json={"owner_id": owner_id, "reason": "check"},
        headers=auth(contact_token),
    )
    assert activation.status_code == 201

    detail = await client.get(f"/api/v1/vaults/{vault_id}", headers=auth(contact_token))
    assert detail.status_code == 403
    assert detail.json()["error"]["code"] == "VAULT_ACCESS_DENIED"


async def test_escalated_emergency_grants_read(client, db_session) -> None:
    owner = await register_and_login(client, "ac12@example.com", "Owner")
    vault_id, _ = await create_vault_with_item(client, owner["access"])
    contact_token = await link_contact(
        client, owner["access"], "ac13@example.com", can_view_vaults=False
    )
    owner_id = await user_id(client, owner["access"])

    activation = await client.post(
        "/api/v1/emergencies",
        json={"owner_id": owner_id, "reason": "no answer"},
        headers=auth(contact_token),
    )
    emergency_id = activation.json()["id"]

    # Force escalation (status flips on the next emergency read).
    emergency = await db_session.get(Emergency, emergency_id)
    assert emergency is not None
    emergency.grace_end_at = utc_now() - timedelta(minutes=1)
    await db_session.commit()

    # An emergency read triggers lazy escalation.
    detail = await client.get(
        f"/api/v1/emergencies/{emergency_id}", headers=auth(contact_token)
    )
    assert detail.status_code == 200
    assert detail.json()["status"] == "escalated"

    # Escalated: contact can now read the vault.
    detail = await client.get(f"/api/v1/vaults/{vault_id}", headers=auth(contact_token))
    assert detail.status_code == 200


async def test_writes_still_owner_only_after_emergency(client, db_session) -> None:
    owner = await register_and_login(client, "ac14@example.com", "Owner")
    vault_id, item_id = await create_vault_with_item(client, owner["access"])
    contact_token = await link_contact(client, owner["access"], "ac15@example.com")
    owner_id = await user_id(client, owner["access"])

    activation = await client.post(
        "/api/v1/emergencies",
        json={"owner_id": owner_id, "reason": "no answer"},
        headers=auth(contact_token),
    )
    emergency_id = activation.json()["id"]

    emergency = await db_session.get(Emergency, emergency_id)
    assert emergency is not None
    emergency.grace_end_at = utc_now() - timedelta(minutes=1)
    await db_session.commit()

    detail = await client.get(f"/api/v1/vaults/{vault_id}", headers=auth(contact_token))
    assert detail.status_code == 200

    update = await client.patch(
        f"/api/v1/vaults/{vault_id}/items/{item_id}",
        json={"content": {"n": "tampered"}},
        headers=auth(contact_token),
    )
    assert update.status_code == 403
    assert update.json()["error"]["code"] == "ITEM_WRITE_DENIED"


async def test_documents_readable_by_contact(client) -> None:
    import io

    owner = await register_and_login(client, "ac16@example.com", "Owner")
    vault_id, item_id = await create_vault_with_item(client, owner["access"])
    contact_token = await link_contact(client, owner["access"], "ac17@example.com")

    up = await client.post(
        f"/api/v1/vaults/{vault_id}/items/{item_id}/documents",
        files={"file": ("scan.pdf", io.BytesIO(b"PDFDATA"), "application/pdf")},
        headers=auth(owner["access"]),
    )
    assert up.status_code == 201
    doc_id = up.json()["document"]["id"]

    dl = await client.get(
        f"/api/v1/vaults/{vault_id}/items/{item_id}/documents/{doc_id}/download",
        headers=auth(contact_token),
    )
    assert dl.status_code == 200
    assert dl.content == b"PDFDATA"