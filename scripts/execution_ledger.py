#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Create and append a bounded, evidence-grounded presentation execution ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


STATUSES = {"started", "succeeded", "failed", "partial", "blocked"}
STAGES = {"logic", "copy", "art-direction", "output", "supervisor", "runtime"}


class LedgerError(ValueError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def file_binding(path: Path) -> dict[str, str]:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path), "sha256": digest.hexdigest()}


def initialize(run_id: str, maximum_cycles: int) -> dict[str, Any]:
    if not run_id:
        raise LedgerError("run_id must not be empty")
    if maximum_cycles < 1:
        raise LedgerError("maximum_cycles must be positive")
    return {
        "contract": "io.clayz.presentation.execution-ledger/1.0",
        "run_id": run_id,
        "created_at": now(),
        "maximum_cycles": maximum_cycles,
        "events": [],
        "final_status": "open",
    }


def configured_maximum_cycles(path: Path) -> int:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
        value = config["workflow"]["maximum_technical_cycles"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise LedgerError(f"invalid execution-ledger configuration: {exc}") from exc
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 10:
        raise LedgerError("configured maximum_technical_cycles must be an integer from 1 to 10")
    return value


def read(path: Path) -> dict[str, Any]:
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LedgerError(str(exc)) from exc
    if ledger.get("contract") != "io.clayz.presentation.execution-ledger/1.0":
        raise LedgerError("unsupported ledger contract")
    if not isinstance(ledger.get("events"), list):
        raise LedgerError("events must be an array")
    return ledger


def append_event(
    ledger: dict[str, Any],
    *,
    cycle: int,
    stage: str,
    tool: str,
    status: str,
    inputs: list[Path],
    outputs: list[Path],
    evidence_refs: list[str],
    error_code: str | None,
    message: str,
) -> dict[str, Any]:
    maximum = int(ledger.get("maximum_cycles", 0))
    if not 1 <= cycle <= maximum:
        raise LedgerError(f"cycle must be from 1 to {maximum}")
    if stage not in STAGES:
        raise LedgerError(f"unsupported stage: {stage}")
    if status not in STATUSES:
        raise LedgerError(f"unsupported status: {status}")
    if status == "failed" and not error_code:
        raise LedgerError("failed events require error_code")
    if ledger.get("final_status") != "open":
        raise LedgerError("cannot append after the ledger is closed")
    for path in [*inputs, *outputs]:
        if not path.is_file():
            raise LedgerError(f"bound file does not exist: {path}")
    event = {
        "event_id": f"event-{len(ledger['events']) + 1:04d}",
        "recorded_at": now(),
        "cycle": cycle,
        "stage": stage,
        "tool": tool,
        "status": status,
        "inputs": [file_binding(path) for path in inputs],
        "outputs": [file_binding(path) for path in outputs],
        "evidence_refs": sorted(set(evidence_refs)),
        "error_code": error_code,
        "message": message,
    }
    ledger["events"].append(event)
    return event


def close(ledger: dict[str, Any], final_status: str) -> None:
    if final_status not in {"pass", "known-risk", "incomplete"}:
        raise LedgerError("unsupported final_status")
    if ledger.get("final_status") != "open":
        raise LedgerError("ledger is already closed")
    ledger["final_status"] = final_status
    ledger["closed_at"] = now()


def write(path: Path, ledger: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a new execution ledger")
    init.add_argument("ledger", type=Path)
    init.add_argument("--run-id", required=True)
    init.add_argument("--config", type=Path, default=Path("config/default.json"))
    init.add_argument("--maximum-cycles", type=int, help="Explicit override; otherwise use central configuration")

    record = subparsers.add_parser("record", help="Append a tool observation")
    record.add_argument("ledger", type=Path)
    record.add_argument("--cycle", type=int, required=True)
    record.add_argument("--stage", choices=sorted(STAGES), required=True)
    record.add_argument("--tool", required=True)
    record.add_argument("--status", choices=sorted(STATUSES), required=True)
    record.add_argument("--input", type=Path, action="append", default=[])
    record.add_argument("--output", type=Path, action="append", default=[])
    record.add_argument("--evidence-ref", action="append", default=[])
    record.add_argument("--error-code")
    record.add_argument("--message", default="")

    finish = subparsers.add_parser("close", help="Close a ledger without inventing success")
    finish.add_argument("ledger", type=Path)
    finish.add_argument("--final-status", choices=["pass", "known-risk", "incomplete"], required=True)

    summary = subparsers.add_parser("summary", help="Print a compact ledger summary")
    summary.add_argument("ledger", type=Path)

    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "init":
            maximum_cycles = args.maximum_cycles if args.maximum_cycles is not None else configured_maximum_cycles(args.config)
            ledger = initialize(args.run_id, maximum_cycles)
            write(args.ledger, ledger)
        else:
            ledger = read(args.ledger)
            if args.command == "record":
                event = append_event(
                    ledger,
                    cycle=args.cycle,
                    stage=args.stage,
                    tool=args.tool,
                    status=args.status,
                    inputs=args.input,
                    outputs=args.output,
                    evidence_refs=args.evidence_ref,
                    error_code=args.error_code,
                    message=args.message,
                )
                write(args.ledger, ledger)
                print(json.dumps(event, ensure_ascii=False, indent=2))
            elif args.command == "close":
                close(ledger, args.final_status)
                write(args.ledger, ledger)
            else:
                counts: dict[str, int] = {}
                for event in ledger["events"]:
                    counts[event.get("status", "unknown")] = counts.get(event.get("status", "unknown"), 0) + 1
                print(
                    json.dumps(
                        {
                            "run_id": ledger.get("run_id"),
                            "event_count": len(ledger["events"]),
                            "status_counts": counts,
                            "final_status": ledger.get("final_status"),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
    except LedgerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
