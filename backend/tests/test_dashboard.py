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
