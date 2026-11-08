#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate repository-local Markdown file links."""

from __future__ import annotations

import argparse
import hashlib
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


def partition_frozen_findings(root: Path, errors: list[dict[str, str]]):
    registry = root / "published/frozen-markdown-findings.json"
    if not registry.is_file():
        return errors, []
    record = json.loads(registry.read_text(encoding="utf-8"))
    if record.get("contract") != "io.clayz.frozen-markdown-findings/1":
        raise ValueError("unknown_frozen_findings_contract")
    publication = (root / record["publication"]).resolve()
    publication.relative_to(root)
    manifest = json.loads(publication.read_text(encoding="utf-8"))
    if manifest["archive"]["sha256"] != record["archive_sha256"]:
        raise ValueError("frozen_publication_identity_changed")
    known = {(row["path"], row["target"], row["error"]): row for row in record["findings"]}
    unexpected, retained = [], []
    for error in errors:
        row = known.get((error["path"], error["target"], error["error"]))
        source = (root / error["path"]).resolve()
        source.relative_to(root)
        if row and hashlib.sha256(source.read_bytes()).hexdigest() == row["source_sha256"]:
            retained.append(error)
        else:
            unexpected.append(error)
    return unexpected, retained


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors = validate(root)
    unexpected, retained = partition_frozen_findings(root, errors)
    print(json.dumps({"ok": not unexpected, "all_links_valid": not errors,
                      "errors": unexpected, "retained_frozen_findings": retained},
                     ensure_ascii=False, indent=2))
    return 1 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())

