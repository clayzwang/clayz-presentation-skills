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
            if redistribution in {"local-private", "owner-private", "forbidden"}:
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
        return True, materialization in {"allowed", "local-only", "owner-private"}, "private-runtime-allowed"

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
            ("format_tags", set(classification.get("format_tags", [])), "format_tag"),
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
            " ".join(classification.get("format_tags", [])),
        ])

    @staticmethod
    def _candidate_similarity(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
        if left.get("record_id") == right.get("record_id"):
            return 1.0
        source_penalty = 1.0 if left.get("source_id") == right.get("source_id") else 0.0
        type_penalty = 0.35 if left.get("record_type") == right.get("record_type") else 0.0
        left_tokens = set(tokenize(str(left.get("title", ""))))
        right_tokens = set(tokenize(str(right.get("title", ""))))
        union = left_tokens | right_tokens
        lexical = len(left_tokens & right_tokens) / len(union) if union else 0.0
        return min(1.0, max(source_penalty, type_penalty * lexical))

    def _diversify(self, ranked: list[dict[str, Any]], request: Mapping[str, Any]) -> list[dict[str, Any]]:
        if len(ranked) < 2:
            return ranked
        relevance_weight = float(request["ranking_policy"]["diversity_lambda"])
        selected: list[dict[str, Any]] = []
        remaining = list(ranked)
        while remaining:
            candidate = max(
                remaining,
                key=lambda item: (
                    relevance_weight * float(item["score"])
                    - (1 - relevance_weight) * max((self._candidate_similarity(item, chosen) for chosen in selected), default=0.0),
                    float(item["score"]),
                    str(item["record_id"]),
                ),
            )
            selected.append(candidate)
            remaining.remove(candidate)
        return selected

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
            semantic = 1 - math.exp(-max(lexical_score, 0.0))
            task_context = sum(name in match_basis for name in ("task_mode", "page_role", "language")) / 3
            relation_purpose = sum(name in match_basis for name in ("semantic_relation", "purpose_tag", "failure_signal")) / 3
            format_fit = 1.0 if "format_tag" in match_basis else (0.25 if request["ranking_policy"]["profile"] == "content" else 0.0)
            evidence_quality = 1.0 if materializable else 0.6
            components = {
                "semantic": semantic,
                "stage": 1.0,
                "task_context": task_context,
                "relation_purpose": relation_purpose,
                "format_fit": format_fit,
                "evidence_quality": evidence_quality,
            }
            weights = {
                "content": {"semantic": 0.40, "stage": 0.10, "task_context": 0.20, "relation_purpose": 0.15, "format_fit": 0.05, "evidence_quality": 0.10},
                "format": {"semantic": 0.25, "stage": 0.10, "task_context": 0.15, "relation_purpose": 0.15, "format_fit": 0.25, "evidence_quality": 0.10},
                "implementation": {"semantic": 0.25, "stage": 0.10, "task_context": 0.15, "relation_purpose": 0.10, "format_fit": 0.25, "evidence_quality": 0.15},
                "failure": {"semantic": 0.35, "stage": 0.10, "task_context": 0.10, "relation_purpose": 0.25, "format_fit": 0.10, "evidence_quality": 0.10},
            }[request["ranking_policy"]["profile"]]
            score = sum(components[key] * weights[key] for key in components)
            if score <= 0:
                continue
            ranked.append({
                "record_id": record["record_id"], "record_type": record["record_type"], "provider_id": provider_id,
                "title": record["title"], "score": round(min(score, 1.0), 6),
                "rank": 0,
                "score_breakdown": {key: round(value, 6) for key, value in components.items()},
                "match_basis": sorted(set(match_basis + (["lexical"] if lexical_score > 0 else []))),
                "rights_decision": rights_decision, "materializable": materializable,
                "source_id": record["source"]["source_id"], "source_revision": record["source"]["source_revision"],
                "license": record["rights"]["license"], "never_copy": list(record["rights"].get("never_copy", [])),
                "neighbor_of": None, "neighbor_type": None,
            })
        ranked.sort(key=lambda item: (-item["score"], item["provider_id"], item["record_id"]))
        ranked = self._diversify(ranked, request)
        for rank, candidate in enumerate(ranked, start=1):
            candidate["rank"] = rank
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
                        "rank": len(expanded) + 1,
                        "score_breakdown": {
                            "semantic": 0.0, "stage": 1.0, "task_context": 0.0,
                            "relation_purpose": 0.0, "format_fit": 0.0, "evidence_quality": 1.0 if materializable else 0.6,
                        },
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
            "ranking": {
                **normalized_request["ranking_policy"],
                "eligible_candidate_count": len(candidates),
                "above_threshold_count": sum(
                    candidate["score"] >= normalized_request["ranking_policy"]["minimum_score"]
                    for candidate in candidates
                ),
            },
            "fallback": {"used": False, "reason": "no-eligible-registered-record" if not candidates else ""},
            "hallucination_guard": {"only_registered_records": True, "invented_record_count": 0, "candidate_count": len(candidates)},
        }

    def finalize_receipt(self, receipt: Mapping[str, Any], *, selected: Mapping[str, Any], rejected: Mapping[str, Any] | None = None) -> dict[str, Any]:
        require(receipt.get("contract") == RECEIPT_CONTRACT, "invalid receipt contract")
        candidate_ids = {candidate["record_id"] for candidate in receipt.get("candidates", [])}
        unknown = set(selected) - candidate_ids
        require(not unknown, f"cannot select unregistered or unretrieved records: {sorted(unknown)}")
        rejected = rejected or {}
        unknown_rejected = set(rejected) - candidate_ids
        require(not unknown_rejected, f"cannot reject unregistered or unretrieved records: {sorted(unknown_rejected)}")
        overlap = set(selected).intersection(rejected)
        require(not overlap, f"records cannot be both selected and rejected: {sorted(overlap)}")
        candidate_by_id = {candidate["record_id"]: candidate for candidate in receipt.get("candidates", [])}
        threshold = float(receipt.get("ranking", {}).get("minimum_score", 0.0))
        maximum = int(receipt.get("ranking", {}).get("max_selected", 10))
        require(len(selected) <= maximum, f"selection exceeds ranking max_selected={maximum}")

        def decision(record_id: str, raw: Any, *, selected_record: bool) -> dict[str, Any]:
            if isinstance(raw, Mapping):
                reason = require_nonempty_string(raw.get("reason"), f"selection reason for {record_id}")
                adoption_targets = list(raw.get("adoption_targets", []))
                adoption_status = raw.get("adoption_status", "planned" if selected_record else "not-adopted")
            else:
                reason = require_nonempty_string(raw, f"selection reason for {record_id}")
                adoption_targets = list(receipt.get("request", {}).get("task_context", {}).get("target_refs", [])) if selected_record else []
                adoption_status = "planned" if selected_record else "not-adopted"
            require(all(isinstance(item, str) and item.strip() for item in adoption_targets), f"adoption targets for {record_id} must be strings")
            if selected_record:
                require(bool(adoption_targets), f"selected record {record_id} requires at least one adoption target")
                require(candidate_by_id[record_id].get("score", 0) >= threshold, f"selected record {record_id} is below minimum_score={threshold}")
                require(adoption_status in {"planned", "material"}, f"selected record {record_id} has invalid adoption status")
            else:
                require(adoption_status == "not-adopted", f"rejected record {record_id} must be not-adopted")
            return {
                "record_id": record_id,
                "reason": reason,
                "adoption_targets": sorted(set(adoption_targets)),
                "adoption_status": adoption_status,
            }
        finalized = copy.deepcopy(dict(receipt))
        finalized["selection"] = {
            "selected": [decision(record_id, selected[record_id], selected_record=True) for record_id in sorted(selected)],
            "rejected": [decision(record_id, rejected[record_id], selected_record=False) for record_id in sorted(rejected)],
            "coverage_status": "complete" if selected else "unresolved",
            "coverage_gaps": [] if selected else ["no-record-selected"],
        }
        finalized["fallback"] = {"used": not bool(selected), "reason": "no-record-selected" if finalized.get("candidates") and not selected else finalized["fallback"].get("reason", "")}
        return finalized
