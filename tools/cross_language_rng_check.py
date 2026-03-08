"""Cross-language deterministic descriptor parity check (Python vs C++)."""

from __future__ import annotations

import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mnn.deterministic.rng import splitmix64_words


def main() -> int:
    seed = 123456789
    stream_index = 2
    words = 8

    py_words = splitmix64_words(seed, stream_index, words)

    binary = Path("/tmp/cpp_descriptor_dump")
    compile_cmd = [
        "g++",
        "-std=c++17",
        "-O2",
        "-Iinclude",
        "src/deterministic_state.cpp",
        "tools/cpp_descriptor_dump.cpp",
        "-o",
        str(binary),
    ]
    subprocess.run(compile_cmd, check=True)

    proc = subprocess.run(
        [str(binary), str(seed), str(stream_index), str(words)],
        check=True,
        capture_output=True,
        text=True,
    )
    cpp_words = [int(part) for part in proc.stdout.strip().split(",") if part.strip()]

    if py_words != cpp_words:
        print("Cross-language determinism check failed")
        print("python:", py_words)
        print("cpp:", cpp_words)
        return 1

    print("Cross-language determinism check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
