#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Reject private paths, opaque file identifiers, caches, and non-public binaries."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


FORBIDDEN_SUFFIXES = {
    ".ppt", ".pptx", ".pdf", ".ttf", ".otf", ".woff", ".woff2",
    ".zip", ".7z", ".rar", ".pyc", ".pyo",
}
GENERIC_PATTERNS = {
    "private-unix-path": re.compile(r"/(?:root|home|Users|workspace)/[^\s'\"`]+"),
    "private-windows-path": re.compile(r"[A-Za-z]:\\\\Users\\\\[^\s'\"`]+"),
    "library-file-id": re.compile(r"\blibfile_[0-9a-f]{12,}\b", re.I),
    "conversation-file-id": re.compile(r"\bfile_[0-9a-f]{12,}\b", re.I),
    "private-reference-root": re.compile(r"(?<![A-Za-z0-9_])" + re.escape("/" + "PPT" + "/")),
    "credential-assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\b"
        r"\s*[:=]\s*[\"']?[A-Za-z0-9_./+=-]{16,}"
    ),
    "credential-in-url": re.compile(r"https?://[^\s/@:]+:[^\s/@]+@"),
}
TEXT_SUFFIXES = {".md", ".py", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".txt", ".cff", ".svg"}
# Organization- or project-specific blocked terms belong in an untracked file
# supplied through --denylist. The public scaffold must not embed private names.
DEFAULT_DENYLIST: list[str] = []


def load_denylist(path: Path | None) -> list[str]:
    if path is None:
        return list(DEFAULT_DENYLIST)
    extra = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]
    return list(dict.fromkeys([*DEFAULT_DENYLIST, *extra]))


def scan(root: Path, denylist: list[str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts:
            continue
        relative = path.relative_to(root)
        if path.is_dir():
            if path.name == "__pycache__":
                findings.append({"path": str(relative), "rule": "python-cache", "match": path.name})
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            findings.append({"path": str(relative), "rule": "forbidden-binary", "match": path.suffix.lower()})
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE", "NOTICE"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append({"path": str(relative), "rule": "unexpected-binary", "match": "non-UTF-8"})
            continue
        for name, pattern in GENERIC_PATTERNS.items():
            match = pattern.search(text)
            if match:
                findings.append({"path": str(relative), "rule": name, "match": match.group(0)[:120]})
        folded = text.casefold()
        for term in denylist:
            if term.casefold() in folded:
                findings.append({"path": str(relative), "rule": "external-denylist", "match": term})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--denylist")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    denylist = load_denylist(Path(args.denylist) if args.denylist else None)
    findings = scan(root, denylist)
    print(json.dumps({"ok": not findings, "findings": findings}, ensure_ascii=False, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
