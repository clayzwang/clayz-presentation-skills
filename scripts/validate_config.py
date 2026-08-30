#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate the centralized Clayz Presentation Skills configuration."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
REQUIRED_TOP_LEVEL = {
    "identity", "workflow", "locale", "theme", "layout",
    "references", "renderer", "runtime", "delivery", "qa",
}
EXPECTED_STAGES = ["logic", "copy", "art-direction", "output", "supervisor"]
EXPECTED_LEARNING_STAGES = ["logic", "copy", "art-direction", "output"]


def require_mapping(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected object")
        return {}
    return value


def validate(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL - set(config))
    if missing:
        errors.append(f"root: missing {', '.join(missing)}")

    identity = require_mapping(config.get("identity"), "identity", errors)
    for key in ("project", "version", "creator", "brand", "namespace", "attribution"):
        if not identity.get(key):
            errors.append(f"identity.{key}: required")
    attribution = require_mapping(identity.get("attribution"), "identity.attribution", errors)
    for key in ("creator", "brand"):
        if identity.get(key) != "clayz":
            errors.append(f"identity.{key}: public distribution must use clayz")
    if identity.get("namespace") != "io.clayz.presentation":
        errors.append("identity.namespace: public distribution must use io.clayz.presentation")
    if attribution.get("mode") not in {"metadata", "none"}:
        errors.append("identity.attribution.mode: expected metadata or none")
    if attribution.get("visible_mark") is not False:
        errors.append("identity.attribution.visible_mark: public default must be false")
    custom = require_mapping(attribution.get("custom_properties"), "identity.attribution.custom_properties", errors)
    if attribution.get("mode") == "metadata":
        for key in ("ClayzGenerator", "ClayzVersion", "ClayzOriginalArchitecture", "ClayzBrand", "ClayzNamespace"):
            if not custom.get(key):
                errors.append(f"identity.attribution.custom_properties.{key}: required")

    theme = require_mapping(config.get("theme"), "theme", errors)
    colors = require_mapping(theme.get("colors"), "theme.colors", errors)
    for name, value in colors.items():
        if not isinstance(value, str) or not HEX_COLOR.fullmatch(value):
            errors.append(f"theme.colors.{name}: expected #RRGGBB")
    typography = require_mapping(theme.get("typography"), "theme.typography", errors)
    fonts = typography.get("primary_fonts")
    if not isinstance(fonts, list) or not fonts or not all(isinstance(item, str) and item.strip() for item in fonts):
        errors.append("theme.typography.primary_fonts: expected non-empty string array")
        fonts = []
    elif len({item.casefold() for item in fonts}) != len(fonts):
        errors.append("theme.typography.primary_fonts: expected case-insensitively unique font families")
    for key in ("body_minimum_pt", "minimum_audience_text_pt", "minimum_chart_text_pt"):
        value = typography.get(key)
        if not isinstance(value, (int, float)) or value < 8:
            errors.append(f"theme.typography.{key}: expected number >= 8")
    for key in ("prefer_even_point_sizes", "allow_fractional_point_sizes", "fail_on_missing_primary_font"):
        if not isinstance(typography.get(key), bool):
            errors.append(f"theme.typography.{key}: expected boolean")
    if not isinstance(typography.get("minimum_exception_policy"), str) or not typography.get("minimum_exception_policy"):
        errors.append("theme.typography.minimum_exception_policy: expected non-empty string")
    font_validation = typography.get("font_validation")
    if font_validation is not None:
        font_validation = require_mapping(font_validation, "theme.typography.font_validation", errors)
        expected_font_validation = {
            "contract_version": "1.0",
            "mode": "preserve-name-defer-native",
            "preserve_requested_font_names": True,
            "silent_substitution_forbidden": True,
            "cloud_render_authority": "diagnostic-only",
            "cloud_pdf_pixel_equivalence": "not-required-when-deferred-font-missing",
            "native_reopen_required_for_final_font_acceptance": True,
            "missing_deferred_font_status": "font-validation-pending",
        }
        for key, expected in expected_font_validation.items():
            if font_validation.get(key) != expected:
                errors.append(f"theme.typography.font_validation.{key}: expected {expected!r}")

        identities = font_validation.get("deferred_font_identities")
        if not isinstance(identities, list) or not identities:
            errors.append(
                "theme.typography.font_validation.deferred_font_identities: "
                "expected non-empty identity array"
            )
            identities = []
        primary_names = {item.casefold() for item in fonts}
        claimed_names: dict[str, str] = {}
        for index, value in enumerate(identities):
            path = f"theme.typography.font_validation.deferred_font_identities[{index}]"
            identity = require_mapping(value, path, errors)
            canonical = identity.get("canonical_family")
            aliases = identity.get("aliases")
            pptx_family = identity.get("pptx_family")
            if not isinstance(canonical, str) or not canonical.strip():
                errors.append(f"{path}.canonical_family: expected non-empty string")
                canonical = ""
            if not isinstance(aliases, list) or not all(
                isinstance(alias, str) and alias.strip() for alias in aliases
            ):
                errors.append(f"{path}.aliases: expected string array")
                aliases = []
            elif len({alias.casefold() for alias in aliases}) != len(aliases):
                errors.append(f"{path}.aliases: expected case-insensitively unique names")
            if not isinstance(pptx_family, str) or not pptx_family.strip():
                errors.append(f"{path}.pptx_family: expected non-empty string")
                pptx_family = ""

            identity_names = [canonical, *aliases]
            identity_keys = {name.casefold() for name in identity_names if name}
            if canonical and canonical.casefold() not in primary_names:
                errors.append(f"{path}.canonical_family: must appear once in primary_fonts")
            for alias in aliases:
                if alias.casefold() in primary_names:
                    errors.append(
                        f"{path}.aliases: alias {alias!r} must not appear in primary_fonts as a fallback"
                    )
            if pptx_family and pptx_family.casefold() not in identity_keys:
                errors.append(f"{path}.pptx_family: must equal the canonical family or one of its aliases")
            for name in identity_names:
                if not name:
                    continue
                key = name.casefold()
                if key in claimed_names:
                    errors.append(
                        f"{path}: font name {name!r} collides with {claimed_names[key]}"
                    )
                else:
                    claimed_names[key] = path

    layout = require_mapping(config.get("layout"), "layout", errors)
    if not isinstance(layout.get("column_count"), int) or layout.get("column_count", 0) < 1:
        errors.append("layout.column_count: expected positive integer")

    references = require_mapping(config.get("references"), "references", errors)
    if references.get("provider_contract") != "packages/contracts/provider-manifest.schema.json":
        errors.append("references.provider_contract: expected the shared Provider manifest schema")
    if references.get("public_provider_manifest") != "catalog/provider-manifest.json":
        errors.append("references.public_provider_manifest: expected the bundled public Provider manifest")
    if references.get("public_index") != "catalog/records.jsonl":
        errors.append("references.public_index: expected the canonical public index")
    if references.get("local_library_adapter") != "filesystem":
        errors.append("references.local_library_adapter: public default must be filesystem")
    roots = references.get("roots")
    if not isinstance(roots, list) or not roots or not all(isinstance(item, str) and item for item in roots):
        errors.append("references.roots: expected non-empty relative-path array")
        roots = []
    path_values = [
        references.get("provider_contract"), references.get("public_provider_manifest"), references.get("public_index"),
        *roots, references.get("registry"), references.get("admission_registry"),
    ]
    index = require_mapping(references.get("index"), "references.index", errors)
    path_values.append(index.get("path"))
    learning = require_mapping(references.get("learning"), "references.learning", errors)
    path_values.extend([learning.get("root"), learning.get("contract")])
    for value in path_values:
        if not isinstance(value, str) or not value or Path(value).is_absolute() or ".." in Path(value).parts:
            errors.append(f"references: expected safe relative path, found {value!r}")
    if learning.get("stages") != EXPECTED_LEARNING_STAGES:
        errors.append(f"references.learning.stages: expected {EXPECTED_LEARNING_STAGES}")
    if learning.get("writeback_mode") != "append-observation-only":
        errors.append("references.learning.writeback_mode: expected append-observation-only")
    if learning.get("auto_promote") is not False:
        errors.append("references.learning.auto_promote: public default must be false")
    if learning.get("contract") != "packages/contracts/knowledge-learning.md":
        errors.append("references.learning.contract: expected shared knowledge contract")
    if references.get("require_human_admission") is not True:
        errors.append("references.require_human_admission: public default must be true")
    if not isinstance(references.get("allow_external_search"), bool):
        errors.append("references.allow_external_search: expected boolean")
    if not isinstance(references.get("maximum_unique_examples_per_deck"), int) or references.get("maximum_unique_examples_per_deck", 0) < 1:
        errors.append("references.maximum_unique_examples_per_deck: expected positive integer")
    if index.get("engine") != "bm25-lexical":
        errors.append("references.index.engine: public default must be bm25-lexical")
    if index.get("role") != "derived-local-search-cache":
        errors.append("references.index.role: must distinguish the local cache from canonical Provider indexes")
    for key in ("maximum_results", "physical_neighbor_expansion", "semantic_neighbor_expansion"):
        if not isinstance(index.get(key), int) or index.get(key, -1) < (1 if key == "maximum_results" else 0):
            errors.append(f"references.index.{key}: invalid retrieval limit")

    workflow = require_mapping(config.get("workflow"), "workflow", errors)
    if workflow.get("contract_version") != "3.1-open":
        errors.append("workflow.contract_version: expected 3.1-open")
    if workflow.get("stages") != EXPECTED_STAGES:
        errors.append(f"workflow.stages: expected {EXPECTED_STAGES}")
    if workflow.get("execution_ledger_contract") != "io.clayz.presentation.execution-ledger/1.0":
        errors.append("workflow.execution_ledger_contract: unsupported contract")
    if not isinstance(workflow.get("maximum_technical_cycles"), int) or not 1 <= workflow.get("maximum_technical_cycles", 0) <= 10:
        errors.append("workflow.maximum_technical_cycles: expected integer from 1 to 10")

    runtime = require_mapping(config.get("runtime"), "runtime", errors)
    if runtime.get("contract_version") != "1.2":
        errors.append("runtime.contract_version: expected 1.2")
    if runtime.get("preflight_script") != "scripts/runtime_preflight.py":
        errors.append("runtime.preflight_script: expected scripts/runtime_preflight.py")
    if runtime.get("model_profiles") != ["A", "B", "C", "D"]:
        errors.append("runtime.model_profiles: expected capability profiles A, B, C, D")
    if runtime.get("classification_basis") != "capabilities-not-model-brands":
        errors.append("runtime.classification_basis: must remain brand-neutral")
    if runtime.get("route_policy") != "scan-once-lock-for-run":
        errors.append("runtime.route_policy: expected scan-once-lock-for-run")
    if runtime.get("fallback_policy") != "restart-from-preflight":
        errors.append("runtime.fallback_policy: expected restart-from-preflight")
    if runtime.get("platform_packs") != ["common", "windows", "macos", "linux"]:
        errors.append("runtime.platform_packs: expected common plus three operating-system packs")
    if runtime.get("pdf_support") != "lazy-optional":
        errors.append("runtime.pdf_support: PDF must remain lazy and optional")
    budgets = require_mapping(runtime.get("budgets"), "runtime.budgets", errors)
    expected_budgets = {
        "maximum_capability_scans": 1,
        "maximum_source_collection_rounds": 1,
        "maximum_office_processes": 1,
        "maximum_repair_cycles": 1,
        "maximum_route_switches": 0,
        "maximum_fallback_restarts": 1,
    }
    for key, expected in expected_budgets.items():
        if budgets.get(key) != expected:
            errors.append(f"runtime.budgets.{key}: expected {expected}")
    for key in ("maximum_authoring_writes", "maximum_full_deck_renders"):
        if not isinstance(budgets.get(key), int) or not 1 <= budgets.get(key, 0) <= 2:
            errors.append(f"runtime.budgets.{key}: expected integer from 1 to 2")

    renderer = require_mapping(config.get("renderer"), "renderer", errors)
    caps = renderer.get("required_capabilities")
    if not isinstance(caps, list) or not caps:
        errors.append("renderer.required_capabilities: expected non-empty array")
    optional_caps = renderer.get("optional_capabilities")
    if not isinstance(optional_caps, list) or len(optional_caps) != len(set(optional_caps)):
        errors.append("renderer.optional_capabilities: expected unique string array")
    elif any(not isinstance(item, str) or not item for item in optional_caps):
        errors.append("renderer.optional_capabilities: expected unique string array")
    adapters = require_mapping(renderer.get("adapters"), "renderer.adapters", errors)
    pptxgenjs = require_mapping(adapters.get("pptxgenjs"), "renderer.adapters.pptxgenjs", errors)
    if pptxgenjs.get("path") != "packages/adapters/pptxgenjs/render.mjs":
        errors.append("renderer.adapters.pptxgenjs: expected the public adapter path")
    if pptxgenjs.get("enabled") is not False or pptxgenjs.get("security_status") != "blocked-unpatched-transitive-dependency":
        errors.append("renderer.adapters.pptxgenjs: public v0.2.0 must fail closed on the unpatched dependency")
    if pptxgenjs.get("blocked_advisories") != ["GHSA-w3rx-r6r6-pgpr", "GHSA-5p2g-fcmc-qvqq"]:
        errors.append("renderer.adapters.pptxgenjs.blocked_advisories: expected both reviewed advisories")
    if renderer.get("baseline_authoring_backend") != "python-pptx":
        errors.append("renderer.baseline_authoring_backend: expected python-pptx")
    if renderer.get("baseline_adapter") != "packages/adapters/python_pptx/render.py":
        errors.append("renderer.baseline_adapter: expected public python-pptx adapter path")

    delivery = require_mapping(config.get("delivery"), "delivery", errors)
    profiles = require_mapping(delivery.get("profiles"), "delivery.profiles", errors)
    if delivery.get("default_profile") not in profiles:
        errors.append("delivery.default_profile: missing matching profile")
    if delivery.get("preserve_editability") is not True:
        errors.append("delivery.preserve_editability: public default must be true")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", nargs="?", default="config/default.json")
    args = parser.parse_args()
    path = Path(args.config)
    try:
        raw = path.read_bytes()
        config = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    if not isinstance(config, dict):
        print("config error: root must be an object", file=sys.stderr)
        return 2
    errors = validate(config)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "sha256": hashlib.sha256(raw).hexdigest(), "path": str(path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
