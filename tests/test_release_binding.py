"""Synthetic transport checks; this does not open or certify an Office file."""
import pathlib,hashlib,tempfile,unittest
from packages.validators.release_evidence import inspect
class ReleaseBindingRegression(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);root=pathlib.Path(t.name)
  self.pptx=root/'current-pptx.bin';self.pptx.write_bytes(b'synthetic-current-pptx')
  self.pdf=root/'current-pdf.bin';self.pdf.write_bytes(b'synthetic-current-pdf')
  ph=hashlib.sha256(self.pptx.read_bytes()).hexdigest();dh=hashlib.sha256(self.pdf.read_bytes()).hexdigest()
  self.reports={n:{'ok':True,'pptx_sha256':ph} for n in ['native-comparison','font-name-audit','cjk-render-report','size-audit','object-inventory','font-environment','pdf-text-check']}
  self.reports['cjk-render-report']['pdf_sha256']=dh;self.reports['pdf-text-check']['pdf']={'sha256':dh}
  self.manifest={'pptx_sha256':ph}
 def test_reports_bind_current_file_bytes(self):
  r=inspect(self.pptx,self.pdf,self.reports,self.manifest);self.assertTrue(r['ok'],r['errors'])
 def test_stale_native_record_stops_release(self):
  self.reports['native-comparison']['pptx_sha256']='0'*64;r=inspect(self.pptx,self.pdf,self.reports,self.manifest);self.assertFalse(r['ok']);self.assertTrue(any('native-comparison' in e for e in r['errors']))
if __name__=='__main__':unittest.main()
