"""3.1 ownership and evidence regressions; fixtures are synthetic, not quality claims."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from tests.test_story_visual_handoff import synthetic_handoff, reference
from packages.validators.story_handoff import digest, spec_digest
from packages.validators.validate_logic_package import validate_package as validate_logic
from packages.validators.validate_ppt_package import validate_package as validate_copy
from packages.validators.validate_art_direction_plan import validate_plan


def convert_to_page_handoff(package, plan):
    package['contract_version']='3.1'
    old=package['logic_layer']
    package['logic_layer']={'lock':{'slide_order_locked':True},'slides':[
        {'slide_id':p['slide_id'],'chapter_id':'C1','narrative_role':p['narrative_role'],
         'claim':p['claim'],'source_story_ids':['B1'],'data':copy.deepcopy(p['data'])}
        for p in old['slides']]}
    package['copy_layer']['pagination_owner']='logic'
    for page, design in zip(package['copy_layer']['slides'], plan['slides']):
        page.pop('speaker_notes',None)
        page.pop('node_copy_map',None)
        for unit in page['copy_units']:
            unit.pop('source_logic_node_ids',None)
        design['visual_layers']=[{'node_id':u['copy_id'],'layer':next(m['visual_role'] for m in design['copy_unit_map'] if m['copy_id']==u['copy_id'])} for u in page['copy_units']]
        design['page_message_tree_depth']=max(u['logic_level'] for u in page['copy_units'])
        design['logic_statement']=package['logic_layer']['slides'][0]['claim']
    plan['package_contract_version']='3.1'
    package['story']['chapters'][0].pop('transition',None)
    package['copy_layer']['story_sha256']=digest(package['story'])


class PageAllocationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        _,self.package,self.plan,self.qa=synthetic_handoff(self.folder)
        convert_to_page_handoff(self.package,self.plan)
        self.origin=copy.deepcopy(self.package)
        self.origin.update(status='logic-approved',copy_layer=None)
        self.origin.pop('logic_artifact',None)
        self.bind()

    def bind(self):
        path=self.folder/'logic31.json';path.write_text(json.dumps(self.origin),encoding='utf-8')
        self.package['logic_artifact']=reference(path)
        self.plan['visual_baseline'].update(copy_package_sha256=digest(self.package),spec_sha256=spec_digest(self.plan))

    def test_simple_logic_and_copy_owned_tags_reach_art(self):
        self.assertEqual([],validate_logic(self.origin))
        self.assertEqual([],validate_copy(self.package))
        self.assertEqual([],validate_plan(self.package,self.plan))
        self.assertNotIn('page_message_tree',self.origin['logic_layer']['slides'][0])
        self.assertNotIn('reasoning_contracts',self.origin['logic_layer']['slides'][0])
        self.assertNotIn('speaker_notes',self.package['copy_layer']['slides'][0])

    def test_storyline_optional_and_copy_breaks_independent(self):
        page = self.package['copy_layer']['slides'][0]
        for unit in page['copy_units']:
            unit['intentional_line_breaks'] = [2, 5]
        for mapping in self.plan['slides'][0]['copy_unit_map']:
            mapping['intentional_line_breaks'] = [2, 5]
        self.bind()
        self.assertEqual([], validate_copy(self.package))
        page.pop('storyline_copy_id', None)
        for unit in page['copy_units']:
            if unit['role'] == 'storyline':
                unit['role'] = 'evidence'
            unit['intentional_line_breaks'] = [2, 5]
        for mapping in self.plan['slides'][0]['copy_unit_map']:
            mapping['intentional_line_breaks'] = [2, 5]
        self.bind()
        self.assertEqual([], validate_copy(self.package))
        self.assertEqual([], validate_plan(self.package, self.plan))
        self.assertEqual(self.origin['logic_layer'], self.package['logic_layer'])
        page['storyline_copy_id'] = None
        self.bind()
        self.assertEqual([], validate_copy(self.package))

    def test_single_line_qa_check_optional_only_for_current_contract(self):
        from validate_output_qa import validate_qa, CHECK_KEYS
        qa = copy.deepcopy(self.qa)
        qa['slides'] = [{'slide_id': self.package['logic_layer']['slides'][0]['slide_id'],
                         'checks': {key: 'pass' for key in CHECK_KEYS - {'storyline_single_line'}},
                         'not_applicable_reasons': {}}]
        # This deliberately partial QA has unrelated missing evidence; isolate
        # the required-key behavior while using the real QA validator.
        errors = validate_qa(self.package, self.plan, qa)
        self.assertFalse(any('storyline_single_line' in e for e in errors), errors)
        qa['slides'][0]['checks']['storyline_single_line'] = 'not-applicable'
        self.assertTrue(any('storyline_single_line' in e for e in validate_qa(self.package, self.plan, qa)))
        qa['slides'][0]['not_applicable_reasons']['storyline_single_line'] = 'No user-selected master imposes a single-line Storyline.'
        self.assertFalse(any('storyline_single_line' in e for e in validate_qa(self.package, self.plan, qa)))
        qa['slides'][0]['checks'].pop('storyline_single_line')
        self.package['contract_version'] = '3.0'
        self.assertTrue(any('storyline_single_line' in e for e in validate_qa(self.package, self.plan, qa)))

    def test_copy_cannot_rewrite_page_claim_or_allocation(self):
        self.package['logic_layer']['slides'][0]['claim']='Different claim'
        self.assertTrue(any('immutable Logic logic_layer' in e for e in validate_copy(self.package)))

    def test_every_story_block_has_a_location_before_copy(self):
        self.origin['story']['chapters'][0]['blocks'].append(dict(self.origin['story']['chapters'][0]['blocks'][0],story_id='B2',must_preserve=False))
        self.assertTrue(any('every story block' in e for e in validate_logic(self.origin)))

    def test_cover_and_closing_default_and_explicit_omission(self):
        self.origin['acceptance_contract']['cover_policy'].update(cover_required=True,closing_required=True)
        from packages.validators.acceptance_contract import acceptance_contract_digest
        self.origin['acceptance_contract']['contract_sha256']=acceptance_contract_digest(self.origin['acceptance_contract'])
        self.assertTrue(any('one cover' in e for e in validate_logic(self.origin)))
        body=self.origin['logic_layer']['slides'][0]
        self.origin['logic_layer']['slides']=[dict(body,slide_id='COVER',narrative_role='cover'),body,dict(body,slide_id='CLOSE',narrative_role='closing')]
        self.origin['logic_layer']['slides'][0]['data']=[]
        self.origin['logic_layer']['slides'][-1]['data']=[]
        self.assertEqual([],validate_logic(self.origin))

    def test_copy_cycle_and_missing_art_tag_fail(self):
        unit=self.package['copy_layer']['slides'][0]['copy_units'][0]
        unit['parent_copy_id']=unit['copy_id']
        self.assertTrue(any('cyclic' in e for e in validate_copy(self.package)))
        unit['parent_copy_id']=None
        self.bind();self.plan['slides'][0]['visual_layers'].pop()
        self.plan['visual_baseline']['spec_sha256']=spec_digest(self.plan)
        self.assertTrue(any('map every' in e for e in validate_plan(self.package,self.plan)))

    def test_source_facts_still_require_evidence(self):
        self.origin['story']['chapters'][0]['blocks'][0]['source_ids']=[]
        self.assertTrue(any('require sources' in e for e in validate_logic(self.origin)))

    def test_no_builtin_narrative_template_required(self):
        from packages.validators.acceptance_contract import acceptance_contract_digest
        self.origin['acceptance_contract']['narrative_policy']={}
        self.origin['acceptance_contract']['contract_sha256']=acceptance_contract_digest(self.origin['acceptance_contract'])
        self.assertEqual([],validate_logic(self.origin))

    def test_required_content_cannot_be_hidden_in_notes(self):
        units=self.package['copy_layer']['slides'][0]['copy_units']
        self.package['copy_layer']['slides'][0]['speaker_notes']=[{'text':'Only in notes', 'source_story_ids':['B1']}]
        for unit in units:
            unit['source_story_ids']=[]
        self.assertTrue(any('required story block' in e for e in validate_copy(self.package)))

    def test_copy_can_create_its_own_group_but_art_must_follow(self):
        page=self.package['copy_layer']['slides'][0]
        parent,child=page['copy_units'][:2]
        child.update(parent_copy_id=parent['copy_id'],logic_level=parent['logic_level']+1,sibling_group_id='Copy-owned-group')
        self.assertEqual([],validate_copy(self.package))
        self.bind()
        self.assertTrue(any('parent_render_target_id mismatch' in e for e in validate_plan(self.package,self.plan)))

    def test_version_cannot_be_relabelled_to_bypass_ownership(self):
        self.origin['contract_version']='3.0';self.bind()
        self.assertTrue(any('contract version' in e for e in validate_copy(self.package)))
