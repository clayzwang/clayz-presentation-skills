# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Deterministic capability routing over the governed retrieval runtime."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .constants import REQUEST_CONTRACT
from .retrieval import CompositeIndex
from .utils import require, require_nonempty_string, sha256_json

CAPABILITY_RESOLUTION_CONTRACT = "io.clayz.presentation.capability-resolution/1.0"

CORE_BY_STAGE: dict[str, tuple[tuple[str, str], ...]] = {
    "logic": (("skills/clayz-presentation-logic/references/logic-package-contract.md", "Logic package contract is mandatory and never search-dependent."), ("packages/contracts/knowledge-learning.md", "Knowledge governance is mandatory before retrieval or learning writeback.")),
    "copy": (("skills/clayz-presentation-copy/references/copy-package-contract.md", "Copy package contract is mandatory and never search-dependent."), ("packages/contracts/knowledge-learning.md", "Knowledge governance is mandatory before retrieval or learning writeback.")),
    "art-direction": (("skills/clayz-presentation-art-direction/references/art-direction-plan-contract.md", "Art owns original design and the locked visual handoff; no layout index or registered match is required."), ("packages/contracts/story-visual-handoff.md", "Clean text roles do not prescribe grouping, styling or visual reading order."), ("packages/contracts/knowledge-learning.md", "Preserve real learning/source provenance without restricting original design.")),
    "output": (("skills/clayz-presentation-output/references/art-direction-handoff.md", "Implement the approved visual handoff and native text ranges, including shared objects."), ("skills/clayz-presentation-output/references/build-only-contract.md", "Output implements Art rather than inventing a design."), ("packages/contracts/knowledge-learning.md", "Preserve source and asset provenance.")),
    "supervisor": (("skills/clayz-presentation-supervisor/references/supervision-contract.md", "Review actual fidelity and defects without inheriting retired Copy rendering rules."), ("packages/contracts/knowledge-learning.md", "Preserve provenance of actually consulted diagnostic knowledge.")),
}


def mandatory_core(stage: str) -> list[dict[str, str]]:
    require(stage in CORE_BY_STAGE, f"unsupported capability stage: {stage}")
    return [{"ref": ref, "reason": reason} for ref, reason in CORE_BY_STAGE[stage]]


def _capability_payload(record: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = record.get("payload", {})
    require(payload.get("kind") == "inline", f"capability payload must be inline: {record.get('record_id')}")
    value = payload.get("ref")
    require(isinstance(value, Mapping), f"capability payload.ref must be an object: {record.get('record_id')}")
    require_nonempty_string(value.get("capability_id"), "capability.capability_id")
    for key in ("knowledge_refs", "validator_refs"):
        refs = value.get(key, [])
        require(isinstance(refs, list) and all(isinstance(item, str) and item for item in refs), f"capability.{key} must be strings")
    return value


def _request(stage: str, task_mode: str, signal: str, rights_context: str, languages: Sequence[str], limit: int) -> dict[str, Any]:
    request_id = f"capability-{stage}-{sha256_json({'task_mode': task_mode, 'signal': signal, 'languages': list(languages)})[:16]}"
    return {
        "contract": REQUEST_CONTRACT, "request_id": request_id, "stage": stage,
        "query": f"{task_mode} {signal}", "rights_context": rights_context,
        "intent": "task-reference",
        "task_context": {"decision_goal": f"Resolve capability signal {signal} for {stage}", "target_refs": [f"stage:{stage}"], "format_need": "governed-method"},
        "ranking_policy": {"profile": "content", "minimum_score": 0.1, "max_selected": min(limit, 5), "diversity_lambda": 0.7},
        "require_human_admission": True, "limit": limit,
        "filters": {
            "record_types": ["capability"], "provider_ids": ["builtin-catalog"], "task_modes": [task_mode],
            "page_roles": [], "semantic_relations": [], "purpose_tags": [signal], "languages": list(languages),
            "failure_signals": [], "include_metadata_only": False,
            "format_tags": [],
        },
        "neighbor_expansion": {"physical": 0, "semantic": 0},
    }


def resolve_capabilities(index: CompositeIndex, *, stage: str, task_mode: str, signals: Sequence[str], rights_context: str = "public-open-source", languages: Sequence[str] = (), limit: int = 12, created_at: str | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    require(stage in CORE_BY_STAGE, f"unsupported capability stage: {stage}")
    require_nonempty_string(task_mode, "task_mode")
    normalized_signals = sorted({require_nonempty_string(value, "signal") for value in signals})
    selected_by_id: dict[str, dict[str, Any]] = {}
    receipts: list[dict[str, Any]] = []
    unresolved: list[str] = []
    for signal in normalized_signals:
        receipt = index.search(_request(stage, task_mode, signal, rights_context, languages, limit), created_at=created_at)
        selected: dict[str, str] = {}
        if receipt["candidates"]:
            candidate = receipt["candidates"][0]
            provider_id, record = index._records[candidate["record_id"]]
            require(provider_id == "builtin-catalog", "capabilities must resolve from builtin-catalog")
            payload = _capability_payload(record)
            reason = f"Matched stage={stage}, task_mode={task_mode}, signal={signal}."
            selected[record["record_id"]] = reason
            existing = selected_by_id.get(record["record_id"])
            if existing is None:
                selected_by_id[record["record_id"]] = {
                    "record_id": record["record_id"], "capability_id": payload["capability_id"], "reason": reason,
                    "knowledge_refs": sorted(set(payload.get("knowledge_refs", []))),
                    "validator_refs": sorted(set(payload.get("validator_refs", []))),
                }
            else:
                existing["reason"] = existing["reason"].rstrip(".") + f"; signal={signal}."
        else:
            unresolved.append(signal)
        receipts.append(index.finalize_receipt(receipt, selected=selected))
    resolution_seed = {"stage": stage, "task_mode": task_mode, "signals": normalized_signals, "receipts": [item["receipt_id"] for item in receipts], "selected": sorted(selected_by_id)}
    resolution = {
        "contract": CAPABILITY_RESOLUTION_CONTRACT,
        "resolution_id": f"resolution-{sha256_json(resolution_seed)[:20]}",
        "stage": stage,
        "request_id": f"capability-batch-{sha256_json({'stage': stage, 'task_mode': task_mode, 'signals': normalized_signals})[:16]}",
        "mandatory_core": mandatory_core(stage),
        "retrieval_receipt_ids": [item["receipt_id"] for item in receipts],
        "selected_capabilities": [selected_by_id[key] for key in sorted(selected_by_id)],
        "unresolved_signals": unresolved,
        "guards": {"core_contracts_not_search_dependent": True, "only_receipt_candidates_selected": True, "no_invented_capabilities": True},
    }
    return resolution, receipts
