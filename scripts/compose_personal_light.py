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
from scripts.validate_plugin_mount import REQUIRED_PERSONAL_PATHS, REQUIRED_SHARED_PATHS, REQUIRED_SKILLS  # noqa: E402


PLUGIN_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHOWCASE_IMAGE_PATTERN = re.compile(r"^!\[[^\]]*\]\(assets/showcase/[^)]+\)\s*$", re.MULTILINE)
PERSONAL_CONFIG_PATH = "config/personal-extension-resolved.json"
PERSONAL_RUNTIME_PATH = "runtime/personal-extension.json"
PLUGIN_MOUNT_PATH = "runtime/plugin-mount-contract.json"


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
    manifest["description"] = "A Supervisor-rooted personal presentation plugin with a user-visible resource inventory before Logic, five stage gates, first-class owner Index materialization, receipt-bound learning, and render-grounded QA."
    interface = dict(manifest.get("interface") or {})
    interface["shortDescription"] = "Inventory resources, then run five governed stages"
    interface["longDescription"] = (
        "Before Logic, Supervisor inventories plugin, task, owner Library, public Index, brand, host, and font "
        "resources; tells the user what was found, selected, unavailable, and which route will be used; then locks "
        "the inventory and starts. It materializes the owner's admitted learning as a first-class task Index, "
        "requires cumulative five-stage receipts, and reconciles actual resource use before delivery."
    )
    manifest["interface"] = interface
    interface = manifest.setdefault("interface", {})
    interface["displayName"] = "Clayz Presentation Skills Personal"
    return manifest


def _light_files() -> list[Path]:
    return [path for path in sorted(ROOT.rglob("*")) if include_light(path, "cloud")]


def _personal_light_bytes(path: Path) -> bytes:
    """Remove public showcase links whose media is intentionally absent in Cloud Light."""

    if path.relative_to(ROOT).as_posix() != "README.md":
        return path.read_bytes()
    text = SHOWCASE_IMAGE_PATTERN.sub("", path.read_text(encoding="utf-8"))
    return text.encode("utf-8")


def compose_personal_light(
    profile_path: Path,
    provider_manifest_paths: Sequence[Path],
    output_path: Path,
    *,
    plugin_name: str = "clayz-presentation-skills-personal",
    wrap_directory: bool = False,
) -> Path:
    """Write a private cloud plugin ZIP without private Library indexes or attachments.

    The default archive is install-ready: ``.codex-plugin/plugin.json`` is at
    the ZIP root. ``wrap_directory`` exists only for source-distribution tools
    that explicitly require one containing folder.
    """

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
        "plugin_mount_contract": PLUGIN_MOUNT_PATH,
        "required_shared_paths": list(REQUIRED_SHARED_PATHS),
        "personal_extension_digest": runtime["lock"]["digest"],
        "resolved_config_digest": sha256_json(resolved_config),
    }
    required_paths = [
        *REQUIRED_SHARED_PATHS,
        *REQUIRED_PERSONAL_PATHS,
        *(f"skills/{name}/SKILL.md" for name in REQUIRED_SKILLS),
    ]
    mount_contract = {
        "contract": "io.clayz.presentation.plugin-mount/1.0",
        "plugin": plugin_name,
        "archive_layout": "wrapped-directory" if wrap_directory else "plugin-root",
        "complete_plugin_required": True,
        "detached_skill_publication_forbidden": True,
        "required_paths": required_paths,
        "failure_status": "plugin-runtime-incomplete",
    }

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prefix = f"{plugin_name}/" if wrap_directory else ""
    def target(relative: str) -> str:
        return f"{prefix}{PurePosixPath(relative).as_posix()}"

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in _light_files():
            relative = path.relative_to(ROOT).as_posix()
            if relative == ".codex-plugin/plugin.json":
                continue
            _write_bytes(archive, target(relative), _personal_light_bytes(path))
        _write_bytes(archive, target(".codex-plugin/plugin.json"), _json_bytes(plugin_manifest))
        _write_bytes(archive, target(PERSONAL_CONFIG_PATH), _json_bytes(resolved_config))
        _write_bytes(archive, target(PERSONAL_RUNTIME_PATH), _json_bytes(runtime))
        _write_bytes(archive, target("runtime/runtime-lock.json"), _json_bytes(runtime_lock))
        _write_bytes(archive, target(PLUGIN_MOUNT_PATH), _json_bytes(mount_contract))

    with zipfile.ZipFile(output_path) as archive:
        names = archive.namelist()
        for name in names:
            member = PurePosixPath(name)
            if member.is_absolute() or ".." in member.parts:
                output_path.unlink(missing_ok=True)
                raise PersonalExtensionError(f"unsafe archive member: {name}")
        required = {target(path) for path in required_paths}
        required.add(target(PLUGIN_MOUNT_PATH))
        if not required.issubset(names):
            output_path.unlink(missing_ok=True)
            missing = sorted(required - set(names))
            raise PersonalExtensionError(f"cloud personal plugin archive is incomplete: {missing}")
        manifest_name = target(".codex-plugin/plugin.json")
        if not wrap_directory and manifest_name != ".codex-plugin/plugin.json":
            output_path.unlink(missing_ok=True)
            raise PersonalExtensionError("install-ready archive must place plugin.json at the ZIP root")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path, help="Private Personal Extension Profile JSON")
    parser.add_argument("--provider-manifest", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--plugin-name", default="clayz-presentation-skills-personal")
    parser.add_argument("--wrap-directory", action="store_true", help="Wrap the plugin in one containing directory")
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    output = args.output or ROOT / "dist" / "private" / f"{args.plugin_name}-{version}-cloud-light.zip"
    try:
        path = compose_personal_light(
            args.profile,
            args.provider_manifest,
            output,
            plugin_name=args.plugin_name,
            wrap_directory=args.wrap_directory,
        )
        print(path)
        return 0
    except (OSError, json.JSONDecodeError, IndexRuntimeError, PersonalExtensionError, zipfile.BadZipFile) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
