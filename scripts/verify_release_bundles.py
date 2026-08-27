#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Verify Clayz light/offline release archives and their checksums."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.build_runtime_packs as builder  # noqa: E402


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _checksum_map(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, separator, filename = line.partition("  ")
        if not separator or len(digest) != 64 or not filename:
            raise ValueError(f"invalid checksum line: {line}")
        result[filename] = digest
    return result


def verify_light(path: Path, target: str) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        lock_name = f"{builder.LIGHT_ROOT}/runtime/runtime-lock.json"
        lock = json.loads(archive.read(lock_name)) if lock_name in names else {}
    for name in names:
        folded = name.casefold()
        if name.endswith(".whl"):
            errors.append(f"light archive contains wheel: {name}")
        if "/experience/" in folded or "/assets/showcase/" in folded:
            errors.append(f"light archive contains excluded showcase material: {name}")
        if Path(name).suffix.lower() in builder.EXCLUDED_SUFFIXES:
            errors.append(f"light archive contains excluded binary: {name}")
    required = f"{builder.LIGHT_ROOT}/runtime/runtime-lock.json"
    if required not in names:
        errors.append(f"light archive missing {required}")
    if lock.get("bundle") != f"{target}-public-light":
        errors.append(f"{path.name}: wrong light target lock")
    if target == "cloud" and any("/packages/adapters/" in name or "/packages/runtime/packs/" in name for name in names):
        errors.append(f"{path.name}: cloud light contains local execution payload")
    return errors


def verify_offline(path: Path, platform_name: str) -> list[str]:
    errors: list[str] = []
    prefix = builder.OFFLINE_ROOT
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        manifest_name = f"{prefix}/offline-pack.json"
        lock_name = f"{prefix}/requirements.lock"
        if manifest_name not in names or lock_name not in names:
            return [f"{path.name}: missing offline manifest or lock"]
        manifest = json.loads(archive.read(manifest_name))
        lock = archive.read(lock_name).decode("utf-8")
        if manifest.get("platform") != platform_name or manifest.get("python") != "CPython 3.12":
            errors.append(f"{path.name}: wrong platform or Python target")
        wheel_records = manifest.get("wheels")
        if not isinstance(wheel_records, list):
            return [f"{path.name}: wheels must be a list"]
        seen_distributions: set[str] = set()
        for record in wheel_records:
            if not isinstance(record, dict) or not isinstance(record.get("file"), str):
                errors.append(f"{path.name}: invalid wheel record")
                continue
            filename = record["file"]
            member = f"{prefix}/wheelhouse/{filename}"
            if member not in names:
                errors.append(f"{path.name}: missing wheel {filename}")
                continue
            payload = archive.read(member)
            digest = _sha256(payload)
            if record.get("sha256") != digest or record.get("bytes") != len(payload):
                errors.append(f"{path.name}: wheel metadata mismatch for {filename}")
            if f"--hash=sha256:{digest}" not in lock:
                errors.append(f"{path.name}: wheel hash absent from requirements.lock for {filename}")
            wheel_key = filename.split("-", 1)[0].lower()
            if wheel_key in builder.WHEEL_KEYS:
                seen_distributions.add(builder.WHEEL_KEYS[wheel_key])
        missing = sorted(set(builder.REQUIRED_DISTRIBUTIONS) - seen_distributions)
        if missing:
            errors.append(f"{path.name}: missing distributions {', '.join(missing)}")
    return errors


def verify(root: Path, platforms: tuple[str, ...] = builder.DEFAULT_RELEASE_PLATFORMS) -> list[str]:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    expected = [f"clayz-presentation-skills-{version}-{target}-light.zip" for target in builder.LIGHT_TARGETS] + [
        f"clayz-presentation-skills-{version}-offline-{platform_name}-py312.zip"
        for platform_name in platforms
    ]
    errors: list[str] = []
    checksum_path = root / "SHA256SUMS.txt"
    if not checksum_path.is_file():
        return ["SHA256SUMS.txt is missing"]
    try:
        checksums = _checksum_map(checksum_path)
    except (OSError, ValueError) as exc:
        return [str(exc)]
    if set(checksums) != set(expected):
        errors.append(
            "SHA256SUMS.txt does not list exactly the two light archives and "
            f"the selected offline add-ons: {', '.join(platforms)}"
        )
    for filename in expected:
        path = root / filename
        if not path.is_file():
            errors.append(f"missing release archive: {filename}")
            continue
        digest = _sha256(path.read_bytes())
        if checksums.get(filename) != digest:
            errors.append(f"checksum mismatch: {filename}")
        try:
            builder.audit_archive(path)
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            errors.append(f"archive audit failed for {filename}: {exc}")
            continue
        if filename.endswith("-light.zip"):
            target = next(name for name in builder.LIGHT_TARGETS if f"-{name}-light.zip" in filename)
            errors.extend(verify_light(path, target))
        else:
            platform_name = next(name for name in builder.OFFLINE_TARGETS if f"-offline-{name}-" in filename)
            errors.extend(verify_offline(path, platform_name))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=ROOT / "dist")
    parser.add_argument("--platform", choices=["windows", "macos", "linux", "all"], default="windows")
    args = parser.parse_args()
    platforms = tuple(builder.OFFLINE_TARGETS) if args.platform == "all" else (args.platform,)
    errors = verify(args.root.resolve(), platforms)
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
