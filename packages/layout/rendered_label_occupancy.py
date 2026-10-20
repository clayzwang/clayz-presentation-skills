"""Observe selected labels in one actual PDF coordinate space.

This is an optional authoring aid, not a quality validator. Native chart labels
and manual annotations can compete for the same space even when each fits its
own object. Exact matching retains missing and ambiguous observations; metric
rectangles only identify pairs worth looking at in the real page image.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET


def normalized(text: str) -> str:
    return re.sub(r"\s+", "", text)


def reference(path: str | Path) -> dict:
    path = Path(path).resolve()
    data = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def rectangle(value) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError("rectangle must be [left, top, right, bottom]")
    result = [float(x) for x in value]
    if not all(math.isfinite(x) for x in result) or result[2] <= result[0] or result[3] <= result[1]:
        raise ValueError("rectangle must have finite positive area")
    return result


def relation(first: list[float], second: list[float]) -> dict:
    x = min(first[2], second[2]) - max(first[0], second[0])
    y = min(first[3], second[3]) - max(first[1], second[1])
    return {
        "positive_metric_intersection": x > 0 and y > 0,
        "intersection_width_pt": max(0.0, x),
        "intersection_height_pt": max(0.0, y),
        "intersection_area_pt2": max(0.0, x) * max(0.0, y),
        "rectangle_gap_pt": math.hypot(max(0.0, -x), max(0.0, -y)),
    }


def inspect_bbox(xml: bytes | str, request: dict) -> dict:
    """Match actual rendered label lines inside caller-supplied search regions.

    Request pages identify the 1-based PDF page and a free slide_id. Each label
    supplies id, text, kind, native_name and search_box (normalized left/top/
    right/bottom, or points with box_units='pt'). Regions guide identity only;
    they are not inferred text capacity or semantic object boundaries.
    """
    if request.get("contract") != "io.clayz.presentation.label-occupancy-request/1.0":
        raise ValueError("unsupported label occupancy request")
    root = ET.fromstring(xml)
    ns = "{http://www.w3.org/1999/xhtml}"
    pdf_pages = list(root.iter(ns + "page"))
    results = []
    seen_pages = set()
    for page_request in request.get("pages", []):
        number = page_request.get("page_number")
        if not isinstance(number, int) or not 1 <= number <= len(pdf_pages) or number in seen_pages:
            raise ValueError("page_number must identify a distinct existing PDF page")
        seen_pages.add(number)
        page = pdf_pages[number - 1]
        width, height = float(page.get("width")), float(page.get("height"))
        line_words = [list(line.iter(ns + "word")) for line in page.iter(ns + "line")]
        labels, seen_ids = [], set()
        for label in page_request.get("labels", []):
            for key in ("label_id", "text", "kind", "native_name"):
                if not isinstance(label.get(key), str) or not label[key].strip():
                    raise ValueError(f"label.{key} must be a nonempty string")
            if label["label_id"] in seen_ids:
                raise ValueError("label_id must be unique within a page")
            seen_ids.add(label["label_id"])
            region = rectangle(label["search_box"])
            units = label.get("box_units", "normalized")
            if units == "normalized":
                if not all(0 <= x <= 1 for x in region):
                    raise ValueError("normalized search region must lie on the page")
                region = [region[0] * width, region[1] * height, region[2] * width, region[3] * height]
            elif units != "pt":
                raise ValueError("box_units must be normalized or pt")
            target, candidates = normalized(label["text"]), []
            for words in line_words:
                for start in range(len(words)):
                    value, selected = "", []
                    for word in words[start:]:
                        value += normalized(word.text or "")
                        selected.append(word)
                        if len(value) > len(target):
                            break
                        if value != target:
                            continue
                        boxes = [[float(word.get(k)) for k in ("xMin", "yMin", "xMax", "yMax")] for word in selected]
                        bounds = [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]
                        if relation(bounds, region)["positive_metric_intersection"]:
                            item = {"bounds_pt": bounds, "word_texts": [word.text or "" for word in selected]}
                            if item not in candidates:
                                candidates.append(item)
                        break
            labels.append({
                "label_id": label["label_id"], "text": label["text"],
                "kind": label["kind"], "native_name": label["native_name"],
                "search_region_pt": region, "candidate_count": len(candidates),
                "match_status": "unique" if len(candidates) == 1 else "missing" if not candidates else "ambiguous",
                "candidates": candidates,
            })
        pairs = []
        unique = [item for item in labels if item["match_status"] == "unique"]
        for i, first in enumerate(unique):
            for second in unique[i + 1:]:
                pairs.append({"label_ids": [first["label_id"], second["label_id"]],
                              **relation(first["candidates"][0]["bounds_pt"], second["candidates"][0]["bounds_pt"])})
        results.append({"slide_id": page_request["slide_id"], "page_number": number,
                        "page_size_pt": [width, height], "labels": labels, "measured_pairs": pairs,
                        "possible_intersections": [p for p in pairs if p["positive_metric_intersection"]]})
    counts = {state: sum(label["match_status"] == state for page in results for label in page["labels"])
              for state in ("unique", "missing", "ambiguous")}
    return {"contract": "io.clayz.presentation.label-occupancy-observation/1.0",
            "status": "observation-only", "coverage": counts, "pages": results,
            "limitations": [
                "Only the requested actual PDF label lines and supplied search regions are observed; unrequested labels are outside coverage.",
                "Whitespace-normalized exact matching does not infer identity when text is missing or ambiguous; such labels are not included in measured pairs.",
                "Rectangles are PDF font metrics, not visible glyph ink, native attachment, semantic ownership, visual polish or reader understanding.",
                "Positive intersection is a candidate for visual review, not an automatic defect; an empty candidate list is not a quality pass.",
                "No hard clearance threshold, aesthetic score, production gate or automatic native-file mutation is introduced.",
            ]}


def observe(pdf: str | Path, request: dict) -> dict:
    result = subprocess.run(["pdftotext", "-bbox-layout", str(pdf), "-"], check=True, capture_output=True)
    observation = inspect_bbox(result.stdout, request)
    observation["pdf"] = reference(pdf)
    observation["process"] = {"command": ["pdftotext", "-bbox-layout", str(pdf), "-"], "returncode": result.returncode}
    return observation
