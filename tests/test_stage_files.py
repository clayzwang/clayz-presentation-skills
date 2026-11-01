"""Protocol regressions. Fixtures are not evidence of presentation quality."""
import base64
import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(os.environ.get('PPT_STAGE_FILES_ROOT', str(Path(__file__).resolve().parents[1])))
sys.path[:0] = [str(ROOT), str(ROOT / 'packages/validators')]
from packages.validators import stage_files as sf
from packages.validators.validate_logic_package import validate_package
from packages.validators.story_handoff import render_document


class StageFilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ppt-stage-files-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.counter = 0

    def path(self, name):
        self.counter += 1
        return self.root / f'{self.counter}-{name}'

    def text(self, name, text):
        p = self.path(name)
        p.write_text(text)
        return p

    def json(self, name, value):
        return self.text(name, json.dumps(value, ensure_ascii=False, indent=2))

    def process(self, name='process.json'):
        return self.json(name, {'events': [{'action': 'inspect', 'record': 'Protocol fixture: inspected the supplied test file.'}]})

    def logic(self):
        source = self.text('source.txt', 'A local protocol fixture, not real company research.')
        brief = self.json('brief.json', {'topic': 'Inspect a file handoff', 'audience': 'Protocol reviewer',
                                        'research_requirements': ['Retain full prose and observable evidence.'],
                                        'materials': [sf.file_ref(source)]})
        input_path = self.path('logic-input.json')
        sf.prepare_input('logic', brief, [], input_path)
        report = self.text('report.md', '# Test report\n\nFull report bytes are retained unchanged.\n\nThis is a protocol fixture, not a claim of research depth.\n')
        process = self.json('research-process.json', {'events': [{'action': 'read', 'record': 'Read the local fixture.',
                   'source_ids': ['source'], 'artifacts': [sf.file_ref(source)]}]})
        evidence = self.json('evidence.json', {'sources': [{'source_id': 'source', 'title': 'Local fixture',
                   'locator': str(source), 'artifacts': [sf.file_ref(source)]}]})
        data = self.json('data.json', [])
        handoff = self.path('logic-handoff.json')
        sf.record_research(input_path, report, process, evidence, data, handoff)
        return handoff

    def account(self):
        logic = self.logic()
        brief = self.json('copy-brief.json', {'purpose': 'Explain the fixture', 'audience': 'Protocol reviewer',
                                            'pagination_requirements': [], 'wording_requirements': []})
        input_path = self.path('copy-input.json')
        sf.prepare_input('copy', brief, [logic], input_path)
        prose = '\n\n'.join(f'Passage {i} explains its test relationship in a complete sentence.' for i in range(6))
        account = self.text('account.md', prose)
        record = self.path('account-record.json')
        sf.record_account(input_path, account, record)
        return input_path, account, record

    def content(self, record_path, heading_count=0):
        record = sf.read_json(record_path)
        text = sf.read_ref(record['account']).decode()
        units, sources, relations = [], {}, []
        for i in range(max(1, heading_count)):
            paragraph = text.split('\n\n')[i]
            start = text.index(paragraph)
            end = start + len(paragraph)
            heading = None
            if heading_count:
                heading = f'H{i}'
                units.append({'copy_id': heading, 'text': f'Relationship {i}', 'role': 'heading', 'heading_level': 2})
                sources[heading] = [{'start': start, 'end': end, 'operation': 'derived',
                                     'reason': 'The fixture heading names this actual paragraph.'}]
            body = f'B{i}'
            units.append({'copy_id': body, 'text': paragraph, 'role': 'body'})
            sources[body] = [{'start': start, 'end': end, 'operation': 'verbatim'}]
            relations.append({'copy_id': body, 'heading_ids': [heading] if heading else [],
                              'purpose': 'Retain this complete source paragraph for the protocol test.'})
        return {'account_record': sf.file_ref(record_path), 'slides': [{'slide_id': 'S01', 'copy_units': units,
            'content_relationships': {'heading_relationships': 'Fixture paragraphs retain their explicit ownership; no layout is prescribed.',
                                     'body_relations': relations}}], 'unit_sources': sources,
            'semantic_review': 'Protocol-only fixture. No presentation quality verdict is asserted.'}

    def copy_handoff(self, heading_count=0):
        input_path, account, record = self.account()
        content = self.json('content.json', self.content(record, heading_count))
        handoff = self.path('copy-handoff.json')
        sf.record_copy(record, content, self.process(), handoff)
        return handoff

    def test_logic_input_rejects_visual_and_runtime_snapshots(self):
        for field in ['theme', 'layout', 'performance_budget', 'task_selection', 'acceptance_contract', 'index_evidence']:
            with self.subTest(field=field):
                brief = self.json('brief.json', {'topic': 'Test', field: {}})
                with self.assertRaises(ValueError):
                    sf.prepare_input('logic', brief, [], self.path('input.json'))

    def test_nested_runtime_config_is_not_a_research_requirement(self):
        brief = self.json('brief.json', {'topic': 'Test', 'research_requirements': {'theme': {'font': 'x'}}})
        with self.assertRaises(ValueError):
            sf.prepare_input('logic', brief, [], self.path('input.json'))

    def test_logic_reference_lookup_does_not_read_industry_cases(self):
        from packages.validators.logic_knowledge import lookup
        knowledge = self.root / 'knowledge'
        knowledge.mkdir()
        nodes = knowledge / 'nodes.json'
        nodes.write_text(json.dumps({'nodes': [{'code': 'BASE', 'principle': 'A foundational inquiry method.',
                                                'positive_example': {'example': 'A case that is not a default method.'},
                                                'example_conclusion': 'A historical case conclusion.'}]}))
        (knowledge / 'manifest.json').write_text(json.dumps({'version': 'fixture', 'files': {'nodes.json': sf.file_ref(nodes)['sha256']}}))
        (knowledge / 'industry-research-cases.json').write_text('This deliberately is not readable JSON and must not be loaded.')
        selected = {'selections': [{'code': 'BASE', 'reason': 'Inspect the base method.', 'decision': 'Use source checking.'}]}
        method = lookup(knowledge, selected)['selected'][0]['record']
        self.assertEqual({'code': 'BASE', 'principle': 'A foundational inquiry method.'}, method)
        with self.assertRaisesRegex(ValueError, 'Case-method retrieval'):
            lookup(knowledge, {**selected, 'case_ids': ['historical-case']})

    def test_research_requires_full_report_and_process_files(self):
        with self.assertRaises(ValueError):
            sf.validate_research_documents({'findings': [{'finding_id': 'F01', 'text': 'A conclusion.'}]})
        handoff = sf.read_json(self.logic())
        del handoff['artifacts']['process']
        with self.assertRaises(ValueError):
            sf.check_handoff(handoff)

    def test_process_declarations_without_saved_evidence_are_rejected(self):
        process = self.process()
        with self.assertRaisesRegex(ValueError, 'actual saved'):
            sf.validate_process(sf.file_ref(process), require_evidence=True)

    def test_research_document_is_not_regenerated_from_findings(self):
        handoff = sf.read_json(self.logic())
        expected = sf.read_ref(handoff['artifacts']['report']).decode()
        document = render_document('logic', {'contract_version': '3.5', 'research': {'documents': handoff['artifacts']},
                                           'task_selection': {'theme': 'MUST_NOT_APPEAR'},
                                           'acceptance_contract': {'performance_budget': 'MUST_NOT_APPEAR'}})
        self.assertIn(expected, document)
        self.assertIn('Research process', document)
        self.assertNotIn('MUST_NOT_APPEAR', document)
        self.assertNotIn('Complete handoff data', document)

    def test_changed_research_report_is_rejected(self):
        handoff = sf.read_json(self.logic())
        Path(handoff['artifacts']['report']['path']).write_text('Changed after registration')
        with self.assertRaisesRegex(ValueError, 'Changed file'):
            sf.check_handoff(handoff)

    def test_copy_requires_the_preexisting_account_record(self):
        _, _, record = self.account()
        content = self.content(record)
        del content['account_record']
        with self.assertRaises(ValueError):
            sf.validate_copy_document(content, sf.read_json(record))

    def test_changed_account_is_rejected(self):
        _, account, record = self.account()
        content = self.content(record)
        account.write_text('Replaced after account registration')
        with self.assertRaisesRegex(ValueError, 'Changed file'):
            sf.validate_copy_document(content, sf.read_json(record))

    def test_actual_account_ranges_are_checked(self):
        _, _, record = self.account()
        content = self.content(record)
        content['slides'][0]['copy_units'][0]['text'] = 'Different purported verbatim text'
        with self.assertRaisesRegex(ValueError, 'verbatim'):
            sf.validate_copy_document(content, sf.read_json(record))

    def test_heading_counts_are_not_fixed(self):
        for count in [0, 1, 2, 3, 4, 5]:
            with self.subTest(count=count):
                handoff = sf.read_json(self.copy_handoff(count))
                content = sf.json_ref(handoff['artifacts']['content'])
                headings = [u for u in content['slides'][0]['copy_units'] if u['role'] == 'heading']
                self.assertEqual(count, len(headings))
                self.assertTrue(all(h['heading_level'] == 2 for h in headings))

    def test_heading_level_is_never_silently_one(self):
        _, _, record = self.account()
        content = self.content(record, 1)
        del content['slides'][0]['copy_units'][0]['heading_level']
        with self.assertRaisesRegex(ValueError, 'no default level'):
            sf.validate_copy_document(content, sf.read_json(record))

    def test_metadata_cannot_be_added_to_professional_handoff(self):
        handoff = sf.read_json(self.logic())
        handoff['resource_inventory'] = {'full_snapshot': True}
        with self.assertRaisesRegex(ValueError, 'runtime/configuration'):
            sf.check_handoff(handoff)

    def test_new_default_entry_does_not_accept_old_summary_package(self):
        errors = validate_package({'contract_version': '3.4', 'research': {'findings': [{'text': 'Summary'}]}})
        self.assertIn('requires package 3.5', errors[0])

    def test_missing_image_cannot_be_declared_rendered(self):
        manifest = self.json('renders.json', {'slides': [{'slide_id': 'S01', 'path': str(self.root/'missing.png'),
                                                          'sha256': '0'*64, 'bytes': 1}]})
        with self.assertRaises(OSError):
            sf.validate_renders(sf.file_ref(manifest), ['S01'])

    def test_output_placeholders_are_rejected(self):
        pptx = self.text('file.pptx', 'not a presentation')
        pdf = self.text('file.pdf', 'not a PDF')
        with self.assertRaises(ValueError):
            sf.validate_output_files(sf.file_ref(pptx), sf.file_ref(pdf), 1)

    def test_registration_never_overwrites_prior_artifacts(self):
        p = self.path('record.json')
        sf.write_new(p, {'revision': 1})
        with self.assertRaises(FileExistsError):
            sf.write_new(p, {'revision': 2})

    def test_five_stages_collect_real_files_and_keep_failed_qa(self):
        copy_path = self.copy_handoff(0)
        copy_value = sf.read_json(copy_path)
        copy_input = sf.json_ref(copy_value['input'])
        logic_path = Path(copy_input['inputs'][0]['path'])
        art_input = self.path('art-input.json')
        sf.prepare_input('art-direction', self.json('art-brief.json', {'purpose': 'Inspect protocol files',
                         'format_requirements': ['Fixture only; no quality verdict.']}), [copy_path], art_input)
        png = self.path('fixture.png')
        png.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jB7sAAAAASUVORK5CYII='))
        renders = self.json('renders.json', {'slides': [{'slide_id': 'S01', **sf.file_ref(png)}]})
        design = self.json('design.json', {'slides': [{'slide_id': 'S01', 'intent': 'Protocol fixture only.'}]})
        art_path = self.path('art-handoff.json')
        sf.record_art(art_input, design, renders, self.process(), art_path)
        output_input = self.path('output-input.json')
        sf.prepare_input('output', self.json('output-brief.json', {'delivery_requirements': ['Retain fixture files.']}),
                         [art_path], output_input)
        from pptx import Presentation
        pres = Presentation()
        pres.slides.add_slide(pres.slide_layouts[6])
        pptx = self.path('fixture.pptx')
        pres.save(pptx)
        # A minimal PDF container is sufficient for this file-protocol test.
        # Actual rendering/native QA is a separate integration check.
        pdf = self.path('fixture.pdf')
        pdf.write_bytes(b'%PDF-1.4\n% Protocol fixture only\n%%EOF\n')
        qa = self.json('qa.json', {'status': 'not-run', 'reason': 'File protocol unit fixture; not native QA.'})
        output_path = self.path('output-handoff.json')
        sf.record_output(output_input, pptx, pdf, renders, qa, self.process(), output_path)
        self.assertEqual('not-run', sf.json_ref(sf.read_json(output_path)['artifacts']['qa'])['status'])
        user_request = self.text('request.txt', 'Test file transport, not presentation quality.')
        tool_version = self.json('tool-version.json', {'version': 'test-only'})
        knowledge_version = self.json('knowledge-version.json', {'version': 'test-only'})
        tool_snapshot = self.text('tool-snapshot.txt', 'Test snapshot bytes')
        knowledge_snapshot = self.text('knowledge-snapshot.txt', 'Test snapshot bytes')
        supervisor_input = self.path('supervisor-input.json')
        sf.prepare_input('supervisor', self.json('supervisor-brief.json', {'user_request': sf.file_ref(user_request)}),
                         [logic_path, copy_path, art_path, output_path], supervisor_input)
        supervisor_path = self.path('supervisor-handoff.json')
        sf.record_supervisor(supervisor_input, self.text('report.md', 'Protocol test; quality not evaluated.'),
                             self.json('exceptions.json', ['Native QA not run.']), supervisor_path)
        destination = self.root / 'retained'
        reader = self.json('reader-observation.json', {'status': 'fail', 'observation': 'Protocol fixture; retain this actual failed observation.'})
        supporting = self.json('supporting-records.json', {'reader': sf.file_ref(reader), 'native_qa': sf.file_ref(qa)})
        sf.collect_materials([logic_path, copy_path, art_path, output_path, supervisor_path], user_request,
                             tool_version, knowledge_version, tool_snapshot, knowledge_snapshot, destination,
                             supporting_artifacts=[supporting])
        manifest = destination / 'training-materials.json'
        value = sf.check_collection(manifest)
        self.assertEqual(5, len(value['handoffs']))
        self.assertEqual(sf.file_ref(tool_snapshot), value['inputs']['tool_snapshot'])
        original_report = sf.read_json(logic_path)['artifacts']['report']
        original_bytes = sf.read_ref(original_report)
        Path(original_report['path']).unlink()
        self.assertEqual(original_bytes, sf.read_collected_file(manifest, original_report))
        self.assertEqual('fail', json.loads(sf.read_collected_file(manifest, sf.file_ref(reader)))['status'])
        # Detect a lost nested file even after originals have gone.
        value['files'] = [e for e in value['files'] if e['original']['path'] != str(reader)]
        manifest.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'nested referenced file is missing'):
            sf.check_collection(manifest)

    def test_art_does_not_need_to_keep_copy_page_count(self):
        copy_path = self.copy_handoff(0)
        copy_value = sf.read_json(copy_path)
        content = sf.json_ref(copy_value['artifacts']['content'])
        changed = copy.deepcopy(content['slides'])
        changed[0]['slide_id'] = 'ART-S01'
        second = copy.deepcopy(changed[0])
        second['slide_id'] = 'ART-S02'
        second['copy_units'][0]['copy_id'] = 'ART-B1'
        second['content_relationships']['body_relations'][0]['copy_id'] = 'ART-B1'
        changed.append(second)
        from packages.validators.art_content import differences
        changes = differences({'copy_layer': {'slides': content['slides']}}, changed)
        for c in changes:
            c.update(reason='Protocol projection fixture.', evidence='Original content file retained.', impact='No quality verdict.')
        design = self.json('design.json', {'slides': [{'slide_id': 'ART-S01'}, {'slide_id': 'ART-S02'}],
                          'art_content': {'slides': changed, 'changes': changes}})
        png = self.path('fixture.png')
        png.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jB7sAAAAASUVORK5CYII='))
        renders = self.json('renders.json', {'slides': [{'slide_id': s, **sf.file_ref(png)} for s in ['ART-S01', 'ART-S02']]})
        art_input = self.path('art-input.json')
        sf.prepare_input('art-direction', self.json('brief.json', {'purpose': 'Test documented projection.'}), [copy_path], art_input)
        art = self.path('art.json')
        sf.record_art(art_input, design, renders, self.process(), art)
        self.assertEqual('art-direction', sf.check_handoff(sf.read_json(art))['stage'])

    def test_native_runtime_binding_without_professional_metadata_leak(self):
        fixture = os.environ.get('PPT_RUNTIME_BINDING_FIXTURE')
        copy_fixture = os.environ.get('PPT_COPY_RUNTIME_BINDING_FIXTURE')
        if not fixture or not copy_fixture:
            self.skipTest('Provide an original frozen runtime envelope for a binding-format regression test.')
        # Only machine-envelope shape is reused. These records are test fixtures,
        # never an actual new task approval, stage work record or quality pass.
        old = sf.read_json(fixture)
        context = {k: copy.deepcopy(v) for k, v in old.items()
                   if k not in {'research', 'logic_layer', 'copy_layer', 'professional_handoff', 'logic_artifact', 'copy_provenance'}}
        context['approvals'] = {'logic': {'status': 'approved', 'approved_by': 'PROTOCOL TEST FIXTURE ONLY'}, 'copy': None}
        context['source_resource_bindings'] = {'source': context['resource_inventory']['selected_resource_ids'][0]}
        logic_path = self.logic()
        runtime_logic = self.path('supervisor-logic-runtime.json')
        sf.bind_logic(logic_path, self.json('supervisor-context.json', context), runtime_logic)
        self.assertEqual([], validate_package(sf.read_json(runtime_logic), 'logic-approved'))
        input_path = self.path('copy-input.json')
        sf.prepare_input('copy', self.json('brief.json', {'purpose': 'Protocol binding test.'}), [logic_path], input_path)
        account = self.text('account.md', '\n\n'.join(f'Passage {i} explains its test relationship in a complete sentence.' for i in range(6)))
        account_record = self.path('account.json')
        sf.record_account(input_path, account, account_record)
        content_path = self.json('content.json', self.content(account_record, 2))
        copy_path = self.path('copy.json')
        sf.record_copy(account_record, content_path, self.process(), copy_path)
        # Existing cover requirements remain enforced by native Copy validation.
        # This fixture has one body page and explicitly opts out in the fixture's
        # actual acceptance record, recomputing its native digest.
        bound_logic = sf.read_json(runtime_logic)
        bound_logic['acceptance_contract']['cover_policy']['cover_required'] = False
        bound_logic['acceptance_contract']['cover_policy']['closing_required'] = False
        from packages.validators.acceptance_contract import acceptance_contract_digest
        bound_logic['acceptance_contract']['contract_sha256'] = acceptance_contract_digest(bound_logic['acceptance_contract'])
        runtime_logic2 = self.json('runtime-fixture-no-covers.json', bound_logic)
        runtime_copy = self.path('supervisor-copy-runtime.json')
        sf.bind_copy(copy_path, runtime_logic2,
                     self.json('approval.json', {'approval': {'status': 'approved', 'approved_by': 'PROTOCOL TEST FIXTURE ONLY'},
                                                'index_evidence': sf.read_json(copy_fixture)['index_evidence']}), runtime_copy)
        from packages.validators.validate_ppt_package import validate_package as validate_copy
        self.assertEqual([], validate_copy(sf.read_json(runtime_copy), 'copy-approved'))
        self.assertNotIn('task_selection', sf.read_json(logic_path))
        self.assertNotIn('acceptance_contract', sf.read_json(copy_path))


if __name__ == '__main__':
    unittest.main()
