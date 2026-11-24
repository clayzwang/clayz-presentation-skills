"""Read-only source-cache/PDF comparison for explicit slide-number fields.

This is a diagnostic, not canonical page-number acceptance. It never starts
Office, renders a new PDF, edits a presentation, or changes a production gate.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import posixpath
import re
import subprocess
import time
import xml.etree.ElementTree as ET
import zipfile

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw)}


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def number(text):
    text = text.strip()
    return int(text) if len(text) <= 12 and re.fullmatch(r"[0-9]+", text) else None


def validate_pair(manifest, sources):
    """Validate only supplied bytes, never open an embedded original path."""
    for role in ("pptx", "pdf"):
        expected = manifest.get(role)
        if not isinstance(expected, dict) or type(expected.get("bytes")) is not int:
            raise ValueError("render manifest needs exact pptx/pdf SHA256 and byte counts")
        if expected.get("sha256") != sources[role]["sha256"] or expected["bytes"] != sources[role]["bytes"]:
            raise ValueError("supplied " + role + " bytes differ from the render manifest")
    return "PPTX/PDF bytes match the supplied render manifest; this is not independent attestation of the export or its timing"


def read_source(path):
    def xml(archive, name):
        if archive.getinfo(name).file_size > 20 * 1024 * 1024:
            raise ValueError("XML part exceeds diagnostic limit")
        return ET.fromstring(archive.read(name))

    pages = []
    with zipfile.ZipFile(path) as archive:
        presentation = xml(archive, "ppt/presentation.xml")
        size = presentation.find("p:sldSz", NS)
        if size is None:
            raise ValueError("explicit slide size required")
        width, height = int(size.get("cx")), int(size.get("cy"))
        if width <= 0 or height <= 0:
            raise ValueError("positive slide size required")
        relations = xml(archive, "ppt/_rels/presentation.xml.rels")
        targets = {}
        for rel in relations.findall(REL + "Relationship"):
            if rel.get("TargetMode") == "External":
                continue
            target = rel.get("Target", "")
            name = posixpath.normpath(posixpath.join("ppt", target))
            if not name.startswith("ppt/slides/") or not name.endswith(".xml"):
                continue
            targets[rel.get("Id")] = name
        slide_ids = presentation.find("p:sldIdLst", NS)
        if slide_ids is None:
            raise ValueError("slide order required")
        for index, slide_id in enumerate(slide_ids, 1):
            name = targets.get(slide_id.get("{" + NS["r"] + "}id"))
            if name is None:
                raise ValueError("slide relationship unavailable")
            root = xml(archive, name)
            parents = {child: parent for parent in root.iter() for child in parent}
            fields = []
            for field in root.findall(".//a:fld", NS):
                if field.get("type", "").lower() != "slidenum":
                    continue
                # Only a:t is cached field text; formatting whitespace is not.
                text = "".join(x.text or "" for x in field.findall("a:t", NS))
                ancestors = []
                node = field
                while node in parents:
                    node = parents[node]
                    ancestors.append(node)
                shape = next((x for x in ancestors if x.tag == "{" + NS["p"] + "}sp"), None)
                item = {"field_id": field.get("id"), "source_cache_text": text,
                        "source_cache_number": number(text), "box_emu": None}
                if any(x.tag == "{" + NS["p"] + "}grpSp" for x in ancestors):
                    item["unobserved_reason"] = "group transform not supported"
                elif shape is None:
                    item["unobserved_reason"] = "no explicit text shape"
                else:
                    props = shape.find("p:nvSpPr/p:cNvPr", NS)
                    item["shape_id"] = props.get("id") if props is not None else None
                    transform = shape.find("p:spPr/a:xfrm", NS)
                    if transform is None:
                        item["unobserved_reason"] = "inherited/absent shape geometry not resolved"
                    elif int(transform.get("rot", "0")) or transform.get("flipH", "0") not in {"0", "false"} or transform.get("flipV", "0") not in {"0", "false"}:
                        item["unobserved_reason"] = "rotated/flipped shape not supported"
                    else:
                        off, ext = transform.find("a:off", NS), transform.find("a:ext", NS)
                        if off is None or ext is None:
                            item["unobserved_reason"] = "explicit offset/extent missing"
                        else:
                            box = [int(off.get("x")), int(off.get("y")),
                                   int(ext.get("cx")), int(ext.get("cy"))]
                            if box[2] <= 0 or box[3] <= 0:
                                item["unobserved_reason"] = "nonpositive shape extent"
                            else:
                                item["box_emu"] = box
                fields.append(item)
            pages.append({"slide_index": index, "slide_part": name, "fields": fields})
        return {"slide_size_emu": [width, height],
                "firstSlideNum_as_stored": presentation.get("firstSlideNum"),
                "slide_count": len(pages), "pages": pages}


def read_pdf_words(path):
    root = ET.parse(path).getroot()
    pages = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "page":
            continue
        width, height = float(element.get("width")), float(element.get("height"))
        if not all(math.isfinite(x) and x > 0 for x in (width, height)):
            raise ValueError("invalid PDF page geometry")
        words = []
        for word in element.iter():
            if word.tag.rsplit("}", 1)[-1] != "word":
                continue
            box = [float(word.get(k)) for k in ("xMin", "yMin", "xMax", "yMax")]
            if not all(math.isfinite(x) for x in box) or box[2] < box[0] or box[3] < box[1]:
                raise ValueError("invalid PDF word geometry")
            words.append({"text": "".join(word.itertext()), "box_pt": box})
        pages.append({"size_pt": [width, height], "words": words})
    return pages


def compare(source, pdf_pages, tolerance_pt=1.5):
    if not math.isfinite(tolerance_pt) or not 0 <= tolerance_pt <= 3:
        raise ValueError("tolerance must be finite and between zero and three points")
    results = []
    same_count = len(pdf_pages) == source["slide_count"]
    for page in source["pages"]:
        for original in page["fields"]:
            item = {**original, "slide_index": page["slide_index"],
                    "observation": "unobserved"}
            reason = item.get("unobserved_reason")
            if not same_count:
                reason = "source/PDF page counts differ; no page correspondence inferred"
            elif not reason and item["source_cache_number"] is None:
                reason = "source cache is not an unambiguous decimal number"
            if not reason:
                pdf = pdf_pages[page["slide_index"] - 1]
                sw, sh = source["slide_size_emu"]
                pw, ph = pdf["size_pt"]
                if abs((pw / ph) / (sw / sh) - 1) > 0.005:
                    reason = "page aspect ratio differs; no alignment inferred"
                else:
                    x, y, w, h = item["box_emu"]
                    box = [x * pw / sw, y * ph / sh, (x + w) * pw / sw,
                           (y + h) * ph / sh]
                    item["field_shape_box_pt"] = box
                    candidates = []
                    for word in pdf["words"]:
                        a, b, c, d = word["box_pt"]
                        cx, cy = (a + c) / 2, (b + d) / 2
                        if box[0] - tolerance_pt <= cx <= box[2] + tolerance_pt and box[1] - tolerance_pt <= cy <= box[3] + tolerance_pt and word["text"].strip():
                            candidates.append(word)
                    item["PDF_words_in_field_shape"] = candidates
                    if len(candidates) != 1 or number(candidates[0]["text"]) is None:
                        reason = "field shape does not contain exactly one decimal PDF word"
                    else:
                        item["correspondence_basis"] = "one decimal PDF word in the explicit field shape region; PDF text carries no source object ID"
                        item["rendered_number"] = number(candidates[0]["text"])
                        item["observation"] = "match" if item["rendered_number"] == item["source_cache_number"] else "disagreement"
            if reason:
                item["unobserved_reason"] = reason
            results.append(item)
    counts = {k: sum(x["observation"] == k for x in results)
              for k in ("match", "disagreement", "unobserved")}
    return {"source_field_count": len(results), "PDF_page_count": len(pdf_pages),
            "source_page_count": source["slide_count"], "counts": counts,
            "fields": results,
            "no_explicit_fields_found": not results,
            "coverage_scope": "explicit slide XML fields with supported top-level geometry only",
            "interpretation": "The correspondence is geometric, not PDF/source object identity. A cache/render disagreement is evidence, not proof which side satisfies the canonical numbering policy. A match is not canonical-policy or native-application acceptance. Inherited/master-only fields and unsupported geometry may be absent/unobserved; zero explicit fields does not establish no applicable fields. No numbers outside explicit field shapes are used."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pptx", required=True)
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--renders", required=True, help="Current render manifest binding these exact PPTX/PDF bytes")
    parser.add_argument("--output", required=True)
    parser.add_argument("--pdftotext", default="pdftotext")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    bbox = output.with_suffix(".bbox.xml")
    receipt = output.with_suffix(".pdftotext.json")
    if any(p.exists() for p in (output, bbox, receipt)):
        raise ValueError("use fresh diagnostic output paths; preserve earlier results")
    sources = {"pptx": ref(args.pptx), "pdf": ref(args.pdf)}
    manifest_ref = ref(args.renders)
    try:
        manifest = json.loads(Path(args.renders).read_text(encoding="utf-8"))
        binding = validate_pair(manifest, sources)
    except (ValueError, TypeError, AttributeError) as error:
        write_new(output, {"status": "not-observed", "source_files": sources,
                           "render_manifest": manifest_ref, "reason": str(error),
                           "PDF_text_extraction_executed": False})
        raise SystemExit(1)
    source = read_source(args.pptx)
    argv = [args.pdftotext, "-bbox-layout", args.pdf, str(bbox)]
    started = datetime.now(timezone.utc).isoformat()
    tick = time.monotonic()
    try:
        process = subprocess.run(argv, capture_output=True, timeout=60)
        observed = {"returncode": process.returncode,
                    "stdout": process.stdout.decode(errors="replace"),
                    "stderr": process.stderr.decode(errors="replace")}
    except (OSError, subprocess.TimeoutExpired) as error:
        observed = {"returncode": None, "error_type": type(error).__name__,
                    "error": str(error)}
    observed.update(argv=argv, started_at=started,
                    ended_at=datetime.now(timezone.utc).isoformat(),
                    wall_seconds=time.monotonic() - tick,
                    model=None, tokens=None, amount=None, active_seconds=None)
    write_new(receipt, observed)
    if observed["returncode"] != 0:
        write_new(output, {"status": "not-observed", "source_files": sources,
                           "command_receipt": ref(receipt),
                           "reason": "PDF text extraction failed; no acceptance inferred"})
        raise SystemExit(1)
    pages = read_pdf_words(bbox)
    if sources != {"pptx": ref(args.pptx), "pdf": ref(args.pdf)} or ref(args.renders) != manifest_ref:
        write_new(output, {"status": "not-observed", "source_files_before": sources,
                           "command_receipt": ref(receipt),
                           "reason": "source changed during observation; no correspondence accepted"})
        raise SystemExit(1)
    result = compare(source, pages)
    result.update(contract="local.slide-number-field-diagnostic/1.0",
                  status="diagnostic-only", source_files=sources,
                  render_manifest=manifest_ref, binding_scope=binding,
                  source_firstSlideNum_as_stored=source["firstSlideNum_as_stored"],
                  bbox_evidence=ref(bbox), command_receipt=ref(receipt))
    write_new(output, result)
    print(json.dumps({"status": result["status"],
                      "source_field_count": result["source_field_count"],
                      "counts": result["counts"], "report": str(output)}))


if __name__ == "__main__":
    main()
