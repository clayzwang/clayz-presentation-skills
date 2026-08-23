# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate v0.4.0 readiness without authorizing a release."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


READINESS_CONTRACT = "io.clayz.presentation.release-readiness/1.0"


class ReadinessError(ValueError):
    """Raised when the unreleased readiness evidence is incomplete or unsafe."""


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
    _require(value.get("target_version") == "0.4.0", "readiness target_version must be 0.4.0")
    current = (root / "VERSION").read_text(encoding="utf-8").strip()
    _require(value.get("current_public_version") == current == "0.3.0", "public VERSION must remain 0.3.0 during review")
    _require(value.get("state") == "draft-review", "readiness state must remain draft-review")
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
    for key in ("merge", "tag", "publish", "experience_center_update"):
        _require(actions.get(key) is False, f"readiness.actions.{key} must remain false")
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
        "current_public_version": current,
        "state": value["state"],
        "benchmark_passed": True,
        "release_authorized": False,
    }
