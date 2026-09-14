#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Independent final-audit artifact creation and validation.

The final audit is deliberately a separate artifact from the Supervisor
release record.  This module only attests to bytes and declared observations;
it never tries to prove that a role string represents a different model or a
different process.
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONTRACT = "io.clayz.presentation.independent-audit/1.0"
AUDIT_RECORD_FIELDS = frozenset(
    {
        "contract",
        "audit_id",
        "run_id",
        "task_request_sha256",
        "task_request",
        "acceptance_rules",
        "supervisor_rules",
        "source_records",
        "expected_source_kinds",
        "final_pptx",
        "render_evidence",
        "coverage",
        "findings",
        "audit_status",
        "independent_context",
        "audited_at",
        "record_sha256",
    }
)
ARTIFACT_FIELDS = frozenset({"path", "sha256", "bytes"})
SOURCE_RECORD_FIELDS = frozenset({"kind", "path", "sha256", "bytes"})
RENDER_RECORD_FIELDS = frozenset({"kind", "path", "sha256", "bytes"})
COVERAGE_FIELDS = frozenset(
    {"hard_requirement_ids", "soft_requirement_ids", "requirements", "rules", "render_status"}
)
COVERAGE_ITEM_FIELDS = frozenset(
    {"requirement_id", "classification", "status", "evidence_refs", "observation"}
)
FINDING_FIELDS = frozenset(
    {
        "finding_id",
        "requirement_ids",
        "rule_ids",
        "slide_ids",
        "owner_layer",
        "severity",
        "statement",
        "expected",
        "actual",
        "impact",
        "evidence_refs",
        "recommended_change",
    }
)
RULE_COVERAGE_FIELDS = frozenset(
    {"rule_id", "source", "status", "evidence_refs", "observation"}
)
CONTEXT_FIELDS = frozenset({"execution_mode", "context_id", "model_identity_disclosure", "limitations"})
AUDIT_STATUSES = frozenset({"clean", "issues-found", "incomplete-evidence"})
COVERAGE_STATUSES = frozenset({"pass", "fail", "deferred", "not-applicable"})
RENDER_STATUSES = frozenset({"complete", "partial", "deferred", "not-run"})
CLASSIFICATIONS = frozenset({"hard", "soft"})
SEVERITIES = frozenset({"critical", "major", "moderate", "minor"})
EXECUTION_MODES = frozenset({"separate-process", "separate-context", "same-model-new-context", "same-context-limited"})
SHA256 = re.compile(r"^[0-9a-f]{64}$")
DEFAULT_SOURCE_KINDS = ("package", "plan", "qa", "inventory")
REQUIRED_SOURCE_KINDS = frozenset(DEFAULT_SOURCE_KINDS)
EVIDENCE_SHA256 = re.compile(r"(?:^|\s)sha256=([0-9a-f]{64})(?=\s|$)")


class IndependentAuditError(ValueError):
    """Raised when an independent audit artifact is malformed or stale."""

    def __init__(self, errors: str | Sequence[str]) -> None:
        self.errors = [errors] if isinstance(errors, str) else [str(item) for item in errors if str(item)]
        super().__init__("; ".join(self.errors) or "invalid independent audit")


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise IndependentAuditError(f"value is not canonical JSON: {exc}") from exc


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def canonical_record_sha256(record: Mapping[str, Any]) -> str:
    body = dict(record)
    body.pop("record_sha256", None)
    return canonical_sha256(body)


def _sha(value: Any) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _timestamp(value: Any) -> bool:
    if not _nonempty(value):
        return False
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.utcoffset() is not None


def _file_record(path: Path) -> dict[str, Any]:
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise IndependentAuditError(f"artifact is not a readable file: {resolved}")
    try:
        raw = resolved.read_bytes()
    except OSError as exc:
        raise IndependentAuditError(f"artifact cannot be read: {resolved}: {exc}") from exc
    if not raw:
        raise IndependentAuditError(f"artifact must not be empty: {resolved}")
    return {
        "path": str(resolved),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    resolved = Path(path).expanduser().resolve()
    if resolved.exists():
        raise FileExistsError(resolved)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _artifact_errors(value: Any, path: str, errors: list[str], *, verify_files: bool) -> None:
    if not isinstance(value, Mapping) or set(value) != ARTIFACT_FIELDS:
        errors.append(f"{path}: must contain exactly {sorted(ARTIFACT_FIELDS)}")
        return
    artifact_path, digest, size = value.get("path"), value.get("sha256"), value.get("bytes")
    if not isinstance(artifact_path, str) or not artifact_path.strip() or not Path(artifact_path).is_absolute():
        errors.append(f"{path}.path: must be an absolute path")
        return
    if not _sha(digest):
        errors.append(f"{path}.sha256: must be a lowercase SHA-256")
    if isinstance(size, bool) or not isinstance(size, int) or size < 1:
        errors.append(f"{path}.bytes: must be a positive integer")
    if verify_files:
        try:
            raw = Path(artifact_path).resolve().read_bytes()
        except OSError as exc:
            errors.append(f"{path}: file cannot be verified: {exc}")
            return
        if not raw:
            errors.append(f"{path}: file must not be empty")
        if _sha(digest) and hashlib.sha256(raw).hexdigest() != digest:
            errors.append(f"{path}.sha256: does not match current file bytes")
        if isinstance(size, int) and not isinstance(size, bool) and len(raw) != size:
            errors.append(f"{path}.bytes: does not match current file bytes")


def _read_json(path: str, errors: list[str], label: str) -> Any | None:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: cannot read JSON: {exc}")
        return None
    return value


def _acceptance_classifications(value: Any, errors: list[str]) -> tuple[set[str], set[str]]:
    hard: set[str] = set()
    soft: set[str] = set()
    if not isinstance(value, Mapping) or not isinstance(value.get("requirements"), list):
        errors.append("acceptance_rules: requirements must be a non-empty array")
        return hard, soft
    try:
        from acceptance_contract import validate_acceptance_contract
    except ImportError:
        try:
            from packages.validators.acceptance_contract import validate_acceptance_contract
        except ImportError as exc:
            errors.append(f"acceptance_rules: validator dependency is unavailable: {exc}")
            validate_acceptance_contract = None  # type: ignore[assignment]
    if validate_acceptance_contract is not None:
        contract_errors: list[str] = []
        validate_acceptance_contract(value, "acceptance_rules", contract_errors)
        errors.extend(contract_errors)
    seen: set[str] = set()
    for index, item in enumerate(value.get("requirements", [])):
        path = f"acceptance_rules.requirements[{index}]"
        if not isinstance(item, Mapping):
            errors.append(f"{path}: must be an object")
            continue
        requirement_id = item.get("requirement_id")
        if not _nonempty(requirement_id) or requirement_id in seen:
            errors.append(f"{path}.requirement_id: must be non-empty and unique")
            continue
        seen.add(str(requirement_id))
        classification = item.get("classification")
        if classification not in CLASSIFICATIONS:
            errors.append(f"{path}.classification: new audit contracts require hard or soft")
        elif classification == "hard":
            hard.add(str(requirement_id))
        else:
            soft.add(str(requirement_id))
    if not seen:
        errors.append("acceptance_rules.requirements: must contain at least one requirement")
    return hard, soft


def _validate_supervisor_rules(value: Any, errors: list[str]) -> set[str]:
    rule_ids: set[str] = set()
    if not isinstance(value, Mapping):
        errors.append("supervisor_rules: must be a JSON object")
        return rule_ids
    seen: set[str] = set()
    for key in ("fixed_commitments", "explicit_changes"):
        entries = value.get(key)
        if not isinstance(entries, list):
            errors.append(f"supervisor_rules.{key}: must be an array")
            continue
        for index, item in enumerate(entries):
            path = f"supervisor_rules.{key}[{index}]"
            if not isinstance(item, Mapping):
                errors.append(f"{path}: must be an object with rule_id and statement")
                continue
            if set(item) - {"rule_id", "statement", "classification", "change"}:
                errors.append(f"{path}: contains unsupported fields")
            rule_id = item.get("rule_id")
            if not _nonempty(rule_id) or rule_id in seen:
                errors.append(f"{path}.rule_id: must be non-empty and unique")
            else:
                seen.add(str(rule_id))
                rule_ids.add(str(rule_id))
            if not _nonempty(item.get("statement")):
                errors.append(f"{path}.statement: must be non-empty")
            if item.get("classification") not in CLASSIFICATIONS:
                errors.append(f"{path}.classification: must be hard or soft")
    if not rule_ids:
        errors.append("supervisor_rules: fixed_commitments and explicit_changes must provide at least one rule")
    return rule_ids


def _evidence_tokens(value: Mapping[str, Any]) -> dict[str, str]:
    """Return identifiers and the hash each evidence ref must carry."""

    tokens: dict[str, str] = {}
    logical = {"task_request": "task_request", "acceptance_rules": "acceptance_rules", "supervisor_rules": "supervisor_rules", "final_pptx": "final_pptx"}
    for key in ("task_request", "acceptance_rules", "supervisor_rules", "final_pptx"):
        record = value.get(key)
        if isinstance(record, Mapping):
            digest = record.get("sha256")
            if not _sha(digest):
                continue
            tokens[logical[key]] = str(digest)
            path = record.get("path")
            if isinstance(path, str) and path.strip():
                tokens[Path(path).name] = str(digest)
    for key, prefix in (("source_records", "source"), ("render_evidence", "render")):
        rows = value.get(key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            kind = row.get("kind")
            digest = row.get("sha256")
            if not _sha(digest):
                continue
            if isinstance(kind, str) and kind.strip():
                tokens[kind] = str(digest)
                tokens[f"{prefix}:{kind}"] = str(digest)
            path = row.get("path")
            if isinstance(path, str) and path.strip():
                tokens[Path(path).name] = str(digest)
    return tokens


def _validate_evidence_refs(
    refs: Any,
    path: str,
    tokens: Mapping[str, str],
    errors: list[str],
    *,
    allow_deferred: bool = False,
) -> None:
    if not isinstance(refs, list) or not refs or any(not _nonempty(item) for item in refs):
        errors.append(f"{path}: must be a non-empty string array")
        return
    for index, reference in enumerate(refs):
        raw = str(reference).strip()
        token = raw.split("#", 1)[0].split(" ", 1)[0]
        expected_hash = tokens.get(token)
        declared = EVIDENCE_SHA256.search(raw)
        if expected_hash is not None and declared is not None and declared.group(1) == expected_hash:
            continue
        if allow_deferred and any(raw.casefold().startswith(prefix) for prefix in ("deferred:", "not-run:", "unavailable:")):
            continue
        errors.append(f"{path}[{index}]: must reference a bound artifact with its matching sha256 or an explicit deferred observation")


def _inspect_render_file(path: Path) -> tuple[str, bool]:
    """Return (format, native_marker) for a readable image/PDF render file."""

    raw = path.read_bytes()
    suffix = path.suffix.casefold()
    if suffix == ".png" and raw.startswith(b"\x89PNG\r\n\x1a\n"):
        try:
            from PIL import Image

            with Image.open(path) as image:
                image.verify()
                return "png", image.info.get("native_render") is True
        except (ImportError, OSError, ValueError):
            return "unverified", False
    if suffix in {".jpg", ".jpeg"} and raw.startswith(b"\xff\xd8\xff"):
        try:
            from PIL import Image

            with Image.open(path) as image:
                image.verify()
            return "jpeg", False
        except (ImportError, OSError, ValueError):
            return "unverified", False
    if suffix == ".pdf" and raw.startswith(b"%PDF-"):
        return "pdf", True
    if suffix == ".svg" and b"<svg" in raw[:4096].lower():
        return "svg", False
    if suffix == ".webp" and raw.startswith(b"RIFF") and b"WEBP" in raw[8:16]:
        return "webp", False
    return "unsupported", False


def _normalise_path_map(
    records: Mapping[str, Path] | Sequence[tuple[str, Path]] | Sequence[Mapping[str, Any]],
) -> list[tuple[str, Path]]:
    if isinstance(records, Mapping):
        return [(str(kind), Path(path)) for kind, path in sorted(records.items())]
    result: list[tuple[str, Path]] = []
    for item in records:
        if isinstance(item, Mapping):
            result.append((str(item.get("kind", "")), Path(str(item.get("path", "")))))
        else:
            kind, path = item
            result.append((str(kind), Path(path)))
    return result


def create_auditor_artifact(
    *,
    task_request: Path,
    acceptance_rules: Path,
    supervisor_rules: Path,
    source_records: Mapping[str, Path] | Sequence[tuple[str, Path]] | Sequence[Mapping[str, Any]],
    expected_source_kinds: Sequence[str] | None = None,
    final_pptx: Path,
    render_evidence: Mapping[str, Path] | Sequence[tuple[str, Path]] | Sequence[Mapping[str, Any]] = (),
    coverage: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]] = (),
    independent_context: Mapping[str, Any],
    run_id: str,
    task_request_sha256: str,
    output: Path | None = None,
    audit_id: str | None = None,
    audited_at: str | None = None,
) -> dict[str, Any]:
    """Create one immutable, byte-bound Auditor artifact.

    ``source_records`` is intentionally keyed by an explicit kind.  The
    validator later checks that each declared kind has an existing file and
    that the set of kinds is exactly the set declared in the artifact.
    """

    if not _nonempty(run_id):
        raise IndependentAuditError("run_id must be non-empty")
    if not _sha(task_request_sha256):
        raise IndependentAuditError("task_request_sha256 must be a lowercase SHA-256")
    task_record = _file_record(task_request)
    if task_record["sha256"] != task_request_sha256:
        raise IndependentAuditError("task_request_sha256 does not match task_request bytes")
    acceptance_record = _file_record(acceptance_rules)
    supervisor_record = _file_record(supervisor_rules)
    pptx_record = _file_record(final_pptx)
    source_rows = []
    for kind, path in _normalise_path_map(source_records):
        if not _nonempty(kind):
            raise IndependentAuditError("source record kinds must be non-empty")
        source_rows.append({"kind": kind, **_file_record(path)})
    if len({row["kind"] for row in source_rows}) != len(source_rows):
        raise IndependentAuditError("source record kinds must be unique")
    expected_kinds = list(DEFAULT_SOURCE_KINDS if expected_source_kinds is None and source_rows else expected_source_kinds or [])
    if (source_rows and not expected_kinds) or len(expected_kinds) != len(set(expected_kinds)) or any(not _nonempty(item) for item in expected_kinds):
        raise IndependentAuditError("expected_source_kinds must be a unique non-empty string array")
    if {row["kind"] for row in source_rows} != set(expected_kinds):
        raise IndependentAuditError("source_records do not contain exactly the expected source kinds")
    render_rows = []
    for kind, path in _normalise_path_map(render_evidence):
        if not _nonempty(kind):
            raise IndependentAuditError("render evidence kinds must be non-empty")
        render_rows.append({"kind": kind, **_file_record(path)})
    if len({row["kind"] for row in render_rows}) != len(render_rows):
        raise IndependentAuditError("render evidence kinds must be unique")
    value: dict[str, Any] = {
        "contract": CONTRACT,
        "audit_id": audit_id or f"AUDIT-{hashlib.sha256((run_id + task_request_sha256).encode()).hexdigest()[:16]}",
        "run_id": run_id,
        "task_request_sha256": task_request_sha256,
        "task_request": task_record,
        "acceptance_rules": acceptance_record,
        "supervisor_rules": supervisor_record,
        "source_records": source_rows,
        "expected_source_kinds": list(expected_kinds),
        "final_pptx": pptx_record,
        "render_evidence": render_rows,
        "coverage": dict(coverage),
        "findings": [dict(item) for item in findings],
        "audit_status": "clean",
        "independent_context": dict(independent_context),
        "audited_at": audited_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    statuses = [
        item.get("status")
        for item in value["coverage"].get("requirements", [])
        if isinstance(item, Mapping)
    ]
    rule_statuses = [
        item.get("status")
        for item in value["coverage"].get("rules", [])
        if isinstance(item, Mapping)
    ]
    if any(status == "deferred" for status in statuses + rule_statuses) or not render_rows or value["coverage"].get("render_status") in {"partial", "deferred", "not-run"}:
        value["audit_status"] = "incomplete-evidence"
    if value["findings"] or any(status == "fail" for status in statuses + rule_statuses):
        value["audit_status"] = "issues-found" if value["audit_status"] != "incomplete-evidence" else "incomplete-evidence"
    value["record_sha256"] = canonical_record_sha256(value)
    if output is not None:
        _write_new(output, value)
    return value


def _validate_findings(value: Any, requirement_ids: set[str], errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("findings: must be an array")
        return
    seen: set[str] = set()
    for index, finding in enumerate(value):
        path = f"findings[{index}]"
        if not isinstance(finding, Mapping) or set(finding) != FINDING_FIELDS:
            errors.append(f"{path}: fields must be exactly {sorted(FINDING_FIELDS)}")
            continue
        finding_id = finding.get("finding_id")
        if not _nonempty(finding_id) or finding_id in seen:
            errors.append(f"{path}.finding_id: must be non-empty and unique")
        else:
            seen.add(str(finding_id))
        ids = finding.get("requirement_ids")
        if not isinstance(ids, list) or any(not _nonempty(item) for item in ids) or len(ids) != len(set(ids)):
            errors.append(f"{path}.requirement_ids: must be a unique string array")
        elif not set(ids) <= requirement_ids:
            errors.append(f"{path}.requirement_ids: references an unknown acceptance requirement")
        rule_ids = finding.get("rule_ids")
        if not isinstance(rule_ids, list) or any(not _nonempty(item) for item in rule_ids) or len(rule_ids) != len(set(rule_ids)):
            errors.append(f"{path}.rule_ids: must be a unique string array")
        if finding.get("owner_layer") not in {"root", "logic", "copy", "art-direction", "output", "supervisor", "system"}:
            errors.append(f"{path}.owner_layer: invalid value")
        if finding.get("severity") not in SEVERITIES:
            errors.append(f"{path}.severity: invalid value")
        for key in ("statement", "expected", "actual", "impact", "recommended_change"):
            if not _nonempty(finding.get(key)):
                errors.append(f"{path}.{key}: must be non-empty")
        refs = finding.get("evidence_refs")
        if not isinstance(refs, list) or not refs or any(not _nonempty(item) for item in refs):
            errors.append(f"{path}.evidence_refs: must be a non-empty string array")


def validate_auditor_artifact(
    value: Any,
    *,
    verify_files: bool = True,
    expected_run_id: str | None = None,
    expected_task_request_sha256: str | None = None,
    expected_pptx_sha256: str | None = None,
) -> None:
    """Validate structure, acceptance coverage, and all bound current bytes."""

    errors: list[str] = []
    if not isinstance(value, Mapping):
        raise IndependentAuditError("audit: must be an object")
    if set(value) != AUDIT_RECORD_FIELDS:
        errors.append(f"audit: fields must be exactly {sorted(AUDIT_RECORD_FIELDS)}")
    if value.get("contract") != CONTRACT:
        errors.append(f"audit.contract: expected {CONTRACT}")
    if not _nonempty(value.get("audit_id")):
        errors.append("audit.audit_id: must be non-empty")
    run_id = value.get("run_id")
    if not _nonempty(run_id):
        errors.append("audit.run_id: must be non-empty")
    elif expected_run_id is not None and run_id != expected_run_id:
        errors.append("audit.run_id: does not match expected run")
    task_sha = value.get("task_request_sha256")
    if not _sha(task_sha):
        errors.append("audit.task_request_sha256: must be a lowercase SHA-256")
    elif expected_task_request_sha256 is not None and task_sha != expected_task_request_sha256:
        errors.append("audit.task_request_sha256: does not match expected task")
    for key in ("task_request", "acceptance_rules", "supervisor_rules", "final_pptx"):
        _artifact_errors(value.get(key), f"audit.{key}", errors, verify_files=verify_files)

    task_record = value.get("task_request")
    if isinstance(task_record, Mapping) and _sha(task_record.get("sha256")) and task_record.get("sha256") != task_sha:
        errors.append("audit.task_request.sha256: must match task_request_sha256")
    acceptance_record = value.get("acceptance_rules")
    acceptance_value: Any | None = None
    if isinstance(acceptance_record, Mapping) and isinstance(acceptance_record.get("path"), str):
        acceptance_value = _read_json(acceptance_record["path"], errors, "audit.acceptance_rules")
    hard_ids, soft_ids = _acceptance_classifications(acceptance_value, errors)

    supervisor_record = value.get("supervisor_rules")
    supervisor_value: Any | None = None
    if isinstance(supervisor_record, Mapping) and isinstance(supervisor_record.get("path"), str):
        supervisor_value = _read_json(supervisor_record["path"], errors, "audit.supervisor_rules")
    supervisor_rule_ids = _validate_supervisor_rules(supervisor_value, errors)

    expected_kinds = value.get("expected_source_kinds")
    if not isinstance(expected_kinds, list) or any(not _nonempty(item) for item in expected_kinds) or len(expected_kinds) != len(set(expected_kinds)):
        errors.append("audit.expected_source_kinds: must be a unique string array")
        expected_kinds = []
    source_rows = value.get("source_records")
    observed_kinds: set[str] = set()
    if not isinstance(source_rows, list):
        errors.append("audit.source_records: must be an array")
        source_rows = []
    for index, row in enumerate(source_rows):
        path = f"audit.source_records[{index}]"
        if not isinstance(row, Mapping) or set(row) != SOURCE_RECORD_FIELDS:
            errors.append(f"{path}: fields must be exactly {sorted(SOURCE_RECORD_FIELDS)}")
            continue
        kind = row.get("kind")
        if not _nonempty(kind) or kind in observed_kinds:
            errors.append(f"{path}.kind: must be non-empty and unique")
        else:
            observed_kinds.add(str(kind))
        _artifact_errors({key: row.get(key) for key in ARTIFACT_FIELDS}, path, errors, verify_files=verify_files)
    if observed_kinds != set(expected_kinds):
        errors.append("audit.source_records: actual source kinds must exactly match expected_source_kinds")
    if observed_kinds and not REQUIRED_SOURCE_KINDS <= observed_kinds:
        errors.append("audit.source_records: package, plan, qa, and inventory are mandatory bound source kinds")
    for index, row in enumerate(source_rows):
        if not isinstance(row, Mapping) or not isinstance(row.get("path"), str):
            continue
        try:
            parsed_source = json.loads(Path(row["path"]).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"audit.source_records[{index}]: source artifact must be readable JSON: {exc}")
            continue
        if not isinstance(parsed_source, (Mapping, list)) or not parsed_source:
            errors.append(f"audit.source_records[{index}]: source artifact JSON must contain governed content")

    _artifact_errors(value.get("final_pptx"), "audit.final_pptx", errors, verify_files=verify_files)
    final_pptx = value.get("final_pptx")
    if isinstance(final_pptx, Mapping) and expected_pptx_sha256 is not None and final_pptx.get("sha256") != expected_pptx_sha256:
        errors.append("audit.final_pptx.sha256: does not match final PPTX")
    if isinstance(final_pptx, Mapping) and isinstance(final_pptx.get("path"), str) and verify_files:
        try:
            with zipfile.ZipFile(Path(final_pptx["path"])) as archive:
                names = set(archive.namelist())
                if "[Content_Types].xml" not in names or "ppt/presentation.xml" not in names:
                    errors.append("audit.final_pptx: must be a readable OOXML presentation package")
        except (OSError, zipfile.BadZipFile) as exc:
            errors.append(f"audit.final_pptx: must be a readable OOXML presentation package: {exc}")

    render_rows = value.get("render_evidence")
    if not isinstance(render_rows, list):
        errors.append("audit.render_evidence: must be an array")
        render_rows = []
    render_kinds: set[str] = set()
    unsupported_render_indices: list[int] = []
    native_render_available = False
    for index, row in enumerate(render_rows):
        path = f"audit.render_evidence[{index}]"
        if not isinstance(row, Mapping) or set(row) != RENDER_RECORD_FIELDS:
            errors.append(f"{path}: fields must be exactly {sorted(RENDER_RECORD_FIELDS)}")
            continue
        kind = row.get("kind")
        if not _nonempty(kind) or kind in render_kinds:
            errors.append(f"{path}.kind: must be non-empty and unique")
        else:
            render_kinds.add(str(kind))
        _artifact_errors({key: row.get(key) for key in ARTIFACT_FIELDS}, path, errors, verify_files=verify_files)
        if verify_files and isinstance(row.get("path"), str):
            try:
                render_format, native_marker = _inspect_render_file(Path(row["path"]))
            except OSError:
                render_format, native_marker = "unsupported", False
            if render_format in {"unsupported", "unverified"}:
                unsupported_render_indices.append(index)
            if isinstance(kind, str) and "native" in kind.casefold():
                if render_format in {"unsupported", "unverified"}:
                    unsupported_render_indices.append(index)
                elif not native_marker:
                    errors.append(f"{path}: synthetic or unverified pixels cannot claim native render acceptance")
                else:
                    native_render_available = True

    evidence_tokens = _evidence_tokens(value)
    coverage = value.get("coverage")
    if not isinstance(coverage, Mapping) or set(coverage) != COVERAGE_FIELDS:
        errors.append(f"audit.coverage: fields must be exactly {sorted(COVERAGE_FIELDS)}")
        coverage = {}
    render_status = coverage.get("render_status")
    if render_status not in RENDER_STATUSES:
        errors.append("audit.coverage.render_status: invalid value")
    elif not render_rows and render_status not in {"deferred", "not-run"}:
        errors.append("audit.coverage.render_status: no render evidence requires deferred or not-run")
    elif render_rows and render_status in {"deferred", "not-run"}:
        errors.append("audit.coverage.render_status: render evidence cannot be deferred or not-run")
    if coverage.get("hard_requirement_ids") != sorted(hard_ids):
        errors.append("audit.coverage.hard_requirement_ids: must exactly match acceptance hard requirements")
    if coverage.get("soft_requirement_ids") != sorted(soft_ids):
        errors.append("audit.coverage.soft_requirement_ids: must exactly match acceptance soft requirements")
    coverage_rows = coverage.get("requirements")
    if not isinstance(coverage_rows, list):
        errors.append("audit.coverage.requirements: must be an array")
        coverage_rows = []
    observed_requirements: set[str] = set()
    acceptance_requirements: dict[str, Mapping[str, Any]] = {
        str(item.get("requirement_id")): item
        for item in (acceptance_value.get("requirements", []) if isinstance(acceptance_value, Mapping) else [])
        if isinstance(item, Mapping) and _nonempty(item.get("requirement_id"))
    }
    deferred = False
    failed = False
    for index, row in enumerate(coverage_rows):
        path = f"audit.coverage.requirements[{index}]"
        if not isinstance(row, Mapping) or set(row) != COVERAGE_ITEM_FIELDS:
            errors.append(f"{path}: fields must be exactly {sorted(COVERAGE_ITEM_FIELDS)}")
            continue
        requirement_id = row.get("requirement_id")
        if not _nonempty(requirement_id) or requirement_id in observed_requirements:
            errors.append(f"{path}.requirement_id: must be non-empty and unique")
        else:
            observed_requirements.add(str(requirement_id))
        expected_class = "hard" if requirement_id in hard_ids else "soft" if requirement_id in soft_ids else None
        if expected_class is None:
            errors.append(f"{path}.requirement_id: unknown acceptance requirement")
        elif row.get("classification") != expected_class:
            errors.append(f"{path}.classification: must match acceptance requirement blocking value")
        status = row.get("status")
        if status not in COVERAGE_STATUSES:
            errors.append(f"{path}.status: invalid value")
        elif status == "deferred":
            deferred = True
        elif status == "fail":
            failed = True
        _validate_evidence_refs(
            row.get("evidence_refs"), f"{path}.evidence_refs", evidence_tokens, errors,
            allow_deferred=row.get("status") in {"deferred", "not-applicable"},
        )
        if not _nonempty(row.get("observation")):
            errors.append(f"{path}.observation: must be non-empty")
    if observed_requirements != hard_ids | soft_ids:
        errors.append("audit.coverage.requirements: must cover every hard and soft acceptance requirement exactly once")
    for requirement_id, requirement in acceptance_requirements.items():
        statement = " ".join(str(requirement.get(key, "")) for key in ("statement", "verification_method")).casefold()
        if "native" in statement or "pixel acceptance" in statement:
            covered = next((row for row in coverage_rows if isinstance(row, Mapping) and row.get("requirement_id") == requirement_id), None)
            if isinstance(covered, Mapping) and covered.get("status") == "pass" and not native_render_available:
                errors.append(f"audit.coverage.requirements[{requirement_id}]: a synthetic or absent render cannot pass an explicit native-render requirement")

    rule_rows = coverage.get("rules")
    if not isinstance(rule_rows, list):
        errors.append("audit.coverage.rules: must be an array")
        rule_rows = []
    observed_rules: set[str] = set()
    for index, row in enumerate(rule_rows):
        path = f"audit.coverage.rules[{index}]"
        if not isinstance(row, Mapping) or set(row) != RULE_COVERAGE_FIELDS:
            errors.append(f"{path}: fields must be exactly {sorted(RULE_COVERAGE_FIELDS)}")
            continue
        rule_id = row.get("rule_id")
        if not _nonempty(rule_id) or rule_id in observed_rules:
            errors.append(f"{path}.rule_id: must be non-empty and unique")
        else:
            observed_rules.add(str(rule_id))
        if rule_id not in supervisor_rule_ids:
            errors.append(f"{path}.rule_id: unknown Supervisor rule")
        if row.get("source") not in {"fixed_commitment", "explicit_change"}:
            errors.append(f"{path}.source: invalid value")
        if row.get("status") not in COVERAGE_STATUSES:
            errors.append(f"{path}.status: invalid value")
        _validate_evidence_refs(
            row.get("evidence_refs"), f"{path}.evidence_refs", evidence_tokens, errors,
            allow_deferred=row.get("status") in {"deferred", "not-applicable"},
        )
        if not _nonempty(row.get("observation")):
            errors.append(f"{path}.observation: must be non-empty")
        if row.get("status") == "deferred":
            deferred = True
        elif row.get("status") == "fail":
            failed = True
    if observed_rules != supervisor_rule_ids:
        errors.append("audit.coverage.rules: must cover every fixed commitment and explicit Supervisor change exactly once")

    _validate_findings(value.get("findings"), hard_ids | soft_ids, errors)
    finding_requirement_ids: set[str] = set()
    finding_rule_ids: set[str] = set()
    if isinstance(value.get("findings"), list):
        for index, finding in enumerate(value["findings"]):
            if not isinstance(finding, Mapping):
                continue
            if isinstance(finding.get("requirement_ids"), list):
                finding_requirement_ids.update(str(item) for item in finding["requirement_ids"])
            rule_ids = finding.get("rule_ids")
            if isinstance(rule_ids, list):
                finding_rule_ids.update(str(item) for item in rule_ids)
                if not set(rule_ids) <= supervisor_rule_ids:
                    errors.append(f"findings[{index}].rule_ids: references an unknown Supervisor rule")
            _validate_evidence_refs(
                finding.get("evidence_refs"), f"findings[{index}].evidence_refs", evidence_tokens, errors,
            )
    failed_requirement_ids = {
        str(row.get("requirement_id"))
        for row in coverage_rows
        if isinstance(row, Mapping) and row.get("status") == "fail"
    }
    failed_rule_ids = {
        str(row.get("rule_id"))
        for row in rule_rows
        if isinstance(row, Mapping) and row.get("status") == "fail"
    }
    if not failed_requirement_ids <= finding_requirement_ids:
        errors.append("audit.findings: every failed requirement must be linked from a finding")
    if not failed_rule_ids <= finding_rule_ids:
        errors.append("audit.findings: every failed Supervisor rule must be linked from a finding")
    context = value.get("independent_context")
    if not isinstance(context, Mapping) or set(context) != CONTEXT_FIELDS:
        errors.append(f"audit.independent_context: fields must be exactly {sorted(CONTEXT_FIELDS)}")
    elif context.get("execution_mode") not in EXECUTION_MODES:
        errors.append("audit.independent_context.execution_mode: invalid value")
    if isinstance(context, Mapping):
        if not _nonempty(context.get("context_id")):
            errors.append("audit.independent_context.context_id: must be non-empty")
        disclosure = context.get("model_identity_disclosure")
        if disclosure not in {"not-attested", "same-model-possible", "provided-by-host"}:
            errors.append("audit.independent_context.model_identity_disclosure: must disclose that model identity is not proven")
        limitations = context.get("limitations")
        if not isinstance(limitations, list) or any(not _nonempty(item) for item in limitations):
            errors.append("audit.independent_context.limitations: must be a string array")
        if context.get("execution_mode") in {"separate-process", "same-context-limited"} and (
            not isinstance(context.get("limitations"), list) or not context.get("limitations")
        ):
            errors.append("audit.independent_context.limitations: execution mode requires explicit limitations")
    if not _timestamp(value.get("audited_at")):
        errors.append("audit.audited_at: must be a timezone-aware ISO timestamp")
    status = value.get("audit_status")
    if status not in AUDIT_STATUSES:
        errors.append("audit.audit_status: invalid value")
    elif status == "clean" and (deferred or failed or value.get("findings") or render_status in {"partial", "deferred", "not-run"}):
        errors.append("audit.audit_status: clean cannot conceal failed findings or incomplete evidence")
    elif status == "issues-found" and not value.get("findings") and not failed:
        errors.append("audit.audit_status: issues-found requires findings or failed coverage")
    elif status == "incomplete-evidence" and not (deferred or render_status in {"partial", "deferred", "not-run"}):
        errors.append("audit.audit_status: incomplete-evidence requires partial or deferred coverage")
    if unsupported_render_indices and not (
        status == "incomplete-evidence" and render_status in {"partial", "deferred", "not-run"}
    ):
        errors.append("audit.render_evidence: every render artifact must be a readable image or PDF, or be explicitly deferred")
    digest = value.get("record_sha256")
    if not _sha(digest):
        errors.append("audit.record_sha256: must be a lowercase SHA-256")
    elif canonical_record_sha256(value) != digest:
        errors.append("audit.record_sha256: does not match canonical content")
    if errors:
        raise IndependentAuditError(errors)


__all__ = [
    "ARTIFACT_FIELDS",
    "AUDIT_RECORD_FIELDS",
    "CONTRACT",
    "IndependentAuditError",
    "canonical_json",
    "canonical_record_sha256",
    "canonical_sha256",
    "create_auditor_artifact",
    "validate_auditor_artifact",
]
