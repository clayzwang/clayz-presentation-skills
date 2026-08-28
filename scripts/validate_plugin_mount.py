#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Verify that a Clayz presentation plugin was mounted as a complete plugin root."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = "io.clayz.presentation.plugin-mount/1.0"
REQUIRED_SKILLS = (
    "clayz-presentation-logic",
    "clayz-presentation-copy",
    "clayz-presentation-art-direction",
    "clayz-presentation-output",
    "clayz-presentation-supervisor",
)
REQUIRED_SHARED_PATHS = (
    ".codex-plugin/plugin.json",
    "config/default.json",
    "scripts/runtime_preflight.py",
    "scripts/validate_personal_extension.py",
    "scripts/validate_plugin_mount.py",
    "scripts/materialize_owner_index.py",
    "scripts/validate_index_regression_gates.py",
    "scripts/finalize_resource_inventory.py",
    "scripts/validate_resource_inventory_regression.py",
    "packages/contracts/knowledge-learning.md",
    "packages/contracts/index-execution-evidence.schema.json",
    "packages/contracts/resource-inventory.schema.json",
    "packages/validators/index_evidence.py",
    "packages/validators/resource_inventory.py",
    "packages/layout/compile_layout_contract.py",
    "packages/layout/solve_relative_layout.py",
    "packages/validators/validate_output_qa.py",
    "packages/validators/validate_supervision_report.py",
    "skills/clayz-presentation-supervisor/references/resource-inventory-gate.md",
    "skills/clayz-presentation-supervisor/references/resource-inventory-gate.zh-CN.md",
)
REQUIRED_PERSONAL_PATHS = (
    "config/personal-extension-resolved.json",
    "runtime/personal-extension.json",
    "runtime/runtime-lock.json",
)


def inspect_plugin_mount(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = root / ".codex-plugin" / "plugin.json"
    plugin_name = None
    manifest_error = None
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            plugin_name = manifest.get("name")
        except (OSError, json.JSONDecodeError) as exc:
            manifest_error = str(exc)

    required = list(REQUIRED_SHARED_PATHS)
    if isinstance(plugin_name, str) and plugin_name.endswith("-personal"):
        required.extend(REQUIRED_PERSONAL_PATHS)
    required.extend(f"skills/{name}/SKILL.md" for name in REQUIRED_SKILLS)
    missing = [relative for relative in required if not (root / relative).is_file()]
    if manifest_error:
        missing.append(".codex-plugin/plugin.json#invalid-json")
    return {
        "contract": CONTRACT,
        "plugin": plugin_name,
        "root": str(root),
        "complete": not missing,
        "status": "complete" if not missing else "plugin-runtime-incomplete",
        "required_paths": required,
        "missing_paths": missing,
        "skill_count": sum((root / "skills" / name / "SKILL.md").is_file() for name in REQUIRED_SKILLS),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    report = inspect_plugin_mount(args.root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
