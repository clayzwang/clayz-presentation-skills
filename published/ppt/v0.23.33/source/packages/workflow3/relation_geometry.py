"""Read a declared relationship against native shapes in an actual PPTX page."""
from fractions import Fraction
import posixpath
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from .technical import NS


def slide_shapes(pptx, slide_id):
    with ZipFile(pptx) as archive:
        presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
        ids = {slide.get("id"): slide.get("{" + NS["r"] + "}id")
               for slide in presentation.findall("p:sldIdLst/p:sldId", NS)}
        relations = ET.fromstring(archive.read("ppt/_rels/presentation.xml.rels"))
        targets = {row.get("Id"): row.get("Target") for row in relations
                   if row.get("TargetMode") != "External" and row.get("Type", "").endswith("/slide")}
        target = targets[ids[str(slide_id)]]
        path = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join("ppt", target))
        if not path.startswith("ppt/slides/"):
            raise ValueError("slide must be a native part of this presentation")
        slide = ET.fromstring(archive.read(path))
    return {int(shape.find("p:nvSpPr/p:cNvPr", NS).get("id")): shape.find("p:spPr", NS)
            for shape in slide.findall("p:cSld/p:spTree/p:sp", NS)}


def bounds(properties):
    transform = properties.find("a:xfrm", NS)
    if transform is None or any(transform.get(key, "0") not in ("0", "false")
                                for key in ("rot", "flipH", "flipV")):
        raise ValueError("axis-aligned native shape coordinates are required")
    point = transform.find("a:off", NS)
    size = transform.find("a:ext", NS)
    return tuple(int(node.get(key)) for node, key in ((point, "x"), (point, "y"), (size, "cx"), (size, "cy")))


def horizontal_tip(properties, side):
    if side not in {"left", "right"}:
        raise ValueError("direction must be left or right")
    paths = properties.findall("a:custGeom/a:pathLst/a:path", NS)
    if len(paths) != 1:
        raise ValueError("a single native polygon path is required to observe a tip")
    path = paths[0]
    allowed = {"{" + NS["a"] + "}" + tag for tag in ("moveTo", "lnTo", "close")}
    if any(element.tag not in allowed for element in path):
        raise ValueError("only linear native polygon geometry has this observation")
    points = {(int(point.get("x")), int(point.get("y"))) for point in path.findall("./*/a:pt", NS)}
    extreme = (min if side == "left" else max)(x for x, y in points)
    ys = {y for x, y in points if x == extreme}
    if len(ys) != 1:
        raise ValueError("the declared side has no single tip")
    ox, oy, width, height = bounds(properties)
    return (ox + Fraction(extreme, int(path.get("w"))) * width,
            oy + Fraction(ys.pop(), int(path.get("h"))) * height)


def observe(pptx, slide_id, relation):
    """Observe a role-selected geometric cue. Semantic truth still comes from the evidence."""
    shapes = slide_shapes(pptx, slide_id)
    kind = relation["kind"]
    source = shapes[relation["source"]]
    target = relation["target"]
    if kind == "horizontal-tip-alignment":
        tip_x, y = horizontal_tip(source, relation["side"])
        source_x, _, source_width, _ = bounds(source)
        source_midpoint = source_x + Fraction(source_width, 2)
        direction = 1 if relation["side"] == "right" else -1
        if direction * (tip_x - source_midpoint) <= 0:
            raise ValueError("the native tip does not extend to the declared side")
        aligned = []
        for shape_id in [target, *relation.get("alternatives", [])]:
            x0, y0, width, height = bounds(shapes[shape_id])
            model_midpoint = x0 + Fraction(width, 2)
            if y0 <= y <= y0 + height and direction * (model_midpoint - source_midpoint) > 0:
                aligned.append(shape_id)
        return {"result": "observed" if aligned == [target] else "inconsistent",
                "aligned_native_ids": aligned, "expected_native_id": target}
    if kind == "rectangular-containment":
        geometry = source.find("a:prstGeom", NS)
        if geometry is None or geometry.get("prst") != "rect":
            raise ValueError("a native rectangular container is required")
        x, y, w, h = bounds(source)
        a, b, width, height = bounds(shapes[target])
        contains = x <= a <= a + width <= x + w and y <= b <= b + height <= y + h
        return {"result": "observed" if contains else "inconsistent", "expected_native_id": target}
    raise ValueError("unsupported relation observation")
