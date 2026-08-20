#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Audit PowerPoint package size, media efficiency, and lightweight delivery risks."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import posixpath
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from PIL import Image


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}
EMU_PER_INCH = 914400
PROFILES = {
    "lightweight": {"max_factor": 2.2, "base_budget": 2_000_000, "extra_per_slide": 120_000},
    "balanced": {"max_factor": 2.7, "base_budget": 5_000_000, "extra_per_slide": 250_000},
    "high-fidelity": {"max_factor": 4.0, "base_budget": 12_000_000, "extra_per_slide": 500_000},
}


def resolve_part(base: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(base), target))


def relationship_part(part: str) -> str:
    return posixpath.join(posixpath.dirname(part), "_rels", posixpath.basename(part) + ".rels")


def slide_count(archive: zipfile.ZipFile) -> int:
    return sum(bool(re.fullmatch(r"ppt/slides/slide\d+\.xml", name)) for name in archive.namelist())


def all_media_references(archive: zipfile.ZipFile) -> set[str]:
    names = set(archive.namelist())
    referenced: set[str] = set()
    for rel_name in (name for name in names if name.endswith(".rels")):
        try:
            root = ET.fromstring(archive.read(rel_name))
        except ET.ParseError:
            continue
        source_dir = posixpath.dirname(posixpath.dirname(rel_name))
        source_name = posixpath.basename(rel_name)[:-5]
        base = posixpath.join(source_dir, source_name)
        for rel in root.findall("pr:Relationship", NS):
            target = resolve_part(base, rel.get("Target", ""))
            if target.startswith("ppt/media/"):
                referenced.add(target)
    return referenced


def placed_media_frames(archive: zipfile.ZipFile) -> dict[str, list[dict[str, Any]]]:
    names = set(archive.namelist())
    frames: dict[str, list[dict[str, Any]]] = defaultdict(list)
    candidate_parts = [
        name for name in names
        if re.fullmatch(r"ppt/(slides|slideLayouts|slideMasters)/[^/]+\.xml", name)
    ]
    for part in candidate_parts:
        rel_name = relationship_part(part)
        if rel_name not in names:
            continue
        try:
            root = ET.fromstring(archive.read(part))
            rel_root = ET.fromstring(archive.read(rel_name))
        except ET.ParseError:
            continue
        rels = {
            rel.get("Id"): resolve_part(part, rel.get("Target", ""))
            for rel in rel_root.findall("pr:Relationship", NS)
        }
        for picture in root.findall(".//p:pic", NS):
            blip = picture.find(".//a:blip", NS)
            ext = picture.find(".//a:xfrm/a:ext", NS)
            if blip is None or ext is None:
                continue
            media = rels.get(blip.get(f"{{{NS['r']}}}embed"))
            if not media or not media.startswith("ppt/media/"):
                continue
            width_px = int(ext.get("cx", "0")) / EMU_PER_INCH * 96
            height_px = int(ext.get("cy", "0")) / EMU_PER_INCH * 96
            if width_px > 0 and height_px > 0:
                frames[media].append({
                    "part": part,
                    "display_pixels_96dpi": [round(width_px), round(height_px)],
                })
    return frames


def chart_linked_workbooks(archive: zipfile.ZipFile) -> set[str]:
    """Return embedded workbooks referenced by native chart relationships."""
    names = set(archive.namelist())
    linked: set[str] = set()
    chart_parts = [name for name in names if re.fullmatch(r"ppt/charts/chart\d+\.xml", name)]
    for part in chart_parts:
        rel_name = relationship_part(part)
        if rel_name not in names:
            continue
        try:
            rel_root = ET.fromstring(archive.read(rel_name))
        except ET.ParseError:
            continue
        for rel in rel_root.findall("pr:Relationship", NS):
            if not rel.get("Type", "").endswith("/package"):
                continue
            target = resolve_part(part, rel.get("Target", ""))
            if target.startswith("ppt/embeddings/"):
                linked.add(target)
    return linked


def budget_for(slides: int, profile: str) -> int:
    settings = PROFILES[profile]
    return int(settings["base_budget"] + max(0, slides - 15) * settings["extra_per_slide"])


def inspect(pptx: Path, profile: str) -> dict[str, Any]:
    total_bytes = pptx.stat().st_size
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    with zipfile.ZipFile(pptx) as archive:
        names = set(archive.namelist())
        slides = slide_count(archive)
        frames = placed_media_frames(archive)
        referenced = all_media_references(archive)
        media_infos = [
            item for item in archive.infolist()
            if item.filename.startswith("ppt/media/") and not item.is_dir()
        ]
        media_names = {item.filename for item in media_infos}
        unused = sorted(media_names - referenced)
        if unused:
            blockers.append({"code": "UNUSED_MEDIA", "items": unused})

        hashes: dict[str, list[str]] = defaultdict(list)
        media: list[dict[str, Any]] = []
        media_compressed_bytes = 0
        for item in sorted(media_infos, key=lambda value: value.compress_size, reverse=True):
            data = archive.read(item)
            digest = hashlib.sha256(data).hexdigest()
            hashes[digest].append(item.filename)
            media_compressed_bytes += item.compress_size
            entry: dict[str, Any] = {
                "name": item.filename,
                "bytes": item.file_size,
                "zip_bytes": item.compress_size,
                "sha256": digest,
                "frames": frames.get(item.filename, []),
            }
            try:
                image = Image.open(io.BytesIO(data))
                entry.update({
                    "format": image.format,
                    "pixels": [image.width, image.height],
                    "mode": image.mode,
                    "has_alpha": "A" in image.mode and image.getchannel("A").getextrema()[0] < 255,
                })
                frame_factors = []
                for frame in entry["frames"]:
                    display_w, display_h = frame["display_pixels_96dpi"]
                    frame_factors.append(max(image.width / display_w, image.height / display_h))
                if frame_factors:
                    entry["maximum_resolution_factor"] = round(max(frame_factors), 2)
                    if max(frame_factors) > PROFILES[profile]["max_factor"]:
                        blockers.append({
                            "code": "RASTER_EXCEEDS_DISPLAY_NEED",
                            "item": item.filename,
                            "factor": round(max(frame_factors), 2),
                            "allowed": PROFILES[profile]["max_factor"],
                        })
                if profile == "lightweight" and image.format == "PNG" and not entry["has_alpha"] and item.file_size > 500_000:
                    warnings.append({
                        "code": "LARGE_OPAQUE_PNG",
                        "item": item.filename,
                        "bytes": item.file_size,
                    })
            except Exception as exc:  # keep non-raster media visible in the report
                entry["image_probe_error"] = str(exc)
            media.append(entry)

        duplicates = [items for items in hashes.values() if len(items) > 1]
        if duplicates:
            blockers.append({"code": "DUPLICATE_MEDIA", "groups": duplicates})

        font_parts = sorted(name for name in names if name.startswith("ppt/fonts/") and not name.endswith("/"))
        embedding_parts = sorted(
            name for name in names if name.startswith("ppt/embeddings/") and not name.endswith("/")
        )
        chart_workbook_parts = sorted(chart_linked_workbooks(archive))
        non_chart_embedding_parts = sorted(set(embedding_parts) - set(chart_workbook_parts))
        audio_video_parts = sorted(
            name for name in names
            if name.startswith("ppt/media/") and not name.endswith("/")
            and Path(name).suffix.lower() in {".mp3", ".wav", ".mp4", ".mov", ".avi", ".m4a"}
        )
        if profile == "lightweight" and font_parts:
            blockers.append({"code": "EMBEDDED_FONTS_IN_LIGHTWEIGHT", "items": font_parts})
        if profile == "lightweight" and (non_chart_embedding_parts or audio_video_parts):
            blockers.append({
                "code": "HEAVY_EMBEDDED_OBJECT_IN_LIGHTWEIGHT",
                "embeddings": non_chart_embedding_parts,
                "audio_video": audio_video_parts,
            })

        preferred_budget = budget_for(slides, profile)
        if total_bytes > preferred_budget:
            warnings.append({
                "code": "ABOVE_PREFERRED_TOTAL_SIZE",
                "actual_bytes": total_bytes,
                "preferred_budget_bytes": preferred_budget,
            })

    return {
        "contract_version": "1.0",
        "pptx": str(pptx),
        "pptx_sha256": hashlib.sha256(pptx.read_bytes()).hexdigest(),
        "delivery_profile": profile,
        "slide_count": slides,
        "total_bytes": total_bytes,
        "preferred_budget_bytes": preferred_budget,
        "media_zip_bytes": media_compressed_bytes,
        "media_share_of_file": round(media_compressed_bytes / total_bytes, 4) if total_bytes else 0,
        "embedded_font_parts": font_parts,
        "embedding_parts": embedding_parts,
        "chart_workbook_parts": chart_workbook_parts,
        "non_chart_embedding_parts": non_chart_embedding_parts,
        "audio_video_parts": audio_video_parts,
        "unused_media": unused,
        "duplicate_media_groups": duplicates,
        "media": media,
        "blockers": blockers,
        "warnings": warnings,
        "ok": not blockers,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--profile", choices=PROFILES, default="lightweight")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        report = inspect(args.pptx, args.profile)
    except (OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8")
    else:
        print(payload)
    print(
        f"{'PASS' if report['ok'] else 'FAILED'}: {report['total_bytes']} bytes, "
        f"{len(report['blockers'])} blocker(s), {len(report['warnings'])} warning(s)",
        file=sys.stderr,
    )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
