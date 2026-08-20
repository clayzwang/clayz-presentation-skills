#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate the five public skill folders without external dependencies."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"')
    return result


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    skill_root = root / "skills"
    skills = sorted(path for path in skill_root.iterdir() if path.is_dir())
    if len(skills) != 5:
        errors.append(f"skills: expected 5 directories, found {len(skills)}")
    for path in skills:
        manifest = path / "SKILL.md"
        if not manifest.is_file():
            errors.append(f"{path.name}: missing SKILL.md")
            continue
        text = manifest.read_text(encoding="utf-8")
        meta = frontmatter(text)
        name = meta.get("name", "")
        description = meta.get("description", "")
        if name != path.name:
            errors.append(f"{path.name}: frontmatter name mismatch: {name!r}")
        if not NAME_RE.fullmatch(name):
            errors.append(f"{path.name}: invalid skill name")
        if not 40 <= len(description) <= 900:
            errors.append(f"{path.name}: description length must be 40..900")
        if len(text.splitlines()) > 500:
            errors.append(f"{path.name}: SKILL.md exceeds 500 lines")
        if "../../config/default.json" not in text:
            errors.append(f"{path.name}: does not route through central config")
        if "../../packages/contracts/knowledge-learning.md" not in text:
            errors.append(f"{path.name}: does not route through shared knowledge contract")
        if ".zh-CN.md" not in text or "locale.default" not in text:
            errors.append(f"{path.name}: does not declare bilingual locale routing")
        if (path / "README.md").exists():
            errors.append(f"{path.name}: README belongs at repository root")
        ui = path / "agents" / "openai.yaml"
        if not ui.is_file():
            errors.append(f"{path.name}: missing agents/openai.yaml")
        else:
            ui_text = ui.read_text(encoding="utf-8")
            if f"${name}" not in ui_text:
                errors.append(f"{path.name}: default prompt must mention ${name}")
        if not (path / "assets" / "clayz-mark.svg").is_file():
            errors.append(f"{path.name}: missing clayz mark")
        references = path / "references"
        english_references = sorted(
            item for item in references.glob("*.md")
            if not item.name.endswith(".zh-CN.md")
        )
        if not english_references:
            errors.append(f"{path.name}: missing English references")
        for english in english_references:
            chinese = english.with_name(f"{english.stem}.zh-CN.md")
            if not chinese.is_file():
                errors.append(f"{path.name}: missing Chinese peer for {english.name}")
        for chinese in references.glob("*.zh-CN.md"):
            english = chinese.with_name(chinese.name.removesuffix(".zh-CN.md") + ".md")
            if not english.is_file():
                errors.append(f"{path.name}: missing English peer for {chinese.name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    errors = validate(Path(args.root).resolve())
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
