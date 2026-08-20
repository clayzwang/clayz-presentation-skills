#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate public attribution, reviewed revisions, and adoption boundaries."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


COMMIT = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_SOURCES = {"pptagent", "deeppresenter", "pom", "vascar", "postero", "pptxgenjs"}


def validate(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    project = document.get("project")
    if not isinstance(project, dict) or project.get("original_architecture") != "clayz" or project.get("brand") != "clayz":
        errors.append("project: clayz architecture and brand are required")

    boundary = document.get("public_growth_boundary")
    if not isinstance(boundary, dict):
        errors.append("public_growth_boundary: object is required")
    else:
        for field in ("bundled_real_cases", "bundled_taste_corpus", "bundled_personal_preferences", "automatic_aesthetic_truth"):
            if boundary.get(field) is not False:
                errors.append(f"public_growth_boundary.{field}: must be false")

    excluded = document.get("deliberately_excluded")
    if not isinstance(excluded, list) or not excluded or not all(isinstance(item, str) and item for item in excluded):
        errors.append("deliberately_excluded: non-empty string array is required")

    sources = document.get("sources")
    if not isinstance(sources, list):
        return [*errors, "sources: array is required"]
    identifiers: set[str] = set()
    for index, source in enumerate(sources, 1):
        label = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{label}: object is required")
            continue
        identifier = source.get("id")
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"{label}.id: non-empty string is required")
        elif identifier in identifiers:
            errors.append(f"{label}.id: duplicate {identifier}")
        else:
            identifiers.add(identifier)
        for field in ("usage_type", "upstream_license", "pinned_version", "reviewed_on", "influenced_components", "redistributed_files", "note"):
            if field not in source:
                errors.append(f"{label}.{field}: required")
        if source.get("redistributed_files") != []:
            errors.append(f"{label}.redistributed_files: public package must redistribute no upstream files")
        if not isinstance(source.get("influenced_components"), list) or not source.get("influenced_components"):
            errors.append(f"{label}.influenced_components: non-empty array is required")
        if "Thank you" not in str(source.get("note", "")):
            errors.append(f"{label}.note: explicit gratitude is required")
        if identifier in {"pptagent", "deeppresenter", "pom"} and not COMMIT.fullmatch(str(source.get("pinned_version", ""))):
            errors.append(f"{label}.pinned_version: reviewed 40-character commit is required")
        if identifier == "postero":
            if source.get("usage_type") != "paper-citation-only" or source.get("upstream_license") != "no-repository-license-observed":
                errors.append(f"{label}: PosterO must remain paper-citation-only")
        if identifier == "pptxgenjs":
            if source.get("usage_type") != "optional-public-api-integration":
                errors.append(f"{label}: PptxGenJS must remain an optional public-API integration")
            if not COMMIT.fullmatch(str(source.get("pinned_commit", ""))):
                errors.append(f"{label}.pinned_commit: reviewed 40-character commit is required")
    if identifiers != REQUIRED_SOURCES:
        errors.append(f"sources: expected exactly {sorted(REQUIRED_SOURCES)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", default="provenance/manifest.yaml")
    args = parser.parse_args()
    try:
        document = yaml.safe_load(Path(args.manifest).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2
    errors = validate(document) if isinstance(document, dict) else ["manifest root must be an object"]
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
