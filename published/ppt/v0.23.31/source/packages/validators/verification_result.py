#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Scoped diagnostics without conflating a tool failure with artifact quality."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable


class Issue(str):
    """Remain compatible with existing list-of-string validator APIs."""

    def __new__(cls, message: str, category: str = "record"):
        if category not in {"record", "quality", "coverage", "tool"}:
            raise ValueError(f"unknown verification category: {category}")
        value = super().__new__(cls, message)
        value.category = category
        return value


class Issues(list):
    def __init__(self, category: str):
        super().__init__()
        self.category = category

    def append(self, value):
        super().append(value if isinstance(value, Issue) else Issue(value, self.category))

    def extend(self, values: Iterable[str]):
        for value in values:
            self.append(value)


def result(tool: str, errors: Iterable[str], *, quality_checked: bool = False,
           execution: str = "completed") -> dict:
    errors = list(errors)
    groups = {kind: [] for kind in ("record", "quality", "coverage", "tool")}
    for error in errors:
        groups[getattr(error, "category", "record")].append(str(error))
    if groups["tool"]:
        execution = "error"
    record = "invalid" if groups["record"] else "unverified" if execution != "completed" else "valid"
    quality = ("fail" if groups["quality"] else "unverified"
               if execution != "completed" or record != "valid" or groups["coverage"] or not quality_checked
               else "pass")
    return {
        "contract": "io.clayz.presentation.verification-result/1.0",
        "tool": tool,
        "ok": not errors and execution == "completed",
        "execution_status": execution,
        "record_status": record,
        "quality_status": quality,
        "errors": [str(error) for error in errors],
        "record_errors": groups["record"],
        "quality_findings": groups["quality"],
        "coverage_gaps": groups["coverage"],
        "tool_errors": groups["tool"],
    }


def finish(tool: str, errors: Iterable[str], path: Path | None = None, *,
           quality_checked: bool = False, execution: str = "completed",
           success: str = "PASS") -> int:
    report = result(tool, errors, quality_checked=quality_checked, execution=execution)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for error in report["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)
    if report["ok"]:
        print(success)
    else:
        print(f"FAILED: execution={report['execution_status']}; record={report['record_status']}; quality={report['quality_status']}")
    return 2 if report["execution_status"] != "completed" else 0 if report["ok"] else 1


def exception_result(tool: str, exc: Exception, path: Path | None = None) -> int:
    # Invalid or missing input is not evidence of a bad page or a validator bug.
    category = "record" if isinstance(exc, (json.JSONDecodeError, FileNotFoundError)) else "tool"
    return finish(tool, [Issue(f"{type(exc).__name__}: {exc}", category)], path,
                  execution="not-run" if category == "record" else "error")
