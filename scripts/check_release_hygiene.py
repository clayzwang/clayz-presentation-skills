#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Reject private paths, opaque file identifiers, caches, and non-public binaries."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath


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
TEXT_SUFFIXES = {".md", ".py", ".js", ".mjs", ".html", ".css", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".txt", ".cff", ".svg"}
DEFAULT_DENYLIST: list[str] = []
PUBLIC_OUTPUT_MANIFEST = Path("experience/case-manifest.json")
PUBLIC_OUTPUT_ROOT = Path("experience/assets/decks")
LEGACY_PUBLIC_OUTPUTS = {Path("clayz-four-slide-showcase.pptx")}
MAX_PUBLIC_OUTPUT_BYTES = 25 * 1024 * 1024
MAX_PUBLIC_OUTPUT_XML_BYTES = 20 * 1024 * 1024


def load_denylist(path: Path | None) -> list[str]:
    if path is None:
        return list(DEFAULT_DENYLIST)
    extra = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]
    return list(dict.fromkeys([*DEFAULT_DENYLIST, *extra]))


def _finding(path: Path | str, rule: str, match: str) -> dict[str, str]:
    return {"path": str(path), "rule": rule, "match": match[:120]}


def load_public_output_allowlist(root: Path) -> tuple[set[Path], list[dict[str, str]]]:
    manifest_path = root / PUBLIC_OUTPUT_MANIFEST
    if not manifest_path.is_file():
        return set(), []

    findings: list[dict[str, str]] = []
    allowed: set[Path] = set()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return set(), [_finding(PUBLIC_OUTPUT_MANIFEST, "invalid-public-output-manifest", str(error))]

    cases = manifest.get("cases")
    if not isinstance(cases, list):
        return set(), [_finding(PUBLIC_OUTPUT_MANIFEST, "invalid-public-output-manifest", "cases must be a list")]

    for index, case in enumerate(cases):
        location = f"cases[{index}]"
        if not isinstance(case, dict):
            findings.append(_finding(PUBLIC_OUTPUT_MANIFEST, "invalid-public-output-case", location))
            continue

        repository_path = case.get("repository_path")
        policy = case.get("policy")
        if not isinstance(repository_path, str) or not repository_path.strip():
            findings.append(_finding(PUBLIC_OUTPUT_MANIFEST, "missing-public-output-path", location))
            continue
        if not isinstance(policy, dict) or not (
            policy.get("public_data_output_evidence") is True
            and policy.get("admitted_to_reference_corpus") is False
            and policy.get("admitted_to_knowledge_corpus") is False
        ):
            findings.append(_finding(PUBLIC_OUTPUT_MANIFEST, "invalid-public-output-policy", repository_path))
            continue

        pure_path = PurePosixPath(repository_path)
        if pure_path.is_absolute() or ".." in pure_path.parts:
            findings.append(_finding(PUBLIC_OUTPUT_MANIFEST, "unsafe-public-output-path", repository_path))
            continue

        relative = Path(*pure_path.parts)
        is_isolated_output = relative.parent == PUBLIC_OUTPUT_ROOT
        if not is_isolated_output and relative not in LEGACY_PUBLIC_OUTPUTS:
            findings.append(_finding(PUBLIC_OUTPUT_MANIFEST, "public-output-outside-isolation-boundary", repository_path))
            continue
        if relative.suffix.lower() != ".pptx":
            findings.append(_finding(PUBLIC_OUTPUT_MANIFEST, "unsupported-public-output-format", repository_path))
            continue
        if not (root / relative).is_file():
            findings.append(_finding(PUBLIC_OUTPUT_MANIFEST, "missing-public-output", repository_path))
            continue
        allowed.add(relative)

    return allowed, findings


def scan_text(path: Path, relative: Path, text: str, denylist: list[str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for name, pattern in GENERIC_PATTERNS.items():
        match = pattern.search(text)
        if match:
            findings.append(_finding(relative, name, match.group(0)))
    folded = text.casefold()
    for term in denylist:
        if term.casefold() in folded:
            findings.append(_finding(relative, "external-denylist", term))
    return findings


def scan_public_pptx(path: Path, relative: Path, denylist: list[str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if path.stat().st_size > MAX_PUBLIC_OUTPUT_BYTES:
        findings.append(_finding(relative, "public-output-too-large", str(path.stat().st_size)))
        return findings

    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            for required in ("[Content_Types].xml", "ppt/presentation.xml"):
                if required not in names:
                    findings.append(_finding(relative, "invalid-pptx-package", f"missing {required}"))

            scanned_bytes = 0
            for info in archive.infolist():
                member = PurePosixPath(info.filename)
                if member.is_absolute() or ".." in member.parts:
                    findings.append(_finding(relative, "unsafe-pptx-member", info.filename))
                    continue
                if member.suffix.lower() not in {".xml", ".rels", ".txt"}:
                    continue
                scanned_bytes += info.file_size
                if scanned_bytes > MAX_PUBLIC_OUTPUT_XML_BYTES:
                    findings.append(_finding(relative, "public-output-xml-too-large", str(scanned_bytes)))
                    break
                text = archive.read(info).decode("utf-8-sig", errors="replace")
                member_relative = Path(f"{relative}!{info.filename}")
                findings.extend(scan_text(path, member_relative, text, denylist))
    except (OSError, zipfile.BadZipFile) as error:
        findings.append(_finding(relative, "invalid-pptx-package", str(error)))
    return findings


def scan(root: Path, denylist: list[str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    allowed_outputs, manifest_findings = load_public_output_allowlist(root)
    findings.extend(manifest_findings)

    for path in sorted(root.rglob("*")):
        if ".git" in path.parts:
            continue
        relative = path.relative_to(root)
        if path.is_dir():
            if path.name == "__pycache__":
                findings.append(_finding(relative, "python-cache", path.name))
            continue

        suffix = path.suffix.lower()
        if suffix in FORBIDDEN_SUFFIXES:
            if relative in allowed_outputs and suffix == ".pptx":
                findings.extend(scan_public_pptx(path, relative, denylist))
            else:
                findings.append(_finding(relative, "forbidden-binary", suffix))

        if suffix not in TEXT_SUFFIXES and path.name not in {"LICENSE", "NOTICE"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(_finding(relative, "unexpected-binary", "non-UTF-8"))
            continue
        findings.extend(scan_text(path, relative, text, denylist))
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
