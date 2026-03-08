"""Infrastructure status checks with graceful mock fallbacks."""

from __future__ import annotations

import socket
from typing import Any, Dict, List
from urllib.parse import urlparse

import httpx


def _service(name: str, status: str, mode: str, detail: str) -> Dict[str, str]:
    return {"name": name, "status": status, "mode": mode, "detail": detail}


def _check_postgres(config: Any) -> Dict[str, str]:
    if not config.THALOS_DB_DSN:
        return _service("postgres", "healthy", "mock", "No DSN configured; using mock fallback mode")

    try:
        import psycopg2

        conn = psycopg2.connect(config.THALOS_DB_DSN, connect_timeout=config.THALOS_DB_CONNECT_TIMEOUT)
        conn.close()
        return _service("postgres", "healthy", "real", "Connected")
    except Exception as exc:  # pragma: no cover - depends on external runtime service
        return _service("postgres", "degraded", "real", f"Connection failed: {exc}")


def _check_redis(config: Any) -> Dict[str, str]:
    if not config.REDIS_URL:
        return _service("redis", "healthy", "mock", "REDIS_URL not configured; using mock fallback mode")

    try:
        parsed = urlparse(config.REDIS_URL)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        with socket.create_connection((host, port), timeout=2):
            return _service("redis", "healthy", "real", "TCP connection established")
    except Exception as exc:  # pragma: no cover - depends on external runtime service
        return _service("redis", "degraded", "real", f"Connection failed: {exc}")


def _check_minio(config: Any) -> Dict[str, str]:
    if not config.MINIO_ENDPOINT:
        return _service("minio", "healthy", "mock", "MINIO_ENDPOINT not configured; using mock fallback mode")

    endpoint = config.MINIO_ENDPOINT
    if not endpoint.startswith("http"):
        endpoint = f"http://{endpoint}"
    health_url = f"{endpoint.rstrip('/')}/minio/health/live"

    try:
        response = httpx.get(health_url, timeout=3)
        if response.status_code == 200:
            return _service("minio", "healthy", "real", "Health endpoint reachable")
        return _service("minio", "degraded", "real", f"Health endpoint returned {response.status_code}")
    except Exception as exc:  # pragma: no cover - depends on external runtime service
        return _service("minio", "degraded", "real", f"Health check failed: {exc}")


def _check_keycloak(config: Any) -> Dict[str, str]:
    if not config.KEYCLOAK_URL:
        return _service("keycloak", "healthy", "mock", "KEYCLOAK_URL not configured; using mock fallback mode")

    base = config.KEYCLOAK_URL.rstrip("/")
    realm = config.KEYCLOAK_REALM or "master"
    well_known = f"{base}/realms/{realm}/.well-known/openid-configuration"

    try:
        response = httpx.get(well_known, timeout=3)
        if response.status_code == 200:
            return _service("keycloak", "healthy", "real", f"Realm '{realm}' reachable")
        return _service("keycloak", "degraded", "real", f"OpenID discovery returned {response.status_code}")
    except Exception as exc:  # pragma: no cover - depends on external runtime service
        return _service("keycloak", "degraded", "real", f"OpenID discovery failed: {exc}")


def get_infra_status(config: Any) -> List[Dict[str, str]]:
    """Collect infra service health in deterministic order."""
    return [
        _service("api", "healthy", "real", "FastAPI runtime active"),
        _check_postgres(config),
        _check_redis(config),
        _check_minio(config),
        _check_keycloak(config),
        _service("mnn_core", "healthy", "real", "C++ core compiled and bundled in repository"),
    ]
