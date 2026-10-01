"""3.2 responsibility boundaries. Synthetic examples do not assert prose quality."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from tests.test_story_visual_handoff import synthetic_handoff, reference
from tests.test_page_allocation_handoff import convert_to_page_handoff
from packages.validators.story_handoff import digest, spec_digest, render_document
from packages.validators.validate_logic_package import validate_package as validate_logic
from packages.validators.validate_ppt_package import validate_package as validate_copy
from packages.validators.validate_art_direction_plan import validate_plan


def convert_to_research_handoff(package, plan):
    convert_to_page_handoff(package, plan)
    story = package.pop('story')
    package['contract_version'] = '3.2'
    package['research'] = {k: copy.deepcopy(story[k]) for k in ('sources','glossary','metric_dictionary','open_items','invariants')}
    data = [copy.deepcopy(item) for page in package['logic_layer']['slides'] for item in page['data']]
    package['research'].update(research_question='What did the synthetic pilot establish?', scope='Synthetic source only.', summary=story['thesis'], data=data,
        findings=[dict(finding_id=b['story_id'], question='What does the evidence establish?', text=b['text'], claim_status=b['claim_status'],
            source_ids=b['source_ids'], qualifiers=b['qualifiers'], must_preserve=b['must_preserve'],data_ids=[x['data_id'] for x in data])
            for chapter in story['chapters'] for b in chapter['blocks']])
    package['logic_layer']['owner'] = 'copy'
    for page in package['logic_layer']['slides']:
        page['source_finding_ids'] = page.pop('source_story_ids')
    layer=package['copy_layer']
    layer.pop('story_sha256')
    layer.update(pagination_owner='copy',research_sha256=digest(package['research']),
        chapters=[dict(chapter_id='C1',title='Pilot outcome',purpose='Explain the result to a reader.')])
    for page in layer['slides']:
        for unit in page['copy_units'] + page.get('speaker_notes',[]):
            unit['source_finding_ids']=unit.pop('source_story_ids')
    plan['package_contract_version']='3.2'


class ResearchContentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        _,self.package,self.plan,self.qa=synthetic_handoff(self.folder)
        convert_to_research_handoff(self.package,self.plan)
        self.origin=copy.deepcopy(self.package)
        self.origin.update(status='logic-approved',logic_layer=None,copy_layer=None)
        self.origin.pop('logic_artifact',None)
        self.bind()

    def bind(self):
        path=self.folder/'research.json';path.write_text(json.dumps(self.origin),encoding='utf-8')
        self.package['logic_artifact']=reference(path)
        self.plan['visual_baseline'].update(copy_package_sha256=digest(self.package),spec_sha256=spec_digest(self.plan))

    def test_research_without_pages_reaches_copy_and_art(self):
        self.assertEqual([],validate_logic(self.origin))
        self.assertEqual([],validate_copy(self.package))
        self.assertEqual([],validate_plan(self.package,self.plan))
        self.assertIn('What did the synthetic pilot establish?',render_document('logic',self.origin))
        self.assertNotIn('## S01:',render_document('logic',self.origin))

    def test_logic_cannot_allocate_pages_or_use_presentation_story(self):
        self.origin['logic_layer']=self.package['logic_layer']
        self.assertTrue(any('must not preallocate' in e for e in validate_logic(self.origin)))
        self.origin['logic_layer']=None
        self.origin['research']['slides']=[]
        self.assertTrue(any('presentation organization' in e for e in validate_logic(self.origin)))
        self.origin['research'].pop('slides')
        self.origin['story']={'title':'PPT title'}
        self.assertTrue(any('not a Logic-authored' in e for e in validate_logic(self.origin)))

    def test_copy_owns_titles_chapters_order_and_split(self):
        layer=self.package['copy_layer'];page=layer['slides'][0]
        page['copy_units'][0]['text']='A clearer title of the same research result'
        second=copy.deepcopy(page)
        mapping={u['copy_id']:'SECOND-'+u['copy_id'] for u in second['copy_units']}
        second['slide_id']='S02'
        for u in second['copy_units']:
            u['copy_id']=mapping[u['copy_id']]
            u['parent_copy_id']=mapping.get(u['parent_copy_id'])
        for key in ['title_copy_id','storyline_copy_id']:
            second[key]=mapping.get(second.get(key))
        second['footnote_copy_ids']=[mapping[c] for c in second['footnote_copy_ids']]
        layer['slides'].insert(0,second)
        projection=copy.deepcopy(self.package['logic_layer']['slides'][0]);projection['slide_id']='S02'
        self.package['logic_layer']['slides'].insert(0,projection)
        layer['chapters'][0]['title']='Copy changed the content chapter'
        self.assertEqual([],validate_copy(self.package))
        self.assertIsNone(self.origin['logic_layer'])

    def test_copy_cannot_change_meaning_or_data_even_with_new_hash(self):
        self.package['research']['summary']='An unsupported stronger answer.'
        self.package['copy_layer']['research_sha256']=digest(self.package['research'])
        self.assertTrue(any('immutable Logic research' in e for e in validate_copy(self.package)))
        self.package['research']=copy.deepcopy(self.origin['research'])
        self.package['copy_layer']['research_sha256']=digest(self.package['research'])
        self.package['logic_layer']['slides'][0]['data'].append(dict(data_id='INVENTED',raw_value=999))
        self.assertTrue(any('cannot invent or alter research data' in e for e in validate_copy(self.package)))

    def test_required_finding_cannot_be_hidden_in_notes(self):
        page=self.package['copy_layer']['slides'][0]
        page['speaker_notes']=[dict(text='Only here',source_finding_ids=['B1'])]
        for u in page['copy_units']:u['source_finding_ids']=[]
        self.assertTrue(any('required research finding' in e for e in validate_copy(self.package)))

    def test_source_and_data_provenance_remain_required(self):
        self.origin['research']['findings'][0]['source_ids']=[]
        self.assertTrue(any('require sources' in e for e in validate_logic(self.origin)))

    def test_copy_requests_art_selects_and_explains_media(self):
        page=self.package['copy_layer']['slides'][0]
        page['presentation_requests']=[dict(request_id='R1',kind='table',purpose='Compare the approved figures.',copy_ids=[],data_ids=[]),
            dict(request_id='R2',kind='logo',purpose='Identify the subject, without implying endorsement.')]
        self.assertEqual([],validate_copy(self.package))
        self.bind()
        self.assertTrue(any('resolve every Copy' in e for e in validate_plan(self.package,self.plan)))
        self.plan['slides'][0]['presentation_request_resolutions']=[dict(request_id='R1',status='adapted',reason='A chart makes this comparison clearer.'),
            dict(request_id='R2',status='declined',reason='No eligible licensed logo is available; keep approved subject text.')]
        self.bind()
        self.assertEqual([],validate_plan(self.package,self.plan))

    def test_relabelling_legacy_logic_does_not_bypass_new_boundary(self):
        self.origin['contract_version']='3.1';self.bind()
        self.assertTrue(any('original package 3.2' in e for e in validate_copy(self.package)))

    def test_unknown_finding_and_wrong_pagination_owner_fail(self):
        self.package['copy_layer']['pagination_owner']='logic'
        self.package['copy_layer']['slides'][0]['copy_units'][0]['source_finding_ids']=['MISSING']
        errors=validate_copy(self.package)
        self.assertTrue(any('owns pagination' in e for e in errors))
        self.assertTrue(any('source_finding_ids' in e for e in errors))

    def test_art_can_add_visual_ordinal_without_copy_request(self):
        from packages.validators.story_handoff import validate_visual_baseline
        element=copy.deepcopy(self.plan['visual_baseline']['slides'][0]['elements'][0])
        element.update(element_id='ORDINAL-1',kind='ordinal',purpose='Navigation number, not a ranking.',copy_ids=[],text='1')
        self.plan['visual_baseline']['slides'][0]['elements'].append(element)
        self.bind()
        self.assertEqual([],validate_visual_baseline(self.package,self.plan))

    def test_portable_report_cannot_hide_changed_research(self):
        from packages.validators.story_handoff import build_stage_documents, validate_embedded_documents
        report={'stage_documents':build_stage_documents(self.package,self.plan)}
        self.assertEqual([],validate_embedded_documents(report))
        doc=report['stage_documents']['documents']['logic']
        doc['content']['research']['summary']='Rewritten after publication.'
        doc['content_sha256']=digest(doc['content'])
        doc['markdown']=render_document('logic',doc['content'])
        import hashlib
        doc['markdown_sha256']=hashlib.sha256(doc['markdown'].encode()).hexdigest()
        self.assertTrue(any('cross-stage' in e for e in validate_embedded_documents(report)))
