#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Build deterministic local plugin ZIPs for Windows, macOS, and Linux."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".idea", ".vscode", "__pycache__", "node_modules", "dist", "build"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".ppt", ".pptx", ".pdf", ".ttf", ".otf", ".woff", ".woff2"}


def include(path: Path, platform_name: str) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_PARTS for part in relative.parts) or path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    marker = ("packages", "runtime", "packs")
    parts = relative.parts
    if len(parts) > 3 and parts[:3] == marker and parts[3] not in {"common", platform_name}:
        return False
    return path.is_file()


def build(platform_name: str, output_dir: Path, version: str) -> Path:
    archive_path = output_dir / f"clayz-presentation-skills-{version}-{platform_name}.zip"
    files = sorted(path for path in ROOT.rglob("*") if include(path, platform_name))
    runtime_lock = {
        "contract": "io.clayz.presentation.runtime-pack-lock/1.0",
        "plugin": "clayz-presentation-skills",
        "version": version,
        "platform": platform_name,
        "dependency_payload": "requirements-and-installable-source; no third-party binary redistribution",
        "preflight": "scripts/runtime_preflight.py",
    }
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            target = Path("clayz-presentation-skills") / path.relative_to(ROOT)
            info = zipfile.ZipInfo(str(target).replace("\\", "/"), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
        info = zipfile.ZipInfo("clayz-presentation-skills/runtime/runtime-lock.json", date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, json.dumps(runtime_lock, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    return archive_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--platform", choices=["windows", "macos", "linux", "all"], default="all")
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    selected = ["windows", "macos", "linux"] if args.platform == "all" else [args.platform]
    for platform_name in selected:
        print(build(platform_name, output, version))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
