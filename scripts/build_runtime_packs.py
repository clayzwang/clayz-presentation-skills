#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Build cloud/local light plugins from one public core plus offline add-ons."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import zipfile
from collections import defaultdict
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_TIME = (1980, 1, 1, 0, 0, 0)
LIGHT_ROOT = "clayz-presentation-skills"
OFFLINE_ROOT = "clayz-presentation-skills-offline"
LIGHT_TARGETS = ("cloud", "local")
EXCLUDED_PARTS = {
    ".git", ".idea", ".release-cache", ".tmp", ".vscode", "__pycache__",
    "build", "dist", "experience", "examples", "node_modules", "tests",
}
EXCLUDED_SUFFIXES = {
    ".pyc", ".pyo", ".ppt", ".pptx", ".pdf", ".ttf", ".otf", ".woff", ".woff2",
}
TEXT_SUFFIXES = {
    ".cff", ".css", ".html", ".js", ".json", ".jsonl", ".md", ".mjs", ".py",
    ".rels", ".svg", ".toml", ".txt", ".xml", ".yaml", ".yml",
}
CLOUD_EXCLUDED_PREFIXES = {
    ("packages", "adapters"),
    ("packages", "runtime", "packs"),
    ("provenance", "OFFLINE_DEPENDENCY_NOTICES.md"),
    ("scripts", "fetch_offline_wheels.py"),
    ("scripts", "install_offline_dependencies.py"),
}
PUBLIC_CORE_PREFIXES = {"catalog", "config", "skills"}
PUBLIC_CORE_PACKAGE_PREFIXES = {"contracts", "index_runtime", "layout", "patterns", "personal_extension", "validators"}
REQUIRED_DISTRIBUTIONS = {
    "Pillow": "12.3.0",
    "PyYAML": "6.0.3",
    "python-pptx": "1.0.2",
    "XlsxWriter": "3.2.9",
    "lxml": "6.0.2",
    "typing-extensions": "4.15.0",
}
WHEEL_KEYS = {name.lower().replace("-", "_"): name for name in REQUIRED_DISTRIBUTIONS}
OFFLINE_TARGETS = {
    "windows": ["CPython 3.12 / Windows x86-64"],
    "macos": ["CPython 3.12 / macOS arm64", "CPython 3.12 / macOS x86-64"],
    "linux": ["CPython 3.12 / manylinux 2.28 x86-64", "CPython 3.12 / manylinux 2.28 aarch64"],
}
DEFAULT_RELEASE_PLATFORMS = ("windows",)


def load_release_denylist(path: Path | None = None) -> tuple[str, ...]:
    """Load owner-private release terms without embedding them in public source."""

    selected = path
    if selected is None:
        configured = os.environ.get("CLAYZ_RELEASE_DENYLIST")
        selected = Path(configured) if configured else None
    if selected is None:
        return ()
    return tuple(
        dict.fromkeys(
            line.strip()
            for line in selected.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    )


def _denylist_match(value: str, denylist: tuple[str, ...]) -> str | None:
    folded = value.casefold()
    return next((term for term in denylist if term.casefold() in folded), None)


def _write_bytes(archive: zipfile.ZipFile, target: str, payload: bytes) -> None:
    info = zipfile.ZipInfo(target.replace("\\", "/"), date_time=ARCHIVE_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, payload)


def _write_file(archive: zipfile.ZipFile, target: str, source: Path) -> None:
    _write_bytes(archive, target, source.read_bytes())


def include_light(path: Path, target: str = "local") -> bool:
    if target not in LIGHT_TARGETS:
        raise ValueError(f"unsupported light target: {target}")
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if relative.parts[:2] == ("assets", "showcase"):
        return False
    if relative.parts[:1] == ("release",):
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    if target == "cloud":
        parts = relative.parts
        if any(parts[:len(prefix)] == prefix for prefix in CLOUD_EXCLUDED_PREFIXES):
            return False
        if relative.as_posix() in {"requirements.txt", "release/offline-requirements-py312.txt"}:
            return False
    return path.is_file()


def light_files(target: str = "local") -> list[Path]:
    selected: list[Path] = []
    for current, directories, filenames in os.walk(ROOT):
        directories[:] = sorted(name for name in directories if name not in EXCLUDED_PARTS)
        current_path = Path(current)
        for filename in sorted(filenames):
            path = current_path / filename
            if include_light(path, target):
                selected.append(path)
    return selected


def _is_public_core_file(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    if relative.parts and relative.parts[0] in PUBLIC_CORE_PREFIXES:
        return True
    return len(relative.parts) > 1 and relative.parts[0] == "packages" and relative.parts[1] in PUBLIC_CORE_PACKAGE_PREFIXES


def public_core_digest() -> str:
    digest = hashlib.sha256()
    for path in sorted(path for path in ROOT.rglob("*") if path.is_file() and _is_public_core_file(path)):
        relative = path.relative_to(ROOT).as_posix().encode("utf-8")
        digest.update(relative + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def _runtime_lock(version: str, target: str) -> dict[str, object]:
    lock: dict[str, object] = {
        "contract": "io.clayz.presentation.runtime-pack-lock/1.1",
        "plugin": "clayz-presentation-skills",
        "version": version,
        "bundle": f"{target}-public-light",
        "public_core_sha256": public_core_digest(),
        "tool_boundary": "host-provided" if target == "cloud" else "local-adapters",
        "preflight": "scripts/runtime_preflight.py",
    }
    if target == "local":
        lock["dependency_payload"] = "external requirements or matching offline add-on"
        lock["offline_addons"] = [
            f"clayz-presentation-skills-{version}-offline-{platform_name}-py312.zip"
            for platform_name in OFFLINE_TARGETS
        ]
    else:
        lock["dependency_payload"] = "ChatGPT host capabilities; no local dependency pack"
        lock["offline_addons"] = []
    return lock


def build_light(output_dir: Path, version: str, target: str = "local") -> Path:
    if target not in LIGHT_TARGETS:
        raise ValueError(f"unsupported light target: {target}")
    archive_path = output_dir / f"clayz-presentation-skills-{version}-{target}-light.zip"
    files = light_files(target)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive_target = PurePosixPath(LIGHT_ROOT) / PurePosixPath(path.relative_to(ROOT).as_posix())
            _write_file(archive, str(archive_target), path)
        _write_bytes(
            archive,
            f"{LIGHT_ROOT}/runtime/runtime-lock.json",
            json.dumps(_runtime_lock(version, target), ensure_ascii=False, indent=2).encode("utf-8") + b"\n",
        )
    audit_archive(archive_path)
    return archive_path


def _wheel_key(path: Path) -> str:
    return path.name.split("-", 1)[0].lower()


def collect_wheels(wheel_dir: Path) -> tuple[list[Path], dict[str, list[Path]]]:
    wheels = sorted(wheel_dir.glob("*.whl"))
    grouped: dict[str, list[Path]] = defaultdict(list)
    for wheel in wheels:
        key = _wheel_key(wheel)
        if key in WHEEL_KEYS:
            grouped[WHEEL_KEYS[key]].append(wheel)
    missing = sorted(set(REQUIRED_DISTRIBUTIONS) - set(grouped))
    if missing:
        raise ValueError(f"offline wheel cache is incomplete at {wheel_dir}: missing {', '.join(missing)}")
    unexpected = [wheel.name for wheel in wheels if _wheel_key(wheel) not in WHEEL_KEYS]
    if unexpected:
        raise ValueError(f"offline wheel cache contains unreviewed distributions: {', '.join(unexpected)}")
    return wheels, grouped


def _requirements_lock(grouped: dict[str, list[Path]]) -> str:
    lines = ["# Generated from reviewed wheels; install with --require-hashes."]
    for distribution, version in REQUIRED_DISTRIBUTIONS.items():
        hashes = sorted(hashlib.sha256(path.read_bytes()).hexdigest() for path in grouped[distribution])
        lines.append(f"{distribution}=={version} \\")
        for index, digest in enumerate(hashes):
            continuation = " \\" if index < len(hashes) - 1 else ""
            lines.append(f"    --hash=sha256:{digest}{continuation}")
    return "\n".join(lines) + "\n"


def _wheel_record(path: Path) -> dict[str, object]:
    return {
        "file": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }


def build_offline(platform_name: str, wheel_cache: Path, output_dir: Path, version: str) -> Path:
    wheel_dir = wheel_cache / platform_name
    wheels, grouped = collect_wheels(wheel_dir)
    archive_path = output_dir / f"clayz-presentation-skills-{version}-offline-{platform_name}-py312.zip"
    manifest = {
        "contract": "io.clayz.presentation.offline-dependency-pack/1.0",
        "plugin": "clayz-presentation-skills",
        "plugin_version": version,
        "platform": platform_name,
        "python": "CPython 3.12",
        "targets": OFFLINE_TARGETS[platform_name],
        "install": "python install_offline_dependencies.py",
        "network_required_at_install_time": False,
        "wheels": [_wheel_record(path) for path in wheels],
    }
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        _write_bytes(
            archive,
            f"{OFFLINE_ROOT}/offline-pack.json",
            json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8") + b"\n",
        )
        _write_bytes(
            archive,
            f"{OFFLINE_ROOT}/requirements.lock",
            _requirements_lock(grouped).encode("utf-8"),
        )
        _write_file(
            archive,
            f"{OFFLINE_ROOT}/install_offline_dependencies.py",
            ROOT / "scripts" / "install_offline_dependencies.py",
        )
        _write_file(
            archive,
            f"{OFFLINE_ROOT}/THIRD_PARTY_NOTICES.md",
            ROOT / "provenance" / "OFFLINE_DEPENDENCY_NOTICES.md",
        )
        for wheel in wheels:
            _write_file(archive, f"{OFFLINE_ROOT}/wheelhouse/{wheel.name}", wheel)
    audit_archive(archive_path)
    return archive_path


def _scan_text(label: str, payload: bytes, findings: list[str], denylist: tuple[str, ...]) -> None:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        return
    if match := _denylist_match(text, denylist):
        findings.append(f"{label}: external denylist term {match!r}")


def _scan_nested_wheel(label: str, payload: bytes, findings: list[str], denylist: tuple[str, ...]) -> None:
    from io import BytesIO

    try:
        with zipfile.ZipFile(BytesIO(payload)) as wheel:
            for info in wheel.infolist():
                folded_name = info.filename.casefold()
                if match := _denylist_match(info.filename, denylist):
                    findings.append(f"{label}!{info.filename}: external denylist path term {match!r}")
                if PurePosixPath(info.filename).suffix.lower() in TEXT_SUFFIXES or ".dist-info/licenses/" in folded_name:
                    _scan_text(f"{label}!{info.filename}", wheel.read(info), findings, denylist)
    except zipfile.BadZipFile:
        findings.append(f"{label}: invalid wheel archive")


def audit_archive(path: Path, denylist: tuple[str, ...] | None = None) -> None:
    denylist = load_release_denylist() if denylist is None else denylist
    findings: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            member = PurePosixPath(info.filename)
            if member.is_absolute() or ".." in member.parts:
                findings.append(f"{info.filename}: unsafe path")
                continue
            if match := _denylist_match(info.filename, denylist):
                findings.append(f"{info.filename}: external denylist path term {match!r}")
            payload = archive.read(info)
            if member.suffix.lower() in TEXT_SUFFIXES:
                _scan_text(info.filename, payload, findings, denylist)
            elif member.suffix.lower() == ".whl":
                _scan_nested_wheel(info.filename, payload, findings, denylist)
    if findings:
        path.unlink(missing_ok=True)
        raise ValueError("release archive audit failed: " + "; ".join(findings[:20]))


def write_checksums(paths: list[Path], output_dir: Path) -> Path:
    checksum_path = output_dir / "SHA256SUMS.txt"
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in sorted(paths)]
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return checksum_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--wheel-cache", type=Path, default=ROOT / ".release-cache" / "wheels")
    parser.add_argument("--bundle", choices=["light", "cloud-light", "local-light", "offline", "all"], default="all")
    parser.add_argument("--platform", choices=["windows", "macos", "linux", "all"], default="windows")
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    built: list[Path] = []
    if args.bundle in {"light", "all"}:
        built.extend(build_light(output, version, target) for target in LIGHT_TARGETS)
    elif args.bundle == "cloud-light":
        built.append(build_light(output, version, "cloud"))
    elif args.bundle == "local-light":
        built.append(build_light(output, version, "local"))
    if args.bundle in {"offline", "all"}:
        selected = list(OFFLINE_TARGETS) if args.platform == "all" else [args.platform]
        for platform_name in selected:
            built.append(build_offline(platform_name, args.wheel_cache.resolve(), output, version))
    checksum = write_checksums(built, output)
    for path in [*built, checksum]:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
