#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Shared fail-closed validation for first-class Index execution evidence."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime.utils import sha256_json  # noqa: E402
from packages.index_runtime.validation import validate_request  # noqa: E402
from packages.personal_extension import required_provider_bindings, validate_personal_extension_runtime  # noqa: E402


CONTRACT = "io.clayz.presentation.index-execution-evidence/1.0"
RECEIPT_CONTRACT = "io.clayz.presentation.retrieval-receipt/1.0"
STAGE_ORDER = ("logic", "copy", "art-direction", "output", "supervisor")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
OWNER_REQUIRED_PROVIDER_IDS = {"builtin-catalog", "task-private-learning"}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require_keys(obj: Any, keys: set[str], path: str, errors: list[str]) -> None:
    if not isinstance(obj, Mapping):
        errors.append(f"{path}: must be an object")
        return
    missing = sorted(keys - set(obj))
    if missing:
        errors.append(f"{path}: missing keys {missing}")


def _source_requirements(
    value: Any,
    path: str,
    errors: list[str],
) -> tuple[dict[str, set[str]], set[str]]:
    """Derive stage requirements from task evidence, never repository-private data."""

    result = {stage: set() for stage in STAGE_ORDER}
    source_ids: set[str] = set()
    if not isinstance(value, list):
        errors.append(f"{path}: must be an array")
        return result, source_ids
    for index, source in enumerate(value):
        spath = f"{path}[{index}]"
        _require_keys(source, {"source_id", "stages"}, spath, errors)
        if not isinstance(source, Mapping):
            continue
        source_id = source.get("source_id")
        if not nonempty(source_id) or source_id in source_ids:
            errors.append(f"{spath}.source_id: must be non-empty and unique")
        else:
            source_ids.add(str(source_id))
        stages = source.get("stages")
        if (
            not isinstance(stages, list)
            or not stages
            or len(stages) != len(set(stages))
            or any(stage not in STAGE_ORDER for stage in stages)
        ):
            errors.append(f"{spath}.stages: must be a non-empty unique stage array")
            continue
        if nonempty(source_id):
            for stage in stages:
                result[stage].add(str(source_id))
    return result, source_ids


def _snapshot_list(provider_lock: Mapping[str, Any], path: str, errors: list[str]) -> list[dict[str, Any]]:
    snapshots = provider_lock.get("snapshots")
    if not isinstance(snapshots, list) or not snapshots:
        errors.append(f"{path}.snapshots: must be a non-empty array")
        return []
    normalized: list[dict[str, Any]] = []
    provider_ids: set[str] = set()
    for index, snapshot in enumerate(snapshots):
        spath = f"{path}.snapshots[{index}]"
        _require_keys(snapshot, {"provider_id", "digest", "record_count"}, spath, errors)
        if not isinstance(snapshot, Mapping):
            continue
        provider_id = snapshot.get("provider_id")
        if not nonempty(provider_id) or provider_id in provider_ids:
            errors.append(f"{spath}.provider_id: must be non-empty and unique")
        else:
            provider_ids.add(provider_id)
        if not isinstance(snapshot.get("digest"), str) or not SHA256.fullmatch(snapshot["digest"]):
            errors.append(f"{spath}.digest: must be lowercase SHA-256")
        if not isinstance(snapshot.get("record_count"), int) or snapshot.get("record_count", -1) < 0:
            errors.append(f"{spath}.record_count: must be a non-negative integer")
        normalized.append(dict(snapshot))
    expected_order = sorted(normalized, key=lambda item: str(item.get("provider_id")))
    if normalized != expected_order:
        errors.append(f"{path}.snapshots: must be sorted by provider_id")
    return normalized


def _bound_personal_runtime(path: str, errors: list[str]) -> Mapping[str, Any] | None:
    runtime_path = ROOT / "runtime" / "personal-extension.json"
    if not runtime_path.is_file():
        return None
    runtime_lock_path = ROOT / "runtime" / "runtime-lock.json"
    config_path = ROOT / "config" / "personal-extension-resolved.json"
    try:
        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        runtime_lock = json.loads(runtime_lock_path.read_text(encoding="utf-8"))
        resolved_config = json.loads(config_path.read_text(encoding="utf-8"))
        return validate_personal_extension_runtime(
            runtime,
            resolved_config=resolved_config,
            runtime_pack_lock=runtime_lock,
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        errors.append(f"{path}.runtime_lock_digest: Personal Extension Runtime binding failed: {exc}")
        return None


def _validate_receipt(
    receipt: Any,
    stage: str,
    mode: str,
    snapshots: list[dict[str, Any]],
    path: str,
    errors: list[str],
) -> tuple[set[str], set[str], set[str]]:
    _require_keys(
        receipt,
        {"contract", "receipt_id", "created_at", "request", "index_snapshot", "candidates", "selection", "fallback", "hallucination_guard"},
        path,
        errors,
    )
    if not isinstance(receipt, Mapping):
        return set(), set(), set()
    if receipt.get("contract") != RECEIPT_CONTRACT:
        errors.append(f"{path}.contract: unsupported retrieval receipt")
    if not nonempty(receipt.get("receipt_id")) or not nonempty(receipt.get("created_at")):
        errors.append(f"{path}: receipt_id and created_at must be non-empty")
    request = receipt.get("request")
    try:
        normalized_request = validate_request(request)
    except Exception as exc:  # IndexRuntimeError is intentionally rendered as contract evidence.
        errors.append(f"{path}.request: {exc}")
        normalized_request = {}
    if normalized_request.get("stage") != stage:
        errors.append(f"{path}.request.stage: must be {stage}")
    if normalized_request and normalized_request.get("require_human_admission") is not True:
        errors.append(f"{path}.request.require_human_admission: must be true")
    expected_rights_context = "private-runtime" if mode == "owner-personal" else "public-open-source"
    if normalized_request and normalized_request.get("rights_context") != expected_rights_context:
        errors.append(f"{path}.request.rights_context: {mode} execution must be {expected_rights_context}")
    if receipt.get("index_snapshot") != snapshots:
        errors.append(f"{path}.index_snapshot: must exactly match the task Provider lock")

    candidates = receipt.get("candidates")
    candidate_by_id: dict[str, Mapping[str, Any]] = {}
    if not isinstance(candidates, list):
        errors.append(f"{path}.candidates: must be an array")
    else:
        for index, candidate in enumerate(candidates):
            cpath = f"{path}.candidates[{index}]"
            _require_keys(candidate, {"record_id", "provider_id", "source_id"}, cpath, errors)
            if not isinstance(candidate, Mapping):
                continue
            record_id = candidate.get("record_id")
            if not nonempty(record_id) or record_id in candidate_by_id:
                errors.append(f"{cpath}.record_id: must be non-empty and unique")
            else:
                candidate_by_id[record_id] = candidate
            if not nonempty(candidate.get("provider_id")) or not nonempty(candidate.get("source_id")):
                errors.append(f"{cpath}: provider_id and source_id must be non-empty")
            elif candidate.get("provider_id") not in {item.get("provider_id") for item in snapshots}:
                errors.append(f"{cpath}.provider_id: must belong to the locked Provider snapshots")

    selection = receipt.get("selection")
    _require_keys(selection, {"selected", "rejected"}, f"{path}.selection", errors)
    selected_ids: set[str] = set()
    selected_sources: set[str] = set()
    selected_providers: set[str] = set()
    if isinstance(selection, Mapping):
        selected = selection.get("selected")
        if not isinstance(selected, list) or not selected:
            errors.append(f"{path}.selection.selected: must contain at least one selected Index record")
        else:
            for index, item in enumerate(selected):
                ipath = f"{path}.selection.selected[{index}]"
                _require_keys(item, {"record_id", "reason"}, ipath, errors)
                if not isinstance(item, Mapping):
                    continue
                record_id = item.get("record_id")
                if record_id not in candidate_by_id or record_id in selected_ids:
                    errors.append(f"{ipath}.record_id: must name one unique retrieved candidate")
                    continue
                if not nonempty(item.get("reason")):
                    errors.append(f"{ipath}.reason: must be non-empty")
                selected_ids.add(record_id)
                selected_sources.add(str(candidate_by_id[record_id].get("source_id")))
                selected_providers.add(str(candidate_by_id[record_id].get("provider_id")))
        rejected = selection.get("rejected")
        if not isinstance(rejected, list):
            errors.append(f"{path}.selection.rejected: must be an array")

    fallback = receipt.get("fallback")
    _require_keys(fallback, {"used", "reason"}, f"{path}.fallback", errors)
    if isinstance(fallback, Mapping) and fallback.get("used") is not False:
        errors.append(f"{path}.fallback.used: approved owner-personal stages cannot use an Index fallback")
    guard = receipt.get("hallucination_guard")
    _require_keys(guard, {"only_registered_records", "invented_record_count", "candidate_count"}, f"{path}.hallucination_guard", errors)
    if isinstance(guard, Mapping):
        if guard.get("only_registered_records") is not True or guard.get("invented_record_count") != 0:
            errors.append(f"{path}.hallucination_guard: only registered records with zero inventions may pass")
        if guard.get("candidate_count") != len(candidate_by_id):
            errors.append(f"{path}.hallucination_guard.candidate_count: must match candidates")
    return selected_ids, selected_sources, selected_providers


def validate_index_evidence(
    evidence: Any,
    required_stages: Sequence[str],
    path: str,
    errors: list[str],
) -> None:
    """Validate the Provider lock, owner materialization, and retrieval receipts."""

    _require_keys(
        evidence,
        {"contract", "mode", "runtime_lock_digest", "provider_lock", "owner_materialization", "stage_receipts"},
        path,
        errors,
    )
    if not isinstance(evidence, Mapping):
        return
    if evidence.get("contract") != CONTRACT:
        errors.append(f"{path}.contract: expected {CONTRACT}")
    mode = evidence.get("mode")
    if mode not in {"owner-personal", "public-core"}:
        errors.append(f"{path}.mode: invalid value")
    if not isinstance(evidence.get("runtime_lock_digest"), str) or not SHA256.fullmatch(evidence["runtime_lock_digest"]):
        errors.append(f"{path}.runtime_lock_digest: must be lowercase SHA-256")
    bound_runtime = _bound_personal_runtime(path, errors) if mode == "owner-personal" else None
    required_provider_ids = set(OWNER_REQUIRED_PROVIDER_IDS)
    required_provider_stages: dict[str, set[str]] = {}
    if isinstance(bound_runtime, Mapping):
        if evidence.get("runtime_lock_digest") != bound_runtime.get("lock", {}).get("digest"):
            errors.append(f"{path}.runtime_lock_digest: must match runtime/personal-extension.json")
        for binding in required_provider_bindings(bound_runtime):
            provider_id = str(binding.get("provider_id"))
            required_provider_ids.add(provider_id)
            required_provider_stages[provider_id] = set(binding.get("stages", []))

    provider_lock = evidence.get("provider_lock")
    _require_keys(provider_lock, {"lock_id", "snapshots", "lock_sha256"}, f"{path}.provider_lock", errors)
    snapshots: list[dict[str, Any]] = []
    if isinstance(provider_lock, Mapping):
        if not nonempty(provider_lock.get("lock_id")):
            errors.append(f"{path}.provider_lock.lock_id: must be non-empty")
        snapshots = _snapshot_list(provider_lock, f"{path}.provider_lock", errors)
        if provider_lock.get("lock_sha256") != sha256_json(snapshots):
            errors.append(f"{path}.provider_lock.lock_sha256: must bind the canonical snapshot list")
    snapshot_by_id = {item.get("provider_id"): item for item in snapshots}
    if "builtin-catalog" not in snapshot_by_id:
        errors.append(f"{path}.provider_lock.snapshots: builtin-catalog is required")
    if mode == "owner-personal" and not required_provider_ids.issubset(snapshot_by_id):
        errors.append(f"{path}.provider_lock.snapshots: owner-personal mode requires {sorted(required_provider_ids)}")
    if mode == "owner-personal":
        for provider_id in sorted(required_provider_ids - {"task-private-learning"}):
            snapshot = snapshot_by_id.get(provider_id)
            if isinstance(snapshot, Mapping) and snapshot.get("record_count", 0) < 1:
                errors.append(
                    f"{path}.provider_lock.snapshots: required Provider {provider_id} must bind a non-empty snapshot"
                )

    materialization = evidence.get("owner_materialization")
    _require_keys(
        materialization,
        {"status", "source_manifest_sha256", "materialization_report_sha256", "provider_id", "record_count", "required_sources", "materialized_source_ids", "missing_source_ids"},
        f"{path}.owner_materialization",
        errors,
    )
    materialized_ids: set[str] = set()
    requirements = {stage: set() for stage in STAGE_ORDER}
    required_ids: set[str] = set()
    if isinstance(materialization, Mapping):
        version_learning_required = isinstance(bound_runtime, Mapping) and isinstance(bound_runtime.get("version_learning"), Mapping)
        if version_learning_required:
            if materialization.get("learning_mode") not in {"first-run", "reused-version-index"}:
                errors.append(f"{path}.owner_materialization.learning_mode: version-bound private learning evidence is required")
            for key in ("learning_key", "version_learning_audit_sha256"):
                value = materialization.get(key)
                if not isinstance(value, str) or not SHA256.fullmatch(value):
                    errors.append(f"{path}.owner_materialization.{key}: must bind the version learning audit")
        if mode == "owner-personal" and materialization.get("status") != "materialized":
            errors.append(f"{path}.owner_materialization.status: owner-personal execution must materialize task-supplied owner learning")
        if mode == "public-core" and materialization.get("status") != "not-applicable":
            errors.append(f"{path}.owner_materialization.status: public-core mode must be not-applicable")
        for key in ("source_manifest_sha256", "materialization_report_sha256"):
            value = materialization.get(key)
            if mode == "owner-personal" and (not isinstance(value, str) or not SHA256.fullmatch(value)):
                errors.append(f"{path}.owner_materialization.{key}: must be lowercase SHA-256")
            if mode == "public-core" and value is not None:
                errors.append(f"{path}.owner_materialization.{key}: public-core mode must use null")
        if materialization.get("provider_id") != "task-private-learning":
            errors.append(f"{path}.owner_materialization.provider_id: must be task-private-learning")
        record_count = materialization.get("record_count")
        if not isinstance(record_count, int) or (mode == "owner-personal" and record_count < 1):
            errors.append(f"{path}.owner_materialization.record_count: materialized owner mode requires a positive count")
        if mode == "public-core" and record_count != 0:
            errors.append(f"{path}.owner_materialization.record_count: public-core mode must be zero")
        requirements, required_ids = _source_requirements(
            materialization.get("required_sources"),
            f"{path}.owner_materialization.required_sources",
            errors,
        )
        for key in ("materialized_source_ids", "missing_source_ids"):
            value = materialization.get(key)
            if not isinstance(value, list) or len(value) != len(set(value)) or any(not nonempty(item) for item in value):
                errors.append(f"{path}.owner_materialization.{key}: must be a unique string array")
        materialized_ids = set(materialization.get("materialized_source_ids", [])) if isinstance(materialization.get("materialized_source_ids"), list) else set()
        if mode == "owner-personal" and not required_ids:
            errors.append(f"{path}.owner_materialization.required_sources: owner-personal mode requires at least one task-supplied source")
        if mode == "owner-personal" and (materialization.get("missing_source_ids") or not required_ids.issubset(materialized_ids)):
            errors.append(f"{path}.owner_materialization: every required source must be materialized with no missing source")
        if mode == "public-core" and (required_ids or materialized_ids or materialization.get("missing_source_ids")):
            errors.append(f"{path}.owner_materialization: public-core mode must not declare owner sources")
        task_snapshot = snapshot_by_id.get("task-private-learning", {})
        if mode == "owner-personal" and (
            task_snapshot.get("record_count") != record_count or task_snapshot.get("record_count", 0) < 1
        ):
            errors.append(f"{path}.owner_materialization.record_count: must match the task-private-learning snapshot")

    stage_receipts = evidence.get("stage_receipts")
    if not isinstance(stage_receipts, Mapping):
        errors.append(f"{path}.stage_receipts: must be an object")
        return
    for stage in required_stages:
        if stage not in STAGE_ORDER:
            errors.append(f"{path}.stage_receipts: unsupported required stage {stage}")
            continue
        receipts = stage_receipts.get(stage)
        spath = f"{path}.stage_receipts.{stage}"
        if not isinstance(receipts, list) or not receipts:
            errors.append(f"{spath}: must contain at least one finalized retrieval receipt")
            continue
        receipt_ids: set[str] = set()
        selected_sources: set[str] = set()
        selected_providers: set[str] = set()
        for index, receipt in enumerate(receipts):
            selected, sources, providers = _validate_receipt(receipt, stage, str(mode), snapshots, f"{spath}[{index}]", errors)
            receipt_id = receipt.get("receipt_id") if isinstance(receipt, Mapping) else None
            if receipt_id in receipt_ids:
                errors.append(f"{spath}[{index}].receipt_id: duplicate within stage")
            elif nonempty(receipt_id):
                receipt_ids.add(receipt_id)
            if not selected:
                errors.append(f"{spath}[{index}]: receipt must select at least one record")
            selected_sources.update(sources)
            selected_providers.update(providers)
        for provider_id, stages in sorted(required_provider_stages.items()):
            if stage in stages and provider_id not in snapshot_by_id:
                errors.append(f"{spath}: required runtime Provider {provider_id} is absent from the shared snapshot lock")
            elif stage in stages and provider_id not in selected_providers:
                errors.append(
                    f"{spath}: required runtime Provider {provider_id} must be selected by a finalized receipt"
                )
        if mode == "owner-personal":
            required_sources = requirements.get(stage, set())
            if not required_sources.issubset(materialized_ids):
                errors.append(f"{spath}: required owner sources were not materialized: {sorted(required_sources - materialized_ids)}")
            if not required_sources.issubset(selected_sources):
                errors.append(f"{spath}: finalized receipts did not consume required owner sources: {sorted(required_sources - selected_sources)}")
            if required_sources and "task-private-learning" not in selected_providers:
                errors.append(f"{spath}: must select first-class records from task-private-learning")


def index_lock_signature(evidence: Any) -> Any:
    """Return the immutable lock surfaces for cross-stage comparison."""

    if not isinstance(evidence, Mapping):
        return None
    materialization = evidence.get("owner_materialization") if isinstance(evidence.get("owner_materialization"), Mapping) else {}
    return {
        "mode": evidence.get("mode"),
        "runtime_lock_digest": evidence.get("runtime_lock_digest"),
        "provider_lock": evidence.get("provider_lock"),
        "owner_materialization": {
            "source_manifest_sha256": materialization.get("source_manifest_sha256"),
            "materialization_report_sha256": materialization.get("materialization_report_sha256"),
            "provider_id": materialization.get("provider_id"),
            "record_count": materialization.get("record_count"),
            "required_sources": materialization.get("required_sources"),
            "materialized_source_ids": materialization.get("materialized_source_ids"),
        },
    }
