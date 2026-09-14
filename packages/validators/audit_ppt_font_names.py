#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Audit effective East Asian font names for visible CJK text in a PPTX."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = {"a": A_NS}
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _font_policy(config: dict[str, Any]) -> tuple[list[str], dict[str, str]]:
    typography = config.get("theme", {}).get("typography", {})
    primary = [str(item) for item in typography.get("primary_fonts", []) if str(item).strip()]
    aliases: dict[str, str] = {}
    validation = typography.get("font_validation", {})
    for identity in validation.get("deferred_font_identities", []) if isinstance(validation, dict) else []:
        if not isinstance(identity, dict):
            continue
        canonical = str(identity.get("canonical_family", "")).strip()
        if not canonical:
            continue
        aliases[canonical.casefold()] = canonical
        for alias in identity.get("aliases", []):
            if str(alias).strip():
                aliases[str(alias).casefold()] = canonical
    for family in primary:
        aliases.setdefault(family.casefold(), family)
    return primary, aliases


def _theme_east_asian_fonts(archive: zipfile.ZipFile) -> list[str]:
    result: list[str] = []
    for name in archive.namelist():
        if not name.startswith("ppt/") or "/theme/theme" not in name or not name.endswith(".xml"):
            continue
        try:
            root = ET.fromstring(archive.read(name))
        except (ET.ParseError, KeyError):
            continue
        for node in root.findall(".//a:majorFont/a:ea", NS) + root.findall(".//a:minorFont/a:ea", NS):
            value = str(node.attrib.get("typeface", "")).strip()
            if value and value not in result:
                result.append(value)
    return result


def audit_font_names(pptx: Path, config: dict[str, Any]) -> dict[str, Any]:
    primary, alias_map = _font_policy(config)
    allowed_canonical = {family.casefold() for family in primary}
    violations: list[dict[str, Any]] = []
    slide_summaries: list[dict[str, Any]] = []
    total_cjk = 0
    conforming_cjk = 0
    inherited_cjk = 0

    with zipfile.ZipFile(pptx) as archive:
        theme_fonts = _theme_east_asian_fonts(archive)
        theme_ok = any(alias_map.get(item.casefold(), item).casefold() in allowed_canonical for item in theme_fonts)
        slide_names = sorted(
            (name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)),
            key=lambda name: int(re.search(r"\d+", Path(name).stem).group()),
        )
        for slide_number, slide_name in enumerate(slide_names, start=1):
            root = ET.fromstring(archive.read(slide_name))
            slide_total = 0
            slide_conforming = 0
            slide_violations = 0
            for run in root.findall(".//a:r", NS) + root.findall(".//a:fld", NS):
                text_node = run.find("a:t", NS)
                text = text_node.text if text_node is not None and text_node.text else ""
                cjk_count = len(CJK.findall(text))
                if cjk_count == 0:
                    continue
                slide_total += cjk_count
                total_cjk += cjk_count
                rpr = run.find("a:rPr", NS)
                ea = rpr.find("a:ea", NS) if rpr is not None else None
                latin = rpr.find("a:latin", NS) if rpr is not None else None
                typeface = ""
                source = "inherited"
                if ea is not None and str(ea.attrib.get("typeface", "")).strip():
                    typeface = str(ea.attrib["typeface"]).strip()
                    source = "east-asian-run"
                elif latin is not None and str(latin.attrib.get("typeface", "")).strip():
                    typeface = str(latin.attrib["typeface"]).strip()
                    source = "latin-run-fallback"
                if source != "east-asian-run":
                    inherited_cjk += cjk_count
                    # A theme or Latin fallback cannot prove the effective
                    # East Asian run font.  Keep the observation explicitly
                    # unresolved even when the declared theme looks correct.
                    continue
                canonical = alias_map.get(typeface.casefold(), typeface)
                if canonical.casefold() in allowed_canonical:
                    slide_conforming += cjk_count
                    conforming_cjk += cjk_count
                else:
                    slide_violations += 1
                    violations.append({
                        "slide_number": slide_number,
                        "text": text,
                        "cjk_char_count": cjk_count,
                        "observed_typeface": typeface or "(inherited-without-approved-theme)",
                        "font_source": source,
                    })
            slide_summaries.append({
                "slide_number": slide_number,
                "visible_cjk_chars": slide_total,
                "conforming_cjk_chars": slide_conforming,
                "violation_count": slide_violations,
            })

    status = "fail" if violations else "deferred" if inherited_cjk else "pass"
    return {
        "contract": "io.clayz.presentation.pptx-font-name-audit/1.0",
        "pptx": pptx.name,
        "pptx_sha256": _sha256(pptx),
        "required_cjk_families": primary,
        "accepted_aliases": alias_map,
        "theme_east_asian_fonts": theme_fonts,
        "visible_cjk_chars": total_cjk,
        "conforming_cjk_chars": conforming_cjk,
        "inherited_cjk_chars": inherited_cjk,
        "violations": violations,
        "slides": slide_summaries,
        "status": status,
        "ok": status == "pass" and total_cjk == conforming_cjk,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        report = audit_font_names(args.pptx, config)
    except (OSError, json.JSONDecodeError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"ERROR: {exc}")
        return 2
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    if not report["ok"]:
        print(f"FAILED: {len(report['violations'])} CJK font-name violation(s)")
        return 1
    print(f"PASS: {report['visible_cjk_chars']} visible CJK character(s) preserve configured font identity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
