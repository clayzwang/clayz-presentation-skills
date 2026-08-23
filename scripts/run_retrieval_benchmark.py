#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Run the deterministic Stage 5 retrieval benchmark."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.feedback import build_learning_provider, run_retrieval_benchmark  # noqa: E402
from packages.index_runtime import CompositeIndex, IndexProvider  # noqa: E402


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", type=Path)
    parser.add_argument("--learning-records", type=Path, required=True)
    parser.add_argument("--learning-admissions", type=Path, required=True)
    parser.add_argument("--created-at", default="2026-08-23T12:00:00Z")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    builtin = IndexProvider.from_jsonl("builtin-catalog", ROOT / "catalog" / "records.jsonl")
    learning, _ = build_learning_provider(
        read_jsonl(args.learning_records),
        read_jsonl(args.learning_admissions),
        created_at=args.created_at,
    )
    spec = json.loads(args.benchmark.read_text(encoding="utf-8"))
    report = run_retrieval_benchmark(CompositeIndex([builtin, learning]), spec, created_at=args.created_at)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["summary"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
