#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate a PPT supervision report and enforce deterministic cross-layer findings."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from config_policy import ValidationPolicy, load_policy
from index_evidence import index_lock_signature, validate_index_evidence
from resource_inventory import resource_inventory_signature, validate_resource_usage
import validate_output_qa as output_qa_validator

CONTRACT_VERSION = "3.3"
RUN_STATUS = {"clean", "complete-with-deferred-acceptance", "issues-found", "incomplete-evidence"}
CHECK_STATUS = {"pass", "fail", "not-applicable", "uncertain"}
TARGET_AVAILABILITY = {"available", "unavailable"}
TARGET_FINAL_STATUS = {"pass", "fail", "deferred", "not-selected"}
CHECK_KEYS = {
    "logic_copy_fidelity", "copy_art_direction_fidelity", "art_direction_build_fidelity",
    "art_direction_first_visual_fidelity", "art_direction_area_plan_fidelity",
    "plan_object_fidelity", "object_render_fidelity", "art_direction_rhythm_fidelity",
    "purposeful_series_fidelity", "cross_slide_invariant_fidelity",
    "semantic_whitespace_fidelity", "motif_fidelity", "context_rail_fidelity",
    "deviation_authorization", "qa_truthfulness", "anti_cardification",
    "target_app_compatibility", "inherited_chrome_fidelity",
    "typography_legibility", "scatter_semantics_and_labels",
    "semantic_layout_tree_fidelity", "visual_self_correction_integrity",
}
MEDIA_LABELS = {
    "typography", "data-chart", "table", "timeline", "swimlane", "matrix",
    "relationship-diagram", "process", "photo-or-screenshot",
    "scenario-illustration", "cards", "columns", "mixed", "other", "not-reviewed",
}
SEVERITIES = {"critical", "major", "moderate", "minor"}
OWNERS = {"logic", "copy", "art-direction", "output-build", "output-qa", "interface", "system"}
CONFIDENCE = {"high", "medium", "low"}
REQUIRED_INVENTORY = {
    "shapes", "text_shapes", "connectors", "pictures", "graphic_frames", "tables", "charts", "diagrams"
}
OBJECT_INVENTORY_MAP = {
    "shape": "shapes",
    "native-table": "tables",
    "native-chart": "charts",
    "connector": "connectors",
    "picture": "pictures",
    "diagram": "diagrams",
}
SUPERVISOR_ROLES = {"initiator", "mediator", "recorder", "final_auditor"}
ROLE_STATUS = {"complete", "not-needed", "incomplete"}
ROLE_EVIDENCE_REQUIREMENTS = {
    "initiator": ("ppt-resource-inventory.json", "ppt-supervision-report.json"),
    "mediator": ("ppt-supervision-report.json#issues",),
    "recorder": ("ppt-supervision-report.json#lifecycle_events",),
    "final_auditor": ("ppt-output-qa.json", "ppt-supervision-report.json#slides"),
}
LIFECYCLE_PHASES = {
    "root", "preflight", "logic", "copy", "art-direction", "output",
    "mediation", "supervision", "delivery",
}
LIFECYCLE_STATUS = {"completed", "blocked", "returned", "not-needed"}
CANONICAL_LIFECYCLE_ACTIONS = (
    "supervision-started",
    "runtime-preflight-completed",
    "resource-brief-presented",
    "logic-handoff-recorded",
    "copy-handoff-recorded",
    "art-direction-handoff-recorded",
    "output-handoff-recorded",
    "final-audit-completed",
    "delivery-pair-locked",
    "control-returned",
)
REQUIRED_LIFECYCLE_ACTIONS = set(CANONICAL_LIFECYCLE_ACTIONS)
LIFECYCLE_ACTION_SPEC = {
    "supervision-started": ("root", "initiator", "completed"),
    "runtime-preflight-completed": ("preflight", "recorder", "completed"),
    "resource-brief-presented": ("preflight", "recorder", "completed"),
    "logic-handoff-recorded": ("logic", "recorder", "completed"),
    "copy-handoff-recorded": ("copy", "recorder", "completed"),
    "art-direction-handoff-recorded": ("art-direction", "recorder", "completed"),
    "output-handoff-recorded": ("output", "recorder", "completed"),
    "mediation-recorded": ("mediation", "mediator", "completed"),
    "final-audit-completed": ("supervision", "final_auditor", "completed"),
    "delivery-pair-locked": ("delivery", "recorder", "completed"),
    "control-returned": ("delivery", "initiator", "returned"),
}
LIFECYCLE_EVIDENCE_REQUIREMENTS = {
    "supervision-started": ("ppt-resource-inventory.json",),
    "runtime-preflight-completed": ("runtime-preflight.json",),
    "resource-brief-presented": ("ppt-resource-inventory.json#user_brief", "content_sha256="),
    "logic-handoff-recorded": ("ppt-design-package.json",),
    "copy-handoff-recorded": ("ppt-design-package.json#copy_layer",),
    "art-direction-handoff-recorded": ("ppt-art-direction-plan.json",),
    "output-handoff-recorded": (".pptx", "ppt-output-qa.json"),
    "mediation-recorded": ("ppt-supervision-checkpoint.json",),
    "final-audit-completed": ("ppt-output-qa.json", "ppt-supervision-report.json#slides"),
    "delivery-pair-locked": (".pptx", "ppt-supervision-report.json"),
    "control-returned": ("ppt-supervision-report.json#control_returned_to",),
}
SHA256_HEX = set("0123456789abcdef")
SHA256_TOKEN = re.compile(r"(?:^|\s)sha256=([0-9a-f]{64})(?=\s|$)")
CHECKPOINT_STATUS = {"continue", "recommend-user-input", "proceed-with-assumptions"}
CHECKPOINT_SEVERITY = {"critical", "major", "moderate", "minor"}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def require_keys(obj: Any, keys: set[str], path: str, errors: list[str]) -> None:
    if not isinstance(obj, dict):
        errors.append(f"{path}: must be an object")
        return
    missing = sorted(keys - set(obj))
    if missing:
        errors.append(f"{path}: missing keys {missing}")


def parse_timestamp(value: Any, path: str, errors: list[str]) -> datetime | None:
    if not nonempty(value):
        errors.append(f"{path}: must be a timezone-aware ISO timestamp")
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{path}: must be a timezone-aware ISO timestamp")
        return None
    if parsed.utcoffset() is None:
        errors.append(f"{path}: timezone is required")
        return None
    return parsed


def valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= SHA256_HEX


def evidence_artifact(ref: str, root: Path) -> Path | None:
    base = ref.split("#", 1)[0].strip().split(" ", 1)[0]
    if not base or "://" in base:
        return None
    candidate = Path(base)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None
    return resolved


def evidence_sha256(ref: str) -> str | None:
    match = SHA256_TOKEN.search(ref)
    return match.group(1) if match else None


def load_evidence_json(
    artifact: Path,
    reference: str,
    path: str,
    errors: list[str],
) -> Any | None:
    """Load a hash-bound JSON evidence file and reject empty or malformed placeholders."""

    declared = evidence_sha256(reference)
    if declared is None:
        errors.append(f"{path}: external evidence must include sha256=<actual-file-sha256>: {reference}")
        return None
    try:
        payload = artifact.read_bytes()
    except OSError as exc:
        errors.append(f"{path}: cannot read evidence artifact {reference}: {exc}")
        return None
    if not payload:
        errors.append(f"{path}: evidence artifact must not be empty: {reference}")
        return None
    actual = hashlib.sha256(payload).hexdigest()
    if actual != declared:
        errors.append(f"{path}: evidence sha256 does not match actual bytes: {reference}")
        return None
    try:
        parsed = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"{path}: evidence artifact must be valid JSON: {reference}: {exc}")
        return None
    if not isinstance(parsed, (dict, list)) or not parsed:
        errors.append(f"{path}: evidence JSON must contain governed content, not an empty placeholder: {reference}")
        return None
    return parsed


def validate_checkpoint(
    checkpoint: Any,
    report: dict[str, Any],
    mediation_event: dict[str, Any] | None,
    path: str,
    errors: list[str],
) -> None:
    """Validate a concrete mediation checkpoint bound to this report and its issues."""

    require_keys(
        checkpoint,
        {
            "checkpoint_version", "checkpoint_id", "run_id", "task_request_sha256",
            "recorded_at", "stage", "status", "related_issue_ids", "conflicts",
            "questions_for_user", "assumptions_if_continue",
            "same_conflict_previously_escalated", "control_returned_to",
        },
        path,
        errors,
    )
    if not isinstance(checkpoint, dict):
        return
    if checkpoint.get("checkpoint_version") != "1.1":
        errors.append(f"{path}.checkpoint_version: expected 1.1")
    for key in ("checkpoint_id", "stage", "control_returned_to"):
        if not nonempty(checkpoint.get(key)):
            errors.append(f"{path}.{key}: must be non-empty")
    if checkpoint.get("run_id") != report.get("run_id"):
        errors.append(f"{path}.run_id: must match the supervision report")
    if checkpoint.get("task_request_sha256") != report.get("task_request_sha256"):
        errors.append(f"{path}.task_request_sha256: must match the supervision report")
    recorded_at = parse_timestamp(checkpoint.get("recorded_at"), f"{path}.recorded_at", errors)
    event_at = None
    if isinstance(mediation_event, dict):
        event_at = parse_timestamp(
            mediation_event.get("occurred_at"),
            "report.lifecycle_events.mediation-recorded.occurred_at",
            errors,
        )
    if recorded_at is not None and event_at is not None and recorded_at != event_at:
        errors.append(f"{path}.recorded_at: must match the mediation-recorded lifecycle event")
    if checkpoint.get("status") not in CHECKPOINT_STATUS:
        errors.append(f"{path}.status: invalid value")
    if not isinstance(checkpoint.get("same_conflict_previously_escalated"), bool):
        errors.append(f"{path}.same_conflict_previously_escalated: must be boolean")

    report_issue_ids = {
        str(item.get("issue_id"))
        for item in report.get("issues", [])
        if isinstance(item, dict) and nonempty(item.get("issue_id"))
    }
    related = checkpoint.get("related_issue_ids")
    if (
        not isinstance(related, list)
        or any(not nonempty(item) for item in related)
        or len(related) != len(set(related or []))
    ):
        errors.append(f"{path}.related_issue_ids: must be a unique non-empty string array")
    elif set(related) != report_issue_ids:
        errors.append(f"{path}.related_issue_ids: must exactly cover the report issue IDs")

    conflicts = checkpoint.get("conflicts")
    if not isinstance(conflicts, list) or not conflicts:
        errors.append(f"{path}.conflicts: must be a non-empty array")
        conflicts = []
    conflict_ids: set[str] = set()
    covered_issue_ids: set[str] = set()
    for index, conflict in enumerate(conflicts):
        conflict_path = f"{path}.conflicts[{index}]"
        require_keys(
            conflict,
            {
                "conflict_id", "issue_ids", "severity", "cause", "decision_impact",
                "evidence", "approved_baseline", "downstream_challenge", "alternatives",
                "user_decision",
            },
            conflict_path,
            errors,
        )
        if not isinstance(conflict, dict):
            continue
        conflict_id = conflict.get("conflict_id")
        if not nonempty(conflict_id) or conflict_id in conflict_ids:
            errors.append(f"{conflict_path}.conflict_id: must be non-empty and unique")
        else:
            conflict_ids.add(str(conflict_id))
        if conflict.get("severity") not in CHECKPOINT_SEVERITY:
            errors.append(f"{conflict_path}.severity: invalid value")
        for key in (
            "cause", "decision_impact", "approved_baseline", "downstream_challenge", "user_decision",
        ):
            if not nonempty(conflict.get(key)):
                errors.append(f"{conflict_path}.{key}: must be non-empty")
        for key in ("evidence", "alternatives"):
            value = conflict.get(key)
            if not isinstance(value, list) or not value or any(not nonempty(item) for item in value):
                errors.append(f"{conflict_path}.{key}: must be a non-empty string array")
        issue_ids = conflict.get("issue_ids")
        if (
            not isinstance(issue_ids, list)
            or not issue_ids
            or any(not nonempty(item) for item in issue_ids)
            or len(issue_ids) != len(set(issue_ids or []))
        ):
            errors.append(f"{conflict_path}.issue_ids: must be a unique non-empty string array")
        elif not set(issue_ids) <= report_issue_ids:
            errors.append(f"{conflict_path}.issue_ids: contains an issue absent from the report")
        else:
            covered_issue_ids.update(str(item) for item in issue_ids)
    if report_issue_ids and covered_issue_ids != report_issue_ids:
        errors.append(f"{path}.conflicts: every report issue must be covered by a conflict")
    for key in ("questions_for_user", "assumptions_if_continue"):
        value = checkpoint.get(key)
        if not isinstance(value, list) or any(not nonempty(item) for item in value):
            errors.append(f"{path}.{key}: must be a string array")
    if isinstance(checkpoint.get("questions_for_user"), list) and len(checkpoint["questions_for_user"]) > 3:
        errors.append(f"{path}.questions_for_user: must contain at most three questions")


def validate_target_application_evidence(
    target: dict[str, Any],
    index: int,
    evidence_root: Path,
    report: dict[str, Any],
    errors: list[str],
) -> None:
    """Bind a target disposition either to preflight absence or an executed acceptance receipt."""

    path = f"report.environment_observation.target_applications[{index}]"
    references = target.get("evidence_refs", [])
    if not isinstance(references, list):
        return
    status = target.get("final_status")
    application = target.get("application")
    if status in {"deferred", "not-selected"}:
        if not any(evidence_artifact(str(ref), evidence_root) and evidence_artifact(str(ref), evidence_root).name.casefold() == "runtime-preflight.json" for ref in references):
            errors.append(f"{path}.evidence_refs: {status} must be bound to runtime-preflight.json")
        return

    receipts: list[Any] = []
    for reference in references:
        artifact = evidence_artifact(str(reference), evidence_root)
        if artifact is None or artifact.name.casefold() == "runtime-preflight.json" or artifact.suffix.casefold() != ".json":
            continue
        parsed = load_evidence_json(artifact, str(reference), f"{path}.evidence_refs", errors)
        if parsed is not None:
            receipts.append(parsed)
    if not receipts:
        errors.append(f"{path}.evidence_refs: {status} requires a hash-bound target-application receipt")
        return
    final_pptx_sha256 = report.get("delivery_pair", {}).get("pptx", {}).get("sha256")
    matching = False
    receipt_failures: list[str] = []
    for receipt in receipts:
        if not isinstance(receipt, dict):
            continue
        receipt_errors: list[str] = []
        require_keys(
            receipt,
            {
                "contract", "application", "run_id", "task_request_sha256", "executed",
                "status", "observed_at", "pptx_sha256", "evidence",
            },
            f"{path}.target_receipt",
            receipt_errors,
        )
        if receipt.get("contract") != "io.clayz.presentation.target-application-check/1.0":
            receipt_errors.append(f"{path}.target_receipt.contract: invalid contract")
        if receipt.get("application") != application:
            receipt_errors.append(f"{path}.target_receipt.application: must match the target")
        if receipt.get("run_id") != report.get("run_id"):
            receipt_errors.append(f"{path}.target_receipt.run_id: must match the report")
        if receipt.get("task_request_sha256") != report.get("task_request_sha256"):
            receipt_errors.append(f"{path}.target_receipt.task_request_sha256: must match the report")
        if receipt.get("executed") is not True:
            receipt_errors.append(f"{path}.target_receipt.executed: pass/fail requires true")
        if receipt.get("status") != status:
            receipt_errors.append(f"{path}.target_receipt.status: must match final_status")
        observed_at = parse_timestamp(
            receipt.get("observed_at"),
            f"{path}.target_receipt.observed_at",
            receipt_errors,
        )
        preflight_binding = report.get("environment_observation", {}).get("preflight", {})
        window_errors: list[str] = []
        issued_at = parse_timestamp(
            preflight_binding.get("issued_at"),
            "report.environment_observation.preflight.issued_at",
            window_errors,
        )
        expires_at = parse_timestamp(
            preflight_binding.get("expires_at"),
            "report.environment_observation.preflight.expires_at",
            window_errors,
        )
        lifecycle = report.get("lifecycle_events", [])
        output_event = next(
            (item for item in lifecycle if isinstance(item, dict) and item.get("action") == "output-handoff-recorded"),
            None,
        )
        audit_event = next(
            (item for item in lifecycle if isinstance(item, dict) and item.get("action") == "final-audit-completed"),
            None,
        )
        output_at = parse_timestamp(
            output_event.get("occurred_at") if isinstance(output_event, dict) else None,
            "report.lifecycle_events.output-handoff-recorded.occurred_at",
            window_errors,
        )
        audit_at = parse_timestamp(
            audit_event.get("occurred_at") if isinstance(audit_event, dict) else None,
            "report.lifecycle_events.final-audit-completed.occurred_at",
            window_errors,
        )
        if observed_at is not None and issued_at is not None and expires_at is not None and not (
            issued_at <= observed_at <= expires_at
        ):
            receipt_errors.append(f"{path}.target_receipt.observed_at: must fall inside the run-challenge window")
        if observed_at is not None and output_at is not None and audit_at is not None and not (
            output_at <= observed_at <= audit_at
        ):
            receipt_errors.append(
                f"{path}.target_receipt.observed_at: must fall between Output handoff and final audit"
            )
        if receipt.get("pptx_sha256") != final_pptx_sha256:
            receipt_errors.append(f"{path}.target_receipt.pptx_sha256: must match the final PPTX")
        if not nonempty(receipt.get("evidence")):
            receipt_errors.append(f"{path}.target_receipt.evidence: must be non-empty")
        if not receipt_errors:
            matching = True
            break
        receipt_failures.extend(receipt_errors)
    if not matching:
        errors.extend(receipt_failures)
        errors.append(f"{path}.evidence_refs: no target-application receipt matches this run and final PPTX")


def validate_evidence_reference(
    reference: str,
    evidence_root: Path,
    package: Any,
    plan: Any,
    qa: Any,
    report: dict[str, Any],
    pptx: Path | None,
    runtime_preflight: Any | None,
    runtime_preflight_sha256: str | None,
    mediation_event: dict[str, Any] | None,
    path: str,
    errors: list[str],
) -> None:
    """Resolve, hash, and minimally validate one governed evidence reference."""

    artifact = evidence_artifact(reference, evidence_root)
    if artifact is None or not artifact.is_file():
        errors.append(f"{path}: referenced evidence artifact does not exist: {reference}")
        return
    artifact_name = artifact.name.casefold()
    if artifact_name == "ppt-supervision-report.json":
        try:
            persisted = json.loads(artifact.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: supervision report self-evidence is unreadable: {reference}: {exc}")
            return
        if persisted != report:
            errors.append(f"{path}: supervision report self-evidence must match the report under validation")
        fragment = reference.split("#", 1)[1].split(" ", 1)[0] if "#" in reference else None
        if fragment and fragment not in report:
            errors.append(f"{path}: supervision report fragment does not exist: {reference}")
        return

    declared = evidence_sha256(reference)
    if declared is None:
        errors.append(f"{path}: external evidence must include sha256=<actual-file-sha256>: {reference}")
        return
    try:
        payload = artifact.read_bytes()
    except OSError as exc:
        errors.append(f"{path}: cannot read evidence artifact {reference}: {exc}")
        return
    if not payload:
        errors.append(f"{path}: evidence artifact must not be empty: {reference}")
        return
    actual = hashlib.sha256(payload).hexdigest()
    if actual != declared:
        errors.append(f"{path}: evidence sha256 does not match actual bytes: {reference}")
        return
    if artifact_name.endswith(".pptx"):
        if pptx is None or not pptx.is_file() or hashlib.sha256(pptx.read_bytes()).hexdigest() != actual:
            errors.append(f"{path}: PPTX evidence bytes must match the final PPTX under validation")
        return
    if artifact.suffix.casefold() != ".json":
        return
    try:
        parsed = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"{path}: evidence artifact must be valid JSON: {reference}: {exc}")
        return
    if not isinstance(parsed, (dict, list)) or not parsed:
        errors.append(f"{path}: evidence JSON must contain governed content, not an empty placeholder: {reference}")
        return
    if artifact_name == "runtime-preflight.json":
        if parsed != runtime_preflight or actual != runtime_preflight_sha256:
            errors.append(f"{path}: runtime-preflight evidence must match the validated preflight bytes")
        if "#target_application_checks." in reference:
            application = reference.split("#target_application_checks.", 1)[1].split(" ", 1)[0]
            checks = parsed.get("target_application_checks", []) if isinstance(parsed, dict) else []
            if not any(isinstance(item, dict) and item.get("application") == application for item in checks):
                errors.append(f"{path}: runtime-preflight target fragment does not exist: {reference}")
    elif artifact_name == "ppt-resource-inventory.json":
        if not isinstance(parsed, dict) or parsed.get("contract") != "io.clayz.presentation.resource-inventory/1.0":
            errors.append(f"{path}: resource-inventory evidence has the wrong contract")
        if isinstance(package, dict) and parsed != package.get("resource_inventory"):
            errors.append(f"{path}: resource-inventory evidence must match the validated design package lock")
        if "#user_brief" in reference and (not isinstance(parsed, dict) or "user_brief" not in parsed):
            errors.append(f"{path}: resource-inventory user_brief fragment does not exist")
    elif artifact_name == "ppt-design-package.json":
        if not isinstance(parsed, dict) or parsed.get("contract_version") != "2.3" or parsed.get("status") != "copy-approved":
            errors.append(f"{path}: design-package evidence must be contract 2.3 and copy-approved")
        if parsed != package:
            errors.append(f"{path}: design-package evidence must match the package under validation")
        if "#copy_layer" in reference and (not isinstance(parsed, dict) or "copy_layer" not in parsed):
            errors.append(f"{path}: design-package copy_layer fragment does not exist")
    elif artifact_name == "ppt-art-direction-plan.json":
        if not isinstance(parsed, dict) or parsed.get("contract_version") != "1.6" or parsed.get("status") != "art-direction-approved":
            errors.append(f"{path}: art-direction evidence must be contract 1.6 and art-direction-approved")
        if plan is not None and parsed != plan:
            errors.append(f"{path}: art-direction evidence must match the plan under validation")
    elif artifact_name == "ppt-output-qa.json":
        if not isinstance(parsed, dict) or parsed.get("contract_version") != "3.9":
            errors.append(f"{path}: Output QA evidence must use contract 3.9")
        if qa is not None and parsed != qa:
            errors.append(f"{path}: Output QA evidence must match the QA document under validation")
    elif artifact_name == "ppt-supervision-checkpoint.json":
        validate_checkpoint(parsed, report, mediation_event, "ppt-supervision-checkpoint.json", errors)


def validate_environment_observation(
    report: Any,
    runtime_preflight: Any | None = None,
    runtime_preflight_sha256: str | None = None,
    resolved_config: Any | None = None,
    resolved_config_sha256: str | None = None,
) -> list[str]:
    """Bind preflight facts and final target-app dispositions into the audit report."""

    errors: list[str] = []
    if not isinstance(report, dict):
        return ["report: must be an object"]
    observation = report.get("environment_observation")
    require_keys(
        observation,
        {"preflight", "route", "required_capabilities", "target_applications", "compatibility_scope", "attribution_summary"},
        "report.environment_observation",
        errors,
    )
    if not isinstance(observation, dict):
        return errors

    preflight_record = observation.get("preflight")
    require_keys(
        preflight_record,
        {
            "artifact", "scan_id", "sha256", "run_id", "task_request_sha256", "config_sha256",
            "nonce", "challenge_sha256", "task_root_sha256", "issued_at", "expires_at",
            "issuance_receipt_sha256", "consumption_receipt_sha256",
        },
        "report.environment_observation.preflight",
        errors,
    )
    if isinstance(preflight_record, dict):
        if not nonempty(preflight_record.get("artifact")) or not nonempty(preflight_record.get("scan_id")):
            errors.append("report.environment_observation.preflight: artifact and scan_id must be non-empty")
        if not valid_sha256(preflight_record.get("sha256")):
            errors.append("report.environment_observation.preflight.sha256: must be a lower-case SHA-256")
        if not nonempty(preflight_record.get("run_id")):
            errors.append("report.environment_observation.preflight.run_id: must be non-empty")
        for key in (
            "task_request_sha256", "config_sha256", "nonce", "challenge_sha256", "task_root_sha256",
            "issuance_receipt_sha256", "consumption_receipt_sha256",
        ):
            if not valid_sha256(preflight_record.get(key)):
                errors.append(f"report.environment_observation.preflight.{key}: must be a lower-case SHA-256")
        parse_timestamp(preflight_record.get("issued_at"), "report.environment_observation.preflight.issued_at", errors)
        parse_timestamp(preflight_record.get("expires_at"), "report.environment_observation.preflight.expires_at", errors)
        artifact_paths = report.get("artifact_paths")
        if isinstance(artifact_paths, dict) and preflight_record.get("artifact") != artifact_paths.get("runtime_preflight"):
            errors.append("report.environment_observation.preflight.artifact: must match artifact_paths.runtime_preflight")
        if runtime_preflight_sha256 is not None and preflight_record.get("sha256") != runtime_preflight_sha256:
            errors.append("report.environment_observation.preflight.sha256: must match runtime-preflight.json")

    route = observation.get("route")
    require_keys(
        route,
        {"route_id", "authoring_backend", "render_backend", "status"},
        "report.environment_observation.route",
        errors,
    )
    if isinstance(route, dict):
        for key in ("route_id", "authoring_backend", "render_backend"):
            if not nonempty(route.get(key)):
                errors.append(f"report.environment_observation.route.{key}: must be non-empty")
        if route.get("status") not in {"ready", "provisional", "blocked"}:
            errors.append("report.environment_observation.route.status: invalid value")

    capabilities = observation.get("required_capabilities")
    require_keys(
        capabilities,
        {"configured", "satisfied", "declared_unverified", "missing"},
        "report.environment_observation.required_capabilities",
        errors,
    )
    if isinstance(capabilities, dict):
        for key in ("configured", "satisfied", "declared_unverified", "missing"):
            value = capabilities.get(key)
            if not isinstance(value, list) or len(value) != len(set(value or [])) or any(not nonempty(item) for item in value or []):
                errors.append(f"report.environment_observation.required_capabilities.{key}: must be a unique string array")

    targets = observation.get("target_applications")
    target_by_application: dict[str, dict[str, Any]] = {}
    final_statuses: list[str] = []
    if not isinstance(targets, list) or not targets:
        errors.append("report.environment_observation.target_applications: must be a non-empty array")
        targets = []
    for index, target in enumerate(targets):
        path = f"report.environment_observation.target_applications[{index}]"
        require_keys(
            target,
            {"application", "capability", "availability", "final_status", "authoring_gate", "evidence_refs"},
            path,
            errors,
        )
        if not isinstance(target, dict):
            continue
        application = target.get("application")
        if not nonempty(application) or application in target_by_application:
            errors.append(f"{path}.application: must be non-empty and unique")
        else:
            target_by_application[str(application)] = target
        if not nonempty(target.get("capability")):
            errors.append(f"{path}.capability: must be non-empty")
        availability = target.get("availability")
        final_status = target.get("final_status")
        if availability not in TARGET_AVAILABILITY:
            errors.append(f"{path}.availability: invalid value")
        if final_status not in TARGET_FINAL_STATUS:
            errors.append(f"{path}.final_status: invalid value")
        else:
            final_statuses.append(str(final_status))
        if target.get("authoring_gate") is not False:
            errors.append(f"{path}.authoring_gate: target-application acceptance must not block authoring")
        if availability == "unavailable" and final_status != "deferred":
            errors.append(f"{path}.final_status: unavailable target must be deferred")
        if availability == "available" and final_status == "deferred":
            errors.append(f"{path}.final_status: available target must pass, fail, or be explicitly not-selected")
        evidence_refs = target.get("evidence_refs")
        if not isinstance(evidence_refs, list) or not evidence_refs or any(not nonempty(item) for item in evidence_refs):
            errors.append(f"{path}.evidence_refs: must be a non-empty string array")

    passed = sum(status == "pass" for status in final_statuses)
    expected_scope = "full" if final_statuses and passed == len(final_statuses) else "partial" if passed else "none"
    if observation.get("compatibility_scope") != expected_scope:
        errors.append("report.environment_observation.compatibility_scope: must match final target-application statuses")
    if not nonempty(observation.get("attribution_summary")):
        errors.append("report.environment_observation.attribution_summary: must be non-empty")

    if runtime_preflight is not None:
        if not isinstance(runtime_preflight, dict):
            errors.append("runtime_preflight: must be an object")
            return errors
        if runtime_preflight.get("contract") != "io.clayz.presentation.runtime-preflight/1.3":
            errors.append("runtime_preflight.contract: expected io.clayz.presentation.runtime-preflight/1.3")
        run_binding = runtime_preflight.get("run_binding", {})
        config_binding = runtime_preflight.get("config_binding", {})
        component_version_gate = runtime_preflight.get("component_version_gate", {})
        if not isinstance(run_binding, dict):
            errors.append("runtime_preflight.run_binding: must be an object")
            run_binding = {}
        if not isinstance(config_binding, dict):
            errors.append("runtime_preflight.config_binding: must be an object")
            config_binding = {}
        if not isinstance(component_version_gate, dict):
            errors.append("runtime_preflight.component_version_gate: must be an object")
            component_version_gate = {}
        if component_version_gate.get("status") != "latest" or component_version_gate.get("all_components_current") is not True:
            errors.append("runtime_preflight.component_version_gate: final delivery requires latest mounted components")
        if any(not valid_sha256(component_version_gate.get(key)) for key in ("sha256", "manifest_sha256")):
            errors.append("runtime_preflight.component_version_gate: report and manifest SHA-256 are required")
        if isinstance(resolved_config, dict):
            configured_version = resolved_config.get("identity", {}).get("version")
            if nonempty(configured_version) and (
                component_version_gate.get("local_release_version") != configured_version
                or component_version_gate.get("latest_release_version") != configured_version
            ):
                errors.append("runtime_preflight.component_version_gate: versions must match the resolved configuration")
        if isinstance(preflight_record, dict):
            if preflight_record.get("run_id") != run_binding.get("run_id"):
                errors.append("report.environment_observation.preflight.run_id: must match runtime-preflight.json")
            if preflight_record.get("task_request_sha256") != run_binding.get("task_request_sha256"):
                errors.append("report.environment_observation.preflight.task_request_sha256: must match runtime-preflight.json")
            if preflight_record.get("config_sha256") != config_binding.get("sha256"):
                errors.append("report.environment_observation.preflight.config_sha256: must match runtime-preflight.json")
        if report.get("run_id") != run_binding.get("run_id"):
            errors.append("report.run_id: must match runtime-preflight.json")
        if report.get("task_request_sha256") != run_binding.get("task_request_sha256"):
            errors.append("report.task_request_sha256: must match runtime-preflight.json")
        if run_binding.get("binding_source") != "script-issued-challenge":
            errors.append("runtime_preflight.run_binding.binding_source: final delivery requires a script-issued challenge")
        if any(not valid_sha256(run_binding.get(key)) for key in ("nonce", "challenge_sha256", "task_root_sha256")):
            errors.append("runtime_preflight.run_binding: nonce, challenge, and task-root SHA-256 must be valid")
        if not nonempty(run_binding.get("issuance_receipt")) or not valid_sha256(run_binding.get("issuance_receipt_sha256")):
            errors.append("runtime_preflight.run_binding: a script issuance receipt is required")
        if not nonempty(run_binding.get("consumption_receipt")) or not valid_sha256(run_binding.get("consumption_receipt_sha256")):
            errors.append("runtime_preflight.run_binding: an exclusive challenge-consumption receipt is required")
        issued = parse_timestamp(run_binding.get("issued_at"), "runtime_preflight.run_binding.issued_at", errors)
        expires = parse_timestamp(run_binding.get("expires_at"), "runtime_preflight.run_binding.expires_at", errors)
        supervised = parse_timestamp(report.get("supervised_at"), "report.supervised_at", errors)
        if issued is not None and expires is not None and supervised is not None and not (issued <= supervised <= expires):
            errors.append("report.supervised_at: must fall inside the fresh run-challenge window")
        if isinstance(preflight_record, dict):
            for key in (
                "nonce", "challenge_sha256", "task_root_sha256", "issued_at", "expires_at",
                "issuance_receipt_sha256", "consumption_receipt_sha256",
            ):
                if preflight_record.get(key) != run_binding.get(key):
                    errors.append(f"report.environment_observation.preflight.{key}: must match runtime-preflight.json")
        host_observation = runtime_preflight.get("dependencies", {}).get("host_tools", {}).get("observation", {})
        host_available = runtime_preflight.get("dependencies", {}).get("host_tools", {}).get("available") is True
        if not isinstance(host_observation, dict):
            errors.append("runtime_preflight.dependencies.host_tools.observation: must be an object")
        else:
            for key in ("run_id", "task_request_sha256", "challenge_sha256"):
                if host_observation.get(key) != run_binding.get(key):
                    errors.append(f"runtime_preflight.dependencies.host_tools.observation.{key}: must match run binding")
            if "verified" in host_observation:
                errors.append("runtime_preflight.dependencies.host_tools.observation.verified: self-verified host claims are forbidden")
            if host_available:
                if host_observation.get("verification_status") != "challenge-bound-host-declaration":
                    errors.append("runtime_preflight.dependencies.host_tools.observation: available host tools require challenge-bound declaration status")
                if host_observation.get("assurance_level") != "host-declared-unverified":
                    errors.append("runtime_preflight.dependencies.host_tools.observation: host declaration must remain explicitly unverified")
                if host_observation.get("route_eligible") is not False:
                    errors.append("runtime_preflight.dependencies.host_tools.observation: unverified host declaration cannot authorize route readiness")
                receipts = host_observation.get("evidence_receipts")
                if not isinstance(receipts, list) or not receipts:
                    errors.append("runtime_preflight.dependencies.host_tools.observation.evidence_receipts: required for available host tools")
        if resolved_config_sha256 is not None and config_binding.get("sha256") != resolved_config_sha256:
            errors.append("runtime_preflight.config_binding.sha256: must match the validated resolved config")
        selected = runtime_preflight.get("selected_route", {})
        if (
            isinstance(selected, dict)
            and "native-presentation-tool" in {selected.get("authoring_backend"), selected.get("render_backend")}
            and selected.get("available") is True
            and host_observation.get("route_eligible") is not True
        ):
            errors.append("runtime_preflight.selected_route.available: unverified native host declaration cannot authorize ready")
        expected_route_status = (
            "ready" if selected.get("available") is True
            else "provisional" if selected.get("attemptable") is True
            else "blocked"
        )
        expected_route = {
            "route_id": selected.get("route_id"),
            "authoring_backend": selected.get("authoring_backend"),
            "render_backend": selected.get("render_backend"),
            "status": expected_route_status,
        }
        if route != expected_route:
            errors.append("report.environment_observation.route: must exactly mirror the locked preflight route")
        configured = sorted(runtime_preflight.get("required_capabilities", []))
        missing = sorted(selected.get("missing_capabilities", []))
        declared_unverified = (
            sorted(set(configured) - set(missing))
            if selected.get("assurance_level") == "host-declared-unverified"
            else []
        )
        expected_capabilities = {
            "configured": configured,
            "satisfied": [] if declared_unverified else sorted(set(configured) - set(missing)),
            "declared_unverified": declared_unverified,
            "missing": missing,
        }
        if capabilities != expected_capabilities:
            errors.append("report.environment_observation.required_capabilities: must exactly mirror preflight satisfaction")
        if isinstance(resolved_config, dict):
            required_by_config = resolved_config.get("renderer", {}).get("required_capabilities", [])
            if not isinstance(required_by_config, list) or any(not nonempty(item) for item in required_by_config):
                errors.append("resolved_config.renderer.required_capabilities: must be a string array")
            elif not set(required_by_config).issubset(set(configured)):
                errors.append("runtime_preflight.required_capabilities: cannot omit resolved-config requirements")
        if isinstance(preflight_record, dict) and preflight_record.get("scan_id") != runtime_preflight.get("scan_id"):
            errors.append("report.environment_observation.preflight.scan_id: must match runtime-preflight.json")
        expected_targets = runtime_preflight.get("target_application_checks", [])
        if not isinstance(expected_targets, list) or len(targets) != len(expected_targets):
            errors.append("report.environment_observation.target_applications: must cover every preflight target exactly once")
        else:
            for expected in expected_targets:
                actual = target_by_application.get(expected.get("application"))
                if not isinstance(actual, dict):
                    errors.append(f"report.environment_observation.target_applications: missing {expected.get('application')}")
                    continue
                for key in ("capability", "availability"):
                    if actual.get(key) != expected.get(key):
                        errors.append(
                            f"report.environment_observation.target_applications.{expected.get('application')}.{key}: "
                            "must match runtime-preflight.json"
                        )
    return errors


def has_deferred_target_acceptance(report: Any) -> bool:
    if not isinstance(report, dict):
        return False
    observation = report.get("environment_observation")
    targets = observation.get("target_applications", []) if isinstance(observation, dict) else []
    return any(
        isinstance(item, dict) and item.get("final_status") in {"deferred", "not-selected"}
        for item in targets
    )


def validate_supervisor_accountability(
    package: Any,
    report: Any,
    pptx: Path | None,
    report_path: Path | None,
    runtime_preflight: Any | None = None,
    runtime_preflight_sha256: str | None = None,
    resolved_config: Any | None = None,
    resolved_config_sha256: str | None = None,
    evidence_root: Path | None = None,
    plan: Any | None = None,
    qa: Any | None = None,
) -> list[str]:
    """Validate the Supervisor's four roles, lifecycle record, and paired delivery."""

    errors: list[str] = []
    if not isinstance(report, dict):
        return ["report: must be an object"]
    errors.extend(validate_environment_observation(
        report,
        runtime_preflight,
        runtime_preflight_sha256,
        resolved_config,
        resolved_config_sha256,
    ))

    roles = report.get("supervisor_roles")
    require_keys(roles, SUPERVISOR_ROLES, "report.supervisor_roles", errors)
    if isinstance(roles, dict):
        extra_roles = sorted(set(roles) - SUPERVISOR_ROLES)
        if extra_roles:
            errors.append(f"report.supervisor_roles: unsupported roles {extra_roles}")
        for role_name in sorted(SUPERVISOR_ROLES):
            role = roles.get(role_name)
            path = f"report.supervisor_roles.{role_name}"
            require_keys(role, {"status", "summary", "evidence_refs"}, path, errors)
            if not isinstance(role, dict):
                continue
            status = role.get("status")
            if status not in ROLE_STATUS:
                errors.append(f"{path}.status: invalid value")
            if role_name in {"initiator", "recorder", "final_auditor"} and status != "complete":
                errors.append(f"{path}.status: must be complete")
            summary = role.get("summary")
            if not nonempty(summary) or len(str(summary).strip()) < 12:
                errors.append(f"{path}.summary: must contain a concrete accountability summary of at least 12 characters")
            evidence_refs = role.get("evidence_refs")
            if not isinstance(evidence_refs, list) or not evidence_refs or any(not nonempty(item) for item in evidence_refs):
                errors.append(f"{path}.evidence_refs: must be a non-empty string array")
            else:
                refs_text = "\n".join(str(item) for item in evidence_refs)
                missing_tokens = [
                    token for token in ROLE_EVIDENCE_REQUIREMENTS.get(role_name, ())
                    if token not in refs_text
                ]
                if missing_tokens:
                    errors.append(f"{path}.evidence_refs: must bind concrete role evidence tokens {missing_tokens}")
                # Concrete evidence is validated after lifecycle parsing so a checkpoint
                # can be bound to the one canonical mediation event.

    events = report.get("lifecycle_events")
    if not isinstance(events, list) or not events:
        errors.append("report.lifecycle_events: must be a non-empty array")
        events = []
    event_ids: set[str] = set()
    actions: set[str] = set()
    action_counts: dict[str, int] = {}
    action_events: dict[str, dict[str, Any]] = {}
    previous_time: datetime | None = None
    for index, event in enumerate(events):
        path = f"report.lifecycle_events[{index}]"
        require_keys(
            event,
            {"event_id", "occurred_at", "phase", "actor_role", "action", "status", "summary", "evidence_refs"},
            path,
            errors,
        )
        if not isinstance(event, dict):
            continue
        event_id = event.get("event_id")
        if not nonempty(event_id) or event_id in event_ids:
            errors.append(f"{path}.event_id: must be non-empty and unique")
        else:
            event_ids.add(str(event_id))
        timestamp = parse_timestamp(event.get("occurred_at"), f"{path}.occurred_at", errors)
        if timestamp is not None and previous_time is not None and timestamp < previous_time:
            errors.append(f"{path}.occurred_at: lifecycle events must be chronological")
        if timestamp is not None:
            previous_time = timestamp
        if event.get("phase") not in LIFECYCLE_PHASES:
            errors.append(f"{path}.phase: invalid value")
        if event.get("actor_role") not in SUPERVISOR_ROLES:
            errors.append(f"{path}.actor_role: invalid Supervisor role")
        action = event.get("action")
        if not nonempty(action):
            errors.append(f"{path}.action: must be non-empty")
        else:
            action = str(action)
            actions.add(action)
            action_counts[action] = action_counts.get(action, 0) + 1
            action_events.setdefault(action, event)
            expected = LIFECYCLE_ACTION_SPEC.get(action)
            if expected is not None:
                expected_phase, expected_role, expected_status = expected
                if event.get("phase") != expected_phase:
                    errors.append(f"{path}.phase: action {action} requires {expected_phase}")
                if event.get("actor_role") != expected_role:
                    errors.append(f"{path}.actor_role: action {action} requires {expected_role}")
                if event.get("status") != expected_status:
                    errors.append(f"{path}.status: action {action} requires {expected_status}")
        if event.get("status") not in LIFECYCLE_STATUS:
            errors.append(f"{path}.status: invalid value")
        if not nonempty(event.get("summary")):
            errors.append(f"{path}.summary: must be non-empty")
        evidence_refs = event.get("evidence_refs")
        if not isinstance(evidence_refs, list) or not evidence_refs or any(not nonempty(item) for item in evidence_refs):
            errors.append(f"{path}.evidence_refs: must be a non-empty string array")
        elif nonempty(action):
            refs_text = "\n".join(str(item) for item in evidence_refs)
            missing_tokens = [
                token for token in LIFECYCLE_EVIDENCE_REQUIREMENTS.get(str(action), ())
                if token not in refs_text
            ]
            if missing_tokens:
                errors.append(
                    f"{path}.evidence_refs: action {action} must bind concrete evidence tokens {missing_tokens}"
                )
            # Concrete evidence is validated below after the canonical event set is known.

    missing_actions = sorted(REQUIRED_LIFECYCLE_ACTIONS - actions)
    if missing_actions:
        errors.append(f"report.lifecycle_events: missing required actions {missing_actions}")
    duplicate_actions = sorted(action for action, count in action_counts.items() if count != 1)
    if duplicate_actions:
        errors.append(f"report.lifecycle_events: lifecycle actions must be unique {duplicate_actions}")

    positions = {
        action: next(
            (index for index, event in enumerate(events) if isinstance(event, dict) and event.get("action") == action),
            None,
        )
        for action in CANONICAL_LIFECYCLE_ACTIONS
    }
    present_positions = [positions[action] for action in CANONICAL_LIFECYCLE_ACTIONS if positions[action] is not None]
    if present_positions != sorted(present_positions):
        errors.append(
            "report.lifecycle_events: canonical order must be supervision -> preflight -> brief -> Logic -> "
            "Copy -> Art Direction -> Output -> final audit -> delivery lock -> control return"
        )
    mediation_position = next(
        (index for index, event in enumerate(events) if isinstance(event, dict) and event.get("action") == "mediation-recorded"),
        None,
    )
    output_position = positions.get("output-handoff-recorded")
    audit_position = positions.get("final-audit-completed")
    if mediation_position is not None and (
        output_position is None
        or audit_position is None
        or not output_position < mediation_position < audit_position
    ):
        errors.append(
            "report.lifecycle_events: mediation-recorded must occur once after Output and before final audit"
        )

    mediation_event = action_events.get("mediation-recorded")
    if evidence_root is not None:
        for role_name, role in roles.items() if isinstance(roles, dict) else []:
            if not isinstance(role, dict):
                continue
            for reference in role.get("evidence_refs", []) if isinstance(role.get("evidence_refs"), list) else []:
                validate_evidence_reference(
                    str(reference), evidence_root, package, plan, qa, report, pptx, runtime_preflight,
                    runtime_preflight_sha256, mediation_event,
                    f"report.supervisor_roles.{role_name}.evidence_refs", errors,
                )
        for index, event in enumerate(events):
            if not isinstance(event, dict):
                continue
            for reference in event.get("evidence_refs", []) if isinstance(event.get("evidence_refs"), list) else []:
                validate_evidence_reference(
                    str(reference), evidence_root, package, plan, qa, report, pptx, runtime_preflight,
                    runtime_preflight_sha256, mediation_event,
                    f"report.lifecycle_events[{index}].evidence_refs", errors,
                )
        observation = report.get("environment_observation")
        targets = observation.get("target_applications", []) if isinstance(observation, dict) else []
        for index, target in enumerate(targets):
            if not isinstance(target, dict):
                continue
            for reference in target.get("evidence_refs", []) if isinstance(target.get("evidence_refs"), list) else []:
                validate_evidence_reference(
                    str(reference), evidence_root, package, plan, qa, report, pptx, runtime_preflight,
                    runtime_preflight_sha256, mediation_event,
                    f"report.environment_observation.target_applications[{index}].evidence_refs", errors,
                )
            validate_target_application_evidence(target, index, evidence_root, report, errors)

    resource_inventory = package.get("resource_inventory") if isinstance(package, dict) else None
    brief = resource_inventory.get("user_brief", {}) if isinstance(resource_inventory, dict) else {}
    if not isinstance(brief, dict):
        brief = {}
    brief_event = action_events.get("resource-brief-presented")
    if isinstance(brief_event, dict):
        if brief.get("status") != "presented":
            errors.append("report.lifecycle_events: resource brief event requires a presented pre-Logic brief")
        brief_errors: list[str] = []
        event_errors: list[str] = []
        parsed_brief = parse_timestamp(brief.get("presented_at"), "package.resource_inventory.user_brief.presented_at", brief_errors)
        parsed_event = parse_timestamp(brief_event.get("occurred_at"), "report.lifecycle_events.resource-brief-presented.occurred_at", event_errors)
        if parsed_brief is not None and parsed_event is not None and parsed_brief != parsed_event:
            errors.append("report.lifecycle_events: resource brief timestamp must match the pre-Logic inventory")
        errors.extend(brief_errors)
        errors.extend(event_errors)
        digest = brief.get("content_sha256")
        refs = brief_event.get("evidence_refs", [])
        if not valid_sha256(digest) or not any(str(digest) in str(ref) for ref in refs):
            errors.append("report.lifecycle_events: resource brief evidence must bind its content_sha256")

    issues = report.get("issues")
    mediator = roles.get("mediator") if isinstance(roles, dict) else None
    if isinstance(issues, list) and issues:
        if not isinstance(mediator, dict) or mediator.get("status") != "complete":
            errors.append("report.supervisor_roles.mediator.status: issues require completed mediation")
        elif "ppt-supervision-checkpoint.json" not in "\n".join(
            str(item) for item in mediator.get("evidence_refs", [])
        ):
            errors.append(
                "report.supervisor_roles.mediator.evidence_refs: issues require ppt-supervision-checkpoint.json"
            )
        if "mediation-recorded" not in actions:
            errors.append("report.lifecycle_events: issues require a mediation-recorded event")
    elif isinstance(mediator, dict) and mediator.get("status") not in {"complete", "not-needed"}:
        errors.append("report.supervisor_roles.mediator.status: no-issue runs may be complete or not-needed")
    elif "mediation-recorded" in actions:
        errors.append("report.lifecycle_events: a no-issue run must not invent a mediation-recorded event")

    delivery = report.get("delivery_pair")
    require_keys(
        delivery,
        {"status", "required_artifacts", "pptx", "supervision_report", "delivery_manifest", "publisher", "evidence"},
        "report.delivery_pair",
        errors,
    )
    if isinstance(delivery, dict):
        expected_status = "blocked" if report.get("run_status") == "incomplete-evidence" else "ready"
        if delivery.get("status") != expected_status:
            errors.append(f"report.delivery_pair.status: expected {expected_status}")
        if delivery.get("required_artifacts") != ["pptx", "supervision-report"]:
            errors.append("report.delivery_pair.required_artifacts: must be ['pptx', 'supervision-report']")
        if not nonempty(delivery.get("evidence")):
            errors.append("report.delivery_pair.evidence: must be non-empty")
        if delivery.get("publisher") != "scripts/publish_supervised_pair.py":
            errors.append("report.delivery_pair.publisher: must use scripts/publish_supervised_pair.py")

        pptx_record = delivery.get("pptx")
        require_keys(pptx_record, {"path", "sha256"}, "report.delivery_pair.pptx", errors)
        if isinstance(pptx_record, dict):
            if not nonempty(pptx_record.get("path")):
                errors.append("report.delivery_pair.pptx.path: must be non-empty")
            digest = pptx_record.get("sha256")
            if not valid_sha256(digest):
                errors.append("report.delivery_pair.pptx.sha256: must be a lower-case SHA-256")
            if pptx is not None and pptx.is_file():
                actual_digest = hashlib.sha256(pptx.read_bytes()).hexdigest()
                if digest != actual_digest:
                    errors.append("report.delivery_pair.pptx.sha256: must match the final PPTX")
                if nonempty(pptx_record.get("path")) and Path(str(pptx_record["path"])).name != pptx.name:
                    errors.append("report.delivery_pair.pptx.path: filename must match the validated final PPTX")

        report_record = delivery.get("supervision_report")
        require_keys(report_record, {"path"}, "report.delivery_pair.supervision_report", errors)
        if isinstance(report_record, dict):
            if not nonempty(report_record.get("path")):
                errors.append("report.delivery_pair.supervision_report.path: must be non-empty")
            elif report_path is not None and Path(str(report_record["path"])).name != report_path.name:
                errors.append("report.delivery_pair.supervision_report.path: filename must match this report")
        manifest_record = delivery.get("delivery_manifest")
        require_keys(manifest_record, {"path"}, "report.delivery_pair.delivery_manifest", errors)
        if isinstance(manifest_record, dict) and manifest_record.get("path") != "delivery-manifest.json":
            errors.append("report.delivery_pair.delivery_manifest.path: expected delivery-manifest.json")
    return errors


def target_counts(slide: dict[str, Any]) -> dict[str, int]:
    result = {"shape": 0, "table-cell": 0, "chart-label": 0}
    for mapping in slide.get("copy_unit_map", []):
        kind = mapping.get("target_type") if isinstance(mapping, dict) else None
        if kind in result:
            result[kind] += 1
    return result


def area_signature(slide: dict[str, Any]) -> str:
    parts: list[str] = []
    for region in slide.get("area_plan", []):
        if isinstance(region, dict):
            parts.append(f"{region.get('region_id')}:{region.get('share_percent')}")
    return "; ".join(parts)


def issue_lookup(issues: list[dict[str, Any]]) -> set[tuple[str, Any]]:
    return {(item.get("finding_code"), item.get("slide_id")) for item in issues if isinstance(item, dict)}


def register_check_evidence(
    evidence: Any,
    slide_id: Any,
    path: str,
    seen: dict[str, str],
    errors: list[str],
) -> None:
    """Reject short, anonymous, or repeated check evidence."""

    if not nonempty(evidence) or len(str(evidence).strip()) < 16:
        errors.append(f"{path}: must be substantive and at least 16 characters")
        return
    normalized = " ".join(str(evidence).casefold().split())
    if nonempty(slide_id) and str(slide_id).casefold() not in normalized:
        errors.append(f"{path}: must cite the stable slide_id")
    if normalized in seen:
        errors.append(f"{path}: duplicate boilerplate already used at {seen[normalized]}")
        return
    seen[normalized] = path


def missing_required_object_types(execution: Any, actual: Any) -> list[str]:
    """Return planned object types whose actual inventory is below the hard minimum."""

    if not isinstance(execution, dict) or not isinstance(actual, dict):
        return []
    missing: list[str] = []
    minimums = execution.get("minimum_object_counts")
    if not isinstance(minimums, dict):
        return missing
    for object_type, minimum in minimums.items():
        inventory_key = OBJECT_INVENTORY_MAP.get(object_type)
        if not inventory_key or not isinstance(minimum, int) or minimum < 0:
            continue
        observed = actual.get(inventory_key)
        if not isinstance(observed, int) or observed < minimum:
            missing.append(object_type)
    return sorted(missing)


def validate_report(
    package: Any,
    plan: Any,
    qa: Any,
    inventory: Any,
    report: Any,
    policy: ValidationPolicy | None = None,
    pptx: Path | None = None,
    render_root: Path | None = None,
    report_path: Path | None = None,
    runtime_preflight: Any | None = None,
    runtime_preflight_sha256: str | None = None,
    resolved_config: Any | None = None,
    resolved_config_sha256: str | None = None,
    evidence_root: Path | None = None,
) -> list[str]:
    policy = policy or load_policy()
    errors: list[str] = output_qa_validator.validate_qa(
        package,
        plan,
        qa,
        render_root=render_root,
        pptx=pptx,
        policy=policy,
    )
    require_keys(report, {
        "contract_version", "origin_namespace", "status", "run_id", "task_request_sha256", "package_id", "package_version", "art_direction_plan_contract_version",
        "output_qa_contract_version", "supervised_at", "run_status", "artifact_paths", "slides",
        "issues", "deck_findings", "responsibility_attribution", "recommendations", "delivery_efficiency", "index_evidence", "resource_usage",
        "supervisor_roles", "lifecycle_events", "environment_observation", "delivery_pair", "control_returned_to",
    }, "$report", errors)
    if not all(isinstance(item, dict) for item in (package, plan, qa, inventory, report)):
        return errors
    errors.extend(validate_supervisor_accountability(
        package,
        report,
        pptx,
        report_path,
        runtime_preflight,
        runtime_preflight_sha256,
        resolved_config,
        resolved_config_sha256,
        evidence_root if evidence_root is not None else (report_path.resolve().parent if report_path is not None else None),
        plan,
        qa,
    ))
    if report.get("contract_version") != CONTRACT_VERSION:
        errors.append(f"report.contract_version: expected {CONTRACT_VERSION}")
    if report.get("origin_namespace") != "io.clayz.presentation":
        errors.append("report.origin_namespace: expected io.clayz.presentation")
    if report.get("status") != "supervised":
        errors.append("report.status: expected supervised")
    if not nonempty(report.get("run_id")):
        errors.append("report.run_id: must be non-empty")
    if not valid_sha256(report.get("task_request_sha256")):
        errors.append("report.task_request_sha256: must be a lower-case SHA-256")
    if not nonempty(report.get("control_returned_to")):
        errors.append("report.control_returned_to: must be non-empty")
    if report.get("package_id") != package.get("package_id") or report.get("package_version") != package.get("version"):
        errors.append("report package identity/version must match package")
    if report.get("art_direction_plan_contract_version") != plan.get("contract_version"):
        errors.append("report.art_direction_plan_contract_version: must match plan")
    if report.get("output_qa_contract_version") != qa.get("contract_version"):
        errors.append("report.output_qa_contract_version: must match QA")
    expected_resource_lock = resource_inventory_signature(package.get("resource_inventory"))
    if qa.get("resource_inventory_lock") != expected_resource_lock:
        errors.append("qa.resource_inventory_lock: must preserve the pre-Logic inventory")
    validate_resource_usage(
        report.get("resource_usage"),
        package.get("resource_inventory"),
        "report.resource_usage",
        errors,
    )
    validate_index_evidence(
        report.get("index_evidence"),
        ["logic", "copy", "art-direction", "output", "supervisor"],
        "report.index_evidence",
        errors,
    )
    if index_lock_signature(report.get("index_evidence")) != index_lock_signature(qa.get("index_evidence")):
        errors.append("report.index_evidence: must preserve the Output QA Provider lock and owner materialization")
    if report.get("run_status") not in RUN_STATUS:
        errors.append("report.run_status: invalid value")
    if not nonempty(report.get("supervised_at")):
        errors.append("report.supervised_at: must be non-empty")
    require_keys(report.get("artifact_paths"), {
        "runtime_preflight", "resource_inventory", "package", "art_direction_plan", "pptx", "render_root", "output_qa", "object_inventory", "build_deviation_log",
        "font_environment_report", "cjk_render_report", "final_reopen_render_root",
        "size_audit_report",
    }, "report.artifact_paths", errors)

    issues = report.get("issues")
    if not isinstance(issues, list):
        errors.append("report.issues: must be an array")
        issues = []
    valid_issues: list[dict[str, Any]] = []
    issue_ids: set[str] = set()
    for index, issue in enumerate(issues):
        path = f"report.issues[{index}]"
        require_keys(issue, {
            "issue_id", "finding_code", "slide_id", "severity", "owner_layer", "confidence",
            "failed_checks", "source_artifacts", "evidence", "expected", "actual", "impact",
            "recommended_change", "regression_rule",
        }, path, errors)
        if not isinstance(issue, dict):
            continue
        valid_issues.append(issue)
        issue_id = issue.get("issue_id")
        if not nonempty(issue_id) or issue_id in issue_ids:
            errors.append(f"{path}.issue_id: must be non-empty and unique")
        else:
            issue_ids.add(issue_id)
        if not nonempty(issue.get("finding_code")):
            errors.append(f"{path}.finding_code: must be non-empty")
        if issue.get("severity") not in SEVERITIES:
            errors.append(f"{path}.severity: invalid value")
        if issue.get("owner_layer") not in OWNERS:
            errors.append(f"{path}.owner_layer: invalid value")
        if issue.get("confidence") not in CONFIDENCE:
            errors.append(f"{path}.confidence: invalid value")
        if not isinstance(issue.get("failed_checks"), list) or any(key not in CHECK_KEYS for key in issue.get("failed_checks", [])):
            errors.append(f"{path}.failed_checks: invalid check reference")
        if not isinstance(issue.get("source_artifacts"), list) or not issue.get("source_artifacts"):
            errors.append(f"{path}.source_artifacts: must be a non-empty array")
        for key in ("evidence", "expected", "actual", "impact", "recommended_change", "regression_rule"):
            if not nonempty(issue.get(key)):
                errors.append(f"{path}.{key}: must be non-empty")

    cjk_qa_ok = qa.get("final_reopen_cjk_render_reviewed") == "pass"
    if not cjk_qa_ok and not any(issue.get("finding_code") == "CJK_GLYPH_RENDER_MISSING" for issue in valid_issues):
        errors.append("report.issues: missing CJK_GLYPH_RENDER_MISSING when final reopen CJK evidence is absent or failed")

    delivery = report.get("delivery_efficiency")
    require_keys(delivery, {
        "status", "profile", "total_bytes", "media_share_of_file", "blocker_count",
        "warning_count", "exception_reason", "evidence",
    }, "report.delivery_efficiency", errors)
    package_media = inventory.get("package_media")
    if not isinstance(package_media, dict):
        errors.append("inventory.package_media: independent package media evidence is required")
        package_media = {}
    if isinstance(delivery, dict):
        status = delivery.get("status")
        if status not in {"pass", "fail", "uncertain"}:
            errors.append("report.delivery_efficiency.status: invalid value")
        if status == "uncertain" and report.get("run_status") != "incomplete-evidence":
            errors.append("report.delivery_efficiency.status: uncertain requires incomplete-evidence")
        if delivery.get("profile") != qa.get("delivery_profile"):
            errors.append("report.delivery_efficiency.profile: must match Output QA")
        if delivery.get("total_bytes") != package_media.get("total_bytes"):
            errors.append("report.delivery_efficiency.total_bytes: must match independent package inventory")
        for key in ("blocker_count", "warning_count"):
            if not isinstance(delivery.get(key), int) or delivery.get(key, -1) < 0:
                errors.append(f"report.delivery_efficiency.{key}: must be a non-negative integer")
        share = delivery.get("media_share_of_file")
        if not isinstance(share, (int, float)) or share < 0 or share > 1:
            errors.append("report.delivery_efficiency.media_share_of_file: must be between 0 and 1")
        if not nonempty(delivery.get("evidence")):
            errors.append("report.delivery_efficiency.evidence: must be non-empty")
        independent_payload_issues = any(package_media.get(key) for key in (
            "duplicate_media_groups", "embedded_font_parts", "embedding_parts", "audio_video_parts",
        ))
        if status == "pass" and independent_payload_issues:
            errors.append("report.delivery_efficiency.status: cannot pass with duplicate media or embedded payloads")
        if status == "pass" and (qa.get("size_audit_reviewed") != "pass" or delivery.get("blocker_count") != 0):
            errors.append("report.delivery_efficiency.status: pass requires reviewed size audit with zero blockers")
        delivery_failure_codes = {
            "PPTX_LIGHTWEIGHT_PROFILE_MISSING", "PPTX_DUPLICATE_OR_UNUSED_MEDIA",
            "PPTX_RASTER_OVERSIZED", "PPTX_UNEXPECTED_EMBEDDED_PAYLOAD",
        }
        if status == "fail" and not any(issue.get("finding_code") in delivery_failure_codes for issue in valid_issues):
            errors.append("report.issues: delivery failure requires a PPTX delivery-efficiency finding")

    pairs = issue_lookup(valid_issues)
    package_order = [slide.get("slide_id") for slide in package.get("logic_layer", {}).get("slides", [])]
    logic_by_id = {
        slide.get("slide_id"): slide
        for slide in package.get("logic_layer", {}).get("slides", [])
        if isinstance(slide, dict)
    }
    plan_slides = plan.get("slides", [])
    qa_by_id = {slide.get("slide_id"): slide for slide in qa.get("slides", []) if isinstance(slide, dict)}
    inventory_by_id = {slide.get("slide_id"): slide for slide in inventory.get("slides", []) if isinstance(slide, dict)}
    report_slides = report.get("slides")
    if not isinstance(report_slides, list):
        errors.append("report.slides: must be an array")
        return errors
    if [slide.get("slide_id") for slide in report_slides if isinstance(slide, dict)] != package_order:
        errors.append("report.slides: order must exactly match package")

    any_uncertain = False
    check_evidence_seen: dict[str, str] = {}
    for index, (plan_slide, report_slide) in enumerate(zip(plan_slides, report_slides)):
        path = f"report.slides[{index}]"
        require_keys(report_slide, {"slide_id", "render_file", "planned", "actual_objects", "rendered", "checks"}, path, errors)
        if not isinstance(report_slide, dict):
            continue
        slide_id = report_slide.get("slide_id")
        logic_slide = logic_by_id.get(slide_id, {})
        is_body = logic_slide.get("narrative_role") not in {"cover", "closing"}
        planned = report_slide.get("planned")
        require_keys(planned, {"first_visual", "area_signature", "silhouette_family", "density_class", "dominant_medium", "structure_signature", "structure_type", "series_id", "series_behavior", "motif_id", "semantic_whitespace_mode", "context_rail_enabled", "semantic_tree_id", "semantic_tree_mode", "visual_self_correction_required", "required_object_types", "minimum_object_counts", "target_type_counts", "audience_detail_min_pt", "chart_text_min_pt", "data_chart_contract", "quantitative_execution_contract"}, f"{path}.planned", errors)
        expected_counts = target_counts(plan_slide)
        execution = plan_slide.get("medium_execution_contract", {})
        if isinstance(planned, dict):
            if planned.get("first_visual") != plan_slide.get("design_intent", {}).get("first_visual"):
                errors.append(f"{path}.planned.first_visual: must match Art Direction")
            if planned.get("area_signature") != area_signature(plan_slide):
                errors.append(f"{path}.planned.area_signature: must be derived from Art Direction area_plan")
            if planned.get("silhouette_family") != plan_slide.get("silhouette_family"):
                errors.append(f"{path}.planned.silhouette_family: must match Art Direction")
            if planned.get("density_class") != plan_slide.get("density_class"):
                errors.append(f"{path}.planned.density_class: must match Art Direction")
            if planned.get("dominant_medium") != plan_slide.get("dominant_medium"):
                errors.append(f"{path}.planned.dominant_medium: must match plan")
            if planned.get("structure_signature") != plan_slide.get("structure_signature"):
                errors.append(f"{path}.planned.structure_signature: must match plan")
            if planned.get("structure_type") != execution.get("structure_type"):
                errors.append(f"{path}.planned.structure_type: must match plan")
            series_contract = plan_slide.get("series_visual_contract", {})
            if planned.get("series_id") != series_contract.get("series_id"):
                errors.append(f"{path}.planned.series_id: must match plan")
            if planned.get("series_behavior") != series_contract.get("behavior"):
                errors.append(f"{path}.planned.series_behavior: must match plan")
            if planned.get("motif_id") != plan_slide.get("motif_id"):
                errors.append(f"{path}.planned.motif_id: must match plan")
            if planned.get("semantic_whitespace_mode") != plan_slide.get("semantic_whitespace", {}).get("mode"):
                errors.append(f"{path}.planned.semantic_whitespace_mode: must match plan")
            if planned.get("context_rail_enabled") != plan_slide.get("persistent_context_rail", {}).get("enabled"):
                errors.append(f"{path}.planned.context_rail_enabled: must match plan")
            semantic_tree = plan_slide.get("semantic_layout_tree", {})
            if planned.get("semantic_tree_id") != semantic_tree.get("tree_id"):
                errors.append(f"{path}.planned.semantic_tree_id: must match plan")
            if planned.get("semantic_tree_mode") != semantic_tree.get("mode"):
                errors.append(f"{path}.planned.semantic_tree_mode: must match plan")
            correction = plan_slide.get("ab_review", {}).get("visual_self_correction", {})
            if planned.get("visual_self_correction_required") is not correction.get("required"):
                errors.append(f"{path}.planned.visual_self_correction_required: must match plan")
            if planned.get("required_object_types") != execution.get("required_object_types"):
                errors.append(f"{path}.planned.required_object_types: must match plan")
            if planned.get("minimum_object_counts") != execution.get("minimum_object_counts"):
                errors.append(f"{path}.planned.minimum_object_counts: must match plan")
            if planned.get("target_type_counts") != expected_counts:
                errors.append(f"{path}.planned.target_type_counts: must be derived from plan")
            typography = plan.get("typography_contract", {})
            if planned.get("audience_detail_min_pt") != typography.get("audience_detail_min_pt"):
                errors.append(f"{path}.planned.audience_detail_min_pt: must match Art Direction")
            if planned.get("chart_text_min_pt") != typography.get("chart_text_min_pt"):
                errors.append(f"{path}.planned.chart_text_min_pt: must match Art Direction")
            if planned.get("data_chart_contract") != execution.get("data_chart_contract"):
                errors.append(f"{path}.planned.data_chart_contract: must match Art Direction")
            if planned.get("quantitative_execution_contract") != execution.get("quantitative_execution_contract"):
                errors.append(f"{path}.planned.quantitative_execution_contract: must match Art Direction")

        actual = report_slide.get("actual_objects")
        require_keys(actual, REQUIRED_INVENTORY, f"{path}.actual_objects", errors)
        source_inventory = inventory_by_id.get(slide_id, {}).get("inventory")
        if isinstance(actual, dict) and isinstance(source_inventory, dict):
            for key in REQUIRED_INVENTORY:
                if actual.get(key) != source_inventory.get(key):
                    errors.append(f"{path}.actual_objects.{key}: must match object inventory")
        else:
            errors.append(f"{path}.actual_objects: missing matching inventory slide")

        rendered = report_slide.get("rendered")
        require_keys(rendered, {"medium_label", "first_visual_observed", "area_plan_observed", "series_backbone_observed", "motif_observed", "semantic_whitespace_observed", "context_rail_observed", "semantic_tree_observed", "visual_self_correction_evidence_observed", "minimum_audience_text_pt_observed", "nonconforming_point_sizes_observed", "scatter_label_evidence", "scatter_line_evidence", "recognizability", "evidence"}, f"{path}.rendered", errors)
        if isinstance(rendered, dict):
            if rendered.get("medium_label") not in MEDIA_LABELS:
                errors.append(f"{path}.rendered.medium_label: invalid value")
            if rendered.get("recognizability") not in {"pass", "fail", "uncertain"}:
                errors.append(f"{path}.rendered.recognizability: invalid value")
            if rendered.get("recognizability") == "uncertain":
                any_uncertain = True
            for key in ("first_visual_observed", "area_plan_observed", "series_backbone_observed", "motif_observed", "semantic_whitespace_observed", "context_rail_observed", "semantic_tree_observed", "visual_self_correction_evidence_observed", "scatter_label_evidence", "scatter_line_evidence", "evidence"):
                if not nonempty(rendered.get(key)):
                    errors.append(f"{path}.rendered.{key}: must be non-empty")
            rendered_evidence = str(rendered.get("evidence", ""))
            if nonempty(slide_id) and slide_id.casefold() not in rendered_evidence.casefold():
                errors.append(f"{path}.rendered.evidence: must cite the stable slide_id")
            observed_min = rendered.get("minimum_audience_text_pt_observed")
            if observed_min is not None and (not isinstance(observed_min, (int, float)) or observed_min <= 0):
                errors.append(f"{path}.rendered.minimum_audience_text_pt_observed: must be null or a positive number")
            if is_body and not isinstance(observed_min, (int, float)):
                errors.append(f"{path}.rendered.minimum_audience_text_pt_observed: body slides require a measured number")
            nonconforming_sizes = rendered.get("nonconforming_point_sizes_observed")
            if not isinstance(nonconforming_sizes, list) or any(not isinstance(value, (int, float)) for value in nonconforming_sizes or []):
                errors.append(f"{path}.rendered.nonconforming_point_sizes_observed: must be a numeric array")

        checks = report_slide.get("checks")
        require_keys(checks, CHECK_KEYS, f"{path}.checks", errors)
        failed_checks: set[str] = set()
        if isinstance(checks, dict):
            unknown = set(checks) - CHECK_KEYS
            if unknown:
                errors.append(f"{path}.checks: unknown checks {sorted(unknown)}")
            for key in CHECK_KEYS:
                check = checks.get(key)
                require_keys(check, {"status", "evidence"}, f"{path}.checks.{key}", errors)
                if isinstance(check, dict):
                    status = check.get("status")
                    if status not in CHECK_STATUS:
                        errors.append(f"{path}.checks.{key}.status: invalid value")
                    elif status == "fail":
                        failed_checks.add(key)
                    elif status == "uncertain":
                        any_uncertain = True
                    register_check_evidence(
                        check.get("evidence"),
                        slide_id,
                        f"{path}.checks.{key}.evidence",
                        check_evidence_seen,
                        errors,
                    )
        covered = {
            check
            for issue in valid_issues
            if issue.get("slide_id") == slide_id
            for check in issue.get("failed_checks", [])
        }
        for check in failed_checks - covered:
            errors.append(f"{path}.checks.{check}: failed check must be covered by an issue")

        medium = plan_slide.get("dominant_medium")
        table_count = actual.get("tables", 0) if isinstance(actual, dict) else 0
        chart_count = actual.get("charts", 0) if isinstance(actual, dict) else 0
        alternative = execution.get("approved_alternative") if isinstance(execution, dict) else None
        table_alternative = isinstance(alternative, dict) and alternative.get("from_object_type") == "native-table"
        chart_alternative = isinstance(alternative, dict) and alternative.get("from_object_type") == "native-chart"
        required_codes: list[str] = []
        if medium == "table" and not table_alternative and expected_counts["table-cell"] == 0:
            required_codes.append("PLAN_TABLE_WITHOUT_TABLE_CELL")
        if medium == "table" and not table_alternative and table_count == 0:
            required_codes.append("BUILD_TABLE_MISSING")
        if medium == "data-chart" and not chart_alternative and chart_count == 0:
            required_codes.append("BUILD_CHART_MISSING")
        missing_objects = missing_required_object_types(execution, actual)
        if any(object_type not in {"native-table", "native-chart"} for object_type in missing_objects):
            required_codes.append("BUILD_REQUIRED_OBJECT_MISSING")
        if isinstance(rendered, dict) and rendered.get("recognizability") == "fail":
            required_codes.append("RENDERED_MEDIUM_UNCLEAR")
        if "art_direction_build_fidelity" in failed_checks:
            required_codes.append("ART_DIRECTION_NOT_EXECUTED")
        if "art_direction_first_visual_fidelity" in failed_checks:
            required_codes.append("ART_DIRECTION_FIRST_VISUAL_DRIFT")
        if "art_direction_area_plan_fidelity" in failed_checks:
            required_codes.append("ART_DIRECTION_AREA_PLAN_DRIFT")
        if "art_direction_rhythm_fidelity" in failed_checks:
            required_codes.append("ART_DIRECTION_RHYTHM_DRIFT")
        if "purposeful_series_fidelity" in failed_checks:
            if plan_slide.get("series_visual_contract", {}).get("series_id") is None:
                required_codes.append("UNJUSTIFIED_SILHOUETTE_REPETITION")
            else:
                required_codes.append("PURPOSEFUL_SERIES_BROKEN")
        if "cross_slide_invariant_fidelity" in failed_checks:
            required_codes.append("CROSS_SLIDE_INVARIANT_DRIFT")
        if "semantic_whitespace_fidelity" in failed_checks:
            semantic_codes = {
                ("SEMANTIC_WHITESPACE_FILLED", slide_id),
                ("ART_DIRECTION_FALSE_SEMANTIC_WHITESPACE", slide_id),
            }
            if not semantic_codes & pairs:
                errors.append(f"{path}: semantic whitespace failure requires FILLED or FALSE_CLAIM finding")
        if "motif_fidelity" in failed_checks:
            required_codes.append("MOTIF_SEQUENCE_DRIFT")
        if "context_rail_fidelity" in failed_checks:
            required_codes.append("CONTEXT_RAIL_UI_DRIFT")
        if "semantic_layout_tree_fidelity" in failed_checks:
            required_codes.append("SEMANTIC_LAYOUT_TREE_FLATTENED")
        if "visual_self_correction_integrity" in failed_checks:
            correction_codes = {
                ("VISUAL_SELF_CORRECTION_EVIDENCE_MISSING", slide_id),
                ("CANDIDATE_DIVERSITY_COLLAPSED", slide_id),
                ("AUTOMATIC_SCORE_SELECTED_LAYOUT", slide_id),
            }
            if not correction_codes & pairs:
                errors.append(f"{path}: visual self-correction failure requires missing-evidence, diversity-collapse, or automatic-score finding")
        if "deviation_authorization" in failed_checks:
            required_codes.append("BUILD_UNAPPROVED_DEVIATION")
        if "inherited_chrome_fidelity" in failed_checks:
            chrome_codes = {
                ("MASTER_PAGE_NUMBER_DUPLICATED", slide_id),
                ("TITLE_CHROME_DUPLICATED", slide_id),
            }
            if not chrome_codes & pairs:
                errors.append(f"{path}: inherited chrome failure requires page-number or title-chrome duplication finding")
        observed_min = rendered.get("minimum_audience_text_pt_observed") if isinstance(rendered, dict) else None
        observed_nonconforming = rendered.get("nonconforming_point_sizes_observed", []) if isinstance(rendered, dict) else []
        if isinstance(observed_min, (int, float)) and observed_min < policy.audience_minimum_pt:
            if "typography_legibility" not in failed_checks:
                errors.append(f"{path}.checks.typography_legibility: must fail when observed audience text is below configured minimum")
            required_codes.append("FONT_SIZE_BELOW_MINIMUM")
        if observed_nonconforming:
            if "typography_legibility" not in failed_checks:
                errors.append(f"{path}.checks.typography_legibility: must fail when nonconforming point sizes are observed")
            required_codes.append("FONT_SIZE_NONCONFORMING_TOKEN")
        if "typography_legibility" in failed_checks:
            typography_codes = {
                ("FONT_SIZE_BELOW_MINIMUM", slide_id),
                ("FONT_SIZE_NONCONFORMING_TOKEN", slide_id),
            }
            if not typography_codes & pairs:
                errors.append(f"{path}: typography failure requires a minimum-size or nonconforming-token finding")
        chart_contract = execution.get("data_chart_contract") if isinstance(execution, dict) else None
        is_scatter = isinstance(chart_contract, dict) and chart_contract.get("chart_type") == "scatter"
        if "scatter_semantics_and_labels" in failed_checks:
            scatter_codes = {
                ("SCATTER_ENTITY_LABEL_MISSING_OR_UNREADABLE", slide_id),
                ("SCATTER_UNJUSTIFIED_POINT_CONNECTIONS", slide_id),
            }
            if not scatter_codes & pairs:
                errors.append(f"{path}: scatter failure requires a label or point-connection finding")
        if not is_scatter and isinstance(checks, dict) and checks.get("scatter_semantics_and_labels", {}).get("status") == "pass":
            errors.append(f"{path}.checks.scatter_semantics_and_labels: non-scatter slides must be not-applicable")
        if is_scatter and isinstance(checks, dict) and checks.get("scatter_semantics_and_labels", {}).get("status") == "not-applicable":
            errors.append(f"{path}.checks.scatter_semantics_and_labels: scatter slides cannot be not-applicable")
        if is_body and isinstance(checks, dict) and checks.get("typography_legibility", {}).get("status") == "not-applicable":
            errors.append(f"{path}.checks.typography_legibility: body slides cannot be not-applicable")
        for code in required_codes:
            if (code, slide_id) not in pairs:
                errors.append(f"{path}: deterministic finding {code} must be reported")

        qa_checks = qa_by_id.get(slide_id, {}).get("checks", {})
        qa_rendered_structure = qa_by_id.get(slide_id, {}).get("rendered_structure_type")
        structure_divergence = qa_rendered_structure not in {None, execution.get("structure_type")}
        divergence = (
            bool(required_codes)
            or structure_divergence
            or bool(failed_checks & {
                "plan_object_fidelity", "object_render_fidelity", "semantic_whitespace_fidelity",
                "inherited_chrome_fidelity", "typography_legibility", "scatter_semantics_and_labels",
                "semantic_layout_tree_fidelity", "visual_self_correction_integrity",
            })
        )
        qa_passed_divergence = any(qa_checks.get(key) == "pass" for key in (
            "object_types_preserved", "material_type_fit", "art_direction_first_visual_fidelity",
            "art_direction_area_plan_fidelity", "art_direction_rhythm_fidelity",
            "purposeful_series_fidelity", "cross_slide_invariant_fidelity",
            "semantic_whitespace_fidelity", "motif_fidelity", "context_rail_fidelity",
            "semantic_layout_tree_fidelity",
            "unapproved_deviation_absent", "inherited_chrome_uniqueness",
            "font_size_discipline", "scatter_semantics_and_labels",
        ))
        if divergence and qa_passed_divergence and ("QA_FALSE_PASS", slide_id) not in pairs:
            errors.append(f"{path}: QA_FALSE_PASS required when QA passes an Art Direction or medium divergence")

    if valid_issues and report.get("run_status") in {"clean", "complete-with-deferred-acceptance"}:
        errors.append("report.run_status: cannot be a clean completion state when issues exist")
    if not valid_issues and report.get("run_status") == "issues-found":
        errors.append("report.run_status: issues-found requires at least one issue")
    if any_uncertain and report.get("run_status") != "incomplete-evidence":
        errors.append("report.run_status: uncertain evidence requires incomplete-evidence")
    if not valid_issues and not any_uncertain and report.get("run_status") in {"clean", "complete-with-deferred-acceptance"}:
        expected_completion = "complete-with-deferred-acceptance" if has_deferred_target_acceptance(report) else "clean"
        if report.get("run_status") != expected_completion:
            errors.append(f"report.run_status: expected {expected_completion} from target-application acceptance")

    attribution = report.get("responsibility_attribution")
    require_keys(attribution, {"mode", "confidence", "rationale"}, "report.responsibility_attribution", errors)
    if isinstance(attribution, dict):
        if attribution.get("confidence") not in CONFIDENCE:
            errors.append("report.responsibility_attribution.confidence: invalid value")
        if not nonempty(attribution.get("rationale")):
            errors.append("report.responsibility_attribution.rationale: must be non-empty")
        if attribution.get("mode") == "weighted":
            weights = attribution.get("weights")
            if not isinstance(weights, dict) or not weights or any(key not in OWNERS for key in weights):
                errors.append("report.responsibility_attribution.weights: invalid owner weights")
            elif any(not isinstance(value, int) or value < 0 for value in weights.values()) or sum(weights.values()) != 100:
                errors.append("report.responsibility_attribution.weights: integer weights must sum to 100")
        elif attribution.get("mode") == "qualitative":
            for key in ("primary", "secondary"):
                values = attribution.get(key)
                if not isinstance(values, list) or any(value not in OWNERS for value in values):
                    errors.append(f"report.responsibility_attribution.{key}: invalid owners")
        else:
            errors.append("report.responsibility_attribution.mode: must be weighted or qualitative")

    if not isinstance(report.get("deck_findings"), list):
        errors.append("report.deck_findings: must be an array")
    recommendations = report.get("recommendations")
    if not isinstance(recommendations, list):
        errors.append("report.recommendations: must be an array")
    else:
        for index, item in enumerate(recommendations):
            path = f"report.recommendations[{index}]"
            require_keys(item, {"priority", "target_layer", "change", "verification", "scope"}, path, errors)
            if isinstance(item, dict):
                if not isinstance(item.get("priority"), int) or item.get("priority", 0) < 1:
                    errors.append(f"{path}.priority: must be a positive integer")
                if item.get("target_layer") not in OWNERS:
                    errors.append(f"{path}.target_layer: invalid value")
                for key in ("change", "verification", "scope"):
                    if not nonempty(item.get(key)):
                        errors.append(f"{path}.{key}: must be non-empty")

    asset_observations = report.get("asset_observations")
    if asset_observations is not None:
        if not isinstance(asset_observations, list):
            errors.append("report.asset_observations: must be an array when present")
        else:
            for index, item in enumerate(asset_observations):
                path = f"report.asset_observations[{index}]"
                require_keys(item, {
                    "asset_id", "task_fit", "execution_effect", "conflict_signal",
                    "neighbor_value", "reuse_note", "evidence",
                }, path, errors)
                if not isinstance(item, dict):
                    continue
                if not nonempty(item.get("asset_id")):
                    errors.append(f"{path}.asset_id: must be non-empty")
                for key in ("task_fit", "execution_effect", "neighbor_value"):
                    value = item.get(key)
                    if not isinstance(value, int) or value < 1 or value > 5:
                        errors.append(f"{path}.{key}: must be an integer from 1 to 5")
                for key in ("conflict_signal", "reuse_note", "evidence"):
                    if not nonempty(item.get(key)):
                        errors.append(f"{path}.{key}: must be non-empty")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("qa", type=Path)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--pptx", type=Path, required=True)
    parser.add_argument("--render-root", type=Path)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--runtime-preflight", type=Path, required=True)
    args = parser.parse_args()
    try:
        documents = [json.loads(path.read_text(encoding="utf-8")) for path in (args.package, args.plan, args.qa, args.inventory, args.report)]
        runtime_preflight_raw = args.runtime_preflight.read_bytes()
        runtime_preflight = json.loads(runtime_preflight_raw)
        resolved_config_raw = args.config.read_bytes()
        resolved_config = json.loads(resolved_config_raw)
        output_qa_validator.qa_path_parent = args.qa.resolve().parent
        errors = validate_report(
            *documents,
            load_policy(args.config),
            pptx=args.pptx,
            render_root=args.render_root,
            report_path=args.report,
            runtime_preflight=runtime_preflight,
            runtime_preflight_sha256=hashlib.sha256(runtime_preflight_raw).hexdigest(),
            resolved_config=resolved_config,
            resolved_config_sha256=hashlib.sha256(resolved_config_raw).hexdigest(),
        )
    except (OSError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAILED: {len(errors)} error(s)")
        return 1
    print(f"PASS: supervision report {documents[-1].get('package_id')} ({len(documents[-1].get('slides', []))} slides)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
