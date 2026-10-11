import unittest
from packages.validators import reader_review as rr
from tests import test_reader_review as fixtures

class ReaderSnapshotTest(unittest.TestCase):
 def setUp(self):
  self.fixture=fixtures.ReaderReviewTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
 def test_original_working_files_can_change_without_destroying_prior_reading(self):
  f=self.fixture;packet=rr.read(f.packet('final'));old=f.png.read_bytes()
  f.pptx.write_bytes(b'next prototype');f.png.write_bytes(b'next image');f.package.write_text('{}');f.renders.write_text('{}')
  payload=rr.validate_packet(packet)
  self.assertEqual(payload['pages'][0]['slide_id'],'S01')
  self.assertEqual(rr.load_ref(packet['renders'])['slides'][0]['sha256'],rr.ref(f.root/'final-packet-sources/rendered/S01.png')['sha256'])
  self.assertEqual((f.root/'final-packet-sources/rendered/S01.png').read_bytes(),old)
 def test_snapshot_is_outside_blind_input(self):
  f=self.fixture;packet=rr.read(f.packet('final'))
  from pathlib import Path
  blind=Path(packet['input']['path']).parent
  self.assertFalse(Path(packet['package']['path']).is_relative_to(blind))
  self.assertFalse(Path(packet['pptx']['path']).is_relative_to(blind))
 def test_identical_preparation_is_idempotent_but_changed_original_rejected(self):
  f=self.fixture;p=f.packet('final');rr.prepare_packet(phase='final',package=f.package,brief=f.brief,directory=f.root/'final-input',output=p,pptx=f.pptx,renders=f.renders)
  f.pptx.write_bytes(b'changed')
  with self.assertRaises(FileExistsError):rr.prepare_packet(phase='final',package=f.package,brief=f.brief,directory=f.root/'final-input',output=p,pptx=f.pptx,renders=f.renders)

if __name__=='__main__':unittest.main()
