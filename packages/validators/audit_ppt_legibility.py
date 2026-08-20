#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Audit explicit audience font sizes and scatter-series line behavior in a PPTX."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from config_policy import ValidationPolicy, load_policy

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def natural_slide_key(name: str) -> int:
    match = re.search(r"slide(\d+)\.xml$", name)
    return int(match.group(1)) if match else 10**9


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_xml(archive: zipfile.ZipFile, name: str) -> ET.Element:
    return ET.fromstring(archive.read(name))


def explicit_font_sizes(root: ET.Element, part: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, node in enumerate(root.iter()):
        if local_name(node.tag) not in {"rPr", "defRPr", "endParaRPr"}:
            continue
        raw = node.get("sz")
        if raw is None:
            continue
        try:
            points = int(raw) / 100
        except ValueError:
            continue
        records.append({"part": part, "property_index": index, "points": points})
    return records


def slide_chart_parts(archive: zipfile.ZipFile, slide_name: str) -> list[str]:
    base = posixpath.basename(slide_name)
    rel_name = posixpath.join(posixpath.dirname(slide_name), "_rels", f"{base}.rels")
    if rel_name not in archive.namelist():
        return []
    root = parse_xml(archive, rel_name)
    parts: list[str] = []
    for rel in root.findall("pr:Relationship", NS):
        if not rel.get("Type", "").endswith("/chart"):
            continue
        target = rel.get("Target", "")
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(slide_name), target)).lstrip("/")
        if resolved in archive.namelist():
            parts.append(resolved)
    return parts


def scatter_details(root: ET.Element, part: str) -> dict[str, Any] | None:
    charts = root.findall(".//c:scatterChart", NS)
    if not charts:
        return None
    series_count = 0
    line_bearing_series = 0
    data_labels_present = False
    point_count = 0
    for chart in charts:
        if chart.find("c:dLbls", NS) is not None:
            data_labels_present = True
        for series in chart.findall("c:ser", NS):
            series_count += 1
            line = series.find("c:spPr/a:ln", NS)
            if line is None or line.find("a:noFill", NS) is None:
                line_bearing_series += 1
            counts = []
            for path in (
                "c:xVal/c:numRef/c:numCache/c:ptCount",
                "c:yVal/c:numRef/c:numCache/c:ptCount",
                "c:xVal/c:numLit/c:ptCount",
                "c:yVal/c:numLit/c:ptCount",
            ):
                node = series.find(path, NS)
                if node is not None and node.get("val", "").isdigit():
                    counts.append(int(node.get("val", "0")))
            if counts:
                point_count += min(counts)
    return {
        "part": part,
        "series_count": series_count,
        "point_count_from_cache": point_count,
        "line_bearing_series_count": line_bearing_series,
        "native_data_labels_present": data_labels_present,
        "manual_render_review_required": True,
    }


def plan_context(
    plan: dict[str, Any] | None,
    index: int,
    policy: ValidationPolicy,
) -> tuple[float, float, dict[str, Any] | None]:
    audience_min = policy.audience_minimum_pt
    chart_min = policy.chart_minimum_pt
    chart_contract = None
    if not isinstance(plan, dict):
        return audience_min, chart_min, chart_contract
    typography = plan.get("typography_contract", {})
    if isinstance(typography, dict):
        audience_min = float(typography.get("audience_detail_min_pt", audience_min))
        chart_min = float(typography.get("chart_text_min_pt", chart_min))
    slides = plan.get("slides", [])
    if index < len(slides) and isinstance(slides[index], dict):
        medium = slides[index].get("medium_execution_contract", {})
        if isinstance(medium, dict) and isinstance(medium.get("data_chart_contract"), dict):
            chart_contract = medium["data_chart_contract"]
            chart_min = float(chart_contract.get("audience_text_min_pt", chart_min))
    return audience_min, chart_min, chart_contract


def audit(pptx: Path, plan: dict[str, Any] | None, policy: ValidationPolicy | None = None) -> dict[str, Any]:
    policy = policy or load_policy()
    slides: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    with zipfile.ZipFile(pptx) as archive:
        slide_names = sorted(
            [name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)],
            key=natural_slide_key,
        )
        for index, slide_name in enumerate(slide_names):
            audience_min, chart_min, chart_contract = plan_context(plan, index, policy)
            size_records = explicit_font_sizes(parse_xml(archive, slide_name), slide_name)
            scatter_records = []
            for chart_part in slide_chart_parts(archive, slide_name):
                chart_root = parse_xml(archive, chart_part)
                size_records.extend(explicit_font_sizes(chart_root, chart_part))
                scatter = scatter_details(chart_root, chart_part)
                if scatter:
                    scatter_records.append(scatter)

            below = [
                item for item in size_records
                if item["points"] < (chart_min if "/charts/" in item["part"] else audience_min)
            ]
            nonconforming = [
                item for item in size_records
                if not policy.size_conforms(item["points"])
            ]
            slide_errors = []
            if below:
                slide_errors.append(f"{len(below)} explicit audience font properties below {audience_min}pt")
            if nonconforming:
                slide_errors.append(f"{len(nonconforming)} explicit font properties violate configured size-token policy")

            expected_scatter = isinstance(chart_contract, dict) and chart_contract.get("chart_type") == "scatter"
            if expected_scatter and not scatter_records:
                slide_errors.append("Art Direction expects scatter, but no native scatterChart was found")
            if scatter_records and isinstance(chart_contract, dict):
                policy = chart_contract.get("point_connection_policy")
                line_count = sum(item["line_bearing_series_count"] for item in scatter_records)
                if policy == "markers-only" and line_count:
                    slide_errors.append(f"markers-only scatter has {line_count} line-bearing series")
                if policy == "semantic-lines-only" and line_count > len(chart_contract.get("semantic_lines", [])):
                    warnings.append(
                        f"slide {index + 1}: line-bearing scatter series exceed declared semantic lines; review rendered line semantics"
                    )
            if scatter_records:
                warnings.append(
                    f"slide {index + 1}: direct institution-label completeness and collisions require full-size render review"
                )

            if not size_records:
                warnings.append(f"slide {index + 1}: no explicit slide/chart font sizes found; inspect inherited sizes manually")
            if slide_errors:
                errors.extend(f"slide {index + 1}: {message}" for message in slide_errors)
            sizes = sorted({item["points"] for item in size_records})
            slides.append({
                "slide_index": index + 1,
                "slide_part": slide_name,
                "audience_text_minimum_required_pt": audience_min,
                "chart_text_minimum_required_pt": chart_min,
                "explicit_font_sizes_pt": sizes,
                "minimum_explicit_font_pt": min(sizes) if sizes else None,
                "below_minimum_items": below,
                "nonconforming_size_items": nonconforming,
                "scatter_charts": scatter_records,
                "errors": slide_errors,
            })
    return {
        "contract_version": "1.0",
        "pptx": str(pptx),
        "plan_contract_version": plan.get("contract_version") if isinstance(plan, dict) else None,
        "status": "fail" if errors else "pass",
        "errors": errors,
        "warnings": warnings,
        "slides": slides,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8")) if args.plan else None
        report = audit(args.pptx, plan, load_policy(args.config))
    except (OSError, zipfile.BadZipFile, ET.ParseError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
