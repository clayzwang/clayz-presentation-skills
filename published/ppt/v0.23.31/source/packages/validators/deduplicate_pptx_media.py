#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Merge byte-identical PPTX media parts and rewrite their relationships."""

from __future__ import annotations

import argparse
import hashlib
import posixpath
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
ET.register_namespace("", REL_NS)


def owner_part(rel_part: str) -> str:
    folder = posixpath.dirname(rel_part)
    parent = posixpath.dirname(folder)
    name = posixpath.basename(rel_part)
    if not name.endswith(".rels"):
        return ""
    return posixpath.join(parent, name[:-5])


def resolve_target(owner: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(owner), target))


def target_for(owner: str, original: str, replacement: str) -> str:
    if original.startswith("/"):
        return "/" + replacement
    return posixpath.relpath(replacement, posixpath.dirname(owner))


def deduplicate(source: Path, output: Path) -> tuple[int, int]:
    with zipfile.ZipFile(source) as archive:
        infos = archive.infolist()
        media = [item for item in infos if item.filename.startswith("ppt/media/")]
        groups: dict[str, list[str]] = {}
        for item in media:
            digest = hashlib.sha256(archive.read(item)).hexdigest()
            groups.setdefault(digest, []).append(item.filename)
        replacement: dict[str, str] = {}
        for items in groups.values():
            if len(items) > 1:
                keep = sorted(items)[0]
                for duplicate in items:
                    if duplicate != keep:
                        replacement[duplicate] = keep
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as result:
            for item in infos:
                if item.filename in replacement:
                    continue
                data = archive.read(item)
                if item.filename.endswith(".rels") and replacement:
                    try:
                        root = ET.fromstring(data)
                    except ET.ParseError:
                        pass
                    else:
                        owner = owner_part(item.filename)
                        changed = False
                        for rel in root.findall(f"{{{REL_NS}}}Relationship"):
                            raw = rel.get("Target", "")
                            resolved = resolve_target(owner, raw)
                            if resolved in replacement:
                                rel.set("Target", target_for(owner, raw, replacement[resolved]))
                                changed = True
                        if changed:
                            data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
                result.writestr(item, data)
    return len(replacement), output.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("input and output must be different files")
    try:
        removed, size = deduplicate(args.input, args.output)
    except (OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"PASS: removed {removed} duplicate media part(s); output={size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
