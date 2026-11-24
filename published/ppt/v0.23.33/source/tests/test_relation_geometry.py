"""Synthetic native geometry checks. No source slides or reader answers."""
from pathlib import Path
import sys
from zipfile import ZipFile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.workflow3.relation_geometry import observe
from packages.workflow3.technical import NS


def shape(shape_id, x, y, w, h, geometry):
    return f"""<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}"/></p:nvSpPr><p:spPr>
    <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>
    {geometry}</p:spPr></p:sp>"""


RECT = '<a:prstGeom prst="rect"/>'
TIP = """<a:custGeom><a:pathLst><a:path w="100" h="100">
<a:moveTo><a:pt x="0" y="0"/></a:moveTo><a:lnTo><a:pt x="85" y="0"/></a:lnTo>
<a:lnTo><a:pt x="100" y="40"/></a:lnTo><a:lnTo><a:pt x="85" y="100"/></a:lnTo>
<a:lnTo><a:pt x="0" y="100"/></a:lnTo><a:close/></a:path></a:pathLst></a:custGeom>"""


def make_deck(tmp_path, source_geometry):
    path = tmp_path / "synthetic.pptx"
    with ZipFile(path, "x") as z:
        z.writestr("ppt/presentation.xml", f"""<p:presentation xmlns:p="{NS["p"]}" xmlns:r="{NS["r"]}">
        <p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst></p:presentation>""")
        z.writestr("ppt/_rels/presentation.xml.rels", f"""<Relationships>
        <Relationship Id="rId1" Type="{NS["r"]}/slide" Target="slides/slide1.xml"/></Relationships>""")
        z.writestr("ppt/slides/slide1.xml", f"""<p:sld xmlns:p="{NS["p"]}" xmlns:a="{NS["a"]}">
        <p:cSld><p:spTree>{shape(2, 0, 0, 100, 100, source_geometry)}
        {shape(3, 72, 30, 18, 20, RECT)}{shape(4, 8, 30, 18, 20, RECT)}
        {shape(5, 108, 30, 18, 20, RECT)}</p:spTree></p:cSld></p:sld>""")
    return path


def test_selected_direction_points_to_the_declared_endpoint(tmp_path):
    deck = make_deck(tmp_path, TIP)
    relation = {"kind": "horizontal-tip-alignment", "source": 2, "target": 3,
                "side": "right", "alternatives": [4]}
    assert observe(deck, 256, relation) == {
        "result": "observed", "aligned_native_ids": [3], "expected_native_id": 3}
    assert observe(deck, 256, {**relation, "target": 4, "alternatives": [3]})["result"] == "inconsistent"
    with pytest.raises(ValueError, match="no single tip"):
        observe(deck, 256, {**relation, "side": "left"})


def test_a_rectangle_can_be_the_actual_containment_cue(tmp_path):
    deck = make_deck(tmp_path, RECT)
    relation = {"kind": "rectangular-containment", "source": 2, "target": 3}
    assert observe(deck, 256, relation)["result"] == "observed"
    assert observe(deck, 256, {**relation, "target": 5})["result"] == "inconsistent"
    with pytest.raises(ValueError, match="single native polygon"):
        observe(deck, 256, {"kind": "horizontal-tip-alignment", "source": 2, "target": 3, "side": "right"})
