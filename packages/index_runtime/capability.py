# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Deterministic capability routing over the governed retrieval runtime."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from typing import Any

from .constants import REQUEST_CONTRACT
from .retrieval import CompositeIndex
from .utils import require, require_nonempty_string, sha256_json

CAPABILITY_RESOLUTION_CONTRACT = "io.clayz.presentation.capability-resolution/1.0"

CORE_BY_STAGE: dict[str, tuple[tuple[str, str], ...]] = {
    "logic": (
        ("skills/clayz-presentation-logic/references/logic-package-contract.md", "Logic package contract is mandatory and never search-dependent."),
        ("packages/contracts/knowledge-learning.md", "Knowledge governance is mandatory before retrieval or learning writeback."),
    ),
    "copy": (
        ("skills/clayz-presentation-copy/references/copy-package-contract.md", "Copy package contract is mandatory and never search-dependent."),
        ("packages/contracts/knowledge-learning.md", "Knowledge governance is mandatory before retrieval or learning writeback."),
    ),
    "art-direction": (
        ("skills/clayz-presentation-art-direction/references/art-direction-plan-contract.md", "Art Direction plan contract is mandatory and never search-dependent."),
        ("skills/clayz-presentation-art-direction/references/material-routes.md", "Dominant medium selection remains a mandatory Art Direction responsibility."),
        ("packages/contracts/knowledge-learning.md", "Knowledge governance is mandatory before retrieval or learning writeback."),
    ),
    "output": (
        ("skills/clayz-presentation-output/references/art-direction-handoff.md", "Output must validate the approved visual handoff before building."),
        ("skills/clayz-presentation-output/references/build-only-contract.md", "Build-only authority remains mandatory and never search-dependent."),
        ("packages/contracts/knowledge-learning.md", "Knowledge governance is mandatory before retrieval or learning writeback."),
    ),
    "supervisor": (
        ("skills/clayz-presentation-supervisor/references/supervision-contract.md", "Supervision authority and evidence contract are mandatory and never search-dependent."),
        ("packages/contracts/knowledge-learning.md", "Knowledge governance is mandatory before routing reusable observations."),
    ),
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
    knowledge_refs = value.get("knowledge_refs", [])
    validator_refs = value.get("validator_refs", [])
    require(isinstance(knowledge_refs, list) and all(isinstance(item, str) and item for item in knowledge_refs), "capability.knowledge_refs must be strings")
    require(isinstance(validator_refs, list) and all(isinstance(item, str) and item for item in validator_refs), "capability.validator_refs must be strings")
    return value


def resolve_capabilities(
    index: CompositeIndex,
    *,
    stage: str,
    task_mode: str,
    signals: Sequence[str],
    rights_context: str = "public-open-source",
    languages: Sequence[str] = (),
    limit: int = 12,
    created_at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    require(stage in CORE_BY_STAGE, f"unsupported capability stage: {stage}")
    require_nonempty_string(task_mode, "task_mode")
    normalized_signals = sorted({require_nonempty_string(value, "signal") for value in signals})
    request_id = f"capability-{stage}-{sha256_json({'task_mode': task_mode, 'signals': normalized_signals, 'languages': list(languages)})[:16]}"
    request = {
        "contract": REQUEST_CONTRACT,
        "request_id": request_id,
        "stage": stage,
        "query": " ".join([task_mode, *normalized_signals]),
        "rights_context": rights_context,
        "require_human_admission": True,
        "limit": limit,
        "filters": {
            "record_types": ["capability"],
            "provider_ids": ["builtin-catalog"],
            "task_modes": [task_mode],
            "page_roles": [],
            "semantic_relations": [],
            "purpose_tags": normalized_signals,
            "languages": list(languages),
            "failure_signals": [],
            "include_metadata_only": False,
        },
        "neighbor_expansion": {"physical": 0, "semantic": 0},
    }
    receipt = index.search(request, created_at=created_at)
    selected: dict[str, str] = {}
    capabilities: list[dict[str, Any]] = []
    covered: set[str] = set()
    for candidate in receipt["candidates"]:
        provider_id, record = index._records[candidate["record_id"]]
        require(provider_id == "builtin-catalog", "capabilities must resolve from builtin-catalog")
        payload = _capability_payload(record)
        record_signals = set(record["classification"].get("purpose_tags", []))
        matched = sorted(set(normalized_signals).intersection(record_signals))
        reason = "Matched stage/task mode" + (f" and signals: {', '.join(matched)}" if matched else ".")
        selected[record["record_id"]] = reason
        covered.update(matched)
        capabilities.append(
            {
                "record_id": record["record_id"],
                "capability_id": payload["capability_id"],
                "reason": reason,
                "knowledge_refs": sorted(set(payload.get("knowledge_refs", []))),
                "validator_refs": sorted(set(payload.get("validator_refs", []))),
            }
        )
    finalized = index.finalize_receipt(receipt, selected=selected)
    resolution_seed = {"request_id": request_id, "receipt_id": finalized["receipt_id"], "selected": sorted(selected)}
    resolution = {
        "contract": CAPABILITY_RESOLUTION_CONTRACT,
        "resolution_id": f"resolution-{sha256_json(resolution_seed)[:20]}",
        "stage": stage,
        "request_id": request_id,
        "mandatory_core": mandatory_core(stage),
        "retrieval_receipt_id": finalized["receipt_id"],
        "selected_capabilities": capabilities,
        "unresolved_signals": sorted(set(normalized_signals) - covered),
        "guards": {
            "core_contracts_not_search_dependent": True,
            "only_receipt_candidates_selected": True,
            "no_invented_capabilities": True,
        },
    }
    return copy.deepcopy(resolution), finalized
