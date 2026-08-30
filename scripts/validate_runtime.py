#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate runtime contracts, packs, adapters, bounded routes, and acceptance observations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.runtime.preflight import CONTRACT, MODEL_PROFILES, build_preflight_report  # noqa: E402


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    try:
        config = json.loads((root / "config" / "default.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"config parse failure: {exc}"]
    runtime = config.get("runtime", {})
    budgets = runtime.get("budgets", {})
    exact = {
        "maximum_capability_scans": 1,
        "maximum_source_collection_rounds": 1,
        "maximum_office_processes": 1,
        "maximum_repair_cycles": 1,
        "maximum_route_switches": 0,
        "maximum_fallback_restarts": 1,
    }
    for key, expected in exact.items():
        if budgets.get(key) != expected:
            errors.append(f"runtime.budgets.{key}: expected {expected}")
    if set(MODEL_PROFILES) != {"A", "B", "C", "D"}:
        errors.append("runtime model profiles must remain A-D")
    required_files = [
        "packages/contracts/runtime-preflight.schema.json",
        "packages/adapters/python_pptx/render.py",
        "packages/adapters/powerpoint_com/render.ps1",
        "packages/runtime/packs/common/runtime-pack.json",
        "packages/runtime/packs/windows/runtime-pack.json",
        "packages/runtime/packs/macos/runtime-pack.json",
        "packages/runtime/packs/linux/runtime-pack.json",
        "scripts/fetch_offline_wheels.py",
        "scripts/install_offline_dependencies.py",
        "scripts/verify_release_bundles.py",
        "release/offline-requirements-py312.txt",
        "provenance/OFFLINE_DEPENDENCY_NOTICES.md",
        "docs/release-packages.md",
        "docs/release-packages.zh-CN.md",
    ]
    for relative in required_files:
        if not (root / relative).is_file():
            errors.append(f"missing runtime file: {relative}")
    for name in ("common", "windows", "macos", "linux"):
        path = root / "packages" / "runtime" / "packs" / name / "runtime-pack.json"
        if not path.is_file():
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("contract") != "io.clayz.presentation.runtime-pack/1.0":
            errors.append(f"{path.relative_to(root)}: wrong contract")
        if name == "common" and value.get("distribution", {}).get("third_party_wheels_in_light_archive") is not False:
            errors.append("common runtime pack must keep the light archive free of third-party wheels")
        if name != "common" and value.get("offline_dependency_pack", {}).get("python") != "CPython 3.12":
            errors.append(f"{path.relative_to(root)}: offline pack must target CPython 3.12")
    try:
        report = build_preflight_report(config, model_profile="D", required_capabilities=["structured-spec"])
        if report.get("contract") != CONTRACT or report.get("selected_route", {}).get("locked") is not True:
            errors.append("runtime preflight did not emit a locked contract")
        if report.get("guards", {}).get("no_mid_run_backend_switch") is not True:
            errors.append("runtime preflight must forbid mid-run backend switching")
        if report.get("guards", {}).get("configured_capabilities_cannot_be_reduced") is not True:
            errors.append("runtime preflight must preserve every configured required capability")
        if report.get("guards", {}).get("host_capabilities_bound_to_run") is not True:
            errors.append("runtime preflight must bind host capabilities to the run")
        if not isinstance(report.get("run_binding"), dict) or not report["run_binding"].get("run_id"):
            errors.append("runtime preflight must bind a run_id")
        if not isinstance(report.get("config_binding"), dict) or not report["config_binding"].get("sha256"):
            errors.append("runtime preflight must bind the exact config")
        host_observation = report.get("dependencies", {}).get("host_tools", {}).get("observation", {})
        if host_observation.get("verification_status") != "runtime-probed":
            errors.append("runtime preflight must distinguish runtime probes from host declarations")
        if host_observation.get("route_eligible") is not False:
            errors.append("an absent or unverified host declaration must not authorize route readiness")
        if report.get("guards", {}).get("host_declarations_never_self_authorize_route_readiness") is not True:
            errors.append("runtime preflight must not let host declarations self-authorize route readiness")
        if report.get("guards", {}).get("run_challenge_has_nonce_and_freshness_window") is not True:
            errors.append("runtime preflight must require nonce and freshness semantics")
        if report.get("guards", {}).get("run_challenge_requires_issuance_and_canonical_consumption_ledgers") is not True:
            errors.append("runtime preflight must require issuance and canonical consumption ledgers")
        checks = report.get("target_application_checks")
        if not isinstance(checks, list) or not checks:
            errors.append("runtime preflight must observe every target application")
        elif any(item.get("blocks_authoring") is not False for item in checks if isinstance(item, dict)):
            errors.append("target-application acceptance must not block authoring")
    except (OSError, ValueError) as exc:
        errors.append(f"runtime preflight failure: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=ROOT)
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
