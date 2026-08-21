#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate the synthetic Art Direction regression suite and its coverage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_CASES = {
    "ROUTE-MANAGEMENT-REPORT": "material-route",
    "ROUTE-BUSINESS-ANALYSIS": "material-route",
    "ROUTE-STRATEGY-DEPLOYMENT": "material-route",
    "ROUTE-SALES-TRAINING": "material-route",
    "SERIES-STABLE-BACKBONE": "cross-slide",
    "SERIES-CONTROLLED-VARIATION": "cross-slide",
    "SERIES-INTENTIONAL-BREAK": "cross-slide",
    "NONSERIES-SILHOUETTE-COLLISION": "cross-slide",
    "CAPABILITY-CONTENT-AWARE-CANVAS": "capability",
    "CAPABILITY-ASSET-TEMPLATE-GRAMMAR": "capability",
}
REQUIRED_FIELDS = {
    "case_id", "category", "source_kind", "license", "task", "risk",
    "rejected_pattern", "target_backbone", "required_signals", "forbidden_signals",
}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def valid_signals(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and len(value) == len(set(value))
        and all(nonempty(item) for item in value)
    )


def validate(document: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["suite root must be an object"]
    if document.get("suite_version") != "1.0":
        errors.append("suite_version: expected 1.0")
    if not nonempty(document.get("purpose")):
        errors.append("purpose: must be non-empty")
    cases = document.get("cases")
    if not isinstance(cases, list):
        return [*errors, "cases: must be an array"]
    seen: dict[str, str] = {}
    for index, case in enumerate(cases):
        path = f"cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{path}: must be an object")
            continue
        missing = sorted(REQUIRED_FIELDS - set(case))
        if missing:
            errors.append(f"{path}: missing keys {missing}")
        case_id = case.get("case_id")
        category = case.get("category")
        if not nonempty(case_id):
            errors.append(f"{path}.case_id: must be non-empty")
        elif case_id in seen:
            errors.append(f"{path}.case_id: duplicate {case_id}")
        else:
            seen[case_id] = category
        if category not in {"material-route", "cross-slide", "capability"}:
            errors.append(f"{path}.category: invalid value")
        if case.get("source_kind") != "synthetic" or case.get("license") != "Apache-2.0":
            errors.append(f"{path}: fixtures must be synthetic Apache-2.0 material")
        for field in ("task", "risk", "rejected_pattern", "target_backbone"):
            if not nonempty(case.get(field)):
                errors.append(f"{path}.{field}: must be non-empty")
        if case.get("rejected_pattern") == case.get("target_backbone"):
            errors.append(f"{path}: rejected and target patterns must differ")
        for field in ("required_signals", "forbidden_signals"):
            if not valid_signals(case.get(field)):
                errors.append(f"{path}.{field}: must be a unique non-empty string array")
    if seen != REQUIRED_CASES:
        errors.append(f"cases: expected exact coverage {sorted(REQUIRED_CASES)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", nargs="?", default="tests/fixtures/visual-regression-suite.json")
    args = parser.parse_args()
    try:
        document = json.loads(Path(args.suite).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2
    errors = validate(document)
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
