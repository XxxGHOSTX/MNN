"""Token and authentication helpers for MNN API."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(message: str, secret: str) -> str:
    signature = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    return _b64url_encode(signature)


def create_access_token(username: str, secret: str, expires_minutes: int = 120) -> str:
    """Create a compact HMAC-signed bearer token."""
    now = int(time.time())
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + (expires_minutes * 60),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}"
    signature = _sign(signing_input, secret)
    return f"{signing_input}.{signature}"


def verify_access_token(token: str, secret: str) -> Optional[Dict[str, Any]]:
    """Verify token signature and expiration."""
    try:
        header_part, payload_part, signature_part = token.split(".")
    except ValueError:
        return None

    signing_input = f"{header_part}.{payload_part}"
    expected_signature = _sign(signing_input, secret)
    if not hmac.compare_digest(signature_part, expected_signature):
        return None

    try:
        payload = json.loads(_b64url_decode(payload_part).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None

    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        return None

    return payload
