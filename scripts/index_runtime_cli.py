#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate index records and emit deterministic retrieval receipts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime import (  # noqa: E402
    CompositeIndex,
    IndexProvider,
    IndexRuntimeError,
    read_json,
    write_json,
)


def provider_spec(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("provider must use PROVIDER_ID=PATH")
    provider_id, path = raw.split("=", 1)
    if not provider_id or not path:
        raise argparse.ArgumentTypeError("provider must use PROVIDER_ID=PATH")
    return provider_id, Path(path)


def build_runtime(root: Path, specs: list[tuple[str, Path]]) -> CompositeIndex:
    providers = []
    for provider_id, path in specs:
        resolved = path if path.is_absolute() else root / path
        providers.append(IndexProvider.from_jsonl(provider_id, resolved))
    return CompositeIndex(providers)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate one or more provider JSONL files")
    validate.add_argument("--provider", action="append", required=True, type=provider_spec)

    search = subparsers.add_parser("search", help="search providers and write a retrieval receipt")
    search.add_argument("--provider", action="append", required=True, type=provider_spec)
    search.add_argument("--request", type=Path, required=True)
    search.add_argument("--receipt", type=Path, required=True)

    finalize = subparsers.add_parser("finalize", help="record selected and rejected candidate IDs")
    finalize.add_argument("--provider", action="append", required=True, type=provider_spec)
    finalize.add_argument("--receipt", type=Path, required=True)
    finalize.add_argument("--selected", action="append", default=[], help="RECORD_ID=REASON")
    finalize.add_argument("--rejected", action="append", default=[], help="RECORD_ID=REASON")
    finalize.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    root = args.root.resolve()
    try:
        runtime = build_runtime(root, args.provider)
        if args.command == "validate":
            print(json.dumps({"providers": runtime.snapshots()}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "search":
            request_path = args.request if args.request.is_absolute() else root / args.request
            receipt_path = args.receipt if args.receipt.is_absolute() else root / args.receipt
            receipt = runtime.search(read_json(request_path))
            write_json(receipt_path, receipt)
            print(json.dumps(receipt, ensure_ascii=False, indent=2))
            return 0

        receipt_path = args.receipt if args.receipt.is_absolute() else root / args.receipt
        output_path = args.output if args.output.is_absolute() else root / args.output

        def decisions(values: list[str]) -> dict[str, str]:
            result: dict[str, str] = {}
            for raw in values:
                if "=" not in raw:
                    raise IndexRuntimeError("selection must use RECORD_ID=REASON")
                record_id, reason = raw.split("=", 1)
                if not record_id or not reason:
                    raise IndexRuntimeError("selection must use RECORD_ID=REASON")
                result[record_id] = reason
            return result

        finalized = runtime.finalize_receipt(
            read_json(receipt_path),
            selected=decisions(args.selected),
            rejected=decisions(args.rejected),
        )
        write_json(output_path, finalized)
        print(json.dumps(finalized, ensure_ascii=False, indent=2))
        return 0
    except (OSError, IndexRuntimeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
