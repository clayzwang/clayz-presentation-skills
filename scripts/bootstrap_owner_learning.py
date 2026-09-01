#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Build and audit the owner-private index once for each public core version.

The state root must be a persistent owner-private location supplied by the
host. A second run for the same core version verifies and reuses the original
index and audit. Changed source bytes under the same version fail closed rather
than silently retraining or overwriting the first-run evidence.
"""

from __future__ import annotations

import argparse
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

from packages.index_runtime import CompositeIndex, IndexProvider  # noqa: E402
from packages.index_runtime.utils import sha256_json  # noqa: E402
from scripts.materialize_owner_index import (  # noqa: E402
    MANIFEST_CONTRACT,
    MaterializationError,
    _parse_bindings,
    materialize,
)


AUDIT_CONTRACT = "io.clayz.presentation.version-private-learning-audit/1.0"
STATE_CONTRACT = "io.clayz.presentation.version-private-learning-state/1.0"
STATUS_CONTRACT = "io.clayz.presentation.version-private-learning-status/1.0"
DEFAULT_REQUIRED_KINDS = ("private-knowledge", "template", "standard", "method")
SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


class VersionLearningError(ValueError):
    """Raised when a version-bound learning state cannot be trusted."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Mapping[str, Any], *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "x" if exclusive else "w"
    with path.open(mode, encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _source_inventory(manifest: Mapping[str, Any], bindings: Mapping[str, Path]) -> list[dict[str, Any]]:
    sources = manifest.get("sources")
    if manifest.get("contract") != MANIFEST_CONTRACT or not isinstance(sources, list) or not sources:
        raise VersionLearningError("owner-learning manifest is missing or invalid")
    inventory: list[dict[str, Any]] = []
    for index, source in enumerate(sources):
        if not isinstance(source, Mapping):
            raise VersionLearningError(f"sources[{index}] must be an object")
        source_id = str(source.get("source_id", ""))
        path = bindings.get(source_id)
        if source.get("required") is True and path is None:
            raise VersionLearningError(f"missing required private learning source: {source_id}")
        if path is None:
            continue
        if not path.is_file():
            raise VersionLearningError(f"materialized private source is missing: {source_id}")
        kinds = source.get("knowledge_kinds")
        if not isinstance(kinds, list) or not kinds or any(not isinstance(item, str) for item in kinds):
            raise VersionLearningError(f"{source_id}: knowledge_kinds must be explicit")
        inventory.append({
            "source_id": source_id,
            "library_uri": source.get("library_uri"),
            "format": source.get("format"),
            "record_type": source.get("record_type"),
            "stages": source.get("stages"),
            "required": source.get("required") is True,
            "knowledge_kinds": sorted(set(kinds)),
            "purpose_tags": source.get("purpose_tags", []),
            "sha256": _sha256_file(path),
            "bytes": path.stat().st_size,
        })
    if not inventory:
        raise VersionLearningError("no private learning sources were materialized")
    return sorted(inventory, key=lambda item: str(item["source_id"]))


def _probe(provider: IndexProvider, kind: str) -> dict[str, Any]:
    matching = [record for record in provider.records if f"knowledge-kind:{kind}" in record["classification"]["purpose_tags"]]
    if not matching:
        return {"knowledge_kind": kind, "status": "fail", "receipt_id": None, "candidate_record_ids": []}
    stage = next((item for item in matching[0]["classification"]["stages"] if item != "shared"), "logic")
    request = {
        "contract": "io.clayz.presentation.retrieval-request/1.0",
        "request_id": f"version-learning-{kind}",
        "stage": stage,
        "query": kind.replace("-", " "),
        "rights_context": "private-runtime",
        "require_human_admission": True,
        "limit": min(5, len(matching)),
        "filters": {
            "record_types": [],
            "provider_ids": ["task-private-learning"],
            "task_modes": [],
            "page_roles": [],
            "semantic_relations": [],
            "purpose_tags": [f"knowledge-kind:{kind}"],
            "languages": ["zh-CN"],
            "failure_signals": [],
            "include_metadata_only": False,
        },
        "neighbor_expansion": {"physical": 0, "semantic": 0},
    }
    receipt = CompositeIndex([provider]).search(request)
    candidates = [str(item["record_id"]) for item in receipt["candidates"]]
    return {
        "knowledge_kind": kind,
        "status": "pass" if candidates else "fail",
        "receipt_id": receipt["receipt_id"],
        "candidate_record_ids": candidates,
    }


def _learned_content(provider: IndexProvider, inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_source: dict[str, list[dict[str, Any]]] = {}
    for record in provider.records:
        by_source.setdefault(str(record["source"]["source_id"]), []).append(record)
    learned: list[dict[str, Any]] = []
    for source in inventory:
        records = by_source.get(str(source["source_id"]), [])
        titles = [str(record["title"]) for record in records]
        learned.append({
            "source_id": source["source_id"],
            "knowledge_kinds": source["knowledge_kinds"],
            "stages": source["stages"],
            "record_count": len(records),
            "representative_titles": titles[:20],
            "titles_truncated": len(titles) > 20,
            "indexed_purpose_tags": sorted({tag for record in records for tag in record["classification"]["purpose_tags"]}),
        })
    return learned


def _markdown(audit: Mapping[str, Any]) -> str:
    lines = [
        f"# 私有学习审计：Clayz PPT {audit['core_version']}",
        "",
        f"- 状态：{audit['status']}",
        f"- 学习键：`{audit['learning_key']}`",
        f"- 私有来源：{len(audit['source_inventory'])} 个",
        f"- 索引记录：{audit['index']['record_count']} 条",
        f"- 已覆盖：{', '.join(audit['observed_knowledge_kinds'])}",
        f"- 缺失：{', '.join(audit['missing_knowledge_kinds']) or '无'}",
        "",
        "## 已学习内容",
        "",
    ]
    for item in audit["learned_content"]:
        titles = "、".join(item["representative_titles"]) or "无可用标题"
        lines.append(
            f"- {item['source_id']}：{item['record_count']} 条；类型 {', '.join(item['knowledge_kinds'])}；代表内容：{titles}"
        )
    lines.extend(["", "## 检索验证", ""])
    for probe in audit["retrieval_probes"]:
        lines.append(f"- {probe['knowledge_kind']}：{probe['status']}；候选 {len(probe['candidate_record_ids'])} 条")
    lines.extend([
        "",
        "> 这里的“学习”指：已准入私有内容被逐字节哈希、结构化索引并通过检索探针验证；不表示修改模型权重。",
        "",
    ])
    return "\n".join(lines)


def bootstrap(
    manifest: Mapping[str, Any],
    bindings: Mapping[str, Path],
    *,
    core_version: str,
    state_root: Path,
    required_kinds: Iterable[str] = DEFAULT_REQUIRED_KINDS,
) -> dict[str, Any]:
    if not SEMVER.fullmatch(core_version):
        raise VersionLearningError("core_version must be stable semantic version X.Y.Z")
    required = sorted(set(required_kinds))
    inventory = _source_inventory(manifest, bindings)
    source_manifest_sha256 = sha256_json(manifest)
    source_set_sha256 = sha256_json(inventory)
    learning_key = sha256_json({
        "core_version": core_version,
        "source_manifest_sha256": source_manifest_sha256,
        "source_set_sha256": source_set_sha256,
    })
    version_root = state_root.resolve() / "version-learning" / f"v{core_version}"
    pointer_path = version_root / "current.json"
    if pointer_path.is_file():
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        if pointer.get("contract") != STATE_CONTRACT or pointer.get("core_version") != core_version:
            raise VersionLearningError("existing version learning state is invalid")
        if pointer.get("source_set_sha256") != source_set_sha256 or pointer.get("learning_key") != learning_key:
            raise VersionLearningError("PRIVATE_LEARNING_SOURCE_DRIFT: private sources changed under the same core version")
        audit_path = version_root / str(pointer.get("audit", {}).get("path", ""))
        index_path = version_root / str(pointer.get("index", {}).get("path", ""))
        if not audit_path.is_file() or not index_path.is_file():
            raise VersionLearningError("existing version learning artifacts are missing")
        if _sha256_file(audit_path) != pointer.get("audit", {}).get("sha256") or _sha256_file(index_path) != pointer.get("index", {}).get("sha256"):
            raise VersionLearningError("existing version learning artifacts failed hash verification")
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if audit.get("status") != "complete" or audit.get("learning_key") != learning_key:
            raise VersionLearningError("existing version learning audit is not complete")
        return {
            "contract": STATUS_CONTRACT,
            "status": "ready",
            "mode": "reused-version-index",
            "core_version": core_version,
            "learning_key": learning_key,
            "source_set_sha256": source_set_sha256,
            "audit_path": audit_path.resolve().as_posix(),
            "audit_sha256": _sha256_file(audit_path),
            "index_path": index_path.resolve().as_posix(),
            "index_sha256": _sha256_file(index_path),
            "provider_snapshot": audit["index"]["snapshot"],
        }

    run_root = version_root / learning_key
    run_root.mkdir(parents=True, exist_ok=False)
    index_path = run_root / "version-private-learning.jsonl"
    materialization_path = run_root / "owner-index-materialization.json"
    materialized = materialize(manifest, bindings, {"logic", "copy", "art-direction", "output", "supervisor"}, index_path, materialization_path)
    provider = IndexProvider.from_jsonl("task-private-learning", index_path)
    observed = sorted({kind for item in inventory for kind in item["knowledge_kinds"]})
    missing = sorted(set(required) - set(observed))
    probes = [_probe(provider, kind) for kind in required]
    if any(item["status"] != "pass" for item in probes):
        missing = sorted(set(missing) | {item["knowledge_kind"] for item in probes if item["status"] != "pass"})
    audit = {
        "contract": AUDIT_CONTRACT,
        "status": "complete" if not missing else "blocked",
        "mode": "first-run",
        "core_version": core_version,
        "learning_key": learning_key,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_manifest_sha256": source_manifest_sha256,
        "source_set_sha256": source_set_sha256,
        "required_knowledge_kinds": required,
        "observed_knowledge_kinds": observed,
        "missing_knowledge_kinds": missing,
        "source_inventory": inventory,
        "learned_content": _learned_content(provider, inventory),
        "retrieval_probes": probes,
        "index": {
            "provider_id": "task-private-learning",
            "snapshot": provider.snapshot(),
            "artifact": index_path.resolve().as_posix(),
            "sha256": _sha256_file(index_path),
            "record_count": len(provider.records),
            "materialization_report": materialization_path.resolve().as_posix(),
            "materialization_report_sha256": _sha256_file(materialization_path),
        },
        "guards": {
            "one_learning_run_per_version": True,
            "source_drift_fails_closed": True,
            "private_content_stays_private": True,
            "retrieval_verified": not missing,
        },
    }
    audit_path = run_root / "version-private-learning-audit.json"
    brief_path = run_root / "version-private-learning-audit.md"
    _write_json(audit_path, audit)
    brief_path.write_text(_markdown(audit), encoding="utf-8", newline="\n")
    if missing:
        raise VersionLearningError(f"PRIVATE_LEARNING_COVERAGE_INCOMPLETE: {missing}; audit={audit_path}")
    pointer = {
        "contract": STATE_CONTRACT,
        "core_version": core_version,
        "learning_key": learning_key,
        "source_set_sha256": source_set_sha256,
        "created_at": audit["generated_at"],
        "audit": {"path": audit_path.relative_to(version_root).as_posix(), "sha256": _sha256_file(audit_path)},
        "index": {"path": index_path.relative_to(version_root).as_posix(), "sha256": _sha256_file(index_path)},
    }
    _write_json(pointer_path, pointer, exclusive=True)
    return {
        "contract": STATUS_CONTRACT,
        "status": "ready",
        "mode": "first-run",
        "core_version": core_version,
        "learning_key": learning_key,
        "source_set_sha256": source_set_sha256,
        "audit_path": audit_path.resolve().as_posix(),
        "audit_sha256": _sha256_file(audit_path),
        "brief_path": brief_path.resolve().as_posix(),
        "index_path": index_path.resolve().as_posix(),
        "index_sha256": _sha256_file(index_path),
        "provider_snapshot": materialized["provider_snapshot"],
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source", action="append", default=[], metavar="SOURCE_ID=PATH")
    parser.add_argument("--core-version", required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--task-root", type=Path, required=True, help="current ephemeral task root; state-root must be outside it")
    parser.add_argument("--require-kind", action="append", choices=sorted({*DEFAULT_REQUIRED_KINDS, "preference", "example", "brand-asset", "failure-pattern", "other"}))
    parser.add_argument("--status-output", type=Path)
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        task_root = args.task_root.resolve()
        state_root = args.state_root.resolve()
        if state_root == task_root or state_root.is_relative_to(task_root):
            raise VersionLearningError("owner-private version learning state must persist outside the current task root")
        status = bootstrap(
            manifest,
            _parse_bindings(args.source),
            core_version=args.core_version,
            state_root=state_root,
            required_kinds=args.require_kind or DEFAULT_REQUIRED_KINDS,
        )
        if args.status_output:
            _write_json(args.status_output, status)
        print(json.dumps({"ok": True, **status}, ensure_ascii=False))
        return 0
    except (OSError, json.JSONDecodeError, MaterializationError, VersionLearningError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
