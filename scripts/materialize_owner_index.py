#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Materialize a task-supplied owner-learning manifest into an Index provider.

The script never reads the host Library directly. The selected host first
materializes the declared ``library://`` files into a task directory, then
passes exact ``source_id=path`` bindings here. Every byte is hashed before it
can become a first-class Index record.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime import IndexProvider  # noqa: E402
from packages.index_runtime.utils import sha256_json  # noqa: E402


CONTRACT = "io.clayz.presentation.owner-index-materialization/1.0"
MANIFEST_CONTRACT = "io.clayz.presentation.owner-learning-sources/1.0"
STAGES = {"logic", "copy", "art-direction", "output", "supervisor"}
FORMATS = {"jsonl", "jsonl-gzip", "json", "markdown"}
RECORD_TYPES = {"learning", "reference", "failure-pattern", "knowledge"}
KNOWLEDGE_KINDS = {
    "private-knowledge", "template", "standard", "method", "preference",
    "example", "brand-asset", "failure-pattern", "other",
}


class MaterializationError(ValueError):
    """Raised when owner-private learning cannot be materialized safely."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise MaterializationError(message)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _slug(value: Any, fallback: str) -> str:
    text = re.sub(r"[^a-z0-9._-]+", "-", str(value or "").casefold()).strip("-._")
    return (text or fallback)[:72]


def _strings(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip() and item.strip() not in result:
                result.append(item.strip())
        return result
    return []


def _json_lines(text: str, label: str) -> list[Any]:
    values: list[Any] = []
    for line_number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        try:
            values.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            raise MaterializationError(f"{label}:{line_number}: invalid JSONL: {exc}") from exc
    return values


def _rows(path: Path, format_name: str) -> tuple[bytes, list[Any]]:
    payload = path.read_bytes()
    if format_name == "jsonl-gzip":
        try:
            text = gzip.decompress(payload).decode("utf-8-sig")
        except (OSError, UnicodeDecodeError) as exc:
            raise MaterializationError(f"{path}: invalid UTF-8 gzip JSONL: {exc}") from exc
        return payload, _json_lines(text, str(path))
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise MaterializationError(f"{path}: expected UTF-8 text: {exc}") from exc
    if format_name == "jsonl":
        return payload, _json_lines(text, str(path))
    if format_name == "json":
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise MaterializationError(f"{path}: invalid JSON: {exc}") from exc
        if isinstance(value, list):
            return payload, value
        if isinstance(value, dict):
            for key in ("records", "items", "cases", "counterexamples"):
                if isinstance(value.get(key), list):
                    return payload, value[key]
        return payload, [value]
    if format_name == "markdown":
        return payload, [{"title": path.stem, "content": text}]
    raise MaterializationError(f"unsupported source format: {format_name}")


def _summary(row: Any, fallback: str) -> str:
    if isinstance(row, Mapping):
        for key in ("summary", "description", "learning", "insight", "reason", "notes", "content"):
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                return re.sub(r"\s+", " ", value).strip()[:1200]
    rendered = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (rendered or fallback)[:1200]


def _title(row: Any, source_id: str, index: int) -> str:
    if isinstance(row, Mapping):
        for key in ("title", "name", "label", "page_title", "case_name", "id", "record_id"):
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:240]
    return f"{source_id} record {index + 1}"


def _records_for_source(source: Mapping[str, Any], path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_id = str(source["source_id"])
    format_name = str(source["format"])
    payload, rows = _rows(path, format_name)
    _require(rows, f"{source_id}: materialized source is empty")
    source_sha256 = _sha256_bytes(payload)
    record_type = str(source["record_type"])
    stages = list(source["stages"])
    configured_tags = _strings(source.get("purpose_tags"))
    knowledge_kinds = _strings(source.get("knowledge_kinds"))
    _require(bool(knowledge_kinds), f"{source_id}: knowledge_kinds must identify what this source teaches")
    _require(set(knowledge_kinds).issubset(KNOWLEDGE_KINDS), f"{source_id}: unsupported knowledge_kinds")
    kind_tags = [f"knowledge-kind:{item}" for item in knowledge_kinds]
    records: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    for index, row in enumerate(rows):
        _require(isinstance(row, (dict, list, str, int, float, bool)) or row is None, f"{source_id}[{index}]: unsupported value")
        row_hash = sha256_json(row)
        candidate_id = None
        if isinstance(row, Mapping):
            candidate_id = row.get("record_id") or row.get("id") or row.get("case_id")
        suffix = _slug(candidate_id, f"r{index + 1:04d}")
        record_id = f"owner.{_slug(source_id, 'source')}.{suffix}.{row_hash[:8]}"
        if record_id in used_ids:
            record_id = f"{record_id}.{index + 1}"
        used_ids.add(record_id)
        row_tags = _strings(row.get("purpose_tags")) if isinstance(row, Mapping) else []
        page_roles = _strings(row.get("page_roles")) if isinstance(row, Mapping) else []
        semantic_relations = _strings(row.get("semantic_relations")) if isinstance(row, Mapping) else []
        failure_signals = _strings(row.get("failure_signals")) if isinstance(row, Mapping) else []
        task_modes = _strings(row.get("task_modes")) if isinstance(row, Mapping) else []
        records.append({
            "contract": "io.clayz.presentation.index-record/1.0",
            "record_id": record_id,
            "record_type": record_type,
            "provider_id": "task-private-learning",
            "title": _title(row, source_id, index),
            "summary": _summary(row, f"Task-supplied owner record from {source_id}"),
            "source": {
                "source_id": source_id,
                "source_uri": str(source["library_uri"]),
                "source_revision": f"sha256:{source_sha256}",
                "sha256": source_sha256,
            },
            "governance": {
                "human_admitted": True,
                "quality_status": "admitted",
                "public_catalog_eligible": False,
                "deprecated": False,
            },
            "rights": {
                "license": "owner-private; pre-existing curated Library learning",
                "redistribution": "owner-private",
                "materialization": "owner-private",
                "commercial_use": None,
                "derivative_use": None,
                "attribution_required": False,
                "never_copy": [
                    "source pixels or media",
                    "brand identity",
                    "verbatim private copy beyond the selected task",
                ],
            },
            "classification": {
                "stages": stages,
                "task_modes": task_modes,
                "page_roles": page_roles,
                "semantic_relations": semantic_relations,
                "purpose_tags": list(dict.fromkeys([*configured_tags, *kind_tags, *row_tags])),
                "languages": ["zh-CN"],
                "failure_signals": failure_signals,
                "asset_class": "owner-private-learning" if record_type == "learning" else "owner-private-reference-metadata",
                "brand_scope": "brand-specific",
            },
            "payload": {
                "kind": "inline",
                "ref": {
                    "owner_source_id": source_id,
                    "library_uri": str(source["library_uri"]),
                    "admission_basis": "task-supplied owner learning admitted for this run",
                    "content": row,
                },
            },
            "neighbors": {"physical": [], "semantic": []},
        })
    return records, {
        "source_id": source_id,
        "library_uri": source["library_uri"],
        "local_path": str(path.resolve()),
        "sha256": source_sha256,
        "bytes": len(payload),
        "record_count": len(records),
        "stages": stages,
        "knowledge_kinds": knowledge_kinds,
    }


def _parse_bindings(values: Iterable[str]) -> dict[str, Path]:
    bindings: dict[str, Path] = {}
    for value in values:
        source_id, separator, raw_path = value.partition("=")
        _require(bool(separator) and bool(source_id.strip()) and bool(raw_path.strip()), "--source must use source_id=path")
        source_id = source_id.strip()
        _require(source_id not in bindings, f"duplicate --source binding: {source_id}")
        bindings[source_id] = Path(raw_path.strip())
    return bindings


def materialize(
    manifest: Mapping[str, Any],
    bindings: Mapping[str, Path],
    stages: set[str],
    output: Path,
    report_path: Path,
) -> dict[str, Any]:
    _require(manifest.get("contract") == MANIFEST_CONTRACT, "owner-learning source manifest contract is unsupported")
    _require(manifest.get("provider_id") == "task-private-learning", "owner-learning source provider_id must be task-private-learning")
    configured = manifest.get("sources")
    _require(isinstance(configured, list) and configured, "owner-learning source manifest must contain sources")
    selected: list[Mapping[str, Any]] = []
    for index, source in enumerate(configured):
        _require(isinstance(source, Mapping), f"sources[{index}] must be an object")
        _require(source.get("format") in FORMATS, f"sources[{index}].format is unsupported")
        _require(source.get("record_type") in RECORD_TYPES, f"sources[{index}].record_type is unsupported")
        kinds = source.get("knowledge_kinds")
        _require(
            isinstance(kinds, list) and bool(kinds) and all(isinstance(item, str) for item in kinds)
            and set(kinds).issubset(KNOWLEDGE_KINDS),
            f"sources[{index}].knowledge_kinds is invalid",
        )
        declared_stages = set(source.get("stages", []))
        _require(bool(declared_stages) and declared_stages.issubset(STAGES), f"sources[{index}].stages is invalid")
        if declared_stages.intersection(stages):
            selected.append(source)
    required_ids = {str(source["source_id"]) for source in selected if source.get("required") is True}
    missing = sorted(source_id for source_id in required_ids if source_id not in bindings)
    _require(not missing, f"missing required owner Library materializations: {missing}")
    unknown = sorted(set(bindings) - {str(source["source_id"]) for source in selected})
    _require(not unknown, f"bindings do not belong to the selected stages: {unknown}")

    records: list[dict[str, Any]] = []
    source_reports: list[dict[str, Any]] = []
    for source in selected:
        source_id = str(source["source_id"])
        path = bindings.get(source_id)
        if path is None:
            continue
        _require(path.is_file(), f"{source_id}: materialized file not found: {path}")
        source_records, source_report = _records_for_source(source, path)
        records.extend(source_records)
        source_reports.append(source_report)

    provider = IndexProvider.from_records("task-private-learning", records)
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in provider.records)
    output.write_text(rendered, encoding="utf-8", newline="\n")
    report = {
        "contract": CONTRACT,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider_id": provider.provider_id,
        "selected_stages": sorted(stages),
        "source_manifest_sha256": sha256_json(manifest),
        "inventory_uri": manifest.get("inventory_uri"),
        "admission_basis": manifest.get("admission_basis"),
        "required_source_ids": sorted(required_ids),
        "missing_source_ids": [],
        "materialized_sources": sorted(source_reports, key=lambda item: item["source_id"]),
        "provider_snapshot": provider.snapshot(),
        "output_path": str(output.resolve()),
        "output_sha256": _sha256_bytes(output.read_bytes()),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="task-local owner-learning manifest")
    parser.add_argument("--stage", action="append", choices=sorted(STAGES))
    parser.add_argument("--source", action="append", default=[], metavar="SOURCE_ID=PATH")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        selected_stages = set(args.stage or STAGES)
        report = materialize(manifest, _parse_bindings(args.source), selected_stages, args.output, args.report)
    except (OSError, json.JSONDecodeError, MaterializationError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "snapshot": report["provider_snapshot"], "report": str(args.report)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
