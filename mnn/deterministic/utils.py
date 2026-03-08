"""Utility helpers for deterministic hashing and canonicalization."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    """Return canonical JSON-like representation (stable key order + separators)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(payload: bytes | str) -> str:
    """Return SHA-256 digest as lowercase hex."""
    raw = payload if isinstance(payload, bytes) else payload.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
