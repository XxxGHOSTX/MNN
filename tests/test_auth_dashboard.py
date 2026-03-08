"""Pytest coverage for auth + dashboard critical operator flow endpoints."""

import os
import pytest
import requests


BASE_URL = os.environ.get("BACKEND_BASE_URL")


@pytest.fixture(scope="session")
def api_client():
    if not BASE_URL:
        pytest.skip("BACKEND_BASE_URL is not set")
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def auth_token(api_client):
    response = api_client.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin", "password": "admin123!"},
        timeout=20,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data.get("access_token"), str)
    assert data.get("token_type") == "bearer"
    assert isinstance(data.get("expires_in"), int)
    return data["access_token"]


# Authentication module tests

def test_login_rejects_invalid_credentials(api_client):
    response = api_client.post(
        f"{BASE_URL}/auth/login",
        json={"username": "invalid", "password": "invalid"},
        timeout=20,
    )
    assert response.status_code == 401
    assert response.json().get("detail") == "Invalid username or password"


def test_login_default_credentials_returns_token(api_client):
    response = api_client.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin", "password": "admin123!"},
        timeout=20,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data.get("access_token"), str) and len(data["access_token"]) > 20
    assert data.get("token_type") == "bearer"


def test_auth_me_requires_bearer_token(api_client):
    response = api_client.get(f"{BASE_URL}/auth/me", timeout=20)
    assert response.status_code == 401
    assert response.json().get("detail") == "Missing bearer token"


def test_auth_me_returns_authenticated_profile(api_client, auth_token):
    response = api_client.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"},
        timeout=20,
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("username") == "admin"
    assert isinstance(data.get("auth_enabled_for_query_endpoint"), bool)


# Dashboard module tests

def test_dashboard_overview_requires_auth(api_client):
    response = api_client.get(f"{BASE_URL}/dashboard/overview", timeout=20)
    assert response.status_code == 401
    assert response.json().get("detail") == "Missing bearer token"


def test_dashboard_overview_returns_metrics_infra_feedback(api_client, auth_token):
    response = api_client.get(
        f"{BASE_URL}/dashboard/overview",
        headers={"Authorization": f"Bearer {auth_token}"},
        timeout=30,
    )
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data.get("metrics"), dict)
    assert isinstance(data.get("infra"), list)
    assert isinstance(data.get("feedback"), dict)

    service_names = {service.get("name") for service in data["infra"]}
    assert {"api", "postgres", "redis", "minio", "keycloak"}.issubset(service_names)

    mock_modes = [s.get("mode") for s in data["infra"] if s.get("name") in {"postgres", "redis", "minio", "keycloak"}]
    assert all(mode in {"mock", "real"} for mode in mock_modes)


# Query module tests

def test_query_works_without_token_when_api_auth_disabled(api_client):
    response = api_client.post(
        f"{BASE_URL}/query",
        json={"query": "deterministic inference"},
        timeout=30,
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("query") == "DETERMINISTIC INFERENCE"
    assert isinstance(data.get("results"), list)
    assert data.get("count") == 5
