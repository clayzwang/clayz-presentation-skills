"""Opt-in actual PPTX/PDF/PNG IO exercise, not presentation-quality acceptance."""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(os.environ.get('PPT_STAGE_FILES_ROOT', str(Path(__file__).resolve().parents[1])))
sys.path[:0] = [str(ROOT), str(ROOT / 'packages/validators')]
from packages.validators import stage_files as sf


class NativeFileRoundTrip(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('PPT_STAGE_NATIVE_IO_DIR'), 'Opt-in actual LibreOffice/Poppler file exercise')
    def test_actual_files_through_the_five_stage_interfaces(self):
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from scripts.render_native_preview import render
        root = Path(os.environ['PPT_STAGE_NATIVE_IO_DIR'])
        root.mkdir(parents=True, exist_ok=False)
        def text(name, value):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('x') as stream:
                stream.write(value)
            return path
        def js(name, value):
            return text(name, json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        def process(name, action, record, artifacts):
            return js(name, {'events': [{'action': action, 'record': record,
                                         'artifacts': [sf.file_ref(p) for p in artifacts]}]})

        request = text('user-request.txt', 'Exercise actual file transport and text preservation. Do not claim research depth or design quality.')
        tool_snapshot = Path(os.environ['PPT_TOOL_SNAPSHOT_FILE'])
        knowledge_snapshot = Path(os.environ['PPT_KNOWLEDGE_SNAPSHOT_FILE'])
        tool_version = js('tool-version.json', {'scope': 'current local workflow code', 'snapshot': sf.file_ref(tool_snapshot)})
        knowledge_version = js('knowledge-version.json', {'scope': 'actual unchanged bound knowledge', 'snapshot': sf.file_ref(knowledge_snapshot)})
        logic_input = root / 'logic/input.json'
        sf.prepare_input('logic', js('logic/brief.json', {'topic': 'Explain this file transport exercise',
                         'audience': 'Workflow reviewer', 'research_requirements': ['Preserve report, observable process and evidence files.'],
                         'materials': [sf.file_ref(request)]}), [], logic_input)
        report = text('logic/research-report.md', '# File transport exercise\n\nThis report is deliberately a technical fixture. It is not company research or a demonstration of substantive research depth.\n\nThe exercise preserves a complete account before page editing, binds actual account spans, renders native files, and retains all stages for later analysis. Evidence is the local request and the actual generated files.\n')
        evidence = js('logic/evidence.json', {'sources': [{'source_id': 'request', 'title': 'Local exercise request',
                      'locator': str(request), 'artifacts': [sf.file_ref(request)]}]})
        research_process = process('logic/research-process.json', 'inspect-local-input',
                                   'Read the local IO exercise request and recorded its scope; no external business research occurred.', [request])
        data = js('logic/data.json', [])
        logic_handoff = root / 'logic/handoff.json'
        sf.record_research(logic_input, report, research_process, evidence, data, logic_handoff)

        copy_input = root / 'copy/input.json'
        sf.prepare_input('copy', js('copy/brief.json', {'purpose': 'Explain the interface exercise',
                         'audience': 'Workflow reviewer', 'pagination_requirements': ['One technical fixture page.'],
                         'wording_requirements': ['Retain the actual account wording.']}), [logic_handoff], copy_input)
        paragraphs = ['Workflow artifact integration check',
                      'The complete account exists before page editing.',
                      'Actual files are preserved for later workflow analysis.']
        account_text = '\n\n'.join(paragraphs)
        account = text('copy/complete-account.md', account_text)
        account_record = root / 'copy/account-record.json'
        sf.record_account(copy_input, account, account_record)
        units, spans, relations = [], {}, []
        for i, paragraph in enumerate(paragraphs):
            cid = f'C{i+1:02}'
            units.append({'copy_id': cid, 'text': paragraph, 'role': 'title' if i == 0 else 'body'})
            start = account_text.index(paragraph)
            spans[cid] = [{'start': start, 'end': start + len(paragraph), 'operation': 'verbatim'}]
            if i:
                relations.append({'copy_id': cid, 'heading_ids': [], 'purpose': 'Explain the actual sequence and retention purpose of this technical exercise.'})
        content = js('copy/content.json', {'account_record': sf.file_ref(account_record), 'slides': [
            {'slide_id': 'S01', 'copy_units': units, 'content_relationships': {
                'heading_relationships': 'There are no local headings; the body directly explains the title.', 'body_relations': relations}}],
            'unit_sources': spans, 'semantic_review': 'The visible text is verbatim from the registered account. This is an IO fixture, not a quality evaluation.'})
        copy_process = process('copy/edit-process.json', 'edit-after-account-registration',
                               'Retained the account wording on one fixture page; created no local headings.', [account_record, content])
        copy_handoff = root / 'copy/handoff.json'
        sf.record_copy(account_record, content, copy_process, copy_handoff)

        font = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
        art_input = root / 'art/input.json'
        sf.prepare_input('art-direction', js('art/brief.json', {'purpose': 'Exercise actual native file rendering',
                         'format_requirements': ['Simple technical fixture, not a design benchmark.'],
                         'fonts': [{'family': 'Noto Sans CJK SC', 'file': sf.file_ref(font)}]}), [copy_handoff], art_input)
        presentation = Presentation()
        presentation.slide_width, presentation.slide_height = Inches(13.333), Inches(7.5)
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        objects = []
        for i, unit in enumerate(units):
            shape = slide.shapes.add_textbox(Inches(.8), Inches(1 + i * 1.4), Inches(11.6), Inches(1))
            shape.name = unit['copy_id']
            run = shape.text_frame.paragraphs[0].add_run()
            run.text, run.font.name, run.font.size = unit['text'], 'Noto Sans CJK SC', Pt(28 if i == 0 else 22)
            objects.append({'copy_id': unit['copy_id'], 'native_name': shape.name, 'purpose': 'Actual editable text in the IO fixture.'})
        pptx = root / 'output/fixture.pptx'
        pptx.parent.mkdir(parents=True)
        presentation.save(pptx)
        renders_dir = root / 'actual-renders'
        manifest = render(pptx, renders_dir, ['S01'], font_file=font, font_family='Noto Sans CJK SC')
        render_manifest = renders_dir / 'manifest.json'
        design = js('art/design.json', {'slides': [{'slide_id': 'S01', 'objects': objects}],
                    'scope': 'IO fixture only; full native Art approval and design review not performed.'})
        art_process = process('art/design-process.json', 'build-and-render-native-fixture',
                              'Created actual editable text and rendered it with the explicitly selected available font.', [design, pptx, render_manifest])
        art_handoff = root / 'art/handoff.json'
        sf.record_art(art_input, design, render_manifest, art_process, art_handoff)

        output_input = root / 'output/input.json'
        sf.prepare_input('output', js('output/brief.json', {'delivery_requirements': ['Preserve the actual PPTX, PDF and page image.'],
                         'editable_requirements': ['Retain native editable text.'], 'target_applications': ['LibreOffice observed; PowerPoint/WPS not observed.']}),
                         [art_handoff], output_input)
        pdf = Path(manifest['pdf']['path'])
        reopened = Presentation(pptx)
        xml_text = [shape.text for shape in reopened.slides[0].shapes if shape.has_text_frame]
        self.assertEqual(paragraphs, xml_text)
        pdf_text = subprocess.run(['pdftotext', str(pdf), '-'], check=True, text=True, capture_output=True).stdout
        for paragraph in paragraphs:
            self.assertIn(' '.join(paragraph.split()), ' '.join(pdf_text.split()))
        qa = js('output/io-check.json', {'scope': 'actual IO and exact text only', 'xml_text_match': True,
                'pdf_text_match': True, 'native_full_qa': 'not-run', 'design_quality': 'not-evaluated',
                'PowerPoint_WPS': 'not-observed'})
        output_process = process('output/process.json', 'reopen-and-compare',
                                 'Reopened actual PPTX XML and extracted actual PDF text; both preserve all supplied text.', [pptx, pdf, qa])
        output_handoff = root / 'output/handoff.json'
        sf.record_output(output_input, pptx, pdf, render_manifest, qa, output_process, output_handoff)

        supervisor_input = root / 'supervisor/input.json'
        sf.prepare_input('supervisor', js('supervisor/brief.json', {'user_request': sf.file_ref(request),
                         'tool_version': sf.file_ref(tool_version), 'knowledge_version': sf.file_ref(knowledge_version)}),
                         [logic_handoff, copy_handoff, art_handoff, output_handoff], supervisor_input)
        supervisor_report = text('supervisor/report.md', '# Actual file IO result\n\nFive stage interfaces recorded real files. PPTX/XML and PDF text were reopened and matched. All renders are real LibreOffice/Poppler outputs.\n\nThis does not assess research depth, editorial or design quality, the full native QA protocol, or cross-task workflow quality. No training occurred.\n')
        exceptions = js('supervisor/exceptions.json', ['Research/editorial/design quality not evaluated by this IO exercise.',
                         'Full native Output QA and independent readers/Auditor were not run in this technical fixture.',
                         'PowerPoint/WPS not observed.'])
        supervisor_handoff = root / 'supervisor/handoff.json'
        sf.record_supervisor(supervisor_input, supervisor_report, exceptions, supervisor_handoff)
        retained = root / 'retained-materials'
        sf.collect_materials([logic_handoff, copy_handoff, art_handoff, output_handoff, supervisor_handoff], request,
                             tool_version, knowledge_version, tool_snapshot, knowledge_snapshot, retained)
        sf.check_collection(retained / 'training-materials.json')
        js('result.json', {'status': 'actual-file-io-tested', 'stage_handoffs': 5, 'pages': 1,
                           'copy_local_headings': 0, 'xml_text_match': True, 'pdf_text_match': True,
                           'collection': sf.file_ref(retained / 'training-materials.json'),
                           'not_established': ['Research quality', 'Editorial quality', 'Design quality', 'Generalized workflow quality', 'Full native QA']})
        print('ACTUAL_IO_ARTIFACTS', root)


if __name__ == '__main__':
    unittest.main()
