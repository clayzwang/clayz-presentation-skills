import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

FILE = Path(__file__).resolve().parents[1] / 'scripts/validate_markdown_links.py'
spec = importlib.util.spec_from_file_location('frozen_link_validation', FILE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FrozenFindingsBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.doc = self.root / 'frozen/old.md'
        self.doc.parent.mkdir()
        self.doc.write_text('[old](missing.md)\n')
        self.sha = 'a' * 64
        (self.root / 'published').mkdir()
        (self.root / 'published/publication.json').write_text(json.dumps({'archive': {'sha256': self.sha}}))
        self.record = {'contract': 'io.clayz.frozen-markdown-findings/1',
                       'publication': 'published/publication.json', 'archive_sha256': self.sha,
                       'findings': [{'path': 'frozen/old.md', 'target': 'missing.md',
                                     'error': 'target does not exist',
                                     'source_sha256': hashlib.sha256(self.doc.read_bytes()).hexdigest()}]}
        self.save()

    def save(self):
        (self.root / 'published/frozen-markdown-findings.json').write_text(json.dumps(self.record))

    def test_strict_validator_still_observes_original_error(self):
        self.assertEqual(len(module.validate(self.root)), 1)

    def test_exact_frozen_error_is_reported_separately(self):
        errors, retained = module.partition_frozen_findings(self.root, module.validate(self.root))
        self.assertFalse(errors)
        self.assertEqual(len(retained), 1)

    def test_changed_source_cannot_reuse_old_allowance(self):
        self.doc.write_text(self.doc.read_text() + '\nChanged bytes.\n')
        errors, retained = module.partition_frozen_findings(self.root, module.validate(self.root))
        self.assertEqual(len(errors), 1)
        self.assertFalse(retained)

    def test_new_errors_remain_blocking(self):
        (self.root / 'new.md').write_text('[new](also-missing.md)\n')
        errors, retained = module.partition_frozen_findings(self.root, module.validate(self.root))
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(retained), 1)

    def test_publication_identity_change_fails_closed(self):
        self.record['archive_sha256'] = 'b' * 64
        self.save()
        with self.assertRaises(ValueError):
            module.partition_frozen_findings(self.root, module.validate(self.root))


if __name__ == '__main__':
    unittest.main()
