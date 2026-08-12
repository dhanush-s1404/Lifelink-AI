"""Integration tests for document storage on vault items."""

from __future__ import annotations

import io


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


async def setup_owner_with_item(client, email: str, other_email: str | None = None):
    """Register an owner, create a vault + item. Optionally register a second user."""
    owner = await register_and_login(client, email, "Owner")
    other = None
    if other_email:
        other = await register_and_login(client, other_email, "Other")

    vault = await client.post(
        "/api/v1/vaults", json={"name": "Docs"}, headers=auth(owner["access"])
    )
    assert vault.status_code == 201
    item = await client.post(
        f"/api/v1/vaults/{vault.json()['id']}/items",
        json={"item_type": "document", "title": "Paperwork", "content": {"note": "x"}},
        headers=auth(owner["access"]),
    )
    assert item.status_code == 201
    return {
        "owner": owner,
        "other": other,
        "vault_id": vault.json()["id"],
        "item_id": item.json()["id"],
    }


async def upload_document(client, token: str, vault_id: str, item_id: str, *, filename: str = "policy.pdf", content: bytes = b"%PDF-1.4 fake", content_type: str = "application/pdf"):
    return await client.post(
        f"/api/v1/vaults/{vault_id}/items/{item_id}/documents",
        files={"file": (filename, io.BytesIO(content), content_type)},
        headers=auth(token),
    )


async def test_upload_and_list_documents(client) -> None:
    ctx = await setup_owner_with_item(client, "doc1@example.com")

    resp = await upload_document(client, ctx["owner"]["access"], ctx["vault_id"], ctx["item_id"])
    assert resp.status_code == 201
    body = resp.json()
    assert body["document"]["original_filename"] == "policy.pdf"
    assert body["document"]["content_type"] == "application/pdf"
    assert body["document"]["size_bytes"] == len(b"%PDF-1.4 fake")

    listing = await client.get(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents",
        headers=auth(ctx["owner"]["access"]),
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1


async def test_upload_rejects_disallowed_type(client) -> None:
    ctx = await setup_owner_with_item(client, "doc2@example.com")
    resp = await upload_document(
        client, ctx["owner"]["access"], ctx["vault_id"], ctx["item_id"],
        filename="malware.exe", content=b"MZ", content_type="application/x-msdownload",
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "DOCUMENT_TYPE_NOT_ALLOWED"


async def test_upload_rejects_extension_mismatch(client) -> None:
    ctx = await setup_owner_with_item(client, "doc3@example.com")
    resp = await upload_document(
        client, ctx["owner"]["access"], ctx["vault_id"], ctx["item_id"],
        filename="notes.txt", content=b"hello", content_type="application/pdf",
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "DOCUMENT_EXTENSION_MISMATCH"


async def test_upload_denied_to_other_user(client) -> None:
    ctx = await setup_owner_with_item(client, "doc4@example.com", "doc5@example.com")
    assert ctx["other"] is not None
    resp = await upload_document(client, ctx["other"]["access"], ctx["vault_id"], ctx["item_id"])
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ITEM_ACCESS_DENIED"


async def test_download_and_delete_document(client) -> None:
    ctx = await setup_owner_with_item(client, "doc6@example.com")
    upload = await upload_document(client, ctx["owner"]["access"], ctx["vault_id"], ctx["item_id"], content=b"SECRET-PDF")
    doc_id = upload.json()["document"]["id"]

    download = await client.get(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents/{doc_id}/download",
        headers=auth(ctx["owner"]["access"]),
    )
    assert download.status_code == 200
    assert download.content == b"SECRET-PDF"
    assert "attachment" in download.headers.get("content-disposition", "")

    deleted = await client.delete(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents/{doc_id}",
        headers=auth(ctx["owner"]["access"]),
    )
    assert deleted.status_code == 204

    listing = await client.get(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents",
        headers=auth(ctx["owner"]["access"]),
    )
    assert listing.json() == []


async def test_delete_denied_to_other_user(client) -> None:
    ctx = await setup_owner_with_item(client, "doc7@example.com", "doc8@example.com")
    upload = await upload_document(client, ctx["owner"]["access"], ctx["vault_id"], ctx["item_id"])
    doc_id = upload.json()["document"]["id"]

    assert ctx["other"] is not None
    resp = await client.delete(
        f"/api/v1/vaults/{ctx['vault_id']}/items/{ctx['item_id']}/documents/{doc_id}",
        headers=auth(ctx["other"]["access"]),
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ITEM_ACCESS_DENIED"


async def test_documents_require_auth(client) -> None:
    resp = await client.get(
        "/api/v1/vaults/00000000-0000-0000-0000-000000000000/items/00000000-0000-0000-0000-000000000000/documents"
    )
    assert resp.status_code == 401
