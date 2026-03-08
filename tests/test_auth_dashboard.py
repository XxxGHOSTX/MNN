"""Pytest coverage for auth + dashboard critical operator flow endpoints."""

from fastapi.testclient import TestClient

from api import app


def _login(client: TestClient) -> str:
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin123!"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("access_token"), str)
    assert payload.get("token_type") == "bearer"
    assert isinstance(payload.get("expires_in"), int)
    return payload["access_token"]


def test_login_rejects_invalid_credentials():
    client = TestClient(app)
    response = client.post(
        "/auth/login",
        json={"username": "invalid", "password": "invalid"},
    )
    assert response.status_code == 401
    assert response.json().get("detail") == "Invalid username or password"


def test_login_default_credentials_returns_token():
    client = TestClient(app)
    token = _login(client)
    assert len(token) > 20


def test_auth_me_requires_bearer_token():
    client = TestClient(app)
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json().get("detail") == "Missing bearer token"


def test_auth_me_returns_authenticated_profile():
    client = TestClient(app)
    token = _login(client)
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("username") == "admin"
    assert isinstance(data.get("auth_enabled_for_query_endpoint"), bool)


def test_dashboard_overview_requires_auth():
    client = TestClient(app)
    response = client.get("/dashboard/overview")
    assert response.status_code == 401
    assert response.json().get("detail") == "Missing bearer token"


def test_dashboard_overview_returns_metrics_infra_feedback():
    client = TestClient(app)
    token = _login(client)
    response = client.get(
        "/dashboard/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data.get("metrics"), dict)
    assert isinstance(data.get("infra"), list)
    assert isinstance(data.get("feedback"), dict)

    service_names = {service.get("name") for service in data["infra"]}
    assert {"api", "postgres", "redis", "minio", "keycloak"}.issubset(service_names)

    mock_modes = [
        s.get("mode")
        for s in data["infra"]
        if s.get("name") in {"postgres", "redis", "minio", "keycloak"}
    ]
    assert all(mode in {"mock", "real"} for mode in mock_modes)


def test_query_works_without_token_when_api_auth_disabled():
    client = TestClient(app)
    response = client.post(
        "/query",
        json={"query": "deterministic inference"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("query") == "DETERMINISTIC INFERENCE"
    assert isinstance(data.get("results"), list)
    assert data.get("count") == 5
