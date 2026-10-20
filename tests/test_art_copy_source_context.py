"""Semantic lineage support stays explicit and independent from structural diff."""
import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from art_learning import copy_source_context


class CopySourceContextTests(unittest.TestCase):
    def setUp(self):
        self.package = {'copy_layer': {'slides': [
            {'slide_id': 'P1', 'copy_units': [{'copy_id': 'a', 'text': 'revenue'}, {'copy_id': 'b', 'text': 'expense'}]},
            {'slide_id': 'P2', 'copy_units': [{'copy_id': 'c', 'text': 'customer orders; company delivers'}]}]}}

    def page(self, sid, uid, refs=None):
        p = {'slide_id': sid, 'copy_units': [{'copy_id': uid, 'text': 'authored result'}]}
        if refs is not None:
            p['source_basis'] = [{'copy_id': uid, 'source_copy_ids': refs}]
        return p

    def test_split_and_shift_use_explicit_original_identity(self):
        pages = [self.page('P1', 'x', ['a']), self.page('P2', 'y', ['b']), self.page('P3', 'z', ['c'])]
        r = copy_source_context(self.package, pages)['pages']
        self.assertEqual(r[1]['same_slot_copy_page_id'], 'P2')
        self.assertEqual(r[1]['units'][0]['source_units'][0]['slide_id'], 'P1')
        self.assertIsNone(r[2]['same_slot_copy_page_id'])
        self.assertEqual(r[2]['units'][0]['source_units'][0]['copy_unit']['text'], 'customer orders; company delivers')

    def test_merge_reorder_and_repeat_references(self):
        r = copy_source_context(self.package, [self.page('R', 'x', ['c', 'a', 'c'])])
        self.assertEqual([s['copy_unit']['copy_id'] for s in r['pages'][0]['units'][0]['source_units']], ['c', 'a'])

    def test_missing_basis_never_falls_back_to_same_page(self):
        u = copy_source_context(self.package, [self.page('P1', 'x')])['pages'][0]['units'][0]
        self.assertFalse(u['basis_supplied'])
        self.assertEqual(u['source_units'], [])

    def test_unknown_and_unmatched_basis_are_exposed(self):
        p = self.page('N', 'x', ['a', 'unknown'])
        p['source_basis'].append({'copy_id': 'missing-target', 'source_copy_ids': ['b']})
        r = copy_source_context(self.package, [p])['pages'][0]
        self.assertEqual(r['units'][0]['unresolved_copy_ids'], ['unknown'])
        self.assertEqual(r['unmatched_basis_rows'][0]['copy_id'], 'missing-target')

    def test_duplicate_original_unit_identity_is_ambiguous(self):
        self.package['copy_layer']['slides'][1]['copy_units'][0]['copy_id'] = 'a'
        with self.assertRaisesRegex(ValueError, 'duplicate Copy-unit'):
            copy_source_context(self.package, [])

    def test_duplicate_target_and_basis_are_rejected(self):
        with self.assertRaises(ValueError):
            copy_source_context(self.package, [self.page('R', 'x'), self.page('R2', 'x')])
        p = self.page('R', 'x', ['a'])
        p['source_basis'].append(copy.deepcopy(p['source_basis'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate source_basis'):
            copy_source_context(self.package, [p])

    def test_bad_reference_shape_and_duplicate_pages(self):
        with self.assertRaisesRegex(ValueError, 'array'):
            copy_source_context(self.package, [self.page('R', 'x', 'a')])
        with self.assertRaisesRegex(ValueError, 'duplicate slide'):
            copy_source_context(self.package, [self.page('R', 'x'), self.page('R', 'y')])

    def test_no_mutation_or_semantic_approval(self):
        pages = [self.page('P1', 'x', ['c'])]
        before = copy.deepcopy((self.package, pages))
        result = copy_source_context(self.package, pages)
        self.assertEqual((self.package, pages), before)
        result['pages'][0]['units'][0]['source_units'][0]['copy_unit']['text'] = 'changed report only'
        self.assertEqual((self.package, pages), before)
        self.assertNotIn('quality_status', result)
        self.assertNotIn('ok', result)


if __name__ == '__main__':
    unittest.main()
