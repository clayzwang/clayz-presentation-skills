# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate evidence-backed release or explicitly restricted local-build state."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


READINESS_CONTRACT = "io.clayz.presentation.release-readiness/1.0"


class ReadinessError(ValueError):
    """Raised when release authorization evidence is incomplete or unsafe."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReadinessError(message)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReadinessError(f"invalid readiness evidence {path}: {exc}") from exc
    _require(isinstance(value, dict), f"readiness evidence must be an object: {path}")
    return value


def validate_release_readiness(root: Path, document: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(document, Mapping), "release readiness must be an object")
    value = dict(document)
    _require(value.get("contract") == READINESS_CONTRACT, f"readiness.contract must be {READINESS_CONTRACT}")
    current = (root / "VERSION").read_text(encoding="utf-8").strip()
    _require(value.get("target_version") == current, "readiness target_version must match VERSION")
    state = value.get("state")
    _require(state in {"release-authorized", "local-build-authorized"}, "unsupported readiness state")
    if state == "release-authorized":
        _require(value.get("current_public_version") == current, "release current_public_version must match VERSION")
    else:
        public_version = value.get("current_public_version")
        _require(isinstance(public_version, str) and public_version != current, "local build must preserve the prior public version")
    stages = value.get("stage_gates")
    _require(isinstance(stages, Mapping), "stage_gates must be an object")
    expected = {
        "index_foundation",
        "capability_integration",
        "layout_contract",
        "pattern_dataset_library",
        "feedback_benchmark_migration",
    }
    _require(set(stages) == expected and all(item is True for item in stages.values()), "all five stage gates must be true")
    actions = value.get("actions")
    _require(isinstance(actions, Mapping), "readiness.actions must be an object")
    expected_action = state == "release-authorized"
    for key in ("merge", "tag", "publish", "experience_center_update"):
        _require(actions.get(key) is expected_action, f"readiness.actions.{key} must be {expected_action}")
    authorization = value.get("authorization")
    _require(isinstance(authorization, Mapping), "readiness.authorization must be an object")
    if state == "release-authorized":
        _require(authorization.get("decision") == "explicit-user-authorization", "release requires an explicit user decision")
        _require(authorization.get("scope") == "merge-tag-publish-experience-center", "release authorization scope is incomplete")
    else:
        _require(authorization.get("decision") == "explicit-user-restriction", "local build requires an explicit no-publish restriction")
        _require(authorization.get("scope") == "local-build-no-github-push", "local build scope must forbid GitHub push")
    authorized_at = authorization.get("authorized_at")
    _require(isinstance(authorized_at, str) and authorized_at.endswith("Z"), "release authorized_at must be UTC")
    evidence = value.get("evidence")
    _require(isinstance(evidence, Mapping), "readiness.evidence must be an object")
    benchmark_path = root / str(evidence.get("benchmark_report", ""))
    migration_path = root / str(evidence.get("migration_report", ""))
    benchmark = _load_json(benchmark_path)
    migration = _load_json(migration_path)
    _require(benchmark.get("contract") == "io.clayz.presentation.retrieval-benchmark-report/1.0", "benchmark report contract is invalid")
    _require(benchmark.get("summary", {}).get("passed") is True, "retrieval benchmark must pass")
    _require(benchmark.get("summary", {}).get("snapshot_drift_count") == 0, "retrieval benchmark has snapshot drift")
    _require(migration.get("contract") == "io.clayz.presentation.legacy-index-migration-report/1.0", "migration report contract is invalid")
    if tuple(int(part) for part in current.split(".")) >= (0, 5, 0):
        for key in ("experience_validation", "presentation_overflow_check", "node_chart_build"):
            _require(isinstance(evidence.get(key), str) and evidence[key], f"readiness.evidence.{key} is required")
    guards = value.get("guards")
    _require(isinstance(guards, Mapping), "readiness.guards must be an object")
    for key in (
        "no_unlicensed_assets",
        "no_private_brand_assets",
        "no_generated_auto_admission",
        "no_automatic_aesthetic_truth",
        "release_requires_separate_human_authorization",
    ):
        _require(guards.get(key) is True, f"readiness.guards.{key} must be true")
    return {
        "target_version": value["target_version"],
        "current_public_version": value["current_public_version"],
        "state": value["state"],
        "benchmark_passed": True,
        "release_authorized": state == "release-authorized",
        "local_build_authorized": state == "local-build-authorized",
    }
