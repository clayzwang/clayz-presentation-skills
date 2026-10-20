"""Coverage boundaries for optional, observation-only rendered-label work."""
import unittest
from packages.layout.rendered_label_occupancy import inspect_bbox


class RenderedLabelOccupancyTest(unittest.TestCase):
    def request(self, labels):
        return {"contract": "io.clayz.presentation.label-occupancy-request/1.0",
                "pages": [{"slide_id": "S1", "page_number": 1, "labels": labels}]}

    def label(self, key, text):
        return {"label_id": key, "text": text, "kind": "manual-annotation",
                "native_name": key, "search_box": [0, 0, 1, 1]}

    def test_ambiguous_and_missing_labels_are_not_silently_matched(self):
        xml = '''<html xmlns="http://www.w3.org/1999/xhtml"><page width="100" height="100">
        <line><word xMin="10" yMin="10" xMax="20" yMax="20">20</word></line>
        <line><word xMin="50" yMin="10" xMax="60" yMax="20">20</word></line>
        </page></html>'''
        result = inspect_bbox(xml, self.request([self.label("ambiguous", "20"), self.label("missing", "30")]))
        self.assertEqual(result["coverage"], {"unique": 0, "missing": 1, "ambiguous": 1})
        self.assertEqual(result["pages"][0]["measured_pairs"], [])
        self.assertEqual(result["status"], "observation-only")
        self.assertNotIn("quality_status", result)

    def test_exact_multiword_line_and_intersection_share_pdf_coordinates(self):
        xml = '''<html xmlns="http://www.w3.org/1999/xhtml"><page width="100" height="100">
        <line><word xMin="10" yMin="10" xMax="30" yMax="20">gross</word><word xMin="32" yMin="10" xMax="50" yMax="20">margin</word></line>
        <line><word xMin="40" yMin="15" xMax="60" yMax="25">+1pp</word></line>
        </page></html>'''
        result = inspect_bbox(xml, self.request([self.label("variable", "gross margin"), self.label("change", "+1pp")]))
        self.assertEqual(result["coverage"]["unique"], 2)
        pair = result["pages"][0]["possible_intersections"][0]
        self.assertEqual(pair["intersection_area_pt2"], 50)
        self.assertEqual(result["pages"][0]["labels"][0]["candidates"][0]["bounds_pt"], [10, 10, 50, 20])


if __name__ == "__main__":
    unittest.main()
