#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate registered public Layout Contracts and their separation guards."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime import IndexProvider, IndexRuntimeError  # noqa: E402
from packages.layout.layout_contract import LayoutContractError, validate_layout_contract  # noqa: E402

SCHEMAS = {
    "packages/contracts/layout-contract.schema.json": "urn:clayz:presentation:schema:layout-contract:1.0",
    "packages/contracts/layout-contract-request.schema.json": "urn:clayz:presentation:schema:layout-contract-request:1.0",
    "packages/contracts/layout-contract-instance.schema.json": "urn:clayz:presentation:schema:layout-contract-instance:1.0",
    "packages/contracts/layout-contract-resolution.schema.json": "urn:clayz:presentation:schema:layout-contract-resolution:1.0",
    "packages/contracts/layout-compilation.schema.json": "urn:clayz:presentation:schema:layout-compilation:1.0",
    "packages/contracts/layout-tree.schema.json": "urn:clayz:presentation:schema:layout-tree:1.0",
}
FORBIDDEN_SUFFIXES = {".pptx", ".pptm", ".potx", ".potm", ".thmx", ".ttf", ".otf", ".woff", ".woff2", ".ckpt", ".safetensors"}


def _fail(message: str) -> None:
    raise IndexRuntimeError(message)


def main() -> int:
    for relative, expected_id in SCHEMAS.items():
        value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema" or value.get("$id") != expected_id:
            _fail(f"{relative}: unexpected schema identity")

    contract_root = (ROOT / "catalog" / "layout-contracts").resolve()
    for path in contract_root.rglob("*"):
        if path.is_file() and path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            _fail(f"public Layout Contract catalog contains a forbidden asset: {path.relative_to(ROOT)}")

    provider = IndexProvider.from_jsonl("builtin-catalog", ROOT / "catalog" / "records.jsonl")
    records = [record for record in provider.records if record["record_type"] == "layout-contract"]
    if len(records) < 2:
        _fail("Stage 3 requires at least two registered synthetic Layout Contracts")
    registered_paths: set[Path] = set()
    for record in records:
        if record["classification"]["brand_scope"] != "none" or record["classification"]["asset_class"] != "contract":
            _fail(f"Layout Contract must remain brand-neutral contract metadata: {record['record_id']}")
        if record["payload"]["kind"] != "path":
            _fail(f"Layout Contract must use a hash-bound path payload: {record['record_id']}")
        if record["rights"]["redistribution"] != "allowed" or record["rights"]["materialization"] != "allowed":
            _fail(f"public Layout Contract needs explicit redistribution and materialization rights: {record['record_id']}")
        path = (ROOT / record["payload"]["ref"]).resolve()
        try:
            path.relative_to(contract_root)
        except ValueError:
            _fail(f"Layout Contract path escapes catalog/layout-contracts: {record['record_id']}")
        if path.suffix.casefold() != ".json" or not path.is_file():
            _fail(f"Layout Contract payload is missing or not JSON: {record['record_id']}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != record["source"]["sha256"]:
            _fail(f"Layout Contract hash mismatch: {record['record_id']}")
        try:
            contract = validate_layout_contract(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, LayoutContractError) as exc:
            _fail(f"invalid Layout Contract {record['record_id']}: {exc}")
        if contract["layout_contract_id"] != record["record_id"]:
            _fail(f"Layout Contract ID must equal its registry record ID: {record['record_id']}")
        for field in ("task_modes", "page_roles", "semantic_relations", "purpose_tags", "languages"):
            if set(contract["selection"][field]) != set(record["classification"][field]):
                _fail(f"Layout Contract selection metadata drift for {field}: {record['record_id']}")
        registered_paths.add(path)

    unregistered = {
        path.resolve()
        for path in contract_root.glob("*.json")
        if path.resolve() not in registered_paths
    }
    if unregistered:
        _fail(f"unregistered Layout Contract files: {[path.name for path in sorted(unregistered)]}")

    fixture_root = ROOT / "examples" / "synthetic-layout-contract"
    compilation = json.loads((fixture_root / "comparison-compilation.json").read_text(encoding="utf-8"))
    resolved = json.loads((fixture_root / "comparison-resolved.json").read_text(encoding="utf-8"))
    unresolved = json.loads((fixture_root / "unresolved-resolution.json").read_text(encoding="utf-8"))
    if compilation.get("contract") != "io.clayz.presentation.layout-compilation/1.0":
        _fail("synthetic Layout Contract compilation has the wrong contract")
    if list(compilation.get("layers", {})) != ["theme", "visual_variant", "layout_contract", "layout_tree", "resolved_coordinates"]:
        _fail("synthetic compilation must preserve the five-layer boundary")
    if compilation["layers"]["theme"].get("input_used") or compilation["layers"]["visual_variant"].get("input_used"):
        _fail("Layout Contract compiler must not consume Theme or Visual Variant")
    if not compilation.get("layout_tree", {}).get("source", {}).get("semantic_layout_tree_id"):
        _fail("compiled Layout Tree must retain its approved Semantic Layout Tree ID")
    if resolved.get("layers", {}).get("resolved_coordinates", {}).get("status") != "materialized":
        _fail("synthetic coordinate fixture was not materialized by the solver")
    if unresolved.get("status") != "unresolved" or not unresolved.get("fallback", {}).get("used"):
        _fail("no-match fixture must remain explicitly unresolved")
    if (fixture_root / "should-not-exist.json").exists():
        _fail("unresolved Layout Contract must not emit a compilation")
    print("layout contracts valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
