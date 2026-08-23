#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Migrate a legacy filesystem knowledge store to governed index records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.feedback import migrate_legacy_knowledge  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--asset-registry", type=Path, required=True)
    parser.add_argument("--admission-registry", type=Path, required=True)
    parser.add_argument("--learning-root", type=Path, required=True)
    parser.add_argument("--provider-id", default="filesystem-library")
    parser.add_argument("--created-at", default="2026-08-23T12:00:00Z")
    parser.add_argument("--records-output", type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    provider, report = migrate_legacy_knowledge(
        source_root=args.source_root,
        asset_registry=args.asset_registry,
        admission_registry=args.admission_registry,
        learning_root=args.learning_root,
        provider_id=args.provider_id,
        created_at=args.created_at,
    )
    if args.records_output:
        args.records_output.parent.mkdir(parents=True, exist_ok=True)
        args.records_output.write_text(
            "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in provider.records),
            encoding="utf-8",
        )
    if args.report_output:
        args.report_output.parent.mkdir(parents=True, exist_ok=True)
        args.report_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not args.records_output and not args.report_output:
        print(json.dumps({"records": list(provider.records), "report": report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
