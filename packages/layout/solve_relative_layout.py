#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Resolve a neutral relative-layout tree into editable slide coordinates.

The implementation is original to Clayz Presentation Skills.  Its declarative
tree and flex-style allocation are conceptually informed by pom/Flexbox; no pom
source code is copied or redistributed.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


EPSILON = 1e-7
CONTAINER_TYPES = {"row", "column", "grid", "layers"}


class LayoutError(ValueError):
    """Raised when a layout tree cannot be resolved without hidden changes."""


def _number(value: Any, path: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise LayoutError(f"{path}: expected a finite number")
    result = float(value)
    if minimum is not None and result < minimum:
        raise LayoutError(f"{path}: expected >= {minimum}")
    return result


def _padding(value: Any, path: str) -> tuple[float, float, float, float]:
    if value is None:
        return 0.0, 0.0, 0.0, 0.0
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        amount = _number(value, path, minimum=0.0)
        return amount, amount, amount, amount
    if not isinstance(value, dict):
        raise LayoutError(f"{path}: expected a number or mapping")
    top = _number(value.get("top", 0), f"{path}.top", minimum=0.0)
    right = _number(value.get("right", 0), f"{path}.right", minimum=0.0)
    bottom = _number(value.get("bottom", 0), f"{path}.bottom", minimum=0.0)
    left = _number(value.get("left", 0), f"{path}.left", minimum=0.0)
    return top, right, bottom, left


def _inner_box(box: dict[str, float], padding: tuple[float, float, float, float], path: str) -> dict[str, float]:
    top, right, bottom, left = padding
    width = box["w"] - left - right
    height = box["h"] - top - bottom
    if width < -EPSILON or height < -EPSILON:
        raise LayoutError(f"{path}.padding: exceeds the assigned box")
    return {"x": box["x"] + left, "y": box["y"] + top, "w": max(0.0, width), "h": max(0.0, height)}


def _clamp(value: float, node: dict[str, Any], path: str) -> float:
    minimum = _number(node.get("min", 0), f"{path}.min", minimum=0.0)
    maximum_value = node.get("max")
    maximum = _number(maximum_value, f"{path}.max", minimum=0.0) if maximum_value is not None else math.inf
    if maximum < minimum:
        raise LayoutError(f"{path}: max is smaller than min")
    return min(max(value, minimum), maximum)


def _cross_box(
    child: dict[str, Any],
    path: str,
    *,
    main_start: float,
    main_size: float,
    cross_start: float,
    cross_size: float,
    horizontal: bool,
    align: str,
) -> dict[str, float]:
    requested = child.get("cross")
    extent = cross_size if requested is None else _number(requested, f"{path}.cross", minimum=0.0)
    if extent > cross_size + EPSILON:
        raise LayoutError(f"{path}.cross: exceeds parent cross-axis extent")
    child_align = child.get("align_self", align)
    if child_align not in {"stretch", "start", "center", "end"}:
        raise LayoutError(f"{path}.align_self: unsupported alignment {child_align!r}")
    if child_align == "stretch" and requested is None:
        offset = 0.0
    elif child_align in {"stretch", "start"}:
        offset = 0.0
    elif child_align == "center":
        offset = (cross_size - extent) / 2
    else:
        offset = cross_size - extent
    if horizontal:
        return {"x": main_start, "y": cross_start + offset, "w": main_size, "h": extent}
    return {"x": cross_start + offset, "y": main_start, "w": extent, "h": main_size}


def _allocate_linear(node: dict[str, Any], box: dict[str, float], path: str) -> list[tuple[dict[str, Any], dict[str, float], str]]:
    horizontal = node["type"] == "row"
    children = node.get("children", [])
    if not isinstance(children, list) or not children:
        raise LayoutError(f"{path}.children: expected a non-empty array")
    gap = _number(node.get("gap", 0), f"{path}.gap", minimum=0.0)
    align = node.get("align", "stretch")
    main_extent = box["w"] if horizontal else box["h"]
    cross_extent = box["h"] if horizontal else box["w"]
    available = main_extent - gap * (len(children) - 1)
    if available < -EPSILON:
        raise LayoutError(f"{path}: gaps exceed the available extent")

    sizes: list[float | None] = []
    flexes: list[float] = []
    fixed_total = 0.0
    flex_total = 0.0
    for index, child in enumerate(children):
        child_path = f"{path}.children[{index}]"
        if not isinstance(child, dict):
            raise LayoutError(f"{child_path}: expected a mapping")
        basis = child.get("basis")
        if basis is not None:
            size = _clamp(_number(basis, f"{child_path}.basis", minimum=0.0), child, child_path)
            sizes.append(size)
            flexes.append(0.0)
            fixed_total += size
        else:
            flex = _number(child.get("flex", 1), f"{child_path}.flex", minimum=0.0)
            sizes.append(None)
            flexes.append(flex)
            flex_total += flex
    remaining = available - fixed_total
    if remaining < -EPSILON:
        raise LayoutError(f"{path}: fixed bases exceed the available extent")
    if flex_total <= EPSILON and any(size is None for size in sizes):
        raise LayoutError(f"{path}: unresolved children require positive flex")
    for index, size in enumerate(sizes):
        if size is None:
            proposed = remaining * flexes[index] / flex_total
            sizes[index] = _clamp(proposed, children[index], f"{path}.children[{index}]")
    resolved_total = sum(float(size) for size in sizes)
    if resolved_total > available + EPSILON:
        raise LayoutError(f"{path}: min/max constraints exceed the available extent")

    cursor = box["x"] if horizontal else box["y"]
    cross_start = box["y"] if horizontal else box["x"]
    result = []
    for index, child in enumerate(children):
        size = float(sizes[index])
        child_path = f"{path}.children[{index}]"
        child_box = _cross_box(
            child,
            child_path,
            main_start=cursor,
            main_size=size,
            cross_start=cross_start,
            cross_size=cross_extent,
            horizontal=horizontal,
            align=align,
        )
        result.append((child, child_box, child_path))
        cursor += size + gap
    return result


def _allocate_grid(node: dict[str, Any], box: dict[str, float], path: str) -> list[tuple[dict[str, Any], dict[str, float], str]]:
    children = node.get("children", [])
    if not isinstance(children, list) or not children:
        raise LayoutError(f"{path}.children: expected a non-empty array")
    columns_value = node.get("columns", 12)
    if isinstance(columns_value, bool) or not isinstance(columns_value, int) or columns_value <= 0:
        raise LayoutError(f"{path}.columns: expected a positive integer")
    columns = columns_value
    column_gap = _number(node.get("column_gap", node.get("gap", 0)), f"{path}.column_gap", minimum=0.0)
    row_gap = _number(node.get("row_gap", node.get("gap", 0)), f"{path}.row_gap", minimum=0.0)
    placements: list[tuple[int, int, int, dict[str, Any], str]] = []
    row = 0
    column = 0
    for index, child in enumerate(children):
        child_path = f"{path}.children[{index}]"
        if not isinstance(child, dict):
            raise LayoutError(f"{child_path}: expected a mapping")
        span_value = child.get("column_span", 1)
        if isinstance(span_value, bool) or not isinstance(span_value, int) or not 1 <= span_value <= columns:
            raise LayoutError(f"{child_path}.column_span: expected an integer from 1 to {columns}")
        if column + span_value > columns:
            row += 1
            column = 0
        placements.append((row, column, span_value, child, child_path))
        column += span_value
        if column == columns:
            row += 1
            column = 0
    row_count = max(item[0] for item in placements) + 1
    cell_width = (box["w"] - column_gap * (columns - 1)) / columns
    cell_height = (box["h"] - row_gap * (row_count - 1)) / row_count
    if cell_width < -EPSILON or cell_height < -EPSILON:
        raise LayoutError(f"{path}: grid gaps exceed the available box")
    result = []
    for grid_row, grid_column, span, child, child_path in placements:
        child_box = {
            "x": box["x"] + grid_column * (cell_width + column_gap),
            "y": box["y"] + grid_row * (cell_height + row_gap),
            "w": cell_width * span + column_gap * (span - 1),
            "h": cell_height,
        }
        result.append((child, child_box, child_path))
    return result


def _allocate_layers(node: dict[str, Any], box: dict[str, float], path: str) -> list[tuple[dict[str, Any], dict[str, float], str]]:
    children = node.get("children", [])
    if not isinstance(children, list) or not children:
        raise LayoutError(f"{path}.children: expected a non-empty array")
    result = []
    for index, child in enumerate(children):
        child_path = f"{path}.children[{index}]"
        if not isinstance(child, dict):
            raise LayoutError(f"{child_path}: expected a mapping")
        inset = child.get("inset", {})
        if not isinstance(inset, dict):
            raise LayoutError(f"{child_path}.inset: expected a mapping")
        x = _number(inset.get("x", 0), f"{child_path}.inset.x")
        y = _number(inset.get("y", 0), f"{child_path}.inset.y")
        width = _number(inset.get("w", box["w"] - x), f"{child_path}.inset.w", minimum=0.0)
        height = _number(inset.get("h", box["h"] - y), f"{child_path}.inset.h", minimum=0.0)
        result.append((child, {"x": box["x"] + x, "y": box["y"] + y, "w": width, "h": height}, child_path))
    return result


def solve(document: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise LayoutError("$: expected a mapping")
    frame = document.get("frame")
    root = document.get("root")
    if not isinstance(frame, dict) or not isinstance(root, dict):
        raise LayoutError("$: frame and root mappings are required")
    root_box = {
        key: _number(frame.get(key), f"$.frame.{key}", minimum=0.0 if key in {"w", "h"} else None)
        for key in ("x", "y", "w", "h")
    }
    boxes: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    diagnostics: list[dict[str, Any]] = []

    def visit(node: dict[str, Any], box: dict[str, float], path: str, parent_id: str | None) -> None:
        node_id = node.get("id")
        node_type = node.get("type", "leaf")
        if not isinstance(node_id, str) or not node_id:
            raise LayoutError(f"{path}.id: expected a non-empty string")
        if node_id in boxes:
            raise LayoutError(f"{path}.id: duplicate node id {node_id!r}")
        if node_type not in CONTAINER_TYPES | {"leaf"}:
            raise LayoutError(f"{path}.type: unsupported type {node_type!r}")
        record: dict[str, Any] = {"id": node_id, "type": node_type, "parent_id": parent_id, **box}
        for key in ("role", "intent", "reading_order", "copy_ids", "protected"):
            if key in node:
                record[key] = node[key]
        boxes[node_id] = record
        order.append(node_id)
        if node_type == "leaf":
            if node.get("children"):
                raise LayoutError(f"{path}.children: leaf nodes cannot contain children")
            return
        inner = _inner_box(box, _padding(node.get("padding"), f"{path}.padding"), path)
        if node_type in {"row", "column"}:
            allocations = _allocate_linear(node, inner, path)
        elif node_type == "grid":
            allocations = _allocate_grid(node, inner, path)
        else:
            allocations = _allocate_layers(node, inner, path)
        for child, child_box, child_path in allocations:
            if (
                child_box["x"] < root_box["x"] - EPSILON
                or child_box["y"] < root_box["y"] - EPSILON
                or child_box["x"] + child_box["w"] > root_box["x"] + root_box["w"] + EPSILON
                or child_box["y"] + child_box["h"] > root_box["y"] + root_box["h"] + EPSILON
            ):
                diagnostics.append({"code": "NODE_OUT_OF_BOUNDS", "node_id": child.get("id"), "path": child_path})
            visit(child, child_box, child_path, node_id)

    visit(root, root_box, "$.root", None)
    return {
        "contract": "io.clayz.presentation.layout-resolution/1.0",
        "frame": root_box,
        "boxes": [boxes[node_id] for node_id in order],
        "diagnostics": diagnostics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Relative-layout tree JSON")
    parser.add_argument("output", type=Path, help="Resolved coordinate manifest JSON")
    args = parser.parse_args()
    try:
        document = json.loads(args.input.read_text(encoding="utf-8"))
        resolved = solve(document)
    except (OSError, json.JSONDecodeError, LayoutError) as exc:
        parser.error(str(exc))
    args.output.write_text(json.dumps(resolved, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
