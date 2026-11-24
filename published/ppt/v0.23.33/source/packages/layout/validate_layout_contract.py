#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate one high-level Clayz Layout Contract JSON document."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.layout.layout_contract import LayoutContractError, validate_layout_contract  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Layout Contract JSON")
    args = parser.parse_args()
    try:
        value = json.loads(args.input.read_text(encoding="utf-8"))
        validate_layout_contract(value)
    except (OSError, json.JSONDecodeError, LayoutContractError) as exc:
        parser.error(str(exc))
    print(f"valid {args.input}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
