#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate the full v2 PPT package, including atomic copy hierarchy."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


COPY_LOCK_KEYS = {
    "titles_locked", "storylines_locked", "visible_copy_locked",
    "copy_hierarchy_locked", "numbers_locked", "punctuation_locked",
    "intentional_line_breaks_locked", "speaker_notes_locked",
    "title_modes_locked", "narrative_functions_locked", "cross_slide_copy_locked",
}
ROLES = {
    "title", "subtitle", "storyline", "group-label", "item", "evidence",
    "data-label", "data-value", "data-unit", "annotation", "footnote", "closing",
}
TEXT_MODES = {"sentence", "label", "list-item", "label-value", "dialogue", "quote", "note"}
FORBIDDEN_TEXT = re.compile(r"[|｜]| {3,}")
STRONG_SEQUENCE_LANGUAGE = re.compile(
    r"先[^。；;]{0,48}(?:再|然后|后再)|第一步|第二步|步骤[一二三四五六七八九1-9]"
)
TITLE_MODES = {
    "cover", "factual-status", "analytical-judgment", "mechanism-rule",
    "action-directive", "transition-assertion", "instructional-action", "closing",
}
STORYLINE_FUNCTIONS = {
    "none", "evidence-bridge", "mechanism-explanation", "action-bridge",
    "audience-transition", "instruction-bridge", "scope-qualification",
}


def _logic_validator_path() -> Path:
    candidates: list[Path] = []
    env_path = os.environ.get("PPT_DESIGN_LOGIC_VALIDATOR")
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(Path(__file__).resolve().parent / "validate_logic_package.py")
    candidates.append(Path(__file__).resolve().parents[2] / "ppt-design-logic" / "scripts" / "validate_logic_package.py")
    candidates.append(Path.home() / ".codex" / "skills" / "ppt-design-logic" / "scripts" / "validate_logic_package.py")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("ppt-design-logic/scripts/validate_logic_package.py not found; set PPT_DESIGN_LOGIC_VALIDATOR")


def _load_logic_validator():
    path = _logic_validator_path()
    spec = importlib.util.spec_from_file_location("ppt_design_logic_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load logic validator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def require_keys(obj: Any, keys: set[str], path: str, errors: list[str]) -> None:
    if not isinstance(obj, dict):
        errors.append(f"{path}: must be an object")
        return
    missing = sorted(keys - set(obj))
    if missing:
        errors.append(f"{path}: missing keys {missing}")


def normalize(text: str) -> str:
    return re.sub(r"[\s：:，,、；;。.!！？?（）()\-—]", "", text).casefold()


def _copy_text(copy_slide: dict[str, Any], copy_id: Any) -> str:
    for unit in copy_slide.get("copy_units", []):
        if isinstance(unit, dict) and unit.get("copy_id") == copy_id:
            return str(unit.get("text", ""))
    return ""


def validate_deck_expression_variation(
    logic_slides: list[Any],
    copy_slides: list[Any],
    errors: list[str],
) -> None:
    """Reject mechanical Copy shells that are not backed by a Logic series."""

    nonseries: list[tuple[str, dict[str, Any]]] = []
    for logic_slide, copy_slide in zip(logic_slides, copy_slides):
        if not isinstance(logic_slide, dict) or not isinstance(copy_slide, dict):
            continue
        slide_id = str(copy_slide.get("slide_id", ""))
        title = _copy_text(copy_slide, copy_slide.get("title_copy_id"))
        storyline = _copy_text(copy_slide, copy_slide.get("storyline_copy_id"))
        normalized_title = normalize(title)
        normalized_storyline = normalize(storyline)
        if (
            normalized_title
            and normalized_storyline
            and min(len(normalized_title), len(normalized_storyline)) >= 8
            and (normalized_title in normalized_storyline or normalized_storyline in normalized_title)
        ):
            errors.append(
                f"copy_layer.slides[{slide_id}]: title and storyline duplicate the same proposition instead of advancing it"
            )
        if logic_slide.get("series_id") is None:
            nonseries.append((slide_id, copy_slide))

    def repeated_groups(values: list[tuple[str, str]], minimum: int) -> list[tuple[str, list[str]]]:
        grouped: dict[str, list[str]] = {}
        for slide_id, value in values:
            if value:
                grouped.setdefault(value, []).append(slide_id)
        return [(value, ids) for value, ids in grouped.items() if len(ids) >= minimum]

    titles = [
        (slide_id, normalize(_copy_text(slide, slide.get("title_copy_id"))))
        for slide_id, slide in nonseries
    ]
    storylines = [
        (slide_id, normalize(_copy_text(slide, slide.get("storyline_copy_id"))))
        for slide_id, slide in nonseries
        if slide.get("storyline_copy_id") is not None
    ]
    for label, values in (("title", titles), ("storyline", storylines)):
        for _, slide_ids in repeated_groups(values, 2):
            errors.append(
                f"copy_layer: identical non-series {label} copy repeats across slides {slide_ids}"
            )

    strategies = [
        (slide_id, normalize(str(slide.get("audience_transition_copy_strategy", ""))))
        for slide_id, slide in nonseries
    ]
    for _, slide_ids in repeated_groups(strategies, 3):
        errors.append(
            f"copy_layer: one audience-transition expression is mechanically repeated across non-series slides {slide_ids}"
        )

    grammar_vectors: list[tuple[str, str]] = []
    phrase_occurrences: dict[str, set[str]] = {}
    for slide_id, slide in nonseries:
        vector: list[str] = []
        for unit in slide.get("copy_units", []):
            if not isinstance(unit, dict):
                continue
            role = unit.get("role")
            signature = unit.get("grammar_signature")
            if role not in {"footnote", "data-label", "data-unit", "data-value"} and nonempty(signature):
                vector.append(f"{role}:{signature}")
            if role in {"storyline", "item", "evidence", "annotation"}:
                phrase = normalize(str(unit.get("text", "")))
                if len(phrase) >= 10 and sum(character.isdigit() for character in phrase) < len(phrase) / 2:
                    phrase_occurrences.setdefault(phrase, set()).add(slide_id)
        if vector:
            grammar_vectors.append((slide_id, "|".join(vector)))
    for _, slide_ids in repeated_groups(grammar_vectors, 3):
        errors.append(
            f"copy_layer: one complete grammar vector is repeated across non-series slides {slide_ids}; vary syntax or declare a Logic series"
        )
    for slide_ids in phrase_occurrences.values():
        if len(slide_ids) >= 3:
            errors.append(
                f"copy_layer: one substantial visible phrase repeats across non-series slides {sorted(slide_ids)}"
            )


def validate_copy_layer(data: dict[str, Any], errors: list[str]) -> None:
    status = data.get("status")
    if status != "copy-approved":
        return
    copy = data.get("copy_layer")
    require_keys(copy, {"logic_version", "cross_slide_copy_contract", "slides", "lock"}, "copy_layer", errors)
    if not isinstance(copy, dict):
        return
    if copy.get("logic_version") != data.get("version"):
        errors.append("copy_layer.logic_version: must equal root version")
    lock = copy.get("lock")
    require_keys(lock, COPY_LOCK_KEYS, "copy_layer.lock", errors)
    if isinstance(lock, dict):
        for key in COPY_LOCK_KEYS:
            if lock.get(key) is not True:
                errors.append(f"copy_layer.lock.{key}: must be true")

    approval = (data.get("approvals") or {}).get("copy") if isinstance(data.get("approvals"), dict) else None
    if not isinstance(approval, dict) or approval.get("status") != "approved" or not nonempty(approval.get("approved_by")):
        errors.append("approvals.copy: requires status approved and approved_by")

    logic_slides = (data.get("logic_layer") or {}).get("slides") or []
    cross_logic = (data.get("logic_layer") or {}).get("cross_slide_contract") or {}
    cross_copy = copy.get("cross_slide_copy_contract")
    require_keys(cross_copy, {"invariant_renderings", "series_copy_strategies"}, "copy_layer.cross_slide_copy_contract", errors)
    if isinstance(cross_copy, dict):
        logic_invariants = {
            item.get("invariant_id"): item for item in cross_logic.get("invariants", []) if isinstance(item, dict)
        }
        logic_invariant_ids = set(logic_invariants)
        renderings = cross_copy.get("invariant_renderings")
        if not isinstance(renderings, list):
            errors.append("copy_layer.cross_slide_copy_contract.invariant_renderings: must be an array")
        else:
            rendering_ids = [item.get("invariant_id") for item in renderings if isinstance(item, dict)]
            if len(rendering_ids) != len(set(rendering_ids)) or set(rendering_ids) != logic_invariant_ids:
                errors.append("copy_layer.cross_slide_copy_contract.invariant_renderings: must cover every Logic invariant once")
            for index, item in enumerate(renderings):
                ipath = f"copy_layer.cross_slide_copy_contract.invariant_renderings[{index}]"
                require_keys(item, {"invariant_id", "visible_terms", "order_locked", "aliases_forbidden"}, ipath, errors)
                if isinstance(item, dict):
                    terms = item.get("visible_terms")
                    if not isinstance(terms, list) or not terms or any(not nonempty(value) for value in terms):
                        errors.append(f"{ipath}.visible_terms: must be non-empty strings")
                    elif terms != logic_invariants.get(item.get("invariant_id"), {}).get("locked_values"):
                        errors.append(f"{ipath}.visible_terms: must preserve Logic locked_values and order")
                    if item.get("order_locked") is not True:
                        errors.append(f"{ipath}.order_locked: must be true")
                    if not isinstance(item.get("aliases_forbidden"), list):
                        errors.append(f"{ipath}.aliases_forbidden: must be an array")
        logic_series_ids = {
            item.get("series_id") for item in cross_logic.get("series", []) if isinstance(item, dict)
        }
        strategies = cross_copy.get("series_copy_strategies")
        if not isinstance(strategies, list):
            errors.append("copy_layer.cross_slide_copy_contract.series_copy_strategies: must be an array")
        else:
            strategy_ids = [item.get("series_id") for item in strategies if isinstance(item, dict)]
            if len(strategy_ids) != len(set(strategy_ids)) or set(strategy_ids) != logic_series_ids:
                errors.append("copy_layer.cross_slide_copy_contract.series_copy_strategies: must cover every Logic series once")
            for index, item in enumerate(strategies):
                spath = f"copy_layer.cross_slide_copy_contract.series_copy_strategies[{index}]"
                require_keys(item, {"series_id", "stable_language", "progression_language", "repetition_rule"}, spath, errors)
                if isinstance(item, dict):
                    for key in ("stable_language", "progression_language", "repetition_rule"):
                        if not nonempty(item.get(key)):
                            errors.append(f"{spath}.{key}: must be non-empty")
    copy_slides = copy.get("slides")
    if not isinstance(copy_slides, list):
        errors.append("copy_layer.slides: must be an array")
        return
    logic_order = [slide.get("slide_id") for slide in logic_slides if isinstance(slide, dict)]
    copy_order = [slide.get("slide_id") for slide in copy_slides if isinstance(slide, dict)]
    if copy_order != logic_order:
        errors.append("copy_layer.slides: order must exactly match logic_layer.slides")

    global_copy_ids: set[str] = set()
    for index, (logic_slide, copy_slide) in enumerate(zip(logic_slides, copy_slides)):
        validate_copy_slide(logic_slide, copy_slide, f"copy_layer.slides[{index}]", global_copy_ids, errors)
    validate_deck_expression_variation(logic_slides, copy_slides, errors)


def validate_copy_slide(
    logic_slide: Any,
    copy_slide: Any,
    path: str,
    global_copy_ids: set[str],
    errors: list[str],
) -> None:
    required = {
        "slide_id", "title_mode", "storyline_function", "audience_transition_copy_strategy",
        "title_copy_id", "storyline_copy_id", "copy_units",
        "node_copy_map", "footnote_copy_ids", "speaker_notes",
        "series_copy_review",
    }
    require_keys(copy_slide, required, path, errors)
    if not isinstance(logic_slide, dict) or not isinstance(copy_slide, dict):
        return
    if copy_slide.get("slide_id") != logic_slide.get("slide_id"):
        errors.append(f"{path}.slide_id: must equal logic slide id")
    if copy_slide.get("title_mode") not in TITLE_MODES:
        errors.append(f"{path}.title_mode: invalid value")
    if copy_slide.get("storyline_function") not in STORYLINE_FUNCTIONS:
        errors.append(f"{path}.storyline_function: invalid value")
    if not nonempty(copy_slide.get("audience_transition_copy_strategy")):
        errors.append(f"{path}.audience_transition_copy_strategy: must be non-empty")

    tree = logic_slide.get("page_message_tree") or {}
    logic_nodes = tree.get("nodes") or []
    node_map = {node.get("node_id"): node for node in logic_nodes if isinstance(node, dict)}
    node_ids = set(node_map)
    root_id = tree.get("root_node_id")

    units = copy_slide.get("copy_units")
    if not isinstance(units, list):
        errors.append(f"{path}.copy_units: must be an array")
        return
    copy_map: dict[str, dict[str, Any]] = {}
    orders: list[int] = []
    for unit_index, unit in enumerate(units):
        upath = f"{path}.copy_units[{unit_index}]"
        require_keys(
            unit,
            {"copy_id", "text", "role", "text_mode", "source_logic_node_ids", "logic_level", "parent_copy_id", "sibling_group_id", "grammar_signature", "order", "render_separately", "merge_with_children", "intentional_line_breaks"},
            upath,
            errors,
        )
        if not isinstance(unit, dict):
            continue
        copy_id = unit.get("copy_id")
        if not nonempty(copy_id):
            errors.append(f"{upath}.copy_id: must be non-empty")
            continue
        if copy_id in global_copy_ids:
            errors.append(f"{upath}.copy_id: duplicate across deck: {copy_id}")
        global_copy_ids.add(copy_id)
        copy_map[copy_id] = unit
        text = unit.get("text")
        if not nonempty(text):
            errors.append(f"{upath}.text: must be non-empty")
        elif "\n" in text or "\r" in text:
            errors.append(f"{upath}.text: store active breaks as indexes, not newline characters")
        elif FORBIDDEN_TEXT.search(text):
            errors.append(f"{upath}.text: contains a fake-column delimiter or excessive spaces")
        if unit.get("role") not in ROLES:
            errors.append(f"{upath}.role: invalid role")
        if unit.get("text_mode") not in TEXT_MODES:
            errors.append(f"{upath}.text_mode: invalid text mode")
        sources = unit.get("source_logic_node_ids")
        if not isinstance(sources, list) or not sources or any(source not in node_ids for source in sources):
            errors.append(f"{upath}.source_logic_node_ids: must reference this slide's logic nodes")
        elif any(node_map[source].get("level") != unit.get("logic_level") for source in sources):
            errors.append(f"{upath}.logic_level: must match every sourced logic node")
        if unit.get("render_separately") is not True:
            errors.append(f"{upath}.render_separately: must be true")
        if unit.get("merge_with_children") is not False:
            errors.append(f"{upath}.merge_with_children: must be false")
        breaks = unit.get("intentional_line_breaks")
        if not isinstance(breaks, list) or any(not isinstance(value, int) or value <= 0 or value >= len(text or "") for value in breaks):
            errors.append(f"{upath}.intentional_line_breaks: must contain valid character indexes")
        order = unit.get("order")
        if not isinstance(order, int) or order < 1:
            errors.append(f"{upath}.order: must be a positive integer")
        else:
            orders.append(order)
        if not nonempty(unit.get("grammar_signature")):
            errors.append(f"{upath}.grammar_signature: must be non-empty")
    if orders and sorted(orders) != list(range(1, len(orders) + 1)):
        errors.append(f"{path}.copy_units.order: must be unique and contiguous from 1")

    title_id = copy_slide.get("title_copy_id")
    storyline_id = copy_slide.get("storyline_copy_id")
    narrative_role = logic_slide.get("narrative_role")
    if narrative_role == "closing":
        if copy_slide.get("title_mode") != "closing" or copy_slide.get("storyline_function") != "none":
            errors.append(f"{path}: closing slide requires closing/none modes")
        if title_id not in copy_map or copy_map.get(title_id, {}).get("role") != "closing":
            errors.append(f"{path}.title_copy_id: closing slide must reference a closing unit")
        if storyline_id is not None:
            errors.append(f"{path}.storyline_copy_id: closing slide must use null")
    elif title_id not in copy_map or copy_map.get(title_id, {}).get("role") != "title":
        errors.append(f"{path}.title_copy_id: must reference a title unit")
    if narrative_role == "cover" and copy_slide.get("title_mode") != "cover":
        errors.append(f"{path}.title_mode: cover slide requires cover")
    if narrative_role not in {"cover", "closing"}:
        if copy_slide.get("storyline_function") == "none":
            errors.append(f"{path}.storyline_function: body slides cannot use none")
        if storyline_id not in copy_map or copy_map.get(storyline_id, {}).get("role") != "storyline":
            errors.append(f"{path}.storyline_copy_id: body slides require a storyline unit")
        elif copy_map[storyline_id].get("intentional_line_breaks"):
            errors.append(f"{path}.storyline_copy_id: storyline must remain one line")
    elif storyline_id is not None and storyline_id not in copy_map:
        errors.append(f"{path}.storyline_copy_id: unknown copy id")

    footnotes = copy_slide.get("footnote_copy_ids")
    if not isinstance(footnotes, list) or any(copy_id not in copy_map or copy_map[copy_id].get("role") != "footnote" for copy_id in footnotes):
        errors.append(f"{path}.footnote_copy_ids: must reference footnote units")
    notes = copy_slide.get("speaker_notes")
    if not isinstance(notes, list):
        errors.append(f"{path}.speaker_notes: must be an array")
    else:
        note_ids: set[str] = set()
        for note_index, note in enumerate(notes):
            npath = f"{path}.speaker_notes[{note_index}]"
            require_keys(note, {"note_id", "text", "source_ids"}, npath, errors)
            if not isinstance(note, dict):
                continue
            if not nonempty(note.get("note_id")) or note.get("note_id") in note_ids:
                errors.append(f"{npath}.note_id: must be unique and non-empty")
            note_ids.add(note.get("note_id"))
            if not nonempty(note.get("text")) or not isinstance(note.get("source_ids"), list):
                errors.append(f"{npath}: requires non-empty text and source_ids array")

    mappings = copy_slide.get("node_copy_map")
    if not isinstance(mappings, list):
        errors.append(f"{path}.node_copy_map: must be an array")
        return
    node_to_primary: dict[str, str] = {}
    used_copy_ids: set[str] = set()
    for map_index, mapping in enumerate(mappings):
        mpath = f"{path}.node_copy_map[{map_index}]"
        require_keys(mapping, {"logic_node_id", "primary_copy_id", "supplemental_copy_ids"}, mpath, errors)
        if not isinstance(mapping, dict):
            continue
        node_id = mapping.get("logic_node_id")
        primary_id = mapping.get("primary_copy_id")
        supplemental = mapping.get("supplemental_copy_ids")
        if node_id not in node_ids or node_id in node_to_primary:
            errors.append(f"{mpath}.logic_node_id: must uniquely reference a logic node")
        if primary_id not in copy_map or primary_id in node_to_primary.values():
            errors.append(f"{mpath}.primary_copy_id: must uniquely reference a copy unit")
        else:
            node_to_primary[node_id] = primary_id
            used_copy_ids.add(primary_id)
            unit = copy_map[primary_id]
            if unit.get("source_logic_node_ids") != [node_id]:
                errors.append(f"{mpath}.primary_copy_id: primary unit must source only {node_id}")
            if unit.get("logic_level") != node_map.get(node_id, {}).get("level"):
                errors.append(f"{mpath}.primary_copy_id: logic_level mismatch")
            if unit.get("sibling_group_id") != node_map.get(node_id, {}).get("sibling_group_id"):
                errors.append(f"{mpath}.primary_copy_id: sibling_group_id mismatch")
        if not isinstance(supplemental, list) or any(copy_id not in copy_map for copy_id in supplemental):
            errors.append(f"{mpath}.supplemental_copy_ids: must reference copy units")
        else:
            for copy_id in supplemental:
                used_copy_ids.add(copy_id)
                if node_id not in copy_map[copy_id].get("source_logic_node_ids", []):
                    errors.append(f"{mpath}.supplemental_copy_ids: {copy_id} does not source {node_id}")
    if set(node_to_primary) != node_ids:
        errors.append(f"{path}.node_copy_map: must cover every logic node exactly once")
    if set(copy_map) != used_copy_ids:
        errors.append(f"{path}.node_copy_map: every copy unit must be primary or supplemental")

    for copy_id, unit in copy_map.items():
        parent_copy_id = unit.get("parent_copy_id")
        if parent_copy_id is not None and (parent_copy_id not in copy_map or parent_copy_id == copy_id):
            errors.append(f"{path}: {copy_id}.parent_copy_id must reference a different copy unit on the same slide")

    for node_id, primary_id in node_to_primary.items():
        node = node_map[node_id]
        unit = copy_map[primary_id]
        parent_node_id = node.get("parent_node_id")
        if parent_node_id is None:
            if unit.get("parent_copy_id") is not None:
                errors.append(f"{path}: root primary {primary_id} must have null parent_copy_id")
        elif parent_node_id in node_to_primary:
            expected_parent = node_to_primary[parent_node_id]
            if unit.get("parent_copy_id") != expected_parent:
                errors.append(f"{path}: {primary_id}.parent_copy_id must be {expected_parent}")
            parent_text = normalize(str(copy_map[expected_parent].get("text", "")))
            child_text = normalize(str(unit.get("text", "")))
            parent_role = copy_map[expected_parent].get("role")
            if parent_role not in {"title", "storyline"} and child_text and child_text in parent_text:
                errors.append(f"{path}: parent copy {expected_parent} contains child copy {primary_id}; hierarchy is flattened")

    sibling_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for node_id, primary_id in node_to_primary.items():
        node = node_map[node_id]
        parent_node_id = node.get("parent_node_id")
        group_id = node.get("sibling_group_id")
        if parent_node_id is not None and group_id:
            sibling_groups.setdefault((parent_node_id, group_id), []).append(copy_map[primary_id])
    for (parent_node_id, group_id), group_units in sibling_groups.items():
        if len(group_units) < 2:
            continue
        signatures = {unit.get("grammar_signature") for unit in group_units}
        roles = {unit.get("role") for unit in group_units}
        modes = {unit.get("text_mode") for unit in group_units}
        if len(signatures) != 1 or len(roles) != 1 or len(modes) != 1:
            errors.append(f"{path}: sibling group {group_id} under {parent_node_id} must use one grammar_signature, role, and text_mode")

    relation_types = {
        relation.get("type")
        for relation in logic_slide.get("semantic_relations", [])
        if isinstance(relation, dict)
    }
    has_ordered_relation = bool(relation_types & {"sequence", "transforms-to", "rank"})
    if not has_ordered_relation:
        for copy_id, unit in copy_map.items():
            text = str(unit.get("text", ""))
            if STRONG_SEQUENCE_LANGUAGE.search(text):
                errors.append(
                    f"{path}: {copy_id} introduces ordered language without a sequence, transforms-to, or rank relation"
                )

    series_review = copy_slide.get("series_copy_review")
    require_keys(
        series_review,
        {"series_id", "invariant_terms_preserved", "object_order_preserved", "new_information_explicit"},
        f"{path}.series_copy_review",
        errors,
    )
    if isinstance(series_review, dict):
        if series_review.get("series_id") != logic_slide.get("series_id"):
            errors.append(f"{path}.series_copy_review.series_id: must match Logic")
        for key in ("invariant_terms_preserved", "object_order_preserved", "new_information_explicit"):
            if series_review.get(key) is not True:
                errors.append(f"{path}.series_copy_review.{key}: must be true")


def validate_package(data: Any, require_status: str = "copy-approved") -> list[str]:
    """Validate the shared Logic contract and the Copy layer as one callable API."""
    logic_validator = _load_logic_validator()
    errors = logic_validator.validate_package(data, require_status)
    if isinstance(data, dict) and require_status == "copy-approved":
        validate_copy_layer(data, errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--require-status", choices=["draft", "logic-approved", "copy-approved"], default="copy-approved")
    args = parser.parse_args()
    try:
        data = json.loads(args.package.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read JSON: {exc}", file=sys.stderr)
        return 2
    try:
        errors = validate_package(data, args.require_status)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAILED: {len(errors)} error(s)")
        return 1
    print(f"PASS: PPT package {data.get('package_id')} ({data.get('status')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
