#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Verify a self-contained ChatGPT Skill generated from the Clayz Public Core."""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.component_version_guard import _collect_actual, component_dependency_paths, VersionGuardError


CONTRACT = "io.clayz.presentation.composite-skill-mount/1.0"
MOUNT_CONTRACT_PATH = Path("runtime/skill-mount-contract.json")
# The ChatGPT editor demonstrably reserializes this YAML, changes its icon
# paths and adds products. These UI files are not presentation runtime inputs.
HOST_UI_PATHS = {"agents/openai.yaml", "assets/icon.svg"}


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _required_provider_bindings(runtime: dict[str, Any]) -> list[dict[str, Any]]:
    providers = runtime.get("providers")
    if not isinstance(providers, list):
        raise ValueError("runtime.providers must be an array")
    bindings = []
    for provider in providers:
        if not isinstance(provider, dict):
            raise ValueError("runtime provider must be an object")
        if provider.get("required") is not True:
            continue
        bindings.append({
            "provider_id": provider.get("provider_id"),
            "visibility": provider.get("visibility"),
            "manifest_uri": provider.get("manifest_uri"),
            "mount_id": provider.get("mount_id"),
            "stages": provider.get("stages"),
            "snapshot_policy": provider.get("snapshot_policy"),
        })
    return sorted(bindings, key=lambda item: str(item.get("provider_id")))


def _validate_personal_lock_surface(root: Path) -> list[str]:
    errors: list[str] = []
    try:
        runtime = json.loads((root / "runtime" / "personal-extension.json").read_text(encoding="utf-8"))
        runtime_lock = json.loads((root / "runtime" / "runtime-lock.json").read_text(encoding="utf-8"))
        config = json.loads((root / "config" / "personal-extension-resolved.json").read_text(encoding="utf-8"))
        unlocked = copy.deepcopy(runtime)
        embedded_lock = unlocked.pop("lock")
        bindings = _required_provider_bindings(runtime)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return [f"personal-runtime-lock#invalid:{exc}"]
    if embedded_lock.get("digest") != _sha256_json(unlocked):
        errors.append("personal-runtime-lock#embedded-digest-mismatch")
    if runtime_lock.get("contract") != "io.clayz.presentation.runtime-pack-lock/1.2":
        errors.append("personal-runtime-lock#wrong-pack-lock-contract")
    if runtime_lock.get("personal_extension_digest") != embedded_lock.get("digest"):
        errors.append("personal-runtime-lock#extension-digest-mismatch")
    if runtime_lock.get("resolved_config_digest") != _sha256_json(config):
        errors.append("personal-runtime-lock#resolved-config-digest-mismatch")
    if runtime.get("config", {}).get("sha256") != _sha256_json(config):
        errors.append("personal-runtime-lock#runtime-config-digest-mismatch")
    if runtime_lock.get("required_provider_bindings") != bindings:
        errors.append("personal-runtime-lock#required-provider-bindings-mismatch")
    if runtime_lock.get("required_provider_set_sha256") != _sha256_json(bindings):
        errors.append("personal-runtime-lock#required-provider-set-digest-mismatch")
    return errors


def inspect_composite_skill_mount(root: Path, *, mode: str = "installed") -> dict[str, Any]:
    if mode not in {"archive", "installed"}:
        raise ValueError("mode must be archive or installed")
    root = root.resolve()
    contract_path = root / MOUNT_CONTRACT_PATH
    contract: dict[str, Any] | None = None
    contract_error = None
    if contract_path.is_file():
        try:
            loaded = json.loads(contract_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                contract = loaded
            else:
                contract_error = "mount contract must be a JSON object"
        except (OSError, json.JSONDecodeError) as exc:
            contract_error = str(exc)

    required = list(contract.get("required_paths", [])) if contract else []
    # Independent of the generated short manifest: cannot hide a component by
    # omitting its path from required_paths.
    required = sorted(set(required) | component_dependency_paths())
    if mode == "installed":
        required = [relative for relative in required if relative not in HOST_UI_PATHS]
    missing = [relative for relative in required if not (root / relative).is_file()]
    skill_files = sorted(path.relative_to(root).as_posix() for path in root.rglob("SKILL.md"))
    stage_modules = list(contract.get("stage_modules", [])) if contract else []
    errors: list[str] = []
    host_observations: list[dict[str, Any]] = []
    if contract is None:
        errors.append("runtime/skill-mount-contract.json#missing-or-invalid")
    else:
        if contract.get("contract") != CONTRACT:
            errors.append("runtime/skill-mount-contract.json#wrong-contract")
        if contract.get("archive_layout") != "standalone-skill-root":
            errors.append("runtime/skill-mount-contract.json#wrong-layout")
        if contract.get("publication_unit") != "single-skill":
            errors.append("runtime/skill-mount-contract.json#wrong-publication-unit")
    if contract_error:
        errors.append(f"runtime/skill-mount-contract.json#invalid-json:{contract_error}")
    # Check local Python imports without importing optional host dependencies.
    for source in root.rglob("*.py"):
        try:
            tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
            for node in ast.walk(tree):
                modules: list[Path] = []
                if isinstance(node, ast.Import):
                    modules = [root.joinpath(*alias.name.split(".")) for alias in node.names
                               if alias.name.split(".")[0] in {"scripts", "packages"}]
                elif isinstance(node, ast.ImportFrom):
                    if node.level:
                        parent = source.parent
                        for _ in range(node.level - 1):
                            parent = parent.parent
                        modules = [parent.joinpath(*(node.module or "").split("."))]
                    elif node.module and node.module.split(".")[0] in {"scripts", "packages"}:
                        modules = [root.joinpath(*node.module.split("."))]
                for module in modules:
                    if not module.resolve().is_relative_to(root) or not (module.is_dir() or module.with_suffix(".py").is_file()):
                        errors.append(f"python-dependency#missing:{source.relative_to(root)}:{module}")
        except (OSError, SyntaxError, UnicodeError) as exc:
            errors.append(f"python-dependency#invalid:{source.relative_to(root)}:{exc}")
    try:
        for line in (root / "catalog/records.jsonl").read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            ref = record.get("payload", {}).get("ref", {})
            references = [item for key in ("knowledge_refs", "validator_refs") for item in ref.get(key, [])] if isinstance(ref, dict) else []
            for relative in references:
                target = (root / relative).resolve()
                if not target.is_relative_to(root) or not target.is_file():
                    errors.append(f"catalog-dependency#missing-or-unsafe:{relative}")
    except (OSError, ValueError, AttributeError, TypeError) as exc:
        errors.append(f"catalog-dependency#invalid:{exc}")
    if skill_files != ["SKILL.md"]:
        errors.append("skill-tree#must-contain-exactly-one-root-SKILL.md")
    if len(stage_modules) != 5 or len(set(stage_modules)) != 5:
        errors.append("stage-modules#must-contain-five-unique-modules")
    if (root / ".codex-plugin" / "plugin.json").exists():
        errors.append("plugin-manifest#forbidden-in-standalone-skill")
    if any((root / relative).name == "SKILL.md" for relative in stage_modules):
        errors.append("stage-modules#nested-SKILL.md-forbidden")
    if not any(relative in missing for relative in (
        "runtime/personal-extension.json",
        "runtime/runtime-lock.json",
        "config/personal-extension-resolved.json",
    )):
        errors.extend(_validate_personal_lock_surface(root))

    try:
        actual, _ = _collect_actual(root)
        expected = json.loads((root / "config/component-versions.json").read_text(encoding="utf-8"))["components"]
        if actual != expected:
            errors.append("component-versions#mounted-components-do-not-match-manifest")
    except (OSError, ValueError, KeyError, VersionGuardError) as exc:
        errors.append(f"component-versions#unreadable:{exc}")
    try:
        lock = json.loads((root / "runtime/runtime-lock.json").read_text(encoding="utf-8"))
        hashes = lock.get("artifact_sha256")
        if not isinstance(hashes, dict) or not hashes:
            errors.append("artifact-lock#missing-file-hashes")
        else:
            files = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
                     and "__pycache__" not in p.parts and p.relative_to(root).as_posix() != "runtime/runtime-lock.json"}
            missing_files = sorted(set(hashes) - files)
            extra_files = sorted(files - set(hashes))
            if mode == "archive" and (missing_files or extra_files):
                errors.append(f"artifact-lock#file-set-mismatch:missing={missing_files};extra={extra_files}")
            elif extra_files:
                host_observations.append({"kind": "untracked-installed-files", "paths": extra_files,
                                          "used_as_runtime_authority": False})
            for relative in required:
                if relative != "runtime/runtime-lock.json" and relative not in hashes:
                    errors.append(f"artifact-lock#required-file-unbound:{relative}")
            for relative, expected_hash in hashes.items():
                target = (root / relative).resolve()
                if mode == "installed" and relative in HOST_UI_PATHS:
                    actual_hash = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
                    if actual_hash != expected_hash:
                        host_observations.append({"kind": "host-ui-metadata-changed", "path": relative,
                                                  "source_sha256": expected_hash, "installed_sha256": actual_hash,
                                                  "used_as_runtime_authority": False})
                    continue
                if not target.is_relative_to(root) or not target.is_file():
                    errors.append(f"artifact-lock#missing-or-unsafe:{relative}")
                elif hashlib.sha256(target.read_bytes()).hexdigest() != expected_hash:
                    errors.append(f"artifact-lock#hash-mismatch:{relative}")
        candidate_path = root / "config/component-candidate-manifest.json"
        if candidate_path.is_file():
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            if lock.get("candidate_manifest_sha256") != _sha256_json(candidate):
                errors.append("candidate-lock#manifest-mismatch")
            if candidate.get("component_manifest_sha256") != hashlib.sha256((root / "config/component-versions.json").read_bytes()).hexdigest():
                errors.append("candidate-lock#component-manifest-mismatch")
    except (OSError, ValueError, TypeError) as exc:
        errors.append(f"artifact-lock#invalid:{exc}")

    complete = not missing and not errors
    return {
        "contract": CONTRACT,
        "validation_mode": mode,
        "skill": contract.get("skill") if contract else None,
        "root": str(root),
        "archive_layout": contract.get("archive_layout") if contract else None,
        "publication_unit": contract.get("publication_unit") if contract else None,
        "complete": complete,
        "status": "complete" if complete else "composite-skill-runtime-incomplete",
        "required_paths": required,
        "missing_paths": missing,
        "skill_files": skill_files,
        "stage_modules": stage_modules,
        "errors": errors,
        "host_observations": host_observations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--mode", choices=("archive", "installed"), default="installed")
    args = parser.parse_args()
    report = inspect_composite_skill_mount(args.root, mode=args.mode)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
