"""Inspect slide/table Latin and digit fonts and native chart text properties.

Explicit local properties can be verified without an Office layout engine.
Theme-only or missing properties remain unresolved, never a rendered-font pass.
"""
from __future__ import annotations

import re
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile


A = "http://schemas.openxmlformats.org/drawingml/2006/main"
C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
NS = {"a": A, "c": C}
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
CHART_COMPONENTS = {
    "catAx", "valAx", "dateAx", "serAx", "legend", "title", "dLbls",
    "dLbl", "trendlineLbl", "dispUnitsLbl", "dTable",
}


def inspect_font_scope(archive: ZipFile, config: dict[str, Any], aliases: dict[str, str]) -> dict[str, Any]:
    typography = config.get("theme", {}).get("typography", {})
    primary = typography.get("primary_fonts", [])
    findings: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    table_count = 0
    chart_parts: list[str] = []
    slide_parts: list[str] = []

    def canonical(value: str) -> str:
        return aliases.get(value.casefold(), value).casefold()

    def check(part: str, location: str, scope: str, field: str, family: str,
              role: str, text: str = "") -> None:
        allowed = typography.get(role + "_fonts") or primary
        status = "deferred" if not family or family.startswith("+") else (
            "pass" if canonical(family) in {canonical(str(x)) for x in allowed} else "fail"
        )
        record = {"part": part, "location": location, "scope": scope,
                  "font_field": field, "observed_typeface": family or "(unresolved)",
                  "font_role": role, "text": text, "status": status}
        checks.append(record)
        if status != "pass":
            findings.append(record)

    def family(properties: ET.Element | None, field: str) -> str:
        node = properties.find("a:" + field, NS) if properties is not None else None
        return str(node.get("typeface", "")).strip() if node is not None else ""

    def ancestors(node: ET.Element, parents: dict[ET.Element, ET.Element]):
        while node is not None:
            yield node
            node = parents.get(node)

    def chart_family(node: ET.Element, parents: dict[ET.Element, ET.Element], field: str) -> str:
        # Run -> paragraph -> chart component -> enclosing component -> chartSpace.
        # A property for one script must not overwrite another script's fallback.
        for current in ancestors(node, parents):
            paths = ("a:rPr", "a:pPr/a:defRPr", "c:txPr/a:p/a:pPr/a:defRPr",
                     "a:lstStyle/a:defPPr/a:defRPr")
            for path in paths:
                value = family(current.find(path, NS), field)
                if value:
                    return value
        return ""

    for part in sorted(archive.namelist()):
        is_slide = bool(re.fullmatch(r"ppt/slides/slide\d+\.xml", part))
        is_chart = bool(re.fullmatch(r"ppt/charts/chart\d+\.xml", part))
        if not (is_slide or is_chart):
            continue
        root = ET.fromstring(archive.read(part))
        parents = {child: parent for parent in root.iter() for child in parent}
        if is_slide:
            slide_parts.append(part)
            table_count += len(root.findall(".//a:tbl", NS))
        else:
            chart_parts.append(part)
        runs = root.findall(".//a:r", NS) + root.findall(".//a:fld", NS)
        for index, run in enumerate(runs):
            text = run.findtext("a:t", default="", namespaces=NS)
            scope = "chart" if is_chart else (
                "table" if any(n.tag == "{" + A + "}tbl" for n in ancestors(run, parents)) else "slide"
            )
            properties = run.find("a:rPr", NS)
            face = lambda field: chart_family(run, parents, field) if is_chart else family(properties, field)
            if is_chart and CJK.search(text):
                check(part, f"run[{index}]", scope, "ea", face("ea"), "chart", text)
            if re.search(r"[A-Za-z]", text):
                check(part, f"run[{index}]", scope, "latin", face("latin"), "chart" if is_chart else "latin", text)
            if re.search(r"\d", text):
                check(part, f"run[{index}]", scope, "latin", face("latin"), "chart" if is_chart else "digit", text)
        if not is_chart:
            continue
        for index, component in enumerate(root.iter()):
            name = component.tag.removeprefix("{" + C + "}")
            if name not in CHART_COMPONENTS:
                continue
            deleted = component.find("c:delete", NS)
            tick_position = component.find("c:tickLblPos", NS)
            if deleted is not None and deleted.get("val") in {"1", "true"}:
                continue
            if name.endswith("Ax") and tick_position is not None and tick_position.get("val") == "none":
                continue
            # Rich titles/individual labels have actual runs checked above.
            # Generated ticks, legends and values have no a:t runs to scan.
            if name in {"title", "dLbl"} and component.find("c:tx/c:rich", NS) is not None:
                continue
            for field in ("latin", "ea"):
                check(part, f"{name}[{index}]", "chart", field,
                      chart_family(component, parents, field), "chart")
    return {
        "coverage": {"slide_parts": slide_parts, "native_table_count": table_count,
                     "chart_parts": chart_parts, "checks_performed": len(checks),
                     "scope": ["slide-cjk", "slide-latin-digits", "native-table-text", "native-chart-text"],
                     "native_render_acceptance": "not-verified"},
        "checks": checks, "findings": findings,
    }
