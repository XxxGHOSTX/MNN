"""Detect host-level variance that can break deterministic builds."""

from __future__ import annotations

import json
import os
import platform
import sys


def collect() -> dict:
    return {
        "python_version": sys.version.split()[0],
        "python_impl": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "endianness": sys.byteorder,
        "deterministic_mode": os.getenv("DETERMINISTIC_MODE", "unset"),
        "pythonhashseed": os.getenv("PYTHONHASHSEED", "unset"),
        "tz": os.getenv("TZ", "unset"),
        "lc_all": os.getenv("LC_ALL", "unset"),
        "source_date_epoch": os.getenv("SOURCE_DATE_EPOCH", "unset"),
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="fail on Python version mismatch")
    args = parser.parse_args()

    payload = collect()
    print(json.dumps(payload, indent=2, sort_keys=True))

    allowed_python_major_minor = "3.12"
    if not payload["python_version"].startswith(allowed_python_major_minor):
        print(
            f"[variance] Expected Python {allowed_python_major_minor}.x, got {payload['python_version']}",
            file=sys.stderr,
        )
        if args.strict:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
