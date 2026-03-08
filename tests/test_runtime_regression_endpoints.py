"""Pytest regression checks for auth/dashboard and monitoring endpoints via FastAPI TestClient."""

from fastapi.testclient import TestClient

from api import app


# Module: Authentication + Dashboard + Monitoring regression checks

def test_health_endpoint_contract():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "MNN Knowledge Engine"
    assert "cache_info" in data


def test_api_version_endpoint_contract():
    client = TestClient(app)
    response = client.get("/api/version")
    assert response.status_code == 200
    data = response.json()
    assert data["api_version"] == "1.0.0"
    assert data["pipeline_version"] == "1.0.0"
    assert isinstance(data["features"], dict)
    assert "deterministic_mode" in data["features"]


def test_auth_login_and_dashboard_overview_flow():
    client = TestClient(app)

    login_response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    profile_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["username"] == "admin"

    dashboard_response = client.get(
        "/dashboard/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dashboard_response.status_code == 200
    dashboard_data = dashboard_response.json()
    assert "metrics" in dashboard_data
    assert "infra" in dashboard_data
    assert "feedback" in dashboard_data
