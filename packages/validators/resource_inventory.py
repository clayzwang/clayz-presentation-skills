#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Build and validate the pre-Logic presentation resource inventory."""

from __future__ import annotations

import copy
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime.utils import sha256_json  # noqa: E402


CONTRACT = "io.clayz.presentation.resource-inventory/1.0"
USAGE_CONTRACT = "io.clayz.presentation.resource-usage/1.0"
TASK_MODES = {"new-build", "revision", "audit"}
RUNTIME_MODES = {"owner-personal", "public-core"}
SCAN_SCOPES = {
    "plugin-runtime",
    "task-inputs",
    "owner-library",
    "public-index",
    "brand-assets",
    "host-capabilities",
    "font-environment",
}
CORE_COMPLETE_SCOPES = {
    "plugin-runtime",
    "task-inputs",
    "public-index",
    "host-capabilities",
    "font-environment",
}
CATEGORIES = {
    "task-input",
    "plugin-skill",
    "runtime-config",
    "index-provider",
    "library-source",
    "reference-pool",
    "theme",
    "template",
    "font",
    "brand-asset",
    "host-capability",
    "authoring-route",
    "renderer",
    "target-application",
}
ORIGINS = {"task", "plugin", "owner-library", "public-catalog", "host"}
AVAILABILITY = {"available", "partial", "missing", "inaccessible", "not-applicable"}
DECISIONS = {"selected", "deferred", "excluded", "unavailable"}
RIGHTS = {"task-provided", "owner-private", "public-open-source", "host-capability"}
STAGES = {"root", "logic", "copy", "art-direction", "output", "supervisor"}
WORKFLOW_STAGES = ("logic", "copy", "art-direction", "output", "supervisor")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
RESOURCE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
LOGICAL_URI = re.compile(r"^(?:attachment|bundle|host|library|plugin|public-index|task)://\S+$")
PRIVATE_PATH = re.compile(r"(?i)(?:\b[a-z]:[\\/]|(?:^|[\s(])/(?:users|home)/)")
SECRET_TEXT = re.compile(r"(?i)(?:api[_-]?key\s*[=:]|bearer\s+[a-z0-9._-]{12,}|\bsk-[a-z0-9_-]{12,})")


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require_keys(obj: Any, keys: set[str], path: str, errors: list[str]) -> None:
    if not isinstance(obj, Mapping):
        errors.append(f"{path}: must be an object")
        return
    missing = sorted(keys - set(obj))
    if missing:
        errors.append(f"{path}: missing keys {missing}")


def _unique_strings(value: Any, path: str, errors: list[str], *, allowed: set[str] | None = None) -> list[str]:
    if not isinstance(value, list) or any(not nonempty(item) for item in value):
        errors.append(f"{path}: must be a unique non-empty string array")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{path}: must be a unique non-empty string array")
        return []
    if allowed is not None and any(item not in allowed for item in value):
        errors.append(f"{path}: contains unsupported values")
    return list(value)


def _timestamp(value: Any, path: str, errors: list[str]) -> datetime | None:
    if not nonempty(value):
        errors.append(f"{path}: must be a timezone-aware ISO timestamp")
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{path}: must be a timezone-aware ISO timestamp")
        return None
    if parsed.utcoffset() is None:
        errors.append(f"{path}: timezone is required")
        return None
    return parsed


def _brief_payload(brief: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "language": brief.get("language"),
        "reported_resource_ids": brief.get("reported_resource_ids"),
        "reported_selected_resource_ids": brief.get("reported_selected_resource_ids"),
        "reported_not_selected_resource_ids": brief.get("reported_not_selected_resource_ids"),
        "reported_unavailable_resource_ids": brief.get("reported_unavailable_resource_ids"),
        "discovered_lines": brief.get("discovered_lines"),
        "selected_lines": brief.get("selected_lines"),
        "unavailable_lines": brief.get("unavailable_lines"),
        "execution_line": brief.get("execution_line"),
    }


def _safe_user_line(value: Any, path: str, errors: list[str]) -> None:
    if not nonempty(value):
        errors.append(f"{path}: must be non-empty")
        return
    text = str(value)
    if PRIVATE_PATH.search(text) or SECRET_TEXT.search(text):
        errors.append(f"{path}: user brief must not expose private paths or secrets")


def _scope_blocking_reasons(inventory: Mapping[str, Any]) -> list[str]:
    scope_by_id = {
        item.get("scope"): item
        for item in inventory.get("scan_scope", [])
        if isinstance(item, Mapping)
    }
    reasons: list[str] = []
    for scope in sorted(CORE_COMPLETE_SCOPES):
        if scope_by_id.get(scope, {}).get("status") != "complete":
            reasons.append(f"required scan scope is not complete: {scope}")
    owner_status = scope_by_id.get("owner-library", {}).get("status")
    if inventory.get("runtime_mode") == "owner-personal" and owner_status != "complete":
        reasons.append("owner-personal mode requires a complete owner-library scan")
    if inventory.get("runtime_mode") == "public-core" and owner_status not in {"not-applicable", "complete"}:
        reasons.append("public-core owner-library scope must be not-applicable or complete")
    route = inventory.get("execution_route")
    if not isinstance(route, Mapping) or route.get("status") != "ready":
        reasons.append("authoring and rendering route is not ready")
    brief = inventory.get("user_brief")
    if not isinstance(brief, Mapping) or brief.get("status") != "presented":
        reasons.append("resource inventory brief has not been presented to the user")
    return reasons


def finalize_resource_inventory(draft: Mapping[str, Any]) -> dict[str, Any]:
    """Derive counts, user-brief hash, gate state, and immutable lock from a draft."""

    result = copy.deepcopy(dict(draft))
    resources = [item for item in result.get("resources", []) if isinstance(item, Mapping)]
    selected_ids = sorted(str(item.get("resource_id")) for item in resources if item.get("decision") == "selected")
    deferred_ids = sorted(str(item.get("resource_id")) for item in resources if item.get("decision") == "deferred")
    unavailable_ids = sorted(str(item.get("resource_id")) for item in resources if item.get("decision") == "unavailable")
    blocking_ids = sorted(
        str(item.get("resource_id"))
        for item in resources
        if item.get("required") is True
        and (item.get("availability") != "available" or item.get("decision") != "selected")
    )
    result["summary"] = {
        "resource_entry_count": len(resources),
        "item_quantity_total": sum(item.get("quantity", 0) for item in resources if isinstance(item.get("quantity"), int)),
        "available_entry_count": sum(item.get("availability") == "available" for item in resources),
        "selected_entry_count": len(selected_ids),
        "deferred_entry_count": len(deferred_ids),
        "unavailable_entry_count": len(unavailable_ids),
        "missing_required_entry_count": len(blocking_ids),
    }
    result["selected_resource_ids"] = selected_ids
    result["deferred_resource_ids"] = deferred_ids
    result["unavailable_resource_ids"] = unavailable_ids
    brief = result.get("user_brief")
    if isinstance(brief, dict):
        brief["content_sha256"] = sha256_json(_brief_payload(brief))
    blocking_reasons = _scope_blocking_reasons(result)
    gate = result.setdefault("gate", {})
    ready = not blocking_ids and not blocking_reasons
    gate["status"] = "ready" if ready else "blocked"
    gate["authoring_may_start"] = ready
    gate["blocking_resource_ids"] = blocking_ids
    gate["blocking_reasons"] = blocking_reasons
    if not ready:
        gate["authoring_started_at"] = None
    result.pop("lock", None)
    result["lock"] = {"algorithm": "sha256", "digest": sha256_json(result)}
    return result


def validate_resource_inventory(
    inventory: Any,
    path: str,
    errors: list[str],
    *,
    require_ready: bool = True,
) -> None:
    """Validate discovery coverage, resource decisions, user briefing, and time order."""

    _require_keys(
        inventory,
        {
            "contract", "inventory_id", "revision", "task_mode", "runtime_mode", "created_at",
            "scan_scope", "resources", "summary", "selected_resource_ids", "deferred_resource_ids",
            "unavailable_resource_ids", "execution_route", "user_brief", "gate", "lock",
        },
        path,
        errors,
    )
    if not isinstance(inventory, Mapping):
        return
    if inventory.get("contract") != CONTRACT:
        errors.append(f"{path}.contract: expected {CONTRACT}")
    if not nonempty(inventory.get("inventory_id")) or not RESOURCE_ID.fullmatch(str(inventory.get("inventory_id", ""))):
        errors.append(f"{path}.inventory_id: invalid identifier")
    if not isinstance(inventory.get("revision"), int) or inventory.get("revision", 0) < 1:
        errors.append(f"{path}.revision: must be a positive integer")
    if inventory.get("task_mode") not in TASK_MODES:
        errors.append(f"{path}.task_mode: invalid value")
    if inventory.get("runtime_mode") not in RUNTIME_MODES:
        errors.append(f"{path}.runtime_mode: invalid value")
    created_at = _timestamp(inventory.get("created_at"), f"{path}.created_at", errors)

    scopes = inventory.get("scan_scope")
    scope_ids: list[str] = []
    if not isinstance(scopes, list):
        errors.append(f"{path}.scan_scope: must be an array")
    else:
        for index, item in enumerate(scopes):
            spath = f"{path}.scan_scope[{index}]"
            _require_keys(item, {"scope", "status", "evidence_ref", "discovered_entry_count", "note"}, spath, errors)
            if not isinstance(item, Mapping):
                continue
            scope = item.get("scope")
            if scope not in SCAN_SCOPES or scope in scope_ids:
                errors.append(f"{spath}.scope: must be supported and unique")
            else:
                scope_ids.append(str(scope))
            if item.get("status") not in {"complete", "partial", "unavailable", "not-applicable"}:
                errors.append(f"{spath}.status: invalid value")
            if not nonempty(item.get("evidence_ref")) or not nonempty(item.get("note")):
                errors.append(f"{spath}: evidence_ref and note must be non-empty")
            if not isinstance(item.get("discovered_entry_count"), int) or item.get("discovered_entry_count", -1) < 0:
                errors.append(f"{spath}.discovered_entry_count: must be a non-negative integer")
        if set(scope_ids) != SCAN_SCOPES:
            errors.append(f"{path}.scan_scope: must cover exactly {sorted(SCAN_SCOPES)}")

    resources = inventory.get("resources")
    resource_by_id: dict[str, Mapping[str, Any]] = {}
    if not isinstance(resources, list) or not resources:
        errors.append(f"{path}.resources: must be a non-empty array")
        resources = []
    for index, item in enumerate(resources):
        rpath = f"{path}.resources[{index}]"
        _require_keys(
            item,
            {
                "resource_id", "category", "label", "origin", "locator", "availability", "required",
                "stages", "quantity", "fingerprint_sha256", "rights_context", "decision", "decision_reason",
                "evidence_ref",
            },
            rpath,
            errors,
        )
        if not isinstance(item, Mapping):
            continue
        resource_id = item.get("resource_id")
        if not nonempty(resource_id) or not RESOURCE_ID.fullmatch(str(resource_id)) or resource_id in resource_by_id:
            errors.append(f"{rpath}.resource_id: must be valid and unique")
        else:
            resource_by_id[str(resource_id)] = item
        if item.get("category") not in CATEGORIES:
            errors.append(f"{rpath}.category: invalid value")
        if item.get("origin") not in ORIGINS:
            errors.append(f"{rpath}.origin: invalid value")
        if item.get("availability") not in AVAILABILITY:
            errors.append(f"{rpath}.availability: invalid value")
        if item.get("decision") not in DECISIONS:
            errors.append(f"{rpath}.decision: invalid value")
        if item.get("rights_context") not in RIGHTS:
            errors.append(f"{rpath}.rights_context: invalid value")
        for key in ("label", "locator", "decision_reason", "evidence_ref"):
            if not nonempty(item.get(key)):
                errors.append(f"{rpath}.{key}: must be non-empty")
        if nonempty(item.get("locator")) and not LOGICAL_URI.fullmatch(str(item["locator"])):
            errors.append(f"{rpath}.locator: must be a sanitized logical URI")
        if not isinstance(item.get("required"), bool):
            errors.append(f"{rpath}.required: must be boolean")
        _unique_strings(item.get("stages"), f"{rpath}.stages", errors, allowed=STAGES)
        if not isinstance(item.get("quantity"), int) or item.get("quantity", 0) < 1:
            errors.append(f"{rpath}.quantity: must be a positive integer")
        fingerprint = item.get("fingerprint_sha256")
        if fingerprint is not None and (not isinstance(fingerprint, str) or not SHA256.fullmatch(fingerprint)):
            errors.append(f"{rpath}.fingerprint_sha256: must be null or lowercase SHA-256")
        if item.get("decision") == "selected" and item.get("availability") != "available":
            errors.append(f"{rpath}: selected resources must be available")
        if item.get("decision") == "unavailable" and item.get("availability") not in {"missing", "inaccessible"}:
            errors.append(f"{rpath}: unavailable decisions require missing or inaccessible availability")
        if item.get("decision") == "selected" and item.get("origin") != "host" and fingerprint is None:
            errors.append(f"{rpath}.fingerprint_sha256: selected non-host resources require a fingerprint")

    expected_selected = sorted(resource_id for resource_id, item in resource_by_id.items() if item.get("decision") == "selected")
    expected_deferred = sorted(resource_id for resource_id, item in resource_by_id.items() if item.get("decision") == "deferred")
    expected_unavailable = sorted(resource_id for resource_id, item in resource_by_id.items() if item.get("decision") == "unavailable")
    for key, expected in (
        ("selected_resource_ids", expected_selected),
        ("deferred_resource_ids", expected_deferred),
        ("unavailable_resource_ids", expected_unavailable),
    ):
        if inventory.get(key) != expected:
            errors.append(f"{path}.{key}: must be the sorted derived resource IDs")

    blocking_ids = sorted(
        resource_id
        for resource_id, item in resource_by_id.items()
        if item.get("required") is True
        and (item.get("availability") != "available" or item.get("decision") != "selected")
    )
    summary = inventory.get("summary")
    _require_keys(
        summary,
        {
            "resource_entry_count", "item_quantity_total", "available_entry_count", "selected_entry_count",
            "deferred_entry_count", "unavailable_entry_count", "missing_required_entry_count",
        },
        f"{path}.summary",
        errors,
    )
    if isinstance(summary, Mapping):
        expected_summary = {
            "resource_entry_count": len(resource_by_id),
            "item_quantity_total": sum(item.get("quantity", 0) for item in resource_by_id.values() if isinstance(item.get("quantity"), int)),
            "available_entry_count": sum(item.get("availability") == "available" for item in resource_by_id.values()),
            "selected_entry_count": len(expected_selected),
            "deferred_entry_count": len(expected_deferred),
            "unavailable_entry_count": len(expected_unavailable),
            "missing_required_entry_count": len(blocking_ids),
        }
        if dict(summary) != expected_summary:
            errors.append(f"{path}.summary: must match the derived resource counts")

    route = inventory.get("execution_route")
    _require_keys(
        route,
        {"status", "authoring_route", "render_route", "target_application", "evidence_ref"},
        f"{path}.execution_route",
        errors,
    )
    if isinstance(route, Mapping):
        if route.get("status") not in {"ready", "blocked"}:
            errors.append(f"{path}.execution_route.status: invalid value")
        for key in ("authoring_route", "render_route", "target_application", "evidence_ref"):
            if not nonempty(route.get(key)):
                errors.append(f"{path}.execution_route.{key}: must be non-empty")

    brief = inventory.get("user_brief")
    _require_keys(
        brief,
        {
            "status", "presented_at", "channel", "language", "discovered_lines", "selected_lines",
            "unavailable_lines", "execution_line", "content_sha256", "reported_resource_ids",
            "reported_selected_resource_ids", "reported_not_selected_resource_ids",
            "reported_unavailable_resource_ids",
        },
        f"{path}.user_brief",
        errors,
    )
    presented_at = None
    if isinstance(brief, Mapping):
        if brief.get("status") not in {"pending", "presented"}:
            errors.append(f"{path}.user_brief.status: invalid value")
        if brief.get("status") == "presented":
            presented_at = _timestamp(brief.get("presented_at"), f"{path}.user_brief.presented_at", errors)
        elif brief.get("presented_at") is not None:
            errors.append(f"{path}.user_brief.presented_at: pending brief must use null")
        if brief.get("channel") != "commentary":
            errors.append(f"{path}.user_brief.channel: must be commentary")
        if brief.get("language") not in {"zh-CN", "en-US"}:
            errors.append(f"{path}.user_brief.language: invalid value")
        reported = _unique_strings(
            brief.get("reported_resource_ids"),
            f"{path}.user_brief.reported_resource_ids",
            errors,
        )
        reported_selected = _unique_strings(
            brief.get("reported_selected_resource_ids"),
            f"{path}.user_brief.reported_selected_resource_ids",
            errors,
        )
        reported_not_selected = _unique_strings(
            brief.get("reported_not_selected_resource_ids"),
            f"{path}.user_brief.reported_not_selected_resource_ids",
            errors,
        )
        reported_unavailable = _unique_strings(
            brief.get("reported_unavailable_resource_ids"),
            f"{path}.user_brief.reported_unavailable_resource_ids",
            errors,
        )
        expected_reported = sorted(resource_by_id)
        expected_not_selected = sorted(set(resource_by_id) - set(expected_selected))
        if reported != expected_reported:
            errors.append(f"{path}.user_brief.reported_resource_ids: must cover every inventoried resource")
        if reported_selected != expected_selected:
            errors.append(f"{path}.user_brief.reported_selected_resource_ids: must cover every selected resource")
        if reported_not_selected != expected_not_selected:
            errors.append(f"{path}.user_brief.reported_not_selected_resource_ids: must cover every non-selected resource")
        if reported_unavailable != expected_unavailable:
            errors.append(f"{path}.user_brief.reported_unavailable_resource_ids: must cover every unavailable resource")
        discovered = _unique_strings(brief.get("discovered_lines"), f"{path}.user_brief.discovered_lines", errors)
        selected = _unique_strings(brief.get("selected_lines"), f"{path}.user_brief.selected_lines", errors)
        unavailable = _unique_strings(brief.get("unavailable_lines"), f"{path}.user_brief.unavailable_lines", errors)
        if not discovered or not selected:
            errors.append(f"{path}.user_brief: discovered_lines and selected_lines must be non-empty")
        if expected_not_selected and not unavailable:
            errors.append(f"{path}.user_brief.unavailable_lines: must explain unavailable or non-selected resources")
        for index, line in enumerate([*discovered, *selected, *unavailable]):
            _safe_user_line(line, f"{path}.user_brief.lines[{index}]", errors)
        _safe_user_line(brief.get("execution_line"), f"{path}.user_brief.execution_line", errors)
        if brief.get("content_sha256") != sha256_json(_brief_payload(brief)):
            errors.append(f"{path}.user_brief.content_sha256: must bind the visible brief")

    gate = inventory.get("gate")
    _require_keys(
        gate,
        {
            "status", "authoring_may_start", "verified_before_logic", "authoring_started_at",
            "blocking_resource_ids", "blocking_reasons",
        },
        f"{path}.gate",
        errors,
    )
    scope_reasons = _scope_blocking_reasons(inventory)
    if isinstance(gate, Mapping):
        if gate.get("blocking_resource_ids") != blocking_ids:
            errors.append(f"{path}.gate.blocking_resource_ids: must match required unavailable resources")
        if gate.get("blocking_reasons") != scope_reasons:
            errors.append(f"{path}.gate.blocking_reasons: must match incomplete scans, route, and brief state")
        expected_ready = not blocking_ids and not scope_reasons
        if gate.get("status") != ("ready" if expected_ready else "blocked"):
            errors.append(f"{path}.gate.status: does not match resource readiness")
        if gate.get("authoring_may_start") is not expected_ready:
            errors.append(f"{path}.gate.authoring_may_start: does not match resource readiness")
        if not isinstance(gate.get("verified_before_logic"), bool):
            errors.append(f"{path}.gate.verified_before_logic: must be boolean")
        started_at = None
        if expected_ready:
            started_at = _timestamp(gate.get("authoring_started_at"), f"{path}.gate.authoring_started_at", errors)
        elif gate.get("authoring_started_at") is not None:
            errors.append(f"{path}.gate.authoring_started_at: blocked inventory must use null")
        if created_at and presented_at and started_at and not (created_at <= presented_at <= started_at):
            errors.append(f"{path}: resource scan and user brief must precede authoring start")
        if require_ready and (
            gate.get("status") != "ready"
            or gate.get("authoring_may_start") is not True
            or gate.get("verified_before_logic") is not True
        ):
            errors.append(f"{path}.gate: a validated user-visible resource inventory is required before Logic")

    lock = inventory.get("lock")
    _require_keys(lock, {"algorithm", "digest"}, f"{path}.lock", errors)
    if isinstance(lock, Mapping):
        if lock.get("algorithm") != "sha256":
            errors.append(f"{path}.lock.algorithm: must be sha256")
        unlocked = copy.deepcopy(dict(inventory))
        unlocked.pop("lock", None)
        if lock.get("digest") != sha256_json(unlocked):
            errors.append(f"{path}.lock.digest: mismatch")


def resource_inventory_signature(inventory: Any) -> Any:
    if not isinstance(inventory, Mapping):
        return None
    lock = inventory.get("lock") if isinstance(inventory.get("lock"), Mapping) else {}
    return {
        "inventory_id": inventory.get("inventory_id"),
        "revision": inventory.get("revision"),
        "digest": lock.get("digest"),
    }


def validate_resource_usage(
    usage: Any,
    inventory: Any,
    path: str,
    errors: list[str],
) -> None:
    """Reconcile the initial selected resources with actual five-stage use."""

    _require_keys(
        usage,
        {
            "contract", "inventory_id", "inventory_revision", "inventory_lock_digest", "used_resource_ids",
            "unused_selected_resources", "stage_usage", "user_summary",
        },
        path,
        errors,
    )
    if not isinstance(usage, Mapping) or not isinstance(inventory, Mapping):
        return
    signature = resource_inventory_signature(inventory) or {}
    if usage.get("contract") != USAGE_CONTRACT:
        errors.append(f"{path}.contract: expected {USAGE_CONTRACT}")
    if usage.get("inventory_id") != signature.get("inventory_id"):
        errors.append(f"{path}.inventory_id: must match the pre-Logic inventory")
    if usage.get("inventory_revision") != signature.get("revision"):
        errors.append(f"{path}.inventory_revision: must match the pre-Logic inventory")
    if usage.get("inventory_lock_digest") != signature.get("digest"):
        errors.append(f"{path}.inventory_lock_digest: must match the pre-Logic inventory")
    selected = set(inventory.get("selected_resource_ids", []))
    used_list = _unique_strings(usage.get("used_resource_ids"), f"{path}.used_resource_ids", errors)
    used = set(used_list)
    if not used or not used.issubset(selected):
        errors.append(f"{path}.used_resource_ids: must be a non-empty subset of initially selected resources")
    unused_items = usage.get("unused_selected_resources")
    unused: set[str] = set()
    if not isinstance(unused_items, list):
        errors.append(f"{path}.unused_selected_resources: must be an array")
    else:
        for index, item in enumerate(unused_items):
            ipath = f"{path}.unused_selected_resources[{index}]"
            _require_keys(item, {"resource_id", "reason"}, ipath, errors)
            if not isinstance(item, Mapping):
                continue
            resource_id = item.get("resource_id")
            if resource_id not in selected or resource_id in unused or resource_id in used:
                errors.append(f"{ipath}.resource_id: must name one unused initially selected resource")
            else:
                unused.add(str(resource_id))
            if not nonempty(item.get("reason")):
                errors.append(f"{ipath}.reason: must be non-empty")
    if used | unused != selected:
        errors.append(f"{path}: every initially selected resource must be reconciled as used or unused")

    stage_usage = usage.get("stage_usage")
    seen_stages: list[str] = []
    stage_used: set[str] = set()
    if not isinstance(stage_usage, list):
        errors.append(f"{path}.stage_usage: must be an array")
    else:
        for index, item in enumerate(stage_usage):
            spath = f"{path}.stage_usage[{index}]"
            _require_keys(item, {"stage", "resource_ids", "evidence_refs"}, spath, errors)
            if not isinstance(item, Mapping):
                continue
            stage = item.get("stage")
            if stage not in WORKFLOW_STAGES or stage in seen_stages:
                errors.append(f"{spath}.stage: must be supported and unique")
            else:
                seen_stages.append(str(stage))
            resource_ids = set(_unique_strings(item.get("resource_ids"), f"{spath}.resource_ids", errors))
            evidence_refs = _unique_strings(item.get("evidence_refs"), f"{spath}.evidence_refs", errors)
            if not resource_ids or not evidence_refs or not resource_ids.issubset(used):
                errors.append(f"{spath}: requires used resource IDs and concrete evidence refs")
            stage_used.update(resource_ids)
        if set(seen_stages) != set(WORKFLOW_STAGES):
            errors.append(f"{path}.stage_usage: must cover all five governed stages")
    if stage_used != used:
        errors.append(f"{path}.stage_usage: every used resource must appear in at least one stage")

    summary = usage.get("user_summary")
    _require_keys(summary, {"status", "presented_at", "lines", "content_sha256"}, f"{path}.user_summary", errors)
    if isinstance(summary, Mapping):
        if summary.get("status") != "presented":
            errors.append(f"{path}.user_summary.status: must be presented")
        _timestamp(summary.get("presented_at"), f"{path}.user_summary.presented_at", errors)
        lines = _unique_strings(summary.get("lines"), f"{path}.user_summary.lines", errors)
        if not lines:
            errors.append(f"{path}.user_summary.lines: must summarize actual use")
        for index, line in enumerate(lines):
            _safe_user_line(line, f"{path}.user_summary.lines[{index}]", errors)
        if summary.get("content_sha256") != sha256_json(lines):
            errors.append(f"{path}.user_summary.content_sha256: must bind the visible actual-use summary")


def render_user_brief(inventory: Mapping[str, Any]) -> str:
    brief = inventory.get("user_brief", {})
    lines = ["## Resource inventory", ""]
    summary = inventory.get("summary", {})
    lines.append(
        "- Coverage: "
        f"{summary.get('resource_entry_count', 0)} inventoried entries / "
        f"{summary.get('item_quantity_total', 0)} resource items; "
        f"{summary.get('selected_entry_count', 0)} selected"
    )
    lines.extend(f"- Found: {line}" for line in brief.get("discovered_lines", []))
    lines.extend(f"- Using: {line}" for line in brief.get("selected_lines", []))
    lines.extend(f"- Unavailable/not used: {line}" for line in brief.get("unavailable_lines", []))
    lines.append(f"- Route: {brief.get('execution_line', '')}")
    return "\n".join(lines).strip() + "\n"
