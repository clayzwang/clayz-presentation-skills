#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Regression tests for the personal presentation first-class Index gates.

These tests deliberately encode the failure modes that prompted the 2026-08-28
repair: locator-only learning, schema-complete but unconsumed Index evidence,
mechanically repeated copy, generic first visuals, shape-only pseudo charts,
missing connectors, and duplicated supervision boilerplate.
"""

from __future__ import annotations

import copy
import gzip
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = ROOT / "packages" / "validators"
for directory in (ROOT, VALIDATORS):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from packages.index_runtime.utils import sha256_json  # noqa: E402
from index_evidence import validate_index_evidence  # noqa: E402
from materialize_owner_index import MaterializationError, materialize  # noqa: E402
from validate_art_direction_plan import is_generic_first_visual  # noqa: E402
from validate_output_qa import validate_quantitative_inventory  # noqa: E402
from validate_ppt_package import validate_deck_expression_variation  # noqa: E402
from validate_supervision_report import (  # noqa: E402
    missing_required_object_types,
    register_check_evidence,
)


STAGES = ("logic", "copy", "art-direction", "output", "supervisor")
HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_D = "d" * 64


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _manifest() -> dict[str, Any]:
    source_specs = (
        ("demo-logic-learning", "jsonl", "learning", ["logic"]),
        ("demo-copy-learning", "jsonl", "learning", ["copy"]),
        ("demo-art-learning", "jsonl-gzip", "learning", ["art-direction"]),
        ("demo-visual-preferences", "json", "learning", ["art-direction"]),
        ("demo-visual-reference-index", "jsonl-gzip", "reference", ["art-direction"]),
        ("demo-purpose-index", "json", "reference", ["art-direction"]),
        ("demo-output-learning", "markdown", "learning", ["output"]),
        ("demo-reviewed-counterexamples", "json", "failure-pattern", ["supervisor"]),
    )
    knowledge_kinds = {
        "demo-logic-learning": ["private-knowledge", "method"],
        "demo-copy-learning": ["standard"],
        "demo-art-learning": ["method"],
        "demo-visual-preferences": ["preference"],
        "demo-visual-reference-index": ["template", "example"],
        "demo-purpose-index": ["method"],
        "demo-output-learning": ["standard", "method"],
        "demo-reviewed-counterexamples": ["failure-pattern"],
    }
    return {
        "contract": "io.clayz.presentation.owner-learning-sources/1.0",
        "provider_id": "task-private-learning",
        "inventory_uri": "runtime-input://resource-inventory",
        "admission_basis": "synthetic public regression fixture",
        "sources": [
            {
                "source_id": source_id,
                "library_uri": f"library://owner-learning/{source_id}",
                "format": format_name,
                "record_type": record_type,
                "stages": stages,
                "required": True,
                "purpose_tags": ["regression-fixture"],
                "knowledge_kinds": knowledge_kinds[source_id],
            }
            for source_id, format_name, record_type, stages in source_specs
        ],
    }


def _request(stage: str) -> dict[str, Any]:
    return {
        "contract": "io.clayz.presentation.retrieval-request/1.0",
        "request_id": f"regression-{stage}",
        "stage": stage,
        "query": f"consume required owner learning for {stage}",
        "rights_context": "private-runtime",
        "require_human_admission": True,
        "limit": 20,
        "filters": {
            "record_types": [],
            "provider_ids": ["task-private-learning"],
            "task_modes": [],
            "page_roles": [],
            "semantic_relations": [],
            "purpose_tags": [],
            "languages": ["zh-CN"],
            "failure_signals": [],
            "include_metadata_only": False,
        },
        "neighbor_expansion": {"physical": 0, "semantic": 0},
    }


def _valid_index_evidence() -> dict[str, Any]:
    manifest = _manifest()
    required_sources = sorted(
        str(source["source_id"])
        for source in manifest["sources"]
        if source.get("required") is True
    )
    snapshots = [
        {"provider_id": "builtin-catalog", "digest": HEX_A, "record_count": 12},
        {"provider_id": "owner-private-library", "digest": HEX_B, "record_count": 9},
        {"provider_id": "task-private-learning", "digest": HEX_D, "record_count": len(required_sources)},
    ]
    receipts: dict[str, list[dict[str, Any]]] = {}
    for stage in STAGES:
        stage_sources = sorted(
            str(source["source_id"])
            for source in manifest["sources"]
            if source.get("required") is True and stage in source.get("stages", [])
        )
        candidates = [
            {
                "record_id": f"owner.{stage}.{index}",
                "provider_id": "task-private-learning",
                "source_id": source_id,
            }
            for index, source_id in enumerate(stage_sources, 1)
        ]
        receipts[stage] = [{
            "contract": "io.clayz.presentation.retrieval-receipt/1.0",
            "receipt_id": f"receipt-{stage}",
            "created_at": "2026-08-28T08:00:00+00:00",
            "request": _request(stage),
            "index_snapshot": snapshots,
            "candidates": candidates,
            "selection": {
                "selected": [
                    {"record_id": candidate["record_id"], "reason": f"applies {candidate['source_id']} to this stage"}
                    for candidate in candidates
                ],
                "rejected": [],
            },
            "fallback": {"used": False, "reason": ""},
            "hallucination_guard": {
                "only_registered_records": True,
                "invented_record_count": 0,
                "candidate_count": len(candidates),
            },
        }]
    return {
        "contract": "io.clayz.presentation.index-execution-evidence/1.0",
        "mode": "owner-personal",
        "runtime_lock_digest": "e" * 64,
        "provider_lock": {
            "lock_id": "regression-provider-lock",
            "snapshots": snapshots,
            "lock_sha256": sha256_json(snapshots),
        },
        "owner_materialization": {
            "status": "materialized",
            "source_manifest_sha256": "f" * 64,
            "materialization_report_sha256": "1" * 64,
            "provider_id": "task-private-learning",
            "record_count": len(required_sources),
            "required_sources": [
                {"source_id": str(source["source_id"]), "stages": list(source["stages"])}
                for source in sorted(manifest["sources"], key=lambda item: str(item["source_id"]))
                if source.get("required") is True
            ],
            "materialized_source_ids": required_sources,
            "missing_source_ids": [],
        },
        "stage_receipts": receipts,
    }


def test_materialization() -> None:
    manifest = _manifest()
    with tempfile.TemporaryDirectory(prefix="clayz-index-regression-") as raw_root:
        task_root = Path(raw_root)
        bindings: dict[str, Path] = {}
        for source in manifest["sources"]:
            source_id = str(source["source_id"])
            format_name = source["format"]
            path = task_root / f"{source_id}.source"
            row = {"title": source_id, "summary": f"substantive regression learning for {source_id}"}
            if format_name == "jsonl-gzip":
                path.write_bytes(gzip.compress((json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8")))
            elif format_name == "jsonl":
                path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
            elif format_name == "json":
                path.write_text(json.dumps({"records": [row]}, ensure_ascii=False), encoding="utf-8")
            elif format_name == "markdown":
                path.write_text(f"# {source_id}\n\nSubstantive owner preference.\n", encoding="utf-8")
            else:  # pragma: no cover - the manifest validator owns this branch.
                raise AssertionError(f"unexpected format {format_name}")
            bindings[source_id] = path
        output = task_root / "provider.jsonl"
        report_path = task_root / "materialization.json"
        report = materialize(manifest, bindings, set(STAGES), output, report_path)
        _assert(report["provider_snapshot"]["record_count"] == len(bindings), "every required source must materialize")
        _assert(len(output.read_text(encoding="utf-8").splitlines()) == len(bindings), "provider rows must be complete")
        _assert(report["missing_source_ids"] == [], "complete materialization cannot report missing sources")
        missing = dict(bindings)
        missing.pop("demo-copy-learning")
        try:
            materialize(manifest, missing, set(STAGES), output, report_path)
        except MaterializationError:
            pass
        else:
            raise AssertionError("missing owner learning must fail closed")


def test_index_execution_evidence() -> None:
    evidence = _valid_index_evidence()
    errors: list[str] = []
    validate_index_evidence(evidence, STAGES, "evidence", errors)
    _assert(errors == [], f"valid first-class Index evidence must pass: {errors}")

    blocked = copy.deepcopy(evidence)
    blocked["owner_materialization"]["status"] = "blocked"
    errors = []
    validate_index_evidence(blocked, ("logic",), "evidence", errors)
    _assert(any("must materialize task-supplied owner learning" in error for error in errors), "locator-only owner source must fail")

    unconsumed = copy.deepcopy(evidence)
    art_selected = unconsumed["stage_receipts"]["art-direction"][0]["selection"]["selected"]
    unconsumed["stage_receipts"]["art-direction"][0]["selection"]["selected"] = [
        item for item in art_selected if "demo-purpose-index" not in item["reason"]
    ]
    errors = []
    validate_index_evidence(unconsumed, ("art-direction",), "evidence", errors)
    _assert(any("did not consume required owner sources" in error for error in errors), "schema-only receipt must fail")


def test_copy_variation() -> None:
    logic_slides = [{"slide_id": f"S0{index}", "series_id": None} for index in range(1, 4)]
    copy_slides: list[dict[str, Any]] = []
    for index in range(1, 4):
        copy_slides.append({
            "slide_id": f"S0{index}",
            "title_copy_id": f"T{index}",
            "storyline_copy_id": f"ST{index}",
            "audience_transition_copy_strategy": "结论在左、解释在右、底部再收束",
            "copy_units": [
                {"copy_id": f"T{index}", "role": "title", "text": f"第{index}页独立标题", "grammar_signature": "判断句"},
                {"copy_id": f"ST{index}", "role": "storyline", "text": f"第{index}页独立推进句", "grammar_signature": "因果句"},
                {"copy_id": f"I{index}", "role": "item", "text": "同一段高度重复的可见表达必须被拦截", "grammar_signature": "主谓宾"},
            ],
        })
    errors: list[str] = []
    validate_deck_expression_variation(logic_slides, copy_slides, errors)
    _assert(any("audience-transition" in error for error in errors), "repeated transition syntax must fail")
    _assert(any("complete grammar vector" in error for error in errors), "repeated grammar vector must fail")
    _assert(any("substantial visible phrase" in error for error in errors), "repeated visible phrase must fail")


def test_visual_and_output_gates() -> None:
    _assert(is_generic_first_visual("主图"), "generic first-visual placeholder must fail")
    _assert(not is_generic_first_visual("八家银行规模与增速二维位置图"), "content-specific first visual must pass")

    execution = {"minimum_object_counts": {"shape": 4, "connector": 1}}
    actual = {"shapes": 6, "connectors": 0}
    _assert(missing_required_object_types(execution, actual) == ["connector"], "zero connectors must not pass a connector plan")

    errors: list[str] = []
    validate_quantitative_inventory(
        {"encoding_mode": "native-chart"},
        {"native-chart": 0, "native-table": 0, "shape": 36},
        "S02.actual_object_inventory",
        errors,
    )
    _assert(any("native chart object" in error for error in errors), "36 shapes must not masquerade as a native chart")

    seen: dict[str, str] = {}
    errors = []
    boilerplate = "S01已按计划与最终渲染逐项复核，未见偏离。"
    register_check_evidence(boilerplate, "S01", "S01.check.one", seen, errors)
    register_check_evidence(boilerplate, "S02", "S02.check.one", seen, errors)
    _assert(any("must cite the stable slide_id" in error for error in errors), "evidence must bind its own slide")
    _assert(any("duplicate boilerplate" in error for error in errors), "duplicate evidence must fail")


def main() -> int:
    tests = (
        test_materialization,
        test_index_execution_evidence,
        test_copy_variation,
        test_visual_and_output_gates,
    )
    try:
        for test in tests:
            test()
    except (AssertionError, MaterializationError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "tests": [test.__name__ for test in tests]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
