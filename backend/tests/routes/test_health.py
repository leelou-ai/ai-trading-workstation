"""Tests for health endpoint."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.health import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_health_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
