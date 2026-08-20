#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate repository-local Markdown file links."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse


LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def local_target(raw: str) -> str | None:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        value = value[1:value.index(">")]
    else:
        value = value.split(maxsplit=1)[0]
    if not value or value.startswith("#"):
        return None
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        return None
    return unquote(parsed.path)


def validate(root: Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for markdown in sorted(root.rglob("*.md")):
        if ".git" in markdown.parts:
            continue
        text = markdown.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = local_target(match.group(1))
            if target is None:
                continue
            resolved = (markdown.parent / target).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append({
                    "path": str(markdown.relative_to(root)),
                    "target": target,
                    "error": "target escapes repository root",
                })
                continue
            if not resolved.exists():
                errors.append({
                    "path": str(markdown.relative_to(root)),
                    "target": target,
                    "error": "target does not exist",
                })
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors = validate(root)
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
