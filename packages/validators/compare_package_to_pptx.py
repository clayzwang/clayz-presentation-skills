#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Compare locked copy and Art Direction execution requirements with final PPTX objects."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import posixpath
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from validate_art_direction_plan import validate_plan
from verification_result import Issue, Issues, exception_result, finish


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
            if name in named:
                raise ValueError(f"duplicate shape name: {name}")
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


def native_text_body(element: ET.Element) -> str:
    """Canonical character offsets, preserving spaces and native soft breaks."""
    paragraphs = []
    for paragraph in element.findall(".//a:p", NS):
        paragraphs.append("".join("\n" if node.tag == f"{{{NS['a']}}}br" else node.text or ""
                                  for node in paragraph.iter()
                                  if node.tag in {f"{{{NS['a']}}}t", f"{{{NS['a']}}}br"}))
    return "\n".join(paragraphs)


def text_locations(xml_bytes: bytes, preserve_offsets: bool = False) -> dict[str, str]:
    """Text bodies and native table cells, never a whole-slide substring search.

    Table coordinates are zero based and stable within the named frame.
    """
    root = ET.fromstring(xml_bytes)
    result = {}
    for index, shape in enumerate(root.findall(".//p:sp", NS)):
        props = shape.find("./p:nvSpPr/p:cNvPr", NS)
        name = props.get("name", "") if props is not None else ""
        result[f"shape:{index}:{name}"] = native_text_body(shape) if preserve_offsets else "\n".join(element_paragraphs(shape))
    for index, frame in enumerate(root.findall(".//p:graphicFrame", NS)):
        props = frame.find("./p:nvGraphicFramePr/p:cNvPr", NS)
        name = props.get("name", "") if props is not None else str(index)
        for row, tr in enumerate(frame.findall(".//a:tbl/a:tr", NS)):
            for col, cell in enumerate(tr.findall("a:tc", NS)):
                key = f"table:{name}:{row}:{col}"
                if key in result:
                    raise ValueError(f"duplicate table location: {key}")
                result[key] = native_text_body(cell) if preserve_offsets else "\n".join(element_paragraphs(cell))
    return result


def chart_label_text(archive, slide_name, xml_bytes, location):
    """Resolve a label in this slide's named native chart, not a slide substring."""
    ns = dict(NS, c="http://schemas.openxmlformats.org/drawingml/2006/chart",
              r="http://schemas.openxmlformats.org/officeDocument/2006/relationships")
    root = ET.fromstring(xml_bytes)
    frames = [f for f in root.findall('.//p:graphicFrame', ns)
              if f.find('./p:nvGraphicFramePr/p:cNvPr', ns).get('name') == location['shape_name']]
    if len(frames) != 1:
        raise ValueError('native chart frame is missing or ambiguous')
    chart_ref = frames[0].find('.//c:chart', ns)
    if chart_ref is None:
        raise ValueError('named object is not a native chart')
    rel_path = posixpath.join(posixpath.dirname(slide_name), '_rels', posixpath.basename(slide_name) + '.rels')
    rels = ET.fromstring(archive.read(rel_path))
    rid = chart_ref.get('{'+ns['r']+'}id')
    matches = [r for r in rels if r.get('Id') == rid and r.get('TargetMode') != 'External']
    if len(matches) != 1:
        raise ValueError('chart relationship unavailable')
    target = matches[0].get('Target', '')
    part = target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(posixpath.dirname(slide_name), target))
    chart = ET.fromstring(archive.read(part))
    kind = location.get('label_kind')
    if kind == 'title':
        node = chart.find('.//c:chart/c:title', ns)
    else:
        series = chart.findall('.//c:ser', ns)
        si = location.get('series_index', 0)
        if si >= len(series):
            raise ValueError('unknown chart series')
        series = series[si]
        if kind == 'series-name':
            node = series.find('c:tx', ns)
        else:
            pi = str(location.get('point_index', 0))
            if kind == 'data-label':
                nodes = [n for n in series.findall('.//c:dLbl', ns) if n.find('c:idx', ns) is not None and n.find('c:idx', ns).get('val') == pi]
            else:
                parent = series.find('c:cat' if kind == 'category' else 'c:val', ns)
                nodes = [] if parent is None else [n for n in parent.findall('.//c:pt', ns) if n.get('idx') == pi]
            if len(nodes) != 1:
                raise ValueError('chart label selector does not resolve once')
            node = nodes[0]
    if node is None:
        raise ValueError('chart label missing')
    tokens = node.findall('.//a:t', ns) or node.findall('.//c:v', ns)
    return ''.join(t.text or '' for t in tokens)


def editable_object_errors(xml_bytes, baseline):
    """Verify separate native children and the exact native grouping Art chose."""
    root = ET.fromstring(xml_bytes)
    actual = {}
    property_paths = {
        'sp': './p:nvSpPr/p:cNvPr', 'pic': './p:nvPicPr/p:cNvPr',
        'graphicFrame': './p:nvGraphicFramePr/p:cNvPr',
        'cxnSp': './p:nvCxnSpPr/p:cNvPr', 'grpSp': './p:nvGrpSpPr/p:cNvPr',
    }
    def visit(container, groups):
        for node in container:
            tag = node.tag.rsplit('}', 1)[-1]
            if tag not in property_paths:
                continue
            props = node.find(property_paths[tag], NS)
            name = props.get('name', '') if props is not None else ''
            actual.setdefault(name, []).append((tag, groups, node))
            if tag == 'grpSp':
                visit(node, groups + [name])
    tree = root.find('./p:cSld/p:spTree', NS)
    if tree is None:
        return ['native object tree missing']
    visit(tree, [])
    errors = []
    for element in baseline['elements']:
        name = element['native_name']
        matches = actual.get(name, [])
        if len(matches) != 1:
            errors.append(f"Art object {name}: requires one separate native object, found {len(matches)}")
            continue
        tag, groups, node = matches[0]
        expected_groups = element.get('native_group_path', [])
        if groups != expected_groups:
            errors.append(f"Art object {name}: native grouping differs from the approved editing boundary")
        for group in expected_groups:
            if len(actual.get(group, [])) != 1 or actual[group][0][0] != 'grpSp':
                errors.append(f"Art object {name}: native group {group} is missing or ambiguous")
        kind = element['native_type']
        expected_tag = {'text':'sp','shape':'sp','image':'pic','picture':'pic',
                        'connector':'cxnSp','table':'graphicFrame','chart':'graphicFrame','diagram':'graphicFrame'}.get(kind)
        if tag == 'grpSp' or (expected_tag and tag != expected_tag):
            errors.append(f"Art object {name}: native type changed; a group or flattened picture cannot replace editable children")
        if kind == 'text' and node.find('p:txBody', NS) is None:
            errors.append(f"Art object {name}: editable text body missing")
        if kind == 'table' and node.find('.//a:tbl', NS) is None:
            errors.append(f"Art object {name}: integrated native table missing")
        if kind == 'chart' and not any('drawingml/2006/chart' in (data.get('uri') or '') for data in node.findall('.//a:graphicData', NS)):
            errors.append(f"Art object {name}: native chart missing")
    return errors


def approved_table_locations(baseline):
    """Bind Art-owned table text to exact named cells, not a text whitelist."""
    locations = {}
    for element in baseline['elements']:
        spec = element.get('table_spec')
        if spec is None:
            continue
        if not isinstance(spec, dict):
            raise ValueError('table_spec must be an object')
        headers, rows = spec.get('headers', []), spec.get('rows', [])
        if not isinstance(headers, list) or not isinstance(rows, list) or any(not isinstance(row, list) for row in rows):
            raise ValueError('table_spec headers and rows must be arrays')
        values = ([headers] if headers else []) + rows
        if not values or not values[0] or any(len(row) != len(values[0]) for row in values):
            raise ValueError('table_spec must declare a nonempty rectangular table')
        name = element.get('native_name', 'ART::' + element['element_id'])
        for row, cells in enumerate(values):
            for column, value in enumerate(cells):
                if not isinstance(value, (str, int, float)) or isinstance(value, bool):
                    raise ValueError('table_spec cells must be text or numbers')
                key = f'table:{name}:{row}:{column}'
                if key in locations:
                    raise ValueError('table_spec repeats a native cell')
                locations[key] = str(value)
    return locations


def compare_clean_content(package, plan, pptx, allow_extra_text=False):
    """Compare native text ranges; many Copy paragraphs may share one object."""
    errors = validate_plan(package, plan)
    if errors:
        return errors
    errors = Issues('quality')
    def text_key(value):
        return re.sub(r'\s+', '', value)  # Preserve case and punctuation.
    try:
        with zipfile.ZipFile(pptx) as archive:
            names = sorted((n for n in archive.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)), key=natural_slide_key)
            from packages.validators.art_content import presentation_pages
            pages = presentation_pages(package, plan)
            if len(names) != len(pages):
                errors.append(f'pptx: expected {len(pages)} slides, found {len(names)}')
            for index, (page, design, name) in enumerate(zip(pages, plan['slides'], names), 1):
                xml = archive.read(name)
                named, _, inventory = extract_slide(xml)
                if plan.get('contract_version') in {'2.2', '2.3'}:
                    errors.extend(f'slide {index}: {error}' for error in editable_object_errors(xml, plan['visual_baseline']['slides'][index-1]))
                locations = text_locations(xml, preserve_offsets=True)
                baseline = plan['visual_baseline']['slides'][index-1]
                try:
                    approved_cells = approved_table_locations(baseline)
                except ValueError as exc:
                    errors.append(Issue(f'slide {index}: invalid approved table specification: {exc}', 'record'))
                    approved_cells = {}
                for cell, expected in approved_cells.items():
                    if cell not in locations or text_key(locations[cell]) != text_key(expected):
                        errors.append(f'slide {index}: native table cell differs from approved Art specification: {cell}')
                table_names = {cell.split(':', 1)[1].rsplit(':', 2)[0] for cell in approved_cells}
                for cell in locations:
                    if cell.startswith('table:') and cell.split(':', 1)[1].rsplit(':', 2)[0] in table_names and cell not in approved_cells:
                        errors.append(f'slide {index}: extra native table cell outside approved Art specification: {cell}')
                by_name = {key.split(':', 2)[2]: value for key, value in locations.items() if key.startswith('shape:')}
                units = {u['copy_id']: u for u in page['copy_units']}
                used, actual_bodies = {}, {}
                for mapping in design['copy_unit_map']:
                    cid = mapping['copy_id']
                    loc = mapping['native_location']
                    kind = mapping['target_type']
                    if kind == 'shape':
                        key = f"shape:{loc['shape_name']}"
                        body = by_name.get(loc['shape_name'])
                    elif kind == 'table-cell':
                        key = f"table:{loc['shape_name']}:{loc['row']}:{loc['column']}"
                        body = locations.get(key)
                    else:
                        key = json.dumps({k:v for k,v in loc.items() if k != 'text_range'}, sort_keys=True)
                        body = chart_label_text(archive, name, xml, loc)
                    if body is None:
                        errors.append(f'slide {index} {cid}: native text location missing')
                        continue
                    span = loc.get('text_range', [0, len(body)])
                    if span[1] > len(body) or text_key(body[span[0]:span[1]]) != text_key(units[cid]['text']):
                        errors.append(f'slide {index} {cid}: native text range differs from approved Copy')
                    used.setdefault(key, []).append(span)
                    actual_bodies[key] = body
                if not allow_extra_text:
                    for key, spans in used.items():
                        body = actual_bodies[key]
                        cursor, remainder = 0, ''
                        for start, end in sorted(spans):
                            remainder += body[cursor:start]
                            cursor = end
                        remainder += body[cursor:]
                        if text_key(remainder):
                            errors.append(f'slide {index}: unapproved visible text in {key}')
                    baseline = plan['visual_baseline']['slides'][index-1]
                    additions = {text_key(e.get('text', '')) for e in baseline['elements'] if not e.get('copy_ids')}
                    for key, body in locations.items():
                        physical = 'shape:' + key.split(':', 2)[2] if key.startswith('shape:') else key
                        if physical not in used and physical not in approved_cells and text_key(body) and text_key(body) not in additions:
                            errors.append(f'slide {index}: extra visible text outside approved Art/Copy bindings')
                for kind, minimum in design['medium_execution_contract'].get('minimum_object_counts', {}).items():
                    if inventory.get(kind, 0) < minimum:
                        errors.append(f'slide {index}: Art requires {minimum} {kind} object(s), found {inventory.get(kind, 0)}')
    except (OSError, zipfile.BadZipFile, KeyError, ValueError, ET.ParseError) as exc:
        errors.append(Issue(f'pptx: cannot inspect native content: {exc}', 'record'))
    return errors


def compare(package: Any, plan: Any, pptx: Path, allow_extra_text: bool = False) -> list[str]:
    if isinstance(package, dict) and package.get('contract_version') in {'3.3', '3.4'}:
        return compare_clean_content(package, plan, pptx, allow_extra_text)
    errors = validate_plan(package, plan)
    if errors or not isinstance(package, dict) or not isinstance(plan, dict):
        return errors
    errors = Issues('quality')
    try:
        with zipfile.ZipFile(pptx) as archive:
            slide_names = sorted(
                [name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)],
                key=natural_slide_key,
            )
            extracted = [extract_slide(archive.read(name)) for name in slide_names]
            locations = [text_locations(archive.read(name)) for name in slide_names]
    except (OSError, zipfile.BadZipFile, KeyError, ValueError, ET.ParseError) as exc:
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
        available = Counter(normalize(value) for value in locations[index - 1].values() if value)
        expected_blocks = Counter(normalize(unit["text"]) for unit in units.values()
                                  if plan_map[unit["copy_id"]]["verification_method"] in {"paragraph-exact", "shape-name", "table-cell"})
        for value, count in expected_blocks.items():
            if available[value] != count:
                errors.append(f"slide {index}: expected {count} text location(s) for {value!r}, found {available[value]}")
        bound_locations = set()

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
                matches = [name for name in named if name == shape_name or name.startswith(shape_name + "::")]
                expected_shape_names.update(matches)
                if len(matches) != 1:
                    errors.append(f"slide {index} {copy_id}: expected exactly one shape named {shape_name}")
                else:
                    actual_text = normalize("".join(named[matches[0]]))
                    if actual_text != expected_text:
                        errors.append(f"slide {index} {copy_id}: named shape text differs from locked copy")
            elif method == "table-cell":
                location = mapping.get("native_location", {})
                key = f"table:{location.get('shape_name')}:{location.get('row')}:{location.get('column')}"
                if key in bound_locations:
                    errors.append(f"slide {index} {copy_id}: duplicate native cell binding")
                bound_locations.add(key)
                if key not in locations[index - 1] or normalize(locations[index - 1][key]) != expected_text:
                    errors.append(f"slide {index} {copy_id}: native table cell text differs from locked copy")

        copy_shape_names = [name for name in named if name.startswith("COPY::")]
        if len(copy_shape_names) != len(set(copy_shape_names)):
            errors.append(f"slide {index}: duplicate COPY shape names")
        unexpected_names = set(copy_shape_names) - expected_shape_names
        if unexpected_names:
            errors.append(f"slide {index}: unexpected COPY shape names {sorted(unexpected_names)}")

        # Exact object/cell comparisons establish separation; an approved sentence
        # may legitimately repeat the same category and value elsewhere.
        if not allow_extra_text:
            # A native cell/text body may contain multiple paragraphs. Accept only
            # segments of an exactly approved complete body, not arbitrary substrings.
            approved_whole = {normalize(unit["text"]) for unit in units.values()}
            for body in locations[index - 1].values():
                if normalize(body) in approved_whole:
                    allowed_paragraphs.update(normalize(part) for part in body.split("\n") if part)
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
    parser.add_argument("--result-json", type=Path)
    args = parser.parse_args()
    try:
        package = json.loads(args.package.read_text(encoding="utf-8"))
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        errors = compare(package, plan, args.pptx, args.allow_extra_text)
    except Exception as exc:
        return exception_result("native-pptx-comparison", exc, args.result_json)
    return finish("native-pptx-comparison", errors, args.result_json,
                  quality_checked=not args.allow_extra_text,
                  success=f"PASS: PPTX copy fidelity {args.pptx}")


if __name__ == "__main__":
    raise SystemExit(main())
