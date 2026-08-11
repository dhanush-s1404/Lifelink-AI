"""Integration tests for the vault domain, including security tests."""

from __future__ import annotations

import json

from sqlalchemy import select

from app.vault.encryption import decrypt, encrypt
from app.vault.models import VaultItem


async def make_user(client, email: str, name: str = "User") -> dict:
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


async def create_vault(client, token: str, name: str = "My Vault") -> dict:
    resp = await client.post(
        "/api/v1/vaults", json={"name": name, "description": "desc"}, headers=auth(token)
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def create_category(client, token: str, vault_id: str, name: str) -> dict:
    resp = await client.post(
        f"/api/v1/vaults/{vault_id}/categories",
        json={"name": name},
        headers=auth(token),
    )
    assert resp.status_code == 201
    return resp.json()


async def create_item(client, token: str, vault_id: str, **overrides) -> dict:
    payload = {
        "item_type": "insurance",
        "title": "Life Insurance Policy",
        "content": {"policy_number": "POL-123", "notes": "secret details"},
        "masked_summary": "Life insurance policy",
        **overrides,
    }
    resp = await client.post(f"/api/v1/vaults/{vault_id}/items", json=payload, headers=auth(token))
    assert resp.status_code == 201, resp.text
    return resp.json()


# --------------------------------------------------------------------------- vaults


async def test_vault_crud(client) -> None:
    u = await make_user(client, "vault@example.com")
    vault = await create_vault(client, u["access"])

    listing = await client.get("/api/v1/vaults", headers=auth(u["access"]))
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    detail = await client.get(f"/api/v1/vaults/{vault['id']}", headers=auth(u["access"]))
    assert detail.status_code == 200
    assert detail.json()["name"] == "My Vault"

    updated = await client.patch(
        f"/api/v1/vaults/{vault['id']}",
        json={"name": "Renamed"},
        headers=auth(u["access"]),
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Renamed"

    deleted = await client.delete(f"/api/v1/vaults/{vault['id']}", headers=auth(u["access"]))
    assert deleted.status_code == 204
    listing = await client.get("/api/v1/vaults", headers=auth(u["access"]))
    assert len(listing.json()) == 0


async def test_vault_access_denied_to_other_user(client) -> None:
    owner = await make_user(client, "owner@example.com")
    intruder = await make_user(client, "intruder@example.com")
    vault = await create_vault(client, owner["access"])

    resp = await client.get(f"/api/v1/vaults/{vault['id']}", headers=auth(intruder["access"]))
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "VAULT_ACCESS_DENIED"


async def test_vault_not_found(client) -> None:
    u = await make_user(client, "nobody@example.com")
    resp = await client.get(
        "/api/v1/vaults/00000000-0000-0000-0000-000000000000",
        headers=auth(u["access"]),
    )
    assert resp.status_code == 404


# --------------------------------------------------------------------------- items


async def test_item_crud_and_encryption(client) -> None:
    u = await make_user(client, "items@example.com")
    vault = await create_vault(client, u["access"])
    cat = await create_category(client, u["access"], vault["id"], "Insurance")

    item = await create_item(client, u["access"], vault["id"], category_id=cat["id"])
    assert item["item_type"] == "insurance"
    assert item["content"]["policy_number"] == "POL-123"

    # Fetch detail (decrypts on read for the owner).
    detail = await client.get(
        f"/api/v1/vaults/{vault['id']}/items/{item['id']}", headers=auth(u["access"])
    )
    assert detail.status_code == 200
    body = detail.json()
    assert body["content"]["policy_number"] == "POL-123"
    assert body["version"] == 1

    # Update content -> new version.
    updated = await client.patch(
        f"/api/v1/vaults/{vault['id']}/items/{item['id']}",
        json={"content": {"policy_number": "POL-999"}},
        headers=auth(u["access"]),
    )
    assert updated.status_code == 200
    assert updated.json()["content"]["policy_number"] == "POL-999"
    assert updated.json()["version"] == 2

    versions = await client.get(
        f"/api/v1/vaults/{vault['id']}/items/{item['id']}/versions",
        headers=auth(u["access"]),
    )
    assert versions.status_code == 200
    assert len(versions.json()) == 2


async def test_item_plaintext_not_stored(client, db_session) -> None:
    u = await make_user(client, "enc@example.com")
    vault = await create_vault(client, u["access"])
    await create_item(client, u["access"], vault["id"])

    stmt = select(VaultItem.content_encrypted).where(VaultItem.vault_id.isnot(None))
    rows = (await db_session.execute(stmt)).scalars().all()
    for payload in rows:
        assert "POL-123" not in payload
        assert "secret details" not in payload
        # Ensure it round-trips through decryption.
        decrypted = json.loads(decrypt(payload))
        assert decrypted["policy_number"] == "POL-123"


async def test_item_access_denied_to_other_user(client) -> None:
    owner = await make_user(client, "o2@example.com")
    intruder = await make_user(client, "i2@example.com")
    vault = await create_vault(client, owner["access"])
    item = await create_item(client, owner["access"], vault["id"])

    resp = await client.get(
        f"/api/v1/vaults/{vault['id']}/items/{item['id']}",
        headers=auth(intruder["access"]),
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ITEM_ACCESS_DENIED"


async def test_item_list_filters_by_type(client) -> None:
    u = await make_user(client, "filters@example.com")
    vault = await create_vault(client, u["access"])
    await create_item(client, u["access"], vault["id"], item_type="insurance")
    await create_item(client, u["access"], vault["id"], item_type="note", title="Quick note")

    listing = await client.get(
        f"/api/v1/vaults/{vault['id']}/items?item_type=note", headers=auth(u["access"])
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["title"] == "Quick note"


async def test_category_belongs_to_vault(client) -> None:
    u = await make_user(client, "cat@example.com")
    vault_a = await create_vault(client, u["access"], "Vault A")
    vault_b = await create_vault(client, u["access"], "Vault B")
    cat = await create_category(client, u["access"], vault_a["id"], "Legal")

    # Using vault B's id with vault A's category must fail.
    resp = await client.post(
        f"/api/v1/vaults/{vault_b['id']}/items",
        json={
            "item_type": "legal",
            "title": "Will",
            "content": {"x": 1},
            "category_id": cat["id"],
        },
        headers=auth(u["access"]),
    )
    assert resp.status_code == 404


async def test_encrypt_decrypt_roundtrip() -> None:
    payload = encrypt('{"policy": "XYZ"}')
    assert "XYZ" not in payload
    assert decrypt(payload) == '{"policy": "XYZ"}'


async def test_decrypt_tampered_payload_fails() -> None:
    from app.vault.encryption import EncryptionError

    payload = encrypt("secret")
    tampered = payload[:-4] + "AAAA"
    try:
        decrypt(tampered)
        raise AssertionError("expected EncryptionError")
    except EncryptionError:
        pass
