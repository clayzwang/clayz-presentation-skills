#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Compare locked copy and Art Direction execution requirements with final PPTX objects."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from validate_art_direction_plan import validate_plan


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}


def natural_slide_key(name: str) -> int:
    match = re.search(r"slide(\d+)\.xml$", name)
    return int(match.group(1)) if match else 10**9


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text).casefold()


def intentional_segments(text: str, breaks: list[int]) -> list[str]:
    starts = [0] + sorted(breaks)
    ends = sorted(breaks) + [len(text)]
    return [text[start:end] for start, end in zip(starts, ends) if text[start:end]]


def element_paragraphs(element: ET.Element) -> list[str]:
    paragraphs: list[str] = []
    for paragraph in element.findall(".//a:p", NS):
        value = "".join(node.text or "" for node in paragraph.findall(".//a:t", NS)).strip()
        if value:
            paragraphs.append(value)
    return paragraphs


def extract_slide(xml_bytes: bytes) -> tuple[dict[str, list[str]], list[str], dict[str, int]]:
    root = ET.fromstring(xml_bytes)
    named: dict[str, list[str]] = {}
    all_paragraphs: list[str] = []
    for shape in root.findall(".//p:sp", NS):
        c_nv_pr = shape.find("./p:nvSpPr/p:cNvPr", NS)
        name = c_nv_pr.get("name", "") if c_nv_pr is not None else ""
        paragraphs = element_paragraphs(shape)
        all_paragraphs.extend(paragraphs)
        if name:
            named[name] = paragraphs
    for frame in root.findall(".//p:graphicFrame", NS):
        paragraphs = element_paragraphs(frame)
        all_paragraphs.extend(paragraphs)
    tables = charts = diagrams = 0
    for data in root.findall(".//a:graphicData", NS):
        uri = (data.get("uri") or "").lower()
        if data.find("a:tbl", NS) is not None or uri.endswith("/table"):
            tables += 1
        if "drawingml/2006/chart" in uri:
            charts += 1
        if "drawingml/2006/diagram" in uri:
            diagrams += 1
    inventory = {
        "shape": len(root.findall(".//p:sp", NS)),
        "native-table": tables,
        "native-chart": charts,
        "connector": len(root.findall(".//p:cxnSp", NS)),
        "picture": len(root.findall(".//p:pic", NS)),
        "diagram": diagrams,
    }
    return named, all_paragraphs, inventory


def compare(package: Any, plan: Any, pptx: Path, allow_extra_text: bool = False) -> list[str]:
    errors = validate_plan(package, plan)
    if errors or not isinstance(package, dict) or not isinstance(plan, dict):
        return errors
    try:
        with zipfile.ZipFile(pptx) as archive:
            slide_names = sorted(
                [name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)],
                key=natural_slide_key,
            )
            extracted = [extract_slide(archive.read(name)) for name in slide_names]
    except (OSError, zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        return [f"pptx: cannot inspect file: {exc}"]

    logic_slides = package["logic_layer"]["slides"]
    copy_slides = package["copy_layer"]["slides"]
    plan_slides = plan["slides"]
    if len(extracted) != len(copy_slides):
        errors.append(f"pptx: expected {len(copy_slides)} slides, found {len(extracted)}")

    for index, (logic_slide, copy_slide, slide_plan, actual) in enumerate(zip(logic_slides, copy_slides, plan_slides, extracted), start=1):
        named, paragraphs, inventory = actual
        units = {unit["copy_id"]: unit for unit in copy_slide["copy_units"]}
        plan_map = {item["copy_id"]: item for item in slide_plan["copy_unit_map"]}
        normalized_paragraphs = [normalize(value) for value in paragraphs]
        allowed_paragraphs = {
            normalize(segment)
            for unit in units.values()
            for segment in intentional_segments(unit["text"], unit.get("intentional_line_breaks", []))
        }
        expected_shape_names: set[str] = set()

        medium = slide_plan["medium_execution_contract"]
        for object_type, minimum in medium["minimum_object_counts"].items():
            actual_count = inventory.get(object_type, 0)
            if actual_count < minimum:
                errors.append(
                    f"slide {index}: medium execution requires at least {minimum} {object_type} object(s), found {actual_count}"
                )

        for copy_id, unit in units.items():
            mapping = plan_map[copy_id]
            expected_text = normalize(unit["text"])
            method = mapping["verification_method"]
            if method == "shape-name":
                shape_name = f"COPY::{copy_id}"
                expected_shape_names.add(shape_name)
                matches = [name for name in named if name == shape_name]
                if len(matches) != 1:
                    errors.append(f"slide {index} {copy_id}: expected exactly one shape named {shape_name}")
                else:
                    actual_text = normalize("".join(named[shape_name]))
                    if actual_text != expected_text:
                        errors.append(f"slide {index} {copy_id}: named shape text differs from locked copy")
            elif method == "paragraph-exact":
                if normalized_paragraphs.count(expected_text) != 1:
                    errors.append(f"slide {index} {copy_id}: expected exactly one matching paragraph")

        copy_shape_names = [name for name in named if name.startswith("COPY::")]
        if len(copy_shape_names) != len(set(copy_shape_names)):
            errors.append(f"slide {index}: duplicate COPY shape names")
        unexpected_names = set(copy_shape_names) - expected_shape_names
        if unexpected_names:
            errors.append(f"slide {index}: unexpected COPY shape names {sorted(unexpected_names)}")

        node_primary = {item["logic_node_id"]: item["primary_copy_id"] for item in copy_slide["node_copy_map"]}
        node_map = {node["node_id"]: node for node in logic_slide["page_message_tree"]["nodes"]}
        for node_id, node in node_map.items():
            parent_id = node.get("parent_node_id")
            if not parent_id:
                continue
            parent_copy = units[node_primary[parent_id]]["text"]
            child_copy = units[node_primary[node_id]]["text"]
            parent_norm = normalize(parent_copy)
            child_norm = normalize(child_copy)
            for paragraph, paragraph_norm in zip(paragraphs, normalized_paragraphs):
                if parent_norm and child_norm and parent_norm in paragraph_norm and child_norm in paragraph_norm and paragraph_norm not in {parent_norm, child_norm}:
                    errors.append(f"slide {index}: parent {node_primary[parent_id]} and child {node_primary[node_id]} are flattened in one paragraph: {paragraph!r}")
                    break

        if not allow_extra_text:
            extras = sorted({paragraph for paragraph, value in zip(paragraphs, normalized_paragraphs) if value not in allowed_paragraphs})
            if extras:
                errors.append(f"slide {index}: extra visible text not found in Copy layer: {extras}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--allow-extra-text", action="store_true", help="diagnostic escape hatch; do not use for final delivery")
    args = parser.parse_args()
    try:
        package = json.loads(args.package.read_text(encoding="utf-8"))
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        errors = compare(package, plan, args.pptx, args.allow_extra_text)
    except (OSError, json.JSONDecodeError, FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAILED: {len(errors)} error(s)")
        return 1
    print(f"PASS: PPTX copy fidelity {args.pptx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
