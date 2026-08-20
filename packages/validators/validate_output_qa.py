#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate final-render QA records against package and approved Art Direction."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from compare_package_to_pptx import extract_slide, natural_slide_key
from config_policy import ValidationPolicy, load_policy
from validate_art_direction_plan import OBJECT_TYPES, STRUCTURE_TYPES, validate_plan


CONTRACT_VERSION = "3.6"
CHECK_KEYS = {
    "exact_text", "copy_id_traceability", "atomic_copy_separation",
    "parent_child_hierarchy", "peer_parallelism", "visual_hierarchy",
    "thumbnail_review", "full_size_review", "storyline_single_line",
    "list_alignment", "object_types_preserved", "icon_execution",
    "image_weight", "kpi_layout", "connectors", "collision_and_tangency",
    "notes_subordinate", "font_size_discipline", "scatter_semantics_and_labels", "grid_alignment",
    "whitespace_scale", "material_type_fit", "medium_plan_object_render_consistency",
    "anti_cardification", "art_direction_first_visual_fidelity",
    "art_direction_area_plan_fidelity", "art_direction_rhythm_fidelity",
    "purposeful_series_fidelity", "cross_slide_invariant_fidelity",
    "semantic_whitespace_fidelity", "motif_fidelity", "context_rail_fidelity",
    "semantic_layout_tree_fidelity",
    "unapproved_deviation_absent", "master_page_number",
    "inherited_chrome_uniqueness", "closing_exact",
}
SEQUENCE_EVIDENCE_KEYS = {
    "planned_series_id_repeated", "planned_series_behavior_repeated",
    "planned_motif_id_repeated", "planned_whitespace_mode_repeated",
    "series_backbone_observed", "motif_observed", "semantic_whitespace_observed",
    "context_rail_observed",
}
SEMANTIC_TREE_EVIDENCE_KEYS = {
    "planned_tree_id_repeated", "planned_tree_mode_repeated", "observed_grouping",
    "observed_reading_order", "observed_shape_semantics", "flattening_detected", "evidence",
}
CHECK_STATUS = {"pass", "not-applicable"}
qa_path_parent = Path.cwd()


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def require_keys(obj: Any, keys: set[str], path: str, errors: list[str]) -> None:
    if not isinstance(obj, dict):
        errors.append(f"{path}: must be an object")
        return
    missing = sorted(keys - set(obj))
    if missing:
        errors.append(f"{path}: missing keys {missing}")


def pptx_inventories(pptx: Path) -> list[dict[str, int]]:
    with zipfile.ZipFile(pptx) as archive:
        slide_names = sorted(
            [name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)],
            key=natural_slide_key,
        )
        return [extract_slide(archive.read(name))[2] for name in slide_names]


def validate_final_cjk_evidence(qa: dict[str, Any], pptx: Path, errors: list[str]) -> None:
    for key in ("font_environment_report", "cjk_render_report", "final_reopen_render_root"):
        if not nonempty(qa.get(key)):
            errors.append(f"qa.{key}: must be a non-empty path")
    if qa.get("final_reopen_cjk_render_reviewed") != "pass":
        errors.append("qa.final_reopen_cjk_render_reviewed: must be pass")
    if errors and any(error.startswith("qa.font_environment_report") or error.startswith("qa.cjk_render_report") for error in errors):
        return
    font_path = Path(qa.get("font_environment_report", ""))
    cjk_path = Path(qa.get("cjk_render_report", ""))
    if not font_path.is_absolute():
        font_path = qa_path_parent / font_path
    if not cjk_path.is_absolute():
        cjk_path = qa_path_parent / cjk_path
    try:
        font = json.loads(font_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"qa.font_environment_report: cannot read evidence: {exc}")
        font = {}
    try:
        cjk = json.loads(cjk_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"qa.cjk_render_report: cannot read evidence: {exc}")
        cjk = {}
    for key in ("ok", "font_identity_ok", "cjk_glyphs_ok", "render_active"):
        if font.get(key) is not True:
            errors.append(f"qa.font_environment_report.{key}: must be true")
    if cjk.get("ok") is not True or cjk.get("final_pptx_reopened") is not True:
        errors.append("qa.cjk_render_report: must prove a successful final-PPTX reopen render")
    expected_hash = cjk.get("pptx_sha256")
    if nonempty(expected_hash):
        import hashlib
        actual_hash = hashlib.sha256(pptx.read_bytes()).hexdigest()
        if expected_hash != actual_hash:
            errors.append("qa.cjk_render_report.pptx_sha256: does not match final PPTX")
    else:
        errors.append("qa.cjk_render_report.pptx_sha256: must be non-empty")
    slides = cjk.get("slides")
    if not isinstance(slides, list) or not slides:
        errors.append("qa.cjk_render_report.slides: must be a non-empty array")
    else:
        failed = [item.get("slide_number") for item in slides if isinstance(item, dict) and item.get("cjk_text_shape_count", 0) > 0 and item.get("status") != "pass"]
        if failed:
            errors.append(f"qa.cjk_render_report.slides: CJK pixel probe did not pass slides {failed}")


def validate_qa(
    package: Any,
    plan: Any,
    qa: Any,
    render_root: Path | None = None,
    pptx: Path | None = None,
    policy: ValidationPolicy | None = None,
) -> list[str]:
    policy = policy or load_policy()
    errors = validate_plan(package, plan, policy)
    require_keys(
        qa,
        {"contract_version", "package_id", "package_version", "art_direction_plan_contract_version", "communication_contract_reviewed", "typography_contract_reviewed", "legibility_audit_reviewed", "font_environment_report", "cjk_render_report", "final_reopen_render_root", "final_reopen_cjk_render_reviewed", "delivery_profile", "size_audit_report", "size_audit_reviewed", "size_budget_exception_reason", "slides"},
        "$qa",
        errors,
    )
    if not isinstance(package, dict) or not isinstance(plan, dict) or not isinstance(qa, dict):
        return errors
    inventories: list[dict[str, int]] = []
    if pptx is None:
        errors.append("qa validation requires final PPTX object evidence")
    else:
        try:
            inventories = pptx_inventories(pptx)
        except (OSError, zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
            errors.append(f"qa PPTX evidence cannot be inspected: {exc}")
        validate_final_cjk_evidence(qa, pptx, errors)
    if qa.get("contract_version") != CONTRACT_VERSION:
        errors.append(f"qa.contract_version: expected {CONTRACT_VERSION}")
    if qa.get("package_id") != package.get("package_id") or qa.get("package_version") != package.get("version"):
        errors.append("qa package identity/version must match package")
    if qa.get("art_direction_plan_contract_version") != plan.get("contract_version"):
        errors.append("qa.art_direction_plan_contract_version: must match plan")
    profile = qa.get("delivery_profile")
    if profile not in {"lightweight", "balanced", "high-fidelity"}:
        errors.append("qa.delivery_profile: invalid value")
    if qa.get("size_audit_reviewed") != "pass":
        errors.append("qa.size_audit_reviewed: must be pass")
    size_report_name = qa.get("size_audit_report")
    if not nonempty(size_report_name):
        errors.append("qa.size_audit_report: must be non-empty")
    elif pptx is not None:
        size_path = qa_path_parent / size_report_name
        try:
            size_report = json.loads(size_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"qa.size_audit_report: cannot load report: {exc}")
        else:
            import hashlib
            expected_hash = hashlib.sha256(pptx.read_bytes()).hexdigest()
            if size_report.get("pptx_sha256") != expected_hash:
                errors.append("qa.size_audit_report.pptx_sha256: does not match final PPTX")
            if size_report.get("delivery_profile") != profile:
                errors.append("qa.size_audit_report.delivery_profile: must match QA")
            if size_report.get("ok") is not True or size_report.get("blockers"):
                errors.append("qa.size_audit_report: blockers must be empty and ok must be true")
            above_budget = any(
                isinstance(item, dict) and item.get("code") == "ABOVE_PREFERRED_TOTAL_SIZE"
                for item in size_report.get("warnings", [])
            )
            reason = qa.get("size_budget_exception_reason")
            if above_budget and not nonempty(reason):
                errors.append("qa.size_budget_exception_reason: required when above preferred total size")
            if not above_budget and reason is not None:
                errors.append("qa.size_budget_exception_reason: must be null when within preferred total size")
    for key in ("communication_contract_reviewed", "typography_contract_reviewed", "legibility_audit_reviewed"):
        if qa.get(key) != "pass":
            errors.append(f"qa.{key}: must be pass")

    logic_slides = package.get("logic_layer", {}).get("slides", [])
    copy_slides = package.get("copy_layer", {}).get("slides", [])
    qa_slides = qa.get("slides")
    if not isinstance(qa_slides, list):
        errors.append("qa.slides: must be an array")
        return errors
    expected_order = [slide.get("slide_id") for slide in logic_slides]
    if [slide.get("slide_id") for slide in qa_slides if isinstance(slide, dict)] != expected_order:
        errors.append("qa.slides: order must exactly match package")

    evidence_seen: set[str] = set()
    plan_slides = plan.get("slides", [])
    if inventories and len(inventories) != len(logic_slides):
        errors.append(f"qa PPTX evidence: expected {len(logic_slides)} slides, found {len(inventories)}")
    for index, (logic_slide, copy_slide, plan_slide, qa_slide) in enumerate(zip(logic_slides, copy_slides, plan_slides, qa_slides)):
        path = f"qa.slides[{index}]"
        require_keys(
            qa_slide,
            {"slide_id", "render_file", "logic_statement_repeated", "rendered_copy_ids", "planned_structure_type_repeated", "actual_object_inventory", "rendered_structure_type", "rendered_medium_evidence", "legibility_evidence", "scatter_evidence", "sequence_render_evidence", "semantic_tree_render_evidence", "checks", "not_applicable_reasons", "issues_remaining", "review_evidence"},
            path,
            errors,
        )
        if not isinstance(qa_slide, dict):
            continue
        if qa_slide.get("slide_id") != logic_slide.get("slide_id"):
            errors.append(f"{path}.slide_id: mismatch")
        if qa_slide.get("logic_statement_repeated") != logic_slide.get("logic_map", {}).get("statement"):
            errors.append(f"{path}.logic_statement_repeated: must be verbatim")
        expected_copy_ids = [unit.get("copy_id") for unit in sorted(copy_slide.get("copy_units", []), key=lambda item: item.get("order", 0))]
        if qa_slide.get("rendered_copy_ids") != expected_copy_ids:
            errors.append(f"{path}.rendered_copy_ids: must exactly match Copy order")
        medium = plan_slide.get("medium_execution_contract", {})
        planned_structure = medium.get("structure_type")
        if qa_slide.get("planned_structure_type_repeated") != planned_structure:
            errors.append(f"{path}.planned_structure_type_repeated: must match Art Direction plan")
        actual_inventory = qa_slide.get("actual_object_inventory")
        if not isinstance(actual_inventory, dict) or set(actual_inventory) != OBJECT_TYPES or any(not isinstance(value, int) or value < 0 for value in actual_inventory.values()):
            errors.append(f"{path}.actual_object_inventory: must contain exact non-negative counts for {sorted(OBJECT_TYPES)}")
        elif index < len(inventories) and actual_inventory != inventories[index]:
            errors.append(f"{path}.actual_object_inventory: must match final PPTX object evidence")
        rendered_structure = qa_slide.get("rendered_structure_type")
        if rendered_structure not in STRUCTURE_TYPES:
            errors.append(f"{path}.rendered_structure_type: invalid value")
        rendered_medium_evidence = qa_slide.get("rendered_medium_evidence")
        if not nonempty(rendered_medium_evidence) or len(rendered_medium_evidence.strip()) < 20:
            errors.append(f"{path}.rendered_medium_evidence: must be specific evidence of at least 20 characters")
        legibility = qa_slide.get("legibility_evidence")
        require_keys(
            legibility,
            {"minimum_audience_text_pt", "chart_text_minimum_pt", "below_minimum_items", "nonconforming_size_items", "evidence"},
            f"{path}.legibility_evidence",
            errors,
        )
        is_body = logic_slide.get("narrative_role") not in {"cover", "closing"}
        if isinstance(legibility, dict):
            minimum_pt = legibility.get("minimum_audience_text_pt")
            below = legibility.get("below_minimum_items")
            nonconforming = legibility.get("nonconforming_size_items")
            if is_body and (
                not isinstance(minimum_pt, (int, float))
                or minimum_pt < policy.audience_minimum_pt
                or not policy.size_conforms(minimum_pt)
            ):
                errors.append(
                    f"{path}.legibility_evidence.minimum_audience_text_pt: body slides must meet configured minimum and size-token policy"
                )
            if not isinstance(below, list) or below:
                errors.append(f"{path}.legibility_evidence.below_minimum_items: must be an empty array")
            if not isinstance(nonconforming, list) or nonconforming:
                errors.append(f"{path}.legibility_evidence.nonconforming_size_items: must be an empty array")
            if not nonempty(legibility.get("evidence")) or len(legibility.get("evidence", "").strip()) < 12:
                errors.append(f"{path}.legibility_evidence.evidence: must contain specific evidence")
            planned_chart = medium.get("data_chart_contract") if isinstance(medium, dict) else None
            chart_min = legibility.get("chart_text_minimum_pt")
            if isinstance(planned_chart, dict):
                required_chart_min = planned_chart.get("audience_text_min_pt", policy.chart_minimum_pt)
                if not isinstance(chart_min, (int, float)) or chart_min < required_chart_min or not policy.size_conforms(chart_min):
                    errors.append(f"{path}.legibility_evidence.chart_text_minimum_pt: must meet configured chart minimum and size-token policy")
            elif chart_min is not None:
                errors.append(f"{path}.legibility_evidence.chart_text_minimum_pt: non-data-chart slides must use null")

        planned_chart = medium.get("data_chart_contract") if isinstance(medium, dict) else None
        is_scatter = isinstance(planned_chart, dict) and planned_chart.get("chart_type") == "scatter"
        scatter = qa_slide.get("scatter_evidence")
        require_keys(
            scatter,
            {"applicable", "point_count", "direct_label_count", "unreadable_or_colliding_labels", "unjustified_point_connection_count", "semantic_lines", "label_collision_resolution"},
            f"{path}.scatter_evidence",
            errors,
        )
        if isinstance(scatter, dict):
            if scatter.get("applicable") is not is_scatter:
                errors.append(f"{path}.scatter_evidence.applicable: must match the Art Direction chart type")
            for key in ("point_count", "direct_label_count", "unjustified_point_connection_count"):
                if not isinstance(scatter.get(key), int) or scatter.get(key, -1) < 0:
                    errors.append(f"{path}.scatter_evidence.{key}: must be a non-negative integer")
            collisions = scatter.get("unreadable_or_colliding_labels")
            if not isinstance(collisions, list):
                errors.append(f"{path}.scatter_evidence.unreadable_or_colliding_labels: must be an array")
            semantic_lines = scatter.get("semantic_lines")
            if not isinstance(semantic_lines, list):
                errors.append(f"{path}.scatter_evidence.semantic_lines: must be an array")
                semantic_lines = []
            if is_scatter:
                if scatter.get("point_count", 0) <= 0:
                    errors.append(f"{path}.scatter_evidence.point_count: scatter must contain at least one point")
                if scatter.get("direct_label_count") != scatter.get("point_count"):
                    errors.append(f"{path}.scatter_evidence.direct_label_count: must equal point_count")
                if collisions:
                    errors.append(f"{path}.scatter_evidence.unreadable_or_colliding_labels: must be empty")
                if scatter.get("unjustified_point_connection_count") != 0:
                    errors.append(f"{path}.scatter_evidence.unjustified_point_connection_count: must be 0")
                if not nonempty(scatter.get("label_collision_resolution")) or scatter.get("label_collision_resolution") == "not-applicable":
                    errors.append(f"{path}.scatter_evidence.label_collision_resolution: scatter requires a concrete resolution")
                expected_lines = {
                    (line.get("line_id"), line.get("visible_label"))
                    for line in planned_chart.get("semantic_lines", [])
                    if isinstance(line, dict)
                }
                observed_lines = set()
                for line_index, line in enumerate(semantic_lines):
                    lpath = f"{path}.scatter_evidence.semantic_lines[{line_index}]"
                    require_keys(line, {"line_id", "visible_label"}, lpath, errors)
                    if isinstance(line, dict):
                        observed_lines.add((line.get("line_id"), line.get("visible_label")))
                if observed_lines != expected_lines:
                    errors.append(f"{path}.scatter_evidence.semantic_lines: must match Art Direction line IDs and visible labels")
            else:
                if any(scatter.get(key) != 0 for key in ("point_count", "direct_label_count", "unjustified_point_connection_count")):
                    errors.append(f"{path}.scatter_evidence: non-scatter slides require zero counts")
                if collisions or semantic_lines:
                    errors.append(f"{path}.scatter_evidence: non-scatter slides require empty label and line arrays")
                if scatter.get("label_collision_resolution") != "not-applicable":
                    errors.append(f"{path}.scatter_evidence.label_collision_resolution: non-scatter slides must use not-applicable")
        sequence_evidence = qa_slide.get("sequence_render_evidence")
        require_keys(sequence_evidence, SEQUENCE_EVIDENCE_KEYS, f"{path}.sequence_render_evidence", errors)
        if isinstance(sequence_evidence, dict):
            series_contract = plan_slide.get("series_visual_contract", {})
            whitespace = plan_slide.get("semantic_whitespace", {})
            repeated = {
                "planned_series_id_repeated": series_contract.get("series_id"),
                "planned_series_behavior_repeated": series_contract.get("behavior"),
                "planned_motif_id_repeated": plan_slide.get("motif_id"),
                "planned_whitespace_mode_repeated": whitespace.get("mode"),
            }
            for key, expected in repeated.items():
                if sequence_evidence.get(key) != expected:
                    errors.append(f"{path}.sequence_render_evidence.{key}: must match Art Direction")
            for key in (
                "series_backbone_observed", "motif_observed",
                "semantic_whitespace_observed", "context_rail_observed",
            ):
                if not nonempty(sequence_evidence.get(key)) or len(sequence_evidence.get(key, "").strip()) < 12:
                    errors.append(f"{path}.sequence_render_evidence.{key}: must contain specific rendered evidence")
        semantic_evidence = qa_slide.get("semantic_tree_render_evidence")
        require_keys(semantic_evidence, SEMANTIC_TREE_EVIDENCE_KEYS, f"{path}.semantic_tree_render_evidence", errors)
        if isinstance(semantic_evidence, dict):
            planned_tree = plan_slide.get("semantic_layout_tree", {})
            if semantic_evidence.get("planned_tree_id_repeated") != planned_tree.get("tree_id"):
                errors.append(f"{path}.semantic_tree_render_evidence.planned_tree_id_repeated: must match Art Direction")
            if semantic_evidence.get("planned_tree_mode_repeated") != planned_tree.get("mode"):
                errors.append(f"{path}.semantic_tree_render_evidence.planned_tree_mode_repeated: must match Art Direction")
            for key in ("observed_grouping", "observed_reading_order", "observed_shape_semantics", "evidence"):
                if not nonempty(semantic_evidence.get(key)) or len(semantic_evidence.get(key, "").strip()) < 12:
                    errors.append(f"{path}.semantic_tree_render_evidence.{key}: must contain specific rendered evidence")
            if not isinstance(semantic_evidence.get("flattening_detected"), bool):
                errors.append(f"{path}.semantic_tree_render_evidence.flattening_detected: must be boolean")
        render_file = qa_slide.get("render_file")
        if not nonempty(render_file):
            errors.append(f"{path}.render_file: must be non-empty")
        elif render_root is not None and not (render_root / render_file).is_file():
            errors.append(f"{path}.render_file: file not found under render root")

        checks = qa_slide.get("checks")
        require_keys(checks, CHECK_KEYS, f"{path}.checks", errors)
        reasons = qa_slide.get("not_applicable_reasons")
        if not isinstance(reasons, dict):
            errors.append(f"{path}.not_applicable_reasons: must be an object")
            reasons = {}
        if isinstance(checks, dict):
            unknown = sorted(set(checks) - CHECK_KEYS)
            if unknown:
                errors.append(f"{path}.checks: unknown checks {unknown}")
            for key in CHECK_KEYS:
                value = checks.get(key)
                if value not in CHECK_STATUS:
                    errors.append(f"{path}.checks.{key}: must be pass or not-applicable")
                elif value == "not-applicable" and not nonempty(reasons.get(key)):
                    errors.append(f"{path}.not_applicable_reasons.{key}: required")
                elif value == "pass" and key in reasons:
                    errors.append(f"{path}.not_applicable_reasons.{key}: remove reason for passed check")
            if checks.get("medium_plan_object_render_consistency") == "pass" and rendered_structure != planned_structure:
                errors.append(f"{path}.checks.medium_plan_object_render_consistency: cannot pass when rendered structure differs from plan")
            if checks.get("anti_cardification") == "pass" and rendered_structure == "cards" and planned_structure != "cards":
                errors.append(f"{path}.checks.anti_cardification: cannot pass when a non-card plan renders as cards")
            if checks.get("semantic_layout_tree_fidelity") == "pass" and isinstance(semantic_evidence, dict) and semantic_evidence.get("flattening_detected") is not False:
                errors.append(f"{path}.checks.semantic_layout_tree_fidelity: cannot pass when hierarchy flattening is observed or uncertain")
            if is_body:
                for key in (
                    "font_size_discipline",
                    "object_types_preserved", "medium_plan_object_render_consistency", "anti_cardification",
                    "art_direction_first_visual_fidelity", "art_direction_area_plan_fidelity",
                    "art_direction_rhythm_fidelity", "purposeful_series_fidelity",
                    "cross_slide_invariant_fidelity", "semantic_whitespace_fidelity",
                    "motif_fidelity", "context_rail_fidelity", "semantic_layout_tree_fidelity", "unapproved_deviation_absent",
                    "master_page_number", "inherited_chrome_uniqueness",
                ):
                    if checks.get(key) != "pass":
                        errors.append(f"{path}.checks.{key}: body slides must pass this check")
            if is_scatter and checks.get("scatter_semantics_and_labels") != "pass":
                errors.append(f"{path}.checks.scatter_semantics_and_labels: scatter slides must pass this check")
            if not is_scatter and checks.get("scatter_semantics_and_labels") != "not-applicable":
                errors.append(f"{path}.checks.scatter_semantics_and_labels: non-scatter slides must be not-applicable")
        if not isinstance(qa_slide.get("issues_remaining"), list) or qa_slide.get("issues_remaining"):
            errors.append(f"{path}.issues_remaining: must be an empty array")
        evidence = qa_slide.get("review_evidence")
        if not nonempty(evidence) or len(evidence.strip()) < 20:
            errors.append(f"{path}.review_evidence: must be a specific record of at least 20 characters")
        else:
            folded = evidence.casefold()
            if isinstance(checks, dict) and checks.get("master_page_number") == "pass" and not any(
                marker in folded for marker in ("页码", "page number", "slide number")
            ):
                errors.append(f"{path}.review_evidence: passed master_page_number must cite the rendered page number check")
            if isinstance(checks, dict) and checks.get("inherited_chrome_uniqueness") == "pass":
                has_line = any(marker in folded for marker in ("标题线", "分隔线", "页眉", "title divider", "header rule"))
                has_unique = any(marker in folded for marker in ("唯一", "单一", "only", "single"))
                if not has_line or not has_unique:
                    errors.append(f"{path}.review_evidence: passed inherited_chrome_uniqueness must cite the unique inherited title-divider check")
            if isinstance(checks, dict) and checks.get("font_size_discipline") == "pass" and not any(
                marker in folded for marker in ("字号", "字体大小", "font size", "minimum text", "minimum type")
            ):
                errors.append(f"{path}.review_evidence: passed font_size_discipline must cite the rendered font-size check")
            if isinstance(checks, dict) and checks.get("scatter_semantics_and_labels") == "pass":
                has_label = any(marker in folded for marker in ("实体标签", "实体名", "direct label", "entity label"))
                has_line = any(marker in folded for marker in ("连线", "阈值线", "参考线", "point connection", "semantic line"))
                if not has_label or not has_line:
                    errors.append(f"{path}.review_evidence: passed scatter check must cite both entity labels and line semantics")
            if evidence in evidence_seen:
                errors.append(f"{path}.review_evidence: duplicate boilerplate across slides")
            else:
                evidence_seen.add(evidence)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("qa", type=Path)
    parser.add_argument("--render-root", type=Path)
    parser.add_argument("--pptx", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    try:
        package = json.loads(args.package.read_text(encoding="utf-8"))
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        qa = json.loads(args.qa.read_text(encoding="utf-8"))
        global qa_path_parent
        qa_path_parent = args.qa.resolve().parent
        errors = validate_qa(package, plan, qa, args.render_root, args.pptx, load_policy(args.config))
    except (OSError, json.JSONDecodeError, FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAILED: {len(errors)} error(s)")
        return 1
    print(f"PASS: final QA {qa.get('package_id')} ({len(qa.get('slides', []))} slides)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
