import json,pathlib,unittest
from packages.validators.page_capacity import inspect
F=pathlib.Path(__file__).parent/'fixtures/native-bounds'
class CapacityRegression(unittest.TestCase):
 def test_real_nvidia_cover_source_region_is_detected(self):
  r=inspect(json.loads((F/'r05-nvidia.json').read_text()))
  self.assertFalse(r['ok']);self.assertTrue(any(x['slide_id']=='S01' and x['gap_pt']<0 for x in r['findings']))
 def test_real_meta_pages_keep_source_clearance(self):
  r=inspect(json.loads((F/'r04-meta.json').read_text()))
  self.assertTrue(r['ok'],r['findings'])
if __name__=='__main__':unittest.main()
