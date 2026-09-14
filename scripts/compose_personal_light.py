#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Attach one private profile and Library route to a ChatGPT cloud artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
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
from scripts.validate_config import validate as validate_config  # noqa: E402
from scripts.component_version_guard import component_dependency_paths  # noqa: E402
from scripts.validate_composite_skill_mount import inspect_composite_skill_mount  # noqa: E402
from scripts.validate_plugin_mount import REQUIRED_PERSONAL_PATHS, REQUIRED_SHARED_PATHS, REQUIRED_SKILLS  # noqa: E402


PLUGIN_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHOWCASE_IMAGE_PATTERN = re.compile(r"^!\[[^\]]*\]\(assets/showcase/[^)]+\)\s*$", re.MULTILINE)
FRONTMATTER_PATTERN = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.DOTALL)
ROOT_RELATIVE_PATTERN = re.compile(r"(?:\.\./)+(scripts|packages|config|runtime|docs|catalog|assets)/")
STAGE_LOCAL_REFERENCE_PATTERN = re.compile(r"(?<![A-Za-z0-9_./-])references/")
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
COMPOSITE_EXCLUDED_TOP_LEVEL = {
    ".github", ".gitattributes", ".gitignore", "CHANGELOG.md", "CITATION.cff",
    "CONTRIBUTING.md", "README.md", "README.zh-CN.md", "SECURITY.md",
    "knowledge", "provenance",
}
COMPOSITE_RUNTIME_SCRIPTS = {
    "cloud_learning_cli.py",
    "task_runtime.py",
    "bootstrap_owner_learning.py",
    "component_version_guard.py",
    "execution_ledger.py",
    "finalize_resource_inventory.py",
    "finalize_task_acceptance.py",
    "index_runtime_cli.py",
    "knowledge_cli.py",
    "materialize_owner_index.py",
    "publish_supervised_pair.py",
    "runtime_preflight.py",
    "stamp_pptx_metadata.py",
    "validate_composite_skill_mount.py",
    "validate_config.py",
    "validate_personal_extension.py",
    "validate_visual_regression_suite.py",
}
COMPOSITE_REQUIRED_DOCS = {
    "docs/layout-contracts.md",
    "docs/layout-contracts.zh-CN.md",
    "docs/pattern-dataset-library.md",
    "docs/pattern-dataset-library.zh-CN.md",
}
# Local inspection/tool listing depends on the local plugin layout. The shared
# knowledge modules run in cloud task scratch through a host-mediated bridge.
COMPOSITE_LOCAL_ONLY_FILES = {
    "config/tool-catalog.json",
    "packages/runtime/plugin_session.py",
}
# These schemas are read only by excluded repository benchmark/release checks.
# Keep them in Public Core source and local packs, not the execution-only cloud
# Skill. This preserves the upload budget without cutting callable dependencies.
COMPOSITE_DEVELOPMENT_SCHEMAS = {
    # These schemas are consumed only by repository/development validators;
    # standalone cloud execution uses the corresponding code contracts.
    "packages/contracts/artifact-envelope.schema.json",
    "packages/contracts/capability-resolution.schema.json",
    "packages/contracts/feedback-index-report.schema.json",
    "packages/contracts/learning-admission.schema.json",
    "packages/contracts/learning-record.schema.json",
    "packages/contracts/retrieval-benchmark.schema.json",
    "packages/contracts/retrieval-benchmark-report.schema.json",
    "packages/contracts/legacy-index-migration-report.schema.json",
    "packages/contracts/release-readiness.schema.json",
    "packages/contracts/chatgpt-release-acceptance.schema.json",
    "packages/contracts/runtime-preflight.schema.json",
    "packages/contracts/supervised-delivery-manifest.schema.json",
    "packages/contracts/work-report.schema.json",
    "packages/contracts/component-candidate-manifest.schema.json",
    # Read only by repository foundation/pattern validation, not runtime export code.
    "packages/contracts/metadata-dataset-export.schema.json",
}


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"


def _native_library_policy(runtime: Mapping[str, Any]) -> dict[str, Any]:
    roots = {mount["root"] for mount in runtime["mounts"] if mount.get("adapter") == "host-library"}
    if len(roots) != 1:
        raise PersonalExtensionError("native learning requires one unambiguous configured host Library root")
    return {
        "contract": "io.clayz.presentation.native-library-policy/1.0",
        "adapter": "host-library",
        "host_root": PurePosixPath(next(iter(roots)), "_extension", "confirmed-learning").as_posix(),
        "logical_root": "library://clayz-confirmed/",
        "provider_id": "clayz.owner-consensus",
    }


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


def _rewrite_composite_stage_markdown(text: str, source_name: str) -> str:
    """Route one internal stage module to the single retained source-reference tree."""

    rewritten = text.replace(
        "../clayz-presentation-supervisor/references/",
        "../../../skills/clayz-presentation-supervisor/references/",
    )
    rewritten = STAGE_LOCAL_REFERENCE_PATTERN.sub(
        f"../../../skills/{source_name}/references/",
        rewritten,
    )
    return _rewrite_composite_markdown(rewritten)


def _composite_stage_files() -> list[tuple[str, bytes]]:
    files: list[tuple[str, bytes]] = []
    for stage_name, source_name in STAGE_SOURCES:
        source_root = ROOT / "skills" / source_name
        body = FRONTMATTER_PATTERN.sub("", (source_root / "SKILL.md").read_text(encoding="utf-8"), count=1)
        body = _rewrite_composite_stage_markdown(body, source_name)
        files.append((f"references/stages/{stage_name}/stage.md", body.encode("utf-8")))
    return files


def _composite_skill_bytes(skill_name: str) -> bytes:
    text = COMPOSITE_TEMPLATE_PATH.read_text(encoding="utf-8")
    return text.replace("{{SKILL_NAME}}", skill_name).encode("utf-8")


def _composite_openai_yaml_bytes(skill_name: str) -> bytes:
    value = f'''interface:
  display_name: "Clayz Presentation Personal"
  short_description: "聊天与Work中的资源检查、讨论学习、原生Library入库与PPT制作"
  icon_small: "./assets/clayz-mark.svg"
  icon_large: "./assets/clayz-mark.svg"
  brand_color: "#5B5BD6"
  default_prompt: "Use ${skill_name} in this chat to inspect my Library, discuss and save confirmed knowledge, or create a presentation through the five governed stages."
policy:
  allow_implicit_invocation: true
'''
    return value.encode("utf-8")


def _catalog_knowledge_reference_paths() -> set[str]:
    references: set[str] = set()
    for line in (ROOT / "catalog" / "records.jsonl").read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        payload = record.get("payload") if isinstance(record, dict) else None
        ref = payload.get("ref") if isinstance(payload, dict) else None
        values = ref.get("knowledge_refs") if isinstance(ref, dict) else None
        if isinstance(values, list):
            references.update(str(value) for value in values)
    return references


def _include_stage_reference(path: Path, locale: str, catalog_references: set[str]) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    if relative in component_dependency_paths():
        return True
    if path.suffix.lower() != ".md":
        return True
    if locale == "en-US":
        return not path.name.endswith(".zh-CN.md")
    if locale == "zh-CN":
        if path.name.endswith(".zh-CN.md") or relative in catalog_references:
            return True
        localized = path.with_name(f"{path.stem}.zh-CN.md")
        return not localized.is_file()
    return True


def _composite_light_files(locale: str) -> list[Path]:
    selected: list[Path] = []
    catalog_references = _catalog_knowledge_reference_paths()
    for path in _light_files():
        relative = path.relative_to(ROOT)
        relative_posix = relative.as_posix()
        if relative_posix in COMPOSITE_LOCAL_ONLY_FILES | COMPOSITE_DEVELOPMENT_SCHEMAS:
            continue
        if relative.parts and relative.parts[0] in COMPOSITE_EXCLUDED_TOP_LEVEL:
            continue
        if relative.parts[:1] == ("scripts",) and path.name not in COMPOSITE_RUNTIME_SCRIPTS:
            continue
        if relative.parts[:1] == ("docs",) and relative_posix not in COMPOSITE_REQUIRED_DOCS:
            continue
        if relative.parts[:1] == ("catalog",) and path.name == "README.md":
            continue
        if relative.parts[:1] == ("skills",):
            # Keep the original reference paths used by immutable public
            # Capability Index records, but never publish another SKILL.md.
            if (
                len(relative.parts) >= 3
                and relative.parts[2] == "references"
                and path.is_file()
                and _include_stage_reference(path, locale, catalog_references)
            ):
                selected.append(path)
            continue
        if relative_posix == ".codex-plugin/plugin.json":
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
    candidate_manifest_path: Path | None = None,
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
    config_errors = validate_config(resolved_config)
    if config_errors:
        raise PersonalExtensionError(
            "resolved configuration failed validation: " + "; ".join(config_errors)
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
        "stage_work_records_required": True,
        "unified_workflow_required": True,
        "personal_extension_digest": runtime["lock"]["digest"],
        "resolved_config_digest": sha256_json(resolved_config),
        "required_provider_bindings": provider_bindings,
        "required_provider_set_sha256": sha256_json(provider_bindings),
    }
    candidate_manifest = None
    candidate_archive_path = "config/component-candidate-manifest.json"
    if candidate_manifest_path is not None:
        candidate_manifest = read_json(candidate_manifest_path.resolve())
        component_digest = hashlib.sha256((ROOT / "config" / "component-versions.json").read_bytes()).hexdigest()
        if (
            candidate_manifest.get("contract") != "io.clayz.presentation.component-candidate-manifest/1.0"
            or candidate_manifest.get("status") != "staged-candidate"
            or candidate_manifest.get("candidate_version") != base_manifest.get("version")
            or candidate_manifest.get("component_manifest_sha256") != component_digest
        ):
            raise PersonalExtensionError("candidate manifest does not bind this public-core candidate")
        runtime_lock["candidate_manifest_sha256"] = sha256_json(candidate_manifest)
    if artifact_kind == COMPOSITE_ARTIFACT:
        stage_modules = [f"references/stages/{stage}/stage.md" for stage, _ in STAGE_SOURCES]
        locale = resolved_config.get("locale", {}).get("default", "en-US")
        supervisor_suffix = ".zh-CN.md" if locale == "zh-CN" else ".md"
        required_paths = [
            "scripts/cloud_learning_cli.py",
            "packages/knowledge_session/__init__.py",
            "packages/knowledge_session/discussion.py",
            "packages/knowledge_session/store.py",
            "packages/contracts/native-library-workflow.md",
            "runtime/native-library-policy.json",
            *sorted(component_dependency_paths()),
            "SKILL.md",
            "agents/openai.yaml",
            "assets/clayz-mark.svg",
            "config/default.json",
            "config/component-versions.json",
            *REQUIRED_PERSONAL_PATHS,
            "scripts/validate_composite_skill_mount.py",
            "scripts/component_version_guard.py",
            "scripts/bootstrap_owner_learning.py",
            "scripts/runtime_preflight.py",
            "scripts/publish_supervised_pair.py",
            "scripts/validate_personal_extension.py",
            "scripts/materialize_owner_index.py",
            "scripts/finalize_resource_inventory.py",
            "packages/contracts/knowledge-learning.md",
            "packages/contracts/stage-enablement.md",
            "scripts/task_runtime.py",
            "packages/contracts/component-version-report.schema.json",
            "packages/contracts/version-private-learning-audit.schema.json",
            "packages/contracts/resource-inventory.schema.json",
            "packages/contracts/task-acceptance.schema.json",
            "packages/contracts/supervisor-calibration.schema.json",
            "packages/contracts/independent-audit.schema.json",
            "packages/validators/validate_supervision_report.py",
            "packages/validators/work_report.py",
            "packages/validators/stage_work_records.py",
            "packages/validators/independent_audit.py",
            "packages/validators/task_commitments.py",
            "packages/validators/acceptance_contract.py",
            "packages/validators/audit_ppt_font_names.py",
            *stage_modules,
            f"skills/clayz-presentation-supervisor/references/resource-inventory-gate{supervisor_suffix}",
            f"skills/clayz-presentation-supervisor/references/supervision-contract{supervisor_suffix}",
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

    if candidate_manifest is not None:
        required_paths.append(candidate_archive_path)

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prefix = f"{plugin_name}/" if wrap_directory else ""
    def target(relative: str) -> str:
        return f"{prefix}{PurePosixPath(relative).as_posix()}"

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        source_files = _composite_light_files(resolved_config.get("locale", {}).get("default", "en-US")) if artifact_kind == COMPOSITE_ARTIFACT else _light_files()
        for path in source_files:
            relative = path.relative_to(ROOT).as_posix()
            if relative == ".codex-plugin/plugin.json":
                continue
            _write_bytes(archive, target(relative), _personal_light_bytes(path))
        if artifact_kind == COMPOSITE_ARTIFACT:
            _write_bytes(archive, "SKILL.md", _composite_skill_bytes(plugin_name))
            _write_bytes(archive, "runtime/native-library-policy.json", _json_bytes(_native_library_policy(runtime)))
            _write_bytes(archive, "agents/openai.yaml", _composite_openai_yaml_bytes(plugin_name))
            for relative, payload in _composite_stage_files():
                _write_bytes(archive, relative, payload)
        else:
            _write_bytes(archive, target(".codex-plugin/plugin.json"), _json_bytes(plugin_manifest))
        _write_bytes(archive, target(PERSONAL_CONFIG_PATH), _json_bytes(resolved_config))
        _write_bytes(archive, target(PERSONAL_RUNTIME_PATH), _json_bytes(runtime))
        _write_bytes(archive, target("runtime/runtime-lock.json"), _json_bytes(runtime_lock))
        _write_bytes(archive, target(mount_path), _json_bytes(mount_contract))
        if candidate_manifest is not None:
            _write_bytes(archive, target(candidate_archive_path), _json_bytes(candidate_manifest))

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
    if artifact_kind == COMPOSITE_ARTIFACT:
        # Bind the exact delivered bytes (including compiled stage modules), not
        # merely the source tree. The lock excludes only itself.
        with zipfile.ZipFile(output_path) as archive:
            payloads = {name: archive.read(name) for name in archive.namelist()}
        runtime_lock["artifact_sha256"] = {
            name: hashlib.sha256(payload).hexdigest() for name, payload in sorted(payloads.items())
            if name != "runtime/runtime-lock.json"
        }
        payloads["runtime/runtime-lock.json"] = _json_bytes(runtime_lock)
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, payload in payloads.items():
                _write_bytes(archive, name, payload)
        with tempfile.TemporaryDirectory(prefix="clayz-final-package-") as directory:
            extracted = Path(directory)
            with zipfile.ZipFile(output_path) as archive:
                archive.extractall(extracted)
            report = inspect_composite_skill_mount(extracted, mode="archive")
            if not report["complete"]:
                output_path.unlink(missing_ok=True)
                raise PersonalExtensionError(f"final archive validation failed: {report['missing_paths']}; {report['errors']}")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path, help="Private Personal Extension Profile JSON")
    parser.add_argument("--provider-manifest", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--plugin-name", default="clayz-presentation-personal", help="Skill or plugin identifier")
    parser.add_argument("--artifact-kind", choices=ARTIFACT_KINDS, default=COMPOSITE_ARTIFACT)
    parser.add_argument("--wrap-directory", action="store_true", help="Wrap only the plugin form in one containing directory")
    parser.add_argument("--candidate-manifest", type=Path, help="Optional staged component manifest for pre-release ChatGPT acceptance")
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
            candidate_manifest_path=args.candidate_manifest,
        )
        print(path)
        return 0
    except (OSError, json.JSONDecodeError, IndexRuntimeError, PersonalExtensionError, zipfile.BadZipFile) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
