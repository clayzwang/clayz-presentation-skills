import pathlib,tempfile,unittest,json,hashlib
from packages.layout.knowledge_policy import load_policy
F=pathlib.Path(__file__).parent/'fixtures/font-policy'
class KnowledgePolicyRegression(unittest.TestCase):
 def test_calibration_binds_exact_declared_file(self):
  # File identity only: no installed font or target-render quality is asserted.
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);font=root/'declared-font.bin';font.write_bytes(b'synthetic-font-identity')
   policy=json.loads((F/'layout-policy.json').read_text());policy['font_sha256']=hashlib.sha256(font.read_bytes()).hexdigest()
   (root/'layout-policy.json').write_text(json.dumps(policy))
   p,r=load_policy(root,font);self.assertEqual(r['status'],'applied');self.assertEqual(p['minimum_footer_gap_pt'],10.8)
 def test_another_font_cannot_inherit_calibration(self):
  with tempfile.TemporaryDirectory() as d:
   f=pathlib.Path(d)/'other-font.ttf';f.write_bytes(b'another-font-file')
   with self.assertRaisesRegex(ValueError,'another font'):load_policy(F,f)
if __name__=='__main__':unittest.main()
