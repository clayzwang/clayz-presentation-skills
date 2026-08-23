#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Resolve, compile, and solve a registered Clayz Layout Contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime import CompositeIndex  # noqa: E402
from packages.layout.layout_contract import (  # noqa: E402
    LayoutContractError,
    compile_layout_contract,
    load_builtin_provider,
    resolve_layout_contract,
)
from packages.layout.solve_relative_layout import solve_compilation  # noqa: E402


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise LayoutContractError(f"{path}: expected an object")
    return value


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path, help="Layout-contract request JSON")
    parser.add_argument("instance", type=Path, help="Layout-contract instance JSON")
    parser.add_argument("output", type=Path, help="Compiled layout envelope JSON")
    parser.add_argument("--receipt-output", type=Path, help="Retrieval receipt JSON")
    parser.add_argument("--resolution-output", type=Path, help="Layout-contract resolution JSON")
    parser.add_argument("--resolved-output", type=Path, help="Resolved coordinate manifest JSON")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root")
    parser.add_argument("--created-at", help="Fixed timestamp for reproducible fixtures")
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        provider = load_builtin_provider(root)
        runtime = CompositeIndex([provider])
        resolution, receipt = resolve_layout_contract(runtime, _read(args.request), created_at=args.created_at)
        if args.receipt_output:
            _write(args.receipt_output, receipt)
        if args.resolution_output:
            _write(args.resolution_output, resolution)
        if resolution["status"] != "selected":
            raise LayoutContractError(f"layout contract unresolved: {resolution['fallback']['reason']}")
        compilation = compile_layout_contract(root, provider, resolution, receipt, _read(args.instance))
        _write(args.output, compilation)
        if args.resolved_output:
            _write(args.resolved_output, solve_compilation(compilation))
    except (OSError, json.JSONDecodeError, LayoutContractError, ValueError) as exc:
        parser.error(str(exc))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
