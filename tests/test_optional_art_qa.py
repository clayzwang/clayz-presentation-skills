"""Applicability only: partial fixtures do not establish rendered quality."""
import tempfile,unittest
from pathlib import Path
from tests.test_release_0180 import clean_handoff
from packages.validators.validate_output_qa import validate_qa,CHECK_KEYS

class OptionalArtQATest(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
  _,self.package,self.plan=clean_handoff(Path(t.name))
  self.package['contract_version']='3.4';self.plan['contract_version']='2.3'
  self.keys=['art_direction_area_plan_fidelity','purposeful_series_fidelity','semantic_whitespace_fidelity','motif_fidelity','semantic_layout_tree_fidelity']
  self.qa={'contract_version':'4.1','slides':[{'slide_id':self.package['copy_layer']['slides'][0]['slide_id'],'checks':{k:('not-applicable' if k in self.keys else 'pass') for k in CHECK_KEYS},'not_applicable_reasons':{k:'Optional Art input was not used in this synthetic fixture.' for k in self.keys},'issues_remaining':[]}]}
 def gaps(self):return [str(e) for e in validate_qa(self.package,self.plan,self.qa) if 'body slide check was not performed' in str(e)]
 def test_absent_optional_inputs_do_not_force_old_preset_checks(self):
  self.assertEqual([],self.gaps())
 def test_used_area_plan_cannot_be_marked_not_applicable(self):
  self.plan['slides'][0]['area_plan']={'region_id':'declared-region'}
  self.assertTrue(any('art_direction_area_plan_fidelity' in e for e in self.gaps()))
 def test_actual_font_check_remains_required(self):
  self.qa['slides'][0]['checks']['font_size_discipline']='not-applicable'
  self.qa['slides'][0]['not_applicable_reasons']['font_size_discipline']='Synthetic attempted omission.'
  self.assertTrue(any('font_size_discipline' in e for e in self.gaps()))
