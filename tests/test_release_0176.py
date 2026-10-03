"""Synthetic object regressions for table identity and complete font scope."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages/validators"))
sys.path.insert(0, str(ROOT))
from audit_ppt_font_names import audit_font_names
from validate_art_direction_plan import validate_plan
from validate_output_qa import pptx_inventories, pptx_table_dimensions, validate_tabular_inventory
from packages.adapters.python_pptx.render import render, _ensure_east_asian_run_fonts
from test_font_name_audit import SLIDE_XML, THEME_XML, _config

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
C = "http://schemas.openxmlformats.org/drawingml/2006/chart"


def chart_xml(latin="STKaiti", ea="STKaiti", override=""):
    east = f'<a:ea typeface="{ea}"/>' if ea else ""
    return f'''<c:chartSpace xmlns:c="{C}" xmlns:a="{A}">
    <c:chart><c:plotArea><c:barChart><c:dLbls><c:showVal val="1"/></c:dLbls></c:barChart>
    <c:catAx>{override}</c:catAx><c:valAx/></c:plotArea><c:legend/></c:chart>
    <c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr><a:latin typeface="{latin}"/>{east}</a:defRPr></a:pPr></a:p></c:txPr>
    </c:chartSpace>'''


def package(path, slide=None, chart=None):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("ppt/slides/slide1.xml", slide or SLIDE_XML.format(font="STKaiti"))
        z.writestr("ppt/theme/theme1.xml", THEME_XML)
        if chart:
            z.writestr("ppt/charts/chart1.xml", chart)


class FontScope176Tests(unittest.TestCase):
    def audit(self, slide=None, chart=None):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "synthetic.pptx"
            package(p, slide, chart)
            return audit_font_names(p, _config())

    def test_latin_and_digits_are_checked_even_without_cjk(self):
        for text in ("Revenue", "123.4%"):
            with self.subTest(text=text):
                slide = SLIDE_XML.format(font="WrongFont").replace("中文字体检查", text)
                r = self.audit(slide=slide)
                self.assertEqual(r["visible_cjk_chars"], 0)
                self.assertEqual(r["font_name_status"], "fail")

    def test_native_table_numeric_cells_cannot_hide_from_font_audit(self):
        slide = f'<root xmlns:a="{A}"><a:tbl><a:tr><a:tc><a:txBody><a:p><a:r><a:rPr><a:latin typeface="WrongFont"/></a:rPr><a:t>42</a:t></a:r></a:p></a:txBody></a:tc></a:tr></a:tbl></root>'
        r = self.audit(slide=slide)
        self.assertEqual(r["coverage"]["native_table_count"], 1)
        self.assertEqual(r["font_scope_findings"][0]["scope"], "table")
        self.assertEqual(r["font_name_status"], "fail")

    def test_body_pass_does_not_hide_chart_missing_east_asian(self):
        r = self.audit(chart=chart_xml(ea=None))
        self.assertEqual(r["visible_cjk_chars"], r["conforming_cjk_chars"])
        self.assertEqual(r["font_name_status"], "deferred")
        self.assertTrue(all(x["font_field"] == "ea" for x in r["font_scope_findings"]))

    def test_chart_local_override_beats_correct_global_font(self):
        override = '<c:txPr><a:p><a:pPr><a:defRPr><a:ea typeface="WrongFont"/></a:defRPr></a:pPr></a:p></c:txPr>'
        r = self.audit(chart=chart_xml(override=override))
        self.assertEqual(r["font_name_status"], "fail")
        self.assertEqual(r["font_scope_findings"][0]["observed_typeface"], "WrongFont")

    def test_global_chart_font_covers_generated_labels_ticks_and_legend(self):
        r = self.audit(chart=chart_xml(ea="华文楷体"))
        self.assertTrue(r["ok"])
        self.assertEqual(r["coverage"]["chart_parts"], ["ppt/charts/chart1.xml"])
        locations = [x["location"] for x in r["font_scope_checks"]]
        for name in ("catAx", "valAx", "legend", "dLbls"):
            self.assertTrue(any(x.startswith(name + "[") for x in locations))

    def test_chart_rich_title_override_is_checked(self):
        chart = chart_xml().replace('<c:plotArea>', '<c:title><c:tx><c:rich><a:p><a:r><a:rPr><a:latin typeface="WrongFont"/></a:rPr><a:t>Title 2026</a:t></a:r></a:p></c:rich></c:tx></c:title><c:plotArea>')
        self.assertEqual(self.audit(chart=chart)["font_name_status"], "fail")

    def test_repair_preserves_explicit_east_asian_override(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthetic.pptx"
            package(path, chart=chart_xml(ea="ExplicitOtherFont"))
            _ensure_east_asian_run_fonts(path)
            self.assertEqual(audit_font_names(path, _config())["font_name_status"], "fail")

    def test_adapter_writes_native_chart_and_table_with_all_font_fields(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            opts = {"x": 0.5, "y": 1, "w": 8, "h": 4, "fontFace": "STKaiti", "fontSize": 16}
            manifest = {"contract": "io.clayz.presentation.render-manifest/1.0", "presentation": {"layout": "LAYOUT_WIDE"}, "slides": [
                {"slide_id": "table", "objects": [{"object_id": "comparison", "type": "table", "rows": [["业务", "2026"], ["合成样本", "42"]], "options": opts}]},
                {"slide_id": "chart", "objects": [{"object_id": "trend", "type": "chart", "chart_type": "column", "series": [{"name": "示例", "labels": ["甲", "乙"], "values": [12, -3]}], "options": {**opts, "showLegend": True, "showValue": True}}]},
            ]}
            source, output = root / "manifest.json", root / "deck.pptx"
            source.write_text(json.dumps(manifest))
            render(source, output)
            report = audit_font_names(output, _config())
            self.assertTrue(report["ok"], report["font_scope_findings"])
            self.assertEqual(pptx_inventories(output)[0]["native-table"], 1)
            self.assertEqual(pptx_table_dimensions(output)[0], [(2, 2)])
            with zipfile.ZipFile(output) as z:
                chart = ET.fromstring(z.read("ppt/charts/chart1.xml"))
                self.assertEqual(chart.find('.//{' + C + '}showVal').get('val'), '1')
                self.assertTrue(chart.findall('.//{' + A + '}ea'))


class TableAndCapacity176Tests(unittest.TestCase):
    def test_qualitative_shape_table_is_rejected_without_numeric_contract(self):
        plan = {"dominant_medium": "table", "medium_execution_contract": {"structure_type": "table"}}
        errors = []
        validate_tabular_inventory(plan, "table", {"shape": 24, "native-table": 0}, "slide", errors)
        self.assertTrue(errors)
        errors = []
        validate_tabular_inventory(plan, "table", {"native-table": 1}, "slide", errors, [(4, 3)])
        self.assertEqual(errors, [])

    def test_native_one_cell_fragments_do_not_pass_integrated_table_check(self):
        errors = []
        validate_tabular_inventory({}, "table", {"native-table": 12}, "slide", errors, [(1, 1)] * 12)
        self.assertTrue(errors)

    def test_real_change_of_presentation_allows_native_shapes(self):
        errors = []
        validate_tabular_inventory({"dominant_medium": "relationship-diagram", "medium_execution_contract": {"structure_type": "process"}}, "process", {"native-table": 0, "shape": 4}, "slide", errors)
        self.assertEqual(errors, [])

    def test_approved_alternative_cannot_keep_tabular_form(self):
        package = json.loads((ROOT / "tests/fixtures/synthetic-copy-package.json").read_text())
        plan = json.loads((ROOT / "tests/fixtures/synthetic-art-direction-plan.json").read_text())
        slide = plan["slides"][0]
        slide["dominant_medium"] = "table"
        slide["medium_execution_contract"].update({"structure_type": "table", "mapping_mode": "mixed", "required_object_types": ["shape"], "minimum_object_counts": {"shape": 4}, "approved_alternative": {"from_object_type": "native-table", "to_object_type": "shape", "approved_by": "art-direction", "reason": "synthetic regression"}})
        errors = validate_plan(package, plan)
        self.assertTrue(any("cannot retain tabular form" in x for x in errors), errors)

    def test_invalid_internal_reserve_is_rejected_and_legacy_defaults_remain(self):
        spec = importlib.util.spec_from_file_location("config176", ROOT / "scripts/validate_config.py")
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        config = json.loads((ROOT / "config/default.json").read_text())
        self.assertAlmostEqual(config["layout"]["internal_content_reserve_ratio"], 0.10)
        for value in (True, -0.1, 1, "10%"):
            config["layout"]["internal_content_reserve_ratio"] = value
            self.assertTrue(any("internal_content_reserve_ratio" in e for e in module.validate(config)))
        del config["layout"]["internal_content_reserve_ratio"]
        self.assertEqual(module.validate(config), [])


if __name__ == "__main__":
    unittest.main()
