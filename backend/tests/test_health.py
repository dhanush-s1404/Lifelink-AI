from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "LifeLink AI"


def test_ready_returns_ready() -> None:
    with TestClient(app) as client:
        resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_live_returns_alive() -> None:
    with TestClient(app) as client:
        resp = client.get("/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


def test_openapi_schema_exposed() -> None:
    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "openapi" in schema
    assert "/health" in schema["paths"]


def test_request_id_header_set() -> None:
    with TestClient(app) as client:
        resp = client.get("/health", headers={"X-Request-ID": "test-req-123"})
    assert resp.headers["X-Request-ID"] == "test-req-123"
