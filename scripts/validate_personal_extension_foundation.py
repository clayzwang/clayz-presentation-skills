#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate the public-only Personal Extension Profile foundation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime import IndexProvider  # noqa: E402
from packages.personal_extension import PersonalExtensionError, validate_provider_manifest  # noqa: E402


SCHEMAS = {
    "packages/contracts/personal-extension-profile.schema.json": "urn:clayz:presentation:schema:personal-extension-profile:1.0",
    "packages/contracts/provider-manifest.schema.json": "urn:clayz:presentation:schema:provider-manifest:1.0",
    "packages/contracts/personal-extension-runtime.schema.json": "urn:clayz:presentation:schema:personal-extension-runtime:1.0",
}
SKILLS = (
    "clayz-presentation-logic",
    "clayz-presentation-copy",
    "clayz-presentation-art-direction",
    "clayz-presentation-output",
    "clayz-presentation-supervisor",
)


def main() -> int:
    for relative, expected_id in SCHEMAS.items():
        value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise PersonalExtensionError(f"{relative}: unexpected JSON Schema draft")
        if value.get("$id") != expected_id or value.get("type") != "object":
            raise PersonalExtensionError(f"{relative}: invalid root contract")
    public_manifest = validate_provider_manifest(json.loads((ROOT / "catalog" / "provider-manifest.json").read_text(encoding="utf-8")))
    public_provider = IndexProvider.from_jsonl("builtin-catalog", ROOT / "catalog" / "records.jsonl")
    if public_manifest["index"]["snapshot"] != public_provider.snapshot():
        raise PersonalExtensionError("catalog/provider-manifest.json: public index snapshot drift")
    if set(public_manifest["evolution_methods"].values()) != {"deferred"}:
        raise PersonalExtensionError("public material evolution methods must remain explicitly deferred")
    for skill in SKILLS:
        text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        if "Personal Extension Runtime" not in text:
            raise PersonalExtensionError(f"{skill}: missing Personal Extension Runtime route")
    if "Task Overlay" in (ROOT / "packages" / "personal_extension" / "resolver.py").read_text(encoding="utf-8"):
        raise PersonalExtensionError("Task Overlay is deferred and must not enter the v0.5.2 runtime")
    print("personal extension foundation valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
