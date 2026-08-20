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
    "references", "renderer", "delivery", "qa",
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

    workflow = require_mapping(config.get("workflow"), "workflow", errors)
    if workflow.get("stages") != EXPECTED_STAGES:
        errors.append(f"workflow.stages: expected {EXPECTED_STAGES}")

    theme = require_mapping(config.get("theme"), "theme", errors)
    colors = require_mapping(theme.get("colors"), "theme.colors", errors)
    for name, value in colors.items():
        if not isinstance(value, str) or not HEX_COLOR.fullmatch(value):
            errors.append(f"theme.colors.{name}: expected #RRGGBB")
    typography = require_mapping(theme.get("typography"), "theme.typography", errors)
    fonts = typography.get("primary_fonts")
    if not isinstance(fonts, list) or not fonts or not all(isinstance(item, str) and item for item in fonts):
        errors.append("theme.typography.primary_fonts: expected non-empty string array")
    for key in ("body_minimum_pt", "minimum_audience_text_pt", "minimum_chart_text_pt"):
        value = typography.get(key)
        if not isinstance(value, (int, float)) or value < 8:
            errors.append(f"theme.typography.{key}: expected number >= 8")
    for key in ("prefer_even_point_sizes", "allow_fractional_point_sizes", "fail_on_missing_primary_font"):
        if not isinstance(typography.get(key), bool):
            errors.append(f"theme.typography.{key}: expected boolean")
    if not isinstance(typography.get("minimum_exception_policy"), str) or not typography.get("minimum_exception_policy"):
        errors.append("theme.typography.minimum_exception_policy: expected non-empty string")

    layout = require_mapping(config.get("layout"), "layout", errors)
    if not isinstance(layout.get("column_count"), int) or layout.get("column_count", 0) < 1:
        errors.append("layout.column_count: expected positive integer")

    references = require_mapping(config.get("references"), "references", errors)
    if references.get("provider") != "filesystem":
        errors.append("references.provider: public default must be filesystem")
    roots = references.get("roots")
    if not isinstance(roots, list) or not roots or not all(isinstance(item, str) and item for item in roots):
        errors.append("references.roots: expected non-empty relative-path array")
        roots = []
    path_values = [*roots, references.get("registry"), references.get("admission_registry")]
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

    renderer = require_mapping(config.get("renderer"), "renderer", errors)
    caps = renderer.get("required_capabilities")
    if not isinstance(caps, list) or not caps:
        errors.append("renderer.required_capabilities: expected non-empty array")

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
