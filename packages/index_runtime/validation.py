# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Contract validation for index records and retrieval requests."""

from __future__ import annotations

import copy
import re
from collections.abc import Mapping
from typing import Any

from .constants import (
    HIGH_RISK_BRAND_ASSET_CLASSES,
    INDEX_CONTRACT,
    MATERIALIZATION,
    QUALITY_STATES,
    RECORD_TYPES,
    REDISTRIBUTION,
    REQUEST_CONTRACT,
    RIGHTS_CONTEXTS,
    STAGES,
)
from .utils import require, require_nonempty_string, require_string_list


def validate_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize one governed index record."""

    require(isinstance(record, Mapping), "record must be an object")
    normalized = copy.deepcopy(dict(record))
    require(normalized.get("contract") == INDEX_CONTRACT, f"record.contract must be {INDEX_CONTRACT}")

    record_id = require_nonempty_string(normalized.get("record_id"), "record.record_id")
    require(bool(re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,127}", record_id)), "record.record_id has invalid characters")
    record_type = require_nonempty_string(normalized.get("record_type"), "record.record_type")
    require(record_type in RECORD_TYPES, f"unsupported record_type: {record_type}")
    require_nonempty_string(normalized.get("provider_id"), "record.provider_id")
    require_nonempty_string(normalized.get("title"), "record.title")
    require_nonempty_string(normalized.get("summary"), "record.summary")

    source = normalized.get("source")
    require(isinstance(source, Mapping), "record.source must be an object")
    require_nonempty_string(source.get("source_id"), "record.source.source_id")
    require_nonempty_string(source.get("source_uri"), "record.source.source_uri")
    require_nonempty_string(source.get("source_revision"), "record.source.source_revision")
    sha256 = require_nonempty_string(source.get("sha256"), "record.source.sha256")
    require(bool(re.fullmatch(r"[0-9a-f]{64}", sha256)), "record.source.sha256 must be lowercase SHA-256")

    governance = normalized.get("governance")
    require(isinstance(governance, Mapping), "record.governance must be an object")
    require(isinstance(governance.get("human_admitted"), bool), "record.governance.human_admitted must be boolean")
    quality_status = require_nonempty_string(governance.get("quality_status"), "record.governance.quality_status")
    require(quality_status in QUALITY_STATES, f"unsupported quality_status: {quality_status}")
    require(isinstance(governance.get("public_catalog_eligible"), bool), "record.governance.public_catalog_eligible must be boolean")
    require(isinstance(governance.get("deprecated"), bool), "record.governance.deprecated must be boolean")

    rights = normalized.get("rights")
    require(isinstance(rights, Mapping), "record.rights must be an object")
    require_nonempty_string(rights.get("license"), "record.rights.license")
    redistribution = require_nonempty_string(rights.get("redistribution"), "record.rights.redistribution")
    materialization = require_nonempty_string(rights.get("materialization"), "record.rights.materialization")
    require(redistribution in REDISTRIBUTION, f"unsupported redistribution state: {redistribution}")
    require(materialization in MATERIALIZATION, f"unsupported materialization state: {materialization}")
    require(isinstance(rights.get("attribution_required"), bool), "record.rights.attribution_required must be boolean")
    require_string_list(rights.get("never_copy", []), "record.rights.never_copy")

    classification = normalized.get("classification")
    require(isinstance(classification, Mapping), "record.classification must be an object")
    stages = require_string_list(classification.get("stages", []), "record.classification.stages")
    require(all(stage in STAGES for stage in stages), "record.classification.stages contains an unsupported stage")
    for key in ("task_modes", "page_roles", "semantic_relations", "purpose_tags", "languages", "failure_signals"):
        require_string_list(classification.get(key, []), f"record.classification.{key}")
    require_string_list(classification.get("format_tags", []), "record.classification.format_tags")
    asset_class = require_nonempty_string(classification.get("asset_class"), "record.classification.asset_class")
    brand_scope = require_nonempty_string(classification.get("brand_scope"), "record.classification.brand_scope")
    require(brand_scope in {"none", "generic", "brand-specific"}, "record.classification.brand_scope is invalid")

    payload = normalized.get("payload")
    require(isinstance(payload, Mapping), "record.payload must be an object")
    payload_kind = payload.get("kind")
    require(payload_kind in {"inline", "path", "uri"}, "record.payload.kind is invalid")
    if payload_kind == "inline":
        require(isinstance(payload.get("ref"), Mapping), "inline record.payload.ref must be an object")
    else:
        require_nonempty_string(payload.get("ref"), "record.payload.ref")

    neighbors = normalized.get("neighbors", {"physical": [], "semantic": []})
    require(isinstance(neighbors, Mapping), "record.neighbors must be an object")
    physical = require_string_list(neighbors.get("physical", []), "record.neighbors.physical")
    semantic = require_string_list(neighbors.get("semantic", []), "record.neighbors.semantic")
    require(record_id not in set(physical) | set(semantic), "record cannot be its own neighbor")

    if asset_class in HIGH_RISK_BRAND_ASSET_CLASSES and brand_scope == "brand-specific":
        if governance.get("public_catalog_eligible"):
            require(
                redistribution == "allowed" and materialization == "allowed",
                "brand-specific template/master/font/brand-kit cannot be public-catalog eligible without explicit redistribution and materialization rights",
            )
    return normalized


def validate_request(request: Mapping[str, Any]) -> dict[str, Any]:
    require(isinstance(request, Mapping), "request must be an object")
    normalized = copy.deepcopy(dict(request))
    require(normalized.get("contract") == REQUEST_CONTRACT, f"request.contract must be {REQUEST_CONTRACT}")
    require_nonempty_string(normalized.get("request_id"), "request.request_id")
    stage = require_nonempty_string(normalized.get("stage"), "request.stage")
    require(stage in STAGES, f"unsupported request stage: {stage}")
    query = require_nonempty_string(normalized.get("query"), "request.query")
    require(len(query.strip()) >= 8, "request.query must contain a substantive task question of at least 8 characters")
    normalized["query"] = query.strip()
    intent = require_nonempty_string(normalized.get("intent", "task-reference"), "request.intent")
    require(
        intent in {"task-reference", "format-reference", "implementation-reference", "failure-diagnosis", "source-consumption"},
        "request.intent is unsupported",
    )
    normalized["intent"] = intent
    rights_context = require_nonempty_string(normalized.get("rights_context"), "request.rights_context")
    require(rights_context in RIGHTS_CONTEXTS, f"unsupported rights_context: {rights_context}")
    limit = normalized.get("limit", 5)
    require(isinstance(limit, int) and 1 <= limit <= 50, "request.limit must be between 1 and 50")
    normalized["limit"] = limit
    require(isinstance(normalized.get("require_human_admission", True), bool), "request.require_human_admission must be boolean")

    filters = normalized.get("filters", {})
    require(isinstance(filters, Mapping), "request.filters must be an object")
    resolved_filters = dict(filters)
    for key in ("record_types", "provider_ids", "task_modes", "page_roles", "semantic_relations", "purpose_tags", "languages", "failure_signals", "format_tags"):
        values = require_string_list(filters.get(key, []), f"request.filters.{key}")
        if key == "record_types":
            require(all(value in RECORD_TYPES for value in values), "request.filters.record_types contains an unsupported value")
        resolved_filters[key] = values
    include_metadata_only = filters.get("include_metadata_only", True)
    require(isinstance(include_metadata_only, bool), "request.filters.include_metadata_only must be boolean")
    resolved_filters["include_metadata_only"] = include_metadata_only
    normalized["filters"] = resolved_filters

    task_context = normalized.get("task_context")
    if task_context is None:
        task_context = {
            "decision_goal": query.strip(),
            "target_refs": [f"stage:{stage}"],
            "format_need": intent,
        }
    require(isinstance(task_context, Mapping), "request.task_context must be an object")
    decision_goal = require_nonempty_string(task_context.get("decision_goal"), "request.task_context.decision_goal")
    target_refs = require_string_list(task_context.get("target_refs", []), "request.task_context.target_refs")
    require(bool(target_refs), "request.task_context.target_refs must identify at least one stage or slide decision")
    format_need = require_nonempty_string(task_context.get("format_need"), "request.task_context.format_need")
    normalized["task_context"] = {
        "decision_goal": decision_goal,
        "target_refs": target_refs,
        "format_need": format_need,
    }

    ranking = normalized.get("ranking_policy")
    if ranking is None:
        profile_by_intent = {
            "task-reference": "content", "source-consumption": "content",
            "format-reference": "format", "implementation-reference": "implementation",
            "failure-diagnosis": "failure",
        }
        ranking = {
            "profile": profile_by_intent[intent], "minimum_score": 0.1,
            "max_selected": min(limit, 5), "diversity_lambda": 0.7,
        }
    require(isinstance(ranking, Mapping), "request.ranking_policy must be an object")
    profile = require_nonempty_string(ranking.get("profile"), "request.ranking_policy.profile")
    require(profile in {"content", "format", "implementation", "failure"}, "request.ranking_policy.profile is unsupported")
    minimum_score = ranking.get("minimum_score")
    require(isinstance(minimum_score, (int, float)) and 0 <= minimum_score <= 1, "request.ranking_policy.minimum_score must be between 0 and 1")
    max_selected = ranking.get("max_selected")
    require(isinstance(max_selected, int) and 1 <= max_selected <= 10, "request.ranking_policy.max_selected must be between 1 and 10")
    diversity_lambda = ranking.get("diversity_lambda")
    require(isinstance(diversity_lambda, (int, float)) and 0 <= diversity_lambda <= 1, "request.ranking_policy.diversity_lambda must be between 0 and 1")
    normalized["ranking_policy"] = {
        "profile": profile,
        "minimum_score": float(minimum_score),
        "max_selected": max_selected,
        "diversity_lambda": float(diversity_lambda),
    }

    expansion = normalized.get("neighbor_expansion", {"physical": 0, "semantic": 0})
    require(isinstance(expansion, Mapping), "request.neighbor_expansion must be an object")
    resolved_expansion: dict[str, int] = {}
    for key in ("physical", "semantic"):
        value = expansion.get(key, 0)
        require(isinstance(value, int) and 0 <= value <= 10, f"request.neighbor_expansion.{key} must be between 0 and 10")
        resolved_expansion[key] = value
    normalized["neighbor_expansion"] = resolved_expansion
    return normalized
