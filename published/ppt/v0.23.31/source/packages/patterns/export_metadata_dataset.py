#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Export registered Pattern Library records as metadata-only JSON."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime import write_json  # noqa: E402
from packages.patterns import PatternLibraryError, export_metadata_dataset, load_builtin_provider  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--record-type", action="append", dest="record_types")
    parser.add_argument("--created-at")
    args = parser.parse_args()
    try:
        provider = load_builtin_provider(ROOT)
        document = export_metadata_dataset(
            ROOT,
            provider,
            record_types=args.record_types or ("composition-pattern", "failure-pattern", "reference", "sequence"),
            created_at=args.created_at,
        )
        write_json(args.output, document)
    except PatternLibraryError as exc:
        print(f"metadata dataset export failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
