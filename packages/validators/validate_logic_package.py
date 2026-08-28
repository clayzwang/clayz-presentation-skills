#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate the v2.3 PPT logic layer with only the Python standard library."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from index_evidence import validate_index_evidence
from resource_inventory import validate_resource_inventory


CONTRACT_VERSION = "2.3"
STATUS_RANK = {"draft": 0, "logic-approved": 1, "copy-approved": 2}
MATERIAL_TYPES = {
    "management-report", "business-analysis", "strategy-deployment", "sales-training"
}
OUTCOME_MODES = {"understand", "approve", "execute"}
CONFIRMATIONS = {"user-provided", "user-confirmed"}
MANAGEMENT_STAGES = {
    "strategic-framing", "mechanism-design", "campaign-deployment",
    "operating-system", "monitoring-diagnosis", "experiment-review",
    "skill-enablement",
}
NARRATIVE_ARCHETYPES = {
    "operating-diagnosis", "policy-reform", "strategy-map",
    "operating-system-design", "experiment-learning", "annual-mobilization",
    "decision-proposal", "training-sop",
}
CLAIM_STATUSES = {
    "source-fact", "direct-calculation", "interpretation", "causal-claim",
    "forecast", "recommendation", "target", "hypothesis", "missing-data",
}
CONFIDENCE = {"high", "medium", "low", "unknown"}
OBJECT_TYPES = {
    "channel-carrier", "method", "principle", "product", "project", "scene",
    "entry-method", "exception", "user-segment", "need", "risk", "role",
    "action", "capability", "resource", "metric", "result", "stage", "other",
}
RELATION_TYPES = {
    "peer", "contains", "supports", "enables", "maps-to", "sequence",
    "transforms-to", "cause", "condition", "feedback", "contrast", "rank",
    "exception-to", "evidence-for",
}
DIRECTIONS = {"none", "forward", "bidirectional"}
STRENGTHS = {"confirmed", "inferred", "hypothesis", "normative"}
CONDITION_COMBINATIONS = {"all-of", "any-of", "one-of"}
LOGIC_LOCK_KEYS = {
    "slide_order_locked", "claims_locked", "numbers_locked",
    "metric_definitions_locked", "semantic_objects_locked",
    "semantic_relations_locked", "page_message_trees_locked", "sources_locked",
    "management_route_locked", "reasoning_contracts_locked",
    "cross_slide_contract_locked",
}
CONTENT_LOAD_CLASSES = {"light", "standard", "dense", "detail-dense"}
DECISION_WEIGHTS = {"low", "medium", "high", "critical"}
ZOOM_TRANSITIONS = {"hold", "zoom-in", "zoom-out", "shift", "none"}
SERIES_ROLES = {"establish", "continue", "advance", "culminate", "break", "standalone"}
INVARIANT_KINDS = {"term", "object-order", "metric-definition", "analysis-axis", "grouping", "scope"}
SERIES_PURPOSES = {"compare", "progressive-reveal", "time-evolution", "object-drilldown", "policy-family", "accumulation"}
FORBIDDEN_KEYS = {
    "copy_id", "visible_copy", "speaker_notes", "font", "font_size", "color",
    "layout", "position", "shape", "text_box", "line_break", "line_breaks",
    "intentional_line_breaks", "typography", "coordinates",
}
VISUAL_WORDS = re.compile(r"左侧|右侧|上方|下方|圆圈|圆形|方框|卡片|箭头|环绕|色块|配色|字号|版式|文本框")


def is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def require_keys(obj: Any, keys: set[str], path: str, errors: list[str]) -> None:
    if not isinstance(obj, dict):
        errors.append(f"{path}: must be an object")
        return
    missing = sorted(keys - set(obj))
    if missing:
        errors.append(f"{path}: missing keys {missing}")


def unique_ids(items: Any, key: str, path: str, errors: list[str]) -> set[str]:
    result: set[str] = set()
    if not isinstance(items, list):
        errors.append(f"{path}: must be an array")
        return result
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path}: must be an object")
            continue
        value = item.get(key)
        if not is_nonempty_string(value):
            errors.append(f"{item_path}.{key}: must be a non-empty string")
        elif value in result:
            errors.append(f"{item_path}.{key}: duplicate id {value}")
        else:
            result.add(value)
    return result


def scan_forbidden(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                errors.append(f"{path}.{key}: belongs to Copy or Output, not Logic")
            scan_forbidden(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_forbidden(child, f"{path}[{index}]", errors)


def validate_brief(brief: Any, errors: list[str]) -> None:
    require_keys(
        brief,
        {"purpose", "initiator_stance", "preflight", "usage_context", "duration_minutes", "constraints"},
        "brief",
        errors,
    )
    if not isinstance(brief, dict):
        return
    for key in ("purpose", "initiator_stance", "usage_context"):
        if not is_nonempty_string(brief.get(key)):
            errors.append(f"brief.{key}: must be a non-empty string")
    if not isinstance(brief.get("duration_minutes"), (int, float)) or brief.get("duration_minutes", 0) <= 0:
        errors.append("brief.duration_minutes: must be a positive number")
    if not isinstance(brief.get("constraints"), list):
        errors.append("brief.constraints: must be an array")

    preflight = brief.get("preflight")
    require_keys(
        preflight,
        {"audience", "material_type", "management_stage", "narrative_archetype", "desired_outcome", "confirmation"},
        "brief.preflight",
        errors,
    )
    if not isinstance(preflight, dict):
        return
    audience = preflight.get("audience")
    if not isinstance(audience, dict) or not is_nonempty_string(audience.get("primary")):
        errors.append("brief.preflight.audience.primary: must be a non-empty string")
    if preflight.get("material_type") not in MATERIAL_TYPES:
        errors.append(f"brief.preflight.material_type: must be one of {sorted(MATERIAL_TYPES)}")
    if preflight.get("management_stage") not in MANAGEMENT_STAGES:
        errors.append(f"brief.preflight.management_stage: must be one of {sorted(MANAGEMENT_STAGES)}")
    if preflight.get("narrative_archetype") not in NARRATIVE_ARCHETYPES:
        errors.append(f"brief.preflight.narrative_archetype: must be one of {sorted(NARRATIVE_ARCHETYPES)}")
    outcome = preflight.get("desired_outcome")
    if not isinstance(outcome, dict) or outcome.get("mode") not in OUTCOME_MODES or not is_nonempty_string(outcome.get("target")):
        errors.append("brief.preflight.desired_outcome: requires a valid mode and non-empty target")
    confirmation = preflight.get("confirmation")
    if not isinstance(confirmation, dict):
        errors.append("brief.preflight.confirmation: must be an object")
    else:
        for key in ("audience", "material_type", "management_stage", "narrative_archetype", "desired_outcome"):
            if confirmation.get(key) not in CONFIRMATIONS:
                errors.append(f"brief.preflight.confirmation.{key}: must be user-provided or user-confirmed")


def validate_slide(slide: Any, path: str, errors: list[str]) -> None:
    required = {
        "slide_id", "section_id", "narrative_role", "question_answered", "claim",
        "audience_state_before", "audience_state_after", "analysis_level", "zoom_transition",
        "content_load_class", "decision_weight", "series_id", "series_role",
        "transition_from", "transition_to", "data", "logic_map", "page_message_tree",
        "semantic_relations", "source_ids", "claim_status", "confidence", "reasoning_contracts",
        "do_not_change",
    }
    require_keys(slide, required, path, errors)
    if not isinstance(slide, dict):
        return
    for key in (
        "slide_id", "section_id", "narrative_role", "question_answered", "claim",
        "audience_state_before", "audience_state_after", "analysis_level",
    ):
        if not is_nonempty_string(slide.get(key)):
            errors.append(f"{path}.{key}: must be a non-empty string")
    if slide.get("zoom_transition") not in ZOOM_TRANSITIONS:
        errors.append(f"{path}.zoom_transition: invalid value")
    if slide.get("content_load_class") not in CONTENT_LOAD_CLASSES:
        errors.append(f"{path}.content_load_class: invalid value")
    if slide.get("decision_weight") not in DECISION_WEIGHTS:
        errors.append(f"{path}.decision_weight: invalid value")
    series_id = slide.get("series_id")
    if series_id is not None and not is_nonempty_string(series_id):
        errors.append(f"{path}.series_id: must be null or a non-empty string")
    if slide.get("series_role") not in SERIES_ROLES:
        errors.append(f"{path}.series_role: invalid value")
    elif series_id is None and slide.get("series_role") != "standalone":
        errors.append(f"{path}.series_role: slides outside a series must use standalone")
    elif series_id is not None and slide.get("series_role") == "standalone":
        errors.append(f"{path}.series_role: series slides cannot use standalone")
    for key in ("transition_from", "transition_to"):
        if not isinstance(slide.get(key), str):
            errors.append(f"{path}.{key}: must be a string")
    if slide.get("claim_status") not in CLAIM_STATUSES:
        errors.append(f"{path}.claim_status: invalid status")
    if slide.get("confidence") not in CONFIDENCE:
        errors.append(f"{path}.confidence: invalid confidence")
    for key in ("source_ids", "do_not_change"):
        if not isinstance(slide.get(key), list):
            errors.append(f"{path}.{key}: must be an array")

    logic_map = slide.get("logic_map")
    require_keys(logic_map, {"statement", "objects"}, f"{path}.logic_map", errors)
    if not isinstance(logic_map, dict):
        return
    statement = logic_map.get("statement")
    if not is_nonempty_string(statement):
        errors.append(f"{path}.logic_map.statement: must be non-empty")
    elif VISUAL_WORDS.search(statement):
        errors.append(f"{path}.logic_map.statement: contains visual wording")
    object_ids = unique_ids(logic_map.get("objects"), "object_id", f"{path}.logic_map.objects", errors)
    for index, obj in enumerate(logic_map.get("objects") or []):
        if not isinstance(obj, dict):
            continue
        opath = f"{path}.logic_map.objects[{index}]"
        require_keys(obj, {"object_id", "label", "type", "definition"}, opath, errors)
        if not is_nonempty_string(obj.get("label")) or not is_nonempty_string(obj.get("definition")):
            errors.append(f"{opath}: label and definition must be non-empty")
        if obj.get("type") not in OBJECT_TYPES:
            errors.append(f"{opath}.type: invalid object type")

    data_ids = unique_ids(slide.get("data"), "data_id", f"{path}.data", errors)
    for index, item in enumerate(slide.get("data") or []):
        if not isinstance(item, dict):
            continue
        dpath = f"{path}.data[{index}]"
        require_keys(
            item,
            {"data_id", "metric_name", "display_value", "raw_value", "unit", "period", "definition_ref", "source_ids", "evidence_status"},
            dpath,
            errors,
        )
        for key in ("metric_name", "display_value", "unit", "period", "definition_ref"):
            if not is_nonempty_string(item.get(key)):
                errors.append(f"{dpath}.{key}: must be non-empty")
        if not isinstance(item.get("source_ids"), list):
            errors.append(f"{dpath}.source_ids: must be an array")
        if item.get("evidence_status") not in CLAIM_STATUSES:
            errors.append(f"{dpath}.evidence_status: invalid status")

    relation_ids = unique_ids(slide.get("semantic_relations"), "relation_id", f"{path}.semantic_relations", errors)
    for index, relation in enumerate(slide.get("semantic_relations") or []):
        if not isinstance(relation, dict):
            continue
        rpath = f"{path}.semantic_relations[{index}]"
        require_keys(
            relation,
            {"relation_id", "type", "source_object_ids", "target_object_ids", "direction", "strength", "evidence_source_ids"},
            rpath,
            errors,
        )
        if relation.get("type") not in RELATION_TYPES:
            errors.append(f"{rpath}.type: invalid relation type")
        if relation.get("direction") not in DIRECTIONS:
            errors.append(f"{rpath}.direction: invalid direction")
        elif relation.get("type") == "peer" and relation.get("direction") != "none":
            errors.append(f"{rpath}.direction: peer relations must use none")
        elif relation.get("type") in {"sequence", "transforms-to"} and relation.get("direction") == "none":
            errors.append(f"{rpath}.direction: ordered relations require a direction")
        if relation.get("strength") not in STRENGTHS:
            errors.append(f"{rpath}.strength: invalid strength")
        for key in ("source_object_ids", "target_object_ids"):
            values = relation.get(key)
            if not isinstance(values, list) or not values:
                errors.append(f"{rpath}.{key}: must be a non-empty array")
            elif any(value not in object_ids for value in values):
                errors.append(f"{rpath}.{key}: references an unknown object")
        if not isinstance(relation.get("evidence_source_ids"), list):
            errors.append(f"{rpath}.evidence_source_ids: must be an array")
        combination = relation.get("combination")
        if relation.get("type") == "condition":
            if combination not in CONDITION_COMBINATIONS:
                errors.append(f"{rpath}.combination: condition relations require all-of, any-of, or one-of")
        elif combination is not None:
            errors.append(f"{rpath}.combination: only condition relations may define a combination")

    tree = slide.get("page_message_tree")
    require_keys(tree, {"root_node_id", "reading_sequence", "nodes"}, f"{path}.page_message_tree", errors)
    if not isinstance(tree, dict):
        return
    nodes = tree.get("nodes")
    node_ids = unique_ids(nodes, "node_id", f"{path}.page_message_tree.nodes", errors)
    root_id = tree.get("root_node_id")
    if root_id not in node_ids:
        errors.append(f"{path}.page_message_tree.root_node_id: unknown node")
    sequence = tree.get("reading_sequence")
    if not isinstance(sequence, list) or len(sequence) != len(node_ids) or set(sequence) != node_ids:
        errors.append(f"{path}.page_message_tree.reading_sequence: must cover every node exactly once")

    node_map = {node.get("node_id"): node for node in nodes or [] if isinstance(node, dict) and is_nonempty_string(node.get("node_id"))}
    child_to_parent: dict[str, str] = {}
    for index, node in enumerate(nodes or []):
        if not isinstance(node, dict):
            continue
        npath = f"{path}.page_message_tree.nodes[{index}]"
        require_keys(
            node,
            {"node_id", "parent_node_id", "level", "semantic_role", "content_ref", "sibling_group_id", "children"},
            npath,
            errors,
        )
        node_id = node.get("node_id")
        parent_id = node.get("parent_node_id")
        if node_id == root_id:
            if parent_id is not None or node.get("level") != 0:
                errors.append(f"{npath}: root must have null parent and level 0")
            if node.get("content_ref") != "claim":
                errors.append(f"{npath}.content_ref: root must reference claim")
        else:
            parent = node_map.get(parent_id)
            if parent is None:
                errors.append(f"{npath}.parent_node_id: unknown parent")
            elif node.get("level") != parent.get("level", -1) + 1:
                errors.append(f"{npath}.level: must equal parent level + 1")
        if not is_nonempty_string(node.get("semantic_role")):
            errors.append(f"{npath}.semantic_role: must be non-empty")
        content_ref = node.get("content_ref")
        valid_ref = content_ref == "claim"
        if isinstance(content_ref, str) and ":" in content_ref:
            prefix, ref_id = content_ref.split(":", 1)
            valid_ref = (prefix == "object" and ref_id in object_ids) or (prefix == "data" and ref_id in data_ids) or (prefix == "relation" and ref_id in relation_ids)
        if not valid_ref:
            errors.append(f"{npath}.content_ref: invalid reference {content_ref!r}")
        children = node.get("children")
        if not isinstance(children, list) or len(children) != len(set(children)):
            errors.append(f"{npath}.children: must be a duplicate-free array")
        else:
            for child_id in children:
                if child_id not in node_ids:
                    errors.append(f"{npath}.children: unknown child {child_id}")
                elif child_id in child_to_parent and child_to_parent[child_id] != node_id:
                    errors.append(f"{npath}.children: child {child_id} has multiple parents")
                else:
                    child_to_parent[child_id] = node_id

    for node_id, node in node_map.items():
        if node_id != root_id and child_to_parent.get(node_id) != node.get("parent_node_id"):
            errors.append(f"{path}.page_message_tree: parent/children mismatch for {node_id}")
        child_ids = node.get("children") if isinstance(node.get("children"), list) else []
        if len(child_ids) > 1:
            groups = {node_map.get(child_id, {}).get("sibling_group_id") for child_id in child_ids}
            if None in groups or "" in groups or len(groups) != 1:
                errors.append(f"{path}.page_message_tree: siblings under {node_id} require one non-empty sibling_group_id")

    reasoning = slide.get("reasoning_contracts")
    require_keys(
        reasoning,
        {"action_traceability", "change_mechanism", "operating_system", "experiment_learning"},
        f"{path}.reasoning_contracts",
        errors,
    )
    if not isinstance(reasoning, dict):
        return

    actions = reasoning.get("action_traceability")
    if not isinstance(actions, list):
        errors.append(f"{path}.reasoning_contracts.action_traceability: must be an array")
        actions = []
    action_nodes: set[str] = set()
    for index, action in enumerate(actions):
        apath = f"{path}.reasoning_contracts.action_traceability[{index}]"
        require_keys(
            action,
            {"action_node_id", "evidence_node_ids", "owner_object_ids", "timing", "metric_refs", "review_cadence"},
            apath,
            errors,
        )
        if not isinstance(action, dict):
            continue
        action_node = action.get("action_node_id")
        if action_node not in node_ids or action_node in action_nodes:
            errors.append(f"{apath}.action_node_id: must uniquely reference a page node")
        else:
            action_nodes.add(action_node)
        evidence_nodes = action.get("evidence_node_ids")
        if not isinstance(evidence_nodes, list) or not evidence_nodes or any(value not in node_ids for value in evidence_nodes):
            errors.append(f"{apath}.evidence_node_ids: must be a non-empty array of page nodes")
        owners = action.get("owner_object_ids")
        if not isinstance(owners, list) or not owners or any(value not in object_ids for value in owners):
            errors.append(f"{apath}.owner_object_ids: must be a non-empty array of page objects")
        metrics = action.get("metric_refs")
        if not isinstance(metrics, list) or any(value not in data_ids for value in metrics):
            errors.append(f"{apath}.metric_refs: must reference page data ids")
        for key in ("timing", "review_cadence"):
            if not is_nonempty_string(action.get(key)):
                errors.append(f"{apath}.{key}: must be non-empty")
    if slide.get("narrative_role") in {"action", "recommendation", "decision"} and not actions:
        errors.append(f"{path}.reasoning_contracts.action_traceability: action pages require evidence-linked actions")

    change = reasoning.get("change_mechanism")
    has_transform = any(
        isinstance(item, dict) and item.get("type") == "transforms-to"
        for item in slide.get("semantic_relations", [])
    )
    if has_transform and not isinstance(change, dict):
        errors.append(f"{path}.reasoning_contracts.change_mechanism: required for transforms-to")
    if change is not None:
        change_keys = {
            "old_constraint_object_ids", "rule_change_object_ids", "behavior_change_object_ids",
            "result_object_ids", "scope_object_ids", "exception_object_ids",
        }
        require_keys(change, change_keys, f"{path}.reasoning_contracts.change_mechanism", errors)
        if isinstance(change, dict):
            for key in change_keys:
                values = change.get(key)
                require_nonempty = key in {
                    "old_constraint_object_ids", "rule_change_object_ids",
                    "behavior_change_object_ids", "result_object_ids",
                }
                if not isinstance(values, list) or (require_nonempty and not values) or any(value not in object_ids for value in values or []):
                    errors.append(f"{path}.reasoning_contracts.change_mechanism.{key}: invalid object references")

    system = reasoning.get("operating_system")
    if slide.get("narrative_role") == "operating-system" and not isinstance(system, dict):
        errors.append(f"{path}.reasoning_contracts.operating_system: required for operating-system pages")
    if system is not None:
        system_keys = {
            "input_object_ids", "decision_rules", "output_object_ids", "user_object_ids",
            "cadence", "feedback_relation_ids", "exception_object_ids",
        }
        require_keys(system, system_keys, f"{path}.reasoning_contracts.operating_system", errors)
        if isinstance(system, dict):
            for key in ("input_object_ids", "output_object_ids", "user_object_ids"):
                values = system.get(key)
                if not isinstance(values, list) or not values or any(value not in object_ids for value in values):
                    errors.append(f"{path}.reasoning_contracts.operating_system.{key}: must be non-empty object references")
            exceptions = system.get("exception_object_ids")
            if not isinstance(exceptions, list) or any(value not in object_ids for value in exceptions or []):
                errors.append(f"{path}.reasoning_contracts.operating_system.exception_object_ids: invalid object references")
            rules = system.get("decision_rules")
            if not isinstance(rules, list) or not rules or any(not is_nonempty_string(value) for value in rules):
                errors.append(f"{path}.reasoning_contracts.operating_system.decision_rules: must be non-empty strings")
            feedback = system.get("feedback_relation_ids")
            if not isinstance(feedback, list) or not feedback or any(value not in relation_ids for value in feedback):
                errors.append(f"{path}.reasoning_contracts.operating_system.feedback_relation_ids: must reference relations")
            if not is_nonempty_string(system.get("cadence")):
                errors.append(f"{path}.reasoning_contracts.operating_system.cadence: must be non-empty")

    experiment = reasoning.get("experiment_learning")
    if slide.get("narrative_role") == "experiment-learning" and not isinstance(experiment, dict):
        errors.append(f"{path}.reasoning_contracts.experiment_learning: required for experiment-learning pages")
    if experiment is not None:
        experiment_keys = {
            "hypothesis", "intervention_object_ids", "observation_refs",
            "disconfirmed_belief", "new_learning", "next_test",
        }
        require_keys(experiment, experiment_keys, f"{path}.reasoning_contracts.experiment_learning", errors)
        if isinstance(experiment, dict):
            for key in ("hypothesis", "disconfirmed_belief", "new_learning", "next_test"):
                if not is_nonempty_string(experiment.get(key)):
                    errors.append(f"{path}.reasoning_contracts.experiment_learning.{key}: must be non-empty")
            interventions = experiment.get("intervention_object_ids")
            if not isinstance(interventions, list) or not interventions or any(value not in object_ids for value in interventions):
                errors.append(f"{path}.reasoning_contracts.experiment_learning.intervention_object_ids: invalid object references")
            observations = experiment.get("observation_refs")
            valid_observations = {f"node:{value}" for value in node_ids} | {f"data:{value}" for value in data_ids}
            if not isinstance(observations, list) or not observations or any(value not in valid_observations for value in observations):
                errors.append(f"{path}.reasoning_contracts.experiment_learning.observation_refs: must reference node: or data: ids")


def validate_package(data: Any, require_status: str = "logic-approved") -> list[str]:
    errors: list[str] = []
    required_root = {"contract_version", "package_id", "version", "status", "brief", "resource_inventory", "logic_layer", "copy_layer", "approvals", "index_evidence"}
    require_keys(data, required_root, "$", errors)
    if not isinstance(data, dict):
        return errors
    if data.get("contract_version") != CONTRACT_VERSION:
        errors.append(f"contract_version: expected {CONTRACT_VERSION}")
    for key in ("package_id", "version"):
        if not is_nonempty_string(data.get(key)):
            errors.append(f"{key}: must be a non-empty string")
    status = data.get("status")
    if status not in STATUS_RANK:
        errors.append("status: must be draft, logic-approved, or copy-approved")
    elif require_status not in STATUS_RANK or STATUS_RANK[status] < STATUS_RANK[require_status]:
        errors.append(f"status: requires at least {require_status}, got {status}")
    if status == "logic-approved" and data.get("copy_layer") is not None:
        errors.append("copy_layer: must be null while status is logic-approved")

    validate_resource_inventory(
        data.get("resource_inventory"),
        "resource_inventory",
        errors,
        require_ready=status in {"logic-approved", "copy-approved"},
    )
    selected_resource_ids = set(
        data.get("resource_inventory", {}).get("selected_resource_ids", [])
        if isinstance(data.get("resource_inventory"), dict)
        else []
    )

    required_index_stages: list[str] = []
    if status in {"logic-approved", "copy-approved"}:
        required_index_stages.append("logic")
    if status == "copy-approved":
        required_index_stages.append("copy")
    validate_index_evidence(data.get("index_evidence"), required_index_stages, "index_evidence", errors)

    validate_brief(data.get("brief"), errors)
    logic = data.get("logic_layer")
    require_keys(
        logic,
        {"knowledge_requirements", "sources", "glossary", "metric_dictionary", "deck_message_tree", "narrative", "cross_slide_contract", "slides", "open_items", "lock"},
        "logic_layer",
        errors,
    )
    if not isinstance(logic, dict):
        return errors
    scan_forbidden(logic, "logic_layer", errors)
    for key in ("knowledge_requirements", "sources", "glossary", "metric_dictionary", "slides", "open_items"):
        if not isinstance(logic.get(key), list):
            errors.append(f"logic_layer.{key}: must be an array")
    source_ids = unique_ids(logic.get("sources"), "source_id", "logic_layer.sources", errors)
    for index, source in enumerate(logic.get("sources") or []):
        if not isinstance(source, dict):
            continue
        spath = f"logic_layer.sources[{index}]"
        require_keys(source, {"source_id", "resource_id", "type", "title", "locator", "accessed_at", "reliability"}, spath, errors)
        for key in ("resource_id", "type", "title", "locator", "accessed_at", "reliability"):
            if not is_nonempty_string(source.get(key)):
                errors.append(f"{spath}.{key}: must be non-empty")
        if source.get("resource_id") not in selected_resource_ids:
            errors.append(f"{spath}.resource_id: must reference a resource selected before Logic")

    deck_tree = logic.get("deck_message_tree")
    require_keys(deck_tree, {"root_claim", "section_order", "slide_order"}, "logic_layer.deck_message_tree", errors)
    slides = logic.get("slides")
    slide_ids = unique_ids(slides, "slide_id", "logic_layer.slides", errors)
    if isinstance(deck_tree, dict):
        if not is_nonempty_string(deck_tree.get("root_claim")):
            errors.append("logic_layer.deck_message_tree.root_claim: must be non-empty")
        if not isinstance(deck_tree.get("section_order"), list):
            errors.append("logic_layer.deck_message_tree.section_order: must be an array")
        order = deck_tree.get("slide_order")
        if not isinstance(order, list) or order != [slide.get("slide_id") for slide in slides or [] if isinstance(slide, dict)]:
            errors.append("logic_layer.deck_message_tree.slide_order: must exactly match logic_layer.slides order")
    narrative = logic.get("narrative")
    require_keys(
        narrative,
        {"opening", "progression", "turning_points", "closing", "management_stage_path", "audience_state_arc"},
        "logic_layer.narrative",
        errors,
    )
    if isinstance(narrative, dict):
        for key in ("opening", "progression", "closing"):
            if not is_nonempty_string(narrative.get(key)):
                errors.append(f"logic_layer.narrative.{key}: must be non-empty")
        if not isinstance(narrative.get("turning_points"), list):
            errors.append("logic_layer.narrative.turning_points: must be an array")
        stages = narrative.get("management_stage_path")
        if not isinstance(stages, list) or not stages or any(stage not in MANAGEMENT_STAGES for stage in stages):
            errors.append("logic_layer.narrative.management_stage_path: must contain valid management stages")
        arc = narrative.get("audience_state_arc")
        slide_order = [slide.get("slide_id") for slide in slides if isinstance(slide, dict)]
        if not isinstance(arc, list) or [item.get("slide_id") for item in arc if isinstance(item, dict)] != slide_order:
            errors.append("logic_layer.narrative.audience_state_arc: must cover slide order exactly")
        else:
            slide_by_id = {slide.get("slide_id"): slide for slide in slides if isinstance(slide, dict)}
            for index, item in enumerate(arc):
                apath = f"logic_layer.narrative.audience_state_arc[{index}]"
                require_keys(item, {"slide_id", "state_before", "state_after", "narrative_move"}, apath, errors)
                if isinstance(item, dict):
                    slide = slide_by_id.get(item.get("slide_id"), {})
                    if item.get("state_before") != slide.get("audience_state_before") or item.get("state_after") != slide.get("audience_state_after"):
                        errors.append(f"{apath}: states must match the slide")
                    if not is_nonempty_string(item.get("narrative_move")):
                        errors.append(f"{apath}.narrative_move: must be non-empty")

    for index, slide in enumerate(slides or []):
        validate_slide(slide, f"logic_layer.slides[{index}]", errors)
        if isinstance(slide, dict):
            unknown_sources = set(slide.get("source_ids") or []) - source_ids
            if unknown_sources:
                errors.append(f"logic_layer.slides[{index}].source_ids: unknown sources {sorted(unknown_sources)}")

    cross = logic.get("cross_slide_contract")
    require_keys(cross, {"invariants", "series"}, "logic_layer.cross_slide_contract", errors)
    if isinstance(cross, dict):
        invariant_ids = unique_ids(cross.get("invariants"), "invariant_id", "logic_layer.cross_slide_contract.invariants", errors)
        for index, invariant in enumerate(cross.get("invariants") or []):
            ipath = f"logic_layer.cross_slide_contract.invariants[{index}]"
            require_keys(invariant, {"invariant_id", "kind", "scope_slide_ids", "locked_values", "rationale"}, ipath, errors)
            if not isinstance(invariant, dict):
                continue
            if invariant.get("kind") not in INVARIANT_KINDS:
                errors.append(f"{ipath}.kind: invalid value")
            scope = invariant.get("scope_slide_ids")
            if not isinstance(scope, list) or len(scope) < 2 or len(scope) != len(set(scope)) or any(value not in slide_ids for value in scope):
                errors.append(f"{ipath}.scope_slide_ids: must reference at least two unique slides")
            values = invariant.get("locked_values")
            if not isinstance(values, list) or not values or any(not is_nonempty_string(value) for value in values):
                errors.append(f"{ipath}.locked_values: must be non-empty strings")
            if not is_nonempty_string(invariant.get("rationale")):
                errors.append(f"{ipath}.rationale: must be non-empty")

        series_ids = unique_ids(cross.get("series"), "series_id", "logic_layer.cross_slide_contract.series", errors)
        slide_to_series: dict[str, str] = {}
        for index, series in enumerate(cross.get("series") or []):
            spath = f"logic_layer.cross_slide_contract.series[{index}]"
            require_keys(series, {"series_id", "purpose", "slide_ids", "comparison_key", "invariant_ids", "change_by_slide", "break_rule"}, spath, errors)
            if not isinstance(series, dict):
                continue
            if series.get("purpose") not in SERIES_PURPOSES:
                errors.append(f"{spath}.purpose: invalid value")
            members = series.get("slide_ids")
            if not isinstance(members, list) or len(members) < 2 or len(members) != len(set(members)) or any(value not in slide_ids for value in members):
                errors.append(f"{spath}.slide_ids: must reference at least two unique slides")
                members = []
            for slide_id in members:
                if slide_id in slide_to_series:
                    errors.append(f"{spath}.slide_ids: {slide_id} already belongs to {slide_to_series[slide_id]}")
                else:
                    slide_to_series[slide_id] = series.get("series_id")
            refs = series.get("invariant_ids")
            if not isinstance(refs, list) or not refs or any(value not in invariant_ids for value in refs):
                errors.append(f"{spath}.invariant_ids: must reference invariants")
            if not is_nonempty_string(series.get("comparison_key")) or not is_nonempty_string(series.get("break_rule")):
                errors.append(f"{spath}: comparison_key and break_rule must be non-empty")
            changes = series.get("change_by_slide")
            if not isinstance(changes, list) or [item.get("slide_id") for item in changes if isinstance(item, dict)] != members:
                errors.append(f"{spath}.change_by_slide: must cover series slides in order")
            else:
                for change_index, change in enumerate(changes):
                    cpath = f"{spath}.change_by_slide[{change_index}]"
                    require_keys(change, {"slide_id", "new_information", "unchanged_context"}, cpath, errors)
                    if isinstance(change, dict) and (
                        not is_nonempty_string(change.get("new_information"))
                        or not is_nonempty_string(change.get("unchanged_context"))
                    ):
                        errors.append(f"{cpath}: new_information and unchanged_context must be non-empty")
        slide_by_id = {slide.get("slide_id"): slide for slide in slides if isinstance(slide, dict)}
        for slide_id, slide in slide_by_id.items():
            if slide.get("series_id") != slide_to_series.get(slide_id):
                errors.append(f"logic_layer.slides[{slide_id}].series_id: must match cross_slide_contract")
        if series_ids != {series.get("series_id") for series in cross.get("series") or [] if isinstance(series, dict)}:
            errors.append("logic_layer.cross_slide_contract.series: invalid series ids")

    lock = logic.get("lock")
    require_keys(lock, LOGIC_LOCK_KEYS, "logic_layer.lock", errors)
    if isinstance(lock, dict) and status in {"logic-approved", "copy-approved"}:
        for key in LOGIC_LOCK_KEYS:
            if lock.get(key) is not True:
                errors.append(f"logic_layer.lock.{key}: must be true for approved status")

    approvals = data.get("approvals")
    require_keys(approvals, {"logic", "copy"}, "approvals", errors)
    if isinstance(approvals, dict) and status in {"logic-approved", "copy-approved"}:
        logic_approval = approvals.get("logic")
        if not isinstance(logic_approval, dict) or logic_approval.get("status") != "approved" or not is_nonempty_string(logic_approval.get("approved_by")):
            errors.append("approvals.logic: requires status approved and approved_by")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--require-status", choices=sorted(STATUS_RANK), default="logic-approved")
    args = parser.parse_args()
    try:
        data = json.loads(args.package.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read JSON: {exc}", file=sys.stderr)
        return 2
    errors = validate_package(data, args.require_status)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAILED: {len(errors)} error(s)")
        return 1
    print(f"PASS: PPT logic package {data.get('package_id')} ({data.get('status')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
