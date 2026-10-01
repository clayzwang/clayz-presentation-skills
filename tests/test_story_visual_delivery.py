"""Exercise the real calibration/assembly/publication CLI with 3.0 handoffs.

Images and PPTX are explicitly synthetic fixtures. This tests artifact
transport and evidence integrity, not production visual quality or rendering.
"""
from __future__ import annotations
import copy
import json
import sys
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests import test_calibrated_audit_adversarial as helpers
from tests.test_story_visual_handoff import synthetic_handoff, reference
from packages.validators.story_handoff import digest, spec_digest


class StoryRun(helpers.RealCliReleaseTests):
    # Helper subclass is instantiated directly, not discovered as a TestCase.
    def configure_story(self, version="3.0"):
        _,package,new_plan,_=synthetic_handoff(self.work)
        for key in ('acceptance_contract','resource_inventory','brief','index_evidence'):
            package[key]=copy.deepcopy(self.package[key])
        from packages.validators.resource_inventory import resource_inventory_signature, finalize_resource_inventory
        package['resource_inventory']['gate']['authoring_started_at']=datetime.now(timezone.utc).isoformat()
        package['resource_inventory']=finalize_resource_inventory(package['resource_inventory'])
        if version in {"3.1", "3.2"}:
            from tests.test_page_allocation_handoff import convert_to_page_handoff
            if version == "3.2":
                from tests.test_research_content_handoff import convert_to_research_handoff
                convert_to_research_handoff(package, self.plan)
            else:
                convert_to_page_handoff(package, self.plan)
            # Current delivery has no mandatory Storyline or single-line QA gate.
            for page in package['copy_layer']['slides']:
                page.pop('storyline_copy_id', None)
                for unit in page['copy_units']:
                    if unit['role'] == 'storyline':
                        unit['role'] = 'evidence'
            for slide in self.qa.get('slides', []):
                slide['checks'].pop('storyline_single_line', None)
                slide.get('not_applicable_reasons', {}).pop('storyline_single_line', None)
        origin=copy.deepcopy(package)
        origin.update(status='logic-approved',copy_layer=None)
        if version in {'3.0', '3.2'}:
            origin['logic_layer']=None
        origin.pop('logic_artifact',None)
        self.original_logic=self.work/'original-logic.json'
        self.original_logic.write_text(json.dumps(origin,ensure_ascii=False),encoding='utf-8')
        package['logic_artifact']=reference(self.original_logic)
        self.package=package
        self.package_path.write_text(json.dumps(package,ensure_ascii=False),encoding='utf-8')
        self.plan.update(contract_version='2.0',package_contract_version=version,visual_baseline=new_plan['visual_baseline'])
        self.plan['resource_inventory_lock']=resource_inventory_signature(package['resource_inventory'])
        self.resource_inventory_path.write_text(json.dumps(package['resource_inventory'],ensure_ascii=False),encoding='utf-8')
        self.plan['visual_baseline'].update(copy_package_sha256=digest(package),spec_sha256=spec_digest(self.plan),
                                           locked_at=datetime.now(timezone.utc).isoformat())
        self.plan_path.write_text(json.dumps(self.plan,ensure_ascii=False),encoding='utf-8')
        self.qa.update(visual_baseline_sha256=digest(self.plan['visual_baseline']),art_direction_plan_contract_version='2.0')

    def _run_cli(self,*args,**kwargs):
        args=list(args)
        if args and args[0]=='record-stage' and '--stage' in args:
            stage=args[args.index('--stage')+1]
            if stage=='logic' and hasattr(self,'original_logic'):
                args=[f'package={self.original_logic}' if a==f'package={self.package_path}' else a for a in args]
            if stage=='output' and hasattr(self,'original_logic'):
                self.qa['output_started_at']=datetime.now(timezone.utc).isoformat()
                self.qa_path.write_text(json.dumps(self.qa,ensure_ascii=False),encoding='utf-8')
        return super()._run_cli(*args,**kwargs)

    def _build_report(self,**kwargs):
        path=super()._build_report(**kwargs)
        value=json.loads(path.read_text(encoding='utf-8'))
        value['design_comparison']={'visual_baseline_sha256':digest(self.plan['visual_baseline']),
            'pptx_sha256':reference(self.pptx)['sha256'],
            'slides':[{'slide_id':page['slide_id'],'preview_sha256':page['image']['sha256'],
                       'status':'deferred','reason':'Synthetic CLI fixture; no actual native render comparison claimed.'}
                      for page in self.plan['visual_baseline']['slides']]}
        path.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
        return path


# Prevent inherited legacy tests from being rediscovered under this helper.
def load_tests(loader, tests, pattern):
    return loader.loadTestsFromTestCase(StoryDeliveryTests)


class StoryDeliveryTests(unittest.TestCase):
    def test_real_cli_preserves_original_logic_and_publishes_companion(self):
        self.run_handoff("3.0")

    def test_real_cli_page_allocation_and_copy_tags_publish_companion(self):
        self.run_handoff("3.1")

    def test_real_cli_research_content_and_art_publish_companion(self):
        self.run_handoff("3.2")

    def run_handoff(self, version):
        case=StoryRun('runTest')
        case.setUp()
        self.addCleanup(case.tearDown)
        case.configure_story(version)
        stages=case._record_stages_and_calibrations()
        auditor=case._write_audit_inputs(stages=stages)
        draft=case._build_report(stages=stages,auditor_path=auditor)
        case._record_supervisor(stages,draft,auditor)
        report_path=case._assemble_report(stages,draft,auditor)
        report=json.loads(report_path.read_text(encoding='utf-8'))
        self.assertEqual(report['stage_snapshots']['logic']['snapshot']['status'],'logic-approved')
        layer=report['stage_documents']['documents']['logic']['content']['logic_layer']
        if version in {'3.0', '3.2'}:
            self.assertIsNone(layer)
        else:
            self.assertEqual(layer,case.package['logic_layer'])
            self.assertNotIn('page_message_tree',layer['slides'][0])
        output=case.work/'published-story'
        case._run_cli(case.package_path,case.plan_path,case.qa_path,case.inventory_path,report_path,
                      '--pptx',case.pptx,'--runtime-preflight',case.preflight_path,'--config',case.config_path,
                      '--render-root',case.render_root,'--output-dir',output)
        case._run_cli('verify-handoff','--bundle',output)
        with zipfile.ZipFile(output/'stage-handoff.zip') as archive:
            self.assertIn('comparison.html',archive.namelist())
            self.assertIn('logic.md',archive.namelist())
            self.assertIn('images/001-design.png',archive.namelist())
        # Hashing a companion in the manifest cannot conceal changed contents.
        (output/'stage-handoff.zip').write_bytes(b'changed companion')
        self.assertNotEqual(case._run_cli('verify-handoff','--bundle',output,expected=1).returncode,0)


if __name__=='__main__':
    unittest.main()
