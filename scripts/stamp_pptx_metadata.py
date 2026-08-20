#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Add documented, removable Clayz provenance to PPTX custom properties."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


CUSTOM_NS = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
VT_NS = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
CUSTOM_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties"
CUSTOM_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.custom-properties+xml"
FMTID = "{D5CDD505-2E9C-101B-9397-08002B2CF9AE}"

ET.register_namespace("", CUSTOM_NS)
ET.register_namespace("vt", VT_NS)
ET.register_namespace("", REL_NS)
ET.register_namespace("", CT_NS)


def qname(namespace: str, local: str) -> str:
    return f"{{{namespace}}}{local}"


def custom_xml(existing: bytes | None, values: dict[str, str]) -> bytes:
    root = ET.fromstring(existing) if existing else ET.Element(qname(CUSTOM_NS, "Properties"))
    by_name = {node.get("name"): node for node in root.findall(qname(CUSTOM_NS, "property"))}
    for name, value in values.items():
        node = by_name.get(name)
        if node is None:
            node = ET.SubElement(root, qname(CUSTOM_NS, "property"), {"fmtid": FMTID, "pid": "2", "name": name})
            by_name[name] = node
        for child in list(node):
            node.remove(child)
        text = ET.SubElement(node, qname(VT_NS, "lpwstr"))
        text.text = str(value)
    for pid, node in enumerate(root.findall(qname(CUSTOM_NS, "property")), start=2):
        node.set("pid", str(pid))
        node.set("fmtid", FMTID)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def custom_xml_without(existing: bytes, names: set[str]) -> bytes | None:
    root = ET.fromstring(existing)
    for node in list(root.findall(qname(CUSTOM_NS, "property"))):
        if node.get("name") in names:
            root.remove(node)
    properties = root.findall(qname(CUSTOM_NS, "property"))
    if not properties:
        return None
    for pid, node in enumerate(properties, start=2):
        node.set("pid", str(pid))
        node.set("fmtid", FMTID)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def relationships_xml(existing: bytes) -> bytes:
    root = ET.fromstring(existing)
    for rel in root.findall(qname(REL_NS, "Relationship")):
        if rel.get("Type") == CUSTOM_REL:
            rel.set("Target", "docProps/custom.xml")
            return ET.tostring(root, encoding="utf-8", xml_declaration=True)
    used = {rel.get("Id", "") for rel in root.findall(qname(REL_NS, "Relationship"))}
    index = 1
    while f"rId{index}" in used:
        index += 1
    ET.SubElement(root, qname(REL_NS, "Relationship"), {
        "Id": f"rId{index}", "Type": CUSTOM_REL, "Target": "docProps/custom.xml",
    })
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def content_types_xml(existing: bytes) -> bytes:
    root = ET.fromstring(existing)
    for node in root.findall(qname(CT_NS, "Override")):
        if node.get("PartName") == "/docProps/custom.xml":
            node.set("ContentType", CUSTOM_CONTENT_TYPE)
            return ET.tostring(root, encoding="utf-8", xml_declaration=True)
    ET.SubElement(root, qname(CT_NS, "Override"), {
        "PartName": "/docProps/custom.xml", "ContentType": CUSTOM_CONTENT_TYPE,
    })
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def relationships_without_custom(existing: bytes) -> bytes:
    root = ET.fromstring(existing)
    for rel in list(root.findall(qname(REL_NS, "Relationship"))):
        if rel.get("Type") == CUSTOM_REL:
            root.remove(rel)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def content_types_without_custom(existing: bytes) -> bytes:
    root = ET.fromstring(existing)
    for node in list(root.findall(qname(CT_NS, "Override"))):
        if node.get("PartName") == "/docProps/custom.xml":
            root.remove(node)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def stamp(source: Path, destination: Path, values: dict[str, str]) -> None:
    if not zipfile.is_zipfile(source):
        raise ValueError(f"not a valid OOXML archive: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source, "r") as archive:
        names = set(archive.namelist())
        required = {"[Content_Types].xml", "_rels/.rels"}
        if not required.issubset(names):
            raise ValueError("archive is missing required OOXML package parts")
        custom = custom_xml(archive.read("docProps/custom.xml") if "docProps/custom.xml" in names else None, values)
        rels = relationships_xml(archive.read("_rels/.rels"))
        content_types = content_types_xml(archive.read("[Content_Types].xml"))
        with zipfile.ZipFile(destination, "w") as output:
            for info in archive.infolist():
                if info.filename in {"docProps/custom.xml", "_rels/.rels", "[Content_Types].xml"}:
                    continue
                output.writestr(info, archive.read(info.filename))
            output.writestr("docProps/custom.xml", custom)
            output.writestr("_rels/.rels", rels)
            output.writestr("[Content_Types].xml", content_types)


def remove_stamp(source: Path, destination: Path, names: set[str]) -> None:
    """Remove only Clayz-owned custom properties, preserving unrelated metadata."""
    if not zipfile.is_zipfile(source):
        raise ValueError(f"not a valid OOXML archive: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source, "r") as archive:
        archive_names = set(archive.namelist())
        required = {"[Content_Types].xml", "_rels/.rels"}
        if not required.issubset(archive_names):
            raise ValueError("archive is missing required OOXML package parts")
        existing_custom = archive.read("docProps/custom.xml") if "docProps/custom.xml" in archive_names else None
        remaining_custom = custom_xml_without(existing_custom, names) if existing_custom else None
        remove_custom_part = existing_custom is not None and remaining_custom is None
        rels = (
            relationships_without_custom(archive.read("_rels/.rels"))
            if remove_custom_part else archive.read("_rels/.rels")
        )
        content_types = (
            content_types_without_custom(archive.read("[Content_Types].xml"))
            if remove_custom_part else archive.read("[Content_Types].xml")
        )
        with zipfile.ZipFile(destination, "w") as output:
            for info in archive.infolist():
                if info.filename in {"docProps/custom.xml", "_rels/.rels", "[Content_Types].xml"}:
                    continue
                output.writestr(info, archive.read(info.filename))
            if remaining_custom is not None:
                output.writestr("docProps/custom.xml", remaining_custom)
            output.writestr("_rels/.rels", rels)
            output.writestr("[Content_Types].xml", content_types)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pptx")
    parser.add_argument("--config", default="config/default.json")
    parser.add_argument("--output")
    parser.add_argument("--remove", action="store_true", help="remove Clayz custom properties instead of adding them")
    args = parser.parse_args()
    source = Path(args.pptx).resolve()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    attribution = config["identity"]["attribution"]
    if attribution.get("mode") != "metadata" and not args.remove:
        print("attribution mode is not metadata; no changes made")
        return 0
    values = attribution.get("custom_properties", {})
    operation = remove_stamp if args.remove else stamp
    payload = set(values) if args.remove else values
    if args.output:
        destination = Path(args.output).resolve()
        operation(source, destination, payload)
    else:
        handle = tempfile.NamedTemporaryFile(prefix="clayz-", suffix=".pptx", dir=source.parent, delete=False)
        handle.close()
        temporary = Path(handle.name)
        try:
            operation(source, temporary, payload)
            os.replace(temporary, source)
        finally:
            if temporary.exists():
                temporary.unlink()
    print(json.dumps({
        "ok": True,
        "action": "removed" if args.remove else "stamped",
        "pptx": str(Path(args.output).resolve() if args.output else source),
        "properties": sorted(values) if args.remove else values,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
