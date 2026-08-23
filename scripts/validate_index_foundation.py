#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate index contracts and the public catalog's no-asset boundary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime import IndexProvider, IndexRuntimeError  # noqa: E402

SCHEMAS = {
    "packages/contracts/index-record.schema.json": "urn:clayz:presentation:schema:index-record:1.0",
    "packages/contracts/retrieval-request.schema.json": "urn:clayz:presentation:schema:retrieval-request:1.0",
    "packages/contracts/retrieval-receipt.schema.json": "urn:clayz:presentation:schema:retrieval-receipt:1.0",
}
FORBIDDEN_CATALOG_SUFFIXES = {
    ".pptx",
    ".pptm",
    ".potx",
    ".potm",
    ".thmx",
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
}


def main() -> int:
    for relative, expected_id in SCHEMAS.items():
        path = ROOT / relative
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise IndexRuntimeError(f"{relative}: unexpected JSON Schema draft")
        if value.get("$id") != expected_id:
            raise IndexRuntimeError(f"{relative}: unexpected $id")
        if value.get("type") != "object":
            raise IndexRuntimeError(f"{relative}: root type must be object")

    catalog = ROOT / "catalog"
    for path in catalog.rglob("*"):
        if path.is_file() and path.suffix.casefold() in FORBIDDEN_CATALOG_SUFFIXES:
            raise IndexRuntimeError(
                f"public catalog must remain metadata/method only; forbidden asset found: {path.relative_to(ROOT)}"
            )

    records = catalog / "records.jsonl"
    provider = IndexProvider.from_jsonl("builtin-catalog", records)
    for record in provider.records:
        if not record["governance"]["public_catalog_eligible"]:
            raise IndexRuntimeError(f"builtin catalog record is not public-catalog eligible: {record['record_id']}")
        if record["rights"]["redistribution"] not in {"allowed", "metadata-only"}:
            raise IndexRuntimeError(f"builtin catalog record has invalid redistribution state: {record['record_id']}")

    print("index foundation valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
