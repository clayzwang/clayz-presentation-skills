# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Provider-aware retrieval and auditable selection receipts."""

from __future__ import annotations

import copy
import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from .constants import HIGH_RISK_BRAND_ASSET_CLASSES, RECEIPT_CONTRACT
from .provider import IndexProvider
from .utils import require, require_nonempty_string, sha256_json, tokenize, utc_now
from .validation import validate_request


class CompositeIndex:
    """Search multiple providers without erasing provenance or rights."""

    def __init__(self, providers: Sequence[IndexProvider]):
        require(bool(providers), "at least one provider is required")
        provider_ids = [provider.provider_id for provider in providers]
        require(len(provider_ids) == len(set(provider_ids)), "provider_id must be unique")
        self.providers = tuple(sorted(providers, key=lambda item: item.provider_id))
        self._records: dict[str, tuple[str, dict[str, Any]]] = {}
        for provider in self.providers:
            for record in provider.records:
                record_id = record["record_id"]
                require(record_id not in self._records, f"record_id must be globally unique: {record_id}")
                self._records[record_id] = (provider.provider_id, record)

    def snapshots(self) -> list[dict[str, Any]]:
        return [provider.snapshot() for provider in self.providers]

    @staticmethod
    def _rights_decision(record: Mapping[str, Any], request: Mapping[str, Any]) -> tuple[bool, bool, str]:
        rights = record["rights"]
        governance = record["governance"]
        classification = record["classification"]
        context = request["rights_context"]
        include_metadata_only = request["filters"].get("include_metadata_only", True)
        if governance.get("deprecated") or governance.get("quality_status") in {"rejected", "deprecated"}:
            return False, False, "record-not-active"
        if request.get("require_human_admission", True):
            if not governance.get("human_admitted") or governance.get("quality_status") != "admitted":
                return False, False, "human-admission-required"
        redistribution = rights["redistribution"]
        materialization = rights["materialization"]
        asset_class = classification["asset_class"]
        brand_scope = classification["brand_scope"]
        if context == "public-open-source":
            if not governance.get("public_catalog_eligible"):
                return False, False, "not-public-catalog-eligible"
            if redistribution in {"local-private", "forbidden"}:
                return False, False, "redistribution-not-allowed"
            if asset_class in HIGH_RISK_BRAND_ASSET_CLASSES and brand_scope == "brand-specific":
                if redistribution != "allowed" or materialization != "allowed":
                    return False, False, "brand-asset-publication-guard"
            if redistribution == "metadata-only":
                if not include_metadata_only:
                    return False, False, "metadata-only-disabled"
                return True, False, "metadata-only"
            return True, materialization == "allowed", "allowed"
        if redistribution == "forbidden" or materialization == "forbidden":
            if redistribution == "metadata-only" and include_metadata_only:
                return True, False, "metadata-only"
            return False, False, "rights-forbidden"
        if redistribution == "metadata-only":
            if not include_metadata_only:
                return False, False, "metadata-only-disabled"
            return True, False, "metadata-only"
        return True, materialization in {"allowed", "local-only"}, "private-runtime-allowed"

    @staticmethod
    def _matches_filter(record: Mapping[str, Any], request: Mapping[str, Any]) -> tuple[bool, list[str]]:
        filters = request["filters"]
        classification = record["classification"]
        match_basis: list[str] = []
        stage_values = set(classification["stages"])
        if request["stage"] not in stage_values and "shared" not in stage_values:
            return False, []
        match_basis.append("stage")
        direct_pairs = (
            ("record_types", {record["record_type"]}, "record_type"),
            ("provider_ids", {record["provider_id"]}, "provider_id"),
            ("task_modes", set(classification["task_modes"]), "task_mode"),
            ("page_roles", set(classification["page_roles"]), "page_role"),
            ("semantic_relations", set(classification["semantic_relations"]), "semantic_relation"),
            ("purpose_tags", set(classification["purpose_tags"]), "purpose_tag"),
            ("languages", set(classification["languages"]), "language"),
            ("failure_signals", set(classification["failure_signals"]), "failure_signal"),
        )
        for filter_key, record_values, basis_name in direct_pairs:
            requested = set(filters.get(filter_key, []))
            if requested:
                if not requested.intersection(record_values):
                    return False, []
                match_basis.append(basis_name)
        return True, match_basis

    @staticmethod
    def _search_text(record: Mapping[str, Any]) -> str:
        classification = record["classification"]
        payload_ref = record.get("payload", {}).get("ref", "")
        payload_text = json.dumps(payload_ref, ensure_ascii=False, sort_keys=True) if isinstance(payload_ref, Mapping) else str(payload_ref)
        return "\n".join([
            record["record_id"], record["title"], record["summary"], record["record_type"],
            " ".join(classification["task_modes"]), " ".join(classification["page_roles"]),
            " ".join(classification["semantic_relations"]), " ".join(classification["purpose_tags"]),
            " ".join(classification["failure_signals"]), payload_text,
        ])

    def _rank(self, request: Mapping[str, Any]) -> list[dict[str, Any]]:
        eligible: list[tuple[str, dict[str, Any], list[str], bool, str]] = []
        for provider in self.providers:
            for record in provider.records:
                matches, match_basis = self._matches_filter(record, request)
                if not matches:
                    continue
                allowed, materializable, rights_decision = self._rights_decision(record, request)
                if allowed:
                    eligible.append((provider.provider_id, record, match_basis, materializable, rights_decision))
        query_tokens = Counter(tokenize(request.get("query", "")))
        document_tokens = [Counter(tokenize(self._search_text(record))) for _, record, _, _, _ in eligible]
        document_count = len(document_tokens)
        document_frequency: Counter[str] = Counter()
        for counts in document_tokens:
            document_frequency.update(counts.keys())
        average_length = sum(sum(counts.values()) for counts in document_tokens) / max(document_count, 1)
        ranked: list[dict[str, Any]] = []
        has_structured_filters = any(request["filters"].get(key) for key in request["filters"] if key != "include_metadata_only")
        for item, counts in zip(eligible, document_tokens):
            provider_id, record, match_basis, materializable, rights_decision = item
            length = max(sum(counts.values()), 1)
            lexical_score = 0.0
            for token, query_count in query_tokens.items():
                frequency = counts.get(token, 0)
                if not frequency:
                    continue
                df = max(document_frequency.get(token, 0), 1)
                inverse = math.log(1 + (document_count - df + 0.5) / (df + 0.5))
                denominator = frequency + 1.2 * (1 - 0.75 + 0.75 * length / max(average_length, 1))
                lexical_score += query_count * inverse * frequency * 2.2 / denominator
            structured_score = 0.22 * len(match_basis)
            if not query_tokens and not has_structured_filters:
                structured_score += 0.1
            score = lexical_score + structured_score
            if score <= 0:
                continue
            ranked.append({
                "record_id": record["record_id"], "record_type": record["record_type"], "provider_id": provider_id,
                "title": record["title"], "score": round(score, 6),
                "match_basis": sorted(set(match_basis + (["lexical"] if lexical_score > 0 else []))),
                "rights_decision": rights_decision, "materializable": materializable,
                "source_id": record["source"]["source_id"], "source_revision": record["source"]["source_revision"],
                "license": record["rights"]["license"], "never_copy": list(record["rights"].get("never_copy", [])),
                "neighbor_of": None, "neighbor_type": None,
            })
        ranked.sort(key=lambda item: (-item["score"], item["provider_id"], item["record_id"]))
        return ranked

    def _expand_neighbors(self, ranked: list[dict[str, Any]], request: Mapping[str, Any]) -> list[dict[str, Any]]:
        limited = ranked[: request["limit"]]
        expanded = list(limited)
        seen = {item["record_id"] for item in expanded}
        for result in limited:
            _, source = self._records[result["record_id"]]
            for field in ("physical", "semantic"):
                maximum = request["neighbor_expansion"].get(field, 0)
                for neighbor_id in source["neighbors"].get(field, [])[:maximum]:
                    if neighbor_id in seen or neighbor_id not in self._records:
                        continue
                    provider_id, neighbor = self._records[neighbor_id]
                    matches, match_basis = self._matches_filter(neighbor, request)
                    if not matches:
                        continue
                    allowed, materializable, rights_decision = self._rights_decision(neighbor, request)
                    if not allowed:
                        continue
                    expanded.append({
                        "record_id": neighbor_id, "record_type": neighbor["record_type"], "provider_id": provider_id,
                        "title": neighbor["title"], "score": 0.0,
                        "match_basis": sorted(set(match_basis + [f"{field}-neighbor"])),
                        "rights_decision": rights_decision, "materializable": materializable,
                        "source_id": neighbor["source"]["source_id"], "source_revision": neighbor["source"]["source_revision"],
                        "license": neighbor["rights"]["license"], "never_copy": list(neighbor["rights"].get("never_copy", [])),
                        "neighbor_of": result["record_id"], "neighbor_type": field,
                    })
                    seen.add(neighbor_id)
        return expanded

    def search(self, request: Mapping[str, Any], *, created_at: str | None = None) -> dict[str, Any]:
        normalized_request = validate_request(request)
        candidates = self._expand_neighbors(self._rank(normalized_request), normalized_request)
        receipt_seed = {"request": normalized_request, "index_snapshot": self.snapshots(), "candidate_ids": [candidate["record_id"] for candidate in candidates]}
        return {
            "contract": RECEIPT_CONTRACT,
            "receipt_id": f"receipt-{sha256_json(receipt_seed)[:20]}",
            "created_at": created_at or utc_now(),
            "request": normalized_request,
            "index_snapshot": self.snapshots(),
            "candidates": candidates,
            "selection": {"selected": [], "rejected": []},
            "fallback": {"used": False, "reason": "no-eligible-registered-record" if not candidates else ""},
            "hallucination_guard": {"only_registered_records": True, "invented_record_count": 0, "candidate_count": len(candidates)},
        }

    def finalize_receipt(self, receipt: Mapping[str, Any], *, selected: Mapping[str, str], rejected: Mapping[str, str] | None = None) -> dict[str, Any]:
        require(receipt.get("contract") == RECEIPT_CONTRACT, "invalid receipt contract")
        candidate_ids = {candidate["record_id"] for candidate in receipt.get("candidates", [])}
        unknown = set(selected) - candidate_ids
        require(not unknown, f"cannot select unregistered or unretrieved records: {sorted(unknown)}")
        rejected = rejected or {}
        unknown_rejected = set(rejected) - candidate_ids
        require(not unknown_rejected, f"cannot reject unregistered or unretrieved records: {sorted(unknown_rejected)}")
        overlap = set(selected).intersection(rejected)
        require(not overlap, f"records cannot be both selected and rejected: {sorted(overlap)}")
        for record_id, reason in list(selected.items()) + list(rejected.items()):
            require_nonempty_string(reason, f"selection reason for {record_id}")
        finalized = copy.deepcopy(dict(receipt))
        finalized["selection"] = {
            "selected": [{"record_id": record_id, "reason": selected[record_id]} for record_id in sorted(selected)],
            "rejected": [{"record_id": record_id, "reason": rejected[record_id]} for record_id in sorted(rejected)],
        }
        finalized["fallback"] = {"used": not bool(selected), "reason": "no-record-selected" if finalized.get("candidates") and not selected else finalized["fallback"].get("reason", "")}
        return finalized
