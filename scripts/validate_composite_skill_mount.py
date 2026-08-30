#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Verify a self-contained ChatGPT Skill generated from the Clayz Public Core."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


CONTRACT = "io.clayz.presentation.composite-skill-mount/1.0"
MOUNT_CONTRACT_PATH = Path("runtime/skill-mount-contract.json")


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


def inspect_composite_skill_mount(root: Path) -> dict[str, Any]:
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
    missing = [relative for relative in required if not (root / relative).is_file()]
    skill_files = sorted(path.relative_to(root).as_posix() for path in root.rglob("SKILL.md"))
    stage_modules = list(contract.get("stage_modules", [])) if contract else []
    errors: list[str] = []
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

    complete = not missing and not errors
    return {
        "contract": CONTRACT,
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
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    report = inspect_composite_skill_mount(args.root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
