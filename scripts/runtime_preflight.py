#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Run one Clayz runtime capability scan and write a locked route plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.runtime.preflight import build_preflight_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "default.json")
    parser.add_argument("--model-profile", choices=["A", "B", "C", "D"])
    parser.add_argument("--model-capabilities", type=Path, help="JSON object used only when --model-profile is omitted")
    parser.add_argument("--host-capabilities", type=Path, help="JSON object declaring inspected host presentation-tool capabilities")
    parser.add_argument("--require", action="append", default=[], help="Override required capability; repeat as needed")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        model_caps = json.loads(args.model_capabilities.read_text(encoding="utf-8")) if args.model_capabilities else None
        host_caps = json.loads(args.host_capabilities.read_text(encoding="utf-8")) if args.host_capabilities else None
        report = build_preflight_report(
            config,
            model_profile=args.model_profile,
            model_capabilities=model_caps,
            host_capabilities=host_caps,
            required_capabilities=args.require or None,
        )
        payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0 if report["selected_route"]["available"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
