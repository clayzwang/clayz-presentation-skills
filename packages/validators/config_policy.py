#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Load presentation validation policy from the repository's central config."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "default.json"


@dataclass(frozen=True)
class ValidationPolicy:
    body_minimum_pt: float
    audience_minimum_pt: float
    chart_minimum_pt: float
    prefer_even_point_sizes: bool
    allow_fractional_point_sizes: bool
    minimum_exception_policy: str
    column_count: int
    accent_rgb: tuple[int, int, int]
    accent_distance: float

    def size_conforms(self, value: Any) -> bool:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False
        numeric = float(value)
        if not self.allow_fractional_point_sizes and not numeric.is_integer():
            return False
        if self.prefer_even_point_sizes and (not numeric.is_integer() or int(numeric) % 2):
            return False
        return True


def _hex_rgb(value: str) -> tuple[int, int, int]:
    normalized = value.strip().lstrip("#")
    if len(normalized) != 6:
        raise ValueError("theme.colors.accent must be a six-digit hex color")
    return tuple(int(normalized[index:index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]


def load_config(path: Path | None = None) -> dict[str, Any]:
    config_path = (path or DEFAULT_CONFIG).resolve()
    return json.loads(config_path.read_text(encoding="utf-8"))


def load_policy(path: Path | None = None) -> ValidationPolicy:
    config = load_config(path)
    typography = config["theme"]["typography"]
    layout = config["layout"]
    accent_detection = config.get("qa", {}).get("accent_band_detection", {})
    return ValidationPolicy(
        body_minimum_pt=float(typography["body_minimum_pt"]),
        audience_minimum_pt=float(typography["minimum_audience_text_pt"]),
        chart_minimum_pt=float(typography["minimum_chart_text_pt"]),
        prefer_even_point_sizes=bool(typography["prefer_even_point_sizes"]),
        allow_fractional_point_sizes=bool(typography["allow_fractional_point_sizes"]),
        minimum_exception_policy=str(typography["minimum_exception_policy"]),
        column_count=int(layout["column_count"]),
        accent_rgb=_hex_rgb(config["theme"]["colors"]["accent"]),
        accent_distance=float(accent_detection.get("rgb_distance", 52.0)),
    )
