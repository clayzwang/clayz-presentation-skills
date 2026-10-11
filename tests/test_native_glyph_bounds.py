import json,pathlib,unittest
from packages.validators.native_glyph_bounds import inspect_bbox
F=pathlib.Path(__file__).parent/'fixtures/native-bounds'
class NativeBoundsRegression(unittest.TestCase):
 def test_real_amazon_horizontal_overrun_detected(self):
  name='r03-amazon';r=inspect_bbox((F/(name+'.html')).read_bytes(),json.loads((F/(name+'.json')).read_text()))
  self.assertTrue(any(x['overrun_pt'].get('right',0)>30 for x in r['frame_spills']))
 def test_real_meta_horizontal_repair_and_vertical_limit_visible(self):
  name='r04-meta';r=inspect_bbox((F/(name+'.html')).read_bytes(),json.loads((F/(name+'.json')).read_text()))
  self.assertFalse(r['unmatched_lines']);self.assertFalse(any('right' in x['overrun_pt'] for x in r['frame_spills']));self.assertTrue(any('bottom' in x['overrun_pt'] for x in r['frame_spills']))
 def test_real_nvidia_duplicate_source_line_uses_both_coordinates(self):
  name='r05-nvidia';r=inspect_bbox((F/(name+'.html')).read_bytes(),json.loads((F/(name+'.json')).read_text()))
  self.assertFalse(r['unmatched_lines']);self.assertFalse(r['frame_spills']);self.assertGreater(r['matched_table_line_count'],0)
 def test_real_tesla_includes_table_cells(self):
  name='r08-tesla';r=inspect_bbox((F/(name+'.html')).read_bytes(),json.loads((F/(name+'.json')).read_text()))
  self.assertFalse(r['unmatched_lines']);self.assertFalse(r['frame_spills']);self.assertGreater(r['matched_table_line_count'],30)
if __name__=='__main__':unittest.main()
