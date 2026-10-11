import hashlib,json,pathlib,tempfile,unittest
from packages.validators.logic_knowledge import lookup
class LogicKnowledgeTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name)
  self.node=dict(code='P.ONE',kind='PRINCIPLE',principle='说明谁交付什么。')
  p=self.root/'nodes.json';p.write_text(json.dumps(dict(nodes=[self.node])))
  (self.root/'manifest.json').write_text(json.dumps(dict(nodes='nodes.json',version='test',files={'nodes.json':hashlib.sha256(p.read_bytes()).hexdigest()})))
  self.selection=dict(selections=[dict(code='P.ONE',reason='陌生行业',decision='先研究产品与交付')])
 def tearDown(self):self.tmp.cleanup()
 def test_returns_exact_selected_reference(self):
  result=lookup(self.root,self.selection);self.assertEqual(result['selected'][0]['record'],self.node);self.assertEqual(result['status'],'retrieved-reference-only')
 def test_modified_nodes_rejected(self):
  (self.root/'nodes.json').write_text('{}')
  with self.assertRaisesRegex(ValueError,'hash mismatch'):lookup(self.root,self.selection)
 def test_unknown_selection_rejected(self):
  self.selection['selections'][0]['code']='P.MISSING'
  with self.assertRaisesRegex(ValueError,'unknown'):lookup(self.root,self.selection)
 def test_missing_case_cannot_be_inferred(self):
  self.selection['case_ids']=['CASE.MISSING']
  with self.assertRaisesRegex(ValueError,'index missing'):lookup(self.root,self.selection)
 def test_only_requested_case_is_returned(self):
  p=self.root/'industry-research-cases.json';p.write_text(json.dumps(dict(cases=[dict(case_id='ONE',industry='行业一'),dict(case_id='TWO',industry='行业二')])))
  m=self.root/'manifest.json';v=json.loads(m.read_text());v['files'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest();m.write_text(json.dumps(v))
  self.selection['case_ids']=['TWO'];r=lookup(self.root,self.selection)
  self.assertEqual([c['case_id'] for c in r['selected_cases']],['TWO'])
if __name__=='__main__':unittest.main()
