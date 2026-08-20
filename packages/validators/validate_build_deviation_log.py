#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate the subordinate build-observation and deviation log."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "1.1"
ENVIRONMENT_PRECEDENCE = "written-pptx-and-render-over-in-memory-state"
SCORING_POLICY = "evidence-not-score"
PHASES = {"initial-render", "targeted-repair", "final-reopen"}
TRIGGERS = {
    "initial-build", "machine-failure", "render-drift", "compatibility-drift",
    "font-drift", "size-drift", "authorized-technical-adjustment", "final-verification",
}
OPERATIONS = {
    "reposition-object", "resize-object", "reorder-layer", "route-connector",
    "adjust-crop", "replace-approved-asset", "repair-native-chart",
    "repair-native-table", "repair-font-encoding", "repair-compatibility",
    "deduplicate-media", "optimize-raster", "remove-duplicate-object",
    "restore-master-inheritance",
}
ACTION_STATUS = {"pass", "fail", "skipped"}
OUTCOMES = {"accept", "targeted-repair", "challenge-upstream", "continue-known-risk"}
OWNERS = {"output-build", "output-qa", "art-direction", "copy", "logic", "system"}
FINAL_STATUS = {"pass", "known-risk", "incomplete"}
RETURN_STATUS = {"implemented", "challenged", "user-approved", "known-risk", "not-applicable"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[A-Z][A-Z0-9_-]*$")


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_keys(obj: Any, keys: set[str], path: str, errors: list[str]) -> None:
    if not isinstance(obj, dict):
        errors.append(f"{path}: must be an object")
        return
    missing = sorted(keys - set(obj))
    if missing:
        errors.append(f"{path}: missing keys {missing}")


def string_list(value: Any, *, allow_empty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(nonempty(item) for item in value)
    )


def validate(
    package: Any,
    plan: Any,
    log: Any,
    package_path: Path,
    plan_path: Path,
    pptx_path: Path | None,
) -> list[str]:
    errors: list[str] = []
    require_keys(log, {
        "contract_version", "artifact_role", "package_id", "package_version",
        "art_direction_plan_contract_version", "source_bindings",
        "environment_precedence", "scoring_policy", "cycles", "deviations",
        "challenges", "final_status",
    }, "$log", errors)
    if not all(isinstance(item, dict) for item in (package, plan, log)):
        return errors
    if log.get("contract_version") != CONTRACT_VERSION:
        errors.append(f"log.contract_version: expected {CONTRACT_VERSION}")
    if log.get("artifact_role") != "subordinate-operational-evidence":
        errors.append("log.artifact_role: must be subordinate-operational-evidence")
    if log.get("package_id") != package.get("package_id"):
        errors.append("log.package_id: must match package")
    if log.get("package_version") != package.get("version"):
        errors.append("log.package_version: must match package")
    if log.get("art_direction_plan_contract_version") != plan.get("contract_version"):
        errors.append("log.art_direction_plan_contract_version: must match plan")
    if log.get("environment_precedence") != ENVIRONMENT_PRECEDENCE:
        errors.append(f"log.environment_precedence: expected {ENVIRONMENT_PRECEDENCE}")
    if log.get("scoring_policy") != SCORING_POLICY:
        errors.append(f"log.scoring_policy: expected {SCORING_POLICY}")

    bindings = log.get("source_bindings")
    require_keys(bindings, {"package_sha256", "art_direction_plan_sha256", "pptx_sha256"}, "log.source_bindings", errors)
    if isinstance(bindings, dict):
        expected = {
            "package_sha256": sha256(package_path),
            "art_direction_plan_sha256": sha256(plan_path),
        }
        if pptx_path is not None:
            expected["pptx_sha256"] = sha256(pptx_path)
        for key in ("package_sha256", "art_direction_plan_sha256", "pptx_sha256"):
            value = bindings.get(key)
            if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
                errors.append(f"log.source_bindings.{key}: must be a lowercase SHA-256")
            elif key in expected and value != expected[key]:
                errors.append(f"log.source_bindings.{key}: hash does not match the supplied file")

    slide_ids = {
        item.get("slide_id")
        for item in package.get("logic_layer", {}).get("slides", [])
        if isinstance(item, dict) and nonempty(item.get("slide_id"))
    }
    cycles = log.get("cycles")
    if not isinstance(cycles, list) or not cycles:
        errors.append("log.cycles: must be a non-empty array")
        cycles = []
    cycle_ids: set[str] = set()
    action_ids: set[str] = set()
    repair_refs: list[tuple[str, str]] = []
    final_reopen_indexes: list[int] = []
    targeted_cycle_ids: set[str] = set()

    for index, cycle in enumerate(cycles):
        path = f"log.cycles[{index}]"
        require_keys(cycle, {
            "cycle_id", "phase", "trigger", "repair_of", "scope", "actions",
            "observation", "decision",
        }, path, errors)
        if not isinstance(cycle, dict):
            continue
        cycle_id = cycle.get("cycle_id")
        if not nonempty(cycle_id) or not ID_RE.fullmatch(cycle_id) or cycle_id in cycle_ids:
            errors.append(f"{path}.cycle_id: must be a unique stable uppercase id")
        else:
            cycle_ids.add(cycle_id)
        phase = cycle.get("phase")
        if phase not in PHASES:
            errors.append(f"{path}.phase: invalid value")
        if cycle.get("trigger") not in TRIGGERS:
            errors.append(f"{path}.trigger: invalid value")
        if phase == "final-reopen":
            final_reopen_indexes.append(index)
        repair_of = cycle.get("repair_of")
        if phase == "targeted-repair":
            targeted_cycle_ids.add(cycle_id)
            if not nonempty(repair_of):
                errors.append(f"{path}.repair_of: targeted repair must name the prior cycle")
            else:
                repair_refs.append((cycle_id, repair_of))
        elif repair_of is not None:
            errors.append(f"{path}.repair_of: only targeted-repair may use a repair reference")

        scope = cycle.get("scope")
        require_keys(scope, {"slide_ids", "target_ids"}, f"{path}.scope", errors)
        if isinstance(scope, dict):
            cycle_slides = scope.get("slide_ids")
            if not string_list(cycle_slides):
                errors.append(f"{path}.scope.slide_ids: must contain at least one slide id")
            elif any(item not in slide_ids for item in cycle_slides):
                errors.append(f"{path}.scope.slide_ids: contains an unknown package slide")
            if not string_list(scope.get("target_ids"), allow_empty=phase != "targeted-repair"):
                errors.append(f"{path}.scope.target_ids: invalid target list")

        actions = cycle.get("actions")
        if not isinstance(actions, list):
            errors.append(f"{path}.actions: must be an array")
            actions = []
        if phase == "targeted-repair" and not actions:
            errors.append(f"{path}.actions: targeted repair requires at least one action")
        for a_index, action in enumerate(actions):
            a_path = f"{path}.actions[{a_index}]"
            require_keys(action, {
                "action_id", "operation", "slide_id", "target_ids", "precondition",
                "authority", "changes_approved_content", "changes_art_direction",
                "status", "evidence",
            }, a_path, errors)
            if not isinstance(action, dict):
                continue
            action_id = action.get("action_id")
            if not nonempty(action_id) or not ID_RE.fullmatch(action_id) or action_id in action_ids:
                errors.append(f"{a_path}.action_id: must be a unique stable uppercase id")
            else:
                action_ids.add(action_id)
            if action.get("operation") not in OPERATIONS:
                errors.append(f"{a_path}.operation: outside the controlled technical vocabulary")
            if action.get("slide_id") not in slide_ids:
                errors.append(f"{a_path}.slide_id: unknown package slide")
            if not string_list(action.get("target_ids")):
                errors.append(f"{a_path}.target_ids: must contain stable target ids")
            if not nonempty(action.get("precondition")):
                errors.append(f"{a_path}.precondition: must be non-empty")
            if action.get("authority") != "output-technical":
                errors.append(f"{a_path}.authority: must be output-technical")
            if action.get("changes_approved_content") is not False:
                errors.append(f"{a_path}.changes_approved_content: must be false; challenge upstream instead")
            if action.get("changes_art_direction") is not False:
                errors.append(f"{a_path}.changes_art_direction: must be false; challenge upstream instead")
            if action.get("status") not in ACTION_STATUS:
                errors.append(f"{a_path}.status: invalid value")
            if not nonempty(action.get("evidence")):
                errors.append(f"{a_path}.evidence: must be non-empty")

        observation = cycle.get("observation")
        require_keys(observation, {
            "machine_evidence", "render_evidence", "model_interpretation", "affected_slides",
        }, f"{path}.observation", errors)
        if isinstance(observation, dict):
            for key in ("machine_evidence", "render_evidence"):
                if not string_list(observation.get(key)):
                    errors.append(f"{path}.observation.{key}: must contain concrete evidence")
            if not nonempty(observation.get("model_interpretation")):
                errors.append(f"{path}.observation.model_interpretation: must be non-empty")
            affected = observation.get("affected_slides")
            if not string_list(affected) or any(item not in slide_ids for item in affected):
                errors.append(f"{path}.observation.affected_slides: must contain known slides")

        decision = cycle.get("decision")
        require_keys(decision, {"outcome", "owner_layer", "reason"}, f"{path}.decision", errors)
        if isinstance(decision, dict):
            if decision.get("outcome") not in OUTCOMES:
                errors.append(f"{path}.decision.outcome: invalid value")
            if decision.get("owner_layer") not in OWNERS:
                errors.append(f"{path}.decision.owner_layer: invalid value")
            if not nonempty(decision.get("reason")):
                errors.append(f"{path}.decision.reason: must be non-empty")
            failed = any(isinstance(a, dict) and a.get("status") == "fail" for a in actions)
            if failed and decision.get("outcome") not in {"targeted-repair", "challenge-upstream", "continue-known-risk"}:
                errors.append(f"{path}.decision.outcome: a failed action cannot be accepted")

    for cycle_id, repair_of in repair_refs:
        if repair_of not in cycle_ids:
            errors.append(f"log.cycles[{cycle_id}].repair_of: unknown cycle {repair_of}")
        if repair_of == cycle_id:
            errors.append(f"log.cycles[{cycle_id}].repair_of: cannot reference itself")
    repair_targets = {repair_of for _, repair_of in repair_refs}
    for cycle in cycles:
        if isinstance(cycle, dict) and cycle.get("decision", {}).get("outcome") == "targeted-repair":
            if cycle.get("cycle_id") not in repair_targets:
                errors.append(f"log.cycles[{cycle.get('cycle_id')}]: targeted-repair decision lacks a following repair cycle")

    if not final_reopen_indexes or final_reopen_indexes[-1] != len(cycles) - 1:
        errors.append("log.cycles: the last cycle must be final-reopen")

    deviations = log.get("deviations")
    if not isinstance(deviations, list):
        errors.append("log.deviations: must be an array")
        deviations = []
    deviation_ids: set[str] = set()
    for index, item in enumerate(deviations):
        path = f"log.deviations[{index}]"
        require_keys(item, {
            "deviation_id", "slide_id", "planned", "actual", "reason",
            "changes_art_direction", "approval_basis", "return_status",
        }, path, errors)
        if not isinstance(item, dict):
            continue
        deviation_id = item.get("deviation_id")
        if not nonempty(deviation_id) or deviation_id in deviation_ids:
            errors.append(f"{path}.deviation_id: must be non-empty and unique")
        else:
            deviation_ids.add(deviation_id)
        if item.get("slide_id") not in slide_ids:
            errors.append(f"{path}.slide_id: unknown package slide")
        for key in ("planned", "actual", "reason", "approval_basis"):
            if not nonempty(item.get(key)):
                errors.append(f"{path}.{key}: must be non-empty")
        if not isinstance(item.get("changes_art_direction"), bool):
            errors.append(f"{path}.changes_art_direction: must be boolean")
        if item.get("changes_art_direction") is True and item.get("return_status") != "user-approved":
            errors.append(f"{path}: an Art Direction change requires user-approved status")
        if item.get("return_status") not in RETURN_STATUS:
            errors.append(f"{path}.return_status: invalid value")

    challenges = log.get("challenges")
    if not isinstance(challenges, list):
        errors.append("log.challenges: must be an array")
        challenges = []
    for index, item in enumerate(challenges):
        path = f"log.challenges[{index}]"
        require_keys(item, {
            "challenge_id", "owner_layer", "challenged_baseline", "evidence",
            "impact", "alternative", "user_decision",
        }, path, errors)
        if not isinstance(item, dict):
            continue
        if item.get("owner_layer") not in OWNERS - {"output-build", "output-qa"}:
            errors.append(f"{path}.owner_layer: challenge must return upstream or to system")
        for key in ("challenge_id", "challenged_baseline", "evidence", "impact", "alternative", "user_decision"):
            if not nonempty(item.get(key)):
                errors.append(f"{path}.{key}: must be non-empty")

    final_status = log.get("final_status")
    if final_status not in FINAL_STATUS:
        errors.append("log.final_status: invalid value")
    if final_status == "pass":
        if challenges and any(item.get("user_decision") == "pending" for item in challenges if isinstance(item, dict)):
            errors.append("log.final_status: cannot pass with pending challenges")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("log", type=Path)
    parser.add_argument("--pptx", type=Path)
    args = parser.parse_args()
    try:
        package = json.loads(args.package.read_text(encoding="utf-8"))
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        log = json.loads(args.log.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate(package, plan, log, args.package, args.plan, args.pptx)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: build deviation and observation log is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
