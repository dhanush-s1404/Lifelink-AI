"""E2E tests for vault lifecycle: create → item → document → download → delete."""

from __future__ import annotations

import pytest
import uuid

from tests.test_documents import auth, e2e_auth


pytestmark = pytest.mark.asyncio


async def test_full_vault_lifecycle(client) -> None:
    """Complete workflow: register → vault → item → document upload → download → delete."""
    # Register owner
    owner = await e2e_auth(client, "owner@example.com")
    other_owner = await e2e_auth(client, "otherowner@example.com")

    # Create vault
    vault = await client.post(
        "/api/v1/vaults",
        json={"name": "E2E Test Vault", "description": "Test vault for e2e"},
        headers=auth(owner["access"]),
    )
    assert vault.status_code == 201
    vault_id = vault.json()["id"]

    # Create item within vault
    item = await client.post(
        f"/api/v1/vaults/{vault_id}/items",
        json={"item_type": "document", "title": "My Documents", "content": {"notes": "x"}},
        headers=auth(owner["access"]),
    )
    assert item.status_code == 201
    item_id = item.json()["id"]

    # Upload a document
    doc_upload = await client.post(
        f"/api/v1/vaults/{vault_id}/items/{item_id}/documents",
        files={"file": ("will.txt", b"Test will content", "text/plain")},
        headers=auth(owner["access"]),
    )
    assert doc_upload.status_code == 201
    doc_id = doc_upload.json()["document"]["id"]

    # List documents
    listing = await client.get(
        f"/api/v1/vaults/{vault_id}/items/{item_id}/documents",
        headers=auth(owner["access"]),
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    # Download document
    download = await client.get(
        f"/api/v1/vaults/{vault_id}/items/{item_id}/documents/{doc_id}/download",
        headers=auth(owner["access"]),
    )
    assert download.status_code == 200
    assert download.content == b"Test will content"
    assert "attachment" in download.headers.get("content-disposition", "")

    # Delete document
    deleted = await client.delete(
        f"/api/v1/vaults/{vault_id}/items/{item_id}/documents/{doc_id}",
        headers=auth(owner["access"]),
    )
    assert deleted.status_code == 204

    # Verify document removed
    listing = await client.get(
        f"/api/v1/vaults/{vault_id}/items/{item_id}/documents",
        headers=auth(owner["access"]),
    )
    assert listing.json() == []

    # Other user cannot upload
    other_upload = await client.post(
        f"/api/v1/vaults/{vault_id}/items/{item_id}/documents",
        files={"file": ("malware.exe", b"MZ", "application/x-msdownload")},
        headers=auth(other_owner["access"]),
    )
    assert other_upload.status_code == 403
    assert other_upload.json()["error"]["code"] == "ITEM_ACCESS_DENIED"


async def test_vault_isolation_between_owners(client) -> None:
    """Two owners have separate vaults; cannot see each other's vaults."""
    owner1 = await e2e_auth(client, "owner1@example.com")
    owner2 = await e2e_auth(client, "owner2@example.com")

    # Owner 1 creates vault
    vault1 = await client.post(
        "/api/v1/vaults",
        json={"name": "Vault 1"},
        headers=auth(owner1["access"]),
    )
    assert vault1.status_code == 201
    vault1_id = vault1.json()["id"]

    # Owner 2 creates vault
    vault2 = await client.post(
        "/api/v1/vaults",
        json={"name": "Vault 2"},
        headers=auth(owner2["access"]),
    )
    assert vault2.status_code == 201
    vault2_id = vault2.json()["id"]

    # Owner 1 cannot see vault 2
    listing = await client.get("/api/v1/vaults", headers=auth(owner1["access"]))
    assert listing.status_code == 200
    vault_names = [v["name"] for v in listing.json()]
    assert "Vault 2" not in vault_names
    assert "Vault 1" in vault_names

    # Owner 2 cannot see vault 1
    listing = await client.get("/api/v1/vaults", headers=auth(owner2["access"]))
    assert listing.status_code == 200
    vault_names = [v["name"] for v in listing.json()]
    assert "Vault 1" not in vault_names
    assert "Vault 2" in vault_names


async def test_upload_denied_to_non_owner(client) -> None:
    """Non-owner users cannot upload documents to an item."""
    owner = await e2e_auth(client, "owner@example.com")
    other = await e2e_auth(client, "other@example.com")

    vault = await client.post(
        "/api/v1/vaults", json={"name": "Docs"}, headers=auth(owner["access"]),
    )
    assert vault.status_code == 201
    item = await client.post(
        f"/api/v1/vaults/{vault.json()['id']}/items",
        json={"item_type": "document", "title": "Paperwork", "content": {"note": "x"}},
        headers=auth(owner["access"]),
    )
    assert item.status_code == 201

    # Other user upload denied
    resp = await client.post(
        f"/api/v1/vaults/{vault.json()['id']}/items/{item.json()['id']}/documents",
        files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")},
        headers=auth(other["access"]),
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ITEM_ACCESS_DENIED"


async def test_download_denied_to_other_user(client) -> None:
    """Non-owner users cannot download documents."""
    owner = await e2e_auth(client, "owner@example.com")
    other = await e2e_auth(client, "other@example.com")

    vault = await client.post(
        "/api/v1/vaults", json={"name": "Docs"}, headers=auth(owner["access"]),
    )
    assert vault.status_code == 201
    item = await client.post(
        f"/api/v1/vaults/{vault.json()['id']}/items",
        json={"item_type": "document", "title": "Paperwork", "content": {"note": "x"}},
        headers=auth(owner["access"]),
    )
    assert item.status_code == 201

    # Upload a document first
    from io import BytesIO
    doc_upload = await client.post(
        f"/api/v1/vaults/{vault.json()['id']}/items/{item.json()['id']}/documents",
        files={"file": ("secret.pdf", b"SECRET-PDF", "application/pdf")},
        headers=auth(owner["access"]),
    )
    assert doc_upload.status_code == 201
    doc_id = doc_upload.json()["document"]["id"]

    # Other user download denied
    download = await client.get(
        f"/api/v1/vaults/{vault.json()['id']}/items/{item.json()['id']}/documents/{doc_id}/download",
        headers=auth(other["access"]),
    )
    assert download.status_code == 403
    assert download.json()["error"]["code"] == "ITEM_ACCESS_DENIED"