#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Finalize and validate one hash-bound task acceptance contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = ROOT / "packages" / "validators"
if str(VALIDATORS) not in sys.path:
    sys.path.insert(0, str(VALIDATORS))

from acceptance_contract import acceptance_contract_digest, validate_acceptance_contract  # noqa: E402
from task_commitments import enrich_task_acceptance  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "default.json")
    parser.add_argument("--origin-map", type=Path)
    parser.add_argument("--brief-output", type=Path)
    args = parser.parse_args()
    try:
        value = json.loads(args.draft.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2
    if not isinstance(value, dict):
        print("ERROR: acceptance draft must be an object")
        return 2
    requirements = value.get("requirements", [])
    if not isinstance(requirements, list):
        print("ERROR: acceptance draft requirements must be an array")
        return 2
    missing_classification = [
        str(item.get("requirement_id", index))
        for index, item in enumerate(requirements)
        if isinstance(item, dict) and "classification" not in item
    ]
    if missing_classification:
        print(
            "ERROR: acceptance requirements missing classification (hard or soft); "
            "Supervisor must classify before finalization: " + ", ".join(missing_classification)
        )
        return 1
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        origin_map = json.loads(args.origin_map.read_text(encoding="utf-8")) if args.origin_map else None
        value, brief = enrich_task_acceptance(value, config, origin_map)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"ERROR: cannot enrich task commitments: {exc}")
        return 2
    value["contract_sha256"] = acceptance_contract_digest(value)
    errors: list[str] = []
    validate_acceptance_contract(value, "acceptance_contract", errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    brief_path = args.brief_output
    if brief_path is not None:
        brief_path.parent.mkdir(parents=True, exist_ok=True)
        brief_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"ok": True, "contract_sha256": value["contract_sha256"], "output": args.output.as_posix(), "brief_output": brief_path.as_posix() if brief_path else None}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
