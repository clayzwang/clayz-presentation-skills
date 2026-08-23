# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Resolve and compile registered, brand-neutral semantic layout contracts.

This implementation is original to Clayz Presentation Skills. It follows the
general structured-generation idea of separating intent, structure, and final
geometry. It does not copy an upstream template, source file, or layout.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime import REQUEST_CONTRACT, CompositeIndex, IndexProvider
from packages.index_runtime.utils import sha256_json

LAYOUT_CONTRACT_CONTRACT = "io.clayz.presentation.layout-contract/1.0"
LAYOUT_CONTRACT_REQUEST_CONTRACT = "io.clayz.presentation.layout-contract-request/1.0"
LAYOUT_CONTRACT_RESOLUTION_CONTRACT = "io.clayz.presentation.layout-contract-resolution/1.0"
LAYOUT_COMPILATION_CONTRACT = "io.clayz.presentation.layout-compilation/1.0"
LAYOUT_TREE_CONTRACT = "io.clayz.presentation.layout-tree/1.0"

NODE_TYPES = {"split", "stack", "grid", "slot"}
DIRECTIONS = {"row", "column"}
GAP_TOKENS = {"none", "xs", "sm", "md", "lg"}
CONTENT_KINDS = {"text", "chart", "table", "diagram", "image", "source-note", "mixed"}
SPACING = {"none": 0.0, "xs": 0.08, "sm": 0.16, "md": 0.28, "lg": 0.44}
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")


class LayoutContractError(ValueError):
    """Raised when resolution or compilation would require a hidden choice."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise LayoutContractError(message)


def _mapping(value: Any, path: str) -> dict[str, Any]:
    _require(isinstance(value, Mapping), f"{path}: expected an object")
    return dict(value)


def _string(value: Any, path: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{path}: expected a non-empty string")
    return value


def _string_list(value: Any, path: str, *, nonempty: bool = False) -> list[str]:
    _require(isinstance(value, list), f"{path}: expected an array")
    result = [_string(item, f"{path}[{index}]") for index, item in enumerate(value)]
    _require(len(result) == len(set(result)), f"{path}: values must be unique")
    if nonempty:
        _require(bool(result), f"{path}: expected at least one value")
    return result


def _finite_number(value: Any, path: str, *, minimum: float | None = None) -> float:
    _require(not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value), f"{path}: expected a finite number")
    number = float(value)
    if minimum is not None:
        _require(number >= minimum, f"{path}: expected >= {minimum}")
    return number


def _exact_keys(value: Mapping[str, Any], allowed: set[str], required: set[str], path: str) -> None:
    missing = required - set(value)
    extra = set(value) - allowed
    _require(not missing, f"{path}: missing fields {sorted(missing)}")
    _require(not extra, f"{path}: unsupported fields {sorted(extra)}")


def validate_layout_contract(document: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one high-level layout contract without materializing geometry."""

    normalized = copy.deepcopy(_mapping(document, "$"))
    root_fields = {"contract", "layout_contract_id", "revision", "title", "summary", "selection", "slots", "structure", "guards"}
    _exact_keys(normalized, root_fields, root_fields, "$")
    _require(normalized["contract"] == LAYOUT_CONTRACT_CONTRACT, f"$.contract: expected {LAYOUT_CONTRACT_CONTRACT}")
    contract_id = _string(normalized["layout_contract_id"], "$.layout_contract_id")
    _require(bool(ID_PATTERN.fullmatch(contract_id)), "$.layout_contract_id: invalid identifier")
    _string(normalized["revision"], "$.revision")
    _string(normalized["title"], "$.title")
    _string(normalized["summary"], "$.summary")

    selection = _mapping(normalized["selection"], "$.selection")
    selection_fields = {"task_modes", "page_roles", "semantic_relations", "purpose_tags", "languages"}
    _exact_keys(selection, selection_fields, selection_fields, "$.selection")
    _string_list(selection["task_modes"], "$.selection.task_modes", nonempty=True)
    _string_list(selection["page_roles"], "$.selection.page_roles", nonempty=True)
    _string_list(selection["semantic_relations"], "$.selection.semantic_relations")
    _string_list(selection["purpose_tags"], "$.selection.purpose_tags")
    _string_list(selection["languages"], "$.selection.languages", nonempty=True)

    slots = normalized["slots"]
    _require(isinstance(slots, list) and bool(slots), "$.slots: expected a non-empty array")
    slot_ids: set[str] = set()
    slot_specs: dict[str, dict[str, Any]] = {}
    slot_fields = {"slot_id", "role", "required", "min_items", "max_items", "content_kinds"}
    for index, raw_slot in enumerate(slots):
        path = f"$.slots[{index}]"
        slot = _mapping(raw_slot, path)
        _exact_keys(slot, slot_fields, slot_fields, path)
        slot_id = _string(slot["slot_id"], f"{path}.slot_id")
        _require(bool(ID_PATTERN.fullmatch(slot_id)), f"{path}.slot_id: invalid identifier")
        _require(slot_id not in slot_ids, f"{path}.slot_id: duplicate slot {slot_id}")
        slot_ids.add(slot_id)
        _string(slot["role"], f"{path}.role")
        _require(isinstance(slot["required"], bool), f"{path}.required: expected boolean")
        minimum = slot["min_items"]
        maximum = slot["max_items"]
        _require(isinstance(minimum, int) and not isinstance(minimum, bool) and minimum >= 0, f"{path}.min_items: expected a non-negative integer")
        _require(isinstance(maximum, int) and not isinstance(maximum, bool) and maximum >= 1, f"{path}.max_items: expected a positive integer")
        _require(minimum <= maximum, f"{path}: min_items exceeds max_items")
        _require(not slot["required"] or minimum >= 1, f"{path}: required slots need min_items >= 1")
        kinds = _string_list(slot["content_kinds"], f"{path}.content_kinds", nonempty=True)
        _require(set(kinds) <= CONTENT_KINDS, f"{path}.content_kinds: unsupported content kind")
        slot_specs[slot_id] = slot

    node_ids: set[str] = set()
    referenced_slots: list[str] = []

    def visit_node(raw_node: Any, path: str, *, is_root: bool = False) -> None:
        node = _mapping(raw_node, path)
        allowed = {"id", "type", "semantic_relation", "direction", "gap_token", "padding_token", "weight", "columns", "column_span", "slot_id", "children"}
        _exact_keys(node, allowed, {"id", "type", "semantic_relation"}, path)
        node_id = _string(node["id"], f"{path}.id")
        _require(bool(ID_PATTERN.fullmatch(node_id)), f"{path}.id: invalid identifier")
        _require(node_id not in node_ids, f"{path}.id: duplicate node {node_id}")
        node_ids.add(node_id)
        node_type = _string(node["type"], f"{path}.type")
        _require(node_type in NODE_TYPES, f"{path}.type: unsupported node type {node_type!r}")
        _string(node["semantic_relation"], f"{path}.semantic_relation")
        if "weight" in node:
            _require(not is_root, f"{path}.weight: root weight is not meaningful")
            _finite_number(node["weight"], f"{path}.weight", minimum=0.000001)
        if "column_span" in node:
            span = node["column_span"]
            _require(isinstance(span, int) and not isinstance(span, bool) and span >= 1, f"{path}.column_span: expected a positive integer")
        if node_type == "slot":
            _exact_keys(node, {"id", "type", "semantic_relation", "weight", "column_span", "slot_id"}, {"id", "type", "semantic_relation", "slot_id"}, path)
            slot_id = _string(node["slot_id"], f"{path}.slot_id")
            _require(slot_id in slot_specs, f"{path}.slot_id: unknown slot {slot_id}")
            referenced_slots.append(slot_id)
            return
        _require("children" in node and isinstance(node["children"], list) and bool(node["children"]), f"{path}.children: expected a non-empty array")
        if node_type in {"split", "stack"}:
            direction = _string(node.get("direction"), f"{path}.direction")
            _require(direction in DIRECTIONS, f"{path}.direction: unsupported direction")
        else:
            _require("direction" not in node, f"{path}.direction: grid direction is implicit")
            columns = node.get("columns")
            _require(isinstance(columns, int) and not isinstance(columns, bool) and columns >= 1, f"{path}.columns: expected a positive integer")
        for token_field in ("gap_token", "padding_token"):
            if token_field in node:
                token = _string(node[token_field], f"{path}.{token_field}")
                _require(token in GAP_TOKENS, f"{path}.{token_field}: unsupported spacing token")
        for child_index, child in enumerate(node["children"]):
            visit_node(child, f"{path}.children[{child_index}]")

    visit_node(normalized["structure"], "$.structure", is_root=True)
    _require(len(referenced_slots) == len(set(referenced_slots)), "$.structure: every slot may appear only once")
    _require(set(referenced_slots) == slot_ids, "$.structure: every declared slot must appear exactly once")

    guards = _mapping(normalized["guards"], "$.guards")
    guard_fields = {"theme_independent", "visual_variant_independent", "coordinates_deferred", "brand_neutral", "no_embedded_assets"}
    _exact_keys(guards, guard_fields, guard_fields, "$.guards")
    for key in guard_fields:
        _require(guards[key] is True, f"$.guards.{key}: must be true")
    return normalized


def validate_layout_contract_request(document: Mapping[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(_mapping(document, "$"))
    required = {"contract", "request_id", "task_mode", "page_role", "semantic_relations", "purpose_tags", "language", "rights_context", "provider_ids"}
    allowed = required | {"preferred_contract_id"}
    _exact_keys(normalized, allowed, required, "$")
    _require(normalized["contract"] == LAYOUT_CONTRACT_REQUEST_CONTRACT, f"$.contract: expected {LAYOUT_CONTRACT_REQUEST_CONTRACT}")
    _string(normalized["request_id"], "$.request_id")
    _string(normalized["task_mode"], "$.task_mode")
    _string(normalized["page_role"], "$.page_role")
    _string_list(normalized["semantic_relations"], "$.semantic_relations")
    _string_list(normalized["purpose_tags"], "$.purpose_tags")
    _string(normalized["language"], "$.language")
    _require(normalized["rights_context"] in {"public-open-source", "private-runtime"}, "$.rights_context: unsupported context")
    _string_list(normalized["provider_ids"], "$.provider_ids", nonempty=True)
    if "preferred_contract_id" in normalized and normalized["preferred_contract_id"] is not None:
        preferred = _string(normalized["preferred_contract_id"], "$.preferred_contract_id")
        _require(bool(ID_PATTERN.fullmatch(preferred)), "$.preferred_contract_id: invalid identifier")
    return normalized


def validate_layout_contract_instance(document: Mapping[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(_mapping(document, "$"))
    fields = {"contract", "instance_id", "layout_contract_id", "semantic_layout_tree_id", "frame", "bindings"}
    _exact_keys(normalized, fields, fields, "$")
    _require(normalized["contract"] == "io.clayz.presentation.layout-contract-instance/1.0", "$.contract: unexpected instance contract")
    _string(normalized["instance_id"], "$.instance_id")
    _string(normalized["layout_contract_id"], "$.layout_contract_id")
    _string(normalized["semantic_layout_tree_id"], "$.semantic_layout_tree_id")
    frame = _mapping(normalized["frame"], "$.frame")
    _exact_keys(frame, {"x", "y", "w", "h"}, {"x", "y", "w", "h"}, "$.frame")
    for key in ("x", "y"):
        _finite_number(frame[key], f"$.frame.{key}")
    for key in ("w", "h"):
        _finite_number(frame[key], f"$.frame.{key}", minimum=0.000001)
    bindings = normalized["bindings"]
    _require(isinstance(bindings, list), "$.bindings: expected an array")
    seen_slots: set[str] = set()
    seen_copy_ids: set[str] = set()
    seen_semantic_node_ids: set[str] = set()
    for index, raw_binding in enumerate(bindings):
        path = f"$.bindings[{index}]"
        binding = _mapping(raw_binding, path)
        fields = {"slot_id", "content_kind", "copy_ids", "semantic_node_ids"}
        _exact_keys(binding, fields, fields, path)
        slot_id = _string(binding["slot_id"], f"{path}.slot_id")
        _require(slot_id not in seen_slots, f"{path}.slot_id: duplicate binding")
        seen_slots.add(slot_id)
        kind = _string(binding["content_kind"], f"{path}.content_kind")
        _require(kind in CONTENT_KINDS, f"{path}.content_kind: unsupported content kind")
        copy_ids = _string_list(binding["copy_ids"], f"{path}.copy_ids")
        duplicate = seen_copy_ids.intersection(copy_ids)
        _require(not duplicate, f"{path}.copy_ids: copy IDs already bound {sorted(duplicate)}")
        seen_copy_ids.update(copy_ids)
        semantic_node_ids = _string_list(binding["semantic_node_ids"], f"{path}.semantic_node_ids", nonempty=True)
        duplicate_nodes = seen_semantic_node_ids.intersection(semantic_node_ids)
        _require(not duplicate_nodes, f"{path}.semantic_node_ids: semantic nodes already bound {sorted(duplicate_nodes)}")
        seen_semantic_node_ids.update(semantic_node_ids)
    return normalized


def _find_record(runtime: CompositeIndex, record_id: str) -> dict[str, Any]:
    for provider in runtime.providers:
        for record in provider.records:
            if record["record_id"] == record_id:
                return copy.deepcopy(record)
    raise LayoutContractError(f"registered record disappeared from runtime: {record_id}")


def resolve_layout_contract(
    runtime: CompositeIndex,
    request: Mapping[str, Any],
    *,
    created_at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve one contract or return an explicit unresolved result.

    Automatic selection is allowed only for one eligible receipt candidate. If
    several records match, the caller must provide ``preferred_contract_id``.
    """

    normalized = validate_layout_contract_request(request)
    query_parts = [normalized["page_role"], *normalized["semantic_relations"], *normalized["purpose_tags"]]
    retrieval_request = {
        "contract": REQUEST_CONTRACT,
        "request_id": f"{normalized['request_id']}-layout-contract",
        "stage": "art-direction",
        "query": " ".join(query_parts),
        "rights_context": normalized["rights_context"],
        "require_human_admission": True,
        "limit": 10,
        "filters": {
            "record_types": ["layout-contract"],
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
    receipt = runtime.search(retrieval_request, created_at=created_at)
    eligible = [candidate for candidate in receipt["candidates"] if candidate["materializable"]]
    preferred = normalized.get("preferred_contract_id")
    selected_id: str | None = None
    unresolved_reason = ""
    if preferred is not None:
        if any(candidate["record_id"] == preferred for candidate in eligible):
            selected_id = preferred
        else:
            unresolved_reason = "preferred-contract-not-retrieved"
    elif len(eligible) == 1:
        selected_id = eligible[0]["record_id"]
    elif not eligible:
        unresolved_reason = "no-eligible-registered-layout-contract"
    else:
        unresolved_reason = "ambiguous-eligible-layout-contracts"

    selected = {selected_id: "registered eligible contract selected for the exact semantic request"} if selected_id else {}
    rejected = {
        candidate["record_id"]: ("not the explicitly preferred contract" if selected_id else "ambiguous candidate requires explicit selection")
        for candidate in eligible
        if candidate["record_id"] != selected_id
    }
    finalized = runtime.finalize_receipt(receipt, selected=selected, rejected=rejected)
    selected_record = _find_record(runtime, selected_id) if selected_id else None
    selected_payload = None
    if selected_record is not None:
        selected_payload = {
            "record_id": selected_record["record_id"],
            "provider_id": selected_record["provider_id"],
            "payload_ref": selected_record["payload"]["ref"],
            "source_sha256": selected_record["source"]["sha256"],
        }
    fallback_reason = unresolved_reason or ""
    seed = {
        "request": normalized,
        "receipt_id": finalized["receipt_id"],
        "selected_record_id": selected_id,
        "fallback_reason": fallback_reason,
    }
    resolution = {
        "contract": LAYOUT_CONTRACT_RESOLUTION_CONTRACT,
        "resolution_id": f"layout-resolution-{sha256_json(seed)[:20]}",
        "request_id": normalized["request_id"],
        "status": "selected" if selected_id else "unresolved",
        "retrieval_receipt_id": finalized["receipt_id"],
        "selected_layout_contract": selected_payload,
        "fallback": {
            "used": selected_id is None,
            "reason": fallback_reason,
            "next_action": "use-core-semantic-layout-tree-without-claiming-a-contract" if selected_id is None else "",
        },
        "guards": {
            "only_registered_records": True,
            "only_receipt_candidates_selected": True,
            "no_invented_layout_contracts": True,
            "theme_not_selected_here": True,
            "visual_variant_not_selected_here": True,
        },
    }
    return resolution, finalized


def _record_for_resolution(provider: IndexProvider, resolution: Mapping[str, Any]) -> dict[str, Any]:
    selected = resolution.get("selected_layout_contract")
    _require(isinstance(selected, Mapping), "resolution has no selected layout contract")
    record_id = selected.get("record_id")
    for record in provider.records:
        if record["record_id"] == record_id:
            return copy.deepcopy(record)
    raise LayoutContractError(f"selected contract is not registered in provider snapshot: {record_id}")


def _load_registered_contract(root: Path, record: Mapping[str, Any]) -> dict[str, Any]:
    _require(record.get("record_type") == "layout-contract", "selected record is not a layout-contract")
    _require(record.get("payload", {}).get("kind") == "path", "layout-contract payload must be a repository path")
    relative = Path(_string(record["payload"]["ref"], "record.payload.ref"))
    _require(not relative.is_absolute(), "layout-contract payload path must be relative")
    path = (root / relative).resolve()
    catalog_root = (root / "catalog" / "layout-contracts").resolve()
    try:
        path.relative_to(catalog_root)
    except ValueError as exc:
        raise LayoutContractError("layout-contract payload must stay under catalog/layout-contracts") from exc
    _require(path.suffix.casefold() == ".json" and path.is_file(), f"layout-contract payload missing: {relative.as_posix()}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    _require(digest == record["source"]["sha256"], f"layout-contract payload hash mismatch: {relative.as_posix()}")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LayoutContractError(f"invalid layout-contract JSON: {relative.as_posix()}: {exc}") from exc
    return validate_layout_contract(document)


def _compile_node(node: Mapping[str, Any], slots: Mapping[str, Mapping[str, Any]], bindings: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    node_type = node["type"]
    result: dict[str, Any] = {
        "id": node["id"],
        "type": "leaf" if node_type == "slot" else ("grid" if node_type == "grid" else node["direction"]),
        "intent": node["semantic_relation"],
        "contract_node_id": node["id"],
    }
    if "weight" in node:
        result["flex"] = node["weight"]
    if "column_span" in node:
        result["column_span"] = node["column_span"]
    if node_type == "slot":
        slot_id = node["slot_id"]
        binding = bindings.get(slot_id)
        result["slot_id"] = slot_id
        result["role"] = slots[slot_id]["role"]
        result["copy_ids"] = list(binding["copy_ids"]) if binding else []
        result["semantic_node_ids"] = list(binding["semantic_node_ids"]) if binding else []
        return result
    if "gap_token" in node:
        result["gap"] = SPACING[node["gap_token"]]
    if "padding_token" in node:
        result["padding"] = SPACING[node["padding_token"]]
    if node_type == "grid":
        result["columns"] = node["columns"]
    result["children"] = [_compile_node(child, slots, bindings) for child in node["children"]]
    return result


def compile_layout_contract(
    root: Path,
    provider: IndexProvider,
    resolution: Mapping[str, Any],
    receipt: Mapping[str, Any],
    instance: Mapping[str, Any],
) -> dict[str, Any]:
    """Compile a selected registered contract into a semantic layout tree."""

    _require(resolution.get("contract") == LAYOUT_CONTRACT_RESOLUTION_CONTRACT, "invalid layout-contract resolution")
    _require(resolution.get("status") == "selected", "cannot compile an unresolved layout contract")
    _require(receipt.get("receipt_id") == resolution.get("retrieval_receipt_id"), "resolution and receipt do not match")
    selected_meta = _mapping(resolution.get("selected_layout_contract"), "resolution.selected_layout_contract")
    selected_ids = {item.get("record_id") for item in receipt.get("selection", {}).get("selected", [])}
    _require(selected_meta.get("record_id") in selected_ids, "selected layout contract was not selected in the receipt")
    _require(receipt.get("hallucination_guard", {}).get("invented_record_count") == 0, "receipt reports invented records")

    record = _record_for_resolution(provider, resolution)
    _require(record["source"]["sha256"] == selected_meta.get("source_sha256"), "resolution source hash does not match registry")
    _require(record["payload"]["ref"] == selected_meta.get("payload_ref"), "resolution payload path does not match registry")
    contract_document = _load_registered_contract(root, record)
    normalized_instance = validate_layout_contract_instance(instance)
    _require(normalized_instance["layout_contract_id"] == contract_document["layout_contract_id"], "instance layout_contract_id does not match selected contract")

    slots = {slot["slot_id"]: slot for slot in contract_document["slots"]}
    bindings = {binding["slot_id"]: binding for binding in normalized_instance["bindings"]}
    unknown_slots = set(bindings) - set(slots)
    _require(not unknown_slots, f"instance binds unknown slots: {sorted(unknown_slots)}")
    for slot_id, slot in slots.items():
        count = len(bindings.get(slot_id, {}).get("copy_ids", []))
        _require(count >= slot["min_items"], f"slot {slot_id}: expected at least {slot['min_items']} copy IDs")
        _require(count <= slot["max_items"], f"slot {slot_id}: expected at most {slot['max_items']} copy IDs")
        if slot_id in bindings:
            _require(bindings[slot_id]["content_kind"] in slot["content_kinds"], f"slot {slot_id}: content kind is not allowed")

    tree_seed = {
        "record_id": record["record_id"],
        "revision": contract_document["revision"],
        "instance": normalized_instance,
    }
    tree_id = f"layout-tree-{sha256_json(tree_seed)[:20]}"
    layout_tree = {
        "contract": LAYOUT_TREE_CONTRACT,
        "tree_id": tree_id,
        "source": {
            "layout_contract_id": contract_document["layout_contract_id"],
            "layout_contract_revision": contract_document["revision"],
            "record_id": record["record_id"],
            "retrieval_receipt_id": receipt["receipt_id"],
            "instance_id": normalized_instance["instance_id"],
            "semantic_layout_tree_id": normalized_instance["semantic_layout_tree_id"],
        },
        "frame": copy.deepcopy(normalized_instance["frame"]),
        "root": _compile_node(contract_document["structure"], slots, bindings),
    }
    compilation_seed = {"tree_id": tree_id, "resolution_id": resolution["resolution_id"]}
    return {
        "contract": LAYOUT_COMPILATION_CONTRACT,
        "compilation_id": f"layout-compilation-{sha256_json(compilation_seed)[:20]}",
        "status": "compiled",
        "lineage": {
            "resolution_id": resolution["resolution_id"],
            "retrieval_receipt_id": receipt["receipt_id"],
            "record_id": record["record_id"],
            "layout_contract_id": contract_document["layout_contract_id"],
            "layout_contract_revision": contract_document["revision"],
            "instance_id": normalized_instance["instance_id"],
            "semantic_layout_tree_id": normalized_instance["semantic_layout_tree_id"],
        },
        "layers": {
            "theme": {"status": "external-not-consumed", "input_used": False},
            "visual_variant": {"status": "external-not-consumed", "input_used": False},
            "layout_contract": {"status": "registered-selected", "id": contract_document["layout_contract_id"]},
            "layout_tree": {"status": "compiled", "id": tree_id},
            "resolved_coordinates": {"status": "pending", "contract": "io.clayz.presentation.layout-resolution/1.0"},
        },
        "layout_tree": layout_tree,
    }


def load_builtin_provider(root: Path) -> IndexProvider:
    """Load the public built-in catalog for CLI and validation workflows."""

    return IndexProvider.from_jsonl("builtin-catalog", root / "catalog" / "records.jsonl")
