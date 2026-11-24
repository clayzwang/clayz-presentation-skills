#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Extract per-slide editable object inventory from a PowerPoint file."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def natural_key(value: str) -> list[Any]:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", value)]


def resolve_part(base: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    parts: list[str] = []
    for part in (PurePosixPath(base).parent / target).parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part not in (".", "/"):
            parts.append(part)
    return "/".join(parts)


def ordered_slide_parts(archive: zipfile.ZipFile) -> list[str]:
    names = set(archive.namelist())
    presentation = "ppt/presentation.xml"
    rels_name = "ppt/_rels/presentation.xml.rels"
    if presentation not in names or rels_name not in names:
        return sorted(
            (name for name in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)),
            key=natural_key,
        )
    root = ET.fromstring(archive.read(presentation))
    rels = ET.fromstring(archive.read(rels_name))
    targets = {
        rel.get("Id"): resolve_part(presentation, rel.get("Target", ""))
        for rel in rels.findall("pr:Relationship", NS)
    }
    ordered: list[str] = []
    for slide_id in root.findall(".//p:sldIdLst/p:sldId", NS):
        part = targets.get(slide_id.get(f"{{{NS['r']}}}id"))
        if part in names:
            ordered.append(part)
    return ordered


def inspect_slide(xml_bytes: bytes) -> dict[str, Any]:
    root = ET.fromstring(xml_bytes)
    shapes = root.findall(".//p:sp", NS)
    graphic_frames = root.findall(".//p:graphicFrame", NS)
    names = [
        item.get("name", "")
        for item in root.findall(".//p:cNvPr", NS)
        if item.get("name")
    ]
    text_shapes = sum(1 for shape in shapes if shape.findall(".//a:t", NS))
    tables = 0
    charts = 0
    diagrams = 0
    for frame in graphic_frames:
        for data in frame.findall(".//a:graphicData", NS):
            uri = (data.get("uri") or "").lower()
            if data.find("a:tbl", NS) is not None or uri.endswith("/table"):
                tables += 1
            if "drawingml/2006/chart" in uri:
                charts += 1
            if "drawingml/2006/diagram" in uri:
                diagrams += 1
    return {
        "shapes": len(shapes),
        "text_shapes": text_shapes,
        "connectors": len(root.findall(".//p:cxnSp", NS)),
        "pictures": len(root.findall(".//p:pic", NS)),
        "graphic_frames": len(graphic_frames),
        "tables": tables,
        "charts": charts,
        "diagrams": diagrams,
        "named_copy_targets": sorted(name for name in names if name.startswith("COPY::")),
    }


def load_plan(path: Path | None) -> dict[str, Any] | None:
    return json.loads(path.read_text(encoding="utf-8")) if path else None


def build_report(pptx: Path, plan: dict[str, Any] | None) -> dict[str, Any]:
    with zipfile.ZipFile(pptx) as archive:
        parts = ordered_slide_parts(archive)
        inventories = [inspect_slide(archive.read(part)) for part in parts]
        names = set(archive.namelist())
        media_infos = [item for item in archive.infolist() if item.filename.startswith("ppt/media/")]
        digest_groups: dict[str, list[str]] = {}
        for item in media_infos:
            digest = hashlib.sha256(archive.read(item)).hexdigest()
            digest_groups.setdefault(digest, []).append(item.filename)
        duplicate_groups = [items for items in digest_groups.values() if len(items) > 1]
        package_media = {
            "pptx_sha256": hashlib.sha256(pptx.read_bytes()).hexdigest(),
            "total_bytes": pptx.stat().st_size,
            "media_count": len(media_infos),
            "media_zip_bytes": sum(item.compress_size for item in media_infos),
            "duplicate_media_groups": duplicate_groups,
            "embedded_font_parts": sorted(name for name in names if name.startswith("ppt/fonts/")),
            "embedding_parts": sorted(name for name in names if name.startswith("ppt/embeddings/")),
            "audio_video_parts": sorted(
                name for name in names
                if name.startswith("ppt/media/") and Path(name).suffix.lower() in {".mp3", ".wav", ".mp4", ".mov", ".avi", ".m4a"}
            ),
        }
    plan_slides = plan.get("slides", []) if isinstance(plan, dict) else []
    if plan and len(plan_slides) != len(inventories):
        raise ValueError(f"plan has {len(plan_slides)} slides but PPTX has {len(inventories)} slides")
    slides = []
    for index, inventory in enumerate(inventories):
        planned = plan_slides[index] if plan else {}
        target_counts = Counter(
            item.get("target_type")
            for item in planned.get("copy_unit_map", [])
            if isinstance(item, dict)
        )
        slides.append({
            "slide_index": index + 1,
            "slide_id": planned.get("slide_id", f"slide-{index + 1}"),
            "planned_medium": planned.get("dominant_medium") if plan else None,
            "planned_structure": planned.get("structure_signature") if plan else None,
            "planned_structure_type": planned.get("medium_execution_contract", {}).get("structure_type") if plan else None,
            "required_object_types": planned.get("medium_execution_contract", {}).get("required_object_types", []) if plan else [],
            "minimum_object_counts": planned.get("medium_execution_contract", {}).get("minimum_object_counts", {}) if plan else {},
            "target_type_counts": {
                "shape": target_counts.get("shape", 0),
                "table-cell": target_counts.get("table-cell", 0),
                "chart-label": target_counts.get("chart-label", 0),
            },
            "inventory": inventory,
        })
    return {
        "contract_version": "1.0",
        "pptx": str(pptx),
        "package_id": plan.get("package_id") if plan else None,
        "package_version": plan.get("package_version") if plan else None,
        "slide_count": len(slides),
        "package_media": package_media,
        "slides": slides,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        plan = load_plan(args.plan)
        report = build_report(args.pptx, plan)
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8")
    else:
        print(payload)
    print(f"PASS: inspected {report['slide_count']} slide(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
