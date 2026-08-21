#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate the canonical release version across every current-version surface."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
REQUIRED_FILES = (
    "VERSION",
    ".codex-plugin/plugin.json",
    ".github/workflows/release.yml",
    "CHANGELOG.md",
    "CITATION.cff",
    "README.md",
    "README.zh-CN.md",
    "config/default.json",
    "experience/index.html",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    missing = [relative for relative in REQUIRED_FILES if not (root / relative).is_file()]
    if missing:
        return [f"missing required version surface: {relative}" for relative in missing]

    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not SEMVER.fullmatch(version):
        errors.append("VERSION: must contain one stable semantic version without a v prefix")
        return errors

    try:
        plugin = read_json(root / ".codex-plugin/plugin.json")
        config = read_json(root / "config/default.json")
        citation = yaml.safe_load((root / "CITATION.cff").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        return [f"version surface parse failure: {exc}"]

    comparisons = {
        ".codex-plugin/plugin.json version": plugin.get("version"),
        "config/default.json identity.version": config.get("identity", {}).get("version"),
        "config/default.json ClayzVersion": config.get("identity", {}).get("attribution", {}).get("custom_properties", {}).get("ClayzVersion"),
        "CITATION.cff version": str(citation.get("version")) if isinstance(citation, dict) else None,
    }
    for label, actual in comparisons.items():
        if actual != version:
            errors.append(f"{label}: expected {version}, found {actual!r}")

    readme = (root / "README.md").read_text(encoding="utf-8")
    readme_zh = (root / "README.zh-CN.md").read_text(encoding="utf-8")
    if f"Current release: **v{version}**" not in readme:
        errors.append("README.md: current-release marker must match VERSION")
    if f"当前版本：**v{version}**" not in readme_zh:
        errors.append("README.zh-CN.md: current-release marker must match VERSION")

    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    release_heading = re.compile(rf"^## {re.escape(version)} — [0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}$", re.MULTILINE)
    if not release_heading.search(changelog):
        errors.append(f"CHANGELOG.md: missing dated section for {version}")
    if "## Unreleased" not in changelog:
        errors.append("CHANGELOG.md: Unreleased section must be preserved")

    experience = (root / "experience/index.html").read_text(encoding="utf-8")
    experience_versions = re.findall(r'data-release-version="([^"]+)"', experience)
    if len(experience_versions) < 2 or any(value != version for value in experience_versions):
        errors.append("experience/index.html: all data-release-version markers must match VERSION")

    workflow = (root / ".github/workflows/release.yml").read_text(encoding="utf-8")
    workflow_checks = {
        'push path "VERSION"': '- "VERSION"',
        "canonical VERSION read": 'root / "VERSION"',
        "immutable tag guard": 'git rev-list -n1 "$TAG"',
    }
    for label, marker in workflow_checks.items():
        if marker not in workflow:
            errors.append(f".github/workflows/release.yml: missing {label}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
