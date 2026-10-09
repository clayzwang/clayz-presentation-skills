#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Prepare visible-only inputs and record actual host reader reviews."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.validators.reader_review import (prepare_packet, record_first, record_review,
                                                read, validate_review, check_art_gate, repair_scope)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--phase", choices=("title", "content", "final", "copy"), required=True)
    for name in ("package", "brief", "directory", "output"):
        prepare.add_argument("--" + name, type=Path, required=True)
    prepare.add_argument("--title-review", type=Path)
    prepare.add_argument("--pptx", type=Path)
    prepare.add_argument("--plan", type=Path)
    prepare.add_argument("--renders", type=Path)
    prepare.add_argument("--unavailable-reason")
    first = commands.add_parser("record-first")
    for name in ("packet", "context", "output"):
        first.add_argument("--" + name, type=Path, required=True)
    first.add_argument("--response", type=Path)
    first.add_argument("--reason")
    reconcile = commands.add_parser("reconcile")
    for name in ("first-read", "dispositions", "output"):
        reconcile.add_argument("--" + name, type=Path, required=True)
    reconcile.add_argument("--comparison", type=Path)
    reconcile.add_argument("--evidence", action="append", type=Path, default=[])
    reconcile.add_argument("--previous-review", action="append", type=Path, default=[], dest="previous_reviews")
    validate = commands.add_parser("validate")
    validate.add_argument("path", type=Path)
    gate = commands.add_parser("check-art-gate")
    gate.add_argument("--package", type=Path, required=True)
    gate.add_argument("--title-review", type=Path, required=True)
    gate.add_argument("--content-review", type=Path, required=True)
    repair = commands.add_parser("repair-scope")
    repair.add_argument("--before", type=Path, required=True)
    repair.add_argument("--after", type=Path, required=True)
    repair.add_argument("--artifact", choices=("copy", "report", "audit-record", "receipt"), default="copy")
    args = vars(parser.parse_args())
    command = args.pop("command")
    try:
        if command == "check-art-gate":
            args["package"] = read(args["package"])
            print(json.dumps(check_art_gate(**args)))
            return 0
        elif command == "repair-scope":
            print(json.dumps(repair_scope(read(args["before"]), read(args["after"]), artifact=args["artifact"])))
            return 0
        elif command == "prepare":
            prepare_packet(**args)
        elif command == "record-first":
            record_first(**args)
        elif command == "reconcile":
            record_review(**args)
        else:
            result = validate_review(read(args["path"]))
            print(json.dumps({"record_valid": True, "assessment": result["assessment"],
                              "independence": result["independence"], "input_scope": result["input_scope"]}))
            return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"record_valid": False, "error": str(exc)}))
        return 1
    print(json.dumps({"status": "recorded", "path": str(args["output"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
