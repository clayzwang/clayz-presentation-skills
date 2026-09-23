#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Durable 3.6 work-report collection and handoff verification.

The work report is a derived section of the existing supervision report.  It
is intentionally source-bound: the collector accepts explicit artifacts and
recorded stage bindings, retains JSON/text sources in full, and reports
binary inputs as metadata.  It does not create a second index or scan an
arbitrary library tree.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import zipfile
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET


WORK_REPORT_CONTRACT = "io.clayz.presentation.work-report/1.0"
WORK_REPORT_VERSION = "3.6"
DELIVERY_MANIFEST_CONTRACT = "io.clayz.presentation.supervised-delivery-manifest/1.0"
MISSING_STATUS = "not-recorded"
PARTIAL_STATUS = "partial"
RECORDED_STATUS = "recorded"
STAGES = ("logic", "copy", "art-direction", "output", "supervisor")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
JSON_SUFFIXES = {".json", ".jsonc"}
TEXT_SUFFIXES = {
    ".txt", ".md", ".markdown", ".rst", ".csv", ".tsv", ".yaml", ".yml",
    ".xml", ".html", ".htm", ".log", ".jsonl",
}
META_FIELDS = ("path", "sha256", "bytes")
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
    "dc": "http://purl.org/dc/elements/1.1/",
}


class WorkReportError(ValueError):
    """Raised for an invalid source binding or work report."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _file(path: Path | str) -> Path:
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise WorkReportError(f"artifact is not a readable file: {resolved}")
    return resolved


def _meta(path: Path, raw: bytes | None = None) -> dict[str, Any]:
    data = path.read_bytes() if raw is None else raw
    return {"path": str(path.resolve()), "sha256": _digest(data), "bytes": len(data)}


def _path_expected(value: Path | str | Mapping[str, Any]) -> tuple[Path, Mapping[str, Any] | None]:
    if isinstance(value, Mapping):
        raw = value.get("path")
        if not isinstance(raw, str) or not raw.strip():
            raise WorkReportError("artifact binding must contain a non-empty path")
        return Path(raw), value
    return Path(value), None


def artifact_snapshot(
    path: Path | str,
    *,
    role: str | None = None,
    stage: str | None = None,
    expected: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Read one explicitly named source and preserve complete JSON/text data."""

    resolved = _file(path)
    raw = resolved.read_bytes()
    actual = _meta(resolved, raw)
    if expected is not None:
        for key in META_FIELDS:
            if key in expected and expected.get(key) != actual.get(key):
                raise WorkReportError(f"{role or resolved.name}: recorded {key} does not match source bytes")
    result: dict[str, Any] = {
        "source_id": role or resolved.name,
        **actual,
    }
    if stage is not None:
        result["stage"] = stage
    text: str | None = None
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    is_json = resolved.suffix.casefold() in JSON_SUFFIXES or (
        role is not None and "json" in role.casefold()
    )
    if text is not None and (is_json or text.lstrip().startswith(("{", "["))):
        try:
            result.update({"kind": "json", "content": json.loads(text), "raw_text": text})
            return result
        except json.JSONDecodeError:
            # A text note with a misleading role remains a complete text
            # snapshot; the bytes/hash still make the binding auditable.
            pass
    if text is not None and (resolved.suffix.casefold() in TEXT_SUFFIXES or role is not None):
        result.update({"kind": "text", "content": text, "raw_text": text})
        return result
    result.update({"kind": "binary", "content_status": "metadata-only"})
    return result


def _ref(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {key: snapshot.get(key) for key in ("source_id", "path", "sha256", "bytes", "kind")}


def _source(
    value: Path | str | Mapping[str, Any] | None,
    *,
    source_id: str,
    stage: str | None,
    snapshots: list[dict[str, Any]],
    ids: set[str],
) -> dict[str, Any] | None:
    if value is None:
        return None
    path, expected = _path_expected(value)
    snap = artifact_snapshot(path, role=source_id, stage=stage, expected=expected)
    if source_id in ids:
        old = next(item for item in snapshots if item.get("source_id") == source_id)
        old_compare = {key: value for key, value in old.items() if key != "stage"}
        new_compare = {key: value for key, value in snap.items() if key != "stage"}
        if old_compare != new_compare:
            raise WorkReportError(f"source {source_id!r} was supplied twice with different bytes")
        if old.get("stage") is None and snap.get("stage") is not None:
            old["stage"] = snap["stage"]
        return _ref(old)
    snapshots.append(snap)
    ids.add(source_id)
    return _ref(snap)


def _path(value: Any) -> Path | None:
    if isinstance(value, (Path, str)):
        return Path(value)
    if isinstance(value, Mapping) and isinstance(value.get("path"), str):
        return Path(value["path"])
    return None


def _snapshot(snapshots: Sequence[Mapping[str, Any]], source_id: str) -> Mapping[str, Any] | None:
    return next((item for item in snapshots if item.get("source_id") == source_id), None)


def _status(value: Any) -> Any:
    return value if value is not None else {"status": MISSING_STATUS}


def _first(mapping: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in mapping:
            return mapping[name]
    return None


def _record_artifacts(
    records: Sequence[Mapping[str, Any]] | None,
    *,
    snapshots: list[dict[str, Any]],
    ids: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records or []:
        if not isinstance(record, Mapping):
            continue
        stage = str(record.get("stage") or "unknown")
        artifacts = record.get("artifacts")
        if not isinstance(artifacts, Mapping):
            continue
        for role in sorted(artifacts, key=lambda value: str(value)):
            binding = artifacts[role]
            if not isinstance(binding, Mapping) or not isinstance(binding.get("path"), str):
                continue
            source_id = f"{stage}:{role}"
            source_ref = _source(
                binding,
                source_id=source_id,
                stage=stage,
                snapshots=snapshots,
                ids=ids,
            )
            rows.append({"stage": stage, "role": str(role), "source_ref": source_ref})
    return rows


def _work_notes(rows: Sequence[Mapping[str, Any]], snapshots: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        role = str(row.get("role", ""))
        if "note" not in role.casefold():
            continue
        ref = row.get("source_ref")
        source_id = ref.get("source_id") if isinstance(ref, Mapping) else None
        snap = _snapshot(snapshots, str(source_id)) if source_id else None
        if snap is None:
            continue
        note: dict[str, Any] = {
            "stage": row.get("stage"),
            "role": role,
            "source_ref": dict(ref) if isinstance(ref, Mapping) else ref,
            "status": RECORDED_STATUS if snap.get("kind") in {"json", "text"} else PARTIAL_STATUS,
        }
        if "raw_text" in snap:
            note["text"] = snap["raw_text"]
        note["content"] = snap.get("content") if snap.get("kind") != "binary" else {"status": "metadata-only"}
        result.append(note)
    observed_stages = {str(item.get("stage")) for item in result}
    for stage in STAGES:
        if stage in observed_stages:
            continue
        result.append({
            "stage": stage,
            "role": "work-notes",
            "source_ref": None,
            "status": MISSING_STATUS,
            "content": {"status": MISSING_STATUS},
        })
    return result


def _substantive(report: Mapping[str, Any], content: Mapping[str, Any]) -> dict[str, Any]:
    package = content.get("package") if isinstance(content.get("package"), Mapping) else {}
    logic_sources = []
    for key, value in content.items():
        if (key == "logic" or key.startswith("logic:")) and isinstance(value, Mapping):
            candidate = value.get("story") if isinstance(value.get("story"), Mapping) else (value.get("logic_layer") if isinstance(value.get("logic_layer"), Mapping) else value)
            logic_sources.append(candidate)
    package_logic = package.get("story") if isinstance(package.get("story"), Mapping) else (package.get("logic_layer") if isinstance(package.get("logic_layer"), Mapping) else None)
    logic = next(iter(logic_sources), package_logic if isinstance(package_logic, Mapping) else {})
    plan = content.get("plan") if isinstance(content.get("plan"), Mapping) else {}
    candidates = [report, package, logic, plan]

    def find(*names: str) -> Any:
        for item in candidates:
            if not isinstance(item, Mapping):
                continue
            value = _first(item, *names)
            if value is not None:
                return value
        return {"status": MISSING_STATUS}

    definitions = None
    if any(key in logic for key in ("glossary", "metric_dictionary")):
        definitions = {
            "glossary": logic.get("glossary", {"status": MISSING_STATUS}),
            "metric_dictionary": logic.get("metric_dictionary", {"status": MISSING_STATUS}),
        }
    if definitions is None:
        definitions = find("definitions", "metric_definitions", "glossary", "terminology")
    storyline = None
    if any(key in logic for key in ("deck_message_tree", "narrative")):
        storyline = {
            "deck_message_tree": logic.get("deck_message_tree", {"status": MISSING_STATUS}),
            "narrative": logic.get("narrative", {"status": MISSING_STATUS}),
        }
    if storyline is None:
        storyline = find("storyline", "story_line", "narrative_arc", "communication_contract")
    return {
        "logic_layer": logic if logic else {"status": MISSING_STATUS},
        "facts": find("facts", "established_facts", "key_facts", "knowledge_requirements"),
        "evidence": find("evidence", "evidence_map", "research_evidence", "sources"),
        "contradictions": find("contradictions", "counterevidence", "counter_evidence", "counterarguments"),
        "definitions": definitions,
        "assumptions": find("assumptions", "working_assumptions"),
        "unknowns": find("unknowns", "open_questions", "unresolved_questions", "open_items"),
        "storyline": storyline,
        "tradeoffs": find("tradeoffs", "trade_offs", "design_tradeoffs", "decision_log"),
    }


def _copy_section(content: Mapping[str, Any], notes: list[dict[str, Any]]) -> dict[str, Any]:
    package = content.get("package") if isinstance(content.get("package"), Mapping) else {}
    layer = package.get("copy_layer") if isinstance(package.get("copy_layer"), Mapping) else None
    slides = layer.get("slides") if isinstance(layer, Mapping) and "slides" in layer else []
    return {
        "artifact_source_id": "package" if package else None,
        "artifact_status": RECORDED_STATUS if package else MISSING_STATUS,
        "copy_layer": _status(layer),
        "slides": slides,
        "slides_status": RECORDED_STATUS if isinstance(layer, Mapping) and "slides" in layer else MISSING_STATUS,
        "notes": notes,
        "notes_status": RECORDED_STATUS if notes else MISSING_STATUS,
    }


def _art_direction(content: Mapping[str, Any]) -> dict[str, Any]:
    plan = content.get("plan") if isinstance(content.get("plan"), Mapping) else {}
    slides = plan.get("slides") if isinstance(plan, Mapping) else None
    sections = {
        key: plan[key]
        for key in ("communication_contract", "art_direction", "decision_log", "typography_contract", "deck_rhythm", "slides")
        if isinstance(plan, Mapping) and key in plan
    }
    return {
        "artifact_source_id": "plan" if plan else None,
        "artifact_status": RECORDED_STATUS if plan else MISSING_STATUS,
        "plan_sections": sections or {"status": MISSING_STATUS},
        "slides": slides if isinstance(slides, list) else [],
        "slides_status": RECORDED_STATUS if isinstance(slides, list) else MISSING_STATUS,
    }


def _calibration_items(calibrations: Any) -> list[tuple[str, Any]]:
    if calibrations is None:
        return []
    if isinstance(calibrations, Mapping):
        return [(str(key), value) for key, value in calibrations.items()]
    if isinstance(calibrations, Sequence) and not isinstance(calibrations, (str, bytes, bytearray)):
        result: list[tuple[str, Any]] = []
        for index, value in enumerate(calibrations):
            label = value.get("step") if isinstance(value, Mapping) and value.get("step") else f"calibration-{index + 1}"
            result.append((str(label), value))
        return result
    raise WorkReportError("calibrations must be a mapping or sequence")


def _dispositions(calibration: Mapping[str, Any], records: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    identifier = calibration.get("calibration_id")
    for record in records or []:
        for binding in record.get("calibration_bindings", []) if isinstance(record, Mapping) and isinstance(record.get("calibration_bindings"), list) else []:
            if isinstance(binding, Mapping) and binding.get("calibration_id") == identifier:
                values = binding.get("finding_dispositions")
                if isinstance(values, list):
                    return [dict(item) for item in values if isinstance(item, Mapping)]
    return []


def _calibrations(
    values: Any,
    *,
    records: Sequence[Mapping[str, Any]] | None,
    snapshots: list[dict[str, Any]],
    ids: set[str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for label, value in _calibration_items(values):
        source_ref: dict[str, Any] | None = None
        if _path(value) is not None:
            source_ref = _source(value, source_id=f"calibration:{label}", stage="supervisor", snapshots=snapshots, ids=ids)
            snap = _snapshot(snapshots, f"calibration:{label}")
            record = snap.get("content") if isinstance(snap, Mapping) else {}
        else:
            record = dict(value) if isinstance(value, Mapping) else {"status": MISSING_STATUS}
        if not isinstance(record, Mapping):
            record = {"status": PARTIAL_STATUS, "value": record}
        finding_values = record.get("findings", [])
        disposition_values = _dispositions(record, records)
        result.append({
            "step": record.get("step", label),
            "calibration_id": record.get("calibration_id"),
            "source_ref": source_ref,
            "record": dict(record),
            "findings": finding_values,
            "finding_dispositions": disposition_values,
            "disposition_status": RECORDED_STATUS if disposition_values or not finding_values else MISSING_STATUS,
        })
    return result


def _auditor(
    value: Any,
    report: Mapping[str, Any],
    *,
    snapshots: list[dict[str, Any]],
    ids: set[str],
) -> dict[str, Any]:
    if value is None and isinstance(report.get("auditor_artifact"), Mapping):
        value = report.get("auditor_artifact")
    source_ref: dict[str, Any] | None = None
    raw: Any = None
    if value is not None and _path(value) is not None:
        source_ref = _source(value, source_id="auditor", stage="supervisor", snapshots=snapshots, ids=ids)
        snap = _snapshot(snapshots, "auditor")
        raw = snap.get("content") if isinstance(snap, Mapping) else None
    elif isinstance(value, Mapping):
        raw = dict(value)
    if raw is None:
        raw = report.get("auditor_result")
    if not isinstance(raw, Mapping):
        return {
            "status": MISSING_STATUS,
            "artifact_ref": source_ref,
            "raw_result": {"status": MISSING_STATUS},
            "findings": [],
            "coverage": {"status": MISSING_STATUS},
            "limitations": [],
        }
    context = raw.get("independent_context") if isinstance(raw.get("independent_context"), Mapping) else {}
    limitations = list(context.get("limitations", [])) if isinstance(context, Mapping) and isinstance(context.get("limitations", []), list) else []
    if not isinstance(limitations, list):
        limitations = [str(limitations)]
    extra = report.get("auditor_limitations")
    if isinstance(extra, list):
        limitations.extend(item for item in extra if item not in limitations)
    return {
        "status": RECORDED_STATUS,
        "artifact_ref": source_ref,
        "raw_result": dict(raw),
        "audit_id": raw.get("audit_id"),
        "audit_status": raw.get("audit_status", report.get("auditor_status")),
        "findings": raw.get("findings", report.get("auditor_findings", [])),
        "coverage": raw.get("coverage", report.get("auditor_coverage", {})),
        "limitations": limitations,
    }


def _release(report: Mapping[str, Any], auditor: Mapping[str, Any]) -> dict[str, Any]:
    release = report.get("supervisor_release") if isinstance(report.get("supervisor_release"), Mapping) else {"status": MISSING_STATUS}
    limitations: list[Any] = []
    for value in (report.get("limitations"), auditor.get("limitations")):
        if isinstance(value, list):
            limitations.extend(item for item in value if item not in limitations)
    improvements = report.get("improvements", report.get("recommendations", {"status": MISSING_STATUS}))
    return {
        "status": release.get("status", report.get("run_status", MISSING_STATUS)),
        "run_status": report.get("run_status", MISSING_STATUS),
        "supervisor_release": dict(release),
        "limitations": limitations,
        "improvements": improvements,
    }


def _slide_differences(planned: Mapping[str, Any], actual: Mapping[str, Any]) -> list[str]:
    if not planned:
        return ["planned-slide-not-recorded"]
    result: list[str] = []
    title = planned.get("title") or planned.get("headline")
    if isinstance(title, str) and title.strip() and title.strip() not in str(actual.get("title", "")):
        result.append("title-text-differs")
    medium = planned.get("dominant_medium")
    inventory = actual.get("inventory", {}) if isinstance(actual.get("inventory"), Mapping) else {}
    if medium == "data-chart" and not inventory.get("charts"):
        result.append("no-native-chart-object-observed")
        result.append("visual-representation-not-determined")
    if medium == "table" and not inventory.get("tables"):
        result.append("no-native-table-object-observed")
        result.append("visual-representation-not-determined")
    return result


def build_work_report(
    *,
    report: Mapping[str, Any],
    artifacts: Mapping[str, Path | str | Mapping[str, Any]] | None = None,
    records: Sequence[Mapping[str, Any]] | None = None,
    record_paths: Sequence[Path | str | Mapping[str, Any]] | None = None,
    calibrations: Any = None,
    auditor: Path | str | Mapping[str, Any] | None = None,
    pptx: Path | str | None = None,
    task_request: Path | str | Mapping[str, Any] | None = None,
    acceptance_rules: Path | str | Mapping[str, Any] | None = None,
    supervisor_rules: Path | str | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Collect one report from explicit artifacts and immutable work records."""

    if not isinstance(report, Mapping):
        raise WorkReportError("report must be an object")
    snapshots: list[dict[str, Any]] = []
    ids: set[str] = set()
    refs: dict[str, dict[str, Any]] = {}
    for role in sorted((artifacts or {}), key=lambda value: str(value)):
        value = (artifacts or {})[role]
        if value is not None:
            source_ref = _source(value, source_id=str(role), stage=None, snapshots=snapshots, ids=ids)
            if source_ref is not None:
                refs[str(role)] = source_ref

    if task_request is None and isinstance(report.get("task_request"), Mapping):
        task_request = report.get("task_request")
    if acceptance_rules is None and isinstance(report.get("acceptance_contract"), Mapping) and isinstance(report["acceptance_contract"].get("path"), str):
        acceptance_rules = report["acceptance_contract"]
    if supervisor_rules is None and isinstance(report.get("supervisor_rules"), Mapping):
        supervisor_rules = report.get("supervisor_rules")
    task_ref = _source(task_request, source_id="task_request", stage="root", snapshots=snapshots, ids=ids)
    acceptance_ref = _source(acceptance_rules, source_id="acceptance_rules", stage="preflight", snapshots=snapshots, ids=ids)
    rules_ref = _source(supervisor_rules, source_id="supervisor_rules", stage="supervisor", snapshots=snapshots, ids=ids)

    record_refs: list[dict[str, Any]] = []
    for index, value in enumerate(record_paths or []):
        stage = str(records[index].get("stage")) if records and index < len(records) and isinstance(records[index], Mapping) else None
        source_ref = _source(value, source_id=f"stage-record:{stage or index + 1}", stage=stage, snapshots=snapshots, ids=ids)
        if source_ref is not None:
            record_refs.append(source_ref)
    artifact_rows = _record_artifacts(records, snapshots=snapshots, ids=ids)
    note_rows = _work_notes(artifact_rows, snapshots)
    content = {
        str(item.get("source_id")): item.get("content")
        for item in snapshots
        if isinstance(item.get("source_id"), str) and "content" in item
    }
    package = content.get("package") if isinstance(content.get("package"), Mapping) else {}
    plan = content.get("plan") if isinstance(content.get("plan"), Mapping) else {}

    actual_pptx: dict[str, Any]
    pptx_value: Any = pptx if pptx is not None else refs.get("pptx", {}).get("path")
    if pptx_value is None:
        actual_pptx = {
            "status": MISSING_STATUS, "artifact": None, "title": {"status": MISSING_STATUS},
            "presentation_title": {"status": MISSING_STATUS}, "slide_count": None,
            "slide_order": [], "slides": [], "totals": {}, "media": {"status": MISSING_STATUS},
            "masters": {"status": MISSING_STATUS}, "scope": {"status": MISSING_STATUS},
        }
    else:
        pptx_path = _path(pptx_value)
        try:
            actual_pptx = inspect_pptx(pptx_path if pptx_path is not None else pptx_value)
        except (OSError, WorkReportError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
            path = pptx_path
            metadata = _meta(path.resolve()) if path is not None and path.is_file() else None
            actual_pptx = {
                "status": PARTIAL_STATUS, "artifact": metadata, "inspection_error": str(exc),
                "title": {"status": MISSING_STATUS}, "presentation_title": {"status": MISSING_STATUS},
                "slide_count": None, "slide_order": [], "slides": [], "totals": {},
                "media": {"status": MISSING_STATUS}, "masters": {"status": MISSING_STATUS},
                "scope": {"status": PARTIAL_STATUS, "inheritance": "not-observed"},
            }
    planned_slides = plan.get("slides", []) if isinstance(plan, Mapping) and isinstance(plan.get("slides"), list) else []
    mapping: list[dict[str, Any]] = []
    for index, slide in enumerate(actual_pptx.get("slides", []) if isinstance(actual_pptx.get("slides"), list) else []):
        planned = planned_slides[index] if index < len(planned_slides) and isinstance(planned_slides[index], Mapping) else {}
        mapping.append({
            "slide_index": index + 1,
            "slide_id": planned.get("slide_id", slide.get("slide_id", f"slide-{index + 1}")),
            "planned_medium": planned.get("dominant_medium"),
            "planned_structure": planned.get("structure_signature"),
            "actual_title": slide.get("title", ""),
            "actual_title_candidate": slide.get("title_candidate", ""),
            "actual_title_source": slide.get("title_source", MISSING_STATUS),
            "actual_body": slide.get("body", ""),
            "actual_inventory": slide.get("inventory", {}),
            "differences": _slide_differences(planned, slide),
        })
    actual_pptx["design_mapping"] = mapping

    auditor_section = _auditor(auditor, report, snapshots=snapshots, ids=ids)
    calibration_section = _calibrations(calibrations, records=records, snapshots=snapshots, ids=ids)
    acceptance_content = content.get("acceptance_rules")
    if acceptance_ref is None and acceptance_content is None:
        acceptance_content = report.get("acceptance_contract", {"status": MISSING_STATUS})
    task_section = {
        "request": {"source_ref": task_ref, "status": RECORDED_STATUS if task_ref else MISSING_STATUS},
        "acceptance": {
            "source_ref": acceptance_ref,
            "status": RECORDED_STATUS if acceptance_ref else (RECORDED_STATUS if acceptance_content is not None else MISSING_STATUS),
            "content": acceptance_content,
        },
        "rules": {"source_ref": rules_ref, "status": RECORDED_STATUS if rules_ref else MISSING_STATUS},
    }
    work_report: dict[str, Any] = {
        "contract": WORK_REPORT_CONTRACT,
        "version": WORK_REPORT_VERSION,
        "task": task_section,
        "substantive_content": _substantive(report, content),
        "storyline": _substantive(report, content)["storyline"],
        "evidence": _substantive(report, content)["evidence"],
        "copy": _copy_section(content, note_rows),
        "art_direction": _art_direction(content),
        "calibrations": calibration_section,
        "supervisor_reviews": calibration_section,
        "stages": [dict(item) for item in records or [] if isinstance(item, Mapping)],
        "stage_record_refs": record_refs,
        "stage_artifact_bindings": artifact_rows,
        "actual_pptx": actual_pptx,
        "auditor": auditor_section,
        "release": _release(report, auditor_section),
        "source_snapshots": snapshots,
        "provenance": {
            "source_snapshot_ids": [item.get("source_id") for item in snapshots],
            "record_count": len([item for item in records or [] if isinstance(item, Mapping)]),
            "source_status": RECORDED_STATUS if snapshots else MISSING_STATUS,
        },
    }
    return work_report


def attach_work_report(report: Mapping[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Attach the collected work report, rejecting an altered prior version."""

    result = copy.deepcopy(dict(report))
    work_report = build_work_report(report=result, **kwargs)
    existing = result.get("work_report")
    if existing is not None and existing != work_report:
        raise WorkReportError("existing work_report differs from immutable source collection")
    digest = canonical_sha256(work_report)
    if result.get("work_report_sha256") is not None and result.get("work_report_sha256") != digest:
        raise WorkReportError("existing work_report_sha256 does not match work_report")
    result["work_report"] = work_report
    result["work_report_sha256"] = digest
    return result


def _resolve_part(base: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    parts: list[str] = []
    for part in (PurePosixPath(base).parent / target).parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part not in {".", "/", ""}:
            parts.append(part)
    return "/".join(parts)


def _natural(value: str) -> list[Any]:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", value)]


def _ordered_slides(archive: zipfile.ZipFile) -> list[str]:
    names = set(archive.namelist())
    presentation = "ppt/presentation.xml"
    rels_part = "ppt/_rels/presentation.xml.rels"
    if presentation not in names:
        raise WorkReportError("PPTX is missing ppt/presentation.xml")
    if rels_part not in names:
        raise WorkReportError("PPTX is missing presentation relationships; slide order is unverified")
    root = ET.fromstring(archive.read(presentation))
    rels = ET.fromstring(archive.read(rels_part))
    target_by_id = {
        item.get("Id"): _resolve_part(presentation, item.get("Target", ""))
        for item in rels.findall("pr:Relationship", NS)
    }
    result: list[str] = []
    slide_ids = root.findall(".//p:sldIdLst/p:sldId", NS)
    for slide_id in slide_ids:
        relation_id = slide_id.get(f"{{{NS['r']}}}id")
        part = target_by_id.get(relation_id)
        if part not in names:
            raise WorkReportError(f"presentation slide relationship {relation_id!r} is missing or unresolved")
        if not part.startswith("ppt/slides/"):
            raise WorkReportError(f"presentation relationship {relation_id!r} is not a slide part")
        result.append(part)
    listed = {name for name in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)}
    if listed - set(result):
        raise WorkReportError("PPTX contains slide parts that are absent from presentation order")
    if not slide_ids and listed:
        raise WorkReportError("presentation has slide parts but no ordered slide id list")
    return result


def _rels(archive: zipfile.ZipFile, part: str) -> list[tuple[str, str, str]]:
    rels_part = str(PurePosixPath(part).parent / "_rels" / (PurePosixPath(part).name + ".rels"))
    if rels_part not in archive.namelist():
        return []
    root = ET.fromstring(archive.read(rels_part))
    result: list[tuple[str, str, str]] = []
    for item in root.findall("pr:Relationship", NS):
        if item.get("TargetMode") == "External":
            continue
        result.append((item.get("Id", ""), item.get("Type", ""), _resolve_part(part, item.get("Target", ""))))
    return result


def _texts(node: ET.Element) -> list[str]:
    return [str(item.text) for item in node.findall(".//a:t", NS) if item.text]


def _placeholder(shape: ET.Element) -> str | None:
    item = shape.find(".//p:ph", NS)
    return item.get("type") if item is not None else None


def _inventory(root: ET.Element) -> dict[str, int]:
    shapes = root.findall(".//p:sp", NS)
    frames = root.findall(".//p:graphicFrame", NS)
    tables = charts = diagrams = 0
    for frame in frames:
        for data in frame.findall(".//a:graphicData", NS):
            uri = (data.get("uri") or "").casefold()
            if data.find("a:tbl", NS) is not None or uri.endswith("/table"):
                tables += 1
            if "drawingml/2006/chart" in uri:
                charts += 1
            if "drawingml/2006/diagram" in uri:
                diagrams += 1
    return {
        "shapes": len(shapes),
        "text_shapes": sum(1 for shape in shapes if shape.findall(".//a:t", NS)),
        "connectors": len(root.findall(".//p:cxnSp", NS)),
        "pictures": len(root.findall(".//p:pic", NS)),
        "graphic_frames": len(frames),
        "tables": tables,
        "charts": charts,
        "diagrams": diagrams,
    }


def _pptx_notes(archive: zipfile.ZipFile, part: str) -> dict[str, Any]:
    target = next((target for _id, kind, target in _rels(archive, part) if "notesslide" in kind.casefold()), None)
    if target is None or target not in archive.namelist():
        return {"status": MISSING_STATUS, "available": False, "part": None, "text": ""}
    text = "\n".join(_texts(ET.fromstring(archive.read(target))))
    return {"status": RECORDED_STATUS, "available": True, "part": target, "text": text}


def _slide(archive: zipfile.ZipFile, part: str, index: int) -> dict[str, Any]:
    root = ET.fromstring(archive.read(part))
    title: list[str] = []
    body: list[str] = []
    text_shapes: list[dict[str, Any]] = []
    for shape in root.findall(".//p:sp", NS):
        values = _texts(shape)
        if not values:
            continue
        value = "\n".join(values)
        kind = _placeholder(shape)
        text_shapes.append({"placeholder": kind, "text": value})
        if kind in {"title", "ctrTitle"}:
            title.extend(values)
        else:
            body.extend(values)
    declared_title = "\n".join(title)
    title_candidate = declared_title or (text_shapes[0]["text"] if text_shapes else "")
    title_text = declared_title
    body_text = "\n".join(body)
    frame_values: list[str] = []
    for frame in root.findall(".//p:graphicFrame", NS):
        frame_values.extend(_texts(frame))
    page_text = "\n".join(_texts(root))
    return {
        "slide_index": index,
        "part": part,
        "hidden": root.get("show") == "0",
        "title": title_text,
        "declared_title": declared_title,
        "title_candidate": title_candidate,
        "title_source": "declared-placeholder" if declared_title else ("first-text-candidate" if title_candidate else MISSING_STATUS),
        "body": "\n".join(item for item in (body_text, "\n".join(frame_values)) if item),
        "page_text": page_text,
        "text_shapes_content": text_shapes,
        "notes": _pptx_notes(archive, part),
        "inventory": _inventory(root),
        "object_names": sorted(item.get("name") for item in root.findall(".//p:cNvPr", NS) if item.get("name")),
    }


def _media(archive: zipfile.ZipFile, slide_parts: Sequence[str]) -> dict[str, Any]:
    names = set(archive.namelist())
    media = [item for item in archive.infolist() if item.filename.startswith("ppt/media/")]
    owners: dict[str, list[str]] = defaultdict(list)
    for rels_part in names:
        if not rels_part.endswith(".rels"):
            continue
        owner = str(PurePosixPath(rels_part).parent.parent / PurePosixPath(rels_part).name.removesuffix(".rels"))
        for _id, _kind, target in _rels(archive, owner):
            if target.startswith("ppt/media/"):
                owners[target].append(owner)
    items: list[dict[str, Any]] = []
    for info in sorted(media, key=lambda item: _natural(item.filename)):
        raw = archive.read(info.filename)
        part_owners = sorted(set(owners.get(info.filename, [])), key=_natural)
        slide_owners = [owner for owner in part_owners if owner in slide_parts]
        items.append({
            "path": info.filename,
            "bytes": len(raw),
            "sha256": _digest(raw),
            "referenced_by_slides": slide_owners,
            "referenced_by_parts": [owner for owner in part_owners if owner not in slide_parts],
            "used_by_slide": bool(slide_owners),
            "unused": not part_owners,
        })
    groups: dict[str, list[str]] = defaultdict(list)
    for item in items:
        groups[item["sha256"]].append(item["path"])
    return {
        "count": len(items),
        "media_count": len(items),
        "items": items,
        "slide_owned_count": sum(1 for item in items if item["used_by_slide"]),
        "unused_media": [item["path"] for item in items if item["unused"]],
        "duplicate_media_groups": [sorted(value, key=_natural) for value in groups.values() if len(value) > 1],
    }


def _masters(archive: zipfile.ZipFile) -> dict[str, Any]:
    parts = sorted((name for name in archive.namelist() if re.fullmatch(r"ppt/slideMasters/slideMaster\d+\.xml", name)), key=_natural)
    rows: list[dict[str, Any]] = []
    for part in parts:
        root = ET.fromstring(archive.read(part))
        rows.append({"part": part, "inventory": _inventory(root), "text": "\n".join(_texts(root))})
    return {"status": RECORDED_STATUS if rows else MISSING_STATUS, "count": len(rows), "parts": rows}


def inspect_pptx(path: Path | str) -> dict[str, Any]:
    """Inspect slide-owned OOXML in real presentation order."""

    pptx = _file(path)
    artifact = _meta(pptx)
    with zipfile.ZipFile(pptx) as archive:
        names = set(archive.namelist())
        if "[Content_Types].xml" not in names or "ppt/presentation.xml" not in names:
            raise WorkReportError("PPTX is missing required OOXML presentation parts")
        parts = _ordered_slides(archive)
        slides = [_slide(archive, part, index + 1) for index, part in enumerate(parts)]
        totals: dict[str, int] = {}
        for slide in slides:
            for key, value in slide["inventory"].items():
                totals[key] = totals.get(key, 0) + value
        core_properties_title = ""
        if "docProps/core.xml" in names:
            core_title = ET.fromstring(archive.read("docProps/core.xml")).find("dc:title", NS)
            core_properties_title = core_title.text if core_title is not None and core_title.text else ""
        cover_title = ""
        title_source = MISSING_STATUS
        if slides:
            cover_title = str(slides[0].get("declared_title") or slides[0].get("title_candidate") or "")
            if slides[0].get("declared_title"):
                title_source = "cover-slide-declared-title"
            elif cover_title:
                title_source = "cover-slide-first-text-candidate"
        title = cover_title or core_properties_title
        if not cover_title and core_properties_title:
            title_source = "core-properties"
        media = _media(archive, parts)
        masters = _masters(archive)
    return {
        "status": RECORDED_STATUS,
        "artifact": artifact,
            "title": title,
            "presentation_title": title,
            "core_properties_title": core_properties_title,
            "cover_title": cover_title,
            "title_source": title_source,
        "slide_count": len(slides),
        "slide_order": list(parts),
        "slides": slides,
        "totals": totals,
        "media": media,
        "masters": masters,
        "scope": {
            "slide_content": "slide XML parts only",
            "master_inheritance_observed": "not-observed",
            "master_parts_present": bool(masters.get("count")),
            "master_objects_in_slide_counts": False,
            "media_count_includes_unused": True,
            "hidden_slide_count": sum(1 for slide in slides if slide.get("hidden")),
            "notes_observed": any(slide.get("notes", {}).get("available") for slide in slides),
        },
    }


def _validate_snapshot(snapshot: Mapping[str, Any], index: int, errors: list[str], *, strict: bool = False) -> None:
    label = f"work_report.source_snapshots[{index}]"
    missing = sorted({"source_id", "path", "sha256", "bytes", "kind"} - set(snapshot))
    if missing:
        errors.append(f"{label}: missing keys {missing}")
        return
    raw_path = snapshot.get("path")
    digest = snapshot.get("sha256")
    size = snapshot.get("bytes")
    kind = snapshot.get("kind")
    if not isinstance(raw_path, str) or not Path(raw_path).is_absolute():
        errors.append(f"{label}.path: must be absolute")
        return
    if not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
        errors.append(f"{label}.sha256: must be lowercase SHA-256")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        errors.append(f"{label}.bytes: must be a non-negative integer")
    if kind not in {"json", "text", "binary"}:
        errors.append(f"{label}.kind: must be json, text, or binary")
        return
    try:
        raw = Path(raw_path).resolve().read_bytes()
    except OSError as exc:
        # The embedded snapshot remains readable after the originating run
        # directory is gone.  Publication performs this check while sources
        # are present; later standalone review records the limitation instead
        # of claiming that the external bytes were re-verified.
        if strict:
            errors.append(f"{label}: source unavailable for assembled report: {exc}")
        return
    if SHA256.fullmatch(str(digest)) and _digest(raw) != digest:
        errors.append(f"{label}.sha256: does not match current bytes")
    if isinstance(size, int) and not isinstance(size, bool) and len(raw) != size:
        errors.append(f"{label}.bytes: does not match current bytes")
    if kind == "binary":
        if "content" in snapshot or "raw_text" in snapshot:
            errors.append(f"{label}: binary snapshots must contain metadata only")
        return
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        errors.append(f"{label}: source is not UTF-8: {exc}")
        return
    if snapshot.get("raw_text") != text:
        errors.append(f"{label}.raw_text: must preserve full source text")
    if kind == "text" and snapshot.get("content") != text:
        errors.append(f"{label}.content: must preserve full source text")
    if kind == "json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            errors.append(f"{label}.content: source is no longer valid JSON: {exc}")
        else:
            if snapshot.get("content") != parsed:
                errors.append(f"{label}.content: does not match source JSON")


def _ref_errors(ref: Any, ids: set[str], label: str, errors: list[str]) -> None:
    if not isinstance(ref, Mapping):
        errors.append(f"{label}: must be a source reference")
        return
    if ref.get("source_id") not in ids:
        errors.append(f"{label}.source_id: does not resolve to a source snapshot")


def _actual_equal(stored: Mapping[str, Any], observed: Mapping[str, Any]) -> bool:
    left = copy.deepcopy(dict(stored))
    right = copy.deepcopy(dict(observed))
    for value in (left, right):
        artifact = value.get("artifact")
        if isinstance(artifact, Mapping):
            artifact = dict(artifact)
            artifact.pop("path", None)
            value["artifact"] = artifact
    return left == right


def _rebuild_from_embedded_sources(report: Mapping[str, Any]) -> dict[str, Any] | None:
    """Re-collect a report using its own explicit source bindings.

    This catches a caller deleting a substantive section, stage record, note,
    calibration, or Auditor result and then simply recalculating the outer
    work-report hash.  If the original source directory is unavailable, the
    embedded snapshots remain reviewable and this strong external check is
    deferred to the publication/verify-handoff path.
    """

    assembled = "assembly" in report
    work = report.get("work_report")
    snapshots = work.get("source_snapshots") if isinstance(work, Mapping) else None
    if not isinstance(snapshots, list) or not snapshots:
        if assembled:
            raise WorkReportError("assembled work_report must contain non-empty source_snapshots")
        return None
    valid_snapshots = [item for item in snapshots if isinstance(item, Mapping) and isinstance(item.get("source_id"), str)]
    if len(valid_snapshots) != len(snapshots):
        if assembled:
            raise WorkReportError("assembled work_report source_snapshots contains an invalid entry")
        return None
    for item in valid_snapshots:
        path = item.get("path")
        if not isinstance(path, str) or not Path(path).is_file():
            if assembled:
                raise WorkReportError(f"assembled work_report source is unavailable: {path}")
            return None

    assembly = report.get("assembly")
    assembly_inputs = assembly.get("inputs") if isinstance(assembly, Mapping) else None
    if not isinstance(assembly_inputs, Mapping):
        if assembled:
            raise WorkReportError("assembled work_report requires assembly.inputs for source recollection")
        return None
    artifacts: dict[str, Mapping[str, Any]] = {}
    for role, binding in assembly_inputs.items():
        if isinstance(binding, Mapping) and isinstance(binding.get("path"), str):
            artifacts[str(role)] = {key: binding.get(key) for key in META_FIELDS}
    if not artifacts:
        return None
    task = work.get("task") if isinstance(work, Mapping) else {}
    task_ref = assembly_inputs.get("task_request")
    acceptance_ref = assembly_inputs.get("acceptance_contract")
    rules_ref = assembly_inputs.get("supervisor_rules")
    if task_ref is None and isinstance(task, Mapping) and isinstance(task.get("request"), Mapping):
        task_ref = task["request"].get("source_ref")
    if acceptance_ref is None and isinstance(task, Mapping) and isinstance(task.get("acceptance"), Mapping):
        acceptance_ref = task["acceptance"].get("source_ref")
    if rules_ref is None and isinstance(task, Mapping) and isinstance(task.get("rules"), Mapping):
        rules_ref = task["rules"].get("source_ref")

    records = report.get("work_records")
    if not isinstance(records, list) or not records:
        if assembled:
            raise WorkReportError("assembled work_report requires report.work_records for source recollection")
        return None
    record_refs = work.get("stage_record_refs") if isinstance(work, Mapping) else []
    if not isinstance(record_refs, list) or len(record_refs) != len(records):
        raise WorkReportError("work_report stage_record_refs must cover every immutable work record")
    record_paths: list[Mapping[str, Any]] = []
    for index, ref in enumerate(record_refs):
        if not isinstance(ref, Mapping) or not isinstance(ref.get("path"), str):
            raise WorkReportError("work_report stage_record_refs contains an invalid binding")
        raw_record = Path(ref["path"]).read_text(encoding="utf-8")
        parsed_record = json.loads(raw_record)
        if parsed_record != records[index]:
            raise WorkReportError(f"work_report stage record {index + 1} differs from report.work_records")
        record_paths.append(ref)
    calibration_paths: dict[str, Mapping[str, Any]] = {}
    calibration_inputs = (
        ("calibration_logic_copy", "logic-to-copy"),
        ("calibration_copy_art_direction", "copy-to-art-direction"),
        ("calibration_art_direction_output", "art-direction-to-output"),
    )
    for role, fallback_step in calibration_inputs:
        binding = assembly_inputs.get(role)
        if not isinstance(binding, Mapping) or not isinstance(binding.get("path"), str):
            continue
        try:
            parsed = json.loads(Path(binding["path"]).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise WorkReportError(f"cannot reread calibration {role}: {exc}") from exc
        step = parsed.get("step", fallback_step) if isinstance(parsed, Mapping) else fallback_step
        calibration_paths[str(step)] = binding
    auditor_ref = assembly_inputs.get("auditor")
    if auditor_ref is None and isinstance(work, Mapping) and isinstance(work.get("auditor"), Mapping):
        auditor_ref = work["auditor"].get("artifact_ref")
    actual = work.get("actual_pptx") if isinstance(work, Mapping) and isinstance(work.get("actual_pptx"), Mapping) else {}
    actual_artifact = actual.get("artifact") if isinstance(actual, Mapping) else None
    pptx_path = actual_artifact if isinstance(actual_artifact, Mapping) else artifacts.get("pptx")
    if not isinstance(pptx_path, Mapping):
        if assembled:
            raise WorkReportError("assembled work_report requires a bound PPTX artifact for source recollection")
        return None
    return build_work_report(
        report=report,
        artifacts=artifacts,
        records=records,
        record_paths=record_paths,
        calibrations=calibration_paths,
        auditor=auditor_ref,
        pptx=pptx_path,
        task_request=task_ref,
        acceptance_rules=acceptance_ref,
        supervisor_rules=rules_ref,
    )


def validate_work_report(
    report: Mapping[str, Any],
    *,
    pptx: Path | str | None = None,
    markdown: Path | str | None = None,
    source_root: Path | None = None,
) -> list[str]:
    """Return integrity errors; disclosed partial/not-recorded data is valid."""

    errors: list[str] = []
    if not isinstance(report, Mapping):
        return ["report: must be an object"]
    work = report.get("work_report")
    if not isinstance(work, Mapping):
        return ["report.work_report: must be an object"]
    if work.get("contract") != WORK_REPORT_CONTRACT:
        errors.append(f"work_report.contract: expected {WORK_REPORT_CONTRACT}")
    if work.get("version") != WORK_REPORT_VERSION:
        errors.append(f"work_report.version: expected {WORK_REPORT_VERSION}")
    assembled = "assembly" in report
    if assembled:
        for section in (
            "task", "substantive_content", "copy", "art_direction", "calibrations",
            "stages", "actual_pptx", "auditor", "release", "source_snapshots",
        ):
            if section not in work:
                errors.append(f"work_report.{section}: required for an assembled 3.6 report")
        if isinstance(work.get("stages"), list) and work.get("stages") != report.get("work_records"):
            errors.append("work_report.stages: must preserve report.work_records verbatim")
        if isinstance(work.get("calibrations"), list) and work.get("supervisor_reviews") != work.get("calibrations"):
            errors.append("work_report.supervisor_reviews: must preserve calibrations verbatim")
        if not isinstance(work.get("source_snapshots"), list) or not work.get("source_snapshots"):
            errors.append("work_report.source_snapshots: assembled 3.6 delivery requires non-empty source snapshots")
    digest = report.get("work_report_sha256")
    if not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
        errors.append("report.work_report_sha256: must be lowercase SHA-256")
    elif canonical_sha256(work) != digest:
        errors.append("report.work_report_sha256: does not match work_report")
    snapshots = work.get("source_snapshots")
    if not isinstance(snapshots, list):
        errors.append("work_report.source_snapshots: must be an array")
        snapshots = []
    by_id: dict[str, Mapping[str, Any]] = {}
    by_path: dict[str, tuple[Any, Any]] = {}
    for index, snapshot in enumerate(snapshots):
        if not isinstance(snapshot, Mapping):
            errors.append(f"work_report.source_snapshots[{index}]: must be an object")
            continue
        _validate_snapshot(snapshot, index, errors, strict=assembled)
        source_id = snapshot.get("source_id")
        if isinstance(source_id, str):
            if source_id in by_id:
                errors.append(f"work_report.source_snapshots[{index}].source_id: duplicate")
            by_id[source_id] = snapshot
        raw_path = snapshot.get("path")
        if isinstance(raw_path, str):
            identity = (snapshot.get("sha256"), snapshot.get("bytes"))
            if raw_path in by_path and by_path[raw_path] != identity:
                errors.append(f"work_report.source_snapshots: conflicting identity for {raw_path}")
            by_path[raw_path] = identity
    ids = set(by_id)
    bindings = work.get("stage_artifact_bindings")
    if not isinstance(bindings, list):
        errors.append("work_report.stage_artifact_bindings: must be an array")
    else:
        for index, binding in enumerate(bindings):
            if not isinstance(binding, Mapping):
                errors.append(f"work_report.stage_artifact_bindings[{index}]: must be an object")
                continue
            ref = binding.get("source_ref")
            label = f"work_report.stage_artifact_bindings[{index}].source_ref"
            _ref_errors(ref, ids, label, errors)
            if isinstance(ref, Mapping) and ref.get("source_id") in by_id:
                source = by_id[str(ref["source_id"])]
                for key in META_FIELDS:
                    if ref.get(key) != source.get(key):
                        errors.append(f"{label}.{key}: differs from source snapshot")
    task = work.get("task")
    if isinstance(task, Mapping):
        for name in ("request", "acceptance", "rules"):
            section = task.get(name)
            if isinstance(section, Mapping) and section.get("source_ref") is not None:
                _ref_errors(section.get("source_ref"), ids, f"work_report.task.{name}.source_ref", errors)
    for index, ref in enumerate(work.get("stage_record_refs", []) if isinstance(work.get("stage_record_refs"), list) else []):
        _ref_errors(ref, ids, f"work_report.stage_record_refs[{index}]", errors)
    copy_section = work.get("copy")
    if isinstance(copy_section, Mapping) and isinstance(copy_section.get("notes"), list):
        for index, note in enumerate(copy_section["notes"]):
            if not isinstance(note, Mapping):
                continue
            ref = note.get("source_ref")
            if ref is None and note.get("status") == MISSING_STATUS:
                continue
            _ref_errors(ref, ids, f"work_report.copy.notes[{index}].source_ref", errors)
            source_id = ref.get("source_id") if isinstance(ref, Mapping) else None
            source = by_id.get(source_id)
            if isinstance(source, Mapping) and source.get("kind") in {"json", "text"} and note.get("text") != source.get("raw_text"):
                errors.append(f"work_report.copy.notes[{index}].text: differs from full source note")
    auditor = work.get("auditor")
    if isinstance(auditor, Mapping) and auditor.get("artifact_ref") is not None:
        ref = auditor.get("artifact_ref")
        _ref_errors(ref, ids, "work_report.auditor.artifact_ref", errors)
        source = by_id.get(ref.get("source_id")) if isinstance(ref, Mapping) else None
        if isinstance(source, Mapping) and auditor.get("raw_result") != source.get("content"):
            errors.append("work_report.auditor.raw_result: differs from bound Auditor artifact")
    for index, calibration in enumerate(work.get("calibrations", []) if isinstance(work.get("calibrations"), list) else []):
        if not isinstance(calibration, Mapping) or calibration.get("source_ref") is None:
            continue
        ref = calibration.get("source_ref")
        _ref_errors(ref, ids, f"work_report.calibrations[{index}].source_ref", errors)
        source = by_id.get(ref.get("source_id")) if isinstance(ref, Mapping) else None
        if isinstance(source, Mapping) and calibration.get("record") != source.get("content"):
            errors.append(f"work_report.calibrations[{index}].record: differs from calibration artifact")
    actual = work.get("actual_pptx")
    if not isinstance(actual, Mapping):
        errors.append("work_report.actual_pptx: must be an object")
    if pptx is not None and isinstance(actual, Mapping):
        try:
            observed = inspect_pptx(pptx)
        except (OSError, WorkReportError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
            if actual.get("status") not in {PARTIAL_STATUS, MISSING_STATUS}:
                errors.append(f"work_report.actual_pptx: cannot inspect current PPTX: {exc}")
        else:
            observed = dict(observed)
            observed["design_mapping"] = actual.get("design_mapping", [])
            if not _actual_equal(actual, observed):
                errors.append("work_report.actual_pptx: differs from current OOXML observation")
    if markdown is not None:
        try:
            current = _file(markdown).read_text(encoding="utf-8")
            expected = render_work_report_markdown(report)
            if current != expected:
                errors.append("work_report Markdown: differs from deterministic JSON rendering")
        except (OSError, UnicodeError, WorkReportError) as exc:
            errors.append(f"work_report Markdown: cannot read: {exc}")
    try:
        rebuilt = _rebuild_from_embedded_sources(report)
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        errors.append(f"work_report: immutable source recollection failed: {exc}")
    else:
        if rebuilt is not None and rebuilt != work:
            errors.append("work_report: content differs from the re-collected immutable source artifacts/records")
    return errors


def validate_work_report_or_raise(report: Mapping[str, Any], **kwargs: Any) -> None:
    errors = validate_work_report(report, **kwargs)
    if errors:
        raise WorkReportError(errors)


def _key_label(value: Any) -> str:
    """Turn a JSON key into a stable reader-facing label."""

    text = str(value).replace("_", " ").replace("-", " ")
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text).strip()
    return text[:1].upper() + text[1:] if text else "Value"


def _inline_value(value: Any) -> str:
    if value is None:
        return f"`{MISSING_STATUS}`"
    if isinstance(value, bool):
        return "`true`" if value else "`false`"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (Mapping, list, tuple)):
        # Mapping insertion order is source-dependent.  Canonical JSON keeps
        # the reader-facing Markdown identical after a JSON round-trip.
        text = canonical_json(value)
    else:
        text = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return f"`{MISSING_STATUS}`"
    if text in {MISSING_STATUS, PARTIAL_STATUS, RECORDED_STATUS, "deferred", "uncertain", "pass", "fail"}:
        return f"`{text}`"
    return text


def _fence(text: str) -> str:
    """Choose a code fence that cannot be closed by the source text."""

    longest = max((len(match.group(0)) for match in re.finditer(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def _fenced_lines(text: str, level: int = 0, language: str = "text") -> list[str]:
    prefix = "  " * level
    fence = _fence(text)
    body = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return [f"{prefix}{fence}{language}", *(f"{prefix}{line}" for line in body), f"{prefix}{fence}"]


def _value_lines(value: Any, level: int = 0, *, skip: set[str] | None = None) -> list[str]:
    """Render structured JSON as nested Markdown fields and lists."""

    prefix = "  " * level
    skipped = skip or set()
    if isinstance(value, Mapping):
        if not value:
            return [f"{prefix}- {{}} (no entries recorded)"]
        lines: list[str] = []
        for key in sorted(value, key=lambda item: str(item)):
            key_text = str(key)
            if key_text in skipped:
                continue
            item = value[key]
            label = _key_label(key_text)
            if isinstance(item, (Mapping, list, tuple)):
                lines.append(f"{prefix}- {label}:")
                child = _value_lines(item, level + 1)
                lines.extend(child or [f"{'  ' * (level + 1)}- `{MISSING_STATUS}`"])
            elif isinstance(item, str) and "\n" in item:
                lines.append(f"{prefix}- {label}:")
                lines.extend(_fenced_lines(item, level + 1))
            else:
                lines.append(f"{prefix}- {label}: {_inline_value(item)}")
        return lines or [f"{prefix}- `{MISSING_STATUS}`"]
    if isinstance(value, (list, tuple)):
        if not value:
            return [f"{prefix}- [] (no entries recorded)"]
        lines = []
        for item in value:
            if isinstance(item, (Mapping, list, tuple)):
                lines.append(f"{prefix}-")
                lines.extend(_value_lines(item, level + 1))
            elif isinstance(item, str) and "\n" in item:
                lines.append(f"{prefix}-")
                lines.extend(_fenced_lines(item, level + 1))
            else:
                lines.append(f"{prefix}- {_inline_value(item)}")
        return lines
    if isinstance(value, str) and "\n" in value:
        return _fenced_lines(value, level)
    return [f"{prefix}- {_inline_value(value)}"]


def _json_text(value: Any) -> str:
    """Return deterministic, readable field/list Markdown for structured JSON."""

    return "\n".join(_value_lines(value))


def _block(lines: list[str], heading: str, value: Any, *, skip: set[str] | None = None) -> None:
    lines.extend([heading, ""])
    rendered = _value_lines(value, skip=skip)
    lines.extend(rendered or [f"- `{MISSING_STATUS}`"])
    lines.append("")


def _details(lines: list[str], summary: str, value: Any, *, skip: set[str] | None = None) -> None:
    """Keep administrative or repeated structure available without burying the narrative."""

    lines.extend(["<details>", f"<summary>{summary}</summary>", ""])
    rendered = _value_lines(value, skip=skip)
    lines.extend(rendered or [f"- `{MISSING_STATUS}`"])
    lines.extend(["", "</details>", ""])


def _text_value(value: Any, *names: str) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, Mapping):
        for name in names:
            candidate = value.get(name)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        for name in ("text", "content", "value", "body", "page_text"):
            candidate = value.get(name)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    return ""


def _title_text(actual: Mapping[str, Any]) -> str:
    for value in (
        actual.get("title"),
        actual.get("presentation_title"),
        actual.get("core_properties_title"),
        actual.get("cover_title"),
        actual.get("title_candidate"),
    ):
        text = _text_value(value, "text", "value", "title")
        if text:
            return text.replace("\n", " ")
    return "Untitled presentation"


def _snapshot_content(work: Mapping[str, Any], reference: Any) -> Any:
    """Resolve one already-bound snapshot for reader-facing task/source prose."""

    source_id = reference.get("source_id") if isinstance(reference, Mapping) else None
    snapshots = work.get("source_snapshots")
    if source_id is None or not isinstance(snapshots, list):
        return None
    for snapshot in snapshots:
        if not isinstance(snapshot, Mapping) or snapshot.get("source_id") != source_id:
            continue
        if snapshot.get("kind") == "binary":
            return None
        return snapshot.get("content", snapshot.get("raw_text"))
    return None


def _render_task(lines: list[str], work: Mapping[str, Any]) -> None:
    """Render task prose and acceptance requirements before binding metadata."""

    lines.extend(["## 任务、验收与规则 / Task, acceptance, and rules", ""])
    task = work.get("task")
    if not isinstance(task, Mapping):
        lines.extend([f"- `{MISSING_STATUS}`", ""])
        return

    for key, label in (("request", "用户原始请求 / User request"), ("rules", "Supervisor 规则 / Supervisor rules")):
        entry = task.get(key)
        lines.extend([f"### {label}", ""])
        content = _snapshot_content(work, entry.get("source_ref") if isinstance(entry, Mapping) else None)
        if content is None and isinstance(entry, Mapping):
            content = entry.get("content")
        if content is None:
            status = entry.get("status") if isinstance(entry, Mapping) else None
            lines.append(f"- `{status or MISSING_STATUS}`")
        elif isinstance(content, str) and "\n" in content:
            lines.extend(_fenced_lines(content, language="text"))
        else:
            lines.extend(_value_lines(content))
        lines.append("")

    acceptance = task.get("acceptance")
    lines.extend(["### 验收要求 / Acceptance requirements", ""])
    if not isinstance(acceptance, Mapping):
        lines.extend([f"- `{MISSING_STATUS}`", ""])
        return
    lines.append(f"- Status: {_inline_value(acceptance.get('status'))}")
    content = acceptance.get("content")
    if not isinstance(content, Mapping):
        resolved = _snapshot_content(work, acceptance.get("source_ref"))
        content = resolved if isinstance(resolved, Mapping) else content
    if isinstance(content, Mapping):
        requirements = content.get("requirements")
        if isinstance(requirements, list):
            if requirements:
                for index, requirement in enumerate(requirements, 1):
                    if not isinstance(requirement, Mapping):
                        lines.append(f"- Requirement {index}: {_inline_value(requirement)}")
                        continue
                    identifier = _first(requirement, "requirement_id", "id") or f"requirement-{index}"
                    statement = _first(requirement, "statement", "requirement", "description") or MISSING_STATUS
                    classification = _first(requirement, "classification", "priority") or MISSING_STATUS
                    owner = _first(requirement, "owner_stage", "owner") or MISSING_STATUS
                    verification = _first(requirement, "verification_method", "verification")
                    lines.append(f"- `{identifier}` — {statement}")
                    lines.append(f"  - Classification: {_inline_value(classification)}; owner: {_inline_value(owner)}")
                    if verification is not None:
                        lines.append(f"  - Verification: {_inline_value(verification)}")
            else:
                lines.append("- Requirements: [] (no requirement entries recorded)")
        else:
            lines.append(f"- Requirements: `{MISSING_STATUS}`")
        for key in ("objective", "desired_outcome", "scope", "delivery_policy", "release_conditions"):
            if key in content:
                lines.append(f"- {_key_label(key)}: {_inline_value(content.get(key)) if not isinstance(content.get(key), (Mapping, list, tuple)) else ''}")
                if isinstance(content.get(key), (Mapping, list, tuple)):
                    lines.extend(_value_lines(content.get(key), 1))
        lines.append("")
        _details(lines, "Full acceptance contract details", content)
    else:
        lines.append(f"- Content: `{MISSING_STATUS}`")
        lines.append("")


def _page_number(page: Mapping[str, Any], fallback: int) -> Any:
    return _first(page, "page", "slide_number", "slide_index", "index") or fallback


def _compact_mapping(value: Any) -> str:
    if not isinstance(value, Mapping):
        return _inline_value(value)
    parts: list[str] = []
    for key in sorted(value, key=lambda item: str(item)):
        item = value[key]
        if isinstance(item, (Mapping, list, tuple)):
            continue
        parts.append(f"{key}={_inline_value(item)}")
    return "; ".join(parts) if parts else "{} (no entries recorded)"


def _report_limitations(work: Mapping[str, Any], actual: Mapping[str, Any], auditor: Mapping[str, Any], release: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for source in (actual, auditor, release):
        if not isinstance(source, Mapping):
            continue
        inspection_error = source.get("inspection_error")
        if inspection_error:
            values.append(str(inspection_error))
        for key in ("limitations", "deferred", "open_issues"):
            item = source.get(key)
            if isinstance(item, list):
                values.extend(str(entry) for entry in item if entry not in (None, ""))
            elif isinstance(item, str) and item.strip():
                values.append(item.strip())
    for key in ("task", "copy", "art_direction", "auditor"):
        section = work.get(key)
        if isinstance(section, Mapping) and section.get("status") in {MISSING_STATUS, PARTIAL_STATUS}:
            values.append(f"{_key_label(key)} section: {section.get('status')}")
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def _render_summary(lines: list[str], report: Mapping[str, Any], work: Mapping[str, Any], actual: Mapping[str, Any], auditor: Mapping[str, Any], release: Mapping[str, Any], digest: str) -> None:
    lines.extend(["## 摘要 / Summary", ""])
    lines.append(f"- Presentation: {_title_text(actual)}")
    for key in ("core_properties_title", "cover_title", "title_source"):
        if key in actual:
            value = actual.get(key)
            display = _text_value(value, "text", "value", "title") if isinstance(value, Mapping) else value
            lines.append(f"- {_key_label(key)}: {_inline_value(display)}")
    count = _first(actual, "page_count", "slide_count")
    lines.append(f"- Actual pages/slides: {_inline_value(count)}")
    totals = _first(actual, "totals", "statistics", "object_counts")
    lines.append(f"- Actual object/media statistics: {_compact_mapping(totals)}")
    media = actual.get("media") if isinstance(actual.get("media"), Mapping) else {}
    if media:
        media_count = _first(media, "count", "media_count")
        unused = media.get("unused_media")
        duplicates = media.get("duplicate_media_groups")
        lines.append(f"- Media: count={_inline_value(media_count)}; unused={_inline_value(len(unused) if isinstance(unused, list) else unused)}; duplicate-groups={_inline_value(len(duplicates) if isinstance(duplicates, list) else duplicates)}")
    notes_observed = _first(actual.get("scope", {}) if isinstance(actual.get("scope"), Mapping) else {}, "notes_observed", "notes_available")
    lines.append(f"- Speaker notes observed: {_inline_value(notes_observed)}")
    lines.append(f"- Report JSON SHA-256: `{digest}`")
    lines.append(f"- Run ID: `{report.get('run_id', MISSING_STATUS)}`")
    lines.append(f"- Task request SHA-256: `{report.get('task_request_sha256', MISSING_STATUS)}`")
    limitations = _report_limitations(work, actual, auditor, release)
    if limitations:
        lines.append("- Limitations recorded:")
        lines.extend(f"  - {item}" for item in limitations)
    elif any(isinstance(source, Mapping) and "limitations" in source for source in (actual, auditor, release)):
        lines.append("- Limitations: [] (no limitations recorded)")
    else:
        lines.append(f"- Limitations: `{MISSING_STATUS}`")
    lines.append("")


def _render_substantive(lines: list[str], work: Mapping[str, Any]) -> None:
    lines.extend(["## 研究、证据、假设与故事线 / Research, evidence, assumptions, and story", ""])
    lines.append("_The fields below come from structured primary artifacts. A `not-recorded` field means it was not separately captured there; consult Stage work notes below for additional recorded context._")
    lines.append("")
    substantive = work.get("substantive_content")
    if isinstance(substantive, Mapping):
        preferred = (
            "knowledge_requirements", "sources", "facts", "research", "evidence",
            "contradictions", "counterevidence", "definitions", "metric_dictionary",
            "assumptions", "unknowns", "open_items", "deck_message_tree",
            "storyline", "narrative", "tradeoffs", "excluded_options", "decisions",
        )
        keys = [key for key in preferred if key in substantive]
        keys.extend(sorted((str(key) for key in substantive if str(key) not in keys), key=str))
        if not keys:
            lines.append("- {} (no entries recorded)")
            lines.append("")
        else:
            for key in keys:
                if key == "logic_layer":
                    _details(lines, "Logic layer details / Logic layer 详情", substantive.get(key))
                else:
                    _block(lines, f"### {_key_label(key)}", substantive.get(key))
    else:
        lines.append(f"- `{MISSING_STATUS}`")
        lines.append("")
    for key, label in (("storyline", "Storyline"), ("evidence", "Evidence")):
        value = work.get(key)
        if value is not None and (not isinstance(substantive, Mapping) or substantive.get(key) != value):
            _block(lines, f"### {label}", value)


def _render_copy(lines: list[str], work: Mapping[str, Any]) -> None:
    copy_section = work.get("copy")
    lines.extend(["## 最终文案 / Final copy", ""])
    if not isinstance(copy_section, Mapping):
        lines.append(f"- `{MISSING_STATUS}`")
        lines.append("")
        return
    for key in ("artifact_source_id", "artifact_status", "slides_status", "notes_status"):
        if key in copy_section:
            lines.append(f"- {_key_label(key)}: {_inline_value(copy_section.get(key))}")
    slides = copy_section.get("slides")
    if not isinstance(slides, list) and isinstance(copy_section.get("copy_layer"), Mapping):
        candidate_slides = copy_section["copy_layer"].get("slides")
        slides = candidate_slides if isinstance(candidate_slides, list) else slides
    if isinstance(slides, list) and slides:
        lines.append("")
        for index, slide in enumerate(slides, 1):
            if not isinstance(slide, Mapping):
                lines.append(f"- Slide {index}: {_inline_value(slide)}")
                continue
            identifier = _first(slide, "slide_id", "page_id", "id") or f"slide-{index}"
            units = slide.get("copy_units") if isinstance(slide.get("copy_units"), list) else []
            unit_titles = [unit for unit in units if isinstance(unit, Mapping) and str(unit.get("role", "")).casefold() in {"title", "headline"}]
            unit_story = [unit for unit in units if isinstance(unit, Mapping) and "story" in str(unit.get("role", "")).casefold()]
            title = _text_value(_first(slide, "title", "headline", "title_text"), "text", "value") or (str(unit_titles[0].get("text")) if unit_titles and unit_titles[0].get("text") is not None else "")
            storyline = _text_value(_first(slide, "storyline", "storyline_text", "supporting_copy"), "text", "value") or (str(unit_story[0].get("text")) if unit_story and unit_story[0].get("text") is not None else "")
            lines.append(f"### {identifier}" + (f" — {title}" if title else ""))
            if title:
                lines.append(f"- Title: {title}")
            if storyline:
                lines.append(f"- Storyline: {storyline}")
            if units:
                lines.append("- Copy units:")
                for unit_index, unit in enumerate(units, 1):
                    if not isinstance(unit, Mapping):
                        lines.append(f"  - {unit_index}: {_inline_value(unit)}")
                        continue
                    unit_id = _first(unit, "copy_id", "id") or f"unit-{unit_index}"
                    role = _first(unit, "role", "function")
                    text = _text_value(unit, "text", "value", "content") or MISSING_STATUS
                    lines.append(f"  - `{unit_id}`" + (f" ({role})" if role else "") + f": {text}")
            elif not title and not storyline:
                lines.append(f"- `{MISSING_STATUS}`")
            lines.append("")
            _details(lines, f"Full copy metadata for {identifier}", slide, skip={"notes", "speaker_notes", "work_notes"})
        if isinstance(copy_section.get("copy_layer"), Mapping):
            _details(lines, "Full copy-layer metadata", copy_section.get("copy_layer"), skip={"slides", "notes", "speaker_notes", "work_notes"})
    elif isinstance(copy_section.get("copy_layer"), Mapping):
        _details(lines, "Full copy-layer metadata", copy_section.get("copy_layer"), skip={"notes", "speaker_notes", "work_notes"})
    else:
        _block(lines, "### 文案记录 / Copy record", copy_section, skip={"notes", "speaker_notes", "work_notes"})


def _note_text_and_content(note: Any) -> tuple[str, Any]:
    if isinstance(note, Mapping):
        text = _text_value(note, "text", "raw_text", "markdown")
        if text:
            return text, note.get("content")
        content = note.get("content")
        if isinstance(content, str):
            return content.strip(), content
        return "", content
    if isinstance(note, str):
        return note.strip(), note
    return "", note


def _note_rows(work: Mapping[str, Any]) -> list[dict[str, Any]]:
    snapshots = work.get("source_snapshots")
    by_id = {
        str(item.get("source_id")): item
        for item in snapshots
        if isinstance(snapshots, list) and isinstance(item, Mapping) and item.get("source_id") is not None
    }
    result: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(stage: Any, role: Any, value: Any, source_ref: Any = None) -> None:
        source_id = source_ref.get("source_id") if isinstance(source_ref, Mapping) else None
        key = str(source_id or f"{stage}:{role}:{len(result)}")
        if source_id and key in seen:
            return
        text, content = _note_text_and_content(value)
        if source_id and source_id in by_id:
            snap = by_id[source_id]
            text = _text_value(snap, "raw_text", "text") or text
            content = snap.get("content", content)
        if not text and content is None and not isinstance(value, Mapping):
            return
        seen.add(key)
        status = value.get("status") if isinstance(value, Mapping) else None
        if status is None and source_id and source_id in by_id:
            status = RECORDED_STATUS if by_id[source_id].get("kind") in {"json", "text"} else PARTIAL_STATUS
        result.append({"stage": stage or "unknown", "role": role or "work-notes", "source_ref": source_ref, "text": text, "content": content, "status": status or RECORDED_STATUS})

    copy_section = work.get("copy")
    if isinstance(copy_section, Mapping) and isinstance(copy_section.get("notes"), list):
        for note in copy_section["notes"]:
            add(note.get("stage") if isinstance(note, Mapping) else "copy", note.get("role") if isinstance(note, Mapping) else "work-notes", note, note.get("source_ref") if isinstance(note, Mapping) else None)

    bindings = work.get("stage_artifact_bindings")
    if isinstance(bindings, list):
        for binding in bindings:
            if not isinstance(binding, Mapping) or "note" not in str(binding.get("role", "")).casefold():
                continue
            ref = binding.get("source_ref")
            source_id = ref.get("source_id") if isinstance(ref, Mapping) else None
            add(binding.get("stage"), binding.get("role"), by_id.get(str(source_id), {"status": MISSING_STATUS}), ref)

    stages = work.get("stages")
    stage_items: list[tuple[Any, Any]] = []
    if isinstance(stages, Mapping):
        stage_items = list(stages.items())
    elif isinstance(stages, list):
        stage_items = [(item.get("stage") if isinstance(item, Mapping) else f"stage-{index + 1}", item) for index, item in enumerate(stages)]
    for stage, record in stage_items:
        if not isinstance(record, Mapping):
            continue
        for key in ("work-notes", "work_notes", "notes", "note"):
            if key in record:
                value = record.get(key)
                if isinstance(value, list):
                    for item in value:
                        add(stage, key, item, item.get("source_ref") if isinstance(item, Mapping) else None)
                else:
                    add(stage, key, value, value.get("source_ref") if isinstance(value, Mapping) else None)
    return result


def _render_work_notes(lines: list[str], work: Mapping[str, Any]) -> None:
    lines.extend(["## 阶段工作笔记 / Stage work notes", ""])
    notes = _note_rows(work)
    if not notes:
        explicit_empty = False
        copy_section = work.get("copy")
        if isinstance(copy_section, Mapping) and (
            copy_section.get("notes_status") in {RECORDED_STATUS, PARTIAL_STATUS}
            or isinstance(copy_section.get("notes"), list)
        ):
            explicit_empty = True
        stages = work.get("stages")
        stage_values = stages.values() if isinstance(stages, Mapping) else stages if isinstance(stages, list) else []
        for record in stage_values:
            if isinstance(record, Mapping) and any(key in record for key in ("work-notes", "work_notes", "notes", "note")):
                explicit_empty = True
                break
        if explicit_empty:
            lines.extend(["- [] (no richer stage notes recorded)", ""])
        else:
            lines.extend([f"- `{MISSING_STATUS}`: no richer stage note was captured.", ""])
        return
    for index, note in enumerate(notes, 1):
        stage = note.get("stage") or "unknown"
        role = note.get("role") or "work-notes"
        lines.extend([f"### {stage} — {role}", "", f"- Status: {_inline_value(note.get('status'))}"])
        ref = note.get("source_ref")
        if isinstance(ref, Mapping):
            lines.append(f"- Source: `{ref.get('source_id', MISSING_STATUS)}` ({ref.get('sha256', MISSING_STATUS)})")
        text, content = note.get("text", ""), note.get("content")
        if isinstance(content, (Mapping, list, tuple)):
            lines.append("")
            lines.extend(_value_lines(content))
        elif isinstance(text, str) and text.strip():
            lines.append("")
            lines.extend(f"> {line}" if line else ">" for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"))
        elif content is not None:
            lines.append("")
            lines.extend(_value_lines(content))
        else:
            lines.append(f"- Content: `{MISSING_STATUS}`")
        lines.append("")


def _render_design(lines: list[str], work: Mapping[str, Any], actual: Mapping[str, Any]) -> None:
    lines.extend(["## 设计意图与实际映射 / Design intent and actual mapping", ""])
    _block(lines, "### Art Direction 计划 / Art Direction plan", work.get("art_direction", {"status": MISSING_STATUS}))
    mapping = actual.get("design_mapping")
    if mapping is not None:
        _block(lines, "### 计划与实际映射 / Planned-to-actual mapping", mapping)


def _entry_items(value: Any, default_prefix: str) -> list[tuple[str, Any]]:
    if isinstance(value, Mapping):
        identity_keys = {"step", "calibration_id", "findings", "finding_dispositions", "record"}
        if identity_keys.intersection(value):
            return [(str(value.get("step") or value.get("calibration_id") or default_prefix), value)]
        return [(str(key), item) for key, item in value.items()]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [(str(item.get("step") or item.get("stage") or f"{default_prefix}-{index + 1}") if isinstance(item, Mapping) else f"{default_prefix}-{index + 1}", item) for index, item in enumerate(value)]
    return []


def _finding_key(value: Any, fallback: str) -> str:
    if isinstance(value, Mapping):
        return str(_first(value, "finding_id", "issue_id", "id", "finding_code") or fallback)
    return fallback


def _render_calibrations(lines: list[str], work: Mapping[str, Any]) -> None:
    lines.extend(["## 三轮 Supervisor 校准与逐发现处置 / Supervisor calibration and finding dispositions", ""])
    values = work.get("calibrations")
    if values is None:
        values = work.get("supervisor_reviews")
    entries = _entry_items(values, "calibration")
    if not entries:
        lines.append(f"- `{MISSING_STATUS}`" if values is None else "- [] (no calibration entries recorded)")
        lines.append("")
        return
    for label, item in entries:
        if not isinstance(item, Mapping):
            _block(lines, f"### {label}", item)
            continue
        step = item.get("step") or label
        identifier = item.get("calibration_id") or item.get("id")
        lines.append(f"### {step}" + (f" (`{identifier}`)" if identifier else ""))
        lines.append("")
        for key in ("source_ref", "disposition_status", "status"):
            if key in item:
                lines.append(f"- {_key_label(key)}: {_inline_value(item.get(key))}")
        record = item.get("record")
        if record is not None:
            _block(lines, "#### 校准记录 / Calibration record", record, skip={"findings", "finding_dispositions"})
        findings = item.get("findings")
        dispositions = item.get("finding_dispositions")
        finding_items = findings if isinstance(findings, list) else ([findings] if findings is not None else [])
        disposition_items = dispositions if isinstance(dispositions, list) else ([dispositions] if dispositions is not None else [])
        disposition_by_key = {_finding_key(value, f"disposition-{index + 1}"): value for index, value in enumerate(disposition_items)}
        if finding_items:
            lines.append("#### 发现与下游处置 / Findings and downstream disposition")
            lines.append("")
            for index, finding in enumerate(finding_items, 1):
                key = _finding_key(finding, f"finding-{index}")
                if isinstance(finding, Mapping):
                    summary = _text_value(finding, "summary", "finding", "evidence", "actual", "description")
                    lines.append(f"- Finding `{key}`" + (f": {summary}" if summary else ":"))
                else:
                    lines.append(f"- Finding `{key}`: {_inline_value(finding)}")
                disposition = disposition_by_key.pop(key, None)
                if disposition is None and index - 1 < len(disposition_items):
                    candidate = disposition_items[index - 1]
                    candidate_key = _finding_key(candidate, f"disposition-{index}")
                    if candidate_key == f"disposition-{index}":
                        disposition = disposition_by_key.pop(candidate_key, candidate)
                if disposition is None:
                    lines.append(f"  - Disposition: `{MISSING_STATUS}`")
                elif isinstance(disposition, Mapping):
                    status = _first(disposition, "status", "decision", "disposition") or MISSING_STATUS
                    reason = _text_value(disposition, "reason", "rationale", "summary")
                    lines.append(f"  - Disposition: {_inline_value(status)}" + (f" — {reason}" if reason else ""))
                else:
                    lines.append(f"  - Disposition: {_inline_value(disposition)}")
            for key in sorted(disposition_by_key):
                _block(lines, f"#### Unmatched disposition `{key}`", disposition_by_key[key])
        elif disposition_items:
            _block(lines, "#### 处置 / Dispositions", disposition_items)
        else:
            if isinstance(findings, list):
                lines.append("- Findings: [] (no findings recorded)")
            elif findings is None:
                lines.append(f"- Findings: `{MISSING_STATUS}`")
            else:
                lines.append(f"- Findings: {_inline_value(findings)}")
            lines.append("")


def _render_stages(lines: list[str], work: Mapping[str, Any]) -> None:
    lines.extend(["## 阶段记录 / Stage record coverage", ""])
    entries = _entry_items(work.get("stages"), "stage")
    if not entries:
        stages = work.get("stages")
        lines.append(f"- `{MISSING_STATUS}`" if stages is None else "- [] (no stage entries recorded)")
        lines.append("")
        return
    for label, item in entries:
        lines.append(f"### {label}")
        lines.append("")
        if isinstance(item, Mapping):
            selected = {key: value for key, value in item.items() if str(key) not in {"work-notes", "work_notes", "notes", "note"}}
            _block(lines, "#### 已记录工作 / Recorded work", selected)
        else:
            lines.append(f"- {_inline_value(item)}")
            lines.append("")


def _render_page(lines: list[str], page: Mapping[str, Any], fallback: int) -> None:
    number = _page_number(page, fallback)
    title = _text_value(page.get("title"), "text", "value")
    title_candidate = _text_value(page.get("title_candidate"), "text", "value", "title")
    title_source = "title"
    if not title:
        for candidate_key in ("title_candidate", "headline", "cover_title"):
            candidate = _text_value(page.get(candidate_key), "text", "value", "title")
            if candidate:
                title = candidate
                title_source = candidate_key
                break
    lines.append(f"### 第 {number} 页 / Page {number}" + (f" — {title}" if title else ""))
    lines.append("")
    observed_title_source = page.get("title_source")
    if observed_title_source not in (None, "", MISSING_STATUS):
        lines.append(f"- Title source: `{observed_title_source}`")
    elif title_source != "title":
        lines.append(f"- Title source: `{title_source}`")
    elif title_candidate and title_candidate != title:
        lines.append(f"- Title candidate (`title_candidate`): {title_candidate}")
    if "hidden" in page:
        lines.append(f"- Hidden slide flag: {_inline_value(page.get('hidden'))}")
    page_text = _text_value(page, "page_text", "text", "body")
    lines.append("#### 从页面对象提取的文字 / Text extracted from page objects")
    lines.append("")
    lines.append("_This text is not evidence of rendered visibility._")
    lines.append("")
    if page_text:
        lines.extend(f"> {line}" if line else ">" for line in page_text.split("\n"))
    else:
        lines.append(f"- `{MISSING_STATUS}`")
    notes = page.get("notes")
    if notes is None:
        notes = _first(page, "speaker_notes", "speakerNotes")
    note_text = _text_value(notes, "text", "raw_text", "content")
    lines.extend(["", "#### 演讲者备注 / Speaker notes", ""])
    note_status = notes.get("status") if isinstance(notes, Mapping) else None
    if note_text:
        lines.extend(f"> {line}" if line else ">" for line in note_text.split("\n"))
    elif note_status in {RECORDED_STATUS, PARTIAL_STATUS} or (isinstance(notes, str) and not notes.strip()):
        lines.append(f"- Note status: `{note_status or RECORDED_STATUS}`; empty note text was recorded.")
    else:
        lines.append(f"- `{MISSING_STATUS}`")
    inventory = page.get("inventory") or page.get("statistics") or page.get("object_counts")
    if inventory is not None:
        lines.extend(["", f"- Object statistics: {_compact_mapping(inventory) if isinstance(inventory, Mapping) else _inline_value(inventory)}"])
    lines.append("")


def _render_actual(lines: list[str], actual: Mapping[str, Any]) -> None:
    lines.extend(["## 实际生成的 PPTX / Actual generated PPTX", ""])
    for key in ("status", "artifact", "title", "presentation_title", "core_properties_title", "cover_title", "title_candidate", "title_source", "page_count", "slide_count", "slide_order", "totals", "statistics", "object_counts", "media", "masters", "master", "scope", "inspection_error"):
        if key in actual and key not in {"slides", "design_mapping"}:
            _block(lines, f"### {_key_label(key)}", actual.get(key))
    pages = actual.get("slides") if isinstance(actual.get("slides"), list) else actual.get("pages")
    if isinstance(pages, list) and pages:
        lines.append("### 每页实际文字与备注 / Per-page text and notes")
        lines.append("")
        for index, page in enumerate(pages, 1):
            if isinstance(page, Mapping):
                _render_page(lines, page, index)
            else:
                lines.append(f"- Page {index}: {_inline_value(page)}")
        lines.append("")
    elif pages is None:
        lines.extend(["### 每页实际文字与备注 / Per-page text and notes", "", f"- `{MISSING_STATUS}`", ""])
    else:
        lines.extend(["### 每页实际文字与备注 / Per-page text and notes", "", "- [] (no pages recorded)", ""])


def _render_auditor(lines: list[str], work: Mapping[str, Any]) -> None:
    auditor = work.get("auditor")
    lines.extend(["## Independent Auditor 观察 / Independent Auditor observations", ""])
    if not isinstance(auditor, Mapping):
        lines.append(f"- `{MISSING_STATUS}`")
        lines.append("")
        return
    for key in ("status", "artifact_ref", "audit_id", "audit_status", "coverage", "limitations", "findings"):
        if key in auditor:
            _block(lines, f"### {_key_label(key)}", auditor.get(key))
    raw = auditor.get("raw_result")
    if raw is not None:
        lines.extend(["### 原始审计详情 / Raw audit details", "", "<details>", "<summary>Open the bound Auditor result</summary>", ""])
        if isinstance(raw, Mapping):
            lines.extend(_value_lines(raw))
        else:
            lines.extend(_fenced_lines(str(raw), language="json"))
        lines.extend(["", "</details>", ""])


def _render_release(lines: list[str], work: Mapping[str, Any]) -> None:
    lines.extend(["## 放行、局限与改进 / Release, limitations, and improvements", ""])
    _block(lines, "### Release decision", work.get("release", {"status": MISSING_STATUS}))


def _render_source_trace(lines: list[str], work: Mapping[str, Any]) -> None:
    snapshots = work.get("source_snapshots")
    lines.extend(["## 来源追踪 / Source trace", ""])
    if not isinstance(snapshots, list) or not snapshots:
        lines.extend([f"- `{MISSING_STATUS}`", ""])
        return
    note_ids = {str(item.get("source_ref", {}).get("source_id")) for item in _note_rows(work) if isinstance(item.get("source_ref"), Mapping)}
    groups: list[list[Mapping[str, Any]]] = []
    group_keys: dict[tuple[Any, Any, Any, Any], int] = {}
    for snap in snapshots:
        if not isinstance(snap, Mapping):
            continue
        key = (snap.get("path"), snap.get("sha256"), snap.get("bytes"), snap.get("kind"))
        group_index = group_keys.get(key)
        if group_index is None:
            group_keys[key] = len(groups)
            groups.append([snap])
        else:
            groups[group_index].append(snap)
    for group in groups:
        first = group[0]
        source_ids = [str(item.get("source_id", MISSING_STATUS)) for item in group]
        source_label = ", ".join(f"`{source_id}`" for source_id in source_ids)
        lines.append(f"- {source_label} ({first.get('kind', MISSING_STATUS)}): path=`{first.get('path', MISSING_STATUS)}`, sha256=`{first.get('sha256', MISSING_STATUS)}`, bytes={first.get('bytes', MISSING_STATUS)}")
    lines.append("")
    lines.extend(["### 原始来源详情 / Raw source details", ""])
    for group in groups:
        first = group[0]
        source_ids = [str(item.get("source_id", MISSING_STATUS)) for item in group]
        source_label = ", ".join(f"<code>{source_id}</code>" for source_id in source_ids)
        lines.extend(["<details>", f"<summary>{source_label} — {first.get('kind', MISSING_STATUS)} source</summary>", ""])
        if any(source_id in note_ids for source_id in source_ids):
            lines.append("The full note is shown above under Stage work notes; this entry retains its trace only.")
        elif all(_source_is_rendered_elsewhere(source_id) for source_id in source_ids):
            lines.append("Structured content is rendered in the relevant report section; this entry retains its path and hash trace.")
        elif first.get("kind") == "binary":
            lines.append("Metadata only; binary content was not copied into the report.")
        else:
            raw = first.get("raw_text")
            if raw is None:
                raw = first.get("content", "")
            if isinstance(raw, (Mapping, list)):
                raw = json.dumps(raw, ensure_ascii=False, indent=2, sort_keys=True)
            language = "json" if first.get("kind") == "json" else "text"
            lines.extend(_fenced_lines(str(raw), language=language))
        lines.extend(["", "</details>", ""])


def _source_is_rendered_elsewhere(source_id: str) -> bool:
    """Avoid repeating large administrative snapshots already rendered above."""

    lowered = source_id.casefold()
    if lowered in {"plan", "qa", "inventory", "pptx", "task_request", "acceptance_rules", "supervisor_rules", "auditor"}:
        return True
    return lowered.startswith(("stage-record:", "calibration:"))


def _render_additional(lines: list[str], work: Mapping[str, Any]) -> None:
    known = {
        "contract", "version", "task", "substantive_content", "storyline", "evidence", "copy",
        "art_direction", "calibrations", "supervisor_reviews", "stages", "stage_record_refs",
        "stage_artifact_bindings", "actual_pptx", "auditor", "release", "source_snapshots", "provenance",
    }
    extra = {str(key): value for key, value in work.items() if str(key) not in known}
    if extra:
        _block(lines, "## 其他已记录 details / Additional recorded details", extra)


def render_work_report_markdown(report_or_work_report: Mapping[str, Any]) -> str:
    """Render a reader-facing Markdown report deterministically from report JSON."""

    if not isinstance(report_or_work_report, Mapping):
        raise WorkReportError("Markdown renderer expects an object")
    report = report_or_work_report
    work = report.get("work_report") if isinstance(report.get("work_report"), Mapping) else report
    if not isinstance(work, Mapping):
        raise WorkReportError("work_report must be an object")
    actual = work.get("actual_pptx") if isinstance(work.get("actual_pptx"), Mapping) else {}
    auditor = work.get("auditor") if isinstance(work.get("auditor"), Mapping) else {}
    release = work.get("release") if isinstance(work.get("release"), Mapping) else {}
    title = _title_text(actual)
    digest = canonical_sha256(work)
    lines: list[str] = [
        f"# 工作报告 / Work report — {title}",
        "",
        f"- Contract: `{work.get('contract', WORK_REPORT_CONTRACT)}`",
        f"- Version: `{work.get('version', WORK_REPORT_VERSION)}`",
        f"- Work-report JSON SHA-256: `{digest}`",
        "",
    ]
    _render_summary(lines, report, work, actual, auditor, release, digest)
    _render_task(lines, work)
    _render_substantive(lines, work)
    _render_copy(lines, work)
    _render_work_notes(lines, work)
    _render_design(lines, work, actual)
    _render_calibrations(lines, work)
    _render_stages(lines, work)
    _render_actual(lines, actual)
    _render_auditor(lines, work)
    _render_release(lines, work)
    _render_additional(lines, work)
    _render_source_trace(lines, work)
    if isinstance(report.get("stage_documents"), Mapping):
        lines.extend(["## 三份阶段交接文档 / Stage handoff documents", ""])
        for stage, document in report["stage_documents"].get("documents", {}).items():
            lines.extend([f"### {stage}", "", document.get("markdown", ""), ""])
        lines.extend(["## 图片稿与成品对照 / Design comparison", ""])
        for preview in report["stage_documents"].get("previews", []):
            mime = "image/png" if preview['base64'].startswith('iVBOR') else "image/jpeg"
            lines.extend([f"### {preview['slide_id']}", "", f"![Locked design](data:{mime};base64,{preview['base64']})", ""])
        _block(lines, "### 审计观察 / Audit observations", report.get("design_comparison"))
    return "\n".join(lines).rstrip() + "\n"


def _manifest_record(bundle: Path, item: Mapping[str, Any], role: str) -> dict[str, Any]:
    if item.get("role") != role:
        raise WorkReportError(f"manifest must bind {role}")
    raw = item.get("path")
    if not isinstance(raw, str) or not raw.strip():
        raise WorkReportError(f"manifest {role} path is missing")
    path = (bundle / raw).resolve()
    if not path.is_relative_to(bundle.resolve()) or not path.is_file():
        raise WorkReportError(f"manifest {role} path is missing or escapes bundle")
    data = path.read_bytes()
    if _digest(data) != item.get("sha256") or len(data) != item.get("bytes"):
        raise WorkReportError(f"manifest {role} hash/byte binding mismatch")
    return {"role": role, "path": str(path), "sha256": _digest(data), "bytes": len(data)}


def verify_handoff(
    bundle: Path | str,
    *,
    pptx: Path | str | None = None,
    report: Path | str | None = None,
    markdown: Path | str | None = None,
) -> dict[str, Any]:
    """Verify the exact bundle paths and return a handoff receipt."""

    root = Path(bundle).expanduser().resolve()
    if not root.is_dir():
        raise WorkReportError(f"handoff bundle is not a directory: {root}")
    manifest_path = root / "delivery-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WorkReportError(f"delivery manifest cannot be read: {exc}") from exc
    if not isinstance(manifest, Mapping):
        raise WorkReportError("delivery manifest must be an object")
    if manifest.get("contract") != DELIVERY_MANIFEST_CONTRACT:
        raise WorkReportError("delivery manifest contract mismatch")
    if manifest.get("required_artifacts") != ["pptx", "supervision-report"]:
        raise WorkReportError("delivery manifest required_artifacts must be the primary PPTX/report pair")
    files = manifest.get("files")
    if not isinstance(files, list) or [item.get("role") for item in files if isinstance(item, Mapping)] != ["pptx", "supervision-report"]:
        raise WorkReportError("delivery manifest files must bind exactly PPTX then supervision-report")
    by_role = {item.get("role"): item for item in files if isinstance(item, Mapping)}
    derived = manifest.get("derived_files", [])
    if not isinstance(derived, list) or [item.get("role") for item in derived if isinstance(item, Mapping)] not in (["work-report-markdown"], ["work-report-markdown", "stage-handoff-archive"]):
        raise WorkReportError("delivery manifest derived_files must bind work-report-markdown and optional stage-handoff-archive")
    derived_by_role = {item.get("role"): item for item in derived if isinstance(item, Mapping)}
    required = {role: by_role.get(role) for role in ("pptx", "supervision-report")}
    required["work-report-markdown"] = derived_by_role.get("work-report-markdown")
    if any(not isinstance(item, Mapping) for item in required.values()):
        raise WorkReportError("delivery manifest must bind PPTX, supervision-report, and work-report-markdown")
    validation = manifest.get("validation")
    if not isinstance(validation, Mapping) or validation.get("report_contract_version") != WORK_REPORT_VERSION or validation.get("publisher") != "scripts/publish_supervised_pair.py" or validation.get("validated") is not True:
        raise WorkReportError("delivery manifest validation must attest the current 3.6 publisher")

    def expected_path(value: Path | str | None, item: Mapping[str, Any], role: str) -> Path:
        expected = (root / str(item.get("path", ""))).resolve()
        if value is not None and Path(value).expanduser().resolve() != expected:
            raise WorkReportError(f"candidate {role} path does not match the manifest path")
        return expected

    pptx_path = expected_path(pptx, required["pptx"], "pptx")
    if isinstance(report, Mapping):
        raise WorkReportError("report candidate must be the manifest-bound report file, not an in-memory Mapping")
    report_path = expected_path(report, required["supervision-report"], "supervision-report")
    markdown_path = expected_path(markdown, required["work-report-markdown"], "work-report-markdown")
    artifact_records = [
        _manifest_record(root, required["pptx"], "pptx"),
        _manifest_record(root, required["supervision-report"], "supervision-report"),
        _manifest_record(root, required["work-report-markdown"], "work-report-markdown"),
    ]
    expected_names = {
        "delivery-manifest.json",
        *(str(item.get("path")) for item in files),
        *(str(item.get("path")) for item in derived),
    }
    actual_names = {item.name for item in root.iterdir() if item.is_file()}
    expected_basenames = {Path(name).name for name in expected_names}
    if actual_names != expected_basenames:
        raise WorkReportError(f"delivery bundle contains unexpected or missing files: {sorted(actual_names ^ expected_basenames)}")
    try:
        report_value = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WorkReportError(f"supervision report cannot be read: {exc}") from exc
    if not isinstance(report_value, Mapping):
        raise WorkReportError("supervision report must be an object")
    if "stage_documents" in report_value:
        from story_handoff import handoff_archive_bytes
        companion = derived_by_role.get("stage-handoff-archive")
        if not isinstance(companion, Mapping):
            raise WorkReportError("story handoff report requires its companion archive")
        artifact_records.append(_manifest_record(root, companion, "stage-handoff-archive"))
        if (root / str(companion.get("path"))).read_bytes() != handoff_archive_bytes(report_value):
            raise WorkReportError("stage handoff companion differs from report")
    run_id = report_value.get("run_id")
    task_sha = report_value.get("task_request_sha256")
    if not isinstance(run_id, str) or not run_id.strip():
        raise WorkReportError("supervision report run_id must be non-empty")
    if not isinstance(task_sha, str) or SHA256.fullmatch(task_sha) is None:
        raise WorkReportError("supervision report task_request_sha256 must be lowercase SHA-256")
    if report_value.get("contract_version") != WORK_REPORT_VERSION:
        raise WorkReportError("verify-handoff requires supervision report contract 3.6")
    errors = validate_work_report(report_value, pptx=pptx_path, markdown=markdown_path)
    if errors:
        raise WorkReportError(errors)
    work = report_value.get("work_report", {})
    actual = work.get("actual_pptx", {}) if isinstance(work, Mapping) else {}
    task_identity = {
        "run_id": report_value.get("run_id"),
        "task_request_sha256": report_value.get("task_request_sha256"),
        "package_id": report_value.get("package_id"),
        "package_version": report_value.get("package_version"),
        "report_contract_version": report_value.get("contract_version"),
        "work_report_version": work.get("version") if isinstance(work, Mapping) else None,
    }
    if manifest.get("run_id") != task_identity["run_id"]:
        raise WorkReportError("manifest run_id does not match report")
    if manifest.get("task_request_sha256") != task_identity["task_request_sha256"]:
        raise WorkReportError("manifest task_request_sha256 does not match report")
    return {
        "status": "handoff-verified",
        "task_identity": task_identity,
        "presentation": {
            "title": actual.get("title") if isinstance(actual, Mapping) else None,
            "slide_count": actual.get("slide_count") if isinstance(actual, Mapping) else None,
            "statistics": dict(actual.get("totals", {})) if isinstance(actual, Mapping) and isinstance(actual.get("totals"), Mapping) else {},
        },
        "artifacts": artifact_records,
        "manifest": {"path": str(manifest_path), "sha256": _digest(manifest_path.read_bytes()), "bytes": manifest_path.stat().st_size},
    }


collect_work_report = build_work_report
render_markdown = render_work_report_markdown
inspect_final_pptx = inspect_pptx

__all__ = [
    "DELIVERY_MANIFEST_CONTRACT", "MISSING_STATUS", "PARTIAL_STATUS", "RECORDED_STATUS", "STAGES", "WORK_REPORT_CONTRACT", "WORK_REPORT_VERSION",
    "WorkReportError", "artifact_snapshot", "attach_work_report", "build_work_report", "canonical_json",
    "canonical_sha256", "collect_work_report", "inspect_final_pptx", "inspect_pptx", "render_markdown",
    "render_work_report_markdown", "validate_work_report", "validate_work_report_or_raise", "verify_handoff",
]
