"""Synthetic fixtures exercise workflow transport, never pretend to be real readers."""
import copy
import json
from pathlib import Path
from unittest import TestCase
from tests import test_reader_review as fixtures
from packages.validators import reader_review as rr
from packages.validators.handoff_io import write_record
from packages.validators.independent_audit import _evidence_tokens, _validate_evidence_refs


class HandoffTests(TestCase):
    setUp = fixtures.ReaderReviewTests.setUp
    put = fixtures.ReaderReviewTests.put
    packet = fixtures.ReaderReviewTests.packet
    context = fixtures.ReaderReviewTests.context
    response = fixtures.ReaderReviewTests.response
    review = fixtures.ReaderReviewTests.review
    audit = fixtures.ReaderReviewTests.audit

    def new_review(self, phase, *, title=None, gaps=False, name=None):
        name = name or 'new-' + phase
        package = rr.read(self.package)
        package['status'] = 'copy-approved'
        # Do not mutate an artifact already bound into a previous review.
        if rr.read(self.package) != package:
            self.put('copy.json', package)
        logic = {k: v for k, v in package.items() if k != 'copy_layer'}
        logic['status'] = 'logic-approved'
        baseline = self.package if phase == 'final' else self.put(name + '-logic.json', logic)
        packet = self.root / (name + '-packet.json')
        rr.prepare_packet(phase=phase, package=self.package, brief=self.brief,
                          directory=self.root / (name + '-input'), output=packet,
                          title_review=title, pptx=self.pptx if phase == 'final' else None,
                          renders=self.renders if phase == 'final' else None)
        first = self.root / (name + '-first.json')
        rr.record_first(packet=packet, context=self.context(packet, name),
                        response=self.put(name + '-response.json', self.response(gaps)), output=first)
        keys = ['research_conclusions'] if phase == 'title' else ['accuracy', 'completeness', 'reasoning']
        comparison = self.put(name + '-comparison.json', {
            'baseline': rr.ref(baseline), 'checks': {k: 'Synthetic observation of the bound comparison.' for k in keys},
            'verdict': 'return-copy' if gaps else 'pass', 'explanation': 'Synthetic transport fixture, not real language judgment.'})
        dispositions = [{'finding_id': 'TITLE-ANSWER', 'owner_layer': 'copy', 'status': 'open',
                         'explanation': 'Fix title meaning.', 'evidence_refs': [rr.ref(baseline)]}] if gaps else []
        review = self.root / (name + '-review.json')
        rr.record_review(first_read=first, dispositions=self.put(name + '-dispositions.json', dispositions),
                         evidence=[baseline], comparison=comparison, output=review)
        return review

    def test_title_is_only_titles_and_content_requires_pass_first(self):
        title = self.new_review('title')
        result = rr.validate_review(rr.read(title))
        self.assertEqual(['T'], [u['copy_id'] for u in result['visible_input']['pages'][0]['text']])
        self.assertNotIn('payment deadline', json.dumps(result['visible_input']))
        with self.assertRaisesRegex(ValueError, 'title-review'):
            rr.prepare_packet(phase='content', package=self.package, brief=self.brief,
                              directory=self.root/'bad-content', output=self.root/'bad-packet')
        self.assertFalse((self.root/'bad-content').exists())
        content = self.new_review('content', title=title)
        self.assertTrue(rr.check_art_gate(rr.read(self.package), title, content)['ready'])
        failed = self.new_review('title', gaps=True, name='failed-title')
        with self.assertRaisesRegex(ValueError, 'owner=copy'):
            self.new_review('content', title=failed, name='blocked-content')

    def test_semantic_reuse_and_minimal_restart(self):
        title = self.new_review('title')
        content = self.new_review('content', title=title)
        before = rr.read(self.package)
        after = copy.deepcopy(before)
        after['version'] = 'record-only-change'
        rr.check_art_gate(after, title, content)
        self.assertFalse(rr.repair_scope(before, after)['render'])
        after['copy_layer']['slides'][0]['copy_units'][1]['text'] += ' New substantive detail.'
        rr.validate_review(rr.read(title), current_package=after)
        with self.assertRaisesRegex(ValueError, 'stale'):
            rr.validate_review(rr.read(content), current_package=after)
        self.assertEqual('content', rr.repair_scope(before, after)['resume'][0])
        after['copy_layer']['slides'][0]['copy_units'][0]['text'] += ' New conclusion.'
        self.assertEqual('title', rr.repair_scope(before, after)['resume'][0])
        after['research']['private'] = 'Changed authoritative conclusion'
        with self.assertRaisesRegex(ValueError, 'stale'):
            rr.validate_review(rr.read(title), current_package=after)
        self.assertEqual('logic', rr.repair_scope(before, after)['owner'])
        self.assertFalse(rr.repair_scope(before, after, artifact='receipt')['render'])

    def test_three_phase_audit_requires_current_final_copy_comparison(self):
        title = self.new_review('title')
        content = self.new_review('content', title=title)
        final = self.new_review('final')
        audit = self.audit({'title': title, 'content': content, 'final': final})
        config = self.put('config.json', {'workflow': {'reader_review': {'phases': ['title', 'content', 'final']}}})
        audit['source_records'].append({'kind':'config', **rr.ref(config)})
        self.assertEqual({'title', 'content', 'final'}, set(rr.audit_reviews(audit, required=True)))
        audit['final_pptx']['sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'PPTX'):
            rr.audit_reviews(audit, required=True)

    def test_retry_preserves_evidence_and_timestamp(self):
        title = self.new_review('title')
        old = title.read_bytes()
        value = rr.read(title)
        value['reconciled_at'] = rr.now()
        write_record(title, value)
        self.assertEqual(old, title.read_bytes())
        self.assertEqual(rr.read(title)['reconciled_at'], value['reconciled_at'])
        value['comparison']['explanation'] += ' Different judgment.'
        with self.assertRaises(FileExistsError):
            write_record(title, value)
        self.assertEqual(old, title.read_bytes())
        self.package.write_text('{}')
        with self.assertRaises(ValueError):
            rr.validate_review(rr.read(title))

    def test_invalid_render_preflight_does_not_leave_packet_directory(self):
        broken = self.put('broken-renders.json', {'pptx_sha256': 'f'*64, 'slides': []})
        with self.assertRaises(ValueError):
            rr.prepare_packet(phase='final', package=self.package, brief=self.brief, directory=self.root/'broken-input',
                              output=self.root/'broken-packet', pptx=self.pptx, renders=broken)
        self.assertFalse((self.root/'broken-input').exists())

    def test_evidence_paths_spaces_and_ambiguous_basenames(self):
        a = self.put('a/shared name.json', {'a':1})
        b = self.put('b/shared name.json', {'b':2})
        tokens = _evidence_tokens({'source_records':[{'kind':'a', **rr.ref(a)}, {'kind':'b', **rr.ref(b)}]})
        for key in ['a', str(a), str(b)]:
            errors = []
            digest = rr.ref(b if key == str(b) else a)['sha256']
            _validate_evidence_refs([f'{key} sha256={digest}'], 'evidence', tokens, errors)
            self.assertEqual([], errors)
        errors = []
        _validate_evidence_refs([f'shared name.json sha256={rr.ref(b)["sha256"]}'], 'evidence', tokens, errors)
        self.assertTrue(errors)

    def test_subsecond_stage_timestamp_is_not_truncated(self):
        from packages.validators.stage_work_records import _now
        self.assertIn('.', _now())
        review = self.review()
        audit = self.audit({'copy':review})
        time = rr.read(review)['reconciled_at']
        rr.validate_copy_review_order(audit, {'recorded_at':time})
        rr.validate_copy_review_order(audit, {'recorded_at':time.split('.')[0]+'Z'})

    def test_current_art_cli_fails_before_creating_output_without_reviews(self):
        import subprocess
        import sys
        script = Path(__file__).resolve().parents[1] / 'scripts/stage_documents.py'
        package = rr.read(self.package)
        package['contract_version'] = '3.4'
        path = self.put('current-copy.json', package)
        output = self.root / 'must-not-create.json'
        result = subprocess.run([sys.executable, str(script), 'record-planning', '--package', str(path),
                                 '--plan', str(self.put('draft.json', {})), '--output', str(output)], capture_output=True, text=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn('title-review', result.stderr)
        self.assertFalse(output.exists())

    def test_record_cli_missing_role_fails_without_writing(self):
        import subprocess
        import sys
        script = Path(__file__).resolve().parents[1] / 'scripts/publish_supervised_pair.py'
        output = self.root / 'must-not-record.json'
        draft = self.put('stage-draft.json', {'summary':'Synthetic conclusion', 'checks':[], 'decisions':[], 'open_issues':[]})
        challenge = self.put('challenge.json', {'run_binding':rr.read(self.package)['run_binding']})
        result = subprocess.run([sys.executable, str(script), 'record-stage', '--stage', 'logic', '--draft', str(draft),
                                 '--challenge', str(challenge), '--artifact', 'wrong-role='+str(self.package),
                                 '--output', str(output)], capture_output=True, text=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn('artifacts.package', result.stderr)
        self.assertFalse(output.exists())
