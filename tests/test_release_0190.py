"""Meaning, actual planning artifacts and portable planning-to-render audit."""
from __future__ import annotations

import base64
import copy
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'packages' / 'validators'))
sys.path.insert(0, str(ROOT))
from tests.test_release_0180 import clean_handoff, relock, write_native
from tests.test_story_visual_handoff import reference
from page_planning import (AUDIT_CHECKS, PLANNING_CONTRACT, planning_reference,
                           validate_content_relationships)
from story_handoff import (digest, build_stage_documents, embed_final_renders,
                           render_document, validate_design_audit,
                           validate_embedded_documents, handoff_archive_bytes)
from validate_logic_package import validate_package as validate_logic
from validate_ppt_package import validate_package as validate_copy
from validate_art_direction_plan import validate_plan
from compare_package_to_pptx import compare


def planning_handoff(folder):
    origin, package, plan = clean_handoff(folder)
    origin['contract_version'] = package['contract_version'] = '3.4'
    origin_path = folder / 'logic-34.json'
    origin_path.write_text(json.dumps(origin), encoding='utf-8')
    package['logic_artifact'] = reference(origin_path)
    package['copy_layer']['slides'][0]['content_relationships'] = {
        'heading_relationships': 'H and H2 are related judgments, without a source-backed process sequence.',
        'body_relations': [{'copy_id': 'B', 'heading_ids': ['H'],
                            'purpose': 'Explains the observed judgment; its uncertainty also qualifies the page.'}]}
    plan.update(contract_version='2.3', package_contract_version='3.4')
    for element in plan['visual_baseline']['slides'][0]['elements']:
        element.update(native_name='ART::'+element['element_id'], render_separately=True)
    record = {
        'contract': PLANNING_CONTRACT, 'package_id': package['package_id'],
        'package_version': package['version'], 'copy_package_sha256': digest(package),
        'recorded_at': '2026-10-04T00:00:00+00:00',
        'slides': [{'slide_id': 'S01',
                    'page_message': 'The pilot permits a bounded next step, with uncertainty visible.',
                    'content_analysis': 'H has explanatory body B; H2 remains a concise related judgment. A qualifies the page.',
                    'composition': 'Group H with B and keep the second judgment distinct; give the caveat a readable supporting position.',
                    'element_strategy': 'H and B share editable text; separate text for the second judgment preserves its distinct role.',
                    'addition_decision': 'No additional words are needed for this synthetic binding exercise.',
                    'expression_additions': []}]}
    record_path = folder / 'planning.json'
    record_path.write_text(json.dumps(record), encoding='utf-8')
    plan['page_planning'] = planning_reference(record_path)
    relock(package, plan)
    return origin, package, plan


class PagePlanningTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.origin, self.package, self.plan = planning_handoff(self.folder)

    @property
    def page(self):
        return self.package['copy_layer']['slides'][0]

    def test_complete_handoff_and_actual_native_shared_text(self):
        self.assertEqual([], validate_logic(self.origin))
        self.assertEqual([], validate_copy(self.package))
        self.assertEqual([], validate_plan(self.package, self.plan))
        path = self.folder / 'native.pptx'
        write_native(self.package, self.plan, path)
        self.assertEqual([], compare(self.package, self.plan, path))

    def test_missing_ownership_is_not_independence(self):
        self.page.pop('content_relationships')
        self.assertTrue(any('content_relationships' in e for e in validate_copy(self.package)))
        self.page['content_relationships'] = {'heading_relationships': 'Two judgments.', 'body_relations': []}
        self.assertTrue(any('every body' in e for e in validate_copy(self.package)))

    def test_shared_and_explicit_page_level_body_are_allowed(self):
        relation = self.page['content_relationships']['body_relations'][0]
        for headings in (['H', 'H2'], []):
            with self.subTest(headings=headings):
                relation['heading_ids'] = headings
                self.assertEqual([], validate_copy(self.package))

    def test_heading_can_own_direct_body_and_child_heading(self):
        units = {unit['copy_id']: unit for unit in self.page['copy_units']}
        units['H']['heading_level'] = 1
        units['H2']['heading_level'] = 2
        self.page['content_relationships']['heading_relationships'] = (
            'H2 is a child heading of H. B directly explains H alongside that child; '
            'H2 currently needs no body of its own.')
        self.page['content_relationships']['body_relations'][0].update(
            heading_ids=['H'], purpose='Direct explanation of parent H, alongside child heading H2.')
        self.assertEqual([], validate_copy(self.package))

    def test_unknown_cross_page_nonheading_and_duplicate_references_fail(self):
        relation = self.page['content_relationships']['body_relations'][0]
        for headings in (['UNKNOWN'], ['T'], ['H', 'H']):
            with self.subTest(headings=headings):
                relation['heading_ids'] = headings
                self.assertTrue(validate_copy(self.package))

    def test_ownership_needs_explicit_target_array_and_purpose(self):
        for field in ('heading_ids', 'purpose'):
            package = copy.deepcopy(self.package)
            package['copy_layer']['slides'][0]['content_relationships']['body_relations'][0].pop(field)
            self.assertTrue(validate_copy(package))

    def test_headings_can_have_no_body_and_body_can_have_no_heading(self):
        self.assertEqual([], validate_content_relationships(self.page))
        page = copy.deepcopy(self.page)
        page['copy_units'] = [u for u in page['copy_units'] if u['role'] == 'body']
        page['content_relationships']['heading_relationships'] = 'A continuous explanation without local headings.'
        page['content_relationships']['body_relations'][0]['heading_ids'] = []
        self.assertEqual([], validate_content_relationships(page))

    def test_old_contract_is_not_relabelled_or_given_new_requirements(self):
        _, package, plan = clean_handoff(self.folder)
        self.assertEqual([], validate_copy(package))
        self.assertEqual([], validate_plan(package, plan))

    def test_contract_pairs_cannot_silently_drop_planning(self):
        self.plan['contract_version'] = '2.2'
        relock(self.package, self.plan)
        self.assertTrue(any('requires Art plan 2.3' in e for e in validate_plan(self.package, self.plan)))

    def test_missing_stale_and_tampered_planning_fail(self):
        plan = copy.deepcopy(self.plan)
        plan.pop('page_planning')
        relock(self.package, plan)
        self.assertTrue(validate_plan(self.package, plan))
        plan = copy.deepcopy(self.plan)
        plan['page_planning']['content']['slides'][0]['composition'] = 'Post-hoc explanation.'
        relock(self.package, plan)
        self.assertTrue(any('snapshot' in e for e in validate_plan(self.package, plan)))
        self.page['content_relationships']['body_relations'][0]['heading_ids'] = []
        relock(self.package, self.plan)
        self.assertTrue(any('exact Copy' in e for e in validate_plan(self.package, self.plan)))

    def update_record(self, edit):
        record = copy.deepcopy(self.plan['page_planning']['content'])
        edit(record)
        path = self.folder / 'planning-revision.json'
        path.write_text(json.dumps(record), encoding='utf-8')
        self.plan['page_planning'] = planning_reference(path)
        relock(self.package, self.plan)

    def test_planning_after_design_lock_fails(self):
        self.update_record(lambda r: r.update(recorded_at='2026-10-05T00:00:00+00:00'))
        self.assertTrue(any('after the design lock' in e for e in validate_plan(self.package, self.plan)))

    def test_planning_must_precede_not_equal_the_lock(self):
        self.update_record(lambda r: r.update(recorded_at=self.plan['visual_baseline']['locked_at']))
        self.assertTrue(validate_plan(self.package, self.plan))

    def test_readable_work_report_keeps_planning_as_an_art_section(self):
        from work_report import _art_direction
        self.assertEqual(self.plan['page_planning'], _art_direction({'plan': self.plan})['plan_sections']['page_planning'])

    def test_missing_page_composition_is_detected(self):
        self.update_record(lambda r: r['slides'][0].pop('composition'))
        self.assertTrue(any('.composition' in e for e in validate_plan(self.package, self.plan)))

    def test_addition_requires_approved_basis_and_purpose(self):
        self.update_record(lambda r: r['slides'][0].update(expression_additions=[
            {'text': 'Next step', 'purpose': 'Compress the bounded recommendation.', 'source_copy_ids': ['UNKNOWN']}]))
        self.assertTrue(any('approved Copy IDs' in e for e in validate_plan(self.package, self.plan)))

    def report(self):
        path = self.folder / 'native.pptx'
        write_native(self.package, self.plan, path)
        sha = reference(path)['sha256']
        page = {'slide_id': 'S01', 'preview_sha256': self.plan['visual_baseline']['slides'][0]['image']['sha256'],
                'status': 'reviewed', 'final_render': reference(self.folder / 'design.png'),
                'rendered_from_pptx_sha256': sha}
        for key in ('content', 'visual_fidelity', 'native_editability', 'design_quality', *AUDIT_CHECKS):
            page[key] = {'status': 'pass', 'observation': 'Synthetic record/transport exercise; no real visual quality attestation.'}
        report = {'run_status': 'clean', 'issues': [], 'stage_documents': build_stage_documents(self.package, self.plan),
                  'design_comparison': {'visual_baseline_sha256': digest(self.plan['visual_baseline']),
                                        'pptx_sha256': sha, 'slides': [page]}}
        embed_final_renders(report)
        qa = {'visual_baseline_sha256': digest(self.plan['visual_baseline']),
              'output_started_at': '2026-10-04T02:00:00+00:00'}
        return report, qa, path

    def test_audit_requires_observed_planning_even_with_matching_output(self):
        report, qa, path = self.report()
        self.assertEqual([], validate_design_audit(self.package, self.plan, qa, report, path))
        for key in AUDIT_CHECKS:
            candidate = copy.deepcopy(report)
            candidate['design_comparison']['slides'][0].pop(key)
            self.assertTrue(any(key in e for e in validate_design_audit(self.package, self.plan, qa, candidate, path)))

    def test_ineffective_or_uncertain_planning_cannot_be_clean(self):
        report, qa, path = self.report()
        report['design_comparison']['slides'][0]['planned_realization'] = {
            'status': 'uncertain', 'observation': 'Actual attention was not observed.',
            'earliest_owner': 'art-direction', 'issue_ids': ['I-PLAN']}
        report['issues'] = [{'issue_id': 'I-PLAN'}]
        self.assertTrue(any('cannot be reported clean' in e for e in validate_design_audit(self.package, self.plan, qa, report, path)))
        report['run_status'] = 'issues-found'
        self.assertEqual([], validate_design_audit(self.package, self.plan, qa, report, path))

    def test_deferred_render_still_requires_planning_observation(self):
        report, qa, path = self.report()
        report.update(run_status='complete-with-deferred-acceptance')
        report['design_comparison']['slides'][0].update(status='deferred', reason='Renderer unavailable.')
        report['design_comparison']['slides'][0].pop('page_planning')
        self.assertTrue(any('page_planning' in e for e in validate_design_audit(self.package, self.plan, qa, report, path)))

    def test_deferred_render_cannot_pass_planned_realization(self):
        report, qa, path = self.report()
        report.update(run_status='complete-with-deferred-acceptance')
        page = report['design_comparison']['slides'][0]
        page.update(status='deferred', reason='Renderer unavailable.')
        self.assertTrue(any('cannot establish a pass' in e for e in validate_design_audit(self.package, self.plan, qa, report, path)))
        page['planned_realization'] = {'status': 'uncertain', 'observation': 'Final rendered realization was not observed.',
                                       'earliest_owner': 'output', 'issue_ids': ['I-RENDER']}
        report['issues'] = [{'issue_id': 'I-RENDER'}]
        self.assertEqual([], validate_design_audit(self.package, self.plan, qa, report, path))

    def test_portable_planning_survives_original_source_removal(self):
        report, _, _ = self.report()
        first = handoff_archive_bytes(report)
        Path(self.plan['page_planning']['path']).unlink()
        (self.folder / 'logic-34.json').unlink()
        (self.folder / 'design.png').unlink()
        self.assertEqual([], validate_embedded_documents(report))
        self.assertEqual(first, handoff_archive_bytes(report))
        with zipfile.ZipFile(io.BytesIO(first)) as archive:
            self.assertIn('art-page-planning.json', archive.namelist())
            self.assertIn('content_analysis', archive.read('art-page-planning.md').decode())
            self.assertEqual(self.plan['page_planning']['content'], json.loads(archive.read('art-page-planning.json')))
        self.assertIn('B → H: Explains the observed judgment', render_document('copy', self.package))
        self.assertIn('content_analysis', render_document('art-direction', self.plan))

    def test_cli_records_then_locks_and_refuses_overwrite(self):
        package_path = self.folder / 'copy.json'
        package_path.write_text(json.dumps(self.package), encoding='utf-8')
        draft_path = self.folder / 'planning-draft.json'
        draft_path.write_text(json.dumps({'slides': self.plan['page_planning']['content']['slides']}), encoding='utf-8')
        record_path = self.folder / 'actual-planning.json'
        config_path = self.folder / 'historical-config.json'
        config = json.loads((ROOT / 'config/default.json').read_text())
        config['workflow'].pop('reader_review', None)
        config_path.write_text(json.dumps(config))
        script = ROOT / 'scripts/stage_documents.py'
        command = [sys.executable, str(script), 'record-planning', '--package', str(package_path),
                   '--plan', str(draft_path), '--output', str(record_path), '--config', str(config_path)]
        self.assertEqual(0, subprocess.run(command, capture_output=True).returncode)
        before = record_path.read_bytes()
        self.assertNotEqual(0, subprocess.run(command, capture_output=True).returncode)
        self.assertEqual(before, record_path.read_bytes())
        plan = copy.deepcopy(self.plan)
        plan.pop('page_planning')
        plan['visual_baseline']['status'] = 'draft'
        plan_path = self.folder / 'art-draft.json'
        plan_path.write_text(json.dumps(plan), encoding='utf-8')
        output = self.folder / 'art-approved.json'
        result = subprocess.run([sys.executable, str(script), 'lock-design', '--package', str(package_path),
                                 '--plan', str(plan_path), '--planning', str(record_path), '--output', str(output), '--config', str(config_path)],
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], validate_plan(self.package, json.loads(output.read_text())))
        export = self.folder / 'readable-handoff'
        result = subprocess.run([sys.executable, str(script), 'export', '--package', str(package_path),
                                 '--plan', str(output), '--output', str(export)], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, (export / 'art-page-planning.json').read_bytes())
        self.assertIn('content_analysis', (export / 'art-page-planning.md').read_text())


if __name__ == '__main__':
    unittest.main()
