#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate the registered public Pattern & Dataset Library."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.patterns import PatternLibraryError, load_builtin_provider, validate_registered_library  # noqa: E402


def main() -> int:
    try:
        result = validate_registered_library(ROOT, load_builtin_provider(ROOT))
    except PatternLibraryError as exc:
        print(f"pattern library validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"pattern library valid: {result['counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
