from fastapi.testclient import TestClient

from app.main import create_app


def test_guidance_rejects_blank_query() -> None:
    client = TestClient(create_app())
    resp = client.post("/api/v1/guidance/stream", json={"query": "   "})
    assert resp.status_code == 422


def test_guidance_retrieve_rejects_blank_query() -> None:
    client = TestClient(create_app())
    resp = client.post("/api/v1/guidance/retrieve", json={"query": "   "})
    assert resp.status_code == 422
