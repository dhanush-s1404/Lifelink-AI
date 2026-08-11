"""Integration tests for the trusted contacts domain."""

from __future__ import annotations


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


async def invite(client, token: str, email: str, **overrides) -> dict:
    payload = {"email": email, **overrides}
    resp = await client.post("/api/v1/contacts", json=payload, headers=auth(token))
    return resp


async def test_invite_creates_pending_contact(client) -> None:
    owner = await register_and_login(client, "co@example.com", "Owner")
    contact = await register_and_login(client, "cc@example.com", "Contact")

    resp = await invite(client, owner["access"], contact["email"])
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "pending"
    assert body["contact_email"] == contact["email"]
    assert body["contact_name"] == "Contact"
    assert body["can_activate_emergency"] is True
    assert body["can_view_vaults"] is True
    assert body["access_grace_days"] == 30


async def test_invite_user_not_found(client) -> None:
    owner = await register_and_login(client, "nf@example.com")
    resp = await invite(client, owner["access"], "ghost@example.com")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "CONTACT_USER_NOT_FOUND"


async def test_invite_self_rejected(client) -> None:
    owner = await register_and_login(client, "self@example.com")
    resp = await invite(client, owner["access"], owner["email"])
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "CANNOT_CONTACT_SELF"


async def test_duplicate_invite_conflict(client) -> None:
    owner = await register_and_login(client, "dup1@example.com")
    contact = await register_and_login(client, "dup2@example.com")
    assert (await invite(client, owner["access"], contact["email"])).status_code == 201
    resp = await invite(client, owner["access"], contact["email"])
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONTACT_EXISTS"


async def test_accept_activates_contact(client) -> None:
    owner = await register_and_login(client, "ac1@example.com", "Owner")
    contact = await register_and_login(client, "ac2@example.com", "Contact")
    pending = (await invite(client, owner["access"], contact["email"])).json()

    incoming = await client.get("/api/v1/contacts/incoming", headers=auth(contact["access"]))
    assert incoming.status_code == 200
    assert len(incoming.json()) == 1
    assert incoming.json()[0]["status"] == "pending"

    accepted = await client.post(
        f"/api/v1/contacts/{pending['id']}/accept", headers=auth(contact["access"])
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "active"

    owned = await client.get("/api/v1/contacts", headers=auth(owner["access"]))
    assert owned.status_code == 200
    assert owned.json()[0]["status"] == "active"


async def test_accept_requires_invited_user(client) -> None:
    owner = await register_and_login(client, "ap1@example.com")
    contact = await register_and_login(client, "ap2@example.com")
    stranger = await register_and_login(client, "ap3@example.com")
    pending = (await invite(client, owner["access"], contact["email"])).json()

    resp = await client.post(
        f"/api/v1/contacts/{pending['id']}/accept", headers=auth(stranger["access"])
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "CONTACT_ACCESS_DENIED"


async def test_decline_removes_request(client) -> None:
    owner = await register_and_login(client, "dc1@example.com")
    contact = await register_and_login(client, "dc2@example.com")
    pending = (await invite(client, owner["access"], contact["email"])).json()

    resp = await client.post(
        f"/api/v1/contacts/{pending['id']}/decline", headers=auth(contact["access"])
    )
    assert resp.status_code == 204

    owned = await client.get("/api/v1/contacts", headers=auth(owner["access"]))
    assert owned.json() == []


async def test_remove_by_owner(client) -> None:
    owner = await register_and_login(client, "rm1@example.com")
    contact = await register_and_login(client, "rm2@example.com")
    pending = (await invite(client, owner["access"], contact["email"])).json()

    resp = await client.delete(f"/api/v1/contacts/{pending['id']}", headers=auth(owner["access"]))
    assert resp.status_code == 204

    owned = await client.get("/api/v1/contacts", headers=auth(owner["access"]))
    assert owned.json() == []


async def test_remove_requires_owner(client) -> None:
    owner = await register_and_login(client, "ro1@example.com")
    contact = await register_and_login(client, "ro2@example.com")
    pending = (await invite(client, owner["access"], contact["email"])).json()

    resp = await client.delete(f"/api/v1/contacts/{pending['id']}", headers=auth(contact["access"]))
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "CONTACT_ACCESS_DENIED"


async def test_update_permissions_by_owner(client) -> None:
    owner = await register_and_login(client, "up1@example.com")
    contact = await register_and_login(client, "up2@example.com")
    pending = (await invite(client, owner["access"], contact["email"])).json()

    resp = await client.patch(
        f"/api/v1/contacts/{pending['id']}",
        json={"can_activate_emergency": False, "access_grace_days": 7},
        headers=auth(owner["access"]),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["can_activate_emergency"] is False
    assert body["access_grace_days"] == 7


async def test_contacts_require_auth(client) -> None:
    assert (await client.get("/api/v1/contacts")).status_code == 401
    assert (await client.post("/api/v1/contacts", json={"email": "x@y.z"})).status_code == 401
