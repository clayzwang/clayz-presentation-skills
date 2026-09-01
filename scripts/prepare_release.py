#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Prepare a release by updating every current-version surface atomically."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

from validate_version import SEMVER, validate


TEXT_SURFACES = (
    "VERSION",
    ".codex-plugin/plugin.json",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/compatibility.yml",
    ".github/ISSUE_TEMPLATE/output_quality.yml",
    "CHANGELOG.md",
    "CITATION.cff",
    "README.md",
    "README.zh-CN.md",
    "config/default.json",
    "config/component-versions.json",
    "experience/index.html",
)


def version_tuple(value: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in value.split("."))  # type: ignore[return-value]


def prepare(root: Path, new_version: str, release_date: str) -> None:
    if not SEMVER.fullmatch(new_version):
        raise RuntimeError("new version must be stable semantic version X.Y.Z without a v prefix")
    try:
        date.fromisoformat(release_date)
    except ValueError as exc:
        raise RuntimeError("release date must use YYYY-MM-DD") from exc

    current = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not SEMVER.fullmatch(current) or version_tuple(new_version) <= version_tuple(current):
        raise RuntimeError(f"new version {new_version} must be greater than current {current}")
    paths = [root / relative for relative in TEXT_SURFACES]
    missing = [str(path.relative_to(root)) for path in paths if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing release surfaces: {missing}")
    originals = {path: path.read_text(encoding="utf-8") for path in paths}
    updated = dict(originals)

    plugin_path = root / ".codex-plugin/plugin.json"
    plugin = json.loads(updated[plugin_path])
    if plugin.get("version") != current:
        raise RuntimeError("plugin version does not match current VERSION")
    plugin_marker = f'"version": "{current}"'
    if updated[plugin_path].count(plugin_marker) != 1:
        raise RuntimeError("plugin version marker is ambiguous")
    updated[plugin_path] = updated[plugin_path].replace(
        plugin_marker,
        f'"version": "{new_version}"',
        1,
    )

    config_path = root / "config/default.json"
    config = json.loads(updated[config_path])
    if config["identity"]["version"] != current or config["identity"]["attribution"]["custom_properties"]["ClayzVersion"] != current:
        raise RuntimeError("central configuration does not match current VERSION")
    config_markers = {
        f'"version": "{current}"': f'"version": "{new_version}"',
        f'"ClayzVersion": "{current}"': f'"ClayzVersion": "{new_version}"',
    }
    for old, new in config_markers.items():
        if updated[config_path].count(old) != 1:
            raise RuntimeError(f"central configuration marker is ambiguous: {old}")
        updated[config_path] = updated[config_path].replace(old, new, 1)

    component_versions_path = root / "config/component-versions.json"
    component_versions = json.loads(updated[component_versions_path])
    if component_versions.get("release_version") != current:
        raise RuntimeError("component version manifest does not match current VERSION")
    component_versions["release_version"] = new_version
    for component_id in ("public-core", "plugin-manifest", "central-config"):
        if component_versions.get("components", {}).get(component_id) != current:
            raise RuntimeError(f"component version manifest {component_id} does not match current VERSION")
        component_versions["components"][component_id] = new_version
    updated[component_versions_path] = json.dumps(component_versions, ensure_ascii=False, indent=2) + "\n"

    citation_path = root / "CITATION.cff"
    citation = updated[citation_path]
    citation, version_count = re.subn(rf"^version: {re.escape(current)}$", f"version: {new_version}", citation, count=1, flags=re.MULTILINE)
    citation, date_count = re.subn(r"^date-released: [0-9]{4}-[0-9]{2}-[0-9]{2}$", f"date-released: {release_date}", citation, count=1, flags=re.MULTILINE)
    if version_count != 1 or date_count != 1:
        raise RuntimeError("CITATION.cff current version or date marker is missing")
    updated[citation_path] = citation

    replacements = {
        root / "README.md": (f"Current release: **v{current}**", f"Current release: **v{new_version}**"),
        root / "README.zh-CN.md": (f"当前版本：**v{current}**", f"当前版本：**v{new_version}**"),
    }
    for path, (old, new) in replacements.items():
        if updated[path].count(old) != 1:
            raise RuntimeError(f"{path.relative_to(root)} current-release marker is ambiguous")
        updated[path] = updated[path].replace(old, new)

    experience_path = root / "experience/index.html"
    experience = updated[experience_path]
    marker = f'data-release-version="{current}"'
    if experience.count(marker) < 2:
        raise RuntimeError("experience current-release markers are missing")
    experience = experience.replace(marker, f'data-release-version="{new_version}"')
    experience = "\n".join(
        line.replace(f"v{current}", f"v{new_version}") if "data-release-version=" in line else line
        for line in experience.split("\n")
    )
    updated[experience_path] = experience

    for relative in (
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/compatibility.yml",
        ".github/ISSUE_TEMPLATE/output_quality.yml",
    ):
        path = root / relative
        updated[path] = updated[path].replace(f"v{current}", f"v{new_version}")

    changelog_path = root / "CHANGELOG.md"
    changelog = updated[changelog_path]
    start_marker = "## Unreleased\n"
    start = changelog.find(start_marker)
    if start < 0:
        raise RuntimeError("CHANGELOG.md has no Unreleased section")
    body_start = start + len(start_marker)
    next_section = changelog.find("\n## ", body_start)
    if next_section < 0:
        raise RuntimeError("CHANGELOG.md has no prior release section")
    unreleased = changelog[body_start:next_section].strip()
    lines = [line for line in unreleased.splitlines() if line.strip() != "- Nothing yet."]
    unreleased = "\n".join(lines).strip()
    if not unreleased or not any(line.startswith("- ") for line in lines):
        raise RuntimeError("CHANGELOG.md Unreleased section has no release notes")
    new_block = f"## Unreleased\n\n- Nothing yet.\n\n## {new_version} — {release_date}\n\n{unreleased}"
    updated[changelog_path] = changelog[:start] + new_block + changelog[next_section:]
    updated[root / "VERSION"] = new_version + "\n"

    try:
        for path, content in updated.items():
            path.write_text(content, encoding="utf-8", newline="\n")
        errors = validate(root)
        if errors:
            raise RuntimeError("prepared release failed validation: " + "; ".join(errors))
    except Exception:
        for path, content in originals.items():
            path.write_text(content, encoding="utf-8", newline="\n")
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("--date", default=date.today().isoformat(), dest="release_date")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        prepare(args.root.resolve(), args.version, args.release_date)
    except (OSError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"prepared release {args.version} ({args.release_date})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
