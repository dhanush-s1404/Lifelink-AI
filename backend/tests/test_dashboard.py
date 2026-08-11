"""Integration tests for the dashboard summary endpoint."""

from __future__ import annotations


async def register_and_login(client, email="dash@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123!", "full_name": "Dash"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "StrongPass123!"}
    )
    return login.json()["tokens"]["access_token"]


async def test_dashboard_summary_requires_auth(client) -> None:
    resp = await client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 401


async def test_dashboard_summary_returns_shape(client) -> None:
    access = await register_and_login(client)
    resp = await client.get(
        "/api/v1/dashboard/summary", headers={"Authorization": f"Bearer {access}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["vaults_count"] == 0
    assert body["items_count"] == 0
    assert body["trusted_contacts_count"] == 0
    assert body["pending_emergencies_count"] == 0
    assert "recent_activity" in body


async def test_dashboard_counts_vaults_and_items(client) -> None:
    access = await register_and_login(client, email="dash2@example.com")
    headers = {"Authorization": f"Bearer {access}"}

    vault = await client.post("/api/v1/vaults", json={"name": "Vault"}, headers=headers)
    assert vault.status_code == 201
    vault_id = vault.json()["id"]

    for title in ("Policy", "Note"):
        resp = await client.post(
            f"/api/v1/vaults/{vault_id}/items",
            json={"item_type": "note", "title": title, "content": {"v": title}},
            headers=headers,
        )
        assert resp.status_code == 201

    resp = await client.get("/api/v1/dashboard/summary", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["vaults_count"] == 1
    assert body["items_count"] == 2


async def test_dashboard_counts_active_contacts(client) -> None:
    owner = await register_and_login(client, email="dash3@example.com")
    await client.post(
        "/api/v1/auth/register",
        json={"email": "dash4@example.com", "password": "StrongPass123!", "full_name": "C"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": "dash4@example.com", "password": "StrongPass123!"}
    )
    contact_access = login.json()["tokens"]["access_token"]

    headers = {"Authorization": f"Bearer {owner}"}
    invite = await client.post(
        "/api/v1/contacts", json={"email": "dash4@example.com"}, headers=headers
    )
    assert invite.status_code == 201
    contact_id = invite.json()["id"]

    # Pending invitation should not count.
    summary = await client.get("/api/v1/dashboard/summary", headers=headers)
    assert summary.json()["trusted_contacts_count"] == 0

    await client.post(
        f"/api/v1/contacts/{contact_id}/accept",
        headers={"Authorization": f"Bearer {contact_access}"},
    )
    summary = await client.get("/api/v1/dashboard/summary", headers=headers)
    assert summary.json()["trusted_contacts_count"] == 1
