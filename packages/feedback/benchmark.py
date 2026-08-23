# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Deterministic retrieval benchmark and snapshot-drift detection."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from packages.index_runtime import CompositeIndex, validate_request


BENCHMARK_CONTRACT = "io.clayz.presentation.retrieval-benchmark/1.0"
BENCHMARK_REPORT_CONTRACT = "io.clayz.presentation.retrieval-benchmark-report/1.0"


class BenchmarkError(ValueError):
    """Raised when a benchmark specification is invalid."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BenchmarkError(message)


def _strings(value: Any, path: str) -> list[str]:
    _require(isinstance(value, list), f"{path} must be a list")
    _require(all(isinstance(item, str) and item for item in value), f"{path} must contain non-empty strings")
    _require(len(value) == len(set(value)), f"{path} must be unique")
    return list(value)


def _report_id(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"benchmark-report-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:20]}"


def _validate_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(spec, Mapping), "benchmark must be an object")
    value = copy.deepcopy(dict(spec))
    _require(value.get("contract") == BENCHMARK_CONTRACT, f"benchmark.contract must be {BENCHMARK_CONTRACT}")
    _require(isinstance(value.get("benchmark_id"), str) and value["benchmark_id"], "benchmark_id must be non-empty")
    snapshots = value.get("expected_provider_snapshots")
    _require(isinstance(snapshots, list) and snapshots, "expected_provider_snapshots must be non-empty")
    seen_providers: set[str] = set()
    for index, snapshot in enumerate(snapshots):
        path = f"expected_provider_snapshots[{index}]"
        _require(isinstance(snapshot, Mapping), f"{path} must be an object")
        provider_id = snapshot.get("provider_id")
        _require(isinstance(provider_id, str) and provider_id, f"{path}.provider_id must be non-empty")
        _require(provider_id not in seen_providers, f"duplicate provider snapshot: {provider_id}")
        seen_providers.add(provider_id)
        digest = snapshot.get("digest")
        _require(isinstance(digest, str) and len(digest) == 64, f"{path}.digest must be SHA-256")
        _require(isinstance(snapshot.get("record_count"), int) and snapshot["record_count"] >= 0, f"{path}.record_count is invalid")
    cases = value.get("cases")
    _require(isinstance(cases, list) and cases, "benchmark.cases must be non-empty")
    seen_cases: set[str] = set()
    for index, case in enumerate(cases):
        path = f"cases[{index}]"
        _require(isinstance(case, Mapping), f"{path} must be an object")
        case_id = case.get("case_id")
        _require(isinstance(case_id, str) and case_id, f"{path}.case_id must be non-empty")
        _require(case_id not in seen_cases, f"duplicate benchmark case: {case_id}")
        seen_cases.add(case_id)
        validate_request(case.get("request", {}))
        _strings(case.get("expected_candidate_ids", []), f"{path}.expected_candidate_ids")
        _strings(case.get("forbidden_candidate_ids", []), f"{path}.forbidden_candidate_ids")
        _require(case.get("expected_status") in {"matched", "unresolved"}, f"{path}.expected_status is invalid")
        _require(isinstance(case.get("top_k"), int) and 1 <= case["top_k"] <= 50, f"{path}.top_k is invalid")
    guards = value.get("guards")
    _require(isinstance(guards, Mapping), "benchmark.guards must be an object")
    _require(guards.get("fail_on_snapshot_drift") is True, "benchmark must fail on snapshot drift")
    _require(guards.get("fail_on_forbidden_candidate") is True, "benchmark must fail on forbidden candidates")
    _require(guards.get("unresolved_must_stay_empty") is True, "unresolved cases must stay empty")
    _require(guards.get("automatic_baseline_update") is False, "benchmark baseline must never auto-update")
    return value


def run_retrieval_benchmark(
    runtime: CompositeIndex,
    spec: Mapping[str, Any],
    *,
    created_at: str,
) -> dict[str, Any]:
    benchmark = _validate_spec(spec)
    actual_snapshots = runtime.snapshots()
    expected_by_id = {item["provider_id"]: item for item in benchmark["expected_provider_snapshots"]}
    actual_by_id = {item["provider_id"]: item for item in actual_snapshots}
    provider_ids = sorted(set(expected_by_id) | set(actual_by_id))
    drift = []
    for provider_id in provider_ids:
        expected = expected_by_id.get(provider_id)
        actual = actual_by_id.get(provider_id)
        if expected != actual:
            drift.append({"provider_id": provider_id, "expected": expected, "actual": actual})

    known_ids = {
        record["record_id"]
        for provider in runtime.providers
        for record in provider.records
    }
    case_reports = []
    for case in benchmark["cases"]:
        receipt = runtime.search(case["request"], created_at=created_at)
        actual_ids = [candidate["record_id"] for candidate in receipt["candidates"][: case["top_k"]]]
        expected_ids = case["expected_candidate_ids"]
        forbidden_ids = case["forbidden_candidate_ids"]
        missing = [record_id for record_id in expected_ids if record_id not in actual_ids]
        forbidden_hits = [record_id for record_id in actual_ids if record_id in forbidden_ids]
        invented = [record_id for record_id in actual_ids if record_id not in known_ids]
        actual_status = "matched" if actual_ids else "unresolved"
        reasons = []
        if missing:
            reasons.append("expected-candidate-missing")
        if forbidden_hits:
            reasons.append("forbidden-candidate-returned")
        if invented or receipt["hallucination_guard"]["invented_record_count"] != 0:
            reasons.append("invented-record-returned")
        if actual_status != case["expected_status"]:
            reasons.append("status-mismatch")
        if case["expected_status"] == "unresolved" and actual_ids:
            reasons.append("unresolved-case-not-empty")
        case_reports.append({
            "case_id": case["case_id"],
            "expected_status": case["expected_status"],
            "actual_status": actual_status,
            "top_k": case["top_k"],
            "expected_candidate_ids": expected_ids,
            "actual_candidate_ids": actual_ids,
            "missing_expected_ids": missing,
            "forbidden_hits": forbidden_hits,
            "invented_ids": invented,
            "receipt_id": receipt["receipt_id"],
            "passed": not reasons,
            "reasons": reasons,
        })

    passed_count = sum(1 for case in case_reports if case["passed"])
    overall_passed = not drift and passed_count == len(case_reports)
    seed = {"benchmark_id": benchmark["benchmark_id"], "snapshots": actual_snapshots, "cases": case_reports}
    return {
        "contract": BENCHMARK_REPORT_CONTRACT,
        "report_id": _report_id(seed),
        "benchmark_id": benchmark["benchmark_id"],
        "created_at": created_at,
        "provider_snapshots": actual_snapshots,
        "snapshot_drift": drift,
        "cases": case_reports,
        "summary": {
            "case_count": len(case_reports),
            "passed_count": passed_count,
            "failed_count": len(case_reports) - passed_count,
            "snapshot_drift_count": len(drift),
            "passed": overall_passed,
        },
        "guards": {
            "only_registered_records": True,
            "invented_record_count": sum(len(case["invented_ids"]) for case in case_reports),
            "automatic_baseline_update": False,
        },
    }
