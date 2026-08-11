"""Integration tests for the emergency workflow."""

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


async def make_active_contact(client, owner_token: str, contact_email: str) -> str:
    """Owner (already logged in) invites contact; contact accepts. Returns contact access token."""
    contact = await register_and_login(client, contact_email, "Contact")

    invite = await client.post(
        "/api/v1/contacts",
        json={"email": contact_email, "access_grace_days": 1},
        headers=auth(owner_token),
    )
    assert invite.status_code == 201
    await client.post(
        f"/api/v1/contacts/{invite.json()['id']}/accept",
        headers=auth(contact["access"]),
    )
    return contact["access"]


async def activate(client, contact_token: str, owner_id: str, reason: str = "No response") -> dict:
    return await client.post(
        "/api/v1/emergencies",
        json={"owner_id": owner_id, "reason": reason},
        headers=auth(contact_token),
    )


async def test_activation_requires_active_contact(client) -> None:
    owner = await register_and_login(client, "em1@example.com", "Owner")
    stranger = await register_and_login(client, "em2@example.com", "Stranger")
    owner_id = await user_id(client, owner["access"])

    resp = await activate(client, stranger["access"], owner_id)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "EMERGENCY_ACCESS_DENIED"


async def test_cannot_raise_emergency_for_self(client) -> None:
    me = await register_and_login(client, "em3@example.com", "Me")
    me_id = await user_id(client, me["access"])

    resp = await activate(client, me["access"], me_id)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "SELF_EMERGENCY"


async def test_activate_creates_pending_emergency(client) -> None:
    owner = await register_and_login(client, "em5@example.com", "Owner")
    contact_token = await make_active_contact(client, owner["access"], "em7@example.com")
    owner_id = await user_id(client, owner["access"])

    resp = await activate(client, contact_token, owner_id, "Please check in")
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "pending"
    assert body["reason"] == "Please check in"
    assert body["contact_name"] == "Contact"


async def test_duplicate_active_emergency_conflict(client) -> None:
    owner = await register_and_login(client, "em8@example.com", "Owner")
    contact_token = await make_active_contact(client, owner["access"], "em10@example.com")
    owner_id = await user_id(client, owner["access"])

    assert (await activate(client, contact_token, owner_id)).status_code == 201
    resp = await activate(client, contact_token, owner_id)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "EMERGENCY_ALREADY_ACTIVE"


async def test_list_and_release_flow(client, db_session) -> None:
    owner = await register_and_login(client, "em11@example.com", "Owner")
    contact_token = await make_active_contact(client, owner["access"], "em13@example.com")
    owner_id = await user_id(client, owner["access"])

    resp = await activate(client, contact_token, owner_id, "Please check in")
    assert resp.status_code == 201
    emergency_id = resp.json()["id"]

    # Owner sees it under /emergencies, contact under /activated.
    as_owner = await client.get("/api/v1/emergencies", headers=auth(owner["access"]))
    assert as_owner.status_code == 200
    assert len(as_owner.json()) == 1
    assert as_owner.json()[0]["status"] == "pending"

    activated = await client.get("/api/v1/emergencies/activated", headers=auth(contact_token))
    assert activated.status_code == 200
    assert len(activated.json()) == 1

    # Vault release is forbidden before escalation.
    before = await client.get(
        f"/api/v1/emergencies/{emergency_id}/release", headers=auth(contact_token)
    )
    assert before.status_code == 403
    assert before.json()["error"]["code"] == "EMERGENCY_NOT_ESCALATED"

    # Force escalation by pushing grace_end_at into the past via the test session.
    emergency = await db_session.get(Emergency, emergency_id)
    assert emergency is not None
    emergency.grace_end_at = utc_now() - timedelta(minutes=1)
    await db_session.commit()

    # Reading triggers lazy escalation.
    detail = await client.get(f"/api/v1/emergencies/{emergency_id}", headers=auth(contact_token))
    assert detail.status_code == 200
    assert detail.json()["status"] == "escalated"

    release = await client.get(
        f"/api/v1/emergencies/{emergency_id}/release", headers=auth(contact_token)
    )
    assert release.status_code == 200


async def test_confirm_resolves_emergency(client) -> None:
    owner = await register_and_login(client, "em14@example.com", "Owner")
    contact_token = await make_active_contact(client, owner["access"], "em16@example.com")
    owner_id = await user_id(client, owner["access"])

    resp = await activate(client, contact_token, owner_id)
    emergency_id = resp.json()["id"]

    confirmed = await client.post(
        f"/api/v1/emergencies/{emergency_id}/confirm", headers=auth(owner["access"])
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "resolved"

    # Contact cannot release after resolution.
    release = await client.get(
        f"/api/v1/emergencies/{emergency_id}/release", headers=auth(contact_token)
    )
    assert release.status_code == 403
    assert release.json()["error"]["code"] == "EMERGENCY_NOT_ESCALATED"


async def test_cancel_emergency(client) -> None:
    owner = await register_and_login(client, "em17@example.com", "Owner")
    contact_token = await make_active_contact(client, owner["access"], "em19@example.com")
    owner_id = await user_id(client, owner["access"])

    resp = await activate(client, contact_token, owner_id)
    emergency_id = resp.json()["id"]

    cancelled = await client.post(
        f"/api/v1/emergencies/{emergency_id}/cancel", headers=auth(owner["access"])
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


async def test_only_participants_can_view(client) -> None:
    owner = await register_and_login(client, "em20@example.com", "Owner")
    contact_token = await make_active_contact(client, owner["access"], "em22@example.com")
    outsider = await register_and_login(client, "em23@example.com", "Outsider")
    owner_id = await user_id(client, owner["access"])

    resp = await activate(client, contact_token, owner_id)
    emergency_id = resp.json()["id"]

    detail = await client.get(
        f"/api/v1/emergencies/{emergency_id}", headers=auth(outsider["access"])
    )
    assert detail.status_code == 403
    assert detail.json()["error"]["code"] == "EMERGENCY_ACCESS_DENIED"


async def test_dashboard_counts_pending_emergency(client) -> None:
    owner = await register_and_login(client, "em24@example.com", "Owner")
    contact_token = await make_active_contact(client, owner["access"], "em26@example.com")
    owner_id = await user_id(client, owner["access"])

    summary = await client.get("/api/v1/dashboard/summary", headers=auth(owner["access"]))
    assert summary.json()["pending_emergencies_count"] == 0

    await activate(client, contact_token, owner_id)
    summary = await client.get("/api/v1/dashboard/summary", headers=auth(owner["access"]))
    assert summary.json()["pending_emergencies_count"] == 1
