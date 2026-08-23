#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Register, admit, index, search, and record portable presentation knowledge."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.feedback.learning import (  # noqa: E402
    FeedbackError,
    validate_learning_admission,
    validate_learning_record,
)

TEXT_SUFFIXES = {".csv", ".json", ".jsonl", ".md", ".svg", ".txt", ".yaml", ".yml"}
KIND_BY_SUFFIX = {
    ".csv": "data",
    ".json": "data",
    ".jsonl": "data",
    ".md": "document",
    ".txt": "document",
    ".yaml": "data",
    ".yml": "data",
    ".svg": "svg",
    ".pptx": "pptx",
    ".pdf": "pdf",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
}
STAGES = {"logic", "copy", "art-direction", "output"}
LEARNING_CONTRACT = "io.clayz.presentation.learning-record/1.0"
LEARNING_ADMISSION_CONTRACT = "io.clayz.presentation.learning-admission/1.0"
PROMOTION_TARGETS = {"knowledge", "failure-pattern", "compatibility-note", "proven-repair"}


class KnowledgeError(ValueError):
    """Raised when a knowledge mutation would violate the public contract."""


def load_settings(root: Path, config_path: Path) -> dict[str, Any]:
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        references = config["references"]
        learning = references["learning"]
        index = references["index"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise KnowledgeError(f"invalid knowledge configuration: {exc}") from exc

    def beneath(relative: str) -> Path:
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise KnowledgeError(f"configured path must remain beneath the repository: {relative}")
        return root / candidate

    roots = references.get("roots")
    if not isinstance(roots, list) or len(roots) != 1 or not isinstance(roots[0], str):
        raise KnowledgeError("the public filesystem runtime requires exactly one configured source root")
    return {
        "source_root": beneath(roots[0]),
        "asset_registry": beneath(references["registry"]),
        "admission_registry": beneath(references["admission_registry"]),
        "learning_root": beneath(learning["root"]),
        "index_path": beneath(index["path"]),
        "maximum_results": int(index["maximum_results"]),
        "physical_neighbor_expansion": int(index["physical_neighbor_expansion"]),
        "semantic_neighbor_expansion": int(index["semantic_neighbor_expansion"]),
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise KnowledgeError(f"{path}:{line_number}: {exc}") from exc
        if not isinstance(row, dict):
            raise KnowledgeError(f"{path}:{line_number}: expected a JSON object")
        rows.append(row)
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: dict[str, Any]) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def tokenize(text: str) -> list[str]:
    lowered = text.casefold()
    latin = re.findall(r"[a-z0-9][a-z0-9_+.-]*", lowered)
    cjk_runs = re.findall(r"[\u3400-\u9fff]+", lowered)
    cjk: list[str] = []
    for run in cjk_runs:
        cjk.extend(run if len(run) == 1 else [run[index : index + 2] for index in range(len(run) - 1)])
    return latin + cjk


def _safe_relative(source: Path, source_root: Path) -> str:
    try:
        relative = source.resolve().relative_to(source_root.resolve())
    except ValueError as exc:
        raise KnowledgeError(f"source must be inside {source_root}") from exc
    if ".." in relative.parts:
        raise KnowledgeError("relative paths may not contain '..'")
    return relative.as_posix()


def _id(prefix: str, seed: str) -> str:
    return f"{prefix}-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"


def register_asset(
    settings: dict[str, Any],
    source: Path,
    *,
    asset_id: str | None,
    kind: str | None,
    source_uri: str,
    license_name: str,
    language: str,
    purpose_tags: list[str],
    physical_neighbors: list[str],
    semantic_neighbors: list[str],
    notes: str,
) -> dict[str, Any]:
    source_root = settings["source_root"]
    if not source.is_file():
        raise KnowledgeError(f"source does not exist: {source}")
    relative = _safe_relative(source, source_root)
    digest = sha256_file(source)
    resolved_kind = kind or KIND_BY_SUFFIX.get(source.suffix.lower())
    if resolved_kind not in {"document", "data", "image", "svg", "pptx", "pdf"}:
        raise KnowledgeError("kind is required for unrecognized file types")
    resolved_id = asset_id or _id("asset", f"{relative}:{digest}")
    registry = settings["asset_registry"]
    rows = read_jsonl(registry)
    for row in rows:
        if row.get("asset_id") == resolved_id:
            if row.get("sha256") == digest and row.get("relative_path") == relative:
                return row
            raise KnowledgeError(f"asset_id already exists with different content: {resolved_id}")
    entry = {
        "asset_id": resolved_id,
        "kind": resolved_kind,
        "relative_path": relative,
        "sha256": digest,
        "source_uri": source_uri,
        "license": license_name,
        "language": language,
        "purpose_tags": sorted(set(purpose_tags)),
        "physical_neighbors": sorted(set(physical_neighbors)),
        "semantic_neighbors": sorted(set(semantic_neighbors)),
        "human_admitted": False,
        "notes": notes,
    }
    append_jsonl(registry, entry)
    return entry


def admit_reference(
    settings: dict[str, Any],
    subject_type: str,
    subject_id: str,
    *,
    admitted_by: str,
    use_for: list[str],
    never_copy: list[str],
    decision_notes: str,
    confirmed: bool,
    promotion_target: str | None = None,
) -> dict[str, Any]:
    if not confirmed:
        raise KnowledgeError("admission requires --confirm-human-decision")
    if subject_type not in {"asset", "learning"}:
        raise KnowledgeError(f"unsupported subject_type: {subject_type}")
    if subject_type == "asset":
        subjects = {
            row.get("asset_id"): row
            for row in read_jsonl(settings["asset_registry"])
            if isinstance(row.get("asset_id"), str)
        }
    else:
        subjects = {}
        for stage in STAGES:
            subjects.update({
                row.get("record_id"): row
                for row in read_jsonl(settings["learning_root"] / stage / "learning-records.jsonl")
                if isinstance(row.get("record_id"), str)
            })
    if subject_id not in subjects:
        raise KnowledgeError(f"unknown {subject_type}: {subject_id}")
    subject = subjects[subject_id]
    if subject_type == "learning":
        try:
            subject = validate_learning_record(subject)
        except FeedbackError as exc:
            raise KnowledgeError(f"invalid learning record: {exc}") from exc
        resolved_target = promotion_target or "knowledge"
        if resolved_target not in PROMOTION_TARGETS:
            raise KnowledgeError(f"unsupported promotion target: {resolved_target}")
        subject_sha256 = sha256_json(subject)
    else:
        resolved_target = None
        subject_sha256 = str(subject.get("sha256", ""))
    admission_id = _id(
        "admission",
        f"{subject_type}:{subject_id}:{admitted_by}:{','.join(use_for)}:{resolved_target or ''}:{subject_sha256}",
    )
    registry = settings["admission_registry"]
    existing = read_jsonl(registry)
    for row in existing:
        if row.get("admission_id") == admission_id:
            return row
    entry = {
        "admission_id": admission_id,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "subject_sha256": subject_sha256,
        "admitted_by": admitted_by,
        "admitted_at": utc_now(),
        "use_for": sorted(set(use_for)),
        "never_copy": sorted(set(never_copy)),
        "decision_notes": decision_notes,
    }
    if subject_type == "learning":
        entry.update({
            "contract": LEARNING_ADMISSION_CONTRACT,
            "promotion_target": resolved_target,
            "public_catalog_eligible": False,
        })
        try:
            entry = validate_learning_admission(entry, subject)
        except FeedbackError as exc:
            raise KnowledgeError(f"invalid learning admission: {exc}") from exc
    append_jsonl(registry, entry)
    return entry


def record_learning(
    settings: dict[str, Any],
    stage: str,
    *,
    task_purpose: str,
    observation: str,
    evidence_refs: list[str],
    decision: str,
    user_ruling: str | None,
    task_modes: list[str] | None = None,
    page_roles: list[str] | None = None,
    purpose_tags: list[str] | None = None,
    language: str = "und",
    failure_signals: list[str] | None = None,
    source_kind: str = "task-observation",
    source_id: str | None = None,
    source_revision: str = "1",
) -> dict[str, Any]:
    if stage not in STAGES:
        raise KnowledgeError(f"unsupported stage: {stage}")
    created_at = utc_now()
    resolved_id = _id("learning", f"{stage}:{task_purpose}:{observation}:{created_at}")
    entry = {
        "contract": LEARNING_CONTRACT,
        "record_id": resolved_id,
        "stage": stage,
        "task_purpose": task_purpose,
        "observation": observation,
        "evidence_refs": sorted(set(evidence_refs)),
        "decision": decision,
        "user_ruling": user_ruling,
        "promotion_status": "observation",
        "created_at": created_at,
        "classification": {
            "task_modes": sorted(set(task_modes or [])),
            "page_roles": sorted(set(page_roles or [])),
            "purpose_tags": sorted(set(purpose_tags or [])),
            "language": language,
            "failure_signals": sorted(set(failure_signals or [])),
        },
        "source": {
            "source_kind": source_kind,
            "source_id": source_id or f"task-local-{resolved_id}",
            "source_revision": source_revision,
        },
        "guards": {
            "human_admission_required": True,
            "generated_artifact_auto_admitted": False,
            "supervisor_owns_store": False,
        },
    }
    append_jsonl(settings["learning_root"] / stage / "learning-records.jsonl", entry)
    return entry


def _extract_text(path: Path, maximum_bytes: int) -> str:
    if path.suffix.lower() not in TEXT_SUFFIXES or path.stat().st_size > maximum_bytes:
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def build_index(settings: dict[str, Any], *, maximum_bytes: int = 2_000_000) -> dict[str, Any]:
    if maximum_bytes < 1:
        raise KnowledgeError("maximum text bytes must be positive")
    assets = read_jsonl(settings["asset_registry"])
    admissions = read_jsonl(settings["admission_registry"])
    admitted_assets = {
        row.get("subject_id"): row
        for row in admissions
        if row.get("subject_type") == "asset"
    }
    documents = []
    document_frequency: Counter[str] = Counter()
    for asset in assets:
        asset_id = asset.get("asset_id")
        admission = admitted_assets.get(asset_id)
        if not admission:
            continue
        relative = asset.get("relative_path")
        if not isinstance(relative, str):
            continue
        path = settings["source_root"] / relative
        if not path.is_file() or sha256_file(path) != asset.get("sha256"):
            continue
        metadata = " ".join(
            [
                str(asset_id),
                relative,
                str(asset.get("kind", "")),
                str(asset.get("language", "")),
                " ".join(str(value) for value in asset.get("purpose_tags", [])),
                " ".join(str(value) for value in admission.get("use_for", [])),
                str(asset.get("notes", "")),
            ]
        )
        counts = Counter(tokenize(metadata + "\n" + _extract_text(path, maximum_bytes)))
        document_frequency.update(counts.keys())
        documents.append(
            {
                "asset_id": asset_id,
                "record_id": asset_id,
                "record_type": "knowledge",
                "source_type": "asset",
                "relative_path": relative,
                "kind": asset.get("kind"),
                "language": asset.get("language"),
                "purpose_tags": asset.get("purpose_tags", []),
                "use_for": admission.get("use_for", []),
                "never_copy": admission.get("never_copy", []),
                "physical_neighbors": asset.get("physical_neighbors", []),
                "semantic_neighbors": asset.get("semantic_neighbors", []),
                "token_counts": dict(sorted(counts.items())),
                "token_length": sum(counts.values()),
            }
        )

    admitted_learning = {
        row.get("subject_id"): row
        for row in admissions
        if row.get("subject_type") == "learning"
    }
    for stage in sorted(STAGES):
        for learning in read_jsonl(settings["learning_root"] / stage / "learning-records.jsonl"):
            record_id = learning.get("record_id")
            if not isinstance(record_id, str) or not record_id:
                continue
            admission = admitted_learning.get(record_id)
            if not admission:
                continue
            try:
                learning = validate_learning_record(learning)
                admission = validate_learning_admission(admission, learning)
            except FeedbackError:
                continue
            classification = learning.get("classification", {})
            purpose_tags = sorted(set(
                [str(value) for value in classification.get("purpose_tags", [])]
                + [str(value) for value in admission.get("use_for", [])]
                + [str(admission.get("promotion_target", "knowledge"))]
            ))
            metadata = " ".join([
                record_id,
                stage,
                str(learning.get("task_purpose", "")),
                str(learning.get("observation", "")),
                str(learning.get("decision", "")),
                str(learning.get("user_ruling", "")),
                " ".join(purpose_tags),
                " ".join(str(value) for value in classification.get("failure_signals", [])),
            ])
            counts = Counter(tokenize(metadata))
            document_frequency.update(counts.keys())
            documents.append({
                "asset_id": record_id,
                "record_id": record_id,
                "record_type": "learning",
                "source_type": "learning",
                "stage": stage,
                "relative_path": None,
                "kind": "learning",
                "language": classification.get("language", "und"),
                "purpose_tags": purpose_tags,
                "use_for": admission.get("use_for", []),
                "never_copy": admission.get("never_copy", []),
                "physical_neighbors": [],
                "semantic_neighbors": [],
                "token_counts": dict(sorted(counts.items())),
                "token_length": sum(counts.values()),
            })
    index = {
        "contract": "io.clayz.presentation.knowledge-index/2.0",
        "generated_at": utc_now(),
        "engine": "bm25-lexical",
        "document_count": len(documents),
        "asset_document_count": sum(1 for document in documents if document.get("source_type") == "asset"),
        "learning_document_count": sum(1 for document in documents if document.get("source_type") == "learning"),
        "document_frequency": dict(sorted(document_frequency.items())),
        "documents": documents,
    }
    destination = settings["index_path"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return index


def search_index(
    index: dict[str, Any],
    query: str,
    *,
    purpose: str | None,
    limit: int,
    physical_neighbor_expansion: int = 0,
    semantic_neighbor_expansion: int = 0,
) -> list[dict[str, Any]]:
    if limit < 1:
        raise KnowledgeError("search limit must be positive")
    query_tokens = Counter(tokenize(query))
    documents = index.get("documents", [])
    document_count = int(index.get("document_count", len(documents)))
    frequencies = index.get("document_frequency", {})
    average_length = sum(int(doc.get("token_length", 0)) for doc in documents) / max(document_count, 1)
    results = []
    for document in documents:
        if purpose and purpose not in set(document.get("purpose_tags", [])) | set(document.get("use_for", [])):
            continue
        counts = document.get("token_counts", {})
        length = max(int(document.get("token_length", 0)), 1)
        score = 0.0
        for token, query_count in query_tokens.items():
            frequency = int(counts.get(token, 0))
            if not frequency:
                continue
            df = max(int(frequencies.get(token, 0)), 1)
            inverse = math.log(1 + (document_count - df + 0.5) / (df + 0.5))
            denominator = frequency + 1.2 * (1 - 0.75 + 0.75 * length / max(average_length, 1))
            score += query_count * inverse * frequency * 2.2 / denominator
        if score > 0:
            results.append(
                {
                    key: document.get(key)
                    for key in (
                        "asset_id", "record_id", "record_type", "source_type", "stage",
                        "relative_path",
                        "kind",
                        "language",
                        "purpose_tags",
                        "use_for",
                        "never_copy",
                        "physical_neighbors",
                        "semantic_neighbors",
                    )
                }
                | {"score": round(score, 6)}
            )
    ranked = sorted(results, key=lambda item: (-item["score"], str(item.get("record_id") or item["asset_id"])))[:limit]
    by_id = {(document.get("record_id") or document.get("asset_id")): document for document in documents}
    expanded = list(ranked)
    seen = {result.get("asset_id") for result in expanded}
    for result in ranked:
        for field, maximum in (
            ("physical_neighbors", physical_neighbor_expansion),
            ("semantic_neighbors", semantic_neighbor_expansion),
        ):
            for neighbor_id in result.get(field, [])[:maximum]:
                if neighbor_id in seen or neighbor_id not in by_id:
                    continue
                neighbor = by_id[neighbor_id]
                expanded.append(
                    {
                        key: neighbor.get(key)
                        for key in (
                            "asset_id", "record_id", "record_type", "source_type", "stage",
                            "relative_path", "kind", "language", "purpose_tags",
                            "use_for", "never_copy", "physical_neighbors", "semantic_neighbors",
                        )
                    }
                    | {"score": 0.0, "neighbor_of": result.get("asset_id"), "neighbor_type": field}
                )
                seen.add(neighbor_id)
    return expanded


def _print(row: Any) -> None:
    print(json.dumps(row, ensure_ascii=False, indent=2))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root")
    parser.add_argument("--config", type=Path, default=Path("config/default.json"), help="Configuration path relative to root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    register = subparsers.add_parser("register", help="Register a source already placed under knowledge/sources")
    register.add_argument("source", type=Path)
    register.add_argument("--asset-id")
    register.add_argument("--kind", choices=sorted(set(KIND_BY_SUFFIX.values())))
    register.add_argument("--source-uri", required=True)
    register.add_argument("--license", dest="license_name", required=True)
    register.add_argument("--language", default="und")
    register.add_argument("--purpose-tag", action="append", default=[])
    register.add_argument("--physical-neighbor", action="append", default=[])
    register.add_argument("--semantic-neighbor", action="append", default=[])
    register.add_argument("--notes", default="")

    admit = subparsers.add_parser("admit", help="Record an explicit human admission decision")
    admit.add_argument("subject_type", choices=["asset", "learning"])
    admit.add_argument("subject_id")
    admit.add_argument("--admitted-by", required=True)
    admit.add_argument("--use-for", action="append", required=True)
    admit.add_argument("--never-copy", action="append", default=[])
    admit.add_argument("--decision-notes", default="")
    admit.add_argument("--promotion-target", choices=sorted(PROMOTION_TARGETS))
    admit.add_argument("--confirm-human-decision", action="store_true")

    learning = subparsers.add_parser("record-learning", help="Append a non-promoted observation")
    learning.add_argument("stage", choices=sorted(STAGES))
    learning.add_argument("--task-purpose", required=True)
    learning.add_argument("--observation", required=True)
    learning.add_argument("--evidence-ref", action="append", default=[])
    learning.add_argument("--decision", required=True)
    learning.add_argument("--user-ruling")
    learning.add_argument("--task-mode", action="append", default=[])
    learning.add_argument("--page-role", action="append", default=[])
    learning.add_argument("--purpose-tag", action="append", default=[])
    learning.add_argument("--language", default="und")
    learning.add_argument("--failure-signal", action="append", default=[])
    learning.add_argument("--source-kind", choices=["task-observation", "synthetic-fixture"], default="task-observation")
    learning.add_argument("--source-id")
    learning.add_argument("--source-revision", default="1")

    index_parser = subparsers.add_parser("build-index", help="Build a local lexical index from admitted sources")
    index_parser.add_argument("--maximum-text-bytes", type=int, default=2_000_000)

    search = subparsers.add_parser("search", help="Search the built local index")
    search.add_argument("query")
    search.add_argument("--purpose")
    search.add_argument("--limit", type=int)

    args = parser.parse_args(list(argv) if argv is not None else None)
    root = args.root.resolve()
    try:
        config_path = args.config if args.config.is_absolute() else root / args.config
        settings = load_settings(root, config_path)
        if args.command == "register":
            source = args.source if args.source.is_absolute() else root / args.source
            _print(
                register_asset(
                    settings,
                    source.resolve(),
                    asset_id=args.asset_id,
                    kind=args.kind,
                    source_uri=args.source_uri,
                    license_name=args.license_name,
                    language=args.language,
                    purpose_tags=args.purpose_tag,
                    physical_neighbors=args.physical_neighbor,
                    semantic_neighbors=args.semantic_neighbor,
                    notes=args.notes,
                )
            )
        elif args.command == "admit":
            _print(
                admit_reference(
                    settings,
                    args.subject_type,
                    args.subject_id,
                    admitted_by=args.admitted_by,
                    use_for=args.use_for,
                    never_copy=args.never_copy,
                    decision_notes=args.decision_notes,
                    confirmed=args.confirm_human_decision,
                    promotion_target=args.promotion_target,
                )
            )
        elif args.command == "record-learning":
            _print(
                record_learning(
                    settings,
                    args.stage,
                    task_purpose=args.task_purpose,
                    observation=args.observation,
                    evidence_refs=args.evidence_ref,
                    decision=args.decision,
                    user_ruling=args.user_ruling,
                    task_modes=args.task_mode,
                    page_roles=args.page_role,
                    purpose_tags=args.purpose_tag,
                    language=args.language,
                    failure_signals=args.failure_signal,
                    source_kind=args.source_kind,
                    source_id=args.source_id,
                    source_revision=args.source_revision,
                )
            )
        elif args.command == "build-index":
            _print(build_index(settings, maximum_bytes=args.maximum_text_bytes))
        else:
            index_path = settings["index_path"]
            if not index_path.is_file():
                raise KnowledgeError("index not found; run build-index first")
            index = json.loads(index_path.read_text(encoding="utf-8"))
            _print(
                search_index(
                    index,
                    args.query,
                    purpose=args.purpose,
                    limit=args.limit or settings["maximum_results"],
                    physical_neighbor_expansion=settings["physical_neighbor_expansion"],
                    semantic_neighbor_expansion=settings["semantic_neighbor_expansion"],
                )
            )
    except (OSError, json.JSONDecodeError, KnowledgeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
