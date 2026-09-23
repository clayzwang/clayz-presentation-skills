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
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = ROOT / "packages" / "validators"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(VALIDATORS))

from packages.personal_extension import validate_personal_extension_runtime  # noqa: E402
from config_policy import load_policy  # noqa: E402
from acceptance_contract import acceptance_contract_digest  # noqa: E402
import validate_output_qa as output_qa_validator  # noqa: E402
from validate_supervision_report import (  # noqa: E402
    CALIBRATED_REPORT_REQUIRED_FIELDS,
    CONTRACT_VERSION,
    REPORT_REQUIRED_FIELDS,
    validate_report,
)
from stage_work_records import (  # noqa: E402
    CALIBRATION_STEPS,
    create_calibration_binding,
    create_calibration_record,
    create_record,
    validate_calibration_chain,
    validate_record,
    validate_records,
    STAGES,
)
from independent_audit import create_auditor_artifact  # noqa: E402
from work_report import (  # noqa: E402
    WorkReportError,
    attach_work_report,
    render_work_report_markdown,
    validate_work_report,
    verify_handoff as verify_work_report_handoff,
)


CONTRACT = "io.clayz.presentation.supervised-delivery-manifest/1.0"
REQUIRED_ROLES = ("pptx", "supervision-report")
DERIVED_ROLE = "work-report-markdown"
ASSEMBLY_CONTRACT = "io.clayz.presentation.supervision-assembly/1.0"
RUNTIME_MODES = {"owner-personal", "public-core", "unified"}
TASK_SELECTION_V2_CONTRACT = "io.clayz.presentation.task-resource-selection/2.0"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _file_record(path: Path) -> dict[str, Any]:
    path = path.resolve()
    data = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def _write_new(path: Path, value: dict[str, Any]) -> None:
    path = path.resolve()
    if path.is_relative_to(ROOT.resolve()):
        raise ValueError("work records and reports must be outside the installed Skill")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _calibrated_assembly(report: Mapping[str, Any], records: Any = None) -> bool:
    if any(key in report for key in ("auditor_artifact", "calibration_artifacts", "supervisor_release")):
        return True
    return isinstance(records, list) and any(
        isinstance(record, Mapping) and "calibration_bindings" in record for record in records
    )


def _calibration_input_names() -> tuple[str, ...]:
    return (
        "calibration_logic_copy",
        "calibration_copy_art_direction",
        "calibration_art_direction_output",
        "auditor",
        "task_request",
        "acceptance_contract",
        "supervisor_rules",
    )


def _calibrated_delivery_required(config: Mapping[str, Any]) -> bool:
    """Read the selected runtime policy; reports cannot opt themselves out."""

    workflow = config.get("workflow") if isinstance(config, Mapping) else None
    policy = workflow.get("delivery_policy") if isinstance(workflow, Mapping) else None
    return isinstance(policy, Mapping) and policy.get("mode") == "calibrated"


def _embed_auditor_observation(report: dict[str, Any]) -> dict[str, Any]:
    """Copy the independently produced result into the portable report."""

    reference = report.get("auditor_artifact")
    if not isinstance(reference, Mapping) or not isinstance(reference.get("path"), str):
        raise RuntimeError("calibrated report must bind an Auditor artifact before embedding its result")
    try:
        auditor = _read_object(Path(reference["path"]))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read bound Auditor artifact: {exc}") from exc
    result = {
        "audit_id": auditor.get("audit_id"),
        "audit_status": auditor.get("audit_status"),
        "findings": auditor.get("findings", []),
        "coverage": auditor.get("coverage", {}),
        "independent_context": auditor.get("independent_context", {}),
        "audited_at": auditor.get("audited_at"),
    }
    context = result.get("independent_context")
    if isinstance(context, Mapping):
        result["limitations"] = list(context.get("limitations", [])) if isinstance(context.get("limitations"), list) else []
    return {
        "auditor_result": result,
        "auditor_status": result["audit_status"],
        "auditor_findings": result["findings"],
        "auditor_coverage": result["coverage"],
        "auditor_limitations": result.get("limitations", []),
    }


def _derive_core_sequence(
    records: list[Mapping[str, Any]],
    calibrations: list[Mapping[str, Any]],
    auditor: Mapping[str, Any],
    auditor_artifact: Mapping[str, Any],
    release: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive a short process sequence from immutable records, without inventing UI events."""

    steps: list[dict[str, Any]] = [
        {"step": "supervision-started", "record_sha256": records[0].get("record_sha256")},
        {
            "step": "logic-to-copy-calibrated",
            "calibration_id": calibrations[0].get("calibration_id"),
            "record_sha256": calibrations[0].get("record_sha256"),
            "recipients": calibrations[0].get("recipients"),
        },
        {
            "step": "copy-to-art-direction-calibrated",
            "calibration_id": calibrations[1].get("calibration_id"),
            "record_sha256": calibrations[1].get("record_sha256"),
            "recipients": calibrations[1].get("recipients"),
        },
        {
            "step": "art-direction-to-output-calibrated",
            "calibration_id": calibrations[2].get("calibration_id"),
            "record_sha256": calibrations[2].get("record_sha256"),
            "recipients": calibrations[2].get("recipients"),
        },
        {
            "step": "independent-audit-completed",
            "audit_id": auditor.get("audit_id"),
            "artifact_sha256": auditor_artifact.get("sha256"),
            "audit_status": auditor.get("audit_status"),
        },
        {
            "step": "supervisor-release",
            "record_sha256": records[4].get("record_sha256"),
            "status": release.get("status"),
            "auditor_artifact_sha256": release.get("auditor_artifact_sha256"),
        },
    ]
    return {"contract": "io.clayz.presentation.calibrated-core-sequence/1.0", "steps": steps}


def _validate_assembly_acceptance_and_rules(
    inputs: Mapping[str, Any],
    package: Mapping[str, Any],
    plan: Mapping[str, Any],
    qa: Mapping[str, Any],
    report: Mapping[str, Any],
    calibrations: Sequence[Mapping[str, Any]],
    auditor: Mapping[str, Any],
) -> None:
    """Require every stage and calibration to use the current rule snapshots."""

    acceptance_path = Path(inputs["acceptance_contract"]["path"])
    acceptance = _read_object(acceptance_path)
    if acceptance != package.get("acceptance_contract") or acceptance != plan.get("acceptance_contract") or acceptance != qa.get("acceptance_contract") or acceptance != report.get("acceptance_contract"):
        raise ValueError("assembly acceptance contract bytes do not match package, plan, QA, and report")
    if acceptance.get("contract_sha256") != acceptance_contract_digest(acceptance):
        raise ValueError("assembly acceptance contract canonical hash is invalid")
    rules_meta = inputs["supervisor_rules"]
    acceptance_meta = inputs["acceptance_contract"]
    for index, calibration in enumerate(calibrations):
        if calibration.get("acceptance_contract") != acceptance_meta:
            raise ValueError(f"calibration {index + 1} does not bind the assembled acceptance contract")
        if calibration.get("shared_rules") != rules_meta:
            raise ValueError(f"calibration {index + 1} does not bind the assembled Supervisor rules")
    if auditor.get("acceptance_rules") != acceptance_meta:
        raise ValueError("Auditor acceptance_rules do not bind the assembled acceptance contract")
    if auditor.get("supervisor_rules") != rules_meta:
        raise ValueError("Auditor supervisor_rules do not bind the assembled Supervisor rules")


def validate_work_record_assembly(report: dict[str, Any], pptx: Path | None = None) -> None:
    records = report.get("work_records")
    validate_records(records, report.get("run_id"), report.get("task_request_sha256"))
    calibrated = _calibrated_assembly(report, records)
    assembly = report.get("assembly")
    if not isinstance(assembly, dict) or assembly.get("contract") != ASSEMBLY_CONTRACT:
        raise ValueError("report must be assembled from the five stage work records")
    if assembly.get("record_set_sha256") != _json_hash(records):
        raise ValueError("assembled work record set has changed")
    if assembly.get("report_content_sha256") != _json_hash({key: value for key, value in report.items() if key != "assembly"}):
        raise ValueError(
            "assembled report content has changed, including a calibration or independent Auditor binding"
            if calibrated else "assembled report content has changed"
        )
    inputs = assembly.get("inputs")
    required = {"package", "plan", "qa", "inventory", "pptx", "runtime_preflight", "config", "supervisor_draft"}
    if calibrated:
        required.update(_calibration_input_names())
    if not isinstance(inputs, dict) or set(inputs) != required:
        raise ValueError("assembly input file set is incomplete")
    for role, evidence in inputs.items():
        if not isinstance(evidence, dict) or _file_record(Path(evidence.get("path", ""))) != evidence:
            raise ValueError(f"assembly input bytes changed: {role}")
    draft = _read_object(Path(inputs["supervisor_draft"]["path"]))
    generated = {"contract_version", "status", "origin_namespace", "run_id", "task_request_sha256", "package_id",
                 "package_version", "art_direction_plan_contract_version", "output_qa_contract_version",
                 "acceptance_contract", "stage_snapshots", "work_records", "assembly",
                 "auditor_artifact", "calibration_artifacts", "supervisor_release", "workflow_contract",
                 "auditor_result", "auditor_status", "auditor_findings", "auditor_coverage", "auditor_limitations",
                 "core_sequence", "work_report", "work_report_sha256", "stage_documents", "design_comparison"}
    for key in (set(draft) | set(report)) - generated:
        if draft.get(key) != report.get(key):
            raise ValueError(f"supervisor finding differs from its recorded draft: {key}")
    expected_roles = [(1, "package", "package"), (2, "plan", "plan"),
                      (3, "qa", "qa"), (3, "inventory", "inventory"), (3, "pptx", "pptx"),
                      (4, "draft", "supervisor_draft"), (4, "pptx", "pptx")]
    if calibrated:
        expected_roles.append((4, "auditor", "auditor"))
    for index, role, input_role in expected_roles:
        if records[index]["artifacts"].get(role) != inputs[input_role]:
            raise ValueError(f"{records[index]['stage']} record does not bind current {role}")
    if not calibrated and not any(role.startswith("render") for role in records[3]["artifacts"]):
        raise ValueError("Output work record must bind actual render evidence")
    logic_evidence = records[0]["artifacts"].get("package")
    if not isinstance(logic_evidence, dict):
        raise ValueError("Logic work record must bind its immutable package")
    original_logic = _read_object(Path(logic_evidence["path"]))
    package = _read_object(Path(inputs["package"]["path"]))
    logic_keys = ("brief", "story") if package.get("contract_version") == "3.0" else ("brief", "logic_layer")
    if {k: original_logic.get(k) for k in logic_keys} != {k: package.get(k) for k in logic_keys}:
        raise ValueError("Copy package no longer matches the recorded Logic; revise dependent records")
    if package.get("contract_version") == "3.0":
        from story_handoff import build_stage_documents, embed_final_renders, timestamp
        if logic_evidence != package.get("logic_artifact"):
            raise ValueError("Copy must bind the actual recorded original Logic artifact")
        plan = _read_object(Path(inputs["plan"]["path"]))
        qa = _read_object(Path(inputs["qa"]["path"]))
        if report.get("stage_documents") != build_stage_documents(package, plan):
            raise ValueError("stage documents differ from actual recorded handoffs")
        # Materialization may add image bytes, never rewrite review observations.
        expected_comparison = json.loads(json.dumps(draft))
        embed_final_renders(expected_comparison)
        if report.get("design_comparison") != expected_comparison.get("design_comparison"):
            raise ValueError("design comparison differs from the Supervisor's recorded observations")
        lock_time = timestamp(plan["visual_baseline"]["locked_at"])
        start_time = timestamp(qa.get("output_started_at"))
        # Existing work records have second precision; compare at that precision
        # while validate_output_baseline checks the precise lock/start ordering.
        if not lock_time.replace(microsecond=0) <= timestamp(records[2]["recorded_at"]) <= start_time.replace(microsecond=0) <= timestamp(records[3]["recorded_at"]):
            raise ValueError("visual baseline must be recorded by Art Direction before Output starts")
    elif report.get("design_comparison") != draft.get("design_comparison") or report.get("stage_documents") != draft.get("stage_documents"):
        raise ValueError("legacy report cannot invent handoff extensions during assembly")
    if pptx is not None and sha256_file(pptx) != inputs["pptx"]["sha256"]:
        raise ValueError("final PPTX differs from the Output/Supervisor work records")
    if calibrated:
        if len(records) != 5:
            raise ValueError("calibrated assembly requires all five stage records")
        for record_index, step in zip((1, 2, 3), CALIBRATION_STEPS):
            bindings = records[record_index].get("calibration_bindings")
            if not isinstance(bindings, list) or len(bindings) != 1:
                raise ValueError(f"{records[record_index]['stage']} record must contain one {step['step']} calibration binding")
        calibration_paths = [inputs[name] for name in _calibration_input_names()[:3]]
        calibration_values = [_read_object(Path(item["path"])) for item in calibration_paths]
        validate_calibration_chain(
            calibration_values,
            report.get("run_id"),
            report.get("task_request_sha256"),
        )
        expected_steps = [item["step"] for item in CALIBRATION_STEPS]
        if [item.get("step") for item in calibration_values] != expected_steps:
            raise ValueError("calibration input files must follow Logic→Copy→Art Direction→Output order")
        if report.get("calibration_artifacts") != [
            {"step": value["step"], **inputs[name]} for value, name in zip(calibration_values, _calibration_input_names()[:3])
        ]:
            raise ValueError("report calibration_artifacts do not bind the assembled calibration bytes")
        if report.get("auditor_artifact") != inputs["auditor"]:
            raise ValueError("report auditor_artifact does not bind the assembled Auditor bytes")
        for record_index, calibration_value, input_name in zip((1, 2, 3), calibration_values, _calibration_input_names()[:3]):
            binding = records[record_index]["calibration_bindings"][0]
            if binding.get("calibration_artifact") != inputs[input_name]:
                raise ValueError(f"{records[record_index]['stage']} calibration binding does not match assembly bytes")
            if binding.get("calibration_id") != calibration_value.get("calibration_id"):
                raise ValueError(f"{records[record_index]['stage']} calibration binding id does not match assembly")
            if binding.get("record_sha256") != calibration_value.get("record_sha256"):
                raise ValueError(f"{records[record_index]['stage']} calibration binding record hash does not match assembly")
        auditor = _read_object(Path(inputs["auditor"]["path"]))
        source_rows = auditor.get("source_records") if isinstance(auditor, dict) else None
        by_kind = {
            row.get("kind"): row for row in source_rows if isinstance(row, dict)
        } if isinstance(source_rows, list) else {}
        for kind in ("package", "plan", "qa", "inventory"):
            if kind not in by_kind:
                raise ValueError(f"Auditor source_records must include real {kind} evidence")
            if by_kind[kind].get("path") != inputs[kind]["path"] or by_kind[kind].get("sha256") != inputs[kind]["sha256"] or by_kind[kind].get("bytes") != inputs[kind]["bytes"]:
                raise ValueError(f"Auditor source_records.{kind} must bind the assembled {kind} bytes")
        for key, input_name in (("task_request", "task_request"), ("acceptance_rules", "acceptance_contract"), ("supervisor_rules", "supervisor_rules")):
            if auditor.get(key) != inputs[input_name]:
                raise ValueError(f"Auditor {key} does not bind the assembled {input_name} bytes")
        package = _read_object(Path(inputs["package"]["path"]))
        plan = _read_object(Path(inputs["plan"]["path"]))
        qa = _read_object(Path(inputs["qa"]["path"]))
        _validate_assembly_acceptance_and_rules(inputs, package, plan, qa, report, calibration_values, auditor)
        expected_sequence = _derive_core_sequence(
            records,
            calibration_values,
            auditor,
            inputs["auditor"],
            report.get("supervisor_release", {}),
        )
        if report.get("core_sequence") != expected_sequence:
            raise ValueError("report core_sequence must be derived from the five records, calibrations, Auditor, and release")


def _records_required() -> bool:
    lock = ROOT / "runtime" / "runtime-lock.json"
    return lock.is_file() and _read_object(lock).get("stage_work_records_required") is True


def _record_commands(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Record stage work, assemble the full report, or verify a handoff bundle")
    commands = parser.add_subparsers(dest="command", required=True)
    record = commands.add_parser("record-stage")
    record.add_argument("--stage", required=True)
    record.add_argument("--draft", type=Path, required=True)
    record.add_argument("--challenge", type=Path, required=True)
    record.add_argument("--artifact", action="append", default=[])
    record.add_argument("--previous-record", type=Path)
    record.add_argument("--calibration", type=Path, help="current Supervisor calibration consumed by this stage")
    record.add_argument("--calibration-dispositions", type=Path, help="JSON array of per-finding accept/decline decisions")
    record.add_argument("--acceptance-contract", type=Path, help="current task acceptance contract bytes")
    record.add_argument("--output", type=Path, required=True)
    calibration = commands.add_parser("record-calibration")
    calibration.add_argument("--step", required=True, choices=[item["step"] for item in CALIBRATION_STEPS])
    calibration.add_argument("--source-record", type=Path, required=True)
    calibration.add_argument("--acceptance-contract", type=Path, required=True)
    calibration.add_argument("--shared-rules", type=Path, required=True)
    calibration.add_argument("--findings", type=Path, required=True, help="JSON array of Supervisor findings")
    calibration.add_argument("--challenge", type=Path, required=True)
    calibration.add_argument("--previous-calibration", type=Path)
    calibration.add_argument("--output", type=Path, required=True)
    audit = commands.add_parser("record-audit")
    audit.add_argument("--task-request", type=Path, required=True)
    audit.add_argument("--acceptance-rules", type=Path, required=True)
    audit.add_argument("--supervisor-rules", type=Path, required=True)
    audit.add_argument("--source-record", action="append", default=[])
    audit.add_argument("--expected-source-kind", action="append")
    audit.add_argument("--pptx", type=Path, required=True)
    audit.add_argument("--render-evidence", action="append", default=[])
    audit.add_argument("--coverage", type=Path, required=True)
    audit.add_argument("--findings", type=Path, required=True)
    audit.add_argument("--independent-context", type=Path, required=True)
    audit.add_argument("--challenge", type=Path, required=True)
    audit.add_argument("--audited-at")
    audit.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("check-records")
    check.add_argument("--record", action="append", type=Path, required=True)
    check.add_argument("--challenge", type=Path, required=True)
    assemble = commands.add_parser("assemble-report")
    assemble.add_argument("--record", action="append", type=Path, required=True)
    for name in ("draft", "package", "plan", "qa", "inventory", "pptx", "runtime-preflight", "config", "output"):
        assemble.add_argument("--" + name, type=Path, required=True)
    for name in _calibration_input_names():
        assemble.add_argument("--" + name.replace("_", "-"), type=Path)
    assemble.add_argument("--acceptance-rules", type=Path)
    assemble.add_argument("--render-root", type=Path)
    verify = commands.add_parser("verify-handoff")
    verify.add_argument("--bundle", type=Path, required=True)
    verify.add_argument("--pptx", type=Path)
    verify.add_argument("--report", type=Path)
    verify.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "check-records":
            challenge = _read_object(args.challenge)
            binding = challenge.get("run_binding", challenge)
            if not 1 <= len(args.record) <= 5:
                raise ValueError("handoff requires the complete available prefix of stage records")
            previous = None
            for stage, path in zip(STAGES, args.record):
                value = _read_object(path)
                if value.get("stage") != stage:
                    raise ValueError("handoff records must start at Logic and follow stage order")
                validate_record(value, binding.get("run_id"), binding.get("task_request_sha256"), previous, require_ready=True)
                previous = value
            print(json.dumps({"status": "handoff-verified", "records": len(args.record)}))
            return 0
        if args.command == "verify-handoff":
            receipt = verify_handoff(
                args.bundle,
                pptx=args.pptx,
                report=args.report,
                markdown=args.markdown,
            )
            print(json.dumps(receipt, ensure_ascii=False, indent=2))
            return 0
        if args.command == "record-stage":
            artifacts = {}
            for item in args.artifact:
                role, separator, path = item.partition("=")
                if not separator or not role or not path or role in artifacts:
                    raise ValueError("each artifact must have a unique ROLE=PATH")
                artifacts[role] = Path(path)
            calibration_bindings = None
            if args.calibration is not None:
                if args.calibration_dispositions is None:
                    raise ValueError("--calibration requires --calibration-dispositions")
                dispositions = json.loads(args.calibration_dispositions.read_text(encoding="utf-8"))
                if not isinstance(dispositions, list):
                    raise ValueError("--calibration-dispositions must contain a JSON array")
                calibration_bindings = [create_calibration_binding(args.calibration, dispositions)]
            result = create_record(
                args.stage,
                _read_object(args.draft),
                _read_object(args.challenge),
                artifacts,
                _read_object(args.previous_record) if args.previous_record else None,
                calibration_bindings=calibration_bindings,
                acceptance_contract=args.acceptance_contract,
            )
            _write_new(args.output, result)
            print(json.dumps({"status": "recorded", "stage": args.stage, "path": str(args.output)}))
            return 0
        if args.command == "record-calibration":
            findings = json.loads(args.findings.read_text(encoding="utf-8"))
            if not isinstance(findings, list):
                raise ValueError("--findings must contain a JSON array")
            previous = _read_object(args.previous_calibration) if args.previous_calibration else None
            result = create_calibration_record(
                args.step,
                args.source_record,
                args.acceptance_contract,
                args.shared_rules,
                findings,
                _read_object(args.challenge),
                output=args.output,
                previous_calibration=previous,
            )
            print(json.dumps({"status": "calibration-recorded", "step": args.step, "path": str(args.output)}))
            return 0
        if args.command == "record-audit":
            def _kind_paths(items: list[str], label: str) -> dict[str, Path]:
                result: dict[str, Path] = {}
                for item in items:
                    kind, separator, path = item.partition("=")
                    if not separator or not kind or not path or kind in result:
                        raise ValueError(f"{label} must use unique KIND=PATH values")
                    result[kind] = Path(path)
                return result

            challenge = _read_object(args.challenge)
            binding = challenge.get("run_binding", challenge)
            coverage = _read_object(args.coverage)
            findings = json.loads(args.findings.read_text(encoding="utf-8"))
            context = _read_object(args.independent_context)
            render = _kind_paths(args.render_evidence, "--render-evidence")
            sources = _kind_paths(args.source_record, "--source-record")
            expected = args.expected_source_kind
            if expected is not None and len(expected) != len(set(expected)):
                raise ValueError("--expected-source-kind values must be unique")
            create_auditor_artifact(
                task_request=args.task_request,
                acceptance_rules=args.acceptance_rules,
                supervisor_rules=args.supervisor_rules,
                source_records=sources,
                expected_source_kinds=expected,
                final_pptx=args.pptx,
                render_evidence=render,
                coverage=coverage,
                findings=findings,
                independent_context=context,
                run_id=binding.get("run_id"),
                task_request_sha256=binding.get("task_request_sha256"),
                output=args.output,
                audited_at=args.audited_at,
            )
            print(json.dumps({"status": "audit-recorded", "path": str(args.output)}))
            return 0
        if args.output.suffix.casefold() != ".json":
            raise ValueError("assemble-report output must use a .json suffix")
        records = [_read_object(path) for path in args.record]
        preflight = _read_object(args.runtime_preflight)
        binding = preflight.get("run_binding", {})
        validate_records(records, binding.get("run_id"), binding.get("task_request_sha256"))
        draft_value = _read_object(args.draft)
        configured_calibrated = _calibrated_delivery_required(_read_object(args.config))
        calibrated = configured_calibrated or _calibrated_assembly(draft_value, records)
        if configured_calibrated and not _calibrated_assembly(draft_value, records):
            raise ValueError("selected configuration requires a three-calibration independent-Auditor assembly")
        if calibrated:
            missing_inputs = [name for name in _calibration_input_names() if getattr(args, name) is None]
            if missing_inputs:
                raise ValueError("calibrated assembly requires: " + ", ".join("--" + item.replace("_", "-") for item in missing_inputs))
        package, plan, qa, inventory, config = [_read_object(path) for path in (args.package, args.plan, args.qa, args.inventory, args.config)]
        result = _read_object(args.draft)
        result.update(contract_version=CONTRACT_VERSION, status="supervised", origin_namespace="io.clayz.presentation",
                      run_id=binding.get("run_id"), task_request_sha256=binding.get("task_request_sha256"),
                      package_id=package.get("package_id"), package_version=package.get("version"),
                      art_direction_plan_contract_version=plan.get("contract_version"), output_qa_contract_version=qa.get("contract_version"),
                      acceptance_contract=package.get("acceptance_contract"))
        snapshots = {"logic": {"brief": package.get("brief"), "logic_layer": package.get("logic_layer")},
                     "copy": package.get("copy_layer"),
                     "art_direction": {k: plan.get(k) for k in ("communication_contract", "art_direction", "decision_log", "typography_contract", "deck_rhythm", "slides")}}
        result["stage_snapshots"] = {stage: {"artifact_sha256": sha256_file(args.plan if stage == "art_direction" else args.package),
                                                    "snapshot_sha256": _json_hash(snapshot), "snapshot": snapshot}
                                     for stage, snapshot in snapshots.items()}
        if package.get("contract_version") == "3.0":
            from story_handoff import build_stage_documents, embed_final_renders, load_logic_origin
            result["stage_documents"] = build_stage_documents(package, plan)
            embed_final_renders(result)
            original_logic = load_logic_origin(package)
            result["stage_snapshots"]["logic"] = {"artifact_sha256": package["logic_artifact"]["sha256"],
                "snapshot_sha256": _json_hash(original_logic), "snapshot": original_logic}
            result["stage_snapshots"]["art_direction"].update(snapshot=plan, snapshot_sha256=_json_hash(plan))
        result["work_records"] = records
        paths = {"package": args.package, "plan": args.plan, "qa": args.qa, "inventory": args.inventory,
                 "pptx": args.pptx, "runtime_preflight": args.runtime_preflight, "config": args.config, "supervisor_draft": args.draft}
        if calibrated:
            for name in _calibration_input_names():
                paths[name] = getattr(args, name)
            result["workflow_contract"] = "io.clayz.presentation.calibrated-audit/1.0"
            result["calibration_artifacts"] = [
                {"step": value["step"], **_file_record(getattr(args, name))}
                for value, name in zip(
                    [_read_object(getattr(args, name)) for name in _calibration_input_names()[:3]],
                    _calibration_input_names()[:3],
                )
            ]
            result["auditor_artifact"] = _file_record(args.auditor)
            result["core_sequence"] = _derive_core_sequence(
                records,
                [_read_object(getattr(args, name)) for name in _calibration_input_names()[:3]],
                _read_object(args.auditor),
                _file_record(args.auditor),
                result.get("supervisor_release", {}),
            )
        try:
            result = attach_work_report(
                result,
                artifacts=paths,
                records=records,
                record_paths=args.record,
                calibrations={
                    _read_object(getattr(args, name)).get("step", name): getattr(args, name)
                    for name in _calibration_input_names()[:3]
                } if calibrated else None,
                auditor=getattr(args, "auditor", None) if calibrated else None,
                pptx=args.pptx,
                task_request=getattr(args, "task_request", None) or paths.get("task_request"),
                acceptance_rules=getattr(args, "acceptance_rules", None) or paths.get("acceptance_contract"),
                supervisor_rules=getattr(args, "supervisor_rules", None) or paths.get("supervisor_rules"),
            )
        except WorkReportError as exc:
            raise ValueError(f"work_report collection failed: {exc}") from exc
        result["assembly"] = {"contract": ASSEMBLY_CONTRACT, "record_set_sha256": _json_hash(records),
                              "report_content_sha256": _json_hash({key: value for key, value in result.items() if key != "assembly"}),
                              "inputs": {role: _file_record(path) for role, path in paths.items()}}
        validate_work_record_assembly(result, args.pptx)
        work_report_errors = validate_work_report(result, pptx=args.pptx)
        if work_report_errors:
            raise ValueError("work_report validation failed:\n" + "\n".join(work_report_errors))
        required_report_fields = CALIBRATED_REPORT_REQUIRED_FIELDS if calibrated else REPORT_REQUIRED_FIELDS
        missing = sorted(required_report_fields - set(result))
        if missing:
            raise ValueError("Supervisor draft is incomplete; supply actual audit evidence for: " + ", ".join(missing))
        output_qa_validator.qa_path_parent = args.qa.resolve().parent
        errors = validate_report(package, plan, qa, inventory, result, load_policy(args.config),
                                 pptx=args.pptx, render_root=args.render_root, report_path=args.output,
                                 runtime_preflight=preflight, runtime_preflight_sha256=sha256_file(args.runtime_preflight),
                                 resolved_config=config, resolved_config_sha256=sha256_file(args.config),
                                 evidence_root=args.draft.resolve().parent)
        if errors:
            raise ValueError("full supervision validation failed:\n" + "\n".join(errors))
        _write_new(args.output, result)
        print(json.dumps({"status": "assembled-and-validated", "path": str(args.output), "records": 5}))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def build_manifest(
    report: dict[str, Any], pptx: Path, report_path: Path, markdown_path: Path | None = None,
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
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
    manifest["derived_files"] = []
    if markdown_path is not None:
        manifest["derived_files"].append(
            {
                "role": DERIVED_ROLE,
                "path": markdown_path.name,
                "sha256": sha256_file(markdown_path),
                "bytes": markdown_path.stat().st_size,
            }
        )
    if isinstance(report.get("stage_documents"), dict):
        companion = report_path.parent / "stage-handoff.zip"
        manifest["derived_files"].append({"role": "stage-handoff-archive", "path": companion.name,
                                          "sha256": sha256_file(companion), "bytes": companion.stat().st_size})
    return manifest


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
    derived = manifest.get("derived_files", [])
    if not isinstance(derived, list):
        errors.append("delivery manifest derived_files must be an array")
        derived = []
    derived_roles: list[str] = []
    for item in derived:
        if not isinstance(item, dict):
            errors.append("delivery manifest derived_files entries must be objects")
            continue
        role = item.get("role")
        if role not in {DERIVED_ROLE, "stage-handoff-archive"} or role in derived_roles:
            errors.append(f"unsupported or duplicate derived delivery role: {role}")
            continue
        derived_roles.append(role)
        raw_path = item.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            errors.append(f"published {role} path is missing")
            continue
        path = (bundle / raw_path).resolve()
        if not path.is_relative_to(bundle.resolve()):
            errors.append(f"published {role} path escapes bundle")
            continue
        expected_names.add(path.name)
        if not path.is_file():
            errors.append(f"missing published {role}: {path.name}")
            continue
        if sha256_file(path) != item.get("sha256"):
            errors.append(f"published {role} hash mismatch")
        if path.stat().st_size != item.get("bytes"):
            errors.append(f"published {role} byte count mismatch")
    try:
        report_record = next(item for item in records if item.get("role") == "supervision-report")
        report_value = _read_object(bundle / report_record["path"])
        if "stage_documents" in report_value:
            from story_handoff import handoff_archive_bytes
            if "stage-handoff-archive" not in derived_roles or (bundle / "stage-handoff.zip").read_bytes() != handoff_archive_bytes(report_value):
                errors.append("stage handoff companion must exactly derive from report")
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        errors.append(f"stage handoff companion: {exc}")
    actual_names = {item.name for item in bundle.iterdir() if item.is_file()}
    if actual_names != expected_names:
        errors.append(f"delivery bundle contains unexpected or missing files: {sorted(actual_names ^ expected_names)}")
    return errors


def verify_handoff(
    bundle: Path,
    *,
    pptx: Path | None = None,
    report: Path | None = None,
    markdown: Path | None = None,
) -> dict[str, Any]:
    """Verify a concrete 3.6 bundle and its complete immutable stage chain."""

    bundle = bundle.resolve()
    bundle_errors = validate_published_bundle(bundle)
    if bundle_errors:
        raise RuntimeError("handoff delivery-bundle validation failed:\n" + "\n".join(bundle_errors))
    receipt = verify_work_report_handoff(bundle, pptx=pptx, report=report, markdown=markdown)
    report_path = (report or bundle / str(next(
        item.get("path") for item in json.loads((bundle / "delivery-manifest.json").read_text(encoding="utf-8")).get("files", [])
        if isinstance(item, Mapping) and item.get("role") == "supervision-report"
    ))).resolve()
    report_value = _read_object(report_path)
    pptx_path = (pptx or bundle / str(next(
        item.get("path") for item in json.loads((bundle / "delivery-manifest.json").read_text(encoding="utf-8")).get("files", [])
        if isinstance(item, Mapping) and item.get("role") == "pptx"
    ))).resolve()
    if "work_records" not in report_value or "assembly" not in report_value:
        raise RuntimeError("verify-handoff requires a complete five-stage work-record assembly")
    try:
        validate_work_record_assembly(report_value, pptx_path)
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        raise RuntimeError(f"handoff work-record assembly validation failed: {exc}") from exc
    full_assembly: dict[str, Any] = {"status": "validated", "records": len(report_value.get("work_records", []))}
    receipt["full_assembly"] = full_assembly
    return receipt


def _resolve_bound_path(value: Any, *, base: Path = ROOT) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError("bound path must be a non-empty string")
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def _valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _unified_workflow_required() -> bool:
    lock_path = ROOT / "runtime" / "runtime-lock.json"
    if not lock_path.is_file():
        return False
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("runtime lock is not valid JSON") from exc
    if not isinstance(lock, Mapping):
        raise RuntimeError("runtime lock must be an object")
    return lock.get("unified_workflow_required") is True


def _validate_task_selected_runtime_binding(
    config_path: Path,
    resolved_config: dict[str, Any],
    runtime_preflight: Mapping[str, Any],
    *,
    runtime_mode: str,
    resolved_config_sha256: str | None,
) -> None:
    """Validate the task-selected config and its hash-bound selection before delivery."""

    binding = runtime_preflight.get("config_binding")
    if not isinstance(binding, Mapping) or binding.get("source") != "task-selected":
        raise RuntimeError("task-selected preflight must declare config_binding.source=task-selected")
    bound_config_path = _resolve_bound_path(binding.get("path"))
    selected_config_path = config_path.resolve()
    if bound_config_path != selected_config_path:
        raise RuntimeError("task-selected preflight config_binding.path does not match selected config")
    try:
        selected_config_raw = selected_config_path.read_bytes()
    except OSError as exc:
        raise RuntimeError("task-selected config file is missing") from exc
    selected_config_sha256 = hashlib.sha256(selected_config_raw).hexdigest()
    if binding.get("sha256") != selected_config_sha256:
        raise RuntimeError("task-selected preflight config_binding.sha256 does not match selected config bytes")
    if resolved_config_sha256 is not None and resolved_config_sha256 != selected_config_sha256:
        raise RuntimeError("selected config hash does not match the preflight config binding")
    try:
        selected_config_value = json.loads(selected_config_raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("task-selected config is not valid JSON") from exc
    if not isinstance(selected_config_value, dict) or selected_config_value != resolved_config:
        raise RuntimeError("selected config content does not match the config supplied for delivery")

    selection_path_value = binding.get("selection_path")
    selection_sha256 = binding.get("selection_sha256")
    if not isinstance(selection_path_value, str) or not selection_path_value.strip():
        raise RuntimeError("task-selected preflight must bind a selection path")
    if not _valid_sha256(selection_sha256):
        raise RuntimeError("task-selected preflight must bind a valid selection SHA-256")
    selection_path = _resolve_bound_path(selection_path_value)
    try:
        selection_raw = selection_path.read_bytes()
    except OSError as exc:
        raise RuntimeError("task selection file is missing") from exc
    if hashlib.sha256(selection_raw).hexdigest() != selection_sha256:
        raise RuntimeError("task-selected preflight selection SHA-256 does not match selection bytes")

    try:
        from packages.personal_extension.resolver import validate_task_selection

        selection = validate_task_selection(
            selection_path,
            selected_config_path,
            ROOT.resolve(),
            expected_mode=runtime_mode,
        )
    except (ImportError, OSError, KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(f"invalid task selection binding: {exc}") from exc
    if not isinstance(selection, Mapping):
        raise RuntimeError("task selection validator returned an invalid selection")
    if runtime_mode == "unified":
        if selection.get("contract") != TASK_SELECTION_V2_CONTRACT or selection.get("workflow") != "unified":
            raise RuntimeError("unified publication requires a task-resource-selection/2.0 unified selection")
        if "mode" in selection or "visual_source" in selection:
            raise RuntimeError("unified task selection must not declare legacy mode or visual_source")
    elif selection.get("mode") != runtime_mode:
        raise RuntimeError("task selection knowledge mode does not match the expected runtime mode")


def validate_personal_runtime_binding(
    config_path: Path,
    resolved_config: dict[str, Any],
    runtime_preflight: dict[str, Any],
    *,
    runtime_mode: str | None = None,
    resolved_config_sha256: str | None = None,
) -> None:
    if runtime_mode is None:
        runtime_mode = "owner-personal"
    if runtime_mode not in RUNTIME_MODES:
        raise RuntimeError(f"unsupported runtime mode: {runtime_mode}")
    if _unified_workflow_required() and runtime_mode != "unified":
        raise RuntimeError("current runtime requires unified package mode")
    config_binding = runtime_preflight.get("config_binding")
    if runtime_mode == "unified" and (
        not isinstance(config_binding, Mapping) or config_binding.get("source") != "task-selected"
    ):
        raise RuntimeError("unified publication requires config binding source task-selected")
    if isinstance(config_binding, Mapping) and config_binding.get("source") == "task-selected":
        _validate_task_selected_runtime_binding(
            config_path,
            resolved_config,
            runtime_preflight,
            runtime_mode=runtime_mode,
            resolved_config_sha256=resolved_config_sha256,
        )
        return
    if isinstance(config_binding, Mapping) and (
        "selection_path" in config_binding or "selection_sha256" in config_binding
    ):
        raise RuntimeError("selection pointer requires config binding source task-selected")
    runtime_path = ROOT / "runtime" / "personal-extension.json"
    if not runtime_path.is_file():
        return
    runtime_lock_path = ROOT / "runtime" / "runtime-lock.json"
    if not runtime_lock_path.is_file():
        raise RuntimeError("Personal Extension Runtime requires runtime/runtime-lock.json")
    try:
        runtime_pack_lock = json.loads(runtime_lock_path.read_text(encoding="utf-8"))
        if runtime_mode == "public-core":
            if not isinstance(runtime_pack_lock, dict):
                raise RuntimeError("runtime pack lock must be an object")
            expected_path = (ROOT / "config" / "default.json").resolve()
            if config_path.resolve() != expected_path:
                raise RuntimeError(f"public-core execution requires bundled config: {expected_path}")
            public_raw = expected_path.read_bytes()
            public_sha256 = hashlib.sha256(public_raw).hexdigest()
            artifact_hashes = runtime_pack_lock.get("artifact_sha256")
            if not isinstance(artifact_hashes, dict) or artifact_hashes.get("config/default.json") != public_sha256:
                raise RuntimeError("runtime pack lock must bind the exact bundled config/default.json hash")
            bundled_config = json.loads(public_raw)
            if not isinstance(bundled_config, dict) or bundled_config != resolved_config:
                raise RuntimeError("public-core config content does not match bundled config/default.json")
            if resolved_config_sha256 is not None and resolved_config_sha256 != public_sha256:
                raise RuntimeError("public-core config hash does not match bundled config/default.json")
            binding = runtime_preflight.get("config_binding")
            if not isinstance(binding, dict) or binding.get("source") != "public-default":
                raise RuntimeError("public preflight must declare config_binding.source=public-default")
            bound_path = Path(str(binding.get("path", "")))
            if not bound_path.is_absolute():
                bound_path = ROOT / bound_path
            if bound_path.resolve() != expected_path:
                raise RuntimeError("public preflight config_binding.path does not match bundled config/default.json")
            if binding.get("sha256") != public_sha256:
                raise RuntimeError("public preflight config_binding.sha256 does not match bundled config/default.json")
            return
        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
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


def _package_runtime_mode(package: Mapping[str, Any], runtime_mode: str | None = None) -> str:
    """Resolve one mode from the immutable package/index evidence surfaces."""

    declared: list[tuple[str, Any]] = []
    resource_inventory = package.get("resource_inventory")
    if isinstance(resource_inventory, Mapping) and "runtime_mode" in resource_inventory:
        declared.append(("package.resource_inventory.runtime_mode", resource_inventory.get("runtime_mode")))
    index_evidence = package.get("index_evidence")
    if isinstance(index_evidence, Mapping) and "mode" in index_evidence:
        declared.append(("package.index_evidence.mode", index_evidence.get("mode")))
    for label, value in declared:
        if not isinstance(value, str) or value not in RUNTIME_MODES:
            raise RuntimeError(f"{label} is not a supported runtime mode")
    values = {str(value) for _, value in declared}
    if len(values) > 1:
        raise RuntimeError("package resource inventory and index evidence select different runtime modes")
    if runtime_mode is not None:
        if runtime_mode not in RUNTIME_MODES:
            raise RuntimeError(f"unsupported runtime mode: {runtime_mode}")
        if values and values != {runtime_mode}:
            raise RuntimeError("caller runtime mode does not match package resource/index evidence")
        return runtime_mode
    return next(iter(values)) if values else "owner-personal"


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
    runtime_mode: str | None = None,
) -> dict[str, Any]:
    if output_dir.exists():
        raise RuntimeError(f"refusing to overwrite existing delivery directory: {output_dir}")
    if report_path.suffix.casefold() != ".json":
        raise RuntimeError("formal supervision report must use a .json suffix")
    if report.get("contract_version") == "3.6" and not isinstance(report.get("work_report"), Mapping):
        raise RuntimeError("3.6 publication requires an assembled work_report and derived Markdown")
    calibrated_required = _calibrated_delivery_required(resolved_config)
    if calibrated_required and not _calibrated_assembly(report):
        raise RuntimeError(
            "selected configuration requires calibrated delivery: three calibration artifacts and an independent Auditor are required"
        )
    if calibrated_required and ("work_records" not in report or "assembly" not in report):
        raise RuntimeError(
            "selected configuration requires an assembled five-stage work-record chain before publication"
        )
    if _calibrated_assembly(report) and report.get("contract_version") != CONTRACT_VERSION:
        raise RuntimeError(f"calibrated delivery requires supervision report contract {CONTRACT_VERSION}")
    if _records_required() or "work_records" in report or "assembly" in report:
        actual_report = _read_object(report_path)
        if actual_report != report:
            raise RuntimeError("report argument differs from the report file")
        validate_work_record_assembly(actual_report, pptx)
    runtime_mode = _package_runtime_mode(package, runtime_mode)
    if _unified_workflow_required() and runtime_mode != "unified":
        raise RuntimeError("current runtime requires unified package mode")
    if runtime_mode == "unified":
        resource_inventory = package.get("resource_inventory")
        index_evidence = package.get("index_evidence")
        if (
            not isinstance(resource_inventory, Mapping)
            or resource_inventory.get("runtime_mode") != "unified"
            or not isinstance(index_evidence, Mapping)
            or index_evidence.get("mode") != "unified"
        ):
            raise RuntimeError("unified publication requires resource_inventory and index_evidence mode unified")
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
    validate_personal_runtime_binding(
        config_path,
        resolved_config,
        runtime_preflight,
        runtime_mode=runtime_mode,
        resolved_config_sha256=resolved_config_sha256,
    )
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
        if _calibrated_assembly(staged_report_value):
            staged_report_value.update(_embed_auditor_observation(staged_report_value))
            if isinstance(staged_report_value.get("assembly"), dict):
                staged_report_value["assembly"]["report_content_sha256"] = _json_hash(
                    {key: value for key, value in staged_report_value.items() if key != "assembly"}
                )
            staged_report.write_text(
                json.dumps(staged_report_value, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        if _records_required() or "work_records" in staged_report_value:
            validate_work_record_assembly(staged_report_value, staged_pptx)
        staged_markdown: Path | None = None
        if isinstance(staged_report_value.get("stage_documents"), dict):
            from story_handoff import handoff_archive_bytes
            (staging / "stage-handoff.zip").write_bytes(handoff_archive_bytes(staged_report_value))
        if isinstance(staged_report_value.get("work_report"), Mapping):
            staged_markdown = staging / "work-report.md"
            staged_markdown.write_text(
                render_work_report_markdown(staged_report_value),
                encoding="utf-8",
                newline="\n",
            )
            work_report_errors = validate_work_report(
                staged_report_value,
                pptx=staged_pptx,
                markdown=staged_markdown,
            )
            if work_report_errors:
                raise RuntimeError("staged work-report validation failed:\n" + "\n".join(work_report_errors))
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
        manifest = build_manifest(staged_report_value, staged_pptx, staged_report, staged_markdown)
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
    if isinstance(published_report.get("work_report"), Mapping):
        published_markdown = output_dir / "work-report.md"
        work_report_errors = validate_work_report(
            published_report,
            pptx=published_pptx,
            markdown=published_markdown,
        )
        if work_report_errors:
            raise RuntimeError("published work-report validation failed:\n" + "\n".join(work_report_errors))
    return json.loads((output_dir / "delivery-manifest.json").read_text(encoding="utf-8"))


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in {"record-stage", "record-calibration", "record-audit", "check-records", "assemble-report", "verify-handoff"}:
        return _record_commands(sys.argv[1:])
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
        runtime_mode = _package_runtime_mode(package)
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
            runtime_mode=runtime_mode,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
