#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate a generated Personal Extension Runtime and its resolved configuration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime import IndexRuntimeError, read_json  # noqa: E402
from packages.personal_extension import PersonalExtensionError, validate_personal_extension_runtime  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runtime", type=Path)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--runtime-lock", type=Path, help="External runtime pack lock; defaults to runtime-lock.json beside the runtime")
    args = parser.parse_args()
    try:
        lock_path = args.runtime_lock or args.runtime.resolve().parent / "runtime-lock.json"
        runtime_pack_lock = read_json(lock_path) if lock_path.is_file() else None
        runtime = validate_personal_extension_runtime(
            read_json(args.runtime.resolve()),
            resolved_config=read_json(args.config.resolve()),
            runtime_pack_lock=runtime_pack_lock,
        )
        if args.runtime.resolve().parent.name == "runtime" and runtime_pack_lock is None:
            raise PersonalExtensionError("runtime/runtime-lock.json is required for a generated Personal Extension Runtime")
        print(json.dumps({"ok": True, "digest": runtime["lock"]["digest"]}, ensure_ascii=False))
        return 0
    except (OSError, IndexRuntimeError, PersonalExtensionError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
