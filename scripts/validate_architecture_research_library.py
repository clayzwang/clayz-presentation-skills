#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate the official architecture source index and distilled pattern library."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


OFFICIAL_HOST_SUFFIXES = (
    "apple.com",
    "aws.amazon.com",
    "databricks.com",
    "docs.aws.amazon.com",
    "docs.cloud.google.com",
    "docs.databricks.com",
    "docs.nvidia.com",
    "docs.oracle.com",
    "docs.snowflake.com",
    "help.sap.com",
    "ibm.com",
    "learn.microsoft.com",
    "sap.com",
    "snowflake.com",
    "support.apple.com",
)

FORBIDDEN_RULE_HEADINGS = (
    "composition rules",
    "rejection tests",
    "house contract",
    "构图规则",
    "否决测试",
    "房子图合同",
)


def validate(index: dict[str, Any], pattern_text: str, method_texts: list[str]) -> list[str]:
    errors: list[str] = []
    sources = index.get("sources")
    if not isinstance(sources, list):
        return ["sources: array is required"]

    declared = index.get("source_count")
    if declared != len(sources):
        errors.append(f"source_count: declared {declared}, found {len(sources)}")
    if not 50 <= len(sources) <= 100:
        errors.append(f"sources: expected 50-100 entries, found {len(sources)}")

    ids: set[str] = set()
    urls: set[str] = set()
    publishers: Counter[str] = Counter()
    for position, source in enumerate(sources, 1):
        label = f"sources[{position}]"
        if not isinstance(source, dict):
            errors.append(f"{label}: object is required")
            continue
        for field in ("id", "publisher", "title", "url", "focus", "structure"):
            if field not in source:
                errors.append(f"{label}.{field}: required")
        identifier = source.get("id")
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"{label}.id: non-empty string is required")
        elif identifier in ids:
            errors.append(f"{label}.id: duplicate {identifier}")
        else:
            ids.add(identifier)
        publisher = source.get("publisher")
        if isinstance(publisher, str) and publisher:
            publishers[publisher] += 1
        else:
            errors.append(f"{label}.publisher: non-empty string is required")
        url = source.get("url")
        if not isinstance(url, str) or not url:
            errors.append(f"{label}.url: non-empty string is required")
        else:
            if url in urls:
                errors.append(f"{label}.url: duplicate {url}")
            urls.add(url)
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()
            if parsed.scheme != "https":
                errors.append(f"{label}.url: https is required")
            if not any(host == suffix or host.endswith(f".{suffix}") for suffix in OFFICIAL_HOST_SUFFIXES):
                errors.append(f"{label}.url: non-official host {host}")
        structure = source.get("structure")
        if not isinstance(structure, list) or len(structure) < 2 or not all(isinstance(item, str) and item for item in structure):
            errors.append(f"{label}.structure: at least two relationship tags are required")

    declared_publishers = index.get("publisher_count")
    if declared_publishers != len(publishers):
        errors.append(f"publisher_count: declared {declared_publishers}, found {len(publishers)}")
    if len(publishers) < 8:
        errors.append(f"publishers: expected at least 8, found {len(publishers)}")

    numbered_cards = [line for line in pattern_text.splitlines() if line.startswith("### ")]
    if len(numbered_cards) < 12:
        errors.append(f"pattern library: expected at least 12 cards, found {len(numbered_cards)}")
    for phrase in ("Relationship grammar", "Synthesis move", "Combining cards"):
        if phrase not in pattern_text:
            errors.append(f"pattern library: missing {phrase}")

    for text in method_texts:
        folded = text.casefold()
        for heading in FORBIDDEN_RULE_HEADINGS:
            if heading.casefold() in folded:
                errors.append(f"method: rule-oriented heading remains: {heading}")
        for required in ("architecture-source-index.json", "architecture-pattern-library"):
            if required not in text:
                errors.append(f"method: missing resource link {required}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    reference_root = root / "skills" / "clayz-presentation-art-direction" / "references"
    try:
        index = json.loads((reference_root / "architecture-source-index.json").read_text(encoding="utf-8"))
        pattern_text = (reference_root / "architecture-pattern-library.md").read_text(encoding="utf-8")
        method_texts = [
            (reference_root / "reference-architecture-house.md").read_text(encoding="utf-8"),
            (reference_root / "reference-architecture-house.zh-CN.md").read_text(encoding="utf-8"),
        ]
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2
    errors = validate(index, pattern_text, method_texts) if isinstance(index, dict) else ["index root must be an object"]
    print(json.dumps({"ok": not errors, "source_count": len(index.get("sources", [])), "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
