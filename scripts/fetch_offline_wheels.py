#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Download reviewed CPython 3.12 wheels for per-system offline packs."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "windows": ["win_amd64"],
    "macos": ["macosx_11_0_arm64", "macosx_10_13_x86_64"],
    "linux": ["manylinux_2_28_x86_64", "manylinux_2_28_aarch64"],
}


def download(platform_name: str, output_root: Path, requirements: Path) -> None:
    destination = output_root / platform_name
    destination.mkdir(parents=True, exist_ok=True)
    for platform_tag in TARGETS[platform_name]:
        command = [
            sys.executable, "-m", "pip", "download", "--disable-pip-version-check",
            "--only-binary=:all:", "--dest", str(destination), "--platform", platform_tag,
            "--python-version", "312", "--implementation", "cp", "--abi", "cp312",
            "--requirement", str(requirements),
        ]
        subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".release-cache" / "wheels")
    parser.add_argument("--requirements", type=Path, default=ROOT / "release" / "offline-requirements-py312.txt")
    parser.add_argument("--platform", choices=["windows", "macos", "linux", "all"], default="all")
    args = parser.parse_args()
    selected = list(TARGETS) if args.platform == "all" else [args.platform]
    for platform_name in selected:
        download(platform_name, args.output.resolve(), args.requirements.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
