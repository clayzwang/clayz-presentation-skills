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
    for key in (
        "task_modes",
        "page_roles",
        "semantic_relations",
        "purpose_tags",
        "languages",
        "failure_signals",
    ):
        require_string_list(classification.get(key, []), f"record.classification.{key}")
    asset_class = require_nonempty_string(classification.get("asset_class"), "record.classification.asset_class")
    brand_scope = require_nonempty_string(classification.get("brand_scope"), "record.classification.brand_scope")
    require(brand_scope in {"none", "generic", "brand-specific"}, "record.classification.brand_scope is invalid")

    payload = normalized.get("payload")
    require(isinstance(payload, Mapping), "record.payload must be an object")
    require(payload.get("kind") in {"inline", "path", "uri"}, "record.payload.kind is invalid")
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
    require(isinstance(normalized.get("query", ""), str), "request.query must be a string")
    rights_context = require_nonempty_string(normalized.get("rights_context"), "request.rights_context")
    require(rights_context in RIGHTS_CONTEXTS, f"unsupported rights_context: {rights_context}")
    limit = normalized.get("limit", 5)
    require(isinstance(limit, int) and 1 <= limit <= 50, "request.limit must be between 1 and 50")
    normalized["limit"] = limit
    require(isinstance(normalized.get("require_human_admission", True), bool), "request.require_human_admission must be boolean")

    filters = normalized.get("filters", {})
    require(isinstance(filters, Mapping), "request.filters must be an object")
    resolved_filters = dict(filters)
    for key in (
        "record_types",
        "provider_ids",
        "task_modes",
        "page_roles",
        "semantic_relations",
        "purpose_tags",
        "languages",
        "failure_signals",
    ):
        values = require_string_list(filters.get(key, []), f"request.filters.{key}")
        if key == "record_types":
            require(all(value in RECORD_TYPES for value in values), "request.filters.record_types contains an unsupported value")
        resolved_filters[key] = values
    include_metadata_only = filters.get("include_metadata_only", True)
    require(isinstance(include_metadata_only, bool), "request.filters.include_metadata_only must be boolean")
    resolved_filters["include_metadata_only"] = include_metadata_only
    normalized["filters"] = resolved_filters

    expansion = normalized.get("neighbor_expansion", {"physical": 0, "semantic": 0})
    require(isinstance(expansion, Mapping), "request.neighbor_expansion must be an object")
    resolved_expansion: dict[str, int] = {}
    for key in ("physical", "semantic"):
        value = expansion.get(key, 0)
        require(isinstance(value, int) and 0 <= value <= 10, f"request.neighbor_expansion.{key} must be between 0 and 10")
        resolved_expansion[key] = value
    normalized["neighbor_expansion"] = resolved_expansion
    return normalized
