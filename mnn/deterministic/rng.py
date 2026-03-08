"""Deterministic RNG propagation helpers for Python/C++ parity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from .utils import canonical_json, sha256_hex


_MASK_64 = (1 << 64) - 1


def splitmix64_words(seed: int, stream_index: int, words: int) -> List[int]:
    """Generate SplitMix64 words deterministically (cross-language compatible)."""
    x = (seed ^ ((stream_index + 1) * 0x9E3779B97F4A7C15)) & _MASK_64
    out: List[int] = []
    for _ in range(words):
        x = (x + 0x9E3779B97F4A7C15) & _MASK_64
        z = x
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9 & _MASK_64
        z = (z ^ (z >> 27)) * 0x94D049BB133111EB & _MASK_64
        z = z ^ (z >> 31)
        out.append(z & _MASK_64)
    return out


@dataclass
class PRNGStreamDescriptor:
    """Bit-stable PRNG stream descriptor for audit and C++ synchronization."""

    name: str
    stream_index: int
    splitmix_words: List[int]
    descriptor_hash: str


class DeterministicSeedManager:
    """Single-root seed manager backed by SeedSequence fan-out."""

    def __init__(self, root_seed: int):
        self.root_seed = int(root_seed)
        self._seed_sequence = np.random.SeedSequence(self.root_seed)
        self._streams: Dict[str, np.random.Generator] = {}
        self._stream_count = 0

    def spawn_stream(self, name: str) -> np.random.Generator:
        """Spawn independent but reproducible stream."""
        if name in self._streams:
            return self._streams[name]
        child_seq = self._seed_sequence.spawn(1)[0]
        generator = np.random.default_rng(child_seq)
        self._streams[name] = generator
        self._stream_count += 1
        return generator

    def stream_descriptor(self, name: str, words: int = 8) -> PRNGStreamDescriptor:
        """Generate cross-language descriptor from root seed + stream index."""
        stream_names = sorted(self._streams)
        if name not in stream_names:
            self.spawn_stream(name)
            stream_names = sorted(self._streams)
        stream_index = stream_names.index(name)
        vector = splitmix64_words(self.root_seed, stream_index, words)
        payload = {
            "root_seed": self.root_seed,
            "name": name,
            "stream_index": stream_index,
            "splitmix_words": vector,
        }
        descriptor_hash = sha256_hex(canonical_json(payload))
        return PRNGStreamDescriptor(
            name=name,
            stream_index=stream_index,
            splitmix_words=vector,
            descriptor_hash=descriptor_hash,
        )
