#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate an IndexRecord JSONL and write its shared Provider manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime import IndexProvider, IndexRuntimeError, write_json  # noqa: E402
from packages.personal_extension import PersonalExtensionError, build_provider_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider-id", required=True)
    parser.add_argument("--records", type=Path, required=True, help="Human-admitted index-record JSONL")
    parser.add_argument("--index-uri", required=True, help="bundle:// URI for public or library:// URI for owner-private")
    parser.add_argument("--visibility", choices=["public", "owner-private"], default="owner-private")
    parser.add_argument("--allowed-host", action="append", choices=["local", "chatgpt-personal"])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        provider = IndexProvider.from_jsonl(args.provider_id, args.records.resolve())
        manifest = build_provider_manifest(
            provider,
            index_uri=args.index_uri,
            visibility=args.visibility,
            allowed_hosts=args.allowed_host or ["local", "chatgpt-personal"],
        )
        write_json(args.output.resolve(), manifest)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0
    except (OSError, IndexRuntimeError, PersonalExtensionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
