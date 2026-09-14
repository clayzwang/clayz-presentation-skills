#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Build a hash-bound staged component manifest for pre-release ChatGPT acceptance."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--commit", required=True)
    parser.add_argument("--base-latest-version", required=True)
    parser.add_argument("--expires-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise SystemExit("VERSION is not stable semantic version text")
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        raise SystemExit("--commit must be a lowercase 40-character Git commit")
    component_path = root / "config" / "component-versions.json"
    manifest = {
        "contract": "io.clayz.presentation.component-candidate-manifest/1.0",
        "repository": "clayzwang/clayz-presentation-skills",
        "status": "staged-candidate",
        "candidate_version": version,
        "base_latest_version": args.base_latest_version,
        "candidate_commit": args.commit,
        "component_manifest_sha256": hashlib.sha256(component_path.read_bytes()).hexdigest(),
        "expires_at": args.expires_at,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"ok": True, "candidate_version": version, "output": args.output.as_posix()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
