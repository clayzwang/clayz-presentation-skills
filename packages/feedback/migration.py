# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed migration from the legacy filesystem knowledge store."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from packages.index_runtime import INDEX_CONTRACT, IndexProvider

from .learning import FeedbackError, build_learning_provider


MIGRATION_REPORT_CONTRACT = "io.clayz.presentation.legacy-index-migration-report/1.0"


class MigrationError(ValueError):
    """Raised when legacy knowledge cannot be migrated safely."""


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MigrationError(f"{path}:{line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise MigrationError(f"{path}:{line_number}: expected an object")
        rows.append(value)
    return rows


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_record_id(asset_id: str) -> str:
    candidate = f"legacy.{asset_id.casefold()}"
    candidate = re.sub(r"[^a-z0-9._-]+", "-", candidate).strip("-._")
    if len(candidate) >= 3 and len(candidate) <= 128 and re.fullmatch(r"[a-z0-9][a-z0-9._-]+", candidate):
        return candidate
    digest = hashlib.sha256(asset_id.encode("utf-8")).hexdigest()[:20]
    return f"legacy.asset.{digest}"


def _newest_admissions(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    selected: dict[tuple[str, str], dict[str, Any]] = {}
    for row in sorted(rows, key=lambda item: (str(item.get("admitted_at", "")), str(item.get("admission_id", "")))):
        key = (str(row.get("subject_type", "")), str(row.get("subject_id", "")))
        selected[key] = row
    return selected


def migrate_legacy_knowledge(
    *,
    source_root: Path,
    asset_registry: Path,
    admission_registry: Path,
    learning_root: Path,
    provider_id: str = "filesystem-library",
    created_at: str,
) -> tuple[IndexProvider, dict[str, Any]]:
    assets = _read_jsonl(asset_registry)
    admissions = _read_jsonl(admission_registry)
    admission_by_subject = _newest_admissions(admissions)
    id_map = {
        str(asset.get("asset_id")): _safe_record_id(str(asset.get("asset_id")))
        for asset in assets
        if isinstance(asset.get("asset_id"), str) and asset.get("asset_id")
    }
    records: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    orphan_neighbors: list[dict[str, str]] = []

    for asset in sorted(assets, key=lambda item: str(item.get("asset_id", ""))):
        asset_id = asset.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id:
            skipped.append({"subject_id": "", "reason": "invalid-asset-id"})
            continue
        admission = admission_by_subject.get(("asset", asset_id))
        if admission is None:
            skipped.append({"subject_id": asset_id, "reason": "human-admission-required"})
            continue
        relative = asset.get("relative_path")
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            skipped.append({"subject_id": asset_id, "reason": "unsafe-relative-path"})
            continue
        source = source_root / relative
        if not source.is_file():
            skipped.append({"subject_id": asset_id, "reason": "source-missing"})
            continue
        if _sha256_file(source) != asset.get("sha256"):
            skipped.append({"subject_id": asset_id, "reason": "source-hash-drift"})
            continue
        physical = []
        semantic = []
        for field, target in (("physical_neighbors", physical), ("semantic_neighbors", semantic)):
            for neighbor_id in asset.get(field, []):
                migrated_id = id_map.get(str(neighbor_id))
                if migrated_id:
                    target.append(migrated_id)
                else:
                    orphan_neighbors.append({"subject_id": asset_id, "neighbor_id": str(neighbor_id)})
        purpose_tags = sorted(set(
            [str(item) for item in asset.get("purpose_tags", []) if str(item)]
            + [str(item) for item in admission.get("use_for", []) if str(item)]
        ))
        notes = str(asset.get("notes", "")).strip()
        records.append({
            "contract": INDEX_CONTRACT,
            "record_id": id_map[asset_id],
            "record_type": "knowledge",
            "provider_id": provider_id,
            "title": Path(relative).stem or asset_id,
            "summary": notes or f"Migrated local knowledge asset {asset_id}",
            "source": {
                "source_id": asset_id,
                "source_uri": str(asset.get("source_uri", "legacy-local-source")),
                "source_revision": "1",
                "sha256": str(asset["sha256"]),
            },
            "governance": {
                "human_admitted": True,
                "quality_status": "admitted",
                "public_catalog_eligible": False,
                "deprecated": False,
            },
            "rights": {
                "license": str(asset.get("license", "unknown-local-rights")),
                "redistribution": "local-private",
                "materialization": "local-only",
                "commercial_use": None,
                "derivative_use": None,
                "attribution_required": False,
                "never_copy": sorted(set(str(item) for item in admission.get("never_copy", []) if str(item))),
            },
            "classification": {
                "stages": ["shared"],
                "task_modes": [],
                "page_roles": [],
                "semantic_relations": [],
                "purpose_tags": purpose_tags,
                "languages": [str(asset.get("language", "und"))],
                "failure_signals": [],
                "asset_class": str(asset.get("kind", "document")),
                "brand_scope": "none",
            },
            "payload": {"kind": "path", "ref": relative},
            "neighbors": {"physical": sorted(set(physical)), "semantic": sorted(set(semantic))},
        })

    learning_rows: list[dict[str, Any]] = []
    for stage in ("logic", "copy", "art-direction", "output"):
        learning_rows.extend(_read_jsonl(learning_root / stage / "learning-records.jsonl"))
    learning_admissions = [row for row in admissions if row.get("subject_type") == "learning"]
    try:
        learning_provider, learning_report = build_learning_provider(
            learning_rows,
            learning_admissions,
            provider_id=provider_id,
            created_at=created_at,
        )
    except FeedbackError as exc:
        raise MigrationError(str(exc)) from exc
    records.extend(learning_provider.records)
    migrated_ids = {record["record_id"] for record in records}
    for record in records:
        for field in ("physical", "semantic"):
            retained = []
            for neighbor_id in record["neighbors"][field]:
                if neighbor_id in migrated_ids:
                    retained.append(neighbor_id)
                else:
                    orphan_neighbors.append({"subject_id": record["source"]["source_id"], "neighbor_id": neighbor_id})
            record["neighbors"][field] = retained
    provider = IndexProvider.from_records(provider_id, records)
    report = {
        "contract": MIGRATION_REPORT_CONTRACT,
        "created_at": created_at,
        "source_contract": "legacy-filesystem-knowledge/1.0",
        "target_contract": "io.clayz.presentation.index-record/1.0",
        "provider_snapshot": provider.snapshot(),
        "counts": {
            "source_assets": len(assets),
            "migrated_assets": sum(1 for record in records if record["record_type"] == "knowledge"),
            "source_learning_records": len(learning_rows),
            "migrated_learning_records": sum(1 for record in records if record["record_type"] == "learning"),
            "skipped": len(skipped) + len(learning_report["skipped"]),
            "orphan_neighbors": len(orphan_neighbors),
        },
        "skipped": skipped + [
            {"subject_id": item["record_id"], "reason": item["reason"]}
            for item in learning_report["skipped"]
        ],
        "orphan_neighbors": orphan_neighbors,
        "guards": {
            "human_admission_required": True,
            "stale_hashes_skipped": True,
            "private_scope_preserved": True,
            "brand_assets_not_public": True,
            "automatic_promotion": False,
        },
    }
    return provider, report
