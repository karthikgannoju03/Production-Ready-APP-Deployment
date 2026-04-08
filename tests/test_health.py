import os

os.environ["APP_ENV"] = "testing"

from src.app import app  # noqa: E402


def test_health_endpoint_ok():
    client = app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data is not None
    assert data["status"] in {"ok", "degraded"}
    assert "database" in data
    assert "redis" in data


def test_create_item_happy_path():
    client = app.test_client()
    resp = client.post("/api/v1/items", json={"message": "hello world"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data is not None
    assert isinstance(data.get("id"), int)
    assert "created_at" in data


def test_create_item_validation():
    client = app.test_client()
    resp = client.post("/api/v1/items", json={"message": ""})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data is not None
    assert "error" in data

