#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate the portable, intentionally empty knowledge scaffold."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


STAGES = ("logic", "copy", "art-direction", "output")
SOURCE_KINDS = ("documents", "data", "images", "svg", "pptx", "pdf")
ASSET_FIELDS = {
    "asset_id", "kind", "relative_path", "sha256", "source_uri", "license",
    "language", "purpose_tags", "physical_neighbors", "semantic_neighbors",
    "human_admitted",
}
ADMISSION_FIELDS = {
    "admission_id", "subject_type", "subject_id", "admitted_by", "admitted_at",
    "use_for", "never_copy", "decision_notes",
}
LEARNING_FIELDS = {
    "record_id", "stage", "task_purpose", "observation", "evidence_refs",
    "decision", "promotion_status", "created_at",
}
SHA256 = re.compile(r"[0-9a-f]{64}")


def read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        errors.append(f"missing file: {path}")
        return rows
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{line_number}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{path}:{line_number}: expected an object")
            continue
        rows.append(value)
    return rows


def require_fields(row: dict[str, Any], fields: set[str], label: str, errors: list[str]) -> None:
    missing = sorted(fields - set(row))
    if missing:
        errors.append(f"{label}: missing fields {missing}")


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    knowledge = root / "knowledge"
    if not (knowledge / "README.md").is_file():
        errors.append("knowledge/README.md is required")

    learning_root = knowledge / "learning"
    for stage in STAGES:
        stage_root = learning_root / stage
        if not (stage_root / "NAVIGATION.md").is_file():
            errors.append(f"knowledge/learning/{stage}/NAVIGATION.md is required")
        rows = read_jsonl(stage_root / "learning-records.jsonl", errors)
        identifiers: set[str] = set()
        for index, row in enumerate(rows, start=1):
            label = f"{stage} learning row {index}"
            require_fields(row, LEARNING_FIELDS, label, errors)
            if row.get("stage") != stage:
                errors.append(f"{label}: stage must be {stage}")
            record_id = row.get("record_id")
            if not isinstance(record_id, str) or not record_id:
                errors.append(f"{label}: record_id must be non-empty")
            elif record_id in identifiers:
                errors.append(f"{label}: duplicate record_id {record_id}")
            else:
                identifiers.add(record_id)
            if row.get("promotion_status") not in {"observation", "rejected", "admitted"}:
                errors.append(f"{label}: invalid promotion_status")

    if (learning_root / "supervisor").exists():
        errors.append("Supervisor must not have an independent learning silo")

    sources = knowledge / "sources"
    if not (sources / "NAVIGATION.md").is_file():
        errors.append("knowledge/sources/NAVIGATION.md is required")
    for kind in SOURCE_KINDS:
        if not (sources / kind).is_dir():
            errors.append(f"knowledge/sources/{kind} directory is required")

    registry = knowledge / "registry"
    if not (registry / "schema.md").is_file():
        errors.append("knowledge/registry/schema.md is required")
    assets = read_jsonl(registry / "asset-registry.jsonl", errors)
    asset_ids: set[str] = set()
    for index, row in enumerate(assets, start=1):
        label = f"asset row {index}"
        require_fields(row, ASSET_FIELDS, label, errors)
        asset_id = row.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id:
            errors.append(f"{label}: asset_id must be non-empty")
        elif asset_id in asset_ids:
            errors.append(f"{label}: duplicate asset_id {asset_id}")
        else:
            asset_ids.add(asset_id)
        relative_path = row.get("relative_path")
        if not isinstance(relative_path, str) or Path(relative_path).is_absolute() or ".." in Path(relative_path).parts:
            errors.append(f"{label}: relative_path must remain beneath knowledge/sources")
        if row.get("kind") not in {"document", "data", "image", "svg", "pptx", "pdf"}:
            errors.append(f"{label}: invalid kind")
        if not isinstance(row.get("sha256"), str) or not SHA256.fullmatch(row["sha256"]):
            errors.append(f"{label}: sha256 must be 64 lowercase hex characters")
        if not isinstance(row.get("human_admitted"), bool):
            errors.append(f"{label}: human_admitted must be boolean")

    admissions = read_jsonl(registry / "admitted-references.jsonl", errors)
    admission_ids: set[str] = set()
    for index, row in enumerate(admissions, start=1):
        label = f"admission row {index}"
        require_fields(row, ADMISSION_FIELDS, label, errors)
        admission_id = row.get("admission_id")
        if not isinstance(admission_id, str) or not admission_id:
            errors.append(f"{label}: admission_id must be non-empty")
        elif admission_id in admission_ids:
            errors.append(f"{label}: duplicate admission_id {admission_id}")
        else:
            admission_ids.add(admission_id)
        if row.get("subject_type") not in {"asset", "learning"}:
            errors.append(f"{label}: subject_type must be asset or learning")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    errors = validate(Path(args.root).resolve())
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
