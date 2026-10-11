import pathlib,json,hashlib,unittest,copy
import tempfile
from PIL import Image
from packages.validators.visual_evidence import validate,CATEGORIES
class VisualGateRegression(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.png=pathlib.Path(t.name)/'synthetic.png';Image.new('RGB',(40,30),'white').save(self.png)
 def data(self):
  p=self.png;ref=dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size);obs='Synthetic review: the declared comparison requires repair; this image does not establish a visual judgment.'
  review={'pptx_sha256':'example-binding','pages':{'S05':{k:{'status':'pass','observation':obs,'evidence':[ref.copy()]} for k in CATEGORIES}}};manifest={'pptx_sha256':'example-binding','slides':[dict(slide_id='S05',**ref)]};return review,manifest
 def test_reported_reader_failure_cannot_release(self):
  r,m=self.data();r['pages']['S05']['comparison']['status']='fail';self.assertTrue(any('requires repair' in e for e in validate(r,['S05'],m)))
 def test_changed_image_reference_cannot_release(self):
  r,m=self.data();r['pages']['S05']['legibility']['evidence'][0]['sha256']='0'*64;self.assertTrue(any('identity mismatch' in e for e in validate(r,['S05'],m)))
if __name__=='__main__':unittest.main()
