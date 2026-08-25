#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Install a matching Clayz offline dependency wheelhouse with no network."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, help="Optional isolated target directory instead of the active environment")
    args = parser.parse_args()
    if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 12):
        print("ERROR: this offline pack requires CPython 3.12.", file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parent
    wheelhouse = root / "wheelhouse"
    requirements = root / "requirements.lock"
    if not wheelhouse.is_dir() or not requirements.is_file():
        print("ERROR: wheelhouse or requirements.lock is missing.", file=sys.stderr)
        return 2
    command = [
        sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
        "--no-index", "--only-binary=:all:", "--require-hashes",
        "--find-links", str(wheelhouse), "--requirement", str(requirements),
    ]
    if args.target:
        args.target.mkdir(parents=True, exist_ok=True)
        command.extend(["--target", str(args.target.resolve())])
    subprocess.run(command, check=True)
    print("Clayz offline presentation dependencies installed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
