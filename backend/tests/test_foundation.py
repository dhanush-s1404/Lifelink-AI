from fastapi.testclient import TestClient

from app.main import app


def test_ping_under_api_prefix() -> None:
    with TestClient(app) as client:
        resp = client.get("/api/v1/ping")
    assert resp.status_code == 200
    assert resp.json() == {"status": "pong"}


def test_security_headers_set() -> None:
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"


def test_unknown_route_returns_error_envelope() -> None:
    with TestClient(app) as client:
        resp = client.get("/api/v1/does-not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"]
    assert body["error"]["message"]
    assert "request_id" in body["error"]


def test_validation_error_returns_envelope() -> None:
    from pydantic import BaseModel

    from app.main import app as _app

    class _Body(BaseModel):
        name: str

    @_app.post("/_test-validate")
    async def _validate(body: _Body) -> dict:
        return {"ok": body.name}

    with TestClient(_app) as client:
        resp = client.post("/_test-validate", json={})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_raised_app_error_uses_envelope() -> None:
    from app.core.exceptions import ForbiddenError

    @app.get("/_test-forbidden")
    async def _forbidden():
        raise ForbiddenError("You cannot do that")

    with TestClient(app) as client:
        resp = client.get("/_test-forbidden")
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"
    assert "stack" not in resp.text.lower()
