#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Audit rendered slide images for repetitive silhouettes and accent-color bands."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageFilter, ImageStat

from config_policy import ValidationPolicy, load_policy

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def pixels(image: Image.Image) -> list[Any]:
    getter = getattr(image, "get_flattened_data", None)
    return list(getter() if getter else image.getdata())


def natural_key(path: Path) -> list[Any]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


def content_crop(image: Image.Image) -> Image.Image:
    width, height = image.size
    return image.crop((int(width * 0.035), int(height * 0.17), int(width * 0.965), int(height * 0.91)))


def color_distance(pixel: tuple[int, int, int], target: tuple[int, int, int]) -> float:
    return math.sqrt(sum((value - expected) ** 2 for value, expected in zip(pixel, target)))


def feature_vector(image: Image.Image, policy: ValidationPolicy) -> list[float]:
    crop = content_crop(image.convert("RGB")).resize((40, 24), Image.Resampling.LANCZOS)
    gray = crop.convert("L")
    white = Image.new("L", gray.size, 255)
    ink = ImageChops.difference(gray, white).point(lambda value: 255 if value > 14 else 0)
    edges = gray.filter(ImageFilter.FIND_EDGES).point(lambda value: 255 if value > 22 else 0)
    rgb = pixels(crop)
    ink_values = [value / 255.0 for value in pixels(ink)]
    edge_values = [value / 255.0 for value in pixels(edges)]
    accent_values = [
        1.0 if color_distance(pixel, policy.accent_rgb) <= policy.accent_distance else 0.0
        for pixel in rgb
    ]
    return ink_values + [value * 0.6 for value in edge_values] + [value * 0.8 for value in accent_values]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 1.0 if left_norm == right_norm else 0.0
    return dot / (left_norm * right_norm)


def has_bottom_accent_band(image: Image.Image, policy: ValidationPolicy) -> bool:
    crop = content_crop(image.convert("RGB"))
    width, height = crop.size
    bottom = crop.crop((0, int(height * 0.68), width, height)).resize((80, 32), Image.Resampling.BILINEAR)
    rows: list[float] = []
    bottom_pixels = pixels(bottom)
    for row in range(bottom.height):
        hits = 0
        for pixel in bottom_pixels[row * bottom.width:(row + 1) * bottom.width]:
            if color_distance(pixel, policy.accent_rgb) <= policy.accent_distance:
                hits += 1
        rows.append(hits / bottom.width)
    longest = current = 0
    for share in rows:
        if share >= 0.62:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest >= 2


def load_plan(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("render_dir", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--similarity-threshold", type=float, default=0.965)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    policy = load_policy(args.config)

    files = sorted(
        [path for path in args.render_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES],
        key=natural_key,
    )
    if len(files) < 3:
        print("FAIL: render directory must contain at least 3 slide images", file=sys.stderr)
        return 2

    images = [Image.open(path).convert("RGB") for path in files]
    vectors = [feature_vector(image, policy) for image in images]
    adjacent = [cosine_similarity(vectors[index], vectors[index + 1]) for index in range(len(vectors) - 1)]
    bottom_bands = [has_bottom_accent_band(image, policy) for image in images]
    plan = load_plan(args.plan)
    slide_ids = [f"slide-{index + 1}" for index in range(len(files))]
    series_ids: list[str | None] = [None for _ in files]
    series_behaviors = ["standalone" for _ in files]
    repetition_reasons = ["" for _ in files]
    max_bottom_share = 0.35
    if plan:
        plan_slides = plan.get("slides", [])
        if len(plan_slides) != len(files):
            print(f"FAIL: plan has {len(plan_slides)} slides but render directory has {len(files)} images", file=sys.stderr)
            return 2
        slide_ids = [str(slide.get("slide_id", slide_ids[index])) for index, slide in enumerate(plan_slides)]
        series_contracts = [slide.get("series_visual_contract", {}) for slide in plan_slides]
        series_ids = [item.get("series_id") if isinstance(item, dict) else None for item in series_contracts]
        series_behaviors = [item.get("behavior", "standalone") if isinstance(item, dict) else "standalone" for item in series_contracts]
        repetition_reasons = [str(slide.get("repetition_reason", "")).strip() for slide in plan_slides]
        rhythm = plan.get("deck_rhythm", {})
        if isinstance(rhythm.get("max_bottom_conclusion_band_share"), (int, float)):
            max_bottom_share = float(rhythm["max_bottom_conclusion_band_share"])

    body_range = range(1, len(files) - 1)
    warnings: list[str] = []
    errors: list[str] = []
    high_pairs = []
    purposeful_pairs = []
    for index, score in enumerate(adjacent):
        if index == 0 or index + 1 == len(files) - 1:
            continue
        if score >= args.similarity_threshold:
            high_pairs.append({"slides": [slide_ids[index], slide_ids[index + 1]], "similarity": round(score, 4)})
            purposeful = (
                series_ids[index] is not None
                and series_ids[index] == series_ids[index + 1]
                and series_behaviors[index] in {"locked-backbone", "controlled-variation"}
                and series_behaviors[index + 1] in {"locked-backbone", "controlled-variation"}
                and repetition_reasons[index]
                and repetition_reasons[index + 1]
            )
            if purposeful:
                purposeful_pairs.append({
                    "slides": [slide_ids[index], slide_ids[index + 1]],
                    "series_id": series_ids[index],
                    "similarity": round(score, 4),
                })
            else:
                warnings.append(
                    f"high adjacent silhouette similarity {score:.3f}: {slide_ids[index]} and {slide_ids[index + 1]}"
                )

    for index in range(1, len(files) - 3):
        if adjacent[index] >= args.similarity_threshold and adjacent[index + 1] >= args.similarity_threshold:
            ids = slide_ids[index:index + 3]
            shared_series = {series_ids[pos] for pos in range(index, index + 3)}
            purposeful = (
                None not in shared_series
                and len(shared_series) == 1
                and all(series_behaviors[pos] in {"locked-backbone", "controlled-variation"} for pos in range(index, index + 3))
                and all(repetition_reasons[pos] for pos in range(index, index + 3))
            )
            if not purposeful:
                errors.append(f"three-slide repetitive silhouette run: {ids}")

    body_bands = [bottom_bands[index] for index in body_range]
    band_count = sum(body_bands)
    if body_bands and band_count / len(body_bands) > max_bottom_share + 1e-9:
        errors.append(
            f"detected bottom accent bands on {band_count}/{len(body_bands)} body slides, above {max_bottom_share:.0%}"
        )
    for index in range(1, len(files) - 3):
        if all(bottom_bands[index:index + 3]):
            errors.append(f"bottom accent band detected on 3 consecutive slides: {slide_ids[index:index + 3]}")

    report = {
        "slide_count": len(files),
        "similarity_threshold": args.similarity_threshold,
        "adjacent_similarity": [round(score, 4) for score in adjacent],
        "high_similarity_pairs": high_pairs,
        "purposeful_series_similarity_pairs": purposeful_pairs,
        "bottom_accent_band": dict(zip(slide_ids, bottom_bands)),
        "warnings": warnings,
        "errors": errors,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    for warning in warnings:
        print(f"WARN: {warning}")
    if errors:
        print(f"FAIL: {len(errors)} visual-rhythm error(s)", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"PASS: visual rhythm audit completed for {len(files)} slides with {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
