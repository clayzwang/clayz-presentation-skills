#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Memory-only creation and validation for immutable five-stage work records."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTRACT = "io.clayz.presentation.stage-work-record/1.0"
STAGES = ("logic", "copy", "art-direction", "output", "supervisor")
CHECK_STATUSES = frozenset(("pass", "fail", "deferred"))
SHA256 = re.compile(r"^[0-9a-f]{64}$")
LEGACY_RECORD_FIELDS = frozenset(
    ("contract", "stage", "run_id", "task_request_sha256", "recorded_at", "summary",
     "decisions", "checks", "open_issues", "artifacts", "previous_record_sha256", "record_sha256")
)
RECORD_FIELDS = LEGACY_RECORD_FIELDS | frozenset(("readiness", "calibration_bindings", "acceptance_contract"))
CHECK_FIELDS = frozenset(("name", "status", "evidence_roles"))
EXTENDED_CHECK_FIELDS = CHECK_FIELDS | frozenset(("blocking",))
ARTIFACT_FIELDS = frozenset(("path", "sha256", "bytes"))

CALIBRATION_CONTRACT = "io.clayz.presentation.supervisor-calibration/1.0"
CALIBRATION_STEPS = (
    {"step": "logic-to-copy", "source_stage": "logic", "target_stage": "copy", "recipients": ["copy", "supervisor"]},
    {"step": "copy-to-art-direction", "source_stage": "copy", "target_stage": "art-direction", "recipients": ["art-direction", "supervisor"]},
    {"step": "art-direction-to-output", "source_stage": "art-direction", "target_stage": "output", "recipients": ["output", "supervisor"]},
)
CALIBRATION_RECORD_FIELDS = frozenset(
    (
        "contract", "calibration_id", "run_id", "task_request_sha256", "step", "source_stage", "target_stage",
        "recipients", "source_records", "expected_source_kinds", "source_artifacts", "acceptance_contract",
        "shared_rules", "findings", "recorded_at", "previous_calibration_sha256", "record_sha256",
    )
)
CALIBRATION_BINDING_FIELDS = frozenset(
    ("calibration_id", "calibration_artifact", "record_sha256", "finding_dispositions")
)
FINDING_DISPOSITION_FIELDS = frozenset(("finding_id", "disposition", "reason"))
CALIBRATION_DISPOSITIONS = frozenset(("accepted", "partially-accepted", "declined", "deferred"))
READINESS_STATES = frozenset(("ready", "quality-limited", "blocked"))


class StageWorkRecordError(ValueError):
    """Detailed validation errors for a stage record or chain."""

    def __init__(self, errors: str | Sequence[str]) -> None:
        self.errors = [errors] if isinstance(errors, str) else [str(e) for e in errors if str(e)]
        super().__init__("; ".join(self.errors) or "invalid stage work record")


WorkRecordValidationError = StageWorkRecordError
ValidationError = StageWorkRecordError


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise StageWorkRecordError(f"value is not canonical JSON: {exc}") from exc


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def canonical_record_sha256(record: Mapping[str, Any]) -> str:
    if not isinstance(record, Mapping):
        raise StageWorkRecordError("record: must be an object")
    body = dict(record)
    body.pop("record_sha256", None)
    return canonical_sha256(body)


record_sha256 = canonical_record_sha256


def _err(path: str, message: str) -> str:
    return f"{path}: {message}"


def _sha(value: Any) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def _record_readiness(record: Mapping[str, Any]) -> str:
    """Resolve readiness while preserving the meaning of legacy records."""

    declared = record.get("readiness")
    if declared in READINESS_STATES:
        return str(declared)
    checks = record.get("checks") if isinstance(record.get("checks"), list) else []
    blocking_failure = any(
        isinstance(check, Mapping) and check.get("status") == "fail" and check.get("blocking", True) is True
        for check in checks
    )
    return "blocked" if blocking_failure or record.get("open_issues") else "ready"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _time(value: Any, path: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(_err(path, "must be a timezone-aware ISO timestamp"))
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(_err(path, "must be a timezone-aware ISO timestamp"))
        return None
    if parsed.utcoffset() is None:
        errors.append(_err(path, "must include a timezone"))
        return None
    return parsed.astimezone(timezone.utc)


def _binding(challenge: Mapping[str, Any]) -> tuple[str, str]:
    """Bind supplied runtime-preflight values without attesting host claims."""
    if not isinstance(challenge, Mapping):
        raise StageWorkRecordError("challenge: must be an object")
    nested = challenge.get("run_binding")
    if nested is not None and not isinstance(nested, Mapping):
        raise StageWorkRecordError("challenge.run_binding: must be an object")
    source = nested if isinstance(nested, Mapping) else challenge
    if isinstance(nested, Mapping):
        for key in ("run_id", "task_request_sha256"):
            if key in challenge and challenge.get(key) != nested.get(key):
                raise StageWorkRecordError(f"challenge.{key}: conflicts with challenge.run_binding.{key}")
    run_id, task_sha = source.get("run_id"), source.get("task_request_sha256")
    if not isinstance(run_id, str) or not run_id.strip():
        raise StageWorkRecordError("challenge.run_id: must be a non-empty string")
    if not _sha(task_sha):
        raise StageWorkRecordError("challenge.task_request_sha256: must be a lowercase SHA-256")
    return run_id.strip(), str(task_sha)


def _strings(value: Any, path: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        errors.append(_err(path, "must be an array of non-empty strings"))
        return []
    return list(value)


def _draft(draft: Mapping[str, Any], *, calibrated: bool = False) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(draft, Mapping):
        return {}, [_err("draft", "must be an object")]
    summary = draft.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        errors.append(_err("draft.summary", "must be a non-empty string"))
    decisions = _strings(draft.get("decisions", []), "draft.decisions", errors)
    checks_raw = draft.get("checks")
    checks: list[dict[str, Any]] = []
    if not isinstance(checks_raw, list) or not checks_raw:
        errors.append(_err("draft.checks", "must be a non-empty array"))
    else:
        names: set[str] = set()
        for i, check in enumerate(checks_raw):
            path = f"draft.checks[{i}]"
            if not isinstance(check, Mapping):
                errors.append(_err(path, "must be an object"))
                continue
            name, status, roles = check.get("name"), check.get("status"), check.get("evidence_roles", [])
            # Historical drafts treated every failed check as a handoff blocker.
            # A new run must opt into a quality-only failure explicitly with
            # ``blocking: false`` so old records retain their meaning.
            blocking = check.get("blocking", False if calibrated and status == "fail" else True)
            if not isinstance(name, str) or not name.strip() or name in names:
                errors.append(_err(path + ".name", "must be non-empty and unique"))
            else:
                names.add(name)
            if status not in CHECK_STATUSES:
                errors.append(_err(path + ".status", "must be pass, fail, or deferred"))
            if not isinstance(blocking, bool):
                errors.append(_err(path + ".blocking", "must be boolean when supplied"))
            role_values = _strings(roles, path + ".evidence_roles", errors)
            if status == "pass" and not role_values:
                errors.append(_err(path + ".evidence_roles", "a passing check requires evidence roles"))
            if len(role_values) != len(set(role_values)):
                errors.append(_err(path + ".evidence_roles", "must not contain duplicates"))
            check_value = {"name": name, "status": status, "evidence_roles": role_values}
            if "blocking" in check or calibrated and status == "fail":
                check_value["blocking"] = bool(blocking)
            checks.append(check_value)
    issues = _strings(draft.get("open_issues", []), "draft.open_issues", errors)
    fields: dict[str, Any] = {"summary": summary, "decisions": decisions, "checks": checks, "open_issues": issues}
    if "readiness" in draft:
        readiness = draft.get("readiness")
        if readiness not in READINESS_STATES:
            errors.append(_err("draft.readiness", "must be ready, quality-limited, or blocked"))
        else:
            fields["readiness"] = readiness
    if "calibration_bindings" in draft:
        fields["calibration_bindings"] = draft.get("calibration_bindings")
    if "acceptance_contract" in draft:
        fields["acceptance_contract"] = draft.get("acceptance_contract")
    return fields, errors


def _artifacts(artifacts: Mapping[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(artifacts, Mapping) or not artifacts:
        return {}, [_err("artifacts", "must contain at least one artifact")]
    for role, supplied in artifacts.items():
        path_label = f"artifacts[{role!r}]"
        if not isinstance(role, str) or not role.strip():
            errors.append(_err("artifacts", "roles must be non-empty strings"))
            continue
        raw_path = supplied.get("path") if isinstance(supplied, Mapping) else supplied
        try:
            path = Path(raw_path).expanduser().resolve()
            raw = path.read_bytes()
        except (TypeError, ValueError, OSError) as exc:
            errors.append(_err(path_label, f"file cannot be read: {exc}"))
            continue
        if not path.is_absolute():
            errors.append(_err(path_label, "path must be absolute"))
            continue
        result[role] = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    return result, errors


def _artifact_meta_errors(value: Any, path: str, errors: list[str], *, verify_files: bool = True) -> None:
    if not isinstance(value, Mapping) or set(value) != ARTIFACT_FIELDS:
        errors.append(_err(path, f"fields must be exactly {sorted(ARTIFACT_FIELDS)}"))
        return
    artifact_path, digest, size = value.get("path"), value.get("sha256"), value.get("bytes")
    if not isinstance(artifact_path, str) or not artifact_path.strip() or not Path(artifact_path).is_absolute():
        errors.append(_err(path + ".path", "must be an absolute path"))
        return
    if not _sha(digest):
        errors.append(_err(path + ".sha256", "must be a lowercase SHA-256"))
    if isinstance(size, bool) or not isinstance(size, int) or size < 1:
        errors.append(_err(path + ".bytes", "must be a positive integer"))
    if not verify_files:
        return
    try:
        raw = Path(artifact_path).resolve().read_bytes()
    except OSError as exc:
        errors.append(_err(path, f"file cannot be verified: {exc}"))
        return
    if not raw:
        errors.append(_err(path, "file must not be empty"))
    if _sha(digest) and hashlib.sha256(raw).hexdigest() != digest:
        errors.append(_err(path + ".sha256", "does not match current file bytes"))
    if isinstance(size, int) and not isinstance(size, bool) and len(raw) != size:
        errors.append(_err(path + ".bytes", "does not match current file bytes"))


def _validate_calibration_binding(value: Any, path: str, errors: list[str], *, verify_files: bool = True) -> None:
    if not isinstance(value, Mapping) or set(value) != CALIBRATION_BINDING_FIELDS:
        errors.append(_err(path, f"fields must be exactly {sorted(CALIBRATION_BINDING_FIELDS)}"))
        return
    if not isinstance(value.get("calibration_id"), str) or not value.get("calibration_id", "").strip():
        errors.append(_err(path + ".calibration_id", "must be non-empty"))
    _artifact_meta_errors(value.get("calibration_artifact"), path + ".calibration_artifact", errors, verify_files=verify_files)
    if not _sha(value.get("record_sha256")):
        errors.append(_err(path + ".record_sha256", "must be a lowercase SHA-256"))
    dispositions = value.get("finding_dispositions")
    if not isinstance(dispositions, list):
        errors.append(_err(path + ".finding_dispositions", "must be an array"))
        dispositions = []
    seen: set[str] = set()
    for index, item in enumerate(dispositions):
        item_path = f"{path}.finding_dispositions[{index}]"
        if not isinstance(item, Mapping) or set(item) != FINDING_DISPOSITION_FIELDS:
            errors.append(_err(item_path, f"fields must be exactly {sorted(FINDING_DISPOSITION_FIELDS)}"))
            continue
        finding_id, disposition, reason = item.get("finding_id"), item.get("disposition"), item.get("reason")
        if not isinstance(finding_id, str) or not finding_id.strip() or finding_id in seen:
            errors.append(_err(item_path + ".finding_id", "must be non-empty and unique"))
        else:
            seen.add(finding_id)
        if disposition not in CALIBRATION_DISPOSITIONS:
            errors.append(_err(item_path + ".disposition", "must be accepted, declined, or deferred"))
        if disposition in {"declined", "deferred"} and (not isinstance(reason, str) or not reason.strip()):
            errors.append(_err(item_path + ".reason", "a declined or deferred finding requires a reason"))
        elif not isinstance(reason, str):
            errors.append(_err(item_path + ".reason", "must be a string"))
    if verify_files:
        artifact = value.get("calibration_artifact")
        if isinstance(artifact, Mapping) and isinstance(artifact.get("path"), str):
            try:
                calibration = json.loads(Path(artifact["path"]).read_text(encoding="utf-8"))
                validate_calibration_record(calibration, verify_files=True)
                if calibration.get("calibration_id") != value.get("calibration_id"):
                    errors.append(_err(path, "calibration_id does not match the bound calibration artifact"))
                if calibration.get("record_sha256") != value.get("record_sha256"):
                    errors.append(_err(path, "record_sha256 does not match the calibration artifact"))
            except (OSError, UnicodeError, json.JSONDecodeError, StageWorkRecordError) as exc:
                errors.append(_err(path, f"calibration artifact is invalid: {exc}"))


def _record_errors(
    record: Any, *, expected_run: str | None = None, expected_task: str | None = None,
    expected_stage: str | None = None, previous: Mapping[str, Any] | None = None,
    verify_files: bool = True,
) -> tuple[list[str], datetime | None]:
    errors: list[str] = []
    if not isinstance(record, Mapping):
        return [_err("record", "must be an object")], None
    record_fields = set(record)
    if not LEGACY_RECORD_FIELDS <= record_fields or not record_fields <= RECORD_FIELDS:
        errors.append(_err("record", f"fields must contain legacy fields and only known extensions {sorted(RECORD_FIELDS)}"))
    if record.get("contract") != CONTRACT:
        errors.append(_err("record.contract", f"expected {CONTRACT}"))
    stage = record.get("stage")
    if stage not in STAGES:
        errors.append(_err("record.stage", "must be one of the five governed stages"))
    if expected_stage is not None and stage != expected_stage:
        errors.append(_err("record.stage", f"expected {expected_stage!r}"))
    run = record.get("run_id")
    if not isinstance(run, str) or not run.strip():
        errors.append(_err("record.run_id", "must be a non-empty string"))
    elif expected_run is not None and run != expected_run:
        errors.append(_err("record.run_id", "does not match the run binding"))
    task = record.get("task_request_sha256")
    if not _sha(task):
        errors.append(_err("record.task_request_sha256", "must be a lowercase SHA-256"))
    elif expected_task is not None and task != expected_task:
        errors.append(_err("record.task_request_sha256", "does not match the task binding"))
    recorded = _time(record.get("recorded_at"), "record.recorded_at", errors)
    if not isinstance(record.get("summary"), str) or not record.get("summary", "").strip():
        errors.append(_err("record.summary", "must be a non-empty string"))
    _strings(record.get("decisions"), "record.decisions", errors)

    readiness = record.get("readiness")
    if readiness is not None and readiness not in READINESS_STATES:
        errors.append(_err("record.readiness", "must be ready, quality-limited, or blocked"))

    artifacts = record.get("artifacts")
    roles: set[str] = set()
    if not isinstance(artifacts, Mapping) or not artifacts:
        errors.append(_err("record.artifacts", "must contain at least one artifact"))
    else:
        for role, meta in artifacts.items():
            path = f"record.artifacts[{role!r}]"
            if not isinstance(role, str) or not role.strip():
                errors.append(_err("record.artifacts", "roles must be non-empty strings"))
                continue
            roles.add(role)
            if not isinstance(meta, Mapping) or set(meta) != ARTIFACT_FIELDS:
                errors.append(_err(path, f"fields must be exactly {sorted(ARTIFACT_FIELDS)}"))
                continue
            artifact_path, digest, size = meta.get("path"), meta.get("sha256"), meta.get("bytes")
            if not isinstance(artifact_path, str) or not artifact_path.strip() or not Path(artifact_path).is_absolute():
                errors.append(_err(path + ".path", "must be an absolute path"))
            if not _sha(digest):
                errors.append(_err(path + ".sha256", "must be a lowercase SHA-256"))
            if isinstance(size, bool) or not isinstance(size, int) or size < 0:
                errors.append(_err(path + ".bytes", "must be a non-negative integer"))
            if verify_files and isinstance(artifact_path, str) and Path(artifact_path).is_absolute():
                try:
                    raw = Path(artifact_path).resolve().read_bytes()
                    if _sha(digest) and hashlib.sha256(raw).hexdigest() != digest:
                        errors.append(_err(path, "sha256 does not match current file bytes"))
                    if isinstance(size, int) and not isinstance(size, bool) and len(raw) != size:
                        errors.append(_err(path, "bytes does not match current file bytes"))
                except OSError as exc:
                    errors.append(_err(path, f"file cannot be verified: {exc}"))

    checks = record.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append(_err("record.checks", "must be a non-empty array"))
    else:
        names: set[str] = set()
        for i, check in enumerate(checks):
            path = f"record.checks[{i}]"
            if not isinstance(check, Mapping) or not CHECK_FIELDS <= set(check) or not set(check) <= EXTENDED_CHECK_FIELDS:
                errors.append(_err(path, f"fields must contain {sorted(CHECK_FIELDS)} and only optional blocking"))
                continue
            name, status, evidence = check.get("name"), check.get("status"), check.get("evidence_roles")
            if not isinstance(name, str) or not name.strip() or name in names:
                errors.append(_err(path + ".name", "must be non-empty and unique"))
            else:
                names.add(name)
            if status not in CHECK_STATUSES:
                errors.append(_err(path + ".status", "must be pass, fail, or deferred"))
            if "blocking" in check and not isinstance(check.get("blocking"), bool):
                errors.append(_err(path + ".blocking", "must be boolean"))
            evidence_values = _strings(evidence, path + ".evidence_roles", errors)
            if len(evidence_values) != len(set(evidence_values)):
                errors.append(_err(path + ".evidence_roles", "must not contain duplicates"))
            if any(role not in roles for role in evidence_values):
                errors.append(_err(path + ".evidence_roles", "must reference declared artifacts"))
            if status == "pass" and not evidence_values:
                errors.append(_err(path + ".evidence_roles", "a passing check requires evidence roles"))
    _strings(record.get("open_issues"), "record.open_issues", errors)

    bindings = record.get("calibration_bindings")
    if bindings is not None:
        if not isinstance(bindings, list):
            errors.append(_err("record.calibration_bindings", "must be an array"))
        else:
            for index, binding in enumerate(bindings):
                _validate_calibration_binding(binding, f"record.calibration_bindings[{index}]", errors, verify_files=verify_files)
    acceptance = record.get("acceptance_contract")
    if acceptance is not None:
        _artifact_meta_errors(acceptance, "record.acceptance_contract", errors, verify_files=verify_files)

    prior_hash = record.get("previous_record_sha256")
    if prior_hash is not None and not _sha(prior_hash):
        errors.append(_err("record.previous_record_sha256", "must be null or a lowercase SHA-256"))
    if previous is None:
        if expected_stage == STAGES[0] and prior_hash is not None:
            errors.append(_err("record.previous_record_sha256", "first stage must use null"))
    else:
        previous_digest = previous.get("record_sha256")
        if not _sha(previous_digest):
            errors.append(_err("previous_record.record_sha256", "must be a lowercase SHA-256"))
        elif prior_hash != previous_digest:
            errors.append(_err("record.previous_record_sha256", "does not match the immediate predecessor"))
        try:
            if _sha(previous_digest) and canonical_record_sha256(previous) != previous_digest:
                errors.append(_err("previous_record.record_sha256", "does not match canonical content"))
        except StageWorkRecordError as exc:
            errors.extend(f"previous_record: {e}" for e in exc.errors)
        if previous.get("run_id") != run:
            errors.append(_err("previous_record.run_id", "does not match the current record"))
        if previous.get("task_request_sha256") != task:
            errors.append(_err("previous_record.task_request_sha256", "does not match the current record"))
        previous_time = _time(previous.get("recorded_at"), "previous_record.recorded_at", errors)
        if previous_time is not None and recorded is not None and previous_time > recorded:
            errors.append(_err("record.recorded_at", "must be nondecreasing from the predecessor"))
    digest = record.get("record_sha256")
    if not _sha(digest):
        errors.append(_err("record.record_sha256", "must be a lowercase SHA-256"))
    else:
        try:
            if canonical_record_sha256(record) != digest:
                errors.append(_err("record.record_sha256", "does not match canonical content excluding itself"))
        except StageWorkRecordError as exc:
            errors.extend(f"record: {e}" for e in exc.errors)
    return errors, recorded


def _calibration_spec(step: str) -> dict[str, Any]:
    for item in CALIBRATION_STEPS:
        if item["step"] == step:
            return item
    raise StageWorkRecordError(f"calibration step must be one of {[item['step'] for item in CALIBRATION_STEPS]}")


def _calibration_findings(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(_err(path, "must be an array"))
        return
    seen: set[str] = set()
    for index, finding in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(finding, Mapping):
            errors.append(_err(item_path, "must be an object"))
            continue
        required = {"finding_id", "requirement_ids", "statement", "recommendation", "severity", "blocking"}
        if set(finding) != required:
            errors.append(_err(item_path, f"fields must be exactly {sorted(required)}"))
            continue
        finding_id = finding.get("finding_id")
        if not isinstance(finding_id, str) or not finding_id.strip() or finding_id in seen:
            errors.append(_err(item_path + ".finding_id", "must be non-empty and unique"))
        else:
            seen.add(finding_id)
        requirement_ids = finding.get("requirement_ids")
        if not isinstance(requirement_ids, list) or any(not isinstance(item, str) or not item.strip() for item in requirement_ids) or len(requirement_ids) != len(set(requirement_ids)):
            errors.append(_err(item_path + ".requirement_ids", "must be a unique string array"))
        for key in ("statement", "recommendation"):
            if not isinstance(finding.get(key), str) or not finding.get(key, "").strip():
                errors.append(_err(item_path + "." + key, "must be non-empty"))
        if finding.get("severity") not in {"critical", "major", "moderate", "minor"}:
            errors.append(_err(item_path + ".severity", "invalid value"))
        if not isinstance(finding.get("blocking"), bool):
            errors.append(_err(item_path + ".blocking", "must be boolean"))


def _load_record_file(path: Path, errors: list[str], label: str) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(_err(label, f"cannot read JSON: {exc}"))
        return None
    if not isinstance(value, dict):
        errors.append(_err(label, "must be a JSON object"))
        return None
    return value


def validate_calibration_record(
    calibration: Any,
    *,
    expected_run_id: str | None = None,
    expected_task_request_sha256: str | None = None,
    expected_source_record: Mapping[str, Any] | None = None,
    expected_target_stage: str | None = None,
    verify_files: bool = True,
) -> None:
    """Validate one immutable Supervisor calibration and its source bytes."""

    errors: list[str] = []
    if not isinstance(calibration, Mapping):
        raise StageWorkRecordError("calibration: must be an object")
    if set(calibration) != CALIBRATION_RECORD_FIELDS:
        errors.append(_err("calibration", f"fields must be exactly {sorted(CALIBRATION_RECORD_FIELDS)}"))
    if calibration.get("contract") != CALIBRATION_CONTRACT:
        errors.append(_err("calibration.contract", f"expected {CALIBRATION_CONTRACT}"))
    if not isinstance(calibration.get("calibration_id"), str) or not calibration.get("calibration_id", "").strip():
        errors.append(_err("calibration.calibration_id", "must be non-empty"))
    run, task = calibration.get("run_id"), calibration.get("task_request_sha256")
    if not isinstance(run, str) or not run.strip():
        errors.append(_err("calibration.run_id", "must be non-empty"))
    elif expected_run_id is not None and run != expected_run_id:
        errors.append(_err("calibration.run_id", "does not match the run binding"))
    if not _sha(task):
        errors.append(_err("calibration.task_request_sha256", "must be a lowercase SHA-256"))
    elif expected_task_request_sha256 is not None and task != expected_task_request_sha256:
        errors.append(_err("calibration.task_request_sha256", "does not match the task binding"))
    try:
        spec = _calibration_spec(str(calibration.get("step")))
    except StageWorkRecordError as exc:
        errors.extend(exc.errors)
        spec = None
    if spec is not None:
        for key in ("source_stage", "target_stage", "recipients"):
            if calibration.get(key) != spec[key]:
                errors.append(_err("calibration." + key, f"must match the {spec['step']} calibration topology"))
        if expected_target_stage is not None and calibration.get("target_stage") != expected_target_stage:
            errors.append(_err("calibration.target_stage", "does not match the downstream stage"))
    if not _time(calibration.get("recorded_at"), "calibration.recorded_at", errors):
        pass

    source_records = calibration.get("source_records")
    if not isinstance(source_records, list) or len(source_records) != 1:
        errors.append(_err("calibration.source_records", "must contain exactly the immediate upstream record"))
        source_records = []
    source_ref: Mapping[str, Any] | None = source_records[0] if source_records and isinstance(source_records[0], Mapping) else None
    if source_ref is not None:
        expected = {"stage", "path", "sha256", "bytes"}
        if set(source_ref) != expected:
            errors.append(_err("calibration.source_records[0]", f"fields must be exactly {sorted(expected)}"))
        if source_ref.get("stage") != calibration.get("source_stage"):
            errors.append(_err("calibration.source_records[0].stage", "must match source_stage"))
        _artifact_meta_errors({key: source_ref.get(key) for key in ARTIFACT_FIELDS}, "calibration.source_records[0]", errors, verify_files=verify_files)
        if verify_files and isinstance(source_ref.get("path"), str):
            upstream = _load_record_file(Path(source_ref["path"]), errors, "calibration.source_records[0]")
            if upstream is not None:
                try:
                    validate_record(upstream, run, task, verify_files=True)
                except StageWorkRecordError as exc:
                    errors.extend(_err("calibration.source_records[0]", item) for item in exc.errors)
                if upstream.get("stage") != calibration.get("source_stage"):
                    errors.append(_err("calibration.source_records[0]", "record stage does not match source_stage"))
                if expected_source_record is not None and upstream != expected_source_record:
                    errors.append(_err("calibration.source_records[0]", "does not match the immediate upstream record"))
                upstream_artifacts = upstream.get("artifacts")
                if calibration.get("source_artifacts") != upstream_artifacts:
                    errors.append(_err("calibration.source_artifacts", "must exactly copy immediate upstream artifact refs"))
    source_artifacts = calibration.get("source_artifacts")
    expected_kinds = calibration.get("expected_source_kinds")
    if not isinstance(source_artifacts, Mapping) or not source_artifacts:
        errors.append(_err("calibration.source_artifacts", "must be a non-empty object"))
        source_artifacts = {}
    else:
        for role, artifact in source_artifacts.items():
            if not isinstance(role, str) or not role.strip():
                errors.append(_err("calibration.source_artifacts", "roles must be non-empty strings"))
            _artifact_meta_errors(artifact, f"calibration.source_artifacts[{role!r}]", errors, verify_files=verify_files)
    if not isinstance(expected_kinds, list) or any(not isinstance(item, str) or not item.strip() for item in expected_kinds) or len(expected_kinds) != len(set(expected_kinds)):
        errors.append(_err("calibration.expected_source_kinds", "must be a unique string array"))
    elif set(expected_kinds) != set(source_artifacts):
        errors.append(_err("calibration.expected_source_kinds", "must exactly match source artifact roles"))

    for key in ("acceptance_contract", "shared_rules"):
        _artifact_meta_errors(calibration.get(key), "calibration." + key, errors, verify_files=verify_files)
    if verify_files:
        acceptance = calibration.get("acceptance_contract")
        if isinstance(acceptance, Mapping) and isinstance(acceptance.get("path"), str):
            acceptance_value = _load_record_file(Path(acceptance["path"]), errors, "calibration.acceptance_contract")
            if acceptance_value is not None:
                try:
                    from acceptance_contract import validate_acceptance_contract
                except ImportError:
                    try:
                        from packages.validators.acceptance_contract import validate_acceptance_contract
                    except ImportError as exc:
                        errors.append(_err("calibration.acceptance_contract", f"validator dependency unavailable: {exc}"))
                    else:
                        acceptance_errors: list[str] = []
                        validate_acceptance_contract(acceptance_value, "calibration.acceptance_contract", acceptance_errors)
                        errors.extend(
                            item for item in acceptance_errors
                            if not ("release_conditions[" in item and ".requirement_id" in item)
                        )
                else:
                    acceptance_errors = []
                    validate_acceptance_contract(acceptance_value, "calibration.acceptance_contract", acceptance_errors)
                    errors.extend(
                        item for item in acceptance_errors
                        if not ("release_conditions[" in item and ".requirement_id" in item)
                    )
        shared = calibration.get("shared_rules")
        if isinstance(shared, Mapping) and isinstance(shared.get("path"), str):
            _load_record_file(Path(shared["path"]), errors, "calibration.shared_rules")
    _calibration_findings(calibration.get("findings"), "calibration.findings", errors)
    prior_hash = calibration.get("previous_calibration_sha256")
    if prior_hash is not None and not _sha(prior_hash):
        errors.append(_err("calibration.previous_calibration_sha256", "must be null or a lowercase SHA-256"))
    digest = calibration.get("record_sha256")
    if not _sha(digest):
        errors.append(_err("calibration.record_sha256", "must be a lowercase SHA-256"))
    elif canonical_record_sha256(calibration) != digest:
        errors.append(_err("calibration.record_sha256", "does not match canonical content"))
    if errors:
        raise StageWorkRecordError(errors)


def create_calibration_record(
    step: str,
    source_record_path: Path,
    acceptance_contract_path: Path,
    shared_rules_path: Path,
    findings: list[dict[str, Any]],
    challenge: Mapping[str, Any],
    *,
    output: Path | None = None,
    calibration_id: str | None = None,
    recorded_at: str | None = None,
    previous_calibration: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a calibration from the actual immediate upstream record bytes."""

    spec = _calibration_spec(step)
    run, task = _binding(challenge)
    source_path = Path(source_record_path).expanduser().resolve()
    source_raw = source_path.read_bytes()
    source_record = json.loads(source_raw)
    if not isinstance(source_record, dict):
        raise StageWorkRecordError("source record must be a JSON object")
    validate_record(source_record, run, task, verify_files=True)
    if source_record.get("stage") != spec["source_stage"]:
        raise StageWorkRecordError("source record stage does not match calibration step")
    acceptance = _artifact_meta(acceptance_contract_path)
    shared = _artifact_meta(shared_rules_path)
    calibration: dict[str, Any] = {
        "contract": CALIBRATION_CONTRACT,
        "calibration_id": calibration_id or f"CAL-{step}-{hashlib.sha256(source_raw).hexdigest()[:16]}",
        "run_id": run,
        "task_request_sha256": task,
        "step": step,
        "source_stage": spec["source_stage"],
        "target_stage": spec["target_stage"],
        "recipients": list(spec["recipients"]),
        "source_records": [{"stage": spec["source_stage"], **_artifact_meta(source_path)}],
        "expected_source_kinds": sorted(source_record["artifacts"]),
        "source_artifacts": source_record["artifacts"],
        "acceptance_contract": acceptance,
        "shared_rules": shared,
        "findings": [dict(item) for item in findings],
        "recorded_at": recorded_at or _now(),
        "previous_calibration_sha256": previous_calibration.get("record_sha256") if previous_calibration else None,
    }
    calibration["record_sha256"] = canonical_record_sha256(calibration)
    validate_calibration_record(calibration, expected_run_id=run, expected_task_request_sha256=task)
    if output is not None:
        _write_new(output, calibration)
    return calibration


def _artifact_meta(path: Path) -> dict[str, Any]:
    resolved = Path(path).expanduser().resolve()
    raw = resolved.read_bytes()
    if not raw:
        raise StageWorkRecordError(f"artifact must not be empty: {resolved}")
    return {"path": str(resolved), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    resolved = Path(path).expanduser().resolve()
    if resolved.exists():
        raise FileExistsError(resolved)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def create_calibration_binding(
    calibration_path: Path,
    finding_dispositions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build one downstream binding after reading the current calibration file."""

    path = Path(calibration_path).expanduser().resolve()
    calibration = json.loads(path.read_text(encoding="utf-8"))
    validate_calibration_record(calibration)
    expected_ids = {
        item.get("finding_id") for item in calibration.get("findings", []) if isinstance(item, Mapping)
    }
    seen: set[str] = set()
    for item in finding_dispositions:
        if not isinstance(item, Mapping) or set(item) != FINDING_DISPOSITION_FIELDS:
            raise StageWorkRecordError("finding dispositions must use finding_id, disposition, and reason")
        finding_id = item.get("finding_id")
        if finding_id in seen or finding_id not in expected_ids:
            raise StageWorkRecordError("finding dispositions must cover each calibration finding exactly once")
        seen.add(str(finding_id))
        if item.get("disposition") not in CALIBRATION_DISPOSITIONS:
            raise StageWorkRecordError("finding disposition must be accepted, declined, or deferred")
        if item.get("disposition") in {"declined", "deferred"} and (
            not isinstance(item.get("reason"), str) or not item.get("reason", "").strip()
        ):
            raise StageWorkRecordError("declined or deferred finding dispositions require a reason")
    if seen != expected_ids:
        raise StageWorkRecordError("finding dispositions must cover each calibration finding exactly once")
    return {
        "calibration_id": calibration["calibration_id"],
        "calibration_artifact": _artifact_meta(path),
        "record_sha256": calibration["record_sha256"],
        "finding_dispositions": [dict(item) for item in finding_dispositions],
    }


def validate_calibration_chain(
    records: list[Mapping[str, Any]],
    run_id: str,
    task_request_sha256: str,
    *,
    verify_files: bool = True,
) -> None:
    """Validate the complete Logic→Copy→Art Direction→Output calibration chain."""

    errors: list[str] = []
    if not isinstance(records, list) or len(records) != len(CALIBRATION_STEPS):
        raise StageWorkRecordError(f"calibration chain must contain exactly {len(CALIBRATION_STEPS)} records")
    previous: Mapping[str, Any] | None = None
    for index, (record, spec) in enumerate(zip(records, CALIBRATION_STEPS)):
        try:
            validate_calibration_record(
                record,
                expected_run_id=run_id,
                expected_task_request_sha256=task_request_sha256,
                expected_target_stage=spec["target_stage"],
                verify_files=verify_files,
            )
        except StageWorkRecordError as exc:
            errors.extend(f"calibrations[{index}]: {item}" for item in exc.errors)
        if previous is None:
            if record.get("previous_calibration_sha256") is not None:
                errors.append(f"calibrations[{index}].previous_calibration_sha256: first calibration must use null")
        elif record.get("previous_calibration_sha256") != previous.get("record_sha256"):
            errors.append(f"calibrations[{index}].previous_calibration_sha256: must match predecessor")
        previous = record
    if errors:
        raise StageWorkRecordError(errors)


def _validate_record_calibration_topology(
    record: Mapping[str, Any],
    previous_record: Mapping[str, Any] | None,
    *,
    stage: str,
    errors: list[str],
) -> None:
    """Ensure a downstream record consumes the calibration for its predecessor."""

    bindings = record.get("calibration_bindings")
    if bindings is None:
        return
    if stage == STAGES[0]:
        errors.append("record.calibration_bindings: Logic cannot consume an upstream calibration")
        return
    if not isinstance(bindings, list) or len(bindings) != 1:
        errors.append("record.calibration_bindings: each downstream stage must consume exactly one calibration")
        return
    binding = bindings[0]
    expected_step = next((item["step"] for item in CALIBRATION_STEPS if item["target_stage"] == stage), None)
    if expected_step is None:
        errors.append("record.calibration_bindings: unsupported downstream stage")
        return
    artifact = binding.get("calibration_artifact") if isinstance(binding, Mapping) else None
    if not isinstance(artifact, Mapping) or not isinstance(artifact.get("path"), str):
        return
    try:
        calibration = json.loads(Path(artifact["path"]).read_text(encoding="utf-8"))
        validate_calibration_record(
            calibration,
            expected_run_id=record.get("run_id"),
            expected_task_request_sha256=record.get("task_request_sha256"),
            expected_target_stage=stage,
            expected_source_record=previous_record,
            verify_files=True,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, StageWorkRecordError) as exc:
        errors.append(f"record.calibration_bindings: calibration is stale or invalid: {exc}")
        return
    if calibration.get("step") != expected_step:
        errors.append("record.calibration_bindings: calibration step does not match this stage")
    findings = {
        item.get("finding_id"): item
        for item in calibration.get("findings", [])
        if isinstance(item, Mapping)
    }
    dispositions = binding.get("finding_dispositions", []) if isinstance(binding, Mapping) else []
    disposition_ids = {item.get("finding_id") for item in dispositions if isinstance(item, Mapping)}
    if disposition_ids != set(findings):
        errors.append("record.calibration_bindings: dispositions must cover every calibration finding exactly once")
    # A Supervisor recommendation may be declined with a reason.  The
    # acceptance contract and the independent Auditor decide whether the
    # underlying requirement was met; an arbitrary Supervisor ``blocking``
    # flag must not turn a quality suggestion into a hidden handoff gate.
    acceptance = record.get("acceptance_contract")
    if acceptance is not None and acceptance != calibration.get("acceptance_contract"):
        errors.append("record.acceptance_contract: must match the consumed calibration acceptance contract")


def validate_record(
    record: Mapping[str, Any], run_id: str | None = None, task_request_sha256: str | None = None,
    previous_record: Mapping[str, Any] | None = None, verify_files: bool = True, *, require_ready: bool = False,
) -> None:
    """Validate one record, optionally checking its immediate predecessor."""
    errors, _ = _record_errors(record, expected_run=run_id, expected_task=task_request_sha256,
                               previous=previous_record, verify_files=verify_files)
    if isinstance(record, Mapping) and record.get("calibration_bindings") is not None:
        _validate_record_calibration_topology(record, previous_record, stage=str(record.get("stage")), errors=errors)
    if require_ready and isinstance(record, Mapping):
        checks = record.get("checks") if isinstance(record.get("checks"), list) else []
        if _record_readiness(record) == "blocked":
            errors.append("record.readiness: blocking identity or quality gate remains unresolved")
        if any(
            isinstance(c, Mapping) and c.get("status") == "fail" and c.get("blocking", True) is True
            for c in checks
        ):
            errors.append("record.checks: blocking failed checks prevent readiness")
        if record.get("open_issues") and _record_readiness(record) == "blocked":
            errors.append("record.open_issues: unresolved blocking issues prevent readiness")
    if errors:
        raise StageWorkRecordError(errors)


def create_record(
    stage: str, draft: dict[str, Any], challenge: dict[str, Any], artifacts: dict[str, Path],
    previous_record: dict[str, Any] | None = None,
    *,
    calibration_bindings: list[dict[str, Any]] | None = None,
    acceptance_contract: Path | None = None,
) -> dict[str, Any]:
    """Construct one record from a draft, actual run binding, and actual files."""
    errors: list[str] = []
    if stage not in STAGES:
        errors.append(_err("stage", "must be one of the five governed stages"))
    try:
        run, task = _binding(challenge)
    except StageWorkRecordError as exc:
        errors.extend(exc.errors)
        run, task = "", ""
    calibrated_hint = acceptance_contract is not None or (
        isinstance(draft, Mapping) and any(key in draft for key in ("acceptance_contract", "calibration_bindings"))
    )
    fields, field_errors = _draft(draft, calibrated=calibrated_hint)
    artifacts_out, artifact_errors = _artifacts(artifacts)
    errors.extend(field_errors + artifact_errors)
    supplied_bindings = calibration_bindings if calibration_bindings is not None else fields.get("calibration_bindings")
    if supplied_bindings is not None:
        if not isinstance(supplied_bindings, list):
            errors.append(_err("calibration_bindings", "must be an array"))
        else:
            for index, binding in enumerate(supplied_bindings):
                _validate_calibration_binding(binding, f"calibration_bindings[{index}]", errors, verify_files=True)
    acceptance_value = acceptance_contract if acceptance_contract is not None else fields.get("acceptance_contract")
    if acceptance_value is not None:
        acceptance_meta = _artifact_meta(acceptance_value) if isinstance(acceptance_value, Path) else acceptance_value
        _artifact_meta_errors(acceptance_meta, "acceptance_contract", errors, verify_files=True)
    if stage == STAGES[0] and previous_record is not None:
        errors.append(_err("previous_record", "logic is the first stage and cannot have a predecessor"))
    if stage in STAGES[1:] and previous_record is None:
        errors.append(_err("previous_record", f"{stage} requires its immediate predecessor"))
    if previous_record is not None and stage in STAGES[1:] and run:
        prior_stage = STAGES[STAGES.index(stage) - 1]
        prior_errors, _ = _record_errors(previous_record, expected_run=run, expected_task=task,
                                         expected_stage=prior_stage, verify_files=True)
        errors.extend(f"previous_record: {e}" for e in prior_errors)
        if not prior_errors:
            if _record_readiness(previous_record) == "blocked":
                errors.append("previous_record: blocking readiness state prevents the next stage")
            if any(
                isinstance(c, Mapping) and c.get("status") == "fail" and c.get("blocking", True) is True
                for c in previous_record.get("checks", [])
            ):
                errors.append("previous_record: blocking failed checks prevent the next stage")
            if previous_record.get("open_issues") and _record_readiness(previous_record) == "blocked":
                errors.append("previous_record: blocking open issues prevent the next stage")
    if errors:
        raise StageWorkRecordError(errors)
    record: dict[str, Any] = {
        "contract": CONTRACT, "stage": stage, "run_id": run, "task_request_sha256": task,
        "recorded_at": _now(), "summary": fields["summary"], "decisions": fields["decisions"],
        "checks": fields["checks"], "open_issues": fields["open_issues"], "artifacts": artifacts_out,
        "previous_record_sha256": previous_record.get("record_sha256") if previous_record else None,
    }
    if "readiness" in fields:
        record["readiness"] = fields["readiness"]
    elif supplied_bindings is not None or acceptance_value is not None:
        # New calibrated records must carry an explicit disposition.  A clean
        # record is ready; a quality-only issue is explicitly quality-limited.
        record["readiness"] = "quality-limited" if fields["open_issues"] or any(
            isinstance(item, Mapping) and item.get("status") == "fail" and item.get("blocking") is False
            for item in fields["checks"]
        ) else "ready"
    if supplied_bindings is not None:
        record["calibration_bindings"] = supplied_bindings
    if acceptance_value is not None:
        record["acceptance_contract"] = acceptance_meta
    record["record_sha256"] = canonical_record_sha256(record)
    validate_record(record, run, task, previous_record)
    return record


def validate_records(records: list[dict[str, Any]], run_id: str, task_request_sha256: str,
                     verify_files: bool = True) -> None:
    """Validate all five records in fixed order and enforce final readiness gates."""
    errors: list[str] = []
    if not isinstance(records, list):
        raise StageWorkRecordError("records: must be an array")
    if len(records) != len(STAGES):
        errors.append(_err("records", f"must contain exactly {len(STAGES)} records in fixed order"))
    if not isinstance(run_id, str) or not run_id.strip():
        errors.append(_err("run_id", "must be a non-empty string"))
    if not _sha(task_request_sha256):
        errors.append(_err("task_request_sha256", "must be a lowercase SHA-256"))
    previous: Mapping[str, Any] | None = None
    previous_time: datetime | None = None
    for i, expected_stage in enumerate(STAGES):
        if i >= len(records):
            errors.append(_err(f"records[{i}]", f"missing {expected_stage} stage"))
            continue
        record = records[i]
        item_errors, item_time = _record_errors(record, expected_run=run_id, expected_task=task_request_sha256,
                                                expected_stage=expected_stage, previous=previous,
                                                verify_files=verify_files)
        if isinstance(record, Mapping):
            _validate_record_calibration_topology(record, previous, stage=expected_stage, errors=item_errors)
        errors.extend(f"records[{i}]: {e}" for e in item_errors)
        if previous_time is not None and item_time is not None and item_time < previous_time:
            errors.append(_err(f"records[{i}].recorded_at", "timestamps must be nondecreasing"))
        previous = record if isinstance(record, Mapping) else None
        previous_time = item_time
    if len(records) > len(STAGES):
        errors.extend(_err(f"records[{i}]", "unexpected extra stage record") for i in range(len(STAGES), len(records)))
    calibrated = any(
        isinstance(record, Mapping) and any(key in record for key in ("acceptance_contract", "calibration_bindings"))
        for record in records
    )
    if calibrated:
        for index in range(1, 4):
            record = records[index] if index < len(records) else None
            if not isinstance(record, Mapping) or not isinstance(record.get("calibration_bindings"), list) or len(record.get("calibration_bindings", [])) != 1:
                errors.append(f"records[{index}].calibration_bindings: calibrated records must explicitly absorb the immediate Supervisor calibration")
    for i, record in enumerate(records):
        if not isinstance(record, Mapping):
            continue
        checks = record.get("checks") if isinstance(record.get("checks"), list) else []
        if _record_readiness(record) == "blocked":
            errors.append(f"records[{i}].readiness: blocking readiness state remains unresolved")
        if any(
            isinstance(c, Mapping) and c.get("status") == "fail" and c.get("blocking", True) is True
            for c in checks
        ):
            errors.append(f"records[{i}].checks: blocking failed checks prevent final readiness")
        if record.get("open_issues") and _record_readiness(record) == "blocked":
            errors.append(f"records[{i}].open_issues: unresolved blocking issues prevent final readiness")
    if errors:
        raise StageWorkRecordError(errors)


__all__ = [
    "ARTIFACT_FIELDS", "CALIBRATION_BINDING_FIELDS", "CALIBRATION_CONTRACT", "CALIBRATION_RECORD_FIELDS",
    "CALIBRATION_STEPS", "CALIBRATION_DISPOSITIONS", "CHECK_FIELDS", "CHECK_STATUSES", "CONTRACT",
    "LEGACY_RECORD_FIELDS", "READINESS_STATES", "RECORD_FIELDS", "SHA256", "STAGES",
    "StageWorkRecordError", "ValidationError", "WorkRecordValidationError", "canonical_json", "canonical_sha256",
    "canonical_record_sha256", "record_sha256", "create_record", "create_calibration_record",
    "create_calibration_binding", "validate_record", "validate_records", "validate_calibration_record",
    "validate_calibration_chain",
]
