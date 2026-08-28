#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate an approved PPT art-direction plan against a copy-approved package."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from config_policy import ValidationPolicy, load_policy
from index_evidence import index_lock_signature, validate_index_evidence
from resource_inventory import resource_inventory_signature
from validate_ppt_package import validate_package


CONTRACT_VERSION = "1.6"
TARGET_TYPES = {"shape", "table-cell", "chart-label"}
VERIFY_METHODS = {"shape-name", "paragraph-exact"}
VISUAL_ROLES = {"primary", "secondary", "tertiary", "annotation"}
ALIGNMENTS = {"left", "center", "right", "decimal", "grid"}
AUTO_FIT = {"none", "shrink-text-on-overflow"}
DOMINANT_MEDIA = {
    "typography", "data-chart", "table", "relationship-diagram",
    "photo-or-screenshot", "scenario-illustration", "mixed",
}
ATOMIC_REVIEW_KEYS = {
    "all_copy_units_mapped", "parent_child_targets_distinct",
    "sibling_targets_parallel", "locked_text_verbatim",
    "intentional_breaks_planned", "no_hierarchy_encoded_only_by_punctuation",
    "atomic_units_organized_into_visual_grammar", "one_copy_one_card_default_rejected",
}
STRUCTURE_TYPES = {
    "typography", "cards", "columns", "table", "data-chart", "timeline", "swimlane",
    "matrix", "process", "relationship-diagram", "hierarchy", "comparison", "mixed",
    "photo-or-screenshot", "scenario-illustration", "other",
}
MAPPING_MODES = {"composite-structure", "independent-shapes", "mixed"}
OBJECT_TYPES = {"shape", "native-table", "native-chart", "connector", "picture", "diagram"}
QUANTITATIVE_ENCODINGS = {"native-chart", "native-table", "kpi-text", "shape-encoded-chart", "not-applicable"}
QUANTITATIVE_SCALES = {"linear", "log", "index", "percentage", "categorical", "none"}
GENERIC_FIRST_VISUALS = {
    "主图", "结论结构", "主表", "结构图", "关系图", "数据图", "图表", "视觉中心",
    "mainvisual", "hero", "herovisual", "mainchart", "maintable", "structure",
}
COMPOSITE_STRUCTURES = {"table", "data-chart", "timeline", "swimlane", "matrix", "process", "relationship-diagram", "hierarchy"}
POST_RENDER_KEYS = {
    "reviewed_at_full_size", "no_collision", "no_collision_or_tangency",
    "full_size_reviewed", "render_file",
}
SERIES_BEHAVIORS = {"standalone", "locked-backbone", "controlled-variation", "series-break"}
WHITESPACE_MODES = {"none", "future-space", "unknown-space", "pause"}
TREE_MODES = {"flat", "hierarchical"}
TREE_NODE_TYPES = {"canvas", "intent-zone", "group", "element", "protected-whitespace"}
TREE_SHAPE_FAMILIES = {
    "none", "rectangle", "rounded-rectangle", "ellipse", "path", "line",
    "table", "chart", "image", "text", "mixed",
}
TREE_RELATIONS = {"contains", "peer", "sequence", "cause", "condition", "supports", "compares", "feedback", "anchors"}
DIRECTED_TREE_RELATIONS = {"contains", "sequence", "cause", "condition", "supports", "feedback", "anchors"}
UNDIRECTED_TREE_RELATIONS = {"peer", "compares"}
TREE_CHECKS = {
    "single_root", "all_copy_ids_covered_once", "hierarchy_explains_grouping",
    "reading_order_explicit", "shape_choices_semantic", "no_flat_card_default",
}
SELF_CORRECTION_DIMENSIONS = {
    "production_integrity", "typography_readability", "attention_hierarchy",
    "structure_semantics", "composition_task_fit",
}
CANVAS_TYPES = {"none", "photo", "screenshot", "illustration", "mixed"}
CROP_STRATEGIES = {"not-applicable", "contain", "cover", "focal-crop"}
CONTRAST_STRATEGIES = {
    "not-applicable", "native", "reposition-copy", "local-scrim",
    "solid-support-surface", "mixed",
}
OVERLAY_POLICIES = {"none", "local-scrim", "local-support-surface"}
ZONE_PROTECTION = {"hard", "soft"}
PLACEMENT_SUITABILITY = {"primary", "secondary", "avoid"}
ANCHOR_EDGES = {"top", "bottom", "left", "right", "center"}
TEMPLATE_MODES = {"derive-not-clone"}
ICON_POLICIES = {"semantic-only", "not-required"}
FAMILY_CONSISTENCY = {"single-family", "intentional-mix", "not-applicable"}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def require_keys(obj: Any, keys: set[str], path: str, errors: list[str]) -> None:
    if not isinstance(obj, dict):
        errors.append(f"{path}: must be an object")
        return
    missing = sorted(keys - set(obj))
    if missing:
        errors.append(f"{path}: missing keys {missing}")


def stage_receipt_selection(evidence: Any, stage: str) -> tuple[set[str], set[str]]:
    receipt_ids: set[str] = set()
    record_ids: set[str] = set()
    if not isinstance(evidence, dict):
        return receipt_ids, record_ids
    receipts = evidence.get("stage_receipts", {}).get(stage, [])
    if not isinstance(receipts, list):
        return receipt_ids, record_ids
    for receipt in receipts:
        if not isinstance(receipt, dict):
            continue
        if nonempty(receipt.get("receipt_id")):
            receipt_ids.add(receipt["receipt_id"])
        selection = receipt.get("selection", {})
        for item in selection.get("selected", []) if isinstance(selection, dict) else []:
            if isinstance(item, dict) and nonempty(item.get("record_id")):
                record_ids.add(item["record_id"])
    return receipt_ids, record_ids


def normalize_first_visual(value: Any) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", str(value or "")).casefold()


def is_generic_first_visual(value: Any) -> bool:
    normalized = normalize_first_visual(value)
    return normalized in GENERIC_FIRST_VISUALS or len(normalized) < 4


def scan_post_render(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in POST_RENDER_KEYS:
                errors.append(f"{path}.{key}: post-render result belongs in ppt-output-qa.json")
            scan_post_render(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_post_render(child, f"{path}[{index}]", errors)


def unique_string_array(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == len(set(value))
        and all(nonempty(item) for item in value)
    )


def validate_content_aware_canvas(
    canvas: Any,
    dominant_medium: Any,
    expected_copy_ids: list[str],
    path: str,
    errors: list[str],
) -> None:
    keys = {
        "enabled", "canvas_type", "subject_protection_zones",
        "candidate_placement_zones", "crop_strategy", "contrast_strategy",
        "directional_flow", "overlay_policy", "evidence_basis",
    }
    require_keys(canvas, keys, path, errors)
    if not isinstance(canvas, dict):
        return
    enabled = canvas.get("enabled")
    if not isinstance(enabled, bool):
        errors.append(f"{path}.enabled: must be boolean")
        return
    image_led = dominant_medium in {"photo-or-screenshot", "scenario-illustration"}
    if image_led and not enabled:
        errors.append(f"{path}.enabled: image-led slides require content-aware analysis")
    if not enabled:
        expected = {
            "canvas_type": "none",
            "subject_protection_zones": [],
            "candidate_placement_zones": [],
            "crop_strategy": "not-applicable",
            "contrast_strategy": "not-applicable",
            "directional_flow": "not-applicable",
            "overlay_policy": "none",
            "evidence_basis": "not-applicable",
        }
        for key, value in expected.items():
            if canvas.get(key) != value:
                errors.append(f"{path}.{key}: disabled canvas must use {value!r}")
        return
    if canvas.get("canvas_type") not in CANVAS_TYPES - {"none"}:
        errors.append(f"{path}.canvas_type: enabled canvas requires an image-like type")
    if canvas.get("crop_strategy") not in CROP_STRATEGIES - {"not-applicable"}:
        errors.append(f"{path}.crop_strategy: enabled canvas requires a crop decision")
    if canvas.get("contrast_strategy") not in CONTRAST_STRATEGIES - {"not-applicable"}:
        errors.append(f"{path}.contrast_strategy: enabled canvas requires a contrast decision")
    if canvas.get("overlay_policy") not in OVERLAY_POLICIES:
        errors.append(f"{path}.overlay_policy: invalid value")
    if not nonempty(canvas.get("directional_flow")) or canvas.get("directional_flow") == "not-applicable":
        errors.append(f"{path}.directional_flow: enabled canvas requires observed visual direction")
    if not nonempty(canvas.get("evidence_basis")) or canvas.get("evidence_basis") == "not-applicable":
        errors.append(f"{path}.evidence_basis: enabled canvas requires traceable visual evidence")

    subject_zones = canvas.get("subject_protection_zones")
    if not isinstance(subject_zones, list) or not subject_zones:
        errors.append(f"{path}.subject_protection_zones: enabled canvas requires at least one zone")
        subject_zones = []
    subject_ids: list[str] = []
    for index, zone in enumerate(subject_zones):
        zpath = f"{path}.subject_protection_zones[{index}]"
        require_keys(zone, {"zone_id", "role", "protection", "reason"}, zpath, errors)
        if not isinstance(zone, dict):
            continue
        subject_ids.append(zone.get("zone_id"))
        if any(not nonempty(zone.get(key)) for key in ("zone_id", "role", "reason")):
            errors.append(f"{zpath}: zone_id, role and reason must be non-empty")
        if zone.get("protection") not in ZONE_PROTECTION:
            errors.append(f"{zpath}.protection: invalid value")
    if len(subject_ids) != len(set(subject_ids)):
        errors.append(f"{path}.subject_protection_zones: zone_id values must be unique")

    placement_zones = canvas.get("candidate_placement_zones")
    if not isinstance(placement_zones, list) or not placement_zones:
        errors.append(f"{path}.candidate_placement_zones: enabled canvas requires candidate zones")
        placement_zones = []
    placement_ids: list[str] = []
    supported: list[str] = []
    usable_zone = False
    for index, zone in enumerate(placement_zones):
        zpath = f"{path}.candidate_placement_zones[{index}]"
        require_keys(zone, {"zone_id", "suitability", "anchor_edges", "supports_copy_ids", "reason"}, zpath, errors)
        if not isinstance(zone, dict):
            continue
        placement_ids.append(zone.get("zone_id"))
        if not nonempty(zone.get("zone_id")) or not nonempty(zone.get("reason")):
            errors.append(f"{zpath}: zone_id and reason must be non-empty")
        suitability = zone.get("suitability")
        if suitability not in PLACEMENT_SUITABILITY:
            errors.append(f"{zpath}.suitability: invalid value")
        anchors = zone.get("anchor_edges")
        if not isinstance(anchors, list) or not anchors or len(anchors) != len(set(anchors)) or any(value not in ANCHOR_EDGES for value in anchors):
            errors.append(f"{zpath}.anchor_edges: must be a unique non-empty anchor array")
        copy_ids = zone.get("supports_copy_ids")
        if not isinstance(copy_ids, list) or len(copy_ids) != len(set(copy_ids)) or any(value not in expected_copy_ids for value in copy_ids):
            errors.append(f"{zpath}.supports_copy_ids: must reference visible copy ids")
            copy_ids = []
        if suitability in {"primary", "secondary"} and copy_ids:
            supported.extend(copy_ids)
            usable_zone = True
    if len(placement_ids) != len(set(placement_ids)) or set(subject_ids) & set(placement_ids):
        errors.append(f"{path}: all subject and placement zone_id values must be unique")
    if not usable_zone:
        errors.append(f"{path}.candidate_placement_zones: at least one usable zone must support copy")
    if not set(expected_copy_ids).issubset(set(supported)):
        errors.append(f"{path}.candidate_placement_zones: usable analysis must cover every visible copy_id")


def validate_asset_strategy(
    strategy: Any,
    icon_scan: Any,
    path: str,
    errors: list[str],
) -> None:
    keys = {
        "template_mode", "icon_policy", "required_roles", "candidate_asset_ids",
        "selected_asset_ids", "selection_rationale", "family_consistency",
        "license_records", "never_copy",
    }
    require_keys(strategy, keys, path, errors)
    if not isinstance(strategy, dict):
        return
    if strategy.get("template_mode") not in TEMPLATE_MODES:
        errors.append(f"{path}.template_mode: must be derive-not-clone")
    if strategy.get("icon_policy") not in ICON_POLICIES:
        errors.append(f"{path}.icon_policy: invalid value")
    for key in ("required_roles", "candidate_asset_ids", "selected_asset_ids", "never_copy"):
        values = strategy.get(key)
        if not unique_string_array(values):
            errors.append(f"{path}.{key}: must be a unique string array")
    if not strategy.get("never_copy"):
        errors.append(f"{path}.never_copy: must state at least one imitation boundary")
    candidates = strategy.get("candidate_asset_ids") if isinstance(strategy.get("candidate_asset_ids"), list) else []
    selected = strategy.get("selected_asset_ids") if isinstance(strategy.get("selected_asset_ids"), list) else []
    if not set(selected).issubset(set(candidates)):
        errors.append(f"{path}.selected_asset_ids: must be a subset of candidate_asset_ids")
    if not nonempty(strategy.get("selection_rationale")):
        errors.append(f"{path}.selection_rationale: must explain selection or non-selection")
    family = strategy.get("family_consistency")
    if family not in FAMILY_CONSISTENCY:
        errors.append(f"{path}.family_consistency: invalid value")
    if selected and family == "not-applicable":
        errors.append(f"{path}.family_consistency: selected assets require a family decision")
    if isinstance(icon_scan, list) and icon_scan and strategy.get("icon_policy") != "semantic-only":
        errors.append(f"{path}.icon_policy: icon candidates require semantic-only")
    records = strategy.get("license_records")
    if not isinstance(records, list):
        errors.append(f"{path}.license_records: must be an array")
        records = []
    record_ids: list[str] = []
    for index, record in enumerate(records):
        rpath = f"{path}.license_records[{index}]"
        require_keys(record, {"asset_id", "source", "license", "attribution_required"}, rpath, errors)
        if not isinstance(record, dict):
            continue
        record_ids.append(record.get("asset_id"))
        if any(not nonempty(record.get(key)) for key in ("asset_id", "source", "license")):
            errors.append(f"{rpath}: asset_id, source and license must be non-empty")
        if not isinstance(record.get("attribution_required"), bool):
            errors.append(f"{rpath}.attribution_required: must be boolean")
    if len(record_ids) != len(set(record_ids)) or set(record_ids) != set(selected):
        errors.append(f"{path}.license_records: must cover every selected asset exactly once")


def communication_contract(package: dict[str, Any]) -> dict[str, Any]:
    return package["brief"]["preflight"]


def validate_semantic_layout_tree(
    tree: Any,
    expected_copy_ids: list[str],
    region_ids: set[str],
    path: str,
    errors: list[str],
) -> None:
    require_keys(tree, {"tree_id", "mode", "root_node_id", "nodes", "relations", "checks"}, path, errors)
    if not isinstance(tree, dict):
        return
    if not nonempty(tree.get("tree_id")):
        errors.append(f"{path}.tree_id: must be non-empty")
    if tree.get("mode") not in TREE_MODES:
        errors.append(f"{path}.mode: invalid value")
    nodes = tree.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        errors.append(f"{path}.nodes: must be a non-empty array")
        nodes = []
    node_ids: list[str] = []
    parents: dict[str, str | None] = {}
    covered_copy_ids: list[str] = []
    for index, node in enumerate(nodes):
        npath = f"{path}.nodes[{index}]"
        require_keys(node, {"node_id", "parent_node_id", "node_type", "semantic_role", "region_id", "copy_ids", "shape_family", "reading_order"}, npath, errors)
        if not isinstance(node, dict):
            continue
        node_id = node.get("node_id")
        if not nonempty(node_id):
            errors.append(f"{npath}.node_id: must be non-empty")
            continue
        node_ids.append(node_id)
        parents[node_id] = node.get("parent_node_id")
        if node.get("node_type") not in TREE_NODE_TYPES:
            errors.append(f"{npath}.node_type: invalid value")
        if not nonempty(node.get("semantic_role")):
            errors.append(f"{npath}.semantic_role: must be non-empty")
        region_id = node.get("region_id")
        if region_id is not None and region_id not in region_ids:
            errors.append(f"{npath}.region_id: must be null or reference area_plan")
        copy_ids = node.get("copy_ids")
        if not isinstance(copy_ids, list) or any(copy_id not in expected_copy_ids for copy_id in copy_ids or []):
            errors.append(f"{npath}.copy_ids: must reference visible copy ids")
        else:
            covered_copy_ids.extend(copy_ids)
        if node.get("shape_family") not in TREE_SHAPE_FAMILIES:
            errors.append(f"{npath}.shape_family: invalid value")
        if not isinstance(node.get("reading_order"), int) or node.get("reading_order", -1) < 0:
            errors.append(f"{npath}.reading_order: must be a non-negative integer")
    if len(node_ids) != len(set(node_ids)):
        errors.append(f"{path}.nodes: node_id values must be unique")
    roots = [node_id for node_id, parent in parents.items() if parent is None]
    if roots != [tree.get("root_node_id")]:
        errors.append(f"{path}.root_node_id: must name the single root node")
    for node_id, parent in parents.items():
        if parent is not None and parent not in parents:
            errors.append(f"{path}.nodes[{node_id}].parent_node_id: must reference another node")
        seen: set[str] = set()
        cursor: str | None = node_id
        while cursor is not None and cursor in parents:
            if cursor in seen:
                errors.append(f"{path}.nodes: hierarchy must be acyclic")
                break
            seen.add(cursor)
            cursor = parents[cursor]
    if covered_copy_ids != expected_copy_ids or len(covered_copy_ids) != len(set(covered_copy_ids)):
        errors.append(f"{path}.nodes.copy_ids: must cover every copy_id exactly once in Copy order")
    if tree.get("mode") == "flat" and any(
        parent not in {None, tree.get("root_node_id")} for parent in parents.values()
    ):
        errors.append(f"{path}.mode: flat trees may only contain root and direct children")
    relations = tree.get("relations")
    if not isinstance(relations, list):
        errors.append(f"{path}.relations: must be an array")
        relations = []
    relation_ids: list[str] = []
    for index, relation in enumerate(relations):
        rpath = f"{path}.relations[{index}]"
        require_keys(relation, {"relation_id", "source_node_id", "target_node_id", "type", "directed"}, rpath, errors)
        if not isinstance(relation, dict):
            continue
        relation_ids.append(relation.get("relation_id"))
        if not nonempty(relation.get("relation_id")):
            errors.append(f"{rpath}.relation_id: must be non-empty")
        if relation.get("source_node_id") not in parents or relation.get("target_node_id") not in parents:
            errors.append(f"{rpath}: relation endpoints must reference tree nodes")
        relation_type = relation.get("type")
        if relation_type not in TREE_RELATIONS:
            errors.append(f"{rpath}.type: invalid value")
        if not isinstance(relation.get("directed"), bool):
            errors.append(f"{rpath}.directed: must be boolean")
        elif relation_type in DIRECTED_TREE_RELATIONS and relation.get("directed") is not True:
            errors.append(f"{rpath}.directed: {relation_type} must be directed")
        elif relation_type in UNDIRECTED_TREE_RELATIONS and relation.get("directed") is not False:
            errors.append(f"{rpath}.directed: {relation_type} must be undirected")
    if len(relation_ids) != len(set(relation_ids)):
        errors.append(f"{path}.relations: relation_id values must be unique")
    checks = tree.get("checks")
    require_keys(checks, TREE_CHECKS, f"{path}.checks", errors)
    if isinstance(checks, dict):
        if set(checks) != TREE_CHECKS:
            errors.append(f"{path}.checks: must contain exactly {sorted(TREE_CHECKS)}")
        for key in TREE_CHECKS:
            if checks.get(key) is not True:
                errors.append(f"{path}.checks.{key}: must be true")


def validate_plan(
    package: Any,
    plan: Any,
    policy: ValidationPolicy | None = None,
) -> list[str]:
    policy = policy or load_policy()
    errors = validate_package(package, "copy-approved")
    require_keys(
        plan,
        {"contract_version", "status", "package_contract_version", "package_id", "package_version", "resource_inventory_lock", "index_evidence", "communication_contract", "art_direction", "reference_budget", "ab_review", "decision_log", "typography_contract", "deck_rhythm", "slides"},
        "$plan",
        errors,
    )
    if not isinstance(package, dict) or not isinstance(plan, dict):
        return errors
    if plan.get("contract_version") != CONTRACT_VERSION:
        errors.append(f"plan.contract_version: expected {CONTRACT_VERSION}")
    if plan.get("status") != "art-direction-approved":
        errors.append("plan.status: expected art-direction-approved")
    if plan.get("package_contract_version") != package.get("contract_version"):
        errors.append("plan.package_contract_version: must equal package contract_version")
    if plan.get("package_id") != package.get("package_id") or plan.get("package_version") != package.get("version"):
        errors.append("plan package identity/version must match package")
    if plan.get("resource_inventory_lock") != resource_inventory_signature(package.get("resource_inventory")):
        errors.append("plan.resource_inventory_lock: must preserve the pre-Logic resource inventory signature")
    if plan.get("communication_contract") != communication_contract(package):
        errors.append("plan.communication_contract: must exactly inherit brief.preflight")
    validate_index_evidence(
        plan.get("index_evidence"),
        ["logic", "copy", "art-direction"],
        "plan.index_evidence",
        errors,
    )
    if index_lock_signature(plan.get("index_evidence")) != index_lock_signature(package.get("index_evidence")):
        errors.append("plan.index_evidence: must preserve the package Provider lock and owner materialization")
    scan_post_render(plan, "$plan", errors)

    art_direction = plan.get("art_direction")
    require_keys(
        art_direction,
        {"visual_thesis", "material_route", "first_impression", "composition_principles", "forbidden_defaults", "silhouette_sequence", "density_sequence", "dominant_media_sequence", "motif_sequence", "brand_constraints_repeated", "approval"},
        "plan.art_direction",
        errors,
    )
    if isinstance(art_direction, dict):
        for key in ("visual_thesis", "material_route", "first_impression"):
            if not nonempty(art_direction.get(key)):
                errors.append(f"plan.art_direction.{key}: must be non-empty")
        for key in ("composition_principles", "forbidden_defaults", "silhouette_sequence", "density_sequence", "dominant_media_sequence", "motif_sequence", "brand_constraints_repeated"):
            if not isinstance(art_direction.get(key), list) or not art_direction.get(key):
                errors.append(f"plan.art_direction.{key}: must be a non-empty array")
        approval = art_direction.get("approval")
        require_keys(approval, {"status", "approved_by", "notes"}, "plan.art_direction.approval", errors)
        if isinstance(approval, dict):
            if approval.get("status") != "approved":
                errors.append("plan.art_direction.approval.status: expected approved")
            if not nonempty(approval.get("approved_by")):
                errors.append("plan.art_direction.approval.approved_by: must be non-empty")

    reference_budget = plan.get("reference_budget")
    require_keys(
        reference_budget,
        {"max_total_loaded", "max_per_archetype", "max_sequences_loaded", "loaded_record_ids", "loaded_sequence_ids", "query_log", "sequence_query_log", "budget_respected"},
        "plan.reference_budget",
        errors,
    )
    loaded_record_ids: set[str] = set()
    loaded_sequence_ids: set[str] = set()
    art_receipt_ids, art_selected_record_ids = stage_receipt_selection(plan.get("index_evidence"), "art-direction")
    if isinstance(reference_budget, dict):
        max_total = reference_budget.get("max_total_loaded")
        max_archetype = reference_budget.get("max_per_archetype")
        max_sequences = reference_budget.get("max_sequences_loaded")
        loaded = reference_budget.get("loaded_record_ids")
        if not isinstance(max_total, int) or not 1 <= max_total <= 24:
            errors.append("plan.reference_budget.max_total_loaded: must be 1..24")
        if not isinstance(max_archetype, int) or not 1 <= max_archetype <= 8:
            errors.append("plan.reference_budget.max_per_archetype: must be 1..8")
        if not isinstance(max_sequences, int) or not 1 <= max_sequences <= 4:
            errors.append("plan.reference_budget.max_sequences_loaded: must be 1..4")
        if not isinstance(loaded, list) or not loaded or len(loaded) != len(set(loaded)) or any(not nonempty(x) for x in loaded):
            errors.append("plan.reference_budget.loaded_record_ids: must be a non-empty unique string array")
        else:
            loaded_record_ids = set(loaded)
            if isinstance(max_total, int) and len(loaded) > max_total:
                errors.append("plan.reference_budget.loaded_record_ids: exceeds max_total_loaded")
            if not loaded_record_ids.issubset(art_selected_record_ids):
                errors.append("plan.reference_budget.loaded_record_ids: every loaded record must be selected by an Art Direction retrieval receipt")
        query_log = reference_budget.get("query_log")
        if not isinstance(query_log, list) or not query_log:
            errors.append("plan.reference_budget.query_log: must be a non-empty array")
        else:
            logged_records: set[str] = set()
            for query_index, query in enumerate(query_log):
                qpath = f"plan.reference_budget.query_log[{query_index}]"
                require_keys(query, {"request_id", "receipt_id", "query", "selected_record_ids", "adoption_outcome"}, qpath, errors)
                if not isinstance(query, dict):
                    continue
                for key in ("request_id", "receipt_id", "query", "adoption_outcome"):
                    if not nonempty(query.get(key)):
                        errors.append(f"{qpath}.{key}: must be non-empty")
                if query.get("receipt_id") not in art_receipt_ids:
                    errors.append(f"{qpath}.receipt_id: must bind an Art Direction retrieval receipt")
                selected_ids = query.get("selected_record_ids")
                if not isinstance(selected_ids, list) or not selected_ids or len(selected_ids) != len(set(selected_ids)):
                    errors.append(f"{qpath}.selected_record_ids: must be a non-empty unique array")
                elif any(record_id not in art_selected_record_ids for record_id in selected_ids):
                    errors.append(f"{qpath}.selected_record_ids: must come from the bound retrieval evidence")
                else:
                    logged_records.update(selected_ids)
            if loaded_record_ids and not loaded_record_ids.issubset(logged_records):
                errors.append("plan.reference_budget.query_log: must explain adoption of every loaded_record_id")
        loaded_sequences = reference_budget.get("loaded_sequence_ids")
        if not isinstance(loaded_sequences, list) or len(loaded_sequences) != len(set(loaded_sequences)) or any(not nonempty(x) for x in loaded_sequences):
            errors.append("plan.reference_budget.loaded_sequence_ids: must be a unique string array")
        else:
            loaded_sequence_ids = set(loaded_sequences)
            if isinstance(max_sequences, int) and len(loaded_sequences) > max_sequences:
                errors.append("plan.reference_budget.loaded_sequence_ids: exceeds max_sequences_loaded")
        if not isinstance(reference_budget.get("sequence_query_log"), list):
            errors.append("plan.reference_budget.sequence_query_log: must be an array")
        if reference_budget.get("budget_respected") is not True:
            errors.append("plan.reference_budget.budget_respected: must be true")

    root_ab = plan.get("ab_review")
    require_keys(root_ab, {"required_slide_ids", "completed_slide_ids", "selection_rule", "completed"}, "plan.ab_review", errors)
    required_ab_ids: set[str] = set()
    if isinstance(root_ab, dict):
        required_ids = root_ab.get("required_slide_ids")
        completed_ids = root_ab.get("completed_slide_ids")
        if not isinstance(required_ids, list) or len(required_ids) != len(set(required_ids)):
            errors.append("plan.ab_review.required_slide_ids: must be a unique array")
        else:
            required_ab_ids = set(required_ids)
        if not isinstance(completed_ids, list) or len(completed_ids) != len(set(completed_ids)):
            errors.append("plan.ab_review.completed_slide_ids: must be a unique array")
        elif set(completed_ids) != required_ab_ids:
            errors.append("plan.ab_review.completed_slide_ids: must equal required_slide_ids")
        if not nonempty(root_ab.get("selection_rule")):
            errors.append("plan.ab_review.selection_rule: must be non-empty")
        if root_ab.get("completed") is not True:
            errors.append("plan.ab_review.completed: must be true")

    decision_log = plan.get("decision_log")
    require_keys(decision_log, {"conflicts", "deviations", "unresolved"}, "plan.decision_log", errors)
    if isinstance(decision_log, dict):
        for key in ("conflicts", "deviations", "unresolved"):
            if not isinstance(decision_log.get(key), list):
                errors.append(f"plan.decision_log.{key}: must be an array")
        if decision_log.get("unresolved"):
            errors.append("plan.decision_log.unresolved: approved plans cannot contain unresolved conflicts")
        for index, conflict in enumerate(decision_log.get("conflicts", [])):
            cpath = f"plan.decision_log.conflicts[{index}]"
            require_keys(conflict, {"conflict_id", "layers", "rules", "owner", "resolution", "backflow", "approval_basis"}, cpath, errors)
            if isinstance(conflict, dict):
                if not isinstance(conflict.get("layers"), list) or len(conflict.get("layers", [])) < 2:
                    errors.append(f"{cpath}.layers: must name at least two layers")
                if not isinstance(conflict.get("rules"), list) or len(conflict.get("rules", [])) < 2:
                    errors.append(f"{cpath}.rules: must name the conflicting rules")
                for key in ("conflict_id", "owner", "resolution", "approval_basis"):
                    if not nonempty(conflict.get(key)):
                        errors.append(f"{cpath}.{key}: must be non-empty")
                if not isinstance(conflict.get("backflow"), bool):
                    errors.append(f"{cpath}.backflow: must be boolean")

    typography = plan.get("typography_contract")
    require_keys(
        typography,
        {"body_min_pt", "audience_detail_min_pt", "chart_text_min_pt", "even_point_sizes_required", "minimum_exception_policy", "allowed_size_tokens", "max_size_variants_per_logic_level", "fractional_point_sizes_allowed", "grid_system", "bottom_safe_area_reserved", "whitespace_review"},
        "plan.typography_contract",
        errors,
    )
    allowed_tokens: set[str] = set()
    if isinstance(typography, dict):
        if not isinstance(typography.get("body_min_pt"), (int, float)) or typography.get("body_min_pt", 0) < policy.body_minimum_pt:
            errors.append(f"plan.typography_contract.body_min_pt: must be at least {policy.body_minimum_pt:g}")
        minimums = {
            "audience_detail_min_pt": policy.audience_minimum_pt,
            "chart_text_min_pt": policy.chart_minimum_pt,
        }
        for key, configured_minimum in minimums.items():
            value = typography.get(key)
            if not isinstance(value, (int, float)) or value < configured_minimum or not policy.size_conforms(value):
                errors.append(
                    f"plan.typography_contract.{key}: must meet configured minimum {configured_minimum:g}pt and size-token policy"
                )
        if typography.get("even_point_sizes_required") is not policy.prefer_even_point_sizes:
            errors.append("plan.typography_contract.even_point_sizes_required: must match central configuration")
        if typography.get("minimum_exception_policy") != policy.minimum_exception_policy:
            errors.append("plan.typography_contract.minimum_exception_policy: must match central configuration")
        tokens = typography.get("allowed_size_tokens")
        if not isinstance(tokens, list) or not tokens or any(not nonempty(token) for token in tokens):
            errors.append("plan.typography_contract.allowed_size_tokens: must be a non-empty string array")
        else:
            allowed_tokens = set(tokens)
        variants = typography.get("max_size_variants_per_logic_level")
        if not isinstance(variants, int) or not 1 <= variants <= 3:
            errors.append("plan.typography_contract.max_size_variants_per_logic_level: must be 1..3")
        if typography.get("fractional_point_sizes_allowed") is not policy.allow_fractional_point_sizes:
            errors.append("plan.typography_contract.fractional_point_sizes_allowed: must match central configuration")
        expected_grid = f"{policy.column_count}-column"
        if typography.get("grid_system") != expected_grid:
            errors.append(f"plan.typography_contract.grid_system: must be {expected_grid}")
        for key in ("bottom_safe_area_reserved", "whitespace_review"):
            if typography.get(key) is not True:
                errors.append(f"plan.typography_contract.{key}: must be true")

    rhythm = plan.get("deck_rhythm")
    require_keys(
        rhythm,
        {"hero_slide_ids", "section_pulses", "max_consecutive_same_silhouette", "max_consecutive_same_density", "max_bottom_conclusion_band_share", "minimum_dominant_media_for_10_plus_body_slides", "exceptions", "series_groups", "motif_sequence", "motif_contracts", "semantic_whitespace_slide_ids", "purposeful_repetition_review", "review"},
        "plan.deck_rhythm",
        errors,
    )
    if isinstance(rhythm, dict):
        for key in ("hero_slide_ids", "section_pulses", "exceptions", "series_groups", "motif_sequence", "motif_contracts", "semantic_whitespace_slide_ids"):
            if not isinstance(rhythm.get(key), list):
                errors.append(f"plan.deck_rhythm.{key}: must be an array")
        for key in ("max_consecutive_same_silhouette", "max_consecutive_same_density"):
            value = rhythm.get(key)
            if not isinstance(value, int) or not 1 <= value <= 3:
                errors.append(f"plan.deck_rhythm.{key}: must be an integer from 1 to 3")
        band_share = rhythm.get("max_bottom_conclusion_band_share")
        if not isinstance(band_share, (int, float)) or not 0 <= band_share <= 0.35:
            errors.append("plan.deck_rhythm.max_bottom_conclusion_band_share: must be between 0 and 0.35")
        media_minimum = rhythm.get("minimum_dominant_media_for_10_plus_body_slides")
        if not isinstance(media_minimum, int) or not 3 <= media_minimum <= len(DOMINANT_MEDIA):
            errors.append("plan.deck_rhythm.minimum_dominant_media_for_10_plus_body_slides: must require at least 3 media")
        repetition_review = rhythm.get("purposeful_repetition_review")
        repetition_keys = {
            "purposeful_series_preserved", "nonseries_repetition_reviewed",
            "motif_breaks_defined", "semantic_whitespace_reviewed",
        }
        require_keys(repetition_review, repetition_keys, "plan.deck_rhythm.purposeful_repetition_review", errors)
        if isinstance(repetition_review, dict):
            for key in repetition_keys:
                if repetition_review.get(key) is not True:
                    errors.append(f"plan.deck_rhythm.purposeful_repetition_review.{key}: must be true")
        if not isinstance(rhythm.get("review"), dict) or rhythm.get("review", {}).get("material_type_fit") is not True:
            errors.append("plan.deck_rhythm.review.material_type_fit: must be true")

    logic_slides = package.get("logic_layer", {}).get("slides", [])
    copy_slides = package.get("copy_layer", {}).get("slides", [])
    plan_slides = plan.get("slides")
    if not isinstance(plan_slides, list):
        errors.append("plan.slides: must be an array")
        return errors
    expected_order = [slide.get("slide_id") for slide in logic_slides]
    if [slide.get("slide_id") for slide in plan_slides if isinstance(slide, dict)] != expected_order:
        errors.append("plan.slides: order must exactly match package")

    global_targets: set[str] = set()
    for index, (logic_slide, copy_slide, slide_plan) in enumerate(zip(logic_slides, copy_slides, plan_slides)):
        validate_slide_plan(logic_slide, copy_slide, slide_plan, f"plan.slides[{index}]", allowed_tokens, global_targets, loaded_record_ids, loaded_sequence_ids, required_ab_ids, policy, errors)

    if isinstance(art_direction, dict):
        sequence_checks = {
            "silhouette_sequence": [slide.get("silhouette_family") for slide in plan_slides],
            "density_sequence": [slide.get("density_class") for slide in plan_slides],
            "dominant_media_sequence": [slide.get("dominant_medium") for slide in plan_slides],
            "motif_sequence": [slide.get("motif_id") for slide in plan_slides],
        }
        for key, expected in sequence_checks.items():
            if art_direction.get(key) != expected:
                errors.append(f"plan.art_direction.{key}: must exactly match slide order")
    if isinstance(rhythm, dict):
        motif_sequence = [slide.get("motif_id") for slide in plan_slides]
        if rhythm.get("motif_sequence") != motif_sequence:
            errors.append("plan.deck_rhythm.motif_sequence: must exactly match slide motif ids")
        motif_contracts = rhythm.get("motif_contracts")
        motif_ids = {value for value in motif_sequence if value is not None}
        if isinstance(motif_contracts, list):
            contract_ids = [item.get("motif_id") for item in motif_contracts if isinstance(item, dict)]
            if len(contract_ids) != len(set(contract_ids)) or set(contract_ids) != motif_ids:
                errors.append("plan.deck_rhythm.motif_contracts: must cover every non-null motif once")
            for index, item in enumerate(motif_contracts):
                mpath = f"plan.deck_rhythm.motif_contracts[{index}]"
                require_keys(item, {"motif_id", "purpose", "establish_slide_id", "repeat_slide_ids", "variation_rule", "break_slide_id", "break_reason"}, mpath, errors)
                if not isinstance(item, dict):
                    continue
                motif_id = item.get("motif_id")
                uses = [plan_slides[pos].get("slide_id") for pos, value in enumerate(motif_sequence) if value == motif_id]
                if not uses or item.get("establish_slide_id") != uses[0]:
                    errors.append(f"{mpath}.establish_slide_id: must be the first motif occurrence")
                if item.get("repeat_slide_ids") != uses[1:]:
                    errors.append(f"{mpath}.repeat_slide_ids: must list subsequent motif occurrences")
                break_id = item.get("break_slide_id")
                if break_id is not None and break_id not in expected_order:
                    errors.append(f"{mpath}.break_slide_id: must be null or a deck slide id")
                for key in ("purpose", "variation_rule", "break_reason"):
                    if not nonempty(item.get(key)):
                        errors.append(f"{mpath}.{key}: must be non-empty")
        whitespace_ids = [
            slide.get("slide_id") for slide in plan_slides
            if isinstance(slide.get("semantic_whitespace"), dict)
            and slide["semantic_whitespace"].get("mode") != "none"
        ]
        if rhythm.get("semantic_whitespace_slide_ids") != whitespace_ids:
            errors.append("plan.deck_rhythm.semantic_whitespace_slide_ids: must match slide plans")
        body_pairs = [
            (logic_slide, plan_slide)
            for logic_slide, plan_slide in zip(logic_slides, plan_slides)
            if logic_slide.get("narrative_role") not in {"cover", "closing"}
        ]
        nonseries_pairs = [
            (logic_slide, plan_slide)
            for logic_slide, plan_slide in body_pairs
            if logic_slide.get("series_id") is None
        ]

        def enforce_run(field: str, maximum_key: str) -> None:
            maximum = rhythm.get(maximum_key)
            if not isinstance(maximum, int):
                return
            run_value: Any = object()
            run_ids: list[str] = []
            for logic_slide, plan_slide in body_pairs:
                if logic_slide.get("series_id") is not None:
                    run_value = object()
                    run_ids = []
                    continue
                value = plan_slide.get(field)
                if value == run_value:
                    run_ids.append(str(plan_slide.get("slide_id")))
                else:
                    run_value = value
                    run_ids = [str(plan_slide.get("slide_id"))]
                if len(run_ids) > maximum:
                    errors.append(
                        f"plan.deck_rhythm.{maximum_key}: non-series {field} run exceeds {maximum} on {run_ids}"
                    )
                    break

        enforce_run("silhouette_family", "max_consecutive_same_silhouette")
        enforce_run("density_class", "max_consecutive_same_density")

        first_visual_reuse: dict[str, list[str]] = {}
        structure_reuse: dict[str, list[str]] = {}
        for _, plan_slide in nonseries_pairs:
            slide_id = str(plan_slide.get("slide_id"))
            first_visual = str(plan_slide.get("design_intent", {}).get("first_visual", ""))
            normalized_visual = normalize_first_visual(first_visual)
            if is_generic_first_visual(first_visual):
                errors.append(
                    f"plan.slides[{slide_id}].design_intent.first_visual: must name the content-specific visual, not a generic placeholder"
                )
            if normalized_visual:
                first_visual_reuse.setdefault(normalized_visual, []).append(slide_id)
            signature = str(plan_slide.get("structure_signature", "")).strip().casefold()
            if signature:
                structure_reuse.setdefault(signature, []).append(slide_id)
        for slide_ids in first_visual_reuse.values():
            if len(slide_ids) >= 3:
                errors.append(
                    f"plan.deck_rhythm: one first visual is reused across non-series slides {slide_ids}"
                )
        for slide_ids in structure_reuse.values():
            if len(slide_ids) >= 3:
                errors.append(
                    f"plan.deck_rhythm: one structure_signature is reused across non-series slides {slide_ids}"
                )
        if len(body_pairs) >= 10 and isinstance(rhythm.get("minimum_dominant_media_for_10_plus_body_slides"), int):
            media_count = len({plan_slide.get("dominant_medium") for _, plan_slide in body_pairs})
            if media_count < rhythm["minimum_dominant_media_for_10_plus_body_slides"]:
                errors.append(
                    "plan.deck_rhythm.minimum_dominant_media_for_10_plus_body_slides: actual dominant-media diversity is too low"
                )
        if body_pairs and isinstance(rhythm.get("max_bottom_conclusion_band_share"), (int, float)):
            actual_share = sum(bool(plan_slide.get("uses_bottom_conclusion_band")) for _, plan_slide in body_pairs) / len(body_pairs)
            if actual_share > rhythm["max_bottom_conclusion_band_share"]:
                errors.append(
                    f"plan.deck_rhythm.max_bottom_conclusion_band_share: actual share {actual_share:.3f} exceeds the plan limit"
                )
        logic_series = (package.get("logic_layer") or {}).get("cross_slide_contract", {}).get("series", [])
        expected_series = []
        plan_by_id = {slide.get("slide_id"): slide for slide in plan_slides}
        for series in logic_series:
            if not isinstance(series, dict):
                continue
            member_ids = series.get("slide_ids", [])
            change_by_id = {
                item.get("slide_id"): item.get("new_information")
                for item in series.get("change_by_slide", []) if isinstance(item, dict)
            }
            for slide_id in member_ids:
                repeated = (plan_by_id.get(slide_id, {}).get("series_visual_contract") or {}).get("logic_change_repeated")
                if repeated != change_by_id.get(slide_id):
                    errors.append(f"plan.slides[{slide_id}].series_visual_contract.logic_change_repeated: must repeat Logic new_information")
            expected_series.append({
                "series_id": series.get("series_id"),
                "slide_ids": member_ids,
                "purpose": series.get("purpose"),
                "behaviors": [
                    (plan_by_id.get(slide_id, {}).get("series_visual_contract") or {}).get("behavior")
                    for slide_id in member_ids
                ],
            })
        if rhythm.get("series_groups") != expected_series:
            errors.append("plan.deck_rhythm.series_groups: must derive exactly from Logic series and slide behaviors")
    return errors


def validate_slide_plan(
    logic_slide: dict[str, Any],
    copy_slide: dict[str, Any],
    plan: Any,
    path: str,
    allowed_tokens: set[str],
    global_targets: set[str],
    loaded_record_ids: set[str],
    loaded_sequence_ids: set[str],
    required_ab_ids: set[str],
    policy: ValidationPolicy,
    errors: list[str],
) -> None:
    required = {
        "slide_id", "logic_statement", "page_message_tree_depth", "main_backbone", "local_relations",
        "visual_layers", "reading_sequence", "copy_unit_map", "visual_hierarchy", "atomicity_review",
        "content_load_class_repeated", "decision_weight_repeated", "series_visual_contract",
        "motif_id", "semantic_whitespace", "persistent_context_rail",
        "structure_signature", "silhouette_family", "dominant_medium", "density_class", "visual_anchor",
        "medium_execution_contract", "content_aware_canvas", "asset_strategy",
        "accent_coverage_band", "uses_bottom_conclusion_band", "rhythm_exception", "repetition_reason",
        "icon_scan", "image_plan", "connector_plan", "kpi_plan", "shape_semantics",
        "backflow_required", "backflow_reason", "anti_flatness_review",
        "design_intent", "area_plan", "semantic_layout_tree", "reference_selection", "reference_exception",
        "ab_review", "art_direction_lock", "handoff_status",
    }
    require_keys(plan, required, path, errors)
    if not isinstance(plan, dict):
        return
    if plan.get("slide_id") != logic_slide.get("slide_id"):
        errors.append(f"{path}.slide_id: mismatch")
    if plan.get("logic_statement") != logic_slide.get("logic_map", {}).get("statement"):
        errors.append(f"{path}.logic_statement: must be verbatim")
    tree_nodes = logic_slide.get("page_message_tree", {}).get("nodes", [])
    depth = max((node.get("level", 0) for node in tree_nodes), default=0)
    if plan.get("page_message_tree_depth") != depth:
        errors.append(f"{path}.page_message_tree_depth: expected {depth}")
    if plan.get("content_load_class_repeated") != logic_slide.get("content_load_class"):
        errors.append(f"{path}.content_load_class_repeated: must match Logic")
    if plan.get("decision_weight_repeated") != logic_slide.get("decision_weight"):
        errors.append(f"{path}.decision_weight_repeated: must match Logic")
    for key in ("main_backbone", "structure_signature", "silhouette_family", "density_class", "visual_anchor"):
        if not nonempty(plan.get(key)):
            errors.append(f"{path}.{key}: must be non-empty")
    local = plan.get("local_relations")
    if not isinstance(local, list) or len(local) > 3:
        errors.append(f"{path}.local_relations: must contain 0..3 items")
    if plan.get("dominant_medium") not in DOMINANT_MEDIA:
        errors.append(f"{path}.dominant_medium: invalid value")

    motif_id = plan.get("motif_id")
    if motif_id is not None and not nonempty(motif_id):
        errors.append(f"{path}.motif_id: must be null or non-empty")

    series_contract = plan.get("series_visual_contract")
    require_keys(
        series_contract,
        {"series_id", "behavior", "persistent_elements", "logic_change_repeated", "progressive_change", "allowed_variation", "sequence_reference_ids", "break_reason"},
        f"{path}.series_visual_contract",
        errors,
    )
    if isinstance(series_contract, dict):
        logic_series_id = logic_slide.get("series_id")
        if series_contract.get("series_id") != logic_series_id:
            errors.append(f"{path}.series_visual_contract.series_id: must match Logic")
        behavior = series_contract.get("behavior")
        if behavior not in SERIES_BEHAVIORS:
            errors.append(f"{path}.series_visual_contract.behavior: invalid value")
        role = logic_slide.get("series_role")
        if logic_series_id is None and behavior != "standalone":
            errors.append(f"{path}.series_visual_contract.behavior: non-series slides must be standalone")
        elif logic_series_id is not None and role == "break" and behavior != "series-break":
            errors.append(f"{path}.series_visual_contract.behavior: Logic break requires series-break")
        elif logic_series_id is not None and role != "break" and behavior not in {"locked-backbone", "controlled-variation"}:
            errors.append(f"{path}.series_visual_contract.behavior: series slides require locked-backbone or controlled-variation")
        persistent = series_contract.get("persistent_elements")
        if not isinstance(persistent, list) or (logic_series_id is not None and not persistent) or any(not nonempty(value) for value in persistent or []):
            errors.append(f"{path}.series_visual_contract.persistent_elements: invalid list")
        allowed = series_contract.get("allowed_variation")
        if not isinstance(allowed, list) or any(not nonempty(value) for value in allowed or []):
            errors.append(f"{path}.series_visual_contract.allowed_variation: invalid list")
        sequence_refs = series_contract.get("sequence_reference_ids")
        if not isinstance(sequence_refs, list) or any(value not in loaded_sequence_ids for value in sequence_refs or []):
            errors.append(f"{path}.series_visual_contract.sequence_reference_ids: must reference loaded sequence records")
        if logic_series_id is not None and not sequence_refs:
            errors.append(f"{path}.series_visual_contract.sequence_reference_ids: series slides require sequence references")
        if not nonempty(series_contract.get("progressive_change")):
            errors.append(f"{path}.series_visual_contract.progressive_change: must be non-empty")
        if not nonempty(series_contract.get("logic_change_repeated")):
            errors.append(f"{path}.series_visual_contract.logic_change_repeated: must be non-empty")
        elif logic_series_id is None and series_contract.get("logic_change_repeated") != "standalone":
            errors.append(f"{path}.series_visual_contract.logic_change_repeated: non-series slides must use standalone")
        if behavior == "series-break" and not nonempty(series_contract.get("break_reason")):
            errors.append(f"{path}.series_visual_contract.break_reason: required for series-break")

    whitespace = plan.get("semantic_whitespace")
    require_keys(
        whitespace,
        {"mode", "zones", "narrative_duty", "protected_from_filling"},
        f"{path}.semantic_whitespace",
        errors,
    )
    if isinstance(whitespace, dict):
        mode = whitespace.get("mode")
        if mode not in WHITESPACE_MODES:
            errors.append(f"{path}.semantic_whitespace.mode: invalid value")
        zones = whitespace.get("zones")
        if not isinstance(zones, list) or any(not nonempty(value) for value in zones or []):
            errors.append(f"{path}.semantic_whitespace.zones: must be a string array")
            zones = []
        if mode == "none":
            if zones or whitespace.get("protected_from_filling") is not False:
                errors.append(f"{path}.semantic_whitespace: none requires empty zones and protected=false")
        else:
            if not zones or whitespace.get("protected_from_filling") is not True:
                errors.append(f"{path}.semantic_whitespace: semantic whitespace requires zones and protected=true")
            if not nonempty(whitespace.get("narrative_duty")):
                errors.append(f"{path}.semantic_whitespace.narrative_duty: must be non-empty")

    rail = plan.get("persistent_context_rail")
    require_keys(
        rail,
        {"enabled", "purpose", "scope_slide_ids", "current_marker", "max_area_percent"},
        f"{path}.persistent_context_rail",
        errors,
    )
    if isinstance(rail, dict):
        enabled = rail.get("enabled")
        if not isinstance(enabled, bool):
            errors.append(f"{path}.persistent_context_rail.enabled: must be boolean")
        scope = rail.get("scope_slide_ids")
        if not isinstance(scope, list):
            errors.append(f"{path}.persistent_context_rail.scope_slide_ids: must be an array")
            scope = []
        area = rail.get("max_area_percent")
        if enabled:
            if not nonempty(rail.get("purpose")) or not nonempty(rail.get("current_marker")):
                errors.append(f"{path}.persistent_context_rail: enabled rail requires purpose and current_marker")
            if logic_slide.get("slide_id") not in scope:
                errors.append(f"{path}.persistent_context_rail.scope_slide_ids: must include this slide")
            if not isinstance(area, (int, float)) or not 1 <= area <= 8:
                errors.append(f"{path}.persistent_context_rail.max_area_percent: enabled rail requires 1..8")
        elif scope or area != 0:
            errors.append(f"{path}.persistent_context_rail: disabled rail requires empty scope and max_area_percent=0")

    design_intent = plan.get("design_intent")
    require_keys(
        design_intent,
        {"communication_job", "first_impression", "first_visual", "attention_order", "why_this_composition", "forbidden_fallbacks"},
        f"{path}.design_intent",
        errors,
    )
    if isinstance(design_intent, dict):
        for key in ("communication_job", "first_impression", "first_visual", "why_this_composition"):
            if not nonempty(design_intent.get(key)):
                errors.append(f"{path}.design_intent.{key}: must be non-empty")
        if not isinstance(design_intent.get("attention_order"), list) or not design_intent.get("attention_order"):
            errors.append(f"{path}.design_intent.attention_order: must be a non-empty array")
        if not isinstance(design_intent.get("forbidden_fallbacks"), list) or not design_intent.get("forbidden_fallbacks"):
            errors.append(f"{path}.design_intent.forbidden_fallbacks: must be a non-empty array")

    medium = plan.get("medium_execution_contract")
    require_keys(
        medium,
        {"structure_type", "mapping_mode", "required_object_types", "minimum_object_counts", "semantic_axes", "render_recognition_criteria", "approved_alternative", "data_chart_contract", "quantitative_execution_contract"},
        f"{path}.medium_execution_contract",
        errors,
    )
    approved_alternative: dict[str, Any] | None = None
    if isinstance(medium, dict):
        structure_type = medium.get("structure_type")
        mapping_mode = medium.get("mapping_mode")
        required_objects = medium.get("required_object_types")
        minimum_counts = medium.get("minimum_object_counts")
        axes = medium.get("semantic_axes")
        criteria = medium.get("render_recognition_criteria")
        alternative = medium.get("approved_alternative")
        data_chart = medium.get("data_chart_contract")
        quantitative = medium.get("quantitative_execution_contract")
        if structure_type not in STRUCTURE_TYPES:
            errors.append(f"{path}.medium_execution_contract.structure_type: invalid value")
        if mapping_mode not in MAPPING_MODES:
            errors.append(f"{path}.medium_execution_contract.mapping_mode: invalid value")
        if structure_type in COMPOSITE_STRUCTURES and mapping_mode == "independent-shapes":
            errors.append(f"{path}.medium_execution_contract.mapping_mode: {structure_type} requires a composite structure")
        if not isinstance(required_objects, list) or not required_objects or len(required_objects) != len(set(required_objects)) or any(value not in OBJECT_TYPES for value in required_objects):
            errors.append(f"{path}.medium_execution_contract.required_object_types: must be a unique non-empty object-type array")
            required_objects = []
        if not isinstance(minimum_counts, dict) or any(key not in OBJECT_TYPES for key in minimum_counts) or any(not isinstance(value, int) or value < 0 for value in minimum_counts.values()):
            errors.append(f"{path}.medium_execution_contract.minimum_object_counts: invalid object counts")
            minimum_counts = {}
        for object_type in required_objects:
            if minimum_counts.get(object_type, 0) < 1:
                errors.append(f"{path}.medium_execution_contract.minimum_object_counts.{object_type}: required objects need a minimum of at least 1")
        if not isinstance(axes, list) or not axes or any(not nonempty(value) for value in axes):
            errors.append(f"{path}.medium_execution_contract.semantic_axes: must be a non-empty string array")
            axes = []
        if structure_type in {"swimlane", "matrix"} and len(axes) < 2:
            errors.append(f"{path}.medium_execution_contract.semantic_axes: {structure_type} requires at least two axes")
        if not isinstance(criteria, list) or not criteria or any(not nonempty(value) for value in criteria):
            errors.append(f"{path}.medium_execution_contract.render_recognition_criteria: must be a non-empty string array")
        if alternative is not None:
            require_keys(alternative, {"from_object_type", "to_object_type", "reason", "approved_by"}, f"{path}.medium_execution_contract.approved_alternative", errors)
            if isinstance(alternative, dict):
                approved_alternative = alternative
                if alternative.get("from_object_type") not in OBJECT_TYPES or alternative.get("to_object_type") not in OBJECT_TYPES:
                    errors.append(f"{path}.medium_execution_contract.approved_alternative: invalid object type")
                if alternative.get("to_object_type") not in required_objects:
                    errors.append(f"{path}.medium_execution_contract.approved_alternative.to_object_type: must appear in required_object_types")
                for key in ("reason", "approved_by"):
                    if not nonempty(alternative.get(key)):
                        errors.append(f"{path}.medium_execution_contract.approved_alternative.{key}: must be non-empty")
        if plan.get("dominant_medium") == "table" and structure_type != "table":
            errors.append(f"{path}.medium_execution_contract.structure_type: table medium requires table structure")
        if plan.get("dominant_medium") == "data-chart" and structure_type != "data-chart":
            errors.append(f"{path}.medium_execution_contract.structure_type: data-chart medium requires data-chart structure")
        if plan.get("dominant_medium") == "table":
            table_alternative = approved_alternative and approved_alternative.get("from_object_type") == "native-table"
            if not table_alternative and "native-table" not in required_objects:
                errors.append(f"{path}.medium_execution_contract.required_object_types: table requires native-table or an approved alternative")
        if plan.get("dominant_medium") == "data-chart":
            chart_alternative = approved_alternative and approved_alternative.get("from_object_type") == "native-chart"
            if not chart_alternative and "native-chart" not in required_objects:
                errors.append(f"{path}.medium_execution_contract.required_object_types: data-chart requires native-chart or an approved alternative")
            require_keys(
                data_chart,
                {"chart_type", "audience_text_min_pt", "even_point_sizes_only", "direct_label_policy", "entity_label_field", "point_connection_policy", "semantic_lines", "label_collision_strategy", "unlabeled_point_exception"},
                f"{path}.medium_execution_contract.data_chart_contract",
                errors,
            )
            if isinstance(data_chart, dict):
                chart_type = data_chart.get("chart_type")
                if not nonempty(chart_type):
                    errors.append(f"{path}.medium_execution_contract.data_chart_contract.chart_type: must be non-empty")
                text_min = data_chart.get("audience_text_min_pt")
                if not isinstance(text_min, (int, float)) or text_min < policy.chart_minimum_pt or not policy.size_conforms(text_min):
                    errors.append(
                        f"{path}.medium_execution_contract.data_chart_contract.audience_text_min_pt: must meet configured chart minimum and size-token policy"
                    )
                if data_chart.get("even_point_sizes_only") is not policy.prefer_even_point_sizes:
                    errors.append(f"{path}.medium_execution_contract.data_chart_contract.even_point_sizes_only: must match central configuration")
                semantic_lines = data_chart.get("semantic_lines")
                if not isinstance(semantic_lines, list):
                    errors.append(f"{path}.medium_execution_contract.data_chart_contract.semantic_lines: must be an array")
                    semantic_lines = []
                for line_index, line in enumerate(semantic_lines):
                    lpath = f"{path}.medium_execution_contract.data_chart_contract.semantic_lines[{line_index}]"
                    require_keys(line, {"line_id", "meaning", "visible_label"}, lpath, errors)
                    if isinstance(line, dict) and any(not nonempty(line.get(key)) for key in ("line_id", "meaning", "visible_label")):
                        errors.append(f"{lpath}: line_id, meaning and visible_label must be non-empty")
                strategies = data_chart.get("label_collision_strategy")
                allowed_strategies = {"offset", "leader-lines", "expand-plot", "facet-or-split"}
                if not isinstance(strategies, list) or not strategies or any(value not in allowed_strategies for value in strategies):
                    errors.append(f"{path}.medium_execution_contract.data_chart_contract.label_collision_strategy: invalid strategy list")
                if chart_type == "scatter":
                    if data_chart.get("direct_label_policy") != "all-entities":
                        errors.append(f"{path}.medium_execution_contract.data_chart_contract.direct_label_policy: scatter requires all-entities")
                    if not nonempty(data_chart.get("entity_label_field")):
                        errors.append(f"{path}.medium_execution_contract.data_chart_contract.entity_label_field: scatter requires a label field")
                    connection_policy = data_chart.get("point_connection_policy")
                    if connection_policy not in {"markers-only", "semantic-lines-only"}:
                        errors.append(f"{path}.medium_execution_contract.data_chart_contract.point_connection_policy: invalid scatter policy")
                    if connection_policy == "markers-only" and semantic_lines:
                        errors.append(f"{path}.medium_execution_contract.data_chart_contract.semantic_lines: markers-only requires no semantic lines")
                    if connection_policy == "semantic-lines-only" and not semantic_lines:
                        errors.append(f"{path}.medium_execution_contract.data_chart_contract.semantic_lines: semantic-lines-only requires labeled lines")
                    if data_chart.get("unlabeled_point_exception") is not None:
                        errors.append(f"{path}.medium_execution_contract.data_chart_contract.unlabeled_point_exception: scatter requires null unless user-approved backflow is recorded")
                else:
                    if data_chart.get("direct_label_policy") not in {"key-values", "as-needed", "all-entities"}:
                        errors.append(f"{path}.medium_execution_contract.data_chart_contract.direct_label_policy: invalid policy")
                    if data_chart.get("point_connection_policy") not in {"not-applicable", "semantic-lines-only"}:
                        errors.append(f"{path}.medium_execution_contract.data_chart_contract.point_connection_policy: invalid policy")
        elif data_chart is not None:
            errors.append(f"{path}.medium_execution_contract.data_chart_contract: non-data-chart slides must use null")
        logic_data_ids = {
            item.get("data_id")
            for item in logic_slide.get("data", [])
            if isinstance(item, dict) and nonempty(item.get("data_id"))
        }
        require_keys(
            quantitative,
            {"data_ids", "encoding_mode", "comparison_task", "scale", "shape_encoded_exception"},
            f"{path}.medium_execution_contract.quantitative_execution_contract",
            errors,
        )
        if isinstance(quantitative, dict):
            qpath = f"{path}.medium_execution_contract.quantitative_execution_contract"
            encoded_ids = quantitative.get("data_ids")
            if not isinstance(encoded_ids, list) or len(encoded_ids) != len(set(encoded_ids)) or set(encoded_ids) != logic_data_ids:
                errors.append(f"{qpath}.data_ids: must cover every Logic data_id exactly once")
            encoding_mode = quantitative.get("encoding_mode")
            if encoding_mode not in QUANTITATIVE_ENCODINGS:
                errors.append(f"{qpath}.encoding_mode: invalid value")
            if not nonempty(quantitative.get("comparison_task")):
                errors.append(f"{qpath}.comparison_task: must be non-empty")
            scale = quantitative.get("scale")
            require_keys(scale, {"type", "baseline", "unit", "rationale"}, f"{qpath}.scale", errors)
            if isinstance(scale, dict):
                if scale.get("type") not in QUANTITATIVE_SCALES:
                    errors.append(f"{qpath}.scale.type: invalid value")
                if not nonempty(scale.get("rationale")):
                    errors.append(f"{qpath}.scale.rationale: must be non-empty")
                if scale.get("type") == "index" and not isinstance(scale.get("baseline"), (int, float)):
                    errors.append(f"{qpath}.scale.baseline: index treatment requires a numeric baseline")
            exception = quantitative.get("shape_encoded_exception")
            if logic_data_ids:
                if encoding_mode == "not-applicable":
                    errors.append(f"{qpath}.encoding_mode: data-bearing slides cannot be not-applicable")
                if len(logic_data_ids) >= 3 and plan.get("dominant_medium") not in {"data-chart", "table"}:
                    errors.append(
                        f"{qpath}: three or more comparable values require a native data-chart or table as the dominant medium"
                    )
                if encoding_mode == "native-chart" and plan.get("dominant_medium") != "data-chart":
                    errors.append(f"{qpath}.encoding_mode: native-chart must use dominant_medium=data-chart")
                if encoding_mode == "native-table" and plan.get("dominant_medium") != "table":
                    errors.append(f"{qpath}.encoding_mode: native-table must use dominant_medium=table")
                if encoding_mode == "shape-encoded-chart":
                    require_keys(exception, {"reason", "approved_by", "approval_basis"}, f"{qpath}.shape_encoded_exception", errors)
                    if isinstance(exception, dict):
                        for key in ("reason", "approved_by", "approval_basis"):
                            if not nonempty(exception.get(key)):
                                errors.append(f"{qpath}.shape_encoded_exception.{key}: must be non-empty")
                        approval = str(exception.get("approved_by", "")).casefold()
                        if "user" not in approval and "用户" not in approval:
                            errors.append(f"{qpath}.shape_encoded_exception.approved_by: requires explicit user approval")
                elif exception is not None:
                    errors.append(f"{qpath}.shape_encoded_exception: must be null unless shape-encoded-chart is used")
            else:
                if encoding_mode != "not-applicable":
                    errors.append(f"{qpath}.encoding_mode: slides without Logic data must be not-applicable")
                if not isinstance(scale, dict) or scale.get("type") != "none" or scale.get("baseline") is not None or scale.get("unit") is not None:
                    errors.append(f"{qpath}.scale: non-quantitative slides must use type=none with null baseline and unit")
                if exception is not None:
                    errors.append(f"{qpath}.shape_encoded_exception: non-quantitative slides must use null")
    for key in ("uses_bottom_conclusion_band", "rhythm_exception", "backflow_required", "anti_flatness_review"):
        if not isinstance(plan.get(key), bool):
            errors.append(f"{path}.{key}: must be boolean")
    if plan.get("backflow_required") is True and not nonempty(plan.get("backflow_reason")):
        errors.append(f"{path}.backflow_reason: required when backflow_required is true")
    series_behavior = series_contract.get("behavior") if isinstance(series_contract, dict) else None
    expected_rhythm_exception = series_behavior in {"locked-backbone", "controlled-variation"}
    if plan.get("rhythm_exception") is not expected_rhythm_exception:
        errors.append(f"{path}.rhythm_exception: must reflect purposeful series repetition")
    if expected_rhythm_exception and not nonempty(plan.get("repetition_reason")):
        errors.append(f"{path}.repetition_reason: required for purposeful repetition")

    units = copy_slide.get("copy_units", [])
    expected_ids = [unit.get("copy_id") for unit in sorted(units, key=lambda item: item.get("order", 0))]
    unit_map = {unit.get("copy_id"): unit for unit in units}
    if plan.get("reading_sequence") != expected_ids:
        errors.append(f"{path}.reading_sequence: must equal Copy order")

    validate_content_aware_canvas(
        plan.get("content_aware_canvas"),
        plan.get("dominant_medium"),
        expected_ids,
        f"{path}.content_aware_canvas",
        errors,
    )
    validate_asset_strategy(
        plan.get("asset_strategy"),
        plan.get("icon_scan"),
        f"{path}.asset_strategy",
        errors,
    )

    area_plan = plan.get("area_plan")
    region_id_set: set[str] = set()
    if not isinstance(area_plan, list) or not area_plan:
        errors.append(f"{path}.area_plan: must be a non-empty array")
    else:
        region_ids = []
        covered_copy_ids = []
        share_total = 0.0
        for region_index, region in enumerate(area_plan):
            rpath = f"{path}.area_plan[{region_index}]"
            require_keys(region, {"region_id", "role", "share_percent", "contains_copy_ids", "grid_columns"}, rpath, errors)
            if not isinstance(region, dict):
                continue
            region_ids.append(region.get("region_id"))
            if not nonempty(region.get("region_id")) or not nonempty(region.get("role")):
                errors.append(f"{rpath}: region_id and role must be non-empty")
            share = region.get("share_percent")
            if not isinstance(share, (int, float)) or share <= 0:
                errors.append(f"{rpath}.share_percent: must be positive")
            else:
                share_total += float(share)
            copy_ids = region.get("contains_copy_ids")
            if not isinstance(copy_ids, list) or any(copy_id not in expected_ids for copy_id in copy_ids):
                errors.append(f"{rpath}.contains_copy_ids: must reference visible copy ids")
            else:
                covered_copy_ids.extend(copy_ids)
            columns = region.get("grid_columns")
            if not isinstance(columns, list) or len(columns) != 2 or any(not isinstance(v, int) or not 1 <= v <= policy.column_count for v in columns) or columns[0] > columns[1]:
                errors.append(f"{rpath}.grid_columns: must be [start,end] within 1..{policy.column_count}")
        if len(region_ids) != len(set(region_ids)):
            errors.append(f"{path}.area_plan: region_id values must be unique")
        region_id_set = {value for value in region_ids if nonempty(value)}
        if not 90 <= share_total <= 110:
            errors.append(f"{path}.area_plan: share_percent total must be 90..110")
        if set(covered_copy_ids) != set(expected_ids):
            errors.append(f"{path}.area_plan: must cover every visible copy_id")

    semantic_tree = plan.get("semantic_layout_tree")
    validate_semantic_layout_tree(
        semantic_tree,
        expected_ids,
        region_id_set,
        f"{path}.semantic_layout_tree",
        errors,
    )

    references = plan.get("reference_selection")
    if not isinstance(references, list) or len(references) > 6:
        errors.append(f"{path}.reference_selection: must contain 0..6 items")
        references = []
    if not references and not nonempty(plan.get("reference_exception")):
        errors.append(f"{path}.reference_exception: required when no reference is selected")
    for ref_index, reference in enumerate(references):
        rpath = f"{path}.reference_selection[{ref_index}]"
        require_keys(reference, {"record_id", "use_for", "do_not_copy", "thumbnail_reviewed"}, rpath, errors)
        if isinstance(reference, dict):
            if reference.get("record_id") not in loaded_record_ids:
                errors.append(f"{rpath}.record_id: must appear in root loaded_record_ids")
            for key in ("use_for", "do_not_copy"):
                if not nonempty(reference.get(key)):
                    errors.append(f"{rpath}.{key}: must be non-empty")
            if reference.get("thumbnail_reviewed") is not True:
                errors.append(f"{rpath}.thumbnail_reviewed: must be true")

    slide_ab = plan.get("ab_review")
    require_keys(
        slide_ab,
        {"required", "candidates", "selected_candidate_id", "rejected_candidate_ids", "rejection_rationale", "greybox_status", "visual_self_correction"},
        f"{path}.ab_review",
        errors,
    )
    if isinstance(slide_ab, dict):
        required = slide_ab.get("required")
        if not isinstance(required, bool):
            errors.append(f"{path}.ab_review.required: must be boolean")
        if (plan.get("slide_id") in required_ab_ids) != (required is True):
            errors.append(f"{path}.ab_review.required: must match root required_slide_ids")
        candidates = slide_ab.get("candidates")
        minimum = 2 if required else 1
        if not isinstance(candidates, list) or len(candidates) < minimum or len(candidates) > 2:
            errors.append(f"{path}.ab_review.candidates: must contain {minimum}..2 candidates")
            candidates = []
        candidate_ids = []
        for candidate_index, candidate in enumerate(candidates):
            cpath = f"{path}.ab_review.candidates[{candidate_index}]"
            require_keys(candidate, {"candidate_id", "silhouette_family", "first_visual", "main_backbone", "reading_path", "area_plan", "reference_ids", "risk_notes", "semantic_tree_signature", "prototype_file"}, cpath, errors)
            if not isinstance(candidate, dict):
                continue
            candidate_ids.append(candidate.get("candidate_id"))
            for key in ("candidate_id", "silhouette_family", "first_visual", "main_backbone", "reading_path", "semantic_tree_signature"):
                if not nonempty(candidate.get(key)):
                    errors.append(f"{cpath}.{key}: must be non-empty")
            prototype_file = candidate.get("prototype_file")
            if required and not nonempty(prototype_file):
                errors.append(f"{cpath}.prototype_file: A/B candidates require rendered prototype evidence")
            elif not required and prototype_file is not None and not nonempty(prototype_file):
                errors.append(f"{cpath}.prototype_file: must be null or non-empty")
            if not isinstance(candidate.get("area_plan"), list) or not candidate.get("area_plan"):
                errors.append(f"{cpath}.area_plan: must be a non-empty array")
            ref_ids = candidate.get("reference_ids")
            if not isinstance(ref_ids, list) or any(ref_id not in loaded_record_ids for ref_id in ref_ids):
                errors.append(f"{cpath}.reference_ids: must reference loaded visual records")
            if not isinstance(candidate.get("risk_notes"), list):
                errors.append(f"{cpath}.risk_notes: must be an array")
        if len(candidate_ids) != len(set(candidate_ids)):
            errors.append(f"{path}.ab_review.candidates: candidate_id values must be unique")
        selected_id = slide_ab.get("selected_candidate_id")
        if selected_id not in candidate_ids:
            errors.append(f"{path}.ab_review.selected_candidate_id: must reference a candidate")
        rejected = slide_ab.get("rejected_candidate_ids")
        expected_rejected = [candidate_id for candidate_id in candidate_ids if candidate_id != selected_id]
        if rejected != expected_rejected:
            errors.append(f"{path}.ab_review.rejected_candidate_ids: must list all non-selected candidates in order")
        if required and not nonempty(slide_ab.get("rejection_rationale")):
            errors.append(f"{path}.ab_review.rejection_rationale: required for A/B pages")
        if slide_ab.get("greybox_status") not in {"approved", "not-required"}:
            errors.append(f"{path}.ab_review.greybox_status: invalid value")

        correction = slide_ab.get("visual_self_correction")
        require_keys(
            correction,
            {"required", "max_rounds", "rounds", "automatic_signals", "automatic_signal_role", "candidate_diversity_status", "final_selection_basis", "stop_reason"},
            f"{path}.ab_review.visual_self_correction",
            errors,
        )
        if isinstance(correction, dict):
            if correction.get("required") is not required:
                errors.append(f"{path}.ab_review.visual_self_correction.required: must match ab_review.required")
            if correction.get("max_rounds") != 2:
                errors.append(f"{path}.ab_review.visual_self_correction.max_rounds: must be 2")
            if correction.get("automatic_signal_role") != "diagnostic-only":
                errors.append(f"{path}.ab_review.visual_self_correction.automatic_signal_role: must be diagnostic-only")
            if correction.get("final_selection_basis") != "professional-visual-judgment":
                errors.append(f"{path}.ab_review.visual_self_correction.final_selection_basis: must be professional-visual-judgment")
            if not isinstance(correction.get("automatic_signals"), list):
                errors.append(f"{path}.ab_review.visual_self_correction.automatic_signals: must be an array")
            if not nonempty(correction.get("stop_reason")):
                errors.append(f"{path}.ab_review.visual_self_correction.stop_reason: must be non-empty")
            rounds = correction.get("rounds")
            if not isinstance(rounds, list):
                errors.append(f"{path}.ab_review.visual_self_correction.rounds: must be an array")
                rounds = []
            if required and not 1 <= len(rounds) <= 2:
                errors.append(f"{path}.ab_review.visual_self_correction.rounds: A/B requires 1..2 rounds")
            if not required and rounds:
                errors.append(f"{path}.ab_review.visual_self_correction.rounds: non-A/B pages require an empty array")
            diversity = correction.get("candidate_diversity_status")
            allowed_diversity = {"preserved", "reconstructed-after-collapse"} if required else {"not-applicable"}
            if diversity not in allowed_diversity:
                errors.append(f"{path}.ab_review.visual_self_correction.candidate_diversity_status: invalid value")
            for round_index, round_item in enumerate(rounds):
                rpath = f"{path}.ab_review.visual_self_correction.rounds[{round_index}]"
                require_keys(round_item, {"round_id", "candidate_ids", "prototype_files", "findings_by_dimension", "preserve", "change", "outcome"}, rpath, errors)
                if not isinstance(round_item, dict):
                    continue
                if not nonempty(round_item.get("round_id")):
                    errors.append(f"{rpath}.round_id: must be non-empty")
                round_candidates = round_item.get("candidate_ids")
                if not isinstance(round_candidates, list) or not round_candidates or any(value not in candidate_ids for value in round_candidates):
                    errors.append(f"{rpath}.candidate_ids: must reference current candidates")
                prototypes = round_item.get("prototype_files")
                if not isinstance(prototypes, list) or len(prototypes) != len(round_candidates or []) or any(not nonempty(value) for value in prototypes or []):
                    errors.append(f"{rpath}.prototype_files: must provide one rendered prototype per candidate")
                findings = round_item.get("findings_by_dimension")
                require_keys(findings, SELF_CORRECTION_DIMENSIONS, f"{rpath}.findings_by_dimension", errors)
                if isinstance(findings, dict):
                    if set(findings) != SELF_CORRECTION_DIMENSIONS:
                        errors.append(f"{rpath}.findings_by_dimension: must contain exactly {sorted(SELF_CORRECTION_DIMENSIONS)}")
                    for dimension in SELF_CORRECTION_DIMENSIONS:
                        if not nonempty(findings.get(dimension)):
                            errors.append(f"{rpath}.findings_by_dimension.{dimension}: must be non-empty")
                for key in ("preserve", "change"):
                    values = round_item.get(key)
                    if not isinstance(values, list) or not values or any(not nonempty(value) for value in values):
                        errors.append(f"{rpath}.{key}: must be a non-empty string array")
                if round_item.get("outcome") not in {"iterate", "select", "both-insufficient-rebuild"}:
                    errors.append(f"{rpath}.outcome: invalid value")
            if rounds and rounds[-1].get("outcome") != "select":
                errors.append(f"{path}.ab_review.visual_self_correction.rounds: final round must select a candidate")

    art_lock = plan.get("art_direction_lock")
    lock_keys = {
        "composition_locked", "silhouette_locked", "dominant_medium_locked", "density_locked",
        "reading_path_locked", "copy_mapping_locked", "series_behavior_locked", "motif_locked",
        "semantic_whitespace_locked", "context_rail_locked", "semantic_layout_tree_locked",
        "content_aware_canvas_locked", "asset_strategy_locked",
    }
    require_keys(art_lock, lock_keys, f"{path}.art_direction_lock", errors)
    if isinstance(art_lock, dict):
        for key in lock_keys:
            if art_lock.get(key) is not True:
                errors.append(f"{path}.art_direction_lock.{key}: must be true")
    if plan.get("handoff_status") != "ready-for-output":
        errors.append(f"{path}.handoff_status: expected ready-for-output")

    visual_layers = plan.get("visual_layers")
    node_ids = {node.get("node_id") for node in tree_nodes}
    if not isinstance(visual_layers, list):
        errors.append(f"{path}.visual_layers: must be an array")
    else:
        layer_node_ids = [item.get("node_id") for item in visual_layers if isinstance(item, dict)]
        if len(layer_node_ids) != len(set(layer_node_ids)) or set(layer_node_ids) != node_ids:
            errors.append(f"{path}.visual_layers: must map every logic node exactly once")
        for layer_index, layer in enumerate(visual_layers):
            if not isinstance(layer, dict) or layer.get("layer") not in VISUAL_ROLES:
                errors.append(f"{path}.visual_layers[{layer_index}]: requires node_id and valid layer")

    mappings = plan.get("copy_unit_map")
    if not isinstance(mappings, list):
        errors.append(f"{path}.copy_unit_map: must be an array")
        return
    plan_by_copy: dict[str, dict[str, Any]] = {}
    for map_index, mapping in enumerate(mappings):
        mpath = f"{path}.copy_unit_map[{map_index}]"
        require_keys(
            mapping,
            {"copy_id", "render_target_id", "target_type", "verification_method", "visual_role", "style_token", "reading_order", "parent_render_target_id", "group_container_id", "alignment", "auto_fit", "intentional_line_breaks"},
            mpath,
            errors,
        )
        if not isinstance(mapping, dict):
            continue
        copy_id = mapping.get("copy_id")
        target_id = mapping.get("render_target_id")
        if copy_id not in unit_map or copy_id in plan_by_copy:
            errors.append(f"{mpath}.copy_id: must uniquely reference a copy unit")
        else:
            plan_by_copy[copy_id] = mapping
        if not nonempty(target_id) or target_id in global_targets:
            errors.append(f"{mpath}.render_target_id: must be globally unique and non-empty")
        else:
            global_targets.add(target_id)
        if mapping.get("target_type") not in TARGET_TYPES:
            errors.append(f"{mpath}.target_type: invalid value")
        if mapping.get("verification_method") not in VERIFY_METHODS:
            errors.append(f"{mpath}.verification_method: invalid value")
        if mapping.get("target_type") == "shape" and mapping.get("verification_method") != "shape-name":
            errors.append(f"{mpath}.verification_method: shape targets require shape-name")
        if mapping.get("visual_role") not in VISUAL_ROLES:
            errors.append(f"{mpath}.visual_role: invalid value")
        if mapping.get("style_token") not in allowed_tokens:
            errors.append(f"{mpath}.style_token: not allowed by typography contract")
        if mapping.get("reading_order") != unit_map.get(copy_id, {}).get("order"):
            errors.append(f"{mpath}.reading_order: must equal Copy order")
        if mapping.get("alignment") not in ALIGNMENTS:
            errors.append(f"{mpath}.alignment: invalid value")
        if mapping.get("auto_fit") not in AUTO_FIT:
            errors.append(f"{mpath}.auto_fit: invalid value")
        if mapping.get("intentional_line_breaks") != unit_map.get(copy_id, {}).get("intentional_line_breaks"):
            errors.append(f"{mpath}.intentional_line_breaks: must match Copy")
    if set(plan_by_copy) != set(expected_ids):
        errors.append(f"{path}.copy_unit_map: must map every copy_id exactly once")

    target_types = [mapping.get("target_type") for mapping in plan_by_copy.values()]
    table_alternative = approved_alternative and approved_alternative.get("from_object_type") == "native-table"
    if plan.get("dominant_medium") == "table" and not table_alternative and "table-cell" not in target_types:
        errors.append(f"{path}.copy_unit_map: dominant_medium=table requires at least one table-cell target unless an alternative is approved")

    for copy_id, mapping in plan_by_copy.items():
        parent_copy_id = unit_map[copy_id].get("parent_copy_id")
        expected_parent_target = plan_by_copy.get(parent_copy_id, {}).get("render_target_id") if parent_copy_id else None
        if mapping.get("parent_render_target_id") != expected_parent_target:
            errors.append(f"{path}.copy_unit_map[{copy_id}]: parent_render_target_id mismatch")
        if expected_parent_target and mapping.get("render_target_id") == expected_parent_target:
            errors.append(f"{path}.copy_unit_map[{copy_id}]: parent and child targets must differ")

    hierarchy = plan.get("visual_hierarchy")
    hierarchy_keys = {"primary_copy_ids", "secondary_copy_ids", "tertiary_copy_ids", "annotation_copy_ids", "anchor_copy_ids", "anchor_rationale"}
    require_keys(hierarchy, hierarchy_keys, f"{path}.visual_hierarchy", errors)
    if isinstance(hierarchy, dict):
        buckets: list[str] = []
        for key in ("primary_copy_ids", "secondary_copy_ids", "tertiary_copy_ids", "annotation_copy_ids"):
            values = hierarchy.get(key)
            if not isinstance(values, list):
                errors.append(f"{path}.visual_hierarchy.{key}: must be an array")
            else:
                buckets.extend(values)
        if len(buckets) != len(set(buckets)) or set(buckets) != set(expected_ids):
            errors.append(f"{path}.visual_hierarchy: four buckets must cover each copy_id once")
        bucket_role = {}
        for key, role in (("primary_copy_ids", "primary"), ("secondary_copy_ids", "secondary"), ("tertiary_copy_ids", "tertiary"), ("annotation_copy_ids", "annotation")):
            for copy_id in hierarchy.get(key, []) if isinstance(hierarchy.get(key), list) else []:
                bucket_role[copy_id] = role
        for copy_id, mapping in plan_by_copy.items():
            if bucket_role.get(copy_id) != mapping.get("visual_role"):
                errors.append(f"{path}.copy_unit_map[{copy_id}].visual_role: must match visual_hierarchy bucket")
        root_id = logic_slide.get("page_message_tree", {}).get("root_node_id")
        root_primary = next((item.get("primary_copy_id") for item in copy_slide.get("node_copy_map", []) if item.get("logic_node_id") == root_id), None)
        if root_primary not in hierarchy.get("primary_copy_ids", []):
            errors.append(f"{path}.visual_hierarchy: root primary copy must be primary")
        anchors = hierarchy.get("anchor_copy_ids")
        if not isinstance(anchors, list) or not anchors or any(copy_id not in set(expected_ids) for copy_id in anchors):
            errors.append(f"{path}.visual_hierarchy.anchor_copy_ids: must be a non-empty subset")
        if not nonempty(hierarchy.get("anchor_rationale")):
            errors.append(f"{path}.visual_hierarchy.anchor_rationale: must be non-empty")

    review = plan.get("atomicity_review")
    require_keys(review, ATOMIC_REVIEW_KEYS, f"{path}.atomicity_review", errors)
    if isinstance(review, dict):
        for key in ATOMIC_REVIEW_KEYS:
            if review.get(key) is not True:
                errors.append(f"{path}.atomicity_review.{key}: must be true")

    node_primary = {item.get("logic_node_id"): item.get("primary_copy_id") for item in copy_slide.get("node_copy_map", [])}
    sibling_groups: dict[tuple[str, str], list[str]] = {}
    for node in tree_nodes:
        if node.get("parent_node_id") and node.get("sibling_group_id"):
            sibling_groups.setdefault((node["parent_node_id"], node["sibling_group_id"]), []).append(node_primary.get(node.get("node_id")))
    for (_, group_id), copy_ids in sibling_groups.items():
        copy_ids = [copy_id for copy_id in copy_ids if copy_id in plan_by_copy]
        if len(copy_ids) < 2:
            continue
        tokens = {plan_by_copy[copy_id].get("style_token") for copy_id in copy_ids}
        alignments = {plan_by_copy[copy_id].get("alignment") for copy_id in copy_ids}
        containers = {plan_by_copy[copy_id].get("group_container_id") for copy_id in copy_ids}
        if len(tokens) != 1 or len(alignments) != 1 or len(containers) != 1:
            errors.append(f"{path}: sibling group {group_id} must share style_token, alignment, and group_container_id")

    data_ids = {item.get("data_id") for item in logic_slide.get("data", []) if isinstance(item, dict)}
    kpi_plan = plan.get("kpi_plan")
    if not isinstance(kpi_plan, list):
        errors.append(f"{path}.kpi_plan: must be an array")
    else:
        planned_data_ids = [item.get("data_id") for item in kpi_plan if isinstance(item, dict)]
        if len(planned_data_ids) != len(set(planned_data_ids)) or set(planned_data_ids) != data_ids:
            errors.append(f"{path}.kpi_plan: must map every data_id exactly once")

    relation_by_id = {item.get("relation_id"): item for item in logic_slide.get("semantic_relations", []) if isinstance(item, dict)}
    connector_plan = plan.get("connector_plan")
    if isinstance(connector_plan, dict):
        connector_ids = connector_plan.get("relation_ids")
        if not isinstance(connector_ids, list) or any(relation_id not in relation_by_id for relation_id in connector_ids):
            errors.append(f"{path}.connector_plan.relation_ids: must reference semantic relations")
        elif any(relation_by_id[relation_id].get("type") == "peer" for relation_id in connector_ids):
            errors.append(f"{path}.connector_plan.relation_ids: peer relations cannot use connectors")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    try:
        package = json.loads(args.package.read_text(encoding="utf-8"))
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        errors = validate_plan(package, plan, load_policy(args.config))
    except (OSError, json.JSONDecodeError, FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAILED: {len(errors)} error(s)")
        return 1
    print(f"PASS: art-direction plan {plan.get('package_id')} ({len(plan.get('slides', []))} slides)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
