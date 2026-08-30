#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Attach one private profile and Library route to a ChatGPT cloud artifact."""

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
from packages.personal_extension import PersonalExtensionError, required_provider_bindings, resolve_personal_extension  # noqa: E402
from scripts.build_runtime_packs import ARCHIVE_TIME, include_light, public_core_digest  # noqa: E402
from scripts.validate_plugin_mount import REQUIRED_PERSONAL_PATHS, REQUIRED_SHARED_PATHS, REQUIRED_SKILLS  # noqa: E402


PLUGIN_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHOWCASE_IMAGE_PATTERN = re.compile(r"^!\[[^\]]*\]\(assets/showcase/[^)]+\)\s*$", re.MULTILINE)
FRONTMATTER_PATTERN = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.DOTALL)
ROOT_RELATIVE_PATTERN = re.compile(r"(?:\.\./)+(scripts|packages|config|runtime|docs|catalog|assets)/")
PERSONAL_CONFIG_PATH = "config/personal-extension-resolved.json"
PERSONAL_RUNTIME_PATH = "runtime/personal-extension.json"
PLUGIN_MOUNT_PATH = "runtime/plugin-mount-contract.json"
COMPOSITE_MOUNT_PATH = "runtime/skill-mount-contract.json"
COMPOSITE_TEMPLATE_PATH = ROOT / "packages" / "chatgpt_personal" / "composite-skill.md"
COMPOSITE_ARTIFACT = "standalone-skill"
PLUGIN_ARTIFACT = "plugin"
ARTIFACT_KINDS = (COMPOSITE_ARTIFACT, PLUGIN_ARTIFACT)
STAGE_SOURCES = (
    ("logic", "clayz-presentation-logic"),
    ("copy", "clayz-presentation-copy"),
    ("art-direction", "clayz-presentation-art-direction"),
    ("output", "clayz-presentation-output"),
    ("supervisor", "clayz-presentation-supervisor"),
)


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


def _rewrite_composite_markdown(text: str) -> str:
    """Rewrite plugin-relative stage guidance for one standalone Skill root."""

    rewritten = ROOT_RELATIVE_PATTERN.sub(r"\1/", text)
    rewritten = rewritten.replace(
        "../clayz-presentation-supervisor/references/",
        "../supervisor/references/",
    )
    rewritten = rewritten.replace("scripts/validate_plugin_mount.py", "scripts/validate_composite_skill_mount.py")
    rewritten = rewritten.replace("runtime/plugin-mount-contract.json", COMPOSITE_MOUNT_PATH)
    rewritten = rewritten.replace("complete plugin root", "complete composite Skill root")
    rewritten = rewritten.replace("plugin root", "composite Skill root")
    rewritten = rewritten.replace("All five Skills", "All five internal stage modules")
    rewritten = rewritten.replace("detached Skills", "detached or partial stage modules")
    rewritten = rewritten.replace("plugin-runtime-incomplete", "composite-skill-runtime-incomplete")
    handoffs = {
        "$clayz-presentation-logic": "the internal Logic module at `../logic/stage.md`",
        "$clayz-presentation-copy": "the internal Copy module at `../copy/stage.md`",
        "$clayz-presentation-art-direction": "the internal Art Direction module at `../art-direction/stage.md`",
        "$clayz-presentation-output": "the internal Output module at `../output/stage.md`",
        "$clayz-presentation-supervisor": "the internal Supervisor module at `../supervisor/stage.md`",
    }
    for source, target in handoffs.items():
        rewritten = rewritten.replace(source, target)
    return rewritten


def _composite_stage_files() -> list[tuple[str, bytes]]:
    files: list[tuple[str, bytes]] = []
    for stage_name, source_name in STAGE_SOURCES:
        source_root = ROOT / "skills" / source_name
        body = FRONTMATTER_PATTERN.sub("", (source_root / "SKILL.md").read_text(encoding="utf-8"), count=1)
        body = _rewrite_composite_markdown(body)
        files.append((f"references/stages/{stage_name}/stage.md", body.encode("utf-8")))
        reference_root = source_root / "references"
        if reference_root.is_dir():
            for path in sorted(reference_root.rglob("*")):
                if not path.is_file():
                    continue
                relative = path.relative_to(reference_root).as_posix()
                payload = path.read_bytes()
                if path.suffix.lower() == ".md":
                    payload = _rewrite_composite_markdown(path.read_text(encoding="utf-8")).encode("utf-8")
                files.append((f"references/stages/{stage_name}/references/{relative}", payload))
    return files


def _composite_skill_bytes(skill_name: str) -> bytes:
    text = COMPOSITE_TEMPLATE_PATH.read_text(encoding="utf-8")
    return text.replace("{{SKILL_NAME}}", skill_name).encode("utf-8")


def _composite_openai_yaml_bytes(skill_name: str) -> bytes:
    value = f'''interface:
  display_name: "Clayz Presentation Personal"
  short_description: "五阶段演示文稿制作、私人资料路由、环境预检与独立审计"
  icon_small: "./assets/clayz-mark.svg"
  icon_large: "./assets/clayz-mark.svg"
  brand_color: "#5B5BD6"
  default_prompt: "Use ${skill_name} to create an editable presentation through the five governed stages and deliver its supervision report."
policy:
  allow_implicit_invocation: true
'''
    return value.encode("utf-8")


def _composite_light_files() -> list[Path]:
    selected: list[Path] = []
    for path in _light_files():
        relative = path.relative_to(ROOT)
        if relative.parts[:1] == ("skills",):
            # Keep the original reference paths used by immutable public
            # Capability Index records, but never publish another SKILL.md.
            if len(relative.parts) >= 3 and relative.parts[2] == "references" and path.is_file():
                selected.append(path)
            continue
        if relative.as_posix() == ".codex-plugin/plugin.json":
            continue
        if path == COMPOSITE_TEMPLATE_PATH:
            continue
        selected.append(path)
    return selected


def compose_personal_light(
    profile_path: Path,
    provider_manifest_paths: Sequence[Path],
    output_path: Path,
    *,
    plugin_name: str = "clayz-presentation-personal",
    artifact_kind: str = COMPOSITE_ARTIFACT,
    wrap_directory: bool = False,
) -> Path:
    """Write a private cloud ZIP without private Library indexes or attachments.

    The default is one self-contained ChatGPT Skill with ``SKILL.md`` at the
    archive root. ``artifact_kind='plugin'`` retains the multi-Skill plugin
    package for plugin-marketplace hosts. ``wrap_directory`` applies only to
    the plugin form.
    """

    if not PLUGIN_NAME_PATTERN.fullmatch(plugin_name) or len(plugin_name) > 64:
        raise PersonalExtensionError("artifact name must be lower-case hyphen-case and at most 64 characters")
    if artifact_kind not in ARTIFACT_KINDS:
        raise PersonalExtensionError(f"artifact kind must be one of: {', '.join(ARTIFACT_KINDS)}")
    if artifact_kind == COMPOSITE_ARTIFACT and wrap_directory:
        raise PersonalExtensionError("standalone Skill archive must place SKILL.md at the ZIP root")
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
    provider_bindings = required_provider_bindings(runtime)
    runtime_lock = {
        "contract": "io.clayz.presentation.runtime-pack-lock/1.2",
        "plugin": plugin_name,
        "version": base_manifest["version"],
        "bundle": "cloud-personal-standalone-skill" if artifact_kind == COMPOSITE_ARTIFACT else "cloud-personal-composition",
        "base_bundle": "cloud-public-light",
        "public_core_sha256": public_core_digest(),
        "tool_boundary": "ChatGPT-host-provided",
        "dependency_payload": "no local dependency pack",
        "preflight": "scripts/runtime_preflight.py",
        "personal_extension_digest": runtime["lock"]["digest"],
        "resolved_config_digest": sha256_json(resolved_config),
        "required_provider_bindings": provider_bindings,
        "required_provider_set_sha256": sha256_json(provider_bindings),
    }
    if artifact_kind == COMPOSITE_ARTIFACT:
        stage_modules = [f"references/stages/{stage}/stage.md" for stage, _ in STAGE_SOURCES]
        required_paths = [
            "SKILL.md",
            "agents/openai.yaml",
            "assets/clayz-mark.svg",
            "config/default.json",
            *REQUIRED_PERSONAL_PATHS,
            "scripts/validate_composite_skill_mount.py",
            "scripts/runtime_preflight.py",
            "scripts/publish_supervised_pair.py",
            "scripts/validate_personal_extension.py",
            "scripts/materialize_owner_index.py",
            "scripts/finalize_resource_inventory.py",
            "packages/contracts/knowledge-learning.md",
            "packages/contracts/resource-inventory.schema.json",
            "packages/contracts/supervised-delivery-manifest.schema.json",
            "packages/validators/validate_supervision_report.py",
            *stage_modules,
            "references/stages/supervisor/references/resource-inventory-gate.md",
            "references/stages/supervisor/references/resource-inventory-gate.zh-CN.md",
            "references/stages/supervisor/references/supervision-contract.md",
            "references/stages/supervisor/references/supervision-contract.zh-CN.md",
        ]
        runtime_lock["skill_mount_contract"] = COMPOSITE_MOUNT_PATH
        runtime_lock["required_stage_modules"] = stage_modules
        mount_contract = {
            "contract": "io.clayz.presentation.composite-skill-mount/1.0",
            "skill": plugin_name,
            "archive_layout": "standalone-skill-root",
            "publication_unit": "single-skill",
            "single_public_core": True,
            "workflow_stages": [stage for stage, _ in STAGE_SOURCES],
            "stage_modules": stage_modules,
            "required_paths": required_paths,
            "failure_status": "composite-skill-runtime-incomplete",
        }
        mount_path = COMPOSITE_MOUNT_PATH
    else:
        required_paths = [
            *REQUIRED_SHARED_PATHS,
            *REQUIRED_PERSONAL_PATHS,
            *(f"skills/{name}/SKILL.md" for name in REQUIRED_SKILLS),
        ]
        runtime_lock["plugin_mount_contract"] = PLUGIN_MOUNT_PATH
        runtime_lock["required_shared_paths"] = list(REQUIRED_SHARED_PATHS)
        mount_contract = {
            "contract": "io.clayz.presentation.plugin-mount/1.0",
            "plugin": plugin_name,
            "archive_layout": "wrapped-directory" if wrap_directory else "plugin-root",
            "complete_plugin_required": True,
            "detached_skill_publication_forbidden": True,
            "required_paths": required_paths,
            "failure_status": "plugin-runtime-incomplete",
        }
        mount_path = PLUGIN_MOUNT_PATH

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prefix = f"{plugin_name}/" if wrap_directory else ""
    def target(relative: str) -> str:
        return f"{prefix}{PurePosixPath(relative).as_posix()}"

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        source_files = _composite_light_files() if artifact_kind == COMPOSITE_ARTIFACT else _light_files()
        for path in source_files:
            relative = path.relative_to(ROOT).as_posix()
            if relative == ".codex-plugin/plugin.json":
                continue
            _write_bytes(archive, target(relative), _personal_light_bytes(path))
        if artifact_kind == COMPOSITE_ARTIFACT:
            _write_bytes(archive, "SKILL.md", _composite_skill_bytes(plugin_name))
            _write_bytes(archive, "agents/openai.yaml", _composite_openai_yaml_bytes(plugin_name))
            for relative, payload in _composite_stage_files():
                _write_bytes(archive, relative, payload)
        else:
            _write_bytes(archive, target(".codex-plugin/plugin.json"), _json_bytes(plugin_manifest))
        _write_bytes(archive, target(PERSONAL_CONFIG_PATH), _json_bytes(resolved_config))
        _write_bytes(archive, target(PERSONAL_RUNTIME_PATH), _json_bytes(runtime))
        _write_bytes(archive, target("runtime/runtime-lock.json"), _json_bytes(runtime_lock))
        _write_bytes(archive, target(mount_path), _json_bytes(mount_contract))

    with zipfile.ZipFile(output_path) as archive:
        names = archive.namelist()
        for name in names:
            member = PurePosixPath(name)
            if member.is_absolute() or ".." in member.parts:
                output_path.unlink(missing_ok=True)
                raise PersonalExtensionError(f"unsafe archive member: {name}")
        required = {target(path) for path in required_paths}
        required.add(target(mount_path))
        if not required.issubset(names):
            output_path.unlink(missing_ok=True)
            missing = sorted(required - set(names))
            raise PersonalExtensionError(f"cloud personal archive is incomplete: {missing}")
        if artifact_kind == COMPOSITE_ARTIFACT:
            skill_files = sorted(name for name in names if PurePosixPath(name).name == "SKILL.md")
            if skill_files != ["SKILL.md"] or ".codex-plugin/plugin.json" in names:
                output_path.unlink(missing_ok=True)
                raise PersonalExtensionError("standalone Skill archive must contain exactly one root SKILL.md and no plugin manifest")
            if any(name.startswith("skills/") and PurePosixPath(name).name == "SKILL.md" for name in names):
                output_path.unlink(missing_ok=True)
                raise PersonalExtensionError("standalone Skill archive must not publish nested stage Skills")
        else:
            manifest_name = target(".codex-plugin/plugin.json")
            if not wrap_directory and manifest_name != ".codex-plugin/plugin.json":
                output_path.unlink(missing_ok=True)
                raise PersonalExtensionError("install-ready plugin archive must place plugin.json at the ZIP root")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path, help="Private Personal Extension Profile JSON")
    parser.add_argument("--provider-manifest", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--plugin-name", default="clayz-presentation-personal", help="Skill or plugin identifier")
    parser.add_argument("--artifact-kind", choices=ARTIFACT_KINDS, default=COMPOSITE_ARTIFACT)
    parser.add_argument("--wrap-directory", action="store_true", help="Wrap only the plugin form in one containing directory")
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    output = args.output or ROOT / "dist" / "private" / f"{args.plugin_name}-{version}-cloud-light.zip"
    try:
        path = compose_personal_light(
            args.profile,
            args.provider_manifest,
            output,
            plugin_name=args.plugin_name,
            artifact_kind=args.artifact_kind,
            wrap_directory=args.wrap_directory,
        )
        print(path)
        return 0
    except (OSError, json.JSONDecodeError, IndexRuntimeError, PersonalExtensionError, zipfile.BadZipFile) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
