#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Audit explicit CJK font names and configured font-file identities in a PPTX."""

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


def audit_font_assets(config: dict[str, Any], font_files: dict[str, Path] | None = None) -> list[dict[str, Any]]:
    """Verify materialized bytes; this does not prove a renderer loaded them."""
    supplied = {name.casefold(): Path(path) for name, path in (font_files or {}).items()}
    validation = config.get("theme", {}).get("typography", {}).get("font_validation")
    identities = validation.get("deferred_font_identities", []) if isinstance(validation, dict) else []
    checks: list[dict[str, Any]] = []
    for identity in identities:
        asset = identity.get("font_asset") if isinstance(identity, dict) else None
        if not isinstance(asset, dict):
            continue
        names = [identity["canonical_family"], *identity.get("aliases", [])]
        paths = {supplied[name.casefold()] for name in names if name.casefold() in supplied}
        check: dict[str, Any] = {
            "canonical_family": identity["canonical_family"],
            "expected": asset,
            "observed": [],
            "status": "deferred",
            "renderer_loaded_file": "not-verified",
        }
        if not paths:
            check["reason"] = "Pinned font file was not supplied; family-name equality is insufficient."
        else:
            for path in sorted(paths):
                observed: dict[str, Any] = {"path": str(path), "status": "deferred"}
                try:
                    observed["sha256"] = _sha256(path)
                    observed["bytes"] = path.stat().st_size
                    observed["status"] = "pass" if (
                        observed["sha256"] == asset.get("sha256")
                        and observed["bytes"] == asset.get("bytes")
                    ) else "fail"
                except OSError as exc:
                    observed["reason"] = str(exc)
                check["observed"].append(observed)
            statuses = {item["status"] for item in check["observed"]}
            check["status"] = "fail" if "fail" in statuses else "deferred" if "deferred" in statuses else "pass"
        checks.append(check)
    return checks


def audit_font_names(pptx: Path, config: dict[str, Any], font_files: dict[str, Path] | None = None) -> dict[str, Any]:
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

    name_status = "fail" if violations else "deferred" if inherited_cjk else "pass"
    asset_checks = audit_font_assets(config, font_files)
    statuses = {name_status, *(item["status"] for item in asset_checks)}
    status = "fail" if "fail" in statuses else "deferred" if "deferred" in statuses else "pass"
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
        "font_name_status": name_status,
        "font_asset_checks": asset_checks,
        "status": status,
        "ok": status == "pass" and total_cjk == conforming_cjk,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--font-file", action="append", default=[], metavar="FAMILY=PATH",
                        help="Materialized file for a pinned font identity; canonical family or alias accepted. Repeat for multiple files.")
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        font_files: dict[str, Path] = {}
        for value in args.font_file:
            name, separator, path = value.partition("=")
            if not separator or not name.strip() or not path.strip():
                raise ValueError("--font-file requires FAMILY=PATH")
            if name.casefold() in {key.casefold() for key in font_files}:
                raise ValueError(f"duplicate --font-file identity: {name}")
            font_files[name] = Path(path)
        report = audit_font_names(args.pptx, config, font_files)
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"ERROR: {exc}")
        return 2
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    if not report["ok"]:
        print(f"{report['status'].upper()}: font names={report['font_name_status']}; "
              f"font files={[item['status'] for item in report['font_asset_checks']]}")
        return 1
    print(f"PASS: {report['visible_cjk_chars']} visible CJK character(s) preserve configured font identity; "
          "any pinned files match. Renderer/native acceptance remains separate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
