# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Hash-bound promotion of human-admitted learning observations."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any

from packages.index_runtime import INDEX_CONTRACT, IndexProvider


LEARNING_CONTRACT = "io.clayz.presentation.learning-record/1.0"
ADMISSION_CONTRACT = "io.clayz.presentation.learning-admission/1.0"
FEEDBACK_REPORT_CONTRACT = "io.clayz.presentation.feedback-index-report/1.0"
STAGES = {"logic", "copy", "art-direction", "output"}
PROMOTION_TARGETS = {"knowledge", "failure-pattern", "compatibility-note", "proven-repair"}


class FeedbackError(ValueError):
    """Raised when feedback would enter retrieval without valid admission evidence."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FeedbackError(message)


def _nonempty(value: Any, path: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{path} must be non-empty")
    return value


def _string_list(value: Any, path: str) -> list[str]:
    _require(isinstance(value, list), f"{path} must be a list")
    _require(all(isinstance(item, str) and item.strip() for item in value), f"{path} must contain non-empty strings")
    _require(len(value) == len(set(value)), f"{path} must not contain duplicates")
    return list(value)


def _timestamp(value: Any, path: str) -> str:
    text = _nonempty(value, path)
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FeedbackError(f"{path} must be ISO-8601") from exc
    return text


def _sha256_json(value: Mapping[str, Any]) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def learning_record_sha256(record: Mapping[str, Any]) -> str:
    return _sha256_json(validate_learning_record(record))


def validate_learning_record(record: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(record, Mapping), "learning record must be an object")
    value = copy.deepcopy(dict(record))
    _require(value.get("contract") == LEARNING_CONTRACT, f"learning.contract must be {LEARNING_CONTRACT}")
    record_id = _nonempty(value.get("record_id"), "learning.record_id")
    _require(bool(re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,127}", record_id)), "learning.record_id has invalid characters")
    stage = _nonempty(value.get("stage"), "learning.stage")
    _require(stage in STAGES, "learning.stage is unsupported")
    for key in ("task_purpose", "observation", "decision"):
        _nonempty(value.get(key), f"learning.{key}")
    _string_list(value.get("evidence_refs", []), "learning.evidence_refs")
    _require(value.get("user_ruling") is None or isinstance(value.get("user_ruling"), str), "learning.user_ruling must be string or null")
    _require(value.get("promotion_status") == "observation", "source learning records must remain observation-only")
    _timestamp(value.get("created_at"), "learning.created_at")

    classification = value.get("classification")
    _require(isinstance(classification, Mapping), "learning.classification must be an object")
    for key in ("task_modes", "page_roles", "purpose_tags", "failure_signals"):
        _string_list(classification.get(key, []), f"learning.classification.{key}")
    _nonempty(classification.get("language"), "learning.classification.language")

    source = value.get("source")
    _require(isinstance(source, Mapping), "learning.source must be an object")
    _require(source.get("source_kind") in {"task-observation", "synthetic-fixture"}, "learning.source.source_kind is unsupported")
    _nonempty(source.get("source_id"), "learning.source.source_id")
    _nonempty(source.get("source_revision"), "learning.source.source_revision")

    guards = value.get("guards")
    _require(isinstance(guards, Mapping), "learning.guards must be an object")
    _require(guards.get("human_admission_required") is True, "learning must require human admission")
    _require(guards.get("generated_artifact_auto_admitted") is False, "generated artifacts must not be auto-admitted")
    _require(guards.get("supervisor_owns_store") is False, "Supervisor must not own a feedback store")
    return value


def validate_learning_admission(admission: Mapping[str, Any], record: Mapping[str, Any] | None = None) -> dict[str, Any]:
    _require(isinstance(admission, Mapping), "learning admission must be an object")
    value = copy.deepcopy(dict(admission))
    _require(value.get("contract") == ADMISSION_CONTRACT, f"admission.contract must be {ADMISSION_CONTRACT}")
    _nonempty(value.get("admission_id"), "admission.admission_id")
    _require(value.get("subject_type") == "learning", "admission.subject_type must be learning")
    _nonempty(value.get("subject_id"), "admission.subject_id")
    sha = _nonempty(value.get("subject_sha256"), "admission.subject_sha256")
    _require(bool(re.fullmatch(r"[0-9a-f]{64}", sha)), "admission.subject_sha256 must be lowercase SHA-256")
    _nonempty(value.get("admitted_by"), "admission.admitted_by")
    _timestamp(value.get("admitted_at"), "admission.admitted_at")
    _string_list(value.get("use_for", []), "admission.use_for")
    _string_list(value.get("never_copy", []), "admission.never_copy")
    _nonempty(value.get("decision_notes"), "admission.decision_notes")
    _require(value.get("promotion_target") in PROMOTION_TARGETS, "admission.promotion_target is unsupported")
    _require(value.get("public_catalog_eligible") is False, "learning admission must not imply public publication")
    if record is not None:
        normalized = validate_learning_record(record)
        _require(value["subject_id"] == normalized["record_id"], "admission subject does not match learning record")
        _require(value["subject_sha256"] == _sha256_json(normalized), "learning record changed after admission")
    return value


def _index_record(record: Mapping[str, Any], admission: Mapping[str, Any], provider_id: str) -> dict[str, Any]:
    learning = validate_learning_record(record)
    admitted = validate_learning_admission(admission, learning)
    classification = learning["classification"]
    record_sha = _sha256_json(learning)
    return {
        "contract": INDEX_CONTRACT,
        "record_id": learning["record_id"],
        "record_type": "learning",
        "provider_id": provider_id,
        "title": learning["task_purpose"],
        "summary": learning["observation"],
        "source": {
            "source_id": learning["source"]["source_id"],
            "source_uri": f"learning://{learning['stage']}/{learning['record_id']}",
            "source_revision": learning["source"]["source_revision"],
            "sha256": record_sha,
        },
        "governance": {
            "human_admitted": True,
            "quality_status": "admitted",
            "public_catalog_eligible": False,
            "deprecated": False,
        },
        "rights": {
            "license": "private-learning-record",
            "redistribution": "local-private",
            "materialization": "local-only",
            "commercial_use": None,
            "derivative_use": None,
            "attribution_required": False,
            "never_copy": admitted["never_copy"],
        },
        "classification": {
            "stages": [learning["stage"]],
            "task_modes": classification["task_modes"],
            "page_roles": classification["page_roles"],
            "semantic_relations": [],
            "purpose_tags": sorted(set(classification["purpose_tags"] + admitted["use_for"] + [admitted["promotion_target"]])),
            "languages": [classification["language"]],
            "failure_signals": classification["failure_signals"],
            "asset_class": "learning-metadata",
            "brand_scope": "none",
        },
        "payload": {
            "kind": "inline",
            "ref": {
                "promotion_target": admitted["promotion_target"],
                "observation": learning["observation"],
                "decision": learning["decision"],
                "user_ruling": learning["user_ruling"],
                "evidence_refs": learning["evidence_refs"],
            },
        },
        "neighbors": {"physical": [], "semantic": []},
    }


def build_learning_provider(
    records: Iterable[Mapping[str, Any]],
    admissions: Iterable[Mapping[str, Any]],
    *,
    provider_id: str = "feedback-learning",
    created_at: str,
) -> tuple[IndexProvider, dict[str, Any]]:
    normalized_records = [validate_learning_record(record) for record in records]
    admission_by_subject: dict[str, dict[str, Any]] = {}
    malformed_admissions: list[str] = []
    for raw in admissions:
        try:
            admission = validate_learning_admission(raw)
        except FeedbackError as exc:
            malformed_admissions.append(str(exc))
            continue
        subject_id = admission["subject_id"]
        _require(subject_id not in admission_by_subject, f"duplicate learning admission: {subject_id}")
        admission_by_subject[subject_id] = admission

    index_records: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    seen: set[str] = set()
    for record in sorted(normalized_records, key=lambda item: item["record_id"]):
        record_id = record["record_id"]
        _require(record_id not in seen, f"duplicate learning record: {record_id}")
        seen.add(record_id)
        admission = admission_by_subject.get(record_id)
        if admission is None:
            skipped.append({"record_id": record_id, "reason": "human-admission-required"})
            continue
        try:
            index_records.append(_index_record(record, admission, provider_id))
        except FeedbackError as exc:
            skipped.append({"record_id": record_id, "reason": str(exc)})

    provider = IndexProvider.from_records(provider_id, index_records)
    report = {
        "contract": FEEDBACK_REPORT_CONTRACT,
        "created_at": created_at,
        "provider_snapshot": provider.snapshot(),
        "source_record_count": len(normalized_records),
        "admitted_record_count": len(index_records),
        "skipped": skipped,
        "malformed_admissions": malformed_admissions,
        "guards": {
            "human_admission_required": True,
            "hash_match_required": True,
            "source_observation_unchanged": True,
            "public_catalog_eligible": False,
            "generated_artifacts_auto_admitted": False,
            "supervisor_owns_store": False,
        },
    }
    return provider, report
