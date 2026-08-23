#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate Stage 5 feedback, benchmark, migration, and readiness evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.feedback import (  # noqa: E402
    build_learning_provider,
    migrate_legacy_knowledge,
    run_retrieval_benchmark,
    validate_release_readiness,
)
from packages.index_runtime import CompositeIndex, IndexProvider  # noqa: E402


SCHEMAS = {
    "packages/contracts/learning-record.schema.json": "urn:clayz:presentation:schema:learning-record:1.0",
    "packages/contracts/learning-admission.schema.json": "urn:clayz:presentation:schema:learning-admission:1.0",
    "packages/contracts/feedback-index-report.schema.json": "urn:clayz:presentation:schema:feedback-index-report:1.0",
    "packages/contracts/retrieval-benchmark.schema.json": "urn:clayz:presentation:schema:retrieval-benchmark:1.0",
    "packages/contracts/retrieval-benchmark-report.schema.json": "urn:clayz:presentation:schema:retrieval-benchmark-report:1.0",
    "packages/contracts/legacy-index-migration-report.schema.json": "urn:clayz:presentation:schema:legacy-index-migration-report:1.0",
    "packages/contracts/release-readiness.schema.json": "urn:clayz:presentation:schema:release-readiness:1.0",
}
FIXTURES = ROOT / "examples" / "synthetic-feedback-loop"
CREATED_AT = "2026-08-23T12:00:00Z"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    for relative, expected_id in SCHEMAS.items():
        schema = read_json(ROOT / relative)
        require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"{relative}: wrong schema draft")
        require(schema.get("$id") == expected_id, f"{relative}: wrong schema id")

    records = read_jsonl(FIXTURES / "learning-records.jsonl")
    admissions = read_jsonl(FIXTURES / "learning-admissions.jsonl")
    learning_provider, feedback_report = build_learning_provider(records, admissions, created_at=CREATED_AT)
    require(feedback_report == read_json(FIXTURES / "feedback-index-report.json"), "feedback report fixture drift")
    require(feedback_report["admitted_record_count"] == 1, "exactly one synthetic learning record must be admitted")
    require(len(feedback_report["skipped"]) == 1, "one observation must remain unadmitted")
    require(all(record["governance"]["public_catalog_eligible"] is False for record in learning_provider.records), "learning admission must stay private")

    builtin = IndexProvider.from_jsonl("builtin-catalog", ROOT / "catalog" / "records.jsonl")
    benchmark = read_json(FIXTURES / "retrieval-benchmark.json")
    report = run_retrieval_benchmark(CompositeIndex([builtin, learning_provider]), benchmark, created_at=CREATED_AT)
    require(report == read_json(FIXTURES / "retrieval-benchmark-report.json"), "retrieval benchmark fixture drift")
    require(report["summary"]["passed"] is True and report["summary"]["case_count"] >= 4, "retrieval benchmark must pass four cases")
    require(report["guards"]["invented_record_count"] == 0, "retrieval benchmark returned invented records")

    migrated, migration_report = migrate_legacy_knowledge(
        source_root=FIXTURES / "legacy-sources",
        asset_registry=FIXTURES / "legacy-asset-registry.jsonl",
        admission_registry=FIXTURES / "legacy-admissions.jsonl",
        learning_root=FIXTURES / "legacy-learning",
        created_at=CREATED_AT,
    )
    require(migration_report == read_json(FIXTURES / "legacy-migration-report.json"), "legacy migration fixture drift")
    require(len(migrated.records) == 2, "migration must admit one asset and one learning record")
    require(any(item["reason"] == "source-hash-drift" for item in migration_report["skipped"]), "migration must report stale asset hashes")
    require(all(record["governance"]["public_catalog_eligible"] is False for record in migrated.records), "migration must preserve private scope")

    readiness = read_json(ROOT / "release" / "v0.4.0-readiness.json")
    result = validate_release_readiness(ROOT, readiness)
    require(result["release_authorized"] is True, "explicit release authorization is missing")

    print("feedback, benchmark, migration, and release readiness valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
