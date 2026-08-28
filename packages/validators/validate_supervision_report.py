#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate a PPT supervision report and enforce deterministic cross-layer findings."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from config_policy import ValidationPolicy, load_policy
from index_evidence import index_lock_signature, validate_index_evidence
from resource_inventory import resource_inventory_signature, validate_resource_usage
import validate_output_qa as output_qa_validator

CONTRACT_VERSION = "2.9"
RUN_STATUS = {"clean", "issues-found", "incomplete-evidence"}
CHECK_STATUS = {"pass", "fail", "not-applicable", "uncertain"}
CHECK_KEYS = {
    "logic_copy_fidelity", "copy_art_direction_fidelity", "art_direction_build_fidelity",
    "art_direction_first_visual_fidelity", "art_direction_area_plan_fidelity",
    "plan_object_fidelity", "object_render_fidelity", "art_direction_rhythm_fidelity",
    "purposeful_series_fidelity", "cross_slide_invariant_fidelity",
    "semantic_whitespace_fidelity", "motif_fidelity", "context_rail_fidelity",
    "deviation_authorization", "qa_truthfulness", "anti_cardification",
    "target_app_compatibility", "inherited_chrome_fidelity",
    "typography_legibility", "scatter_semantics_and_labels",
    "semantic_layout_tree_fidelity", "visual_self_correction_integrity",
}
MEDIA_LABELS = {
    "typography", "data-chart", "table", "timeline", "swimlane", "matrix",
    "relationship-diagram", "process", "photo-or-screenshot",
    "scenario-illustration", "cards", "columns", "mixed", "other", "not-reviewed",
}
SEVERITIES = {"critical", "major", "moderate", "minor"}
OWNERS = {"logic", "copy", "art-direction", "output-build", "output-qa", "interface", "system"}
CONFIDENCE = {"high", "medium", "low"}
REQUIRED_INVENTORY = {
    "shapes", "text_shapes", "connectors", "pictures", "graphic_frames", "tables", "charts", "diagrams"
}
OBJECT_INVENTORY_MAP = {
    "shape": "shapes",
    "native-table": "tables",
    "native-chart": "charts",
    "connector": "connectors",
    "picture": "pictures",
    "diagram": "diagrams",
}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def require_keys(obj: Any, keys: set[str], path: str, errors: list[str]) -> None:
    if not isinstance(obj, dict):
        errors.append(f"{path}: must be an object")
        return
    missing = sorted(keys - set(obj))
    if missing:
        errors.append(f"{path}: missing keys {missing}")


def target_counts(slide: dict[str, Any]) -> dict[str, int]:
    result = {"shape": 0, "table-cell": 0, "chart-label": 0}
    for mapping in slide.get("copy_unit_map", []):
        kind = mapping.get("target_type") if isinstance(mapping, dict) else None
        if kind in result:
            result[kind] += 1
    return result


def area_signature(slide: dict[str, Any]) -> str:
    parts: list[str] = []
    for region in slide.get("area_plan", []):
        if isinstance(region, dict):
            parts.append(f"{region.get('region_id')}:{region.get('share_percent')}")
    return "; ".join(parts)


def issue_lookup(issues: list[dict[str, Any]]) -> set[tuple[str, Any]]:
    return {(item.get("finding_code"), item.get("slide_id")) for item in issues if isinstance(item, dict)}


def register_check_evidence(
    evidence: Any,
    slide_id: Any,
    path: str,
    seen: dict[str, str],
    errors: list[str],
) -> None:
    """Reject short, anonymous, or repeated check evidence."""

    if not nonempty(evidence) or len(str(evidence).strip()) < 16:
        errors.append(f"{path}: must be substantive and at least 16 characters")
        return
    normalized = " ".join(str(evidence).casefold().split())
    if nonempty(slide_id) and str(slide_id).casefold() not in normalized:
        errors.append(f"{path}: must cite the stable slide_id")
    if normalized in seen:
        errors.append(f"{path}: duplicate boilerplate already used at {seen[normalized]}")
        return
    seen[normalized] = path


def missing_required_object_types(execution: Any, actual: Any) -> list[str]:
    """Return planned object types whose actual inventory is below the hard minimum."""

    if not isinstance(execution, dict) or not isinstance(actual, dict):
        return []
    missing: list[str] = []
    minimums = execution.get("minimum_object_counts")
    if not isinstance(minimums, dict):
        return missing
    for object_type, minimum in minimums.items():
        inventory_key = OBJECT_INVENTORY_MAP.get(object_type)
        if not inventory_key or not isinstance(minimum, int) or minimum < 0:
            continue
        observed = actual.get(inventory_key)
        if not isinstance(observed, int) or observed < minimum:
            missing.append(object_type)
    return sorted(missing)


def validate_report(
    package: Any,
    plan: Any,
    qa: Any,
    inventory: Any,
    report: Any,
    policy: ValidationPolicy | None = None,
    pptx: Path | None = None,
    render_root: Path | None = None,
) -> list[str]:
    policy = policy or load_policy()
    errors: list[str] = output_qa_validator.validate_qa(
        package,
        plan,
        qa,
        render_root=render_root,
        pptx=pptx,
        policy=policy,
    )
    require_keys(report, {
        "contract_version", "package_id", "package_version", "art_direction_plan_contract_version",
        "output_qa_contract_version", "supervised_at", "run_status", "artifact_paths", "slides",
        "issues", "deck_findings", "responsibility_attribution", "recommendations", "delivery_efficiency", "index_evidence", "resource_usage",
    }, "$report", errors)
    if not all(isinstance(item, dict) for item in (package, plan, qa, inventory, report)):
        return errors
    if report.get("contract_version") != CONTRACT_VERSION:
        errors.append(f"report.contract_version: expected {CONTRACT_VERSION}")
    if report.get("package_id") != package.get("package_id") or report.get("package_version") != package.get("version"):
        errors.append("report package identity/version must match package")
    if report.get("art_direction_plan_contract_version") != plan.get("contract_version"):
        errors.append("report.art_direction_plan_contract_version: must match plan")
    if report.get("output_qa_contract_version") != qa.get("contract_version"):
        errors.append("report.output_qa_contract_version: must match QA")
    expected_resource_lock = resource_inventory_signature(package.get("resource_inventory"))
    if qa.get("resource_inventory_lock") != expected_resource_lock:
        errors.append("qa.resource_inventory_lock: must preserve the pre-Logic inventory")
    validate_resource_usage(
        report.get("resource_usage"),
        package.get("resource_inventory"),
        "report.resource_usage",
        errors,
    )
    validate_index_evidence(
        report.get("index_evidence"),
        ["logic", "copy", "art-direction", "output", "supervisor"],
        "report.index_evidence",
        errors,
    )
    if index_lock_signature(report.get("index_evidence")) != index_lock_signature(qa.get("index_evidence")):
        errors.append("report.index_evidence: must preserve the Output QA Provider lock and owner materialization")
    if report.get("run_status") not in RUN_STATUS:
        errors.append("report.run_status: invalid value")
    if not nonempty(report.get("supervised_at")):
        errors.append("report.supervised_at: must be non-empty")
    require_keys(report.get("artifact_paths"), {
        "package", "art_direction_plan", "pptx", "render_root", "output_qa", "object_inventory", "build_deviation_log",
        "font_environment_report", "cjk_render_report", "final_reopen_render_root",
        "size_audit_report",
    }, "report.artifact_paths", errors)

    issues = report.get("issues")
    if not isinstance(issues, list):
        errors.append("report.issues: must be an array")
        issues = []
    valid_issues: list[dict[str, Any]] = []
    issue_ids: set[str] = set()
    for index, issue in enumerate(issues):
        path = f"report.issues[{index}]"
        require_keys(issue, {
            "issue_id", "finding_code", "slide_id", "severity", "owner_layer", "confidence",
            "failed_checks", "source_artifacts", "evidence", "expected", "actual", "impact",
            "recommended_change", "regression_rule",
        }, path, errors)
        if not isinstance(issue, dict):
            continue
        valid_issues.append(issue)
        issue_id = issue.get("issue_id")
        if not nonempty(issue_id) or issue_id in issue_ids:
            errors.append(f"{path}.issue_id: must be non-empty and unique")
        else:
            issue_ids.add(issue_id)
        if not nonempty(issue.get("finding_code")):
            errors.append(f"{path}.finding_code: must be non-empty")
        if issue.get("severity") not in SEVERITIES:
            errors.append(f"{path}.severity: invalid value")
        if issue.get("owner_layer") not in OWNERS:
            errors.append(f"{path}.owner_layer: invalid value")
        if issue.get("confidence") not in CONFIDENCE:
            errors.append(f"{path}.confidence: invalid value")
        if not isinstance(issue.get("failed_checks"), list) or any(key not in CHECK_KEYS for key in issue.get("failed_checks", [])):
            errors.append(f"{path}.failed_checks: invalid check reference")
        if not isinstance(issue.get("source_artifacts"), list) or not issue.get("source_artifacts"):
            errors.append(f"{path}.source_artifacts: must be a non-empty array")
        for key in ("evidence", "expected", "actual", "impact", "recommended_change", "regression_rule"):
            if not nonempty(issue.get(key)):
                errors.append(f"{path}.{key}: must be non-empty")

    cjk_qa_ok = qa.get("final_reopen_cjk_render_reviewed") == "pass"
    if not cjk_qa_ok and not any(issue.get("finding_code") == "CJK_GLYPH_RENDER_MISSING" for issue in valid_issues):
        errors.append("report.issues: missing CJK_GLYPH_RENDER_MISSING when final reopen CJK evidence is absent or failed")

    delivery = report.get("delivery_efficiency")
    require_keys(delivery, {
        "status", "profile", "total_bytes", "media_share_of_file", "blocker_count",
        "warning_count", "exception_reason", "evidence",
    }, "report.delivery_efficiency", errors)
    package_media = inventory.get("package_media")
    if not isinstance(package_media, dict):
        errors.append("inventory.package_media: independent package media evidence is required")
        package_media = {}
    if isinstance(delivery, dict):
        status = delivery.get("status")
        if status not in {"pass", "fail", "uncertain"}:
            errors.append("report.delivery_efficiency.status: invalid value")
        if status == "uncertain" and report.get("run_status") != "incomplete-evidence":
            errors.append("report.delivery_efficiency.status: uncertain requires incomplete-evidence")
        if delivery.get("profile") != qa.get("delivery_profile"):
            errors.append("report.delivery_efficiency.profile: must match Output QA")
        if delivery.get("total_bytes") != package_media.get("total_bytes"):
            errors.append("report.delivery_efficiency.total_bytes: must match independent package inventory")
        for key in ("blocker_count", "warning_count"):
            if not isinstance(delivery.get(key), int) or delivery.get(key, -1) < 0:
                errors.append(f"report.delivery_efficiency.{key}: must be a non-negative integer")
        share = delivery.get("media_share_of_file")
        if not isinstance(share, (int, float)) or share < 0 or share > 1:
            errors.append("report.delivery_efficiency.media_share_of_file: must be between 0 and 1")
        if not nonempty(delivery.get("evidence")):
            errors.append("report.delivery_efficiency.evidence: must be non-empty")
        independent_payload_issues = any(package_media.get(key) for key in (
            "duplicate_media_groups", "embedded_font_parts", "embedding_parts", "audio_video_parts",
        ))
        if status == "pass" and independent_payload_issues:
            errors.append("report.delivery_efficiency.status: cannot pass with duplicate media or embedded payloads")
        if status == "pass" and (qa.get("size_audit_reviewed") != "pass" or delivery.get("blocker_count") != 0):
            errors.append("report.delivery_efficiency.status: pass requires reviewed size audit with zero blockers")
        delivery_failure_codes = {
            "PPTX_LIGHTWEIGHT_PROFILE_MISSING", "PPTX_DUPLICATE_OR_UNUSED_MEDIA",
            "PPTX_RASTER_OVERSIZED", "PPTX_UNEXPECTED_EMBEDDED_PAYLOAD",
        }
        if status == "fail" and not any(issue.get("finding_code") in delivery_failure_codes for issue in valid_issues):
            errors.append("report.issues: delivery failure requires a PPTX delivery-efficiency finding")

    pairs = issue_lookup(valid_issues)
    package_order = [slide.get("slide_id") for slide in package.get("logic_layer", {}).get("slides", [])]
    logic_by_id = {
        slide.get("slide_id"): slide
        for slide in package.get("logic_layer", {}).get("slides", [])
        if isinstance(slide, dict)
    }
    plan_slides = plan.get("slides", [])
    qa_by_id = {slide.get("slide_id"): slide for slide in qa.get("slides", []) if isinstance(slide, dict)}
    inventory_by_id = {slide.get("slide_id"): slide for slide in inventory.get("slides", []) if isinstance(slide, dict)}
    report_slides = report.get("slides")
    if not isinstance(report_slides, list):
        errors.append("report.slides: must be an array")
        return errors
    if [slide.get("slide_id") for slide in report_slides if isinstance(slide, dict)] != package_order:
        errors.append("report.slides: order must exactly match package")

    any_uncertain = False
    check_evidence_seen: dict[str, str] = {}
    for index, (plan_slide, report_slide) in enumerate(zip(plan_slides, report_slides)):
        path = f"report.slides[{index}]"
        require_keys(report_slide, {"slide_id", "render_file", "planned", "actual_objects", "rendered", "checks"}, path, errors)
        if not isinstance(report_slide, dict):
            continue
        slide_id = report_slide.get("slide_id")
        logic_slide = logic_by_id.get(slide_id, {})
        is_body = logic_slide.get("narrative_role") not in {"cover", "closing"}
        planned = report_slide.get("planned")
        require_keys(planned, {"first_visual", "area_signature", "silhouette_family", "density_class", "dominant_medium", "structure_signature", "structure_type", "series_id", "series_behavior", "motif_id", "semantic_whitespace_mode", "context_rail_enabled", "semantic_tree_id", "semantic_tree_mode", "visual_self_correction_required", "required_object_types", "minimum_object_counts", "target_type_counts", "audience_detail_min_pt", "chart_text_min_pt", "data_chart_contract", "quantitative_execution_contract"}, f"{path}.planned", errors)
        expected_counts = target_counts(plan_slide)
        execution = plan_slide.get("medium_execution_contract", {})
        if isinstance(planned, dict):
            if planned.get("first_visual") != plan_slide.get("design_intent", {}).get("first_visual"):
                errors.append(f"{path}.planned.first_visual: must match Art Direction")
            if planned.get("area_signature") != area_signature(plan_slide):
                errors.append(f"{path}.planned.area_signature: must be derived from Art Direction area_plan")
            if planned.get("silhouette_family") != plan_slide.get("silhouette_family"):
                errors.append(f"{path}.planned.silhouette_family: must match Art Direction")
            if planned.get("density_class") != plan_slide.get("density_class"):
                errors.append(f"{path}.planned.density_class: must match Art Direction")
            if planned.get("dominant_medium") != plan_slide.get("dominant_medium"):
                errors.append(f"{path}.planned.dominant_medium: must match plan")
            if planned.get("structure_signature") != plan_slide.get("structure_signature"):
                errors.append(f"{path}.planned.structure_signature: must match plan")
            if planned.get("structure_type") != execution.get("structure_type"):
                errors.append(f"{path}.planned.structure_type: must match plan")
            series_contract = plan_slide.get("series_visual_contract", {})
            if planned.get("series_id") != series_contract.get("series_id"):
                errors.append(f"{path}.planned.series_id: must match plan")
            if planned.get("series_behavior") != series_contract.get("behavior"):
                errors.append(f"{path}.planned.series_behavior: must match plan")
            if planned.get("motif_id") != plan_slide.get("motif_id"):
                errors.append(f"{path}.planned.motif_id: must match plan")
            if planned.get("semantic_whitespace_mode") != plan_slide.get("semantic_whitespace", {}).get("mode"):
                errors.append(f"{path}.planned.semantic_whitespace_mode: must match plan")
            if planned.get("context_rail_enabled") != plan_slide.get("persistent_context_rail", {}).get("enabled"):
                errors.append(f"{path}.planned.context_rail_enabled: must match plan")
            semantic_tree = plan_slide.get("semantic_layout_tree", {})
            if planned.get("semantic_tree_id") != semantic_tree.get("tree_id"):
                errors.append(f"{path}.planned.semantic_tree_id: must match plan")
            if planned.get("semantic_tree_mode") != semantic_tree.get("mode"):
                errors.append(f"{path}.planned.semantic_tree_mode: must match plan")
            correction = plan_slide.get("ab_review", {}).get("visual_self_correction", {})
            if planned.get("visual_self_correction_required") is not correction.get("required"):
                errors.append(f"{path}.planned.visual_self_correction_required: must match plan")
            if planned.get("required_object_types") != execution.get("required_object_types"):
                errors.append(f"{path}.planned.required_object_types: must match plan")
            if planned.get("minimum_object_counts") != execution.get("minimum_object_counts"):
                errors.append(f"{path}.planned.minimum_object_counts: must match plan")
            if planned.get("target_type_counts") != expected_counts:
                errors.append(f"{path}.planned.target_type_counts: must be derived from plan")
            typography = plan.get("typography_contract", {})
            if planned.get("audience_detail_min_pt") != typography.get("audience_detail_min_pt"):
                errors.append(f"{path}.planned.audience_detail_min_pt: must match Art Direction")
            if planned.get("chart_text_min_pt") != typography.get("chart_text_min_pt"):
                errors.append(f"{path}.planned.chart_text_min_pt: must match Art Direction")
            if planned.get("data_chart_contract") != execution.get("data_chart_contract"):
                errors.append(f"{path}.planned.data_chart_contract: must match Art Direction")
            if planned.get("quantitative_execution_contract") != execution.get("quantitative_execution_contract"):
                errors.append(f"{path}.planned.quantitative_execution_contract: must match Art Direction")

        actual = report_slide.get("actual_objects")
        require_keys(actual, REQUIRED_INVENTORY, f"{path}.actual_objects", errors)
        source_inventory = inventory_by_id.get(slide_id, {}).get("inventory")
        if isinstance(actual, dict) and isinstance(source_inventory, dict):
            for key in REQUIRED_INVENTORY:
                if actual.get(key) != source_inventory.get(key):
                    errors.append(f"{path}.actual_objects.{key}: must match object inventory")
        else:
            errors.append(f"{path}.actual_objects: missing matching inventory slide")

        rendered = report_slide.get("rendered")
        require_keys(rendered, {"medium_label", "first_visual_observed", "area_plan_observed", "series_backbone_observed", "motif_observed", "semantic_whitespace_observed", "context_rail_observed", "semantic_tree_observed", "visual_self_correction_evidence_observed", "minimum_audience_text_pt_observed", "nonconforming_point_sizes_observed", "scatter_label_evidence", "scatter_line_evidence", "recognizability", "evidence"}, f"{path}.rendered", errors)
        if isinstance(rendered, dict):
            if rendered.get("medium_label") not in MEDIA_LABELS:
                errors.append(f"{path}.rendered.medium_label: invalid value")
            if rendered.get("recognizability") not in {"pass", "fail", "uncertain"}:
                errors.append(f"{path}.rendered.recognizability: invalid value")
            if rendered.get("recognizability") == "uncertain":
                any_uncertain = True
            for key in ("first_visual_observed", "area_plan_observed", "series_backbone_observed", "motif_observed", "semantic_whitespace_observed", "context_rail_observed", "semantic_tree_observed", "visual_self_correction_evidence_observed", "scatter_label_evidence", "scatter_line_evidence", "evidence"):
                if not nonempty(rendered.get(key)):
                    errors.append(f"{path}.rendered.{key}: must be non-empty")
            rendered_evidence = str(rendered.get("evidence", ""))
            if nonempty(slide_id) and slide_id.casefold() not in rendered_evidence.casefold():
                errors.append(f"{path}.rendered.evidence: must cite the stable slide_id")
            observed_min = rendered.get("minimum_audience_text_pt_observed")
            if observed_min is not None and (not isinstance(observed_min, (int, float)) or observed_min <= 0):
                errors.append(f"{path}.rendered.minimum_audience_text_pt_observed: must be null or a positive number")
            if is_body and not isinstance(observed_min, (int, float)):
                errors.append(f"{path}.rendered.minimum_audience_text_pt_observed: body slides require a measured number")
            nonconforming_sizes = rendered.get("nonconforming_point_sizes_observed")
            if not isinstance(nonconforming_sizes, list) or any(not isinstance(value, (int, float)) for value in nonconforming_sizes or []):
                errors.append(f"{path}.rendered.nonconforming_point_sizes_observed: must be a numeric array")

        checks = report_slide.get("checks")
        require_keys(checks, CHECK_KEYS, f"{path}.checks", errors)
        failed_checks: set[str] = set()
        if isinstance(checks, dict):
            unknown = set(checks) - CHECK_KEYS
            if unknown:
                errors.append(f"{path}.checks: unknown checks {sorted(unknown)}")
            for key in CHECK_KEYS:
                check = checks.get(key)
                require_keys(check, {"status", "evidence"}, f"{path}.checks.{key}", errors)
                if isinstance(check, dict):
                    status = check.get("status")
                    if status not in CHECK_STATUS:
                        errors.append(f"{path}.checks.{key}.status: invalid value")
                    elif status == "fail":
                        failed_checks.add(key)
                    elif status == "uncertain":
                        any_uncertain = True
                    register_check_evidence(
                        check.get("evidence"),
                        slide_id,
                        f"{path}.checks.{key}.evidence",
                        check_evidence_seen,
                        errors,
                    )
        covered = {
            check
            for issue in valid_issues
            if issue.get("slide_id") == slide_id
            for check in issue.get("failed_checks", [])
        }
        for check in failed_checks - covered:
            errors.append(f"{path}.checks.{check}: failed check must be covered by an issue")

        medium = plan_slide.get("dominant_medium")
        table_count = actual.get("tables", 0) if isinstance(actual, dict) else 0
        chart_count = actual.get("charts", 0) if isinstance(actual, dict) else 0
        alternative = execution.get("approved_alternative") if isinstance(execution, dict) else None
        table_alternative = isinstance(alternative, dict) and alternative.get("from_object_type") == "native-table"
        chart_alternative = isinstance(alternative, dict) and alternative.get("from_object_type") == "native-chart"
        required_codes: list[str] = []
        if medium == "table" and not table_alternative and expected_counts["table-cell"] == 0:
            required_codes.append("PLAN_TABLE_WITHOUT_TABLE_CELL")
        if medium == "table" and not table_alternative and table_count == 0:
            required_codes.append("BUILD_TABLE_MISSING")
        if medium == "data-chart" and not chart_alternative and chart_count == 0:
            required_codes.append("BUILD_CHART_MISSING")
        missing_objects = missing_required_object_types(execution, actual)
        if any(object_type not in {"native-table", "native-chart"} for object_type in missing_objects):
            required_codes.append("BUILD_REQUIRED_OBJECT_MISSING")
        if isinstance(rendered, dict) and rendered.get("recognizability") == "fail":
            required_codes.append("RENDERED_MEDIUM_UNCLEAR")
        if "art_direction_build_fidelity" in failed_checks:
            required_codes.append("ART_DIRECTION_NOT_EXECUTED")
        if "art_direction_first_visual_fidelity" in failed_checks:
            required_codes.append("ART_DIRECTION_FIRST_VISUAL_DRIFT")
        if "art_direction_area_plan_fidelity" in failed_checks:
            required_codes.append("ART_DIRECTION_AREA_PLAN_DRIFT")
        if "art_direction_rhythm_fidelity" in failed_checks:
            required_codes.append("ART_DIRECTION_RHYTHM_DRIFT")
        if "purposeful_series_fidelity" in failed_checks:
            if plan_slide.get("series_visual_contract", {}).get("series_id") is None:
                required_codes.append("UNJUSTIFIED_SILHOUETTE_REPETITION")
            else:
                required_codes.append("PURPOSEFUL_SERIES_BROKEN")
        if "cross_slide_invariant_fidelity" in failed_checks:
            required_codes.append("CROSS_SLIDE_INVARIANT_DRIFT")
        if "semantic_whitespace_fidelity" in failed_checks:
            semantic_codes = {
                ("SEMANTIC_WHITESPACE_FILLED", slide_id),
                ("ART_DIRECTION_FALSE_SEMANTIC_WHITESPACE", slide_id),
            }
            if not semantic_codes & pairs:
                errors.append(f"{path}: semantic whitespace failure requires FILLED or FALSE_CLAIM finding")
        if "motif_fidelity" in failed_checks:
            required_codes.append("MOTIF_SEQUENCE_DRIFT")
        if "context_rail_fidelity" in failed_checks:
            required_codes.append("CONTEXT_RAIL_UI_DRIFT")
        if "semantic_layout_tree_fidelity" in failed_checks:
            required_codes.append("SEMANTIC_LAYOUT_TREE_FLATTENED")
        if "visual_self_correction_integrity" in failed_checks:
            correction_codes = {
                ("VISUAL_SELF_CORRECTION_EVIDENCE_MISSING", slide_id),
                ("CANDIDATE_DIVERSITY_COLLAPSED", slide_id),
                ("AUTOMATIC_SCORE_SELECTED_LAYOUT", slide_id),
            }
            if not correction_codes & pairs:
                errors.append(f"{path}: visual self-correction failure requires missing-evidence, diversity-collapse, or automatic-score finding")
        if "deviation_authorization" in failed_checks:
            required_codes.append("BUILD_UNAPPROVED_DEVIATION")
        if "inherited_chrome_fidelity" in failed_checks:
            chrome_codes = {
                ("MASTER_PAGE_NUMBER_DUPLICATED", slide_id),
                ("TITLE_CHROME_DUPLICATED", slide_id),
            }
            if not chrome_codes & pairs:
                errors.append(f"{path}: inherited chrome failure requires page-number or title-chrome duplication finding")
        observed_min = rendered.get("minimum_audience_text_pt_observed") if isinstance(rendered, dict) else None
        observed_nonconforming = rendered.get("nonconforming_point_sizes_observed", []) if isinstance(rendered, dict) else []
        if isinstance(observed_min, (int, float)) and observed_min < policy.audience_minimum_pt:
            if "typography_legibility" not in failed_checks:
                errors.append(f"{path}.checks.typography_legibility: must fail when observed audience text is below configured minimum")
            required_codes.append("FONT_SIZE_BELOW_MINIMUM")
        if observed_nonconforming:
            if "typography_legibility" not in failed_checks:
                errors.append(f"{path}.checks.typography_legibility: must fail when nonconforming point sizes are observed")
            required_codes.append("FONT_SIZE_NONCONFORMING_TOKEN")
        if "typography_legibility" in failed_checks:
            typography_codes = {
                ("FONT_SIZE_BELOW_MINIMUM", slide_id),
                ("FONT_SIZE_NONCONFORMING_TOKEN", slide_id),
            }
            if not typography_codes & pairs:
                errors.append(f"{path}: typography failure requires a minimum-size or nonconforming-token finding")
        chart_contract = execution.get("data_chart_contract") if isinstance(execution, dict) else None
        is_scatter = isinstance(chart_contract, dict) and chart_contract.get("chart_type") == "scatter"
        if "scatter_semantics_and_labels" in failed_checks:
            scatter_codes = {
                ("SCATTER_ENTITY_LABEL_MISSING_OR_UNREADABLE", slide_id),
                ("SCATTER_UNJUSTIFIED_POINT_CONNECTIONS", slide_id),
            }
            if not scatter_codes & pairs:
                errors.append(f"{path}: scatter failure requires a label or point-connection finding")
        if not is_scatter and isinstance(checks, dict) and checks.get("scatter_semantics_and_labels", {}).get("status") == "pass":
            errors.append(f"{path}.checks.scatter_semantics_and_labels: non-scatter slides must be not-applicable")
        if is_scatter and isinstance(checks, dict) and checks.get("scatter_semantics_and_labels", {}).get("status") == "not-applicable":
            errors.append(f"{path}.checks.scatter_semantics_and_labels: scatter slides cannot be not-applicable")
        if is_body and isinstance(checks, dict) and checks.get("typography_legibility", {}).get("status") == "not-applicable":
            errors.append(f"{path}.checks.typography_legibility: body slides cannot be not-applicable")
        for code in required_codes:
            if (code, slide_id) not in pairs:
                errors.append(f"{path}: deterministic finding {code} must be reported")

        qa_checks = qa_by_id.get(slide_id, {}).get("checks", {})
        qa_rendered_structure = qa_by_id.get(slide_id, {}).get("rendered_structure_type")
        structure_divergence = qa_rendered_structure not in {None, execution.get("structure_type")}
        divergence = (
            bool(required_codes)
            or structure_divergence
            or bool(failed_checks & {
                "plan_object_fidelity", "object_render_fidelity", "semantic_whitespace_fidelity",
                "inherited_chrome_fidelity", "typography_legibility", "scatter_semantics_and_labels",
                "semantic_layout_tree_fidelity", "visual_self_correction_integrity",
            })
        )
        qa_passed_divergence = any(qa_checks.get(key) == "pass" for key in (
            "object_types_preserved", "material_type_fit", "art_direction_first_visual_fidelity",
            "art_direction_area_plan_fidelity", "art_direction_rhythm_fidelity",
            "purposeful_series_fidelity", "cross_slide_invariant_fidelity",
            "semantic_whitespace_fidelity", "motif_fidelity", "context_rail_fidelity",
            "semantic_layout_tree_fidelity",
            "unapproved_deviation_absent", "inherited_chrome_uniqueness",
            "font_size_discipline", "scatter_semantics_and_labels",
        ))
        if divergence and qa_passed_divergence and ("QA_FALSE_PASS", slide_id) not in pairs:
            errors.append(f"{path}: QA_FALSE_PASS required when QA passes an Art Direction or medium divergence")

    if valid_issues and report.get("run_status") == "clean":
        errors.append("report.run_status: cannot be clean when issues exist")
    if not valid_issues and report.get("run_status") == "issues-found":
        errors.append("report.run_status: issues-found requires at least one issue")
    if any_uncertain and report.get("run_status") != "incomplete-evidence":
        errors.append("report.run_status: uncertain evidence requires incomplete-evidence")

    attribution = report.get("responsibility_attribution")
    require_keys(attribution, {"mode", "confidence", "rationale"}, "report.responsibility_attribution", errors)
    if isinstance(attribution, dict):
        if attribution.get("confidence") not in CONFIDENCE:
            errors.append("report.responsibility_attribution.confidence: invalid value")
        if not nonempty(attribution.get("rationale")):
            errors.append("report.responsibility_attribution.rationale: must be non-empty")
        if attribution.get("mode") == "weighted":
            weights = attribution.get("weights")
            if not isinstance(weights, dict) or not weights or any(key not in OWNERS for key in weights):
                errors.append("report.responsibility_attribution.weights: invalid owner weights")
            elif any(not isinstance(value, int) or value < 0 for value in weights.values()) or sum(weights.values()) != 100:
                errors.append("report.responsibility_attribution.weights: integer weights must sum to 100")
        elif attribution.get("mode") == "qualitative":
            for key in ("primary", "secondary"):
                values = attribution.get(key)
                if not isinstance(values, list) or any(value not in OWNERS for value in values):
                    errors.append(f"report.responsibility_attribution.{key}: invalid owners")
        else:
            errors.append("report.responsibility_attribution.mode: must be weighted or qualitative")

    if not isinstance(report.get("deck_findings"), list):
        errors.append("report.deck_findings: must be an array")
    recommendations = report.get("recommendations")
    if not isinstance(recommendations, list):
        errors.append("report.recommendations: must be an array")
    else:
        for index, item in enumerate(recommendations):
            path = f"report.recommendations[{index}]"
            require_keys(item, {"priority", "target_layer", "change", "verification", "scope"}, path, errors)
            if isinstance(item, dict):
                if not isinstance(item.get("priority"), int) or item.get("priority", 0) < 1:
                    errors.append(f"{path}.priority: must be a positive integer")
                if item.get("target_layer") not in OWNERS:
                    errors.append(f"{path}.target_layer: invalid value")
                for key in ("change", "verification", "scope"):
                    if not nonempty(item.get(key)):
                        errors.append(f"{path}.{key}: must be non-empty")

    asset_observations = report.get("asset_observations")
    if asset_observations is not None:
        if not isinstance(asset_observations, list):
            errors.append("report.asset_observations: must be an array when present")
        else:
            for index, item in enumerate(asset_observations):
                path = f"report.asset_observations[{index}]"
                require_keys(item, {
                    "asset_id", "task_fit", "execution_effect", "conflict_signal",
                    "neighbor_value", "reuse_note", "evidence",
                }, path, errors)
                if not isinstance(item, dict):
                    continue
                if not nonempty(item.get("asset_id")):
                    errors.append(f"{path}.asset_id: must be non-empty")
                for key in ("task_fit", "execution_effect", "neighbor_value"):
                    value = item.get(key)
                    if not isinstance(value, int) or value < 1 or value > 5:
                        errors.append(f"{path}.{key}: must be an integer from 1 to 5")
                for key in ("conflict_signal", "reuse_note", "evidence"):
                    if not nonempty(item.get(key)):
                        errors.append(f"{path}.{key}: must be non-empty")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("qa", type=Path)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--pptx", type=Path, required=True)
    parser.add_argument("--render-root", type=Path)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    try:
        documents = [json.loads(path.read_text(encoding="utf-8")) for path in (args.package, args.plan, args.qa, args.inventory, args.report)]
        output_qa_validator.qa_path_parent = args.qa.resolve().parent
        errors = validate_report(
            *documents,
            load_policy(args.config),
            pptx=args.pptx,
            render_root=args.render_root,
        )
    except (OSError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAILED: {len(errors)} error(s)")
        return 1
    print(f"PASS: supervision report {documents[-1].get('package_id')} ({len(documents[-1].get('slides', []))} slides)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
