#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Shared validation for task-level presentation acceptance requirements."""

from __future__ import annotations

import re
import hashlib
import json
from collections.abc import Mapping
from typing import Any


CONTRACT = "io.clayz.presentation.task-acceptance/1.0"
STAGES = {"root", "logic", "copy", "art-direction", "output", "supervisor", "system"}
CATEGORIES = {"content", "narrative", "copy", "visual", "typography", "compatibility", "performance", "delivery"}
COVER_MODES = {"topic-only", "verdict-allowed", "not-applicable"}
FONT_MODES = {"configured-family", "explicit-family", "no-explicit-requirement"}
RUN_MODES = {"warm", "cold", "either"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
RELEASE_CONDITION_FIELDS = frozenset(("condition_id", "requirement_id", "statement", "source", "action"))


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require_keys(value: Any, keys: set[str], path: str, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append(f"{path}: must be an object")
        return
    missing = sorted(keys - set(value))
    if missing:
        errors.append(f"{path}: missing keys {missing}")


def validate_acceptance_contract(value: Any, path: str, errors: list[str]) -> None:
    required = {
        "contract", "requirements", "cover_policy", "narrative_policy",
        "typography_policy", "performance_budget", "contract_sha256",
    }
    _require_keys(value, required, path, errors)
    if not isinstance(value, Mapping):
        return
    if value.get("contract") != CONTRACT:
        errors.append(f"{path}.contract: expected {CONTRACT}")
    digest = value.get("contract_sha256")
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        errors.append(f"{path}.contract_sha256: must be a lowercase SHA-256")
    elif digest != acceptance_contract_digest(value):
        errors.append(f"{path}.contract_sha256: does not match the canonical acceptance contract")

    requirements = value.get("requirements")
    requirement_ids: set[str] = set()
    if not isinstance(requirements, list) or not requirements:
        errors.append(f"{path}.requirements: must be a non-empty array")
    else:
        for index, requirement in enumerate(requirements):
            rpath = f"{path}.requirements[{index}]"
            _require_keys(
                requirement,
                {"requirement_id", "category", "statement", "owner_stage", "verification_method", "blocking"},
                rpath,
                errors,
            )
            if not isinstance(requirement, Mapping):
                continue
            requirement_id = requirement.get("requirement_id")
            if not _nonempty(requirement_id) or requirement_id in requirement_ids:
                errors.append(f"{rpath}.requirement_id: must be non-empty and unique")
            else:
                requirement_ids.add(str(requirement_id))
            if requirement.get("category") not in CATEGORIES:
                errors.append(f"{rpath}.category: invalid value")
            if not _nonempty(requirement.get("statement")):
                errors.append(f"{rpath}.statement: must be non-empty")
            if requirement.get("owner_stage") not in STAGES:
                errors.append(f"{rpath}.owner_stage: invalid value")
            if not _nonempty(requirement.get("verification_method")):
                errors.append(f"{rpath}.verification_method: must be non-empty")
            if not isinstance(requirement.get("blocking"), bool):
                errors.append(f"{rpath}.blocking: must be boolean")
            if "classification" in requirement and requirement.get("classification") not in {"hard", "soft"}:
                errors.append(f"{rpath}.classification: must be hard or soft when supplied")
            if "source" in requirement and not _nonempty(requirement.get("source")):
                errors.append(f"{rpath}.source: must be non-empty when supplied")
            if "commitment_kind" in requirement and not _nonempty(requirement.get("commitment_kind")):
                errors.append(f"{rpath}.commitment_kind: must be non-empty when supplied")

    release_conditions = value.get("release_conditions", [])
    if not isinstance(release_conditions, list):
        errors.append(f"{path}.release_conditions: must be an array when supplied")
    else:
        condition_ids: set[str] = set()
        requirement_ids_for_conditions = set(requirement_ids)
        for index, condition in enumerate(release_conditions):
            cpath = f"{path}.release_conditions[{index}]"
            _require_keys(condition, set(RELEASE_CONDITION_FIELDS), cpath, errors)
            if not isinstance(condition, Mapping):
                continue
            if set(condition) != set(RELEASE_CONDITION_FIELDS):
                errors.append(f"{cpath}: fields must be exactly {sorted(RELEASE_CONDITION_FIELDS)}")
            condition_id = condition.get("condition_id")
            if not _nonempty(condition_id) or condition_id in condition_ids:
                errors.append(f"{cpath}.condition_id: must be non-empty and unique")
            else:
                condition_ids.add(str(condition_id))
            if condition.get("requirement_id") not in requirement_ids_for_conditions:
                errors.append(f"{cpath}.requirement_id: must reference an acceptance requirement")
            if not _nonempty(condition.get("statement")):
                errors.append(f"{cpath}.statement: must be non-empty")
            source = condition.get("source")
            if not _nonempty(source) or not str(source).casefold().startswith("user"):
                errors.append(f"{cpath}.source: must be an explicit user source")
            if condition.get("action") != "no-delivery":
                errors.append(f"{cpath}.action: must be no-delivery")

    cover = value.get("cover_policy")
    _require_keys(cover, {"mode", "conclusion_allowed_roles"}, f"{path}.cover_policy", errors)
    if isinstance(cover, Mapping):
        for key in ("cover_required", "closing_required"):
            if key in cover and not isinstance(cover[key], bool):
                errors.append(f"{path}.cover_policy.{key}: must be boolean")
        if cover.get("mode") not in COVER_MODES:
            errors.append(f"{path}.cover_policy.mode: invalid value")
        roles = cover.get("conclusion_allowed_roles")
        if not isinstance(roles, list) or any(not _nonempty(item) for item in roles):
            errors.append(f"{path}.cover_policy.conclusion_allowed_roles: must be a string array")

    narrative = value.get("narrative_policy")
    _require_keys(
        narrative,
        {"problem_before_recommendation", "minimum_friction_impact_pairs", "required_relation_types"},
        f"{path}.narrative_policy",
        errors,
    )
    if isinstance(narrative, Mapping):
        if not isinstance(narrative.get("problem_before_recommendation"), bool):
            errors.append(f"{path}.narrative_policy.problem_before_recommendation: must be boolean")
        pairs = narrative.get("minimum_friction_impact_pairs")
        if not isinstance(pairs, int) or pairs < 0:
            errors.append(f"{path}.narrative_policy.minimum_friction_impact_pairs: must be a non-negative integer")
        relation_types = narrative.get("required_relation_types")
        if not isinstance(relation_types, list) or len(relation_types) != len(set(relation_types)) or any(not _nonempty(item) for item in relation_types):
            errors.append(f"{path}.narrative_policy.required_relation_types: must be a unique string array")

    typography = value.get("typography_policy")
    _require_keys(typography, {"mode", "required_cjk_families", "exceptions"}, f"{path}.typography_policy", errors)
    if isinstance(typography, Mapping):
        mode = typography.get("mode")
        if mode not in FONT_MODES:
            errors.append(f"{path}.typography_policy.mode: invalid value")
        families = typography.get("required_cjk_families")
        if not isinstance(families, list) or len(families) != len(set(families)) or any(not _nonempty(item) for item in families):
            errors.append(f"{path}.typography_policy.required_cjk_families: must be a unique string array")
        elif mode != "no-explicit-requirement" and not families:
            errors.append(f"{path}.typography_policy.required_cjk_families: required by selected mode")
        if not isinstance(typography.get("exceptions"), list):
            errors.append(f"{path}.typography_policy.exceptions: must be an array")

    performance = value.get("performance_budget")
    _require_keys(
        performance,
        {
            "run_mode", "max_total_seconds", "stage_seconds", "max_receipts_per_stage",
            "max_candidates_per_stage", "max_selected_per_stage", "max_write_count",
            "max_render_count", "max_repair_count",
        },
        f"{path}.performance_budget",
        errors,
    )
    if isinstance(performance, Mapping):
        if performance.get("enforcement", "hard") not in {"advisory", "hard"}:
            errors.append(f"{path}.performance_budget.enforcement: invalid value")
        if performance.get("run_mode") not in RUN_MODES:
            errors.append(f"{path}.performance_budget.run_mode: invalid value")
        for key in (
            "max_total_seconds", "max_receipts_per_stage", "max_candidates_per_stage",
            "max_selected_per_stage", "max_write_count", "max_render_count", "max_repair_count",
        ):
            if not isinstance(performance.get(key), int) or performance.get(key, -1) < 0:
                errors.append(f"{path}.performance_budget.{key}: must be a non-negative integer")
        stages = performance.get("stage_seconds")
        required_stages = {"root", "preflight", "logic", "copy", "art-direction", "output", "supervisor", "delivery"}
        _require_keys(stages, required_stages, f"{path}.performance_budget.stage_seconds", errors)
        if isinstance(stages, Mapping):
            for key in required_stages:
                if not isinstance(stages.get(key), int) or stages.get(key, -1) < 0:
                    errors.append(f"{path}.performance_budget.stage_seconds.{key}: must be a non-negative integer")


def validate_stage_retrieval_budget(
    index_evidence: Any,
    acceptance: Any,
    stages: list[str],
    path: str,
    errors: list[str],
) -> None:
    """Enforce each acceptance budget cumulatively before a stage can be approved."""

    if not isinstance(index_evidence, Mapping) or not isinstance(acceptance, Mapping):
        return
    receipts_by_stage = index_evidence.get("stage_receipts")
    budget = acceptance.get("performance_budget")
    if not isinstance(receipts_by_stage, Mapping) or not isinstance(budget, Mapping):
        return
    # Historical contracts remain hard; new task guidance chooses advisory
    # budgets unless the user has explicitly imposed a hard limit.
    if budget.get("enforcement") == "advisory":
        return
    limits = {
        "receipts": budget.get("max_receipts_per_stage"),
        "candidates": budget.get("max_candidates_per_stage"),
        "selected": budget.get("max_selected_per_stage"),
    }
    for stage in stages:
        receipts = receipts_by_stage.get(stage)
        if not isinstance(receipts, list):
            continue
        counts = {"receipts": len(receipts), "candidates": 0, "selected": 0}
        for receipt in receipts:
            if not isinstance(receipt, Mapping):
                continue
            candidates = receipt.get("candidates")
            if isinstance(candidates, list):
                counts["candidates"] += len(candidates)
            selection = receipt.get("selection")
            selected = selection.get("selected") if isinstance(selection, Mapping) else None
            if isinstance(selected, list):
                counts["selected"] += len(selected)
        for label, count in counts.items():
            limit = limits.get(label)
            if isinstance(limit, int) and count > limit:
                errors.append(
                    f"{path}.stage_receipts.{stage}: cumulative {label} {count} exceeds stage budget {limit}"
                )


def requirement_ids(value: Any) -> set[str]:
    if not isinstance(value, Mapping) or not isinstance(value.get("requirements"), list):
        return set()
    return {
        str(item.get("requirement_id"))
        for item in value["requirements"]
        if isinstance(item, Mapping) and _nonempty(item.get("requirement_id"))
    }


def acceptance_contract_digest(value: Any) -> str:
    if not isinstance(value, Mapping):
        return ""
    canonical = dict(value)
    canonical.pop("contract_sha256", None)
    payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
