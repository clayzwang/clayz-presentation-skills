# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Registered composition, failure, reference, and sequence metadata.

The implementation is original to Clayz Presentation Skills. External projects
influenced only the abstract separation of layout reasoning, failure knowledge,
and dataset-ready metadata. No upstream code, data, model, layout, or asset is
copied or materialized here.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime import REQUEST_CONTRACT, CompositeIndex, IndexProvider
from packages.index_runtime.utils import sha256_json, utc_now

COMPOSITION_PATTERN_CONTRACT = "io.clayz.presentation.composition-pattern/1.0"
FAILURE_PATTERN_CONTRACT = "io.clayz.presentation.failure-pattern/1.0"
REFERENCE_RECORD_CONTRACT = "io.clayz.presentation.reference-record/1.0"
SEQUENCE_RECORD_CONTRACT = "io.clayz.presentation.sequence-record/1.0"
PATTERN_REQUEST_CONTRACT = "io.clayz.presentation.composition-pattern-request/1.0"
PATTERN_RESOLUTION_CONTRACT = "io.clayz.presentation.composition-pattern-resolution/1.0"
COMPOSITION_PLAN_CONTRACT = "io.clayz.presentation.composition-plan/1.0"
DATASET_EXPORT_CONTRACT = "io.clayz.presentation.metadata-dataset-export/1.0"

PATTERN_LIBRARY_TYPES = {"composition-pattern", "failure-pattern", "reference", "sequence"}
STAGES = {"logic", "copy", "art-direction", "output", "supervisor"}
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
TYPE_CONFIG: dict[str, tuple[str, str, str, Callable[[Mapping[str, Any]], dict[str, Any]]]] = {}


class PatternLibraryError(ValueError):
    """Raised when a pattern decision would require invention or unsafe data."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PatternLibraryError(message)


def _mapping(value: Any, path: str) -> dict[str, Any]:
    _require(isinstance(value, Mapping), f"{path}: expected an object")
    return dict(value)


def _string(value: Any, path: str, *, allow_empty: bool = False) -> str:
    _require(isinstance(value, str), f"{path}: expected a string")
    if not allow_empty:
        _require(bool(value.strip()), f"{path}: expected a non-empty string")
    return value


def _string_list(value: Any, path: str, *, nonempty: bool = False) -> list[str]:
    _require(isinstance(value, list), f"{path}: expected an array")
    result = [_string(item, f"{path}[{index}]") for index, item in enumerate(value)]
    _require(len(result) == len(set(result)), f"{path}: values must be unique")
    if nonempty:
        _require(bool(result), f"{path}: expected at least one value")
    return result


def _exact(value: Mapping[str, Any], allowed: set[str], required: set[str], path: str) -> None:
    missing = required - set(value)
    extra = set(value) - allowed
    _require(not missing, f"{path}: missing fields {sorted(missing)}")
    _require(not extra, f"{path}: unsupported fields {sorted(extra)}")


def _identifier(value: Any, path: str, prefix: str) -> str:
    result = _string(value, path)
    _require(result.startswith(prefix) and bool(ID_PATTERN.fullmatch(result)), f"{path}: invalid identifier")
    return result


def _all_true(value: Any, fields: set[str], path: str) -> dict[str, Any]:
    result = _mapping(value, path)
    _exact(result, fields, fields, path)
    for key in fields:
        _require(result[key] is True, f"{path}.{key}: must be true")
    return result


def _validate_selection(value: Any, path: str) -> dict[str, Any]:
    selection = _mapping(value, path)
    fields = {"task_modes", "page_roles", "semantic_relations", "purpose_tags", "languages"}
    _exact(selection, fields, fields, path)
    _string_list(selection["task_modes"], f"{path}.task_modes", nonempty=True)
    _string_list(selection["page_roles"], f"{path}.page_roles", nonempty=True)
    _string_list(selection["semantic_relations"], f"{path}.semantic_relations")
    _string_list(selection["purpose_tags"], f"{path}.purpose_tags")
    _string_list(selection["languages"], f"{path}.languages", nonempty=True)
    return selection


def validate_composition_pattern(document: Mapping[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(_mapping(document, "$"))
    fields = {"contract", "composition_pattern_id", "revision", "title", "summary", "selection", "mapping", "applicability", "failure_pattern_ids", "decision_contract", "guards"}
    _exact(normalized, fields, fields, "$")
    _require(normalized["contract"] == COMPOSITION_PATTERN_CONTRACT, "$.contract: unexpected composition-pattern contract")
    _identifier(normalized["composition_pattern_id"], "$.composition_pattern_id", "pattern.")
    for key in ("revision", "title", "summary"):
        _string(normalized[key], f"$.{key}")
    _validate_selection(normalized["selection"], "$.selection")

    mapping = _mapping(normalized["mapping"], "$.mapping")
    mapping_fields = {"first_visual_role", "backbone_relation", "reading_path", "spatial_rules", "object_hierarchy"}
    _exact(mapping, mapping_fields, mapping_fields, "$.mapping")
    for key in ("first_visual_role", "backbone_relation", "reading_path"):
        _string(mapping[key], f"$.mapping.{key}")
    rules = mapping["spatial_rules"]
    _require(isinstance(rules, list) and bool(rules), "$.mapping.spatial_rules: expected a non-empty array")
    rule_pairs: set[tuple[str, str]] = set()
    for index, raw_rule in enumerate(rules):
        path = f"$.mapping.spatial_rules[{index}]"
        rule = _mapping(raw_rule, path)
        _exact(rule, {"semantic_relation", "spatial_behavior"}, {"semantic_relation", "spatial_behavior"}, path)
        pair = (_string(rule["semantic_relation"], f"{path}.semantic_relation"), _string(rule["spatial_behavior"], f"{path}.spatial_behavior"))
        _require(pair not in rule_pairs, f"{path}: duplicate spatial rule")
        rule_pairs.add(pair)
    _string_list(mapping["object_hierarchy"], "$.mapping.object_hierarchy", nonempty=True)

    applicability = _mapping(normalized["applicability"], "$.applicability")
    _exact(applicability, {"requires", "avoid_when"}, {"requires", "avoid_when"}, "$.applicability")
    _string_list(applicability["requires"], "$.applicability.requires", nonempty=True)
    _string_list(applicability["avoid_when"], "$.applicability.avoid_when", nonempty=True)
    failures = _string_list(normalized["failure_pattern_ids"], "$.failure_pattern_ids", nonempty=True)
    for index, failure_id in enumerate(failures):
        _identifier(failure_id, f"$.failure_pattern_ids[{index}]", "failure.")
    _all_true(normalized["decision_contract"], {"selection_reason_required", "rejection_reason_required", "constraints_required", "expected_visual_effect_required"}, "$.decision_contract")
    _all_true(normalized["guards"], {"brand_neutral", "original_method", "theme_independent", "visual_variant_independent", "layout_contract_independent", "coordinates_deferred", "editable_objects_required", "flattened_output_forbidden", "no_embedded_assets"}, "$.guards")
    return normalized


def validate_failure_pattern(document: Mapping[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(_mapping(document, "$"))
    fields = {"contract", "failure_pattern_id", "revision", "title", "summary", "signals", "ownership", "repair", "evidence_policy", "guards"}
    _exact(normalized, fields, fields, "$")
    _require(normalized["contract"] == FAILURE_PATTERN_CONTRACT, "$.contract: unexpected failure-pattern contract")
    _identifier(normalized["failure_pattern_id"], "$.failure_pattern_id", "failure.")
    for key in ("revision", "title", "summary"):
        _string(normalized[key], f"$.{key}")

    signals = _mapping(normalized["signals"], "$.signals")
    signal_fields = {"failure_signals", "rendered_symptoms", "not_sufficient_evidence"}
    _exact(signals, signal_fields, signal_fields, "$.signals")
    for key in signal_fields:
        _string_list(signals[key], f"$.signals.{key}", nonempty=True)

    ownership = _mapping(normalized["ownership"], "$.ownership")
    ownership_fields = {"earliest_preventable_stage", "diagnostic_stage", "repair_owner_stage"}
    _exact(ownership, ownership_fields, ownership_fields, "$.ownership")
    _require(ownership["diagnostic_stage"] == "supervisor", "$.ownership.diagnostic_stage: must be supervisor")
    for key in ("earliest_preventable_stage", "repair_owner_stage"):
        _require(ownership[key] in STAGES, f"$.ownership.{key}: unsupported stage")
    _require(ownership["repair_owner_stage"] != "supervisor", "$.ownership.repair_owner_stage: Supervisor diagnoses but does not own repairs")

    repair = _mapping(normalized["repair"], "$.repair")
    repair_fields = {"actions", "verification", "stop_conditions"}
    _exact(repair, repair_fields, repair_fields, "$.repair")
    for key in repair_fields:
        _string_list(repair[key], f"$.repair.{key}", nonempty=True)

    policy = _mapping(normalized["evidence_policy"], "$.evidence_policy")
    policy_fields = {"rendered_evidence_required", "automatic_signal_role", "human_ruling_required_for_promotion"}
    _exact(policy, policy_fields, policy_fields, "$.evidence_policy")
    _require(policy["rendered_evidence_required"] is True, "$.evidence_policy.rendered_evidence_required: must be true")
    _require(policy["automatic_signal_role"] == "diagnostic-only", "$.evidence_policy.automatic_signal_role: must be diagnostic-only")
    _require(policy["human_ruling_required_for_promotion"] is True, "$.evidence_policy.human_ruling_required_for_promotion: must be true")
    _all_true(normalized["guards"], {"brand_neutral", "original_method", "no_embedded_assets", "no_automatic_aesthetic_truth", "supervisor_does_not_own_repairs"}, "$.guards")
    return normalized


def validate_reference_record(document: Mapping[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(_mapping(document, "$"))
    fields = {"contract", "reference_record_id", "revision", "title", "summary", "provenance", "classification", "neighbors", "quality", "content_boundary"}
    _exact(normalized, fields, fields, "$")
    _require(normalized["contract"] == REFERENCE_RECORD_CONTRACT, "$.contract: unexpected reference-record contract")
    reference_id = _identifier(normalized["reference_record_id"], "$.reference_record_id", "reference.")
    for key in ("revision", "title", "summary"):
        _string(normalized[key], f"$.{key}")

    provenance = _mapping(normalized["provenance"], "$.provenance")
    provenance_fields = {"source_kind", "source_id", "source_revision", "rights_status", "materialization_policy", "never_copy"}
    _exact(provenance, provenance_fields, provenance_fields, "$.provenance")
    _require(provenance["source_kind"] in {"synthetic-only", "public-metadata", "private-metadata"}, "$.provenance.source_kind: unsupported value")
    _string(provenance["source_id"], "$.provenance.source_id")
    _string(provenance["source_revision"], "$.provenance.source_revision")
    _require(provenance["rights_status"] in {"redistributable-metadata", "metadata-only", "local-private"}, "$.provenance.rights_status: unsupported value")
    _require(provenance["materialization_policy"] in {"metadata-only", "local-only"}, "$.provenance.materialization_policy: unsupported value")
    _string_list(provenance["never_copy"], "$.provenance.never_copy")

    classification = _mapping(normalized["classification"], "$.classification")
    class_fields = {"page_role", "first_visual_role", "semantic_relations", "composition_pattern_ids", "dominant_medium", "content_load", "density", "reading_path", "series_role", "failure_pattern_ids", "languages"}
    _exact(classification, class_fields, class_fields, "$.classification")
    for key in ("page_role", "first_visual_role", "dominant_medium", "reading_path"):
        _string(classification[key], f"$.classification.{key}")
    _string_list(classification["semantic_relations"], "$.classification.semantic_relations")
    for index, pattern_id in enumerate(_string_list(classification["composition_pattern_ids"], "$.classification.composition_pattern_ids", nonempty=True)):
        _identifier(pattern_id, f"$.classification.composition_pattern_ids[{index}]", "pattern.")
    _require(classification["content_load"] in {"low", "medium", "high"}, "$.classification.content_load: unsupported value")
    _require(classification["density"] in {"low", "medium", "high"}, "$.classification.density: unsupported value")
    _require(classification["series_role"] in {"standalone", "opening", "continuation", "checkpoint", "closing", "break"}, "$.classification.series_role: unsupported value")
    for index, failure_id in enumerate(_string_list(classification["failure_pattern_ids"], "$.classification.failure_pattern_ids")):
        _identifier(failure_id, f"$.classification.failure_pattern_ids[{index}]", "failure.")
    _string_list(classification["languages"], "$.classification.languages", nonempty=True)

    neighbors = _mapping(normalized["neighbors"], "$.neighbors")
    _exact(neighbors, {"physical", "semantic"}, {"physical", "semantic"}, "$.neighbors")
    physical = _string_list(neighbors["physical"], "$.neighbors.physical")
    semantic = _string_list(neighbors["semantic"], "$.neighbors.semantic")
    _require(reference_id not in set(physical) | set(semantic), "$.neighbors: record cannot reference itself")
    for field, values in (("physical", physical), ("semantic", semantic)):
        for index, neighbor_id in enumerate(values):
            _identifier(neighbor_id, f"$.neighbors.{field}[{index}]", "reference.")

    quality = _mapping(normalized["quality"], "$.quality")
    quality_fields = {"status", "human_admitted", "decision_basis", "automatic_score_role"}
    _exact(quality, quality_fields, quality_fields, "$.quality")
    _require(quality["status"] in {"synthetic-fixture", "observation", "admitted"}, "$.quality.status: unsupported value")
    _require(isinstance(quality["human_admitted"], bool), "$.quality.human_admitted: expected boolean")
    _require(quality["decision_basis"] in {"synthetic-contract", "human-review"}, "$.quality.decision_basis: unsupported value")
    _require(quality["automatic_score_role"] == "diagnostic-only", "$.quality.automatic_score_role: must be diagnostic-only")
    if quality["status"] in {"synthetic-fixture", "admitted"}:
        _require(quality["human_admitted"] is True, "$.quality.human_admitted: admitted public metadata must be true")

    boundary = _mapping(normalized["content_boundary"], "$.content_boundary")
    boundary_fields = {"metadata_only", "media_included", "copy_included", "coordinates_included", "fonts_included", "model_features_included"}
    _exact(boundary, boundary_fields, boundary_fields, "$.content_boundary")
    _require(boundary["metadata_only"] is True, "$.content_boundary.metadata_only: must be true")
    for key in boundary_fields - {"metadata_only"}:
        _require(boundary[key] is False, f"$.content_boundary.{key}: must be false")
    return normalized


def validate_sequence_record(document: Mapping[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(_mapping(document, "$"))
    fields = {"contract", "sequence_record_id", "revision", "title", "summary", "slide_record_ids", "narrative_role", "persistent_elements", "progressive_change", "allowed_variation", "break_reason", "guards"}
    _exact(normalized, fields, fields, "$")
    _require(normalized["contract"] == SEQUENCE_RECORD_CONTRACT, "$.contract: unexpected sequence-record contract")
    _identifier(normalized["sequence_record_id"], "$.sequence_record_id", "sequence.")
    for key in ("revision", "title", "summary", "narrative_role"):
        _string(normalized[key], f"$.{key}")
    _string(normalized["break_reason"], "$.break_reason", allow_empty=True)
    slide_ids = _string_list(normalized["slide_record_ids"], "$.slide_record_ids", nonempty=True)
    _require(len(slide_ids) >= 2, "$.slide_record_ids: expected at least two references")
    for index, reference_id in enumerate(slide_ids):
        _identifier(reference_id, f"$.slide_record_ids[{index}]", "reference.")
    for key in ("persistent_elements", "progressive_change", "allowed_variation"):
        _string_list(normalized[key], f"$.{key}", nonempty=True)
    _all_true(normalized["guards"], {"metadata_only", "brand_neutral", "synthetic_only", "no_embedded_assets", "no_coordinates", "no_copy_text"}, "$.guards")
    return normalized


TYPE_CONFIG.update({
    "composition-pattern": ("catalog/composition-patterns", "composition_pattern_id", "method", validate_composition_pattern),
    "failure-pattern": ("catalog/failure-patterns", "failure_pattern_id", "method", validate_failure_pattern),
    "reference": ("catalog/references", "reference_record_id", "reference-metadata", validate_reference_record),
    "sequence": ("catalog/sequences", "sequence_record_id", "sequence-metadata", validate_sequence_record),
})


def validate_composition_pattern_request(document: Mapping[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(_mapping(document, "$"))
    required = {"contract", "request_id", "task_mode", "page_role", "semantic_relations", "purpose_tags", "language", "rights_context", "provider_ids", "constraints", "expected_visual_effect"}
    allowed = required | {"preferred_pattern_id"}
    _exact(normalized, allowed, required, "$")
    _require(normalized["contract"] == PATTERN_REQUEST_CONTRACT, "$.contract: unexpected composition-pattern-request contract")
    for key in ("request_id", "task_mode", "page_role", "language", "expected_visual_effect"):
        _string(normalized[key], f"$.{key}")
    _string_list(normalized["semantic_relations"], "$.semantic_relations")
    _string_list(normalized["purpose_tags"], "$.purpose_tags")
    _string_list(normalized["provider_ids"], "$.provider_ids", nonempty=True)
    _string_list(normalized["constraints"], "$.constraints", nonempty=True)
    _require(normalized["rights_context"] in {"public-open-source", "private-runtime"}, "$.rights_context: unsupported value")
    if "preferred_pattern_id" in normalized and normalized["preferred_pattern_id"] is not None:
        _identifier(normalized["preferred_pattern_id"], "$.preferred_pattern_id", "pattern.")
    return normalized


def _record(runtime: CompositeIndex, record_id: str) -> dict[str, Any]:
    item = runtime._records.get(record_id)
    if item is None:
        raise PatternLibraryError(f"registered record disappeared from runtime: {record_id}")
    return copy.deepcopy(item[1])


def load_registered_payload(root: Path, record: Mapping[str, Any]) -> dict[str, Any]:
    """Load and validate one hash-bound public metadata payload."""

    record_type = record.get("record_type")
    _require(record_type in TYPE_CONFIG, f"unsupported Pattern Library record type: {record_type}")
    directory, id_field, expected_asset_class, validator = TYPE_CONFIG[record_type]
    _require(record.get("classification", {}).get("brand_scope") == "none", f"{record.get('record_id')}: Pattern Library records must be brand-neutral")
    _require(record.get("classification", {}).get("asset_class") == expected_asset_class, f"{record.get('record_id')}: unexpected asset class")
    _require(record.get("payload", {}).get("kind") == "path", f"{record.get('record_id')}: payload must be a repository path")
    relative = Path(_string(record["payload"]["ref"], "record.payload.ref"))
    _require(not relative.is_absolute(), f"{record.get('record_id')}: payload path must be relative")
    path = (root / relative).resolve()
    allowed_root = (root / directory).resolve()
    try:
        path.relative_to(allowed_root)
    except ValueError as exc:
        raise PatternLibraryError(f"{record.get('record_id')}: payload path escapes {directory}") from exc
    _require(path.suffix.casefold() == ".json" and path.is_file(), f"{record.get('record_id')}: payload JSON is missing")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    _require(digest == record["source"]["sha256"], f"{record.get('record_id')}: payload hash mismatch")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PatternLibraryError(f"{record.get('record_id')}: invalid JSON: {exc}") from exc
    normalized = validator(document)
    _require(normalized[id_field] == record["record_id"], f"{record.get('record_id')}: payload ID does not match registry")
    return normalized


def resolve_composition_pattern(
    root: Path,
    runtime: CompositeIndex,
    request: Mapping[str, Any],
    *,
    created_at: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Resolve one registered pattern and all linked failure records."""

    normalized = validate_composition_pattern_request(request)
    retrieval_request = {
        "contract": REQUEST_CONTRACT,
        "request_id": f"{normalized['request_id']}-composition-pattern",
        "stage": "art-direction",
        "query": " ".join([normalized["page_role"], *normalized["semantic_relations"], *normalized["purpose_tags"]]),
        "rights_context": normalized["rights_context"],
        "require_human_admission": True,
        "limit": 20,
        "filters": {
            "record_types": ["composition-pattern"],
            "provider_ids": normalized["provider_ids"],
            "task_modes": [normalized["task_mode"]],
            "page_roles": [normalized["page_role"]],
            "semantic_relations": normalized["semantic_relations"],
            "purpose_tags": normalized["purpose_tags"],
            "languages": [normalized["language"]],
            "failure_signals": [],
            "include_metadata_only": False,
        },
        "neighbor_expansion": {"physical": 0, "semantic": 0},
    }
    raw_pattern_receipt = runtime.search(retrieval_request, created_at=created_at)
    eligible = [candidate for candidate in raw_pattern_receipt["candidates"] if candidate["materializable"]]
    preferred = normalized.get("preferred_pattern_id")
    selected_id: str | None = None
    unresolved_reason = ""
    if preferred is not None:
        if any(candidate["record_id"] == preferred for candidate in eligible):
            selected_id = preferred
        else:
            unresolved_reason = "preferred-pattern-not-retrieved"
    elif len(eligible) == 1:
        selected_id = eligible[0]["record_id"]
    elif not eligible:
        unresolved_reason = "no-eligible-registered-composition-pattern"
    else:
        unresolved_reason = "ambiguous-eligible-composition-patterns"

    selected_document: dict[str, Any] | None = None
    linked_failure_ids: list[str] = []
    failure_receipt: dict[str, Any] | None = None
    if selected_id:
        selected_document = load_registered_payload(root, _record(runtime, selected_id))
        linked_failure_ids = list(selected_document["failure_pattern_ids"])
        failure_request = {
            "contract": REQUEST_CONTRACT,
            "request_id": f"{normalized['request_id']}-linked-failures",
            "stage": "art-direction",
            "query": " ".join(linked_failure_ids),
            "rights_context": normalized["rights_context"],
            "require_human_admission": True,
            "limit": 50,
            "filters": {
                "record_types": ["failure-pattern"],
                "provider_ids": normalized["provider_ids"],
                "task_modes": [],
                "page_roles": [],
                "semantic_relations": [],
                "purpose_tags": [],
                "languages": [normalized["language"]],
                "failure_signals": [],
                "include_metadata_only": False,
            },
            "neighbor_expansion": {"physical": 0, "semantic": 0},
        }
        raw_failure_receipt = runtime.search(failure_request, created_at=created_at)
        failure_candidates = {candidate["record_id"] for candidate in raw_failure_receipt["candidates"] if candidate["materializable"]}
        missing = sorted(set(linked_failure_ids) - failure_candidates)
        if missing:
            unresolved_reason = "linked-failure-pattern-unavailable"
            selected_id = None
            failure_receipt = runtime.finalize_receipt(
                raw_failure_receipt,
                selected={},
                rejected={candidate["record_id"]: f"required linked set is incomplete; missing {', '.join(missing)}" for candidate in raw_failure_receipt["candidates"]},
            )
        else:
            failure_receipt = runtime.finalize_receipt(
                raw_failure_receipt,
                selected={failure_id: f"registered failure guard required by {selected_document['composition_pattern_id']}" for failure_id in linked_failure_ids},
                rejected={candidate["record_id"]: "not linked by the selected composition pattern" for candidate in raw_failure_receipt["candidates"] if candidate["record_id"] not in set(linked_failure_ids)},
            )

    if selected_id:
        selection_reason = "unique registered, human-admitted, materializable pattern matched the structured request"
        if preferred:
            selection_reason = "explicitly preferred registered pattern matched the structured request"
        selected_map = {selected_id: selection_reason}
        rejected_map = {candidate["record_id"]: "eligible alternative was not selected" for candidate in eligible if candidate["record_id"] != selected_id}
    else:
        selection_reason = ""
        selected_map = {}
        rejected_map = {}
        for candidate in eligible:
            if unresolved_reason == "preferred-pattern-not-retrieved":
                reason = "not the explicitly preferred pattern"
            elif unresolved_reason == "linked-failure-pattern-unavailable":
                reason = "required linked failure knowledge was unavailable"
            else:
                reason = "ambiguous candidate requires explicit selection"
            rejected_map[candidate["record_id"]] = reason
    pattern_receipt = runtime.finalize_receipt(raw_pattern_receipt, selected=selected_map, rejected=rejected_map)
    receipts = [pattern_receipt] + ([failure_receipt] if failure_receipt is not None else [])

    selected_meta = None
    if selected_id and selected_document is not None:
        record = _record(runtime, selected_id)
        selected_meta = {
            "record_id": record["record_id"],
            "provider_id": record["provider_id"],
            "payload_ref": record["payload"]["ref"],
            "source_sha256": record["source"]["sha256"],
            "selection_reason": selection_reason,
        }
    seed = {
        "request": normalized,
        "receipt_ids": [receipt["receipt_id"] for receipt in receipts],
        "selected_id": selected_id,
        "failure_ids": linked_failure_ids,
        "fallback": unresolved_reason,
    }
    resolution = {
        "contract": PATTERN_RESOLUTION_CONTRACT,
        "resolution_id": f"pattern-resolution-{sha256_json(seed)[:20]}",
        "request": normalized,
        "status": "selected" if selected_id else "unresolved",
        "retrieval_receipt_ids": [receipt["receipt_id"] for receipt in receipts],
        "selected_composition_pattern": selected_meta,
        "linked_failure_pattern_ids": linked_failure_ids if selected_id else [],
        "rejected_patterns": copy.deepcopy(pattern_receipt["selection"]["rejected"]),
        "fallback": {
            "used": selected_id is None,
            "reason": unresolved_reason,
            "next_action": "use-core-art-direction-without-claiming-a-pattern" if selected_id is None else "",
        },
        "guards": {
            "only_registered_records": True,
            "only_receipt_candidates_selected": True,
            "linked_failures_receipt_bound": True,
            "no_invented_patterns": True,
            "theme_not_selected_here": True,
            "visual_variant_not_selected_here": True,
            "layout_contract_not_selected_here": True,
            "coordinates_not_selected_here": True,
        },
    }
    return resolution, receipts


def compile_composition_pattern(
    root: Path,
    provider: IndexProvider,
    resolution: Mapping[str, Any],
    receipts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compile a receipt-selected pattern into a coordinate-free plan."""

    _require(resolution.get("contract") == PATTERN_RESOLUTION_CONTRACT, "invalid composition-pattern resolution")
    _require(resolution.get("status") == "selected", "cannot compile an unresolved composition pattern")
    selected = _mapping(resolution.get("selected_composition_pattern"), "resolution.selected_composition_pattern")
    receipts_by_id = {receipt.get("receipt_id"): receipt for receipt in receipts}
    _require(set(resolution.get("retrieval_receipt_ids", [])) == set(receipts_by_id), "resolution receipts do not match compiler inputs")
    for receipt in receipts:
        _require(receipt.get("hallucination_guard", {}).get("invented_record_count") == 0, "receipt reports invented records")
    selected_ids = {
        item.get("record_id")
        for receipt in receipts
        for item in receipt.get("selection", {}).get("selected", [])
    }
    _require(selected["record_id"] in selected_ids, "composition pattern is not selected in its receipt")
    linked_failure_ids = list(resolution.get("linked_failure_pattern_ids", []))
    _require(set(linked_failure_ids) <= selected_ids, "linked failure patterns are not all selected in receipts")

    provider_records = {record["record_id"]: record for record in provider.records}
    record = provider_records.get(selected["record_id"])
    _require(record is not None, "selected composition pattern is not registered in provider snapshot")
    _require(record["source"]["sha256"] == selected["source_sha256"], "resolution source hash does not match registry")
    _require(record["payload"]["ref"] == selected["payload_ref"], "resolution payload path does not match registry")
    pattern = load_registered_payload(root, record)
    _require(pattern["failure_pattern_ids"] == linked_failure_ids, "linked failure IDs drifted after resolution")

    failures: list[dict[str, Any]] = []
    for failure_id in linked_failure_ids:
        failure_record = provider_records.get(failure_id)
        _require(failure_record is not None, f"linked failure record disappeared: {failure_id}")
        failure = load_registered_payload(root, failure_record)
        failures.append({
            "failure_pattern_id": failure["failure_pattern_id"],
            "summary": failure["summary"],
            "failure_signals": failure["signals"]["failure_signals"],
            "earliest_preventable_stage": failure["ownership"]["earliest_preventable_stage"],
            "repair_owner_stage": failure["ownership"]["repair_owner_stage"],
            "verification": failure["repair"]["verification"],
            "automatic_signal_role": failure["evidence_policy"]["automatic_signal_role"],
        })
    request = resolution["request"]
    seed = {"resolution_id": resolution["resolution_id"], "record_id": record["record_id"], "revision": pattern["revision"]}
    return {
        "contract": COMPOSITION_PLAN_CONTRACT,
        "composition_plan_id": f"composition-plan-{sha256_json(seed)[:20]}",
        "status": "compiled",
        "lineage": {
            "resolution_id": resolution["resolution_id"],
            "retrieval_receipt_ids": list(resolution["retrieval_receipt_ids"]),
            "record_id": record["record_id"],
            "composition_pattern_id": pattern["composition_pattern_id"],
            "revision": pattern["revision"],
        },
        "decision": {
            "constraints": copy.deepcopy(request["constraints"]),
            "expected_visual_effect": request["expected_visual_effect"],
            "selection_reason": selected["selection_reason"],
            "rejected_patterns": copy.deepcopy(resolution["rejected_patterns"]),
        },
        "composition": {
            "title": pattern["title"],
            "summary": pattern["summary"],
            "mapping": copy.deepcopy(pattern["mapping"]),
            "applicability": copy.deepcopy(pattern["applicability"]),
        },
        "failure_guards": failures,
        "layers": {
            "theme": {"status": "external-not-consumed", "input_used": False},
            "visual_variant": {"status": "external-not-consumed", "input_used": False},
            "layout_contract": {"status": "external-not-consumed", "input_used": False},
            "composition_pattern": {"status": "registered-selected", "id": pattern["composition_pattern_id"]},
            "layout_tree": {"status": "pending", "input_used": False},
            "resolved_coordinates": {"status": "pending", "input_used": False},
        },
        "guards": {
            "only_receipt_selected_records": True,
            "no_invented_patterns": True,
            "no_coordinates_emitted": True,
            "no_assets_embedded": True,
            "editable_output_required": True,
            "automatic_scores_diagnostic_only": True,
        },
    }


def validate_registered_library(root: Path, provider: IndexProvider) -> dict[str, Any]:
    """Validate all registered public Pattern Library payloads and links."""

    records = [record for record in provider.records if record["record_type"] in PATTERN_LIBRARY_TYPES]
    payloads: dict[str, dict[str, Any]] = {}
    registered_paths: set[Path] = set()
    counts = {record_type: 0 for record_type in sorted(PATTERN_LIBRARY_TYPES)}
    for record in records:
        _require(record["governance"]["human_admitted"] and record["governance"]["quality_status"] == "admitted", f"{record['record_id']}: public Pattern Library record must be human-admitted")
        _require(record["governance"]["public_catalog_eligible"], f"{record['record_id']}: public Pattern Library record must be catalog-eligible")
        _require(record["rights"]["redistribution"] == "allowed" and record["rights"]["materialization"] == "allowed", f"{record['record_id']}: public Pattern Library metadata requires explicit rights")
        payloads[record["record_id"]] = load_registered_payload(root, record)
        registered_paths.add((root / record["payload"]["ref"]).resolve())
        counts[record["record_type"]] += 1

    pattern_ids = {record_id for record_id, payload in payloads.items() if payload.get("contract") == COMPOSITION_PATTERN_CONTRACT}
    failure_ids = {record_id for record_id, payload in payloads.items() if payload.get("contract") == FAILURE_PATTERN_CONTRACT}
    reference_ids = {record_id for record_id, payload in payloads.items() if payload.get("contract") == REFERENCE_RECORD_CONTRACT}
    for record_id in pattern_ids:
        missing = set(payloads[record_id]["failure_pattern_ids"]) - failure_ids
        _require(not missing, f"{record_id}: unregistered failure links {sorted(missing)}")
    for record_id in reference_ids:
        document = payloads[record_id]
        missing_patterns = set(document["classification"]["composition_pattern_ids"]) - pattern_ids
        missing_failures = set(document["classification"]["failure_pattern_ids"]) - failure_ids
        missing_neighbors = set(document["neighbors"]["physical"] + document["neighbors"]["semantic"]) - reference_ids
        _require(not missing_patterns, f"{record_id}: unregistered composition links {sorted(missing_patterns)}")
        _require(not missing_failures, f"{record_id}: unregistered failure links {sorted(missing_failures)}")
        _require(not missing_neighbors, f"{record_id}: orphan reference neighbors {sorted(missing_neighbors)}")
    for record_id, document in payloads.items():
        if document.get("contract") == SEQUENCE_RECORD_CONTRACT:
            missing = set(document["slide_record_ids"]) - reference_ids
            _require(not missing, f"{record_id}: unregistered sequence slides {sorted(missing)}")

    for record_type, (directory, _, _, _) in TYPE_CONFIG.items():
        root_dir = (root / directory).resolve()
        unregistered = {path.resolve() for path in root_dir.glob("*.json") if path.resolve() not in registered_paths}
        _require(not unregistered, f"{record_type}: unregistered JSON files {[path.name for path in sorted(unregistered)]}")
    return {"counts": counts, "payloads": payloads, "registered_paths": registered_paths}


def export_metadata_dataset(
    root: Path,
    provider: IndexProvider,
    *,
    record_types: Sequence[str] = ("composition-pattern", "failure-pattern", "reference", "sequence"),
    created_at: str | None = None,
) -> dict[str, Any]:
    """Export only admitted, registered public metadata; never source bytes."""

    requested = sorted(set(record_types))
    _require(bool(requested) and set(requested) <= PATTERN_LIBRARY_TYPES, "unsupported metadata export record types")
    validation = validate_registered_library(root, provider)
    rows: list[dict[str, Any]] = []
    for record in provider.records:
        if record["record_type"] not in requested:
            continue
        _require(record["provider_id"] == "builtin-catalog", f"{record['record_id']}: dataset export is public-catalog only")
        rows.append({
            "record_id": record["record_id"],
            "record_type": record["record_type"],
            "source_id": record["source"]["source_id"],
            "source_revision": record["source"]["source_revision"],
            "source_sha256": record["source"]["sha256"],
            "classification": copy.deepcopy(record["classification"]),
            "metadata": copy.deepcopy(validation["payloads"][record["record_id"]]),
        })
    rows.sort(key=lambda item: (item["record_type"], item["record_id"]))
    snapshot = provider.snapshot()
    seed = {"provider": snapshot, "records": [(row["record_id"], row["source_sha256"]) for row in rows]}
    return {
        "contract": DATASET_EXPORT_CONTRACT,
        "dataset_id": f"metadata-dataset-{sha256_json(seed)[:20]}",
        "created_at": created_at or utc_now(),
        "provider_snapshot": snapshot,
        "record_types": requested,
        "records": rows,
        "guards": {
            "only_registered_records": True,
            "human_admitted_only": True,
            "public_catalog_only": True,
            "metadata_only": True,
            "no_asset_bytes": True,
            "no_raw_source_text": True,
            "no_coordinates": True,
            "no_fonts": True,
            "no_model_weights": True,
            "generated_artifacts_auto_admitted": False,
            "automatic_aesthetic_truth": False,
        },
    }


def load_builtin_provider(root: Path) -> IndexProvider:
    return IndexProvider.from_jsonl("builtin-catalog", root / "catalog" / "records.jsonl")
