"""Basile deterministic coordinate mapping and corpus generation."""

from __future__ import annotations

from typing import Iterable, List, Tuple

import numpy as np

from .utils import sha256_hex


BASE29_ALPHABET = "abcdefghijklmnopqrstuvwxyz ,."
_CHAR_TO_INDEX = {c: i for i, c in enumerate(BASE29_ALPHABET)}


def normalize_query_seed_lock(query: str) -> str:
    """Seed-locked query normalization for deterministic search."""
    clean = "".join(ch for ch in query.lower() if ch in _CHAR_TO_INDEX)
    return " ".join(clean.split())


def coordinate_to_base29(coordinate: int) -> str:
    """Convert integer coordinate into deterministic base-29 string."""
    if coordinate < 0:
        raise ValueError("coordinate must be non-negative")
    if coordinate == 0:
        return BASE29_ALPHABET[0]
    value = coordinate
    chars: List[str] = []
    while value > 0:
        value, rem = divmod(value, 29)
        chars.append(BASE29_ALPHABET[rem])
    return "".join(reversed(chars))


def _seed_from_coordinate(coordinate: int, seed: int, query: str) -> int:
    payload = f"{seed}|{coordinate}|{normalize_query_seed_lock(query)}"
    digest = sha256_hex(payload)
    return int(digest[:16], 16)


def generate_basile_volume(
    coordinate: int,
    seed: int,
    query: str = "",
    volume_length: int = 1_312_000,
) -> str:
    """Generate deterministic fixed-length Library-of-Babel-style corpus text."""
    if volume_length <= 0:
        raise ValueError("volume_length must be positive")

    rng_seed = _seed_from_coordinate(coordinate, seed, query)
    rng = np.random.default_rng(rng_seed)
    indices = rng.integers(0, len(BASE29_ALPHABET), size=volume_length, dtype=np.uint8)
    table = np.frombuffer(BASE29_ALPHABET.encode("ascii"), dtype=np.uint8)
    volume_bytes = table[indices].tobytes()
    return volume_bytes.decode("ascii")


def ngram_decompose(text: str, n: int = 5) -> List[str]:
    """Deterministically decompose a string into ordered n-grams."""
    if n <= 0:
        raise ValueError("n must be positive")
    if len(text) < n:
        return []
    return [text[i : i + n] for i in range(0, len(text) - n + 1)]


def center_weighted_score(text: str, pattern: str) -> float:
    """Score sequence by proximity of pattern occurrence to center."""
    idx = text.find(pattern)
    if idx < 0:
        return 0.0
    center = len(text) / 2.0
    pattern_center = idx + len(pattern) / 2.0
    return 1.0 / (1.0 + abs(center - pattern_center))


def deterministic_search(
    query: str,
    coordinates: Iterable[int],
    seed: int,
    sample_size: int = 4096,
) -> List[Tuple[int, float]]:
    """Stable search scoring over coordinate-generated samples."""
    normalized = normalize_query_seed_lock(query)
    results: List[Tuple[int, float]] = []
    for coord in coordinates:
        corpus = generate_basile_volume(coord, seed, query=normalized, volume_length=sample_size)
        score = center_weighted_score(corpus, normalized)
        results.append((coord, score))
    return sorted(results, key=lambda item: (-item[1], item[0]))
