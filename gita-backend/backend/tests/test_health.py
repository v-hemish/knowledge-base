from fastapi.testclient import TestClient

from app.main import create_app


def test_health_ok() -> None:
    client = TestClient(create_app())
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_ready_has_components() -> None:
    """Readiness shape is stable; individual ``ok`` flags depend on local Ollama and DB."""
    client = TestClient(create_app())
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("ready", "degraded")
    comps = body["components"]
    assert set(comps.keys()) == {"database", "embeddings", "ollama"}
    for key in ("database", "embeddings", "ollama"):
        assert "ok" in comps[key]


def test_api_v1_version_present() -> None:
    client = TestClient(create_app())
    resp = client.get("/api/v1/version")
    assert resp.status_code == 200
    body = resp.json()
    assert body["api"] == "v1"
    assert "package_version" in body
