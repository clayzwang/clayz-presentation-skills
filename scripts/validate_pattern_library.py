#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate Stage 4 Pattern & Dataset Library contracts and fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime import IndexProvider, IndexRuntimeError  # noqa: E402
from packages.patterns import PatternLibraryError, validate_registered_library  # noqa: E402

SCHEMAS = {
    "packages/contracts/composition-pattern.schema.json": "urn:clayz:presentation:schema:composition-pattern:1.0",
    "packages/contracts/failure-pattern.schema.json": "urn:clayz:presentation:schema:failure-pattern:1.0",
    "packages/contracts/reference-record.schema.json": "urn:clayz:presentation:schema:reference-record:1.0",
    "packages/contracts/sequence-record.schema.json": "urn:clayz:presentation:schema:sequence-record:1.0",
    "packages/contracts/composition-pattern-request.schema.json": "urn:clayz:presentation:schema:composition-pattern-request:1.0",
    "packages/contracts/composition-pattern-resolution.schema.json": "urn:clayz:presentation:schema:composition-pattern-resolution:1.0",
    "packages/contracts/composition-plan.schema.json": "urn:clayz:presentation:schema:composition-plan:1.0",
    "packages/contracts/metadata-dataset-export.schema.json": "urn:clayz:presentation:schema:metadata-dataset-export:1.0",
}
CATALOG_DIRS = ["composition-patterns", "failure-patterns", "references", "sequences"]
FORBIDDEN_SUFFIXES = {
    ".pptx", ".pptm", ".potx", ".potm", ".thmx", ".ttf", ".otf", ".woff", ".woff2",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".psd",
    ".csv", ".tsv", ".parquet", ".xlsx", ".xls",
    ".ckpt", ".safetensors", ".pt", ".pth", ".onnx",
}
FORBIDDEN_BRAND_TERMS = ("平安", "ping an", "pingan")


def _fail(message: str) -> None:
    raise IndexRuntimeError(message)


def main() -> int:
    for relative, expected_id in SCHEMAS.items():
        document = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        if document.get("$schema") != "https://json-schema.org/draft/2020-12/schema" or document.get("$id") != expected_id:
            _fail(f"{relative}: unexpected schema identity")

    for name in CATALOG_DIRS:
        directory = ROOT / "catalog" / name
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix.casefold() in FORBIDDEN_SUFFIXES:
                _fail(f"Stage 4 public catalog contains forbidden asset: {path.relative_to(ROOT)}")
            if path.is_file():
                text = path.read_text(encoding="utf-8").casefold()
                if any(term in text for term in FORBIDDEN_BRAND_TERMS):
                    _fail(f"Stage 4 public catalog contains forbidden brand-specific text: {path.relative_to(ROOT)}")

    provider = IndexProvider.from_jsonl("builtin-catalog", ROOT / "catalog" / "records.jsonl")
    try:
        result = validate_registered_library(ROOT, provider)
    except PatternLibraryError as exc:
        _fail(str(exc))
    minimums = {"composition-pattern": 3, "failure-pattern": 4, "reference": 3, "sequence": 1}
    for record_type, minimum in minimums.items():
        if result["counts"].get(record_type, 0) < minimum:
            _fail(f"Stage 4 requires at least {minimum} registered {record_type} records")

    fixtures = ROOT / "examples" / "synthetic-pattern-library"
    resolution = json.loads((fixtures / "comparison-resolution.json").read_text(encoding="utf-8"))
    plan = json.loads((fixtures / "comparison-composition-plan.json").read_text(encoding="utf-8"))
    dataset = json.loads((fixtures / "metadata-dataset-export.json").read_text(encoding="utf-8"))
    unresolved = json.loads((fixtures / "unresolved-resolution.json").read_text(encoding="utf-8"))
    if resolution.get("status") != "selected" or len(resolution.get("retrieval_receipt_ids", [])) != 2:
        _fail("synthetic pattern resolution must select one pattern and bind linked failures to a second receipt")
    if plan.get("contract") != "io.clayz.presentation.composition-plan/1.0":
        _fail("synthetic composition plan has the wrong contract")
    if any(plan["layers"][key].get("input_used") for key in ("theme", "visual_variant", "layout_contract", "layout_tree", "resolved_coordinates")):
        _fail("composition compiler must not consume visual layers or coordinates")
    if not plan.get("decision", {}).get("rejected_patterns") and resolution.get("rejected_patterns"):
        _fail("composition plan lost rejected-pattern evidence")
    if dataset.get("contract") != "io.clayz.presentation.metadata-dataset-export/1.0" or len(dataset.get("records", [])) < 11:
        _fail("metadata dataset fixture is incomplete")
    guards = dataset.get("guards", {})
    if not all(guards.get(key) is True for key in ("metadata_only", "no_asset_bytes", "no_raw_source_text", "no_coordinates", "no_fonts", "no_model_weights")):
        _fail("metadata dataset export boundary is incomplete")
    if guards.get("generated_artifacts_auto_admitted") is not False or guards.get("automatic_aesthetic_truth") is not False:
        _fail("metadata dataset export must reject automatic admission and aesthetic truth")
    if unresolved.get("status") != "unresolved" or not unresolved.get("fallback", {}).get("used"):
        _fail("no-match pattern fixture must remain explicitly unresolved")
    if (fixtures / "unresolved-composition-plan.json").exists():
        _fail("unresolved pattern request must not emit a composition plan")

    print("pattern and dataset library valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
