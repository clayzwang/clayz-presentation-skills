#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Attach one private profile and Library route to the cloud public light core."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime import IndexRuntimeError, read_json  # noqa: E402
from packages.index_runtime.utils import sha256_json  # noqa: E402
from packages.personal_extension import PersonalExtensionError, resolve_personal_extension  # noqa: E402
from scripts.build_runtime_packs import ARCHIVE_TIME, include_light, public_core_digest  # noqa: E402


PLUGIN_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PERSONAL_CONFIG_PATH = "config/personal-extension-resolved.json"
PERSONAL_RUNTIME_PATH = "runtime/personal-extension.json"


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"


def _write_bytes(archive: zipfile.ZipFile, target: str, payload: bytes) -> None:
    info = zipfile.ZipInfo(target.replace("\\", "/"), date_time=ARCHIVE_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, payload)


def _personal_manifest(base: Mapping[str, Any], plugin_name: str) -> dict[str, Any]:
    manifest = json.loads(json.dumps(base))
    manifest["name"] = plugin_name
    manifest["description"] = "A personal ChatGPT composition of the Clayz cloud public core, one Personal Extension Profile, and owner-private Library routes."
    interface = manifest.setdefault("interface", {})
    interface["displayName"] = "Clayz Presentation Skills Personal"
    interface["shortDescription"] = "Cloud public core with one private extension"
    interface["longDescription"] = "Connect the unchanged Clayz Logic, Copy, Art Direction, Output, and Supervisor brain to ChatGPT host tools, one resolved owner-private profile, and host Library provider routes."
    return manifest


def _light_files() -> list[Path]:
    return [path for path in sorted(ROOT.rglob("*")) if include_light(path, "cloud")]


def compose_personal_light(
    profile_path: Path,
    provider_manifest_paths: Sequence[Path],
    output_path: Path,
    *,
    plugin_name: str = "clayz-presentation-skills-personal",
) -> Path:
    """Write a private cloud ZIP without copying private Library indexes or attachments."""

    if not PLUGIN_NAME_PATTERN.fullmatch(plugin_name) or len(plugin_name) > 64:
        raise PersonalExtensionError("plugin name must be lower-case hyphen-case and at most 64 characters")
    private_inputs = [profile_path.resolve(), *(path.resolve() for path in provider_manifest_paths)]
    for path in private_inputs:
        try:
            path.relative_to(ROOT)
        except ValueError:
            pass
        else:
            raise PersonalExtensionError(f"private input must stay outside the public repository: {path.name}")
    profile = read_json(private_inputs[0])
    provider_manifests = [read_json(path) for path in private_inputs[1:]]
    base_config = read_json(ROOT / "config" / "default.json")
    public_provider_manifest = read_json(ROOT / base_config["references"]["public_provider_manifest"])
    resolved_config, runtime = resolve_personal_extension(
        base_config,
        profile,
        host="chatgpt-personal",
        public_provider_manifests=[public_provider_manifest],
        provider_manifests=provider_manifests,
        config_path=PERSONAL_CONFIG_PATH,
    )
    base_manifest = read_json(ROOT / ".codex-plugin" / "plugin.json")
    plugin_manifest = _personal_manifest(base_manifest, plugin_name)
    runtime_lock = {
        "contract": "io.clayz.presentation.runtime-pack-lock/1.1",
        "plugin": plugin_name,
        "version": base_manifest["version"],
        "bundle": "cloud-personal-composition",
        "base_bundle": "cloud-public-light",
        "public_core_sha256": public_core_digest(),
        "tool_boundary": "ChatGPT-host-provided",
        "dependency_payload": "no local dependency pack",
        "preflight": "scripts/runtime_preflight.py",
        "personal_extension_digest": runtime["lock"]["digest"],
        "resolved_config_digest": sha256_json(resolved_config),
    }

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    root = PurePosixPath(plugin_name)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in _light_files():
            relative = path.relative_to(ROOT).as_posix()
            if relative == ".codex-plugin/plugin.json":
                continue
            target = root / PurePosixPath(relative)
            _write_bytes(archive, str(target), path.read_bytes())
        _write_bytes(archive, str(root / ".codex-plugin" / "plugin.json"), _json_bytes(plugin_manifest))
        _write_bytes(archive, str(root / PERSONAL_CONFIG_PATH), _json_bytes(resolved_config))
        _write_bytes(archive, str(root / PERSONAL_RUNTIME_PATH), _json_bytes(runtime))
        _write_bytes(archive, str(root / "runtime" / "runtime-lock.json"), _json_bytes(runtime_lock))

    with zipfile.ZipFile(output_path) as archive:
        names = archive.namelist()
        for name in names:
            member = PurePosixPath(name)
            if member.is_absolute() or ".." in member.parts:
                output_path.unlink(missing_ok=True)
                raise PersonalExtensionError(f"unsafe archive member: {name}")
        required = {
            str(root / ".codex-plugin" / "plugin.json"),
            str(root / PERSONAL_CONFIG_PATH),
            str(root / PERSONAL_RUNTIME_PATH),
            str(root / "runtime" / "runtime-lock.json"),
        }
        if not required.issubset(names):
            output_path.unlink(missing_ok=True)
            raise PersonalExtensionError("cloud personal light archive is incomplete")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path, help="Private Personal Extension Profile JSON")
    parser.add_argument("--provider-manifest", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--plugin-name", default="clayz-presentation-skills-personal")
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    output = args.output or ROOT / "dist" / "private" / f"{args.plugin_name}-{version}-cloud-light.zip"
    try:
        path = compose_personal_light(args.profile, args.provider_manifest, output, plugin_name=args.plugin_name)
        print(path)
        return 0
    except (OSError, json.JSONDecodeError, IndexRuntimeError, PersonalExtensionError, zipfile.BadZipFile) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
