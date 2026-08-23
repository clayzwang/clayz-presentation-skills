#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Resolve and compile one registered composition pattern."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime import CompositeIndex, read_json, write_json  # noqa: E402
from packages.patterns import (  # noqa: E402
    PatternLibraryError,
    compile_composition_pattern,
    load_builtin_provider,
    resolve_composition_pattern,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--resolution-output", type=Path, required=True)
    parser.add_argument("--receipt-dir", type=Path, required=True)
    parser.add_argument("--plan-output", type=Path, required=True)
    parser.add_argument("--created-at")
    args = parser.parse_args()

    provider = load_builtin_provider(ROOT)
    runtime = CompositeIndex([provider])
    try:
        resolution, receipts = resolve_composition_pattern(
            ROOT,
            runtime,
            read_json(args.request),
            created_at=args.created_at,
        )
        write_json(args.resolution_output, resolution)
        for receipt in receipts:
            write_json(args.receipt_dir / f"{receipt['receipt_id']}.json", receipt)
        if resolution["status"] != "selected":
            if args.plan_output.exists():
                raise PatternLibraryError("unresolved request cannot overwrite or leave a composition plan")
            return 2
        write_json(args.plan_output, compile_composition_pattern(ROOT, provider, resolution, receipts))
    except PatternLibraryError as exc:
        print(f"composition pattern compilation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
