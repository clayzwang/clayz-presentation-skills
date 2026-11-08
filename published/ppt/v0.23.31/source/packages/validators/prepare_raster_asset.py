#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Prepare one raster image for a PowerPoint display frame."""

from __future__ import annotations

import argparse
import io
import json
import math
import sys
from pathlib import Path

from PIL import Image


PROFILES = {
    "lightweight": {"scale": 1.75, "jpeg_quality": 86, "max_long_edge": 1600},
    "balanced": {"scale": 2.0, "jpeg_quality": 90, "max_long_edge": 2200},
    "high-fidelity": {"scale": 2.5, "jpeg_quality": 94, "max_long_edge": 3200},
}
ROLES = {"auto", "photo", "background", "illustration", "screenshot", "line-art", "qr"}


def parse_hex_color(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) != 6:
        raise ValueError("matte must be a six-digit hex color")
    return tuple(int(text[index:index + 2], 16) for index in (0, 2, 4))


def has_real_alpha(image: Image.Image) -> bool:
    if "A" not in image.mode:
        return False
    return image.getchannel("A").getextrema()[0] < 255


def target_size(
    width: int,
    height: int,
    placed_width_in: float | None,
    placed_height_in: float | None,
    profile: dict[str, float | int],
) -> tuple[int, int]:
    if placed_width_in and placed_height_in:
        frame_w = placed_width_in * 96 * float(profile["scale"])
        frame_h = placed_height_in * 96 * float(profile["scale"])
        cover_scale = max(frame_w / width, frame_h / height)
        scale = min(1.0, cover_scale)
    else:
        scale = min(1.0, float(profile["max_long_edge"]) / max(width, height))
    return max(1, round(width * scale)), max(1, round(height * scale))


def choose_role(requested: str, alpha: bool) -> str:
    if requested != "auto":
        return requested
    return "illustration" if alpha else "photo"


def prepare(args: argparse.Namespace) -> dict[str, object]:
    profile = PROFILES[args.profile]
    source = Image.open(args.input)
    source.load()
    source_bytes = args.input.stat().st_size
    alpha = has_real_alpha(source)
    role = choose_role(args.role, alpha)
    resized_to = target_size(
        source.width,
        source.height,
        args.placed_width_in,
        args.placed_height_in,
        profile,
    )
    image = source.resize(resized_to, Image.Resampling.LANCZOS) if source.size != resized_to else source.copy()

    screenshot_like = role in {"screenshot", "line-art", "qr"}
    matte = parse_hex_color(args.matte) if args.matte else None
    use_jpeg = not screenshot_like and (not alpha or matte is not None) and role in {"photo", "background"}

    requested_output = args.output
    if use_jpeg:
        output = requested_output.with_suffix(".jpg")
        if alpha:
            rgba = image.convert("RGBA")
            base = Image.new("RGB", rgba.size, matte or (255, 255, 255))
            base.paste(rgba, mask=rgba.getchannel("A"))
            image = base
        else:
            image = image.convert("RGB")
        save_kwargs = {
            "format": "JPEG",
            "quality": int(profile["jpeg_quality"]),
            "optimize": True,
            "progressive": True,
            "subsampling": 0,
        }
        output_format = "JPEG"
        quantized = False
    else:
        output = requested_output.with_suffix(".png")
        quantized = args.profile == "lightweight" and role == "illustration" and not args.keep_truecolor
        if quantized:
            image = image.convert("RGBA").quantize(
                colors=256,
                method=Image.Quantize.FASTOCTREE,
                dither=Image.Dither.FLOYDSTEINBERG,
            )
        save_kwargs = {"format": "PNG", "optimize": True, "compress_level": 9}
        output_format = "PNG"

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, **save_kwargs)
    output_bytes = output.stat().st_size
    report = {
        "contract_version": "1.0",
        "profile": args.profile,
        "role": role,
        "input": str(args.input),
        "output": str(output),
        "source_pixels": [source.width, source.height],
        "output_pixels": list(resized_to),
        "source_bytes": source_bytes,
        "output_bytes": output_bytes,
        "reduction_ratio": round(1 - output_bytes / source_bytes, 4) if source_bytes else 0,
        "source_has_transparency": alpha,
        "output_format": output_format,
        "palette_quantized": quantized,
        "visual_review_required": True,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, help="Output stem; extension is selected automatically")
    parser.add_argument("--profile", choices=PROFILES, default="lightweight")
    parser.add_argument("--role", choices=ROLES, default="auto")
    parser.add_argument("--placed-width-in", type=float)
    parser.add_argument("--placed-height-in", type=float)
    parser.add_argument("--matte", help="Six-digit matte color used only when flattening transparency")
    parser.add_argument("--keep-truecolor", action="store_true", help="Keep a transparent illustration as true-color PNG")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if (args.placed_width_in is None) != (args.placed_height_in is None):
        parser.error("placed width and height must be supplied together")
    if args.placed_width_in is not None and (args.placed_width_in <= 0 or args.placed_height_in <= 0):
        parser.error("placed width and height must be positive")
    try:
        report = prepare(args)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
