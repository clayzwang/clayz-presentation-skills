#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate and atomically publish one PPTX plus its supervision report."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = ROOT / "packages" / "validators"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(VALIDATORS))

from packages.personal_extension import validate_personal_extension_runtime  # noqa: E402
from config_policy import load_policy  # noqa: E402
import validate_output_qa as output_qa_validator  # noqa: E402
from validate_supervision_report import CONTRACT_VERSION, validate_report  # noqa: E402


CONTRACT = "io.clayz.presentation.supervised-delivery-manifest/1.0"
REQUIRED_ROLES = ("pptx", "supervision-report")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest(report: dict[str, Any], pptx: Path, report_path: Path) -> dict[str, Any]:
    return {
        "contract": CONTRACT,
        "run_id": report["run_id"],
        "task_request_sha256": report["task_request_sha256"],
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "required_artifacts": list(REQUIRED_ROLES),
        "files": [
            {"role": "pptx", "path": pptx.name, "sha256": sha256_file(pptx), "bytes": pptx.stat().st_size},
            {
                "role": "supervision-report",
                "path": report_path.name,
                "sha256": sha256_file(report_path),
                "bytes": report_path.stat().st_size,
            },
        ],
        "validation": {
            "report_contract_version": CONTRACT_VERSION,
            "publisher": "scripts/publish_supervised_pair.py",
            "validated": True,
        },
    }


def validate_published_bundle(bundle: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = bundle / "delivery-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"delivery manifest parse failure: {exc}"]
    if manifest.get("contract") != CONTRACT:
        errors.append("delivery manifest contract mismatch")
    if manifest.get("required_artifacts") != list(REQUIRED_ROLES):
        errors.append("delivery manifest must require exactly PPTX and supervision-report")
    records = manifest.get("files")
    if not isinstance(records, list) or [item.get("role") for item in records if isinstance(item, dict)] != list(REQUIRED_ROLES):
        errors.append("delivery manifest file roles must be the fixed pair")
        return errors
    expected_names = {"delivery-manifest.json"}
    for item in records:
        path = bundle / str(item.get("path", ""))
        expected_names.add(path.name)
        if not path.is_file():
            errors.append(f"missing published {item.get('role')}: {path.name}")
            continue
        if sha256_file(path) != item.get("sha256"):
            errors.append(f"published {item.get('role')} hash mismatch")
        if path.stat().st_size != item.get("bytes"):
            errors.append(f"published {item.get('role')} byte count mismatch")
    actual_names = {item.name for item in bundle.iterdir() if item.is_file()}
    if actual_names != expected_names:
        errors.append(f"delivery bundle contains unexpected or missing files: {sorted(actual_names ^ expected_names)}")
    return errors


def validate_personal_runtime_binding(
    config_path: Path,
    resolved_config: dict[str, Any],
    runtime_preflight: dict[str, Any],
) -> None:
    """Fail closed when a composed Personal Skill is validated against another config."""

    runtime_path = ROOT / "runtime" / "personal-extension.json"
    if not runtime_path.is_file():
        return
    runtime_lock_path = ROOT / "runtime" / "runtime-lock.json"
    if not runtime_lock_path.is_file():
        raise RuntimeError("Personal Extension Runtime requires runtime/runtime-lock.json")
    try:
        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        runtime_pack_lock = json.loads(runtime_lock_path.read_text(encoding="utf-8"))
        validate_personal_extension_runtime(
            runtime,
            resolved_config=resolved_config,
            runtime_pack_lock=runtime_pack_lock,
        )
        expected_path = (ROOT / runtime["config"]["path"]).resolve()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(f"invalid Personal Extension Runtime binding: {exc}") from exc
    if config_path.resolve() != expected_path:
        raise RuntimeError(f"Personal Extension Runtime requires resolved config: {expected_path}")
    binding = runtime_preflight.get("config_binding")
    if not isinstance(binding, dict) or binding.get("source") != "personal-resolved":
        raise RuntimeError("personal preflight must declare config_binding.source=personal-resolved")
    bound_path = Path(str(binding.get("path", "")))
    if not bound_path.is_absolute():
        bound_path = ROOT / bound_path
    if bound_path.resolve() != expected_path:
        raise RuntimeError("personal preflight config_binding.path does not match Personal Extension Runtime")


def publish_supervised_pair(
    *,
    package: dict[str, Any],
    plan: dict[str, Any],
    qa: dict[str, Any],
    inventory: dict[str, Any],
    report: dict[str, Any],
    report_path: Path,
    pptx: Path,
    runtime_preflight: dict[str, Any],
    runtime_preflight_sha256: str,
    resolved_config: dict[str, Any],
    resolved_config_sha256: str,
    config_path: Path,
    output_dir: Path,
    render_root: Path | None = None,
) -> dict[str, Any]:
    if output_dir.exists():
        raise RuntimeError(f"refusing to overwrite existing delivery directory: {output_dir}")
    binding = runtime_preflight.get("run_binding")
    if not isinstance(binding, dict) or binding.get("binding_source") != "script-issued-challenge":
        raise RuntimeError("final publication requires a fresh script-issued run challenge")
    for key in ("task_root_sha256", "issuance_receipt_sha256", "consumption_receipt_sha256"):
        value = binding.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise RuntimeError(f"final publication requires a valid run binding {key}")
    try:
        expires = datetime.fromisoformat(str(binding["expires_at"]).replace("Z", "+00:00"))
    except (KeyError, ValueError) as exc:
        raise RuntimeError("run challenge expiry is invalid") from exc
    if expires.utcoffset() is None or datetime.now(timezone.utc) > expires.astimezone(timezone.utc):
        raise RuntimeError("run challenge expired before final publication")
    validate_personal_runtime_binding(config_path, resolved_config, runtime_preflight)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{output_dir.name}-", dir=output_dir.parent) as temporary:
        staging = Path(temporary) / "bundle"
        staging.mkdir()
        staged_pptx = staging / pptx.name
        staged_report = staging / report_path.name
        shutil.copy2(pptx, staged_pptx)
        shutil.copy2(report_path, staged_report)
        try:
            staged_report_value = json.loads(staged_report.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"staged supervision report parse failure: {exc}") from exc
        errors = validate_report(
            package,
            plan,
            qa,
            inventory,
            staged_report_value,
            load_policy(config_path),
            pptx=staged_pptx,
            render_root=render_root,
            report_path=staged_report,
            runtime_preflight=runtime_preflight,
            runtime_preflight_sha256=runtime_preflight_sha256,
            resolved_config=resolved_config,
            resolved_config_sha256=resolved_config_sha256,
            evidence_root=report_path.resolve().parent,
        )
        if errors:
            raise RuntimeError("staged supervision validation failed:\n" + "\n".join(errors))
        manifest = build_manifest(staged_report_value, staged_pptx, staged_report)
        (staging / "delivery-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        errors = validate_published_bundle(staging)
        if errors:
            raise RuntimeError("staged delivery validation failed:\n" + "\n".join(errors))
        os.replace(staging, output_dir)

    errors = validate_published_bundle(output_dir)
    if errors:
        raise RuntimeError("published delivery validation failed:\n" + "\n".join(errors))
    published_pptx = output_dir / pptx.name
    published_report_path = output_dir / report_path.name
    try:
        published_report = json.loads(published_report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"published supervision report parse failure: {exc}") from exc
    errors = validate_report(
        package,
        plan,
        qa,
        inventory,
        published_report,
        load_policy(config_path),
        pptx=published_pptx,
        render_root=render_root,
        report_path=published_report_path,
        runtime_preflight=runtime_preflight,
        runtime_preflight_sha256=runtime_preflight_sha256,
        resolved_config=resolved_config,
        resolved_config_sha256=resolved_config_sha256,
        evidence_root=report_path.resolve().parent,
    )
    if errors:
        raise RuntimeError("published supervision semantic validation failed:\n" + "\n".join(errors))
    return json.loads((output_dir / "delivery-manifest.json").read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("qa", type=Path)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--pptx", type=Path, required=True)
    parser.add_argument("--runtime-preflight", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--render-root", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        package, plan, qa, inventory, report = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in (args.package, args.plan, args.qa, args.inventory, args.report)
        ]
        runtime_raw = args.runtime_preflight.read_bytes()
        runtime_preflight = json.loads(runtime_raw)
        config_raw = args.config.read_bytes()
        resolved_config = json.loads(config_raw)
        output_qa_validator.qa_path_parent = args.qa.resolve().parent
        manifest = publish_supervised_pair(
            package=package,
            plan=plan,
            qa=qa,
            inventory=inventory,
            report=report,
            report_path=args.report,
            pptx=args.pptx,
            runtime_preflight=runtime_preflight,
            runtime_preflight_sha256=hashlib.sha256(runtime_raw).hexdigest(),
            resolved_config=resolved_config,
            resolved_config_sha256=hashlib.sha256(config_raw).hexdigest(),
            config_path=args.config,
            output_dir=args.output_dir,
            render_root=args.render_root,
        )
    except (OSError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
